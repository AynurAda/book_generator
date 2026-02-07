"""
Content generation for subsections, sections, and chapters.

This module handles the generation of actual book content:
- Subsection content (individual topic explanations with multi-branch generation)
- Section introductions
- Chapter introductions
- Final assembly by concatenation

CITATION AWARENESS:
When citations are enabled, content generation is CONSTRAINED to only
include factual claims that have been verified against sources. The
citation context provides a list of "allowed claims" that can be made
and must be cited properly.
"""

import logging
from typing import List, Optional, Dict

import synalinks

from .models import (
    SubsectionInput, SubsectionContent,
    SectionIntroInput, SectionIntro,
    ChapterIntroInput, ChapterIntro,
    PartConclusionInput, PartConclusion,
    SectionQualityInput, QualityAssessment,
    ResearchDistributionInput, ResearchDistributionPlan,
)
from .utils import (
    sanitize_filename,
    output_exists,
    load_from_file,
    load_json_from_file,
    save_to_file,
    save_json_to_file,
    build_outline_text,
)
from .planning import (
    format_book_plan,
    format_chapters_overview,
    format_chapter_plan,
    format_section_plan,
)

logger = logging.getLogger(__name__)


# =============================================================================
# QUALITY CONTROL
# =============================================================================

async def check_section_quality(
    section_content: str,
    section_name: str,
    section_plan: str,
    audience: str,
    language_model,
) -> tuple:
    """
    Check quality of a section and return (passed: bool, feedback: str).
    """
    quality_input = SectionQualityInput(
        section_name=section_name,
        section_content=section_content,
        section_plan=section_plan,
        audience=audience
    )

    generator = synalinks.Generator(
        data_model=QualityAssessment,
        language_model=language_model,
        temperature=1.0,
        instructions="""Assess the quality of this section content. Check for:

1. REPEATED EXAMPLES: Are any examples repeated or too similar across subsections?
2. REPEATED CONCEPTS: Are explanations redundantly repeated?
3. STYLE ISSUES: Is there forced humor, patronizing tone, or overused phrases like "Imagine..."?
4. COVERAGE GAPS: Are important topics from the plan not adequately covered?

Be specific about issues. Set verdict to 'pass' if acceptable, 'needs_rewrite' if significant issues."""
    )

    result = await generator(quality_input)
    if result is None:
        return (True, "")

    data = result.get_json()
    verdict = data.get("verdict", "pass")
    passed = verdict == "pass"

    # Build feedback from issues found
    feedback_parts = []
    if data.get("repeated_examples"):
        feedback_parts.append(f"Repeated examples: {', '.join(data['repeated_examples'])}")
    if data.get("repeated_concepts"):
        feedback_parts.append(f"Repeated concepts: {', '.join(data['repeated_concepts'])}")
    if data.get("style_issues"):
        feedback_parts.append(f"Style issues: {', '.join(data['style_issues'])}")
    if data.get("coverage_gaps"):
        feedback_parts.append(f"Coverage gaps: {', '.join(data['coverage_gaps'])}")

    feedback = "; ".join(feedback_parts)
    return (passed, feedback)


# =============================================================================
# RESEARCH DISTRIBUTION PLANNING
# =============================================================================

class SubsectionMatchInput(synalinks.DataModel):
    """Input for subsection matching Decision."""
    subsection_name: str = synalinks.Field(description="The subsection name to match")


async def match_subsection_to_assignment(
    subsection_name: str,
    assignments: List[dict],
    language_model,
) -> Optional[dict]:
    """
    Use synalinks.Decision to match a subsection to its research assignment.

    Args:
        subsection_name: The actual subsection name we're generating
        assignments: List of assignment dicts from plan_research_distribution
        language_model: Synalinks language model

    Returns:
        The matched assignment dict, or None if no match
    """
    if not assignments:
        return None

    # Build labels from assignment names
    labels = [a.get("subsection_name", f"Assignment {i+1}") for i, a in enumerate(assignments)]

    # Build descriptive text for the question
    assignments_text = "\n".join(
        f"  {i+1}. {a.get('subsection_name', 'Unknown')}: {a.get('focus_area', '')[:60]}"
        for i, a in enumerate(assignments)
    )

    match_input = SubsectionMatchInput(subsection_name=subsection_name)

    try:
        decision = await synalinks.Decision(
            question=f"""Which research assignment should be used for this subsection?

SUBSECTION: "{subsection_name}"

AVAILABLE ASSIGNMENTS:
{assignments_text}

Select the assignment whose topic best matches this subsection.""",
            labels=labels,
            language_model=language_model,
            temperature=1.0,
        )(match_input)

        if decision is None:
            logger.warning(f"    Decision returned None for '{subsection_name[:40]}...'")
            return None

        # Get the selected label and find the corresponding assignment
        decision_json = decision.get_json()
        selected_label = decision_json.get("choice")
        logger.debug(f"    Decision result: {decision_json}")

        if selected_label:
            for i, label in enumerate(labels):
                if label == selected_label:
                    logger.info(f"    Decision: '{subsection_name[:30]}...' → '{selected_label[:30]}...'")
                    return assignments[i]
        else:
            logger.warning(f"    Decision has no 'choice' field: {decision_json}")

    except Exception as e:
        logger.error(f"    Decision failed for '{subsection_name[:40]}...': {e}")

    return None


async def plan_research_distribution(
    section_name: str,
    section_plan: str,
    subsection_names: List[str],
    research_context: str,
    language_model,
) -> List[dict]:
    """
    Plan how to distribute research findings across subsections.

    Returns a LIST of assignments (not a dict). Each subsection will use
    synalinks.Decision to match itself to the appropriate assignment.

    Returns:
        List of assignment dicts, each with:
            "subsection_name": str (LLM's name for this assignment)
            "concepts": [...]
            "example_domain": str
            "focus_area": str
    """
    if not research_context or not subsection_names:
        return []

    logger.info(f"  Planning research distribution for {len(subsection_names)} subsections...")

    # Format subsection names for the LLM
    numbered_names = "\n".join(f"{i+1}. {name}" for i, name in enumerate(subsection_names))

    distribution_input = ResearchDistributionInput(
        section_name=section_name,
        section_plan=section_plan,
        subsection_names=numbered_names,
        research_context=research_context,
    )

    generator = synalinks.Generator(
        data_model=ResearchDistributionPlan,
        language_model=language_model,
        temperature=1.0,
        instructions=f"""Distribute research concepts across subsections to PREVENT REPETITION.

THE SUBSECTIONS ARE:
{numbered_names}

=== CONCEPT EXCLUSIVITY (CRITICAL) ===

Each concept/paper/method can ONLY appear in ONE subsection's assigned_concepts.

Example: If research mentions VeriCoT, DomiKnowS, LoT, Z3:
- VeriCoT → assign to ONE subsection ONLY
- DomiKnowS → assign to a DIFFERENT subsection ONLY
- LoT → assign to a DIFFERENT subsection ONLY
- Z3 → assign to a DIFFERENT subsection ONLY

NO CONCEPT SHOULD APPEAR IN MULTIPLE ASSIGNMENTS.

=== DOMAIN EXCLUSIVITY ===

Each subsection gets a UNIQUE example_domain:
- Subsection 1: e.g., "healthcare"
- Subsection 2: e.g., "finance" (NOT healthcare)
- Subsection 3: e.g., "robotics" (NOT healthcare or finance)
- Subsection 4: e.g., "education" (NOT any used above)

=== OUTPUT ===

Create one assignment per subsection with:
- subsection_name: the subsection this is for
- assigned_concepts: list of concepts EXCLUSIVE to this subsection
- example_domain: domain UNIQUE to this subsection
- focus_area: what this subsection emphasizes"""
    )

    result = await generator(distribution_input)
    if result is None:
        logger.warning("  Research distribution planning failed")
        return []

    data = result.get_json()
    assignments = data.get("assignments", [])

    # Convert to list of dicts
    distribution_list = []
    for assignment in assignments:
        distribution_list.append({
            "subsection_name": assignment.get("subsection_name", ""),
            "concepts": assignment.get("assigned_concepts", []),
            "example_domain": assignment.get("example_domain", ""),
            "focus_area": assignment.get("focus_area", ""),
        })
        logger.info(f"    {assignment.get('subsection_name', '')[:40]}: {len(assignment.get('assigned_concepts', []))} concepts, domain={assignment.get('example_domain', '')}")

    all_concepts = []
    for a in distribution_list:
        all_concepts.extend(a.get("concepts", []))
    logger.info(f"  Distribution complete: {len(all_concepts)} total concepts across {len(distribution_list)} assignments")

    return distribution_list


def format_assigned_research(
    assignment: dict,
    full_research: str,
    all_assignments: Optional[List[dict]] = None,
    current_subsection: str = "",
) -> str:
    """
    Format the assigned research for a specific subsection.

    Args:
        assignment: The assignment for this subsection
        full_research: The full research context
        all_assignments: Optional list of all assignments (for showing banned concepts)
        current_subsection: Name of current subsection (for filtering)
    """
    if not assignment:
        return ""

    parts = []

    # Show assigned concepts prominently
    if assignment.get("concepts"):
        parts.append("╔══════════════════════════════════════════════════════════════╗")
        parts.append("║ YOUR EXCLUSIVE CONCEPTS (explain ONLY these in depth):       ║")
        parts.append("╚══════════════════════════════════════════════════════════════╝")
        for concept in assignment["concepts"]:
            parts.append(f"  ✓ {concept}")
        parts.append("")

    # Show banned concepts (assigned to other subsections)
    if all_assignments:
        other_concepts = []
        current_concepts = set(assignment.get("concepts", []))
        for other_assignment in all_assignments:
            # Skip if this is the same assignment (compare by concepts)
            other_concepts_set = set(other_assignment.get("concepts", []))
            if other_concepts_set != current_concepts:
                other_concepts.extend(other_assignment.get("concepts", []))
        if other_concepts:
            parts.append("╔══════════════════════════════════════════════════════════════╗")
            parts.append("║ BANNED CONCEPTS (assigned to other subsections - DO NOT      ║")
            parts.append("║ explain these, just reference them if needed):               ║")
            parts.append("╚══════════════════════════════════════════════════════════════╝")
            for concept in other_concepts[:10]:  # Limit to avoid token overflow
                parts.append(f"  ✗ {concept}")
            if len(other_concepts) > 10:
                parts.append(f"  ... and {len(other_concepts) - 10} more")
            parts.append("")

    # Show assigned domain
    if assignment.get("example_domain"):
        parts.append(f"YOUR EXAMPLE DOMAIN: {assignment['example_domain']}")
        parts.append("(Use examples from this domain ONLY. Other subsections use different domains.)")
        parts.append("")

    # Show focus area
    if assignment.get("focus_area"):
        parts.append(f"YOUR FOCUS: {assignment['focus_area']}")
        parts.append("")

    # Include research for reference
    parts.append("RESEARCH CONTEXT (for reference - but only cover YOUR assigned concepts):")
    parts.append(full_research[:6000])  # Slightly reduced to make room for banned concepts

    return "\n".join(parts)


# =============================================================================
# SUBSECTION GENERATION
# =============================================================================

async def generate_subsection(
    subsection_input: SubsectionInput,
    language_model,
    writing_style: Optional[object] = None,
    citation_instructions: Optional[str] = None,
    research_context: Optional[str] = None,
) -> str:
    """
    Generate a single subsection with full planning context.

    The subsection_input contains all context needed:
    - topic, goal, book_name, audience
    - full_outline (entire book structure)
    - book_plan (high-level book strategy)
    - chapters_overview (all chapters summary)
    - chapter_name, chapter_plan (current chapter context)
    - section_name, section_plan (current section context)
    - subsection_name (the specific topic to write)

    Args:
        subsection_input: Input with all context
        language_model: Synalinks language model
        writing_style: Optional writing style object
        citation_instructions: Optional citation constraints from verification pipeline.
            When provided, the generator is CONSTRAINED to only make factual claims
            that appear in the allowed claims list and must cite them properly.
        research_context: Optional research findings to incorporate (cutting-edge content)

    Returns:
        The subsection content
    """
    # Build style instructions if provided
    style_section = ""
    if writing_style:
        style_section = f"""
=== WRITING STYLE ===

{writing_style.style_instructions}

Apply this style while maintaining all depth requirements. Style does NOT mean shorter.

"""

    # Build citation section if provided - THIS IS CRITICAL FOR PREVENTING HALLUCINATION
    citation_section = ""
    if citation_instructions:
        citation_section = f"""
=== CITATION REQUIREMENTS (MANDATORY) ===

{citation_instructions}

=== END CITATION REQUIREMENTS ===

"""

    # Build research section if provided - FOR CUTTING-EDGE CONTENT
    research_section = ""
    if research_context:
        research_section = f"""
=== YOUR EXCLUSIVE RESEARCH ASSIGNMENT ===

{research_context}

=== CONCEPT EXCLUSIVITY RULES (MANDATORY) ===

A planner has DIVIDED the research concepts among subsections. You have been assigned SPECIFIC concepts above.

1. EXPLAIN ONLY your assigned concepts in depth
2. If you need to mention a concept NOT in your list:
   - Do NOT explain it
   - Just reference it briefly: "Using VeriCoT (covered in Section 1.1.2)..."
3. Use ONLY your assigned example domain (other subsections have different domains)
4. If a concept appears in a previous subsection, reference it, don't re-explain

Violating these rules causes repetition across subsections - the #1 quality issue we need to avoid.

=== END RESEARCH ===

"""

    # Build previous subsections section - FOR COHERENCE AND SAFETY
    previous_section = ""
    previous_subsections = getattr(subsection_input, 'previous_subsections', '')
    if previous_subsections:
        previous_section = f"""
=== PREVIOUSLY WRITTEN SUBSECTIONS (READ CAREFULLY) ===

{previous_subsections}

=== ANTI-REPETITION CHECK (MANDATORY) ===

Before you write, scan the above content for:

1. **Concepts already explained** - If VeriCoT, DomiKnowS, Z3, LoT, or any framework was explained above:
   - Do NOT re-explain it
   - Reference it: "As we saw with VeriCoT in Section 1.1.2..."
   - Focus on NEW aspects not covered above

2. **Example domains used** - Note what domains were used (e.g., finance, healthcare, robotics)
   - Use YOUR assigned domain (which should be different)
   - Do NOT use the same domain as a previous section

3. **Opening patterns** - Note how previous sections started
   - Vary your opening style

If you find yourself about to explain something that was explained above, STOP and reference it instead.

=== END PREVIOUS SUBSECTIONS ===

"""

    instructions = f"""{style_section}{citation_section}{research_section}{previous_section}Write comprehensive content for this specific subsection/topic in WaitButWhy style (Tim Urban's blog) but with TEXTBOOK-LEVEL DEPTH AND RIGOR.

You have access to the full book context: book plan, chapters overview, chapter plan, and section plan.
Use this context to understand what depth and coverage is expected.

TARGET AUDIENCE: Write for the specified audience with appropriate technical depth.

=== WAITBUTWHY + TEXTBOOK HYBRID ===

Channel Tim Urban's WaitButWhy style:
- Conversational, engaging tone that pulls readers in
- Break down complex ideas so they truly click
- Use analogies and thought experiments that illuminate
- Don't be afraid to be a bit playful or use humor naturally
- Write like you're explaining to a smart friend over coffee

BUT maintain textbook rigor:
- Be technically precise - no hand-waving or oversimplification
- Include the actual mechanisms, algorithms, and formal details
- Don't sacrifice accuracy for accessibility - do BOTH
- Cover the topic comprehensively, not superficially
- This should be something a student could study from

ORIGINAL THINKING (encouraged):
- Share novel interpretations: "One way to think about this is..."
- Make connections: "This suggests a potential link to..."
- Offer mental models: "A useful way to visualize this..."
- Speculate on implications: "This opens the possibility that..."
- Provide author insights: "What makes this particularly elegant is..."

You CAN be original and speculative - just don't present speculation as established fact.

OPENING: Use the approach specified in the input's "opening_approach" field. Do NOT use "Imagine..." - this is overused.

=== CONCEPT DEFINITIONS (CRITICAL) ===

When you first introduce a technical term or concept, you MUST define it clearly.

For each new technical term or method:
1. **Bold** the term on first use
2. Immediately follow with a brief, accessible definition
3. Use format: "**Term Name** — definition explanation."

Examples:
- "**Noise-tolerant ILP** — a variant of Inductive Logic Programming that can handle noisy or inconsistent training examples without failing."
- "**Top-k Provenance Semiring** — a mathematical structure that tracks not just whether a conclusion is derivable, but the k most important proofs of it."
- "**Differentiable logic** — an approach that makes discrete logical operations continuous, allowing gradient-based optimization to flow through symbolic reasoning."

DO NOT assume readers know specialized terminology. Every first-use technical term needs a clear definition inline.
If you reference a paper or method by name, explain what it does, not just that it exists.

=== CONTENT REQUIREMENTS ===

Write free-flowing, well-organized prose that:

1. **Defines and explains** - Establish what the concept IS. Be precise with definitions but explain them in accessible terms. Build understanding from first principles.

2. **Goes deep into mechanisms** - Explain HOW things work, not just what they are. Include the underlying principles, algorithms, or processes. Make technical content engaging, not dry.

3. **Illustrates with examples** - Weave in concrete, specific examples that illuminate different aspects. Good examples make abstract concepts click.

4. **Addresses nuances** - Cover edge cases, limitations, and common misconceptions. Anticipate where readers might get confused and address it.

5. **Shows connections** - Help readers see how this fits into the broader picture. Reference related concepts and show how ideas build on each other.

Let the content dictate structure - some topics need more examples, others need more theory. Paragraphs should flow naturally.

LENGTH: Write substantial content. A subsection should be thorough enough to stand alone as a complete explanation. Think 800-1500 words depending on topic complexity.

=== WHAT NOT TO INCLUDE ===

Do NOT include generic "why it matters" content about:
- Explainability/interpretability benefits
- Generalization improvements
- Real-world applications
- Practical implications

These are covered in a separate part-level conclusion. Focus on explaining WHAT this concept is and HOW it works.

FORMATTING:
- Do NOT use markdown headers (no #, ##, ###, ####)
- You CAN use **bold** for emphasis
- Write in flowing prose (occasional bullets for lists are OK)"""

    generator = synalinks.Generator(
        data_model=SubsectionContent,
        language_model=language_model,
        temperature=1.0,
        instructions=instructions
    )

    result = await generator(subsection_input)
    data = result.get_json()

    # Return the free-flowing content
    return data.get("content", "")


async def generate_section_intro(
    topic: str,
    book_name: str,
    chapter_name: str,
    section_name: str,
    section_plan: str,
    subsection_names: List[str],
    intro_style: str,
    language_model
) -> str:
    """
    Generate an introduction for a section.

    Returns:
        The section introduction (2-3 paragraphs)
    """
    generator = synalinks.Generator(
        data_model=SectionIntro,
        language_model=language_model,
        temperature=1.0,
        instructions=f"""Write a section introduction in WaitButWhy style (Tim Urban's blog).

OPENING APPROACH: {intro_style}

1-2 short paragraphs that set up what this section covers and why it matters.
No headers. No formal academic tone."""
    )

    subsections_list = "\n".join(f"- {name}" for name in subsection_names)

    input_data = SectionIntroInput(
        topic=topic,
        book_name=book_name,
        chapter_name=chapter_name,
        section_name=section_name,
        section_plan=section_plan or "No specific plan available",
        subsection_names=subsections_list,
        intro_style=intro_style
    )

    result = await generator(input_data)
    return result.get_json().get("introduction", "")


async def generate_part_intro(
    topic: str,
    book_name: str,
    book_plan: dict,
    chapters_overview: dict,
    part_name: str,
    part_number: int,
    total_parts: int,
    part_plan: dict,
    chapter_names: List[str],
    chapter_plans: List[dict],
    language_model
) -> str:
    """
    Generate an introduction for a part that shows how chapters fit together
    and how this part fits into the overall book.

    Returns:
        The part introduction
    """
    generator = synalinks.Generator(
        data_model=ChapterIntro,
        language_model=language_model,
        temperature=1.0,
        instructions="""Write a part introduction in WaitButWhy style (Tim Urban's blog).

You have access to:
- The overall book plan and narrative arc
- This part's plan
- Detailed plans for EACH chapter within this part

Your intro should:
1. Put this part in context of the OVERALL BOOK JOURNEY (what came before, what comes after)
2. Explain the UNIFYING THEME of this part - what ties all the chapters together
3. Show how the chapters BUILD ON EACH OTHER within this part
4. Give the reader a sense of the intellectual journey through this part

2-3 paragraphs. Show the connections and flow, not just a list of topics.
No headers. No formal academic tone."""
    )

    # Format chapters list
    chapters_list = "\n".join(f"- {name}" for name in chapter_names)

    # Format detailed chapter plans
    chapter_plans_text = []
    for i, (name, plan) in enumerate(zip(chapter_names, chapter_plans)):
        plan_text = format_section_plan(plan) if plan else "No detailed plan"
        chapter_plans_text.append(f"Chapter {name}:\n{plan_text}")
    chapter_plans_detail = "\n\n".join(chapter_plans_text)

    input_data = ChapterIntroInput(
        topic=topic,
        book_name=book_name,
        book_plan=format_book_plan(book_plan),
        chapters_overview=format_chapters_overview(chapters_overview),
        chapter_name=part_name,
        chapter_number=part_number,
        total_chapters=total_parts,
        chapter_plan=format_chapter_plan(part_plan),
        section_names=chapters_list,
        chapter_plans_detail=chapter_plans_detail
    )

    result = await generator(input_data)
    return result.get_json().get("introduction", "")


async def generate_part_conclusion(
    topic: str,
    book_name: str,
    book_plan: dict,
    part_name: str,
    part_number: int,
    total_parts: int,
    chapter_names: List[str],
    chapter_summaries: List[str],
    audience: str,
    language_model
) -> str:
    """
    Generate a conclusion for a part - the unified "Why It Matters" section.

    This replaces repetitive "why it matters" subsections in each section.
    Instead, we have one comprehensive conclusion per part that covers
    practical implications and significance.

    Returns:
        The part conclusion
    """
    generator = synalinks.Generator(
        data_model=PartConclusion,
        language_model=language_model,
        temperature=1.0,
        instructions="""Write a "Why It Matters" conclusion for this part in WaitButWhy style.

This is the UNIFIED place to discuss practical significance - individual sections do NOT need their own "why it matters."

Your conclusion should:
1. SYNTHESIZE the key takeaways from all chapters in this part
2. Explain PRACTICAL IMPLICATIONS - how this knowledge is applied in the real world
3. Connect to the TARGET AUDIENCE's needs and goals
4. Show why understanding these concepts is valuable (not just interesting)

Be specific and concrete:
- Don't just say "this is important for explainability" - explain HOW it enables explainability
- Don't just say "this matters for generalization" - show WHAT problems it solves
- Use specific examples of real-world applications

3-4 paragraphs. No headers. Conversational but substantive."""
    )

    chapters_list = "\n".join(f"- {name}" for name in chapter_names)
    summaries_text = "\n\n".join(chapter_summaries)

    input_data = PartConclusionInput(
        topic=topic,
        book_name=book_name,
        book_plan=format_book_plan(book_plan),
        part_name=part_name,
        part_number=part_number,
        total_parts=total_parts,
        chapter_names=chapters_list,
        chapter_summaries=summaries_text,
        audience=audience
    )

    result = await generator(input_data)
    return result.get_json().get("conclusion", "")


def _assemble_section(section_intro: str, subsection_contents: List[tuple]) -> str:
    """Assemble section from intro and subsection contents."""
    section_parts = []

    if section_intro:
        section_parts.append(section_intro)
        section_parts.append("")

    for subsection_name, content in subsection_contents:
        section_parts.append(f"### {subsection_name}")
        section_parts.append("")
        section_parts.append(content)
        section_parts.append("")

    return "\n".join(section_parts)


async def write_section_with_subsections(
    topic_data: dict,
    full_outline: str,
    book_plan: dict,
    chapters_overview: dict,
    chapter_name: str,
    chapter_plan: dict,
    section_name: str,
    section_plan: dict,
    subsection_names: List[str],
    intro_style: str,
    intro_styles: List[str],
    style_idx: int,
    language_model,
    output_dir: str,
    section_num: int,
    writing_style: Optional[object] = None,
    get_citation_instructions: Optional[callable] = None,
    get_research_context: Optional[callable] = None,
) -> tuple:
    """
    Write a complete section by generating each subsection separately.
    If quality check fails, regenerates subsections with feedback.

    Args:
        get_citation_instructions: Optional callback(chapter, section, subsection) -> str
            Returns STRICT citation instructions for each subsection.
        get_research_context: Optional callback(chapter, section) -> str
            Returns research context for cutting-edge content.
    """
    safe_section = sanitize_filename(section_name)
    section_filename = f"03_section_{section_num:03d}_{safe_section}.txt"

    # Check for existing content
    if output_dir and output_exists(output_dir, section_filename):
        existing = load_from_file(output_dir, section_filename)
        if existing:
            logger.info(f"Loaded existing section: {section_name}")
            return (existing, style_idx)

    logger.info(f"Writing section: {section_name} ({len(subsection_names)} subsections)")

    section_plan_text = format_section_plan(section_plan) if section_plan else "No specific plan"
    quality_feedback = ""
    attempt = 0
    max_attempts = 5  # Safety limit

    # Get research context ONCE for the entire section (outside the loop)
    full_research_context = None
    research_assignments = []  # List of assignments from planning
    if get_research_context:
        import inspect
        if inspect.iscoroutinefunction(get_research_context):
            full_research_context = await get_research_context(chapter_name, section_name)
        else:
            full_research_context = get_research_context(chapter_name, section_name)
        if full_research_context:
            logger.info(f"  Research context for section: {len(full_research_context)} chars")
            # Plan how to distribute research across subsections (prevents repetition)
            research_assignments = await plan_research_distribution(
                section_name=section_name,
                section_plan=section_plan_text,
                subsection_names=subsection_names,
                research_context=full_research_context,
                language_model=language_model,
            )

    while attempt < max_attempts:
        # Generate section introduction (only on first attempt)
        if attempt == 0:
            section_intro = await generate_section_intro(
                topic=topic_data["topic"],
                book_name=topic_data["book_name"],
                chapter_name=chapter_name,
                section_name=section_name,
                section_plan=section_plan_text,
                subsection_names=subsection_names,
                intro_style=intro_style,
                language_model=language_model
            )

        # Generate each subsection with sequential awareness
        subsection_contents = []
        previous_subsections_text = ""  # Build up as we generate

        for i, subsection_name in enumerate(subsection_names):
            if attempt == 0:
                logger.info(f"  Generating subsection {i+1}/{len(subsection_names)}: {subsection_name}")
            else:
                logger.info(f"  Regenerating subsection {i+1}/{len(subsection_names)}: {subsection_name} (attempt {attempt + 1})")

            opening_approach = intro_styles[style_idx % len(intro_styles)]
            style_idx += 1

            # Add quality feedback to the plan if this is a rewrite
            augmented_plan = section_plan_text
            if quality_feedback:
                augmented_plan = f"{section_plan_text}\n\n=== QUALITY FEEDBACK (fix these issues) ===\n{quality_feedback}"

            # Get subsection-specific citation instructions
            citation_instructions = None
            if get_citation_instructions:
                citation_instructions = get_citation_instructions(chapter_name, section_name, subsection_name)

            # Get ASSIGNED research for this subsection using Decision
            research_context = None
            if full_research_context and research_assignments:
                # Use synalinks.Decision to match subsection to its assignment
                assignment = await match_subsection_to_assignment(
                    subsection_name=subsection_name,
                    assignments=research_assignments,
                    language_model=language_model,
                )
                if assignment:
                    research_context = format_assigned_research(
                        assignment,
                        full_research_context,
                        all_assignments=research_assignments,
                        current_subsection=subsection_name,
                    )
                    logger.info(f"    Assigned: {len(assignment.get('concepts', []))} concepts, domain={assignment.get('example_domain', 'N/A')}")
                else:
                    # Fallback to full context if Decision fails
                    logger.warning(f"    No assignment matched for '{subsection_name[:40]}...', using full context")
                    research_context = full_research_context
            elif full_research_context:
                # No assignments planned, use full context
                research_context = full_research_context

            subsection_input = SubsectionInput(
                topic=topic_data["topic"],
                goal=topic_data["goal"],
                book_name=topic_data["book_name"],
                audience=topic_data.get("audience", "technical readers"),
                full_outline=full_outline,
                book_plan=format_book_plan(book_plan),
                chapters_overview=format_chapters_overview(chapters_overview),
                chapter_name=chapter_name,
                chapter_plan=format_chapter_plan(chapter_plan),
                section_name=section_name,
                section_plan=augmented_plan,
                subsection_name=subsection_name,
                opening_approach=opening_approach,
                previous_subsections=previous_subsections_text,
            )

            content = await generate_subsection(
                subsection_input=subsection_input,
                language_model=language_model,
                writing_style=writing_style,
                citation_instructions=citation_instructions,
                research_context=research_context,
            )

            if content:
                subsection_contents.append((subsection_name, content))
                # Add to previous subsections for sequential awareness
                previous_subsections_text += f"\n### {subsection_name}\n{content}\n"

        # Assemble section
        section_content = _assemble_section(section_intro, subsection_contents)

        # Quality check
        passed, feedback = await check_section_quality(
            section_content=section_content,
            section_name=section_name,
            section_plan=section_plan_text,
            audience=topic_data.get("audience", "technical readers"),
            language_model=language_model,
        )

        if passed:
            logger.info(f"  Quality check: PASSED for {section_name}")
            break
        else:
            attempt += 1
            if attempt >= max_attempts:
                logger.warning(f"  Quality check: MAX ATTEMPTS reached for {section_name}, using last version")
                break
            logger.info(f"  Quality check: NEEDS IMPROVEMENT for {section_name} (will retry)")
            logger.info(f"    Feedback: {feedback[:200]}...")
            quality_feedback = feedback
            # Save QC feedback
            if output_dir:
                qc_filename = f"03_qc_{section_num:03d}_{safe_section}.txt"
                save_to_file(output_dir, qc_filename, f"Attempt {attempt}\nFeedback: {feedback}")

    # Save the final section
    if output_dir:
        save_to_file(output_dir, section_filename, section_content)

    return (section_content, style_idx)


async def write_chapter_with_sections(
    topic_data: dict,
    full_outline: str,
    book_plan: dict,
    chapters_overview: dict,
    chapter_name: str,
    chapter_number: int,
    total_chapters: int,
    chapter_plan: dict,
    chapter_section_plans: dict,
    chapter_sections: Dict[str, List[str]],
    language_model,
    output_dir: str,
    intro_styles: List[str],
    style_idx: int,
    writing_style: Optional[object] = None,
    get_citation_instructions: Optional[callable] = None,
    get_research_context: Optional[callable] = None,
    citation_manager: Optional[object] = None,
    chapter_papers: Optional[List[dict]] = None,
) -> tuple:
    """
    Write a complete chapter by:
    1. Generating a chapter introduction
    2. Generating each section (which generates each subsection separately)
    3. Concatenating everything

    Args:
        get_research_context: Optional callback(chapter, section) -> str for research context
        citation_manager: Optional CitationManager for per-chapter references (from full citation pipeline)
        chapter_papers: Optional list of paper dicts for fast chapter references (from research)

    Returns:
        Tuple of (chapter_content, new_style_idx)
    """
    safe_chapter = sanitize_filename(chapter_name)
    chapter_filename = f"04_chapter_{safe_chapter}.txt"

    # Check for existing chapter
    if output_dir and output_exists(output_dir, chapter_filename):
        existing = load_from_file(output_dir, chapter_filename)
        if existing:
            logger.info(f"Loaded existing chapter: {chapter_name}")
            return ({"chapter_content": existing}, style_idx)

    logger.info(f"Writing chapter {chapter_number}/{total_chapters}: {chapter_name}")

    chapter_names_in_part = list(chapter_sections.keys())
    chapter_plans_in_part = chapter_section_plans.get("section_plans", [])

    # Generate part introduction
    part_intro = await generate_part_intro(
        topic=topic_data["topic"],
        book_name=topic_data["book_name"],
        book_plan=book_plan,
        chapters_overview=chapters_overview,
        part_name=chapter_name,
        part_number=chapter_number,
        total_parts=total_chapters,
        part_plan=chapter_plan,
        chapter_names=chapter_names_in_part,
        chapter_plans=chapter_plans_in_part,
        language_model=language_model
    )

    # Generate each section
    section_contents = []
    section_counter = (chapter_number - 1) * 100  # Section numbering for file naming

    for i, (section_name, subsection_names) in enumerate(chapter_sections.items()):
        if not subsection_names:
            continue

        section_plan = chapter_plans_in_part[i] if i < len(chapter_plans_in_part) else None

        # Get intro style for section intro (rotating)
        intro_style = intro_styles[style_idx % len(intro_styles)]
        style_idx += 1

        section_content, style_idx = await write_section_with_subsections(
            topic_data=topic_data,
            full_outline=full_outline,
            book_plan=book_plan,
            chapters_overview=chapters_overview,
            chapter_name=chapter_name,
            chapter_plan=chapter_plan,
            section_name=section_name,
            section_plan=section_plan,
            subsection_names=subsection_names,
            intro_style=intro_style,
            intro_styles=intro_styles,
            style_idx=style_idx,
            language_model=language_model,
            output_dir=output_dir,
            section_num=section_counter + i + 1,
            writing_style=writing_style,
            get_citation_instructions=get_citation_instructions,
            get_research_context=get_research_context,
        )

        section_contents.append((section_name, section_content))

    # Generate part conclusion (Why It Matters)
    # Create chapter summaries from section plans
    chapter_summaries = []
    for i, (section_name, _) in enumerate(section_contents):
        plan = chapter_plans_in_part[i] if i < len(chapter_plans_in_part) else None
        if plan:
            summary = plan.get("section_summary", f"Covers {section_name}")
        else:
            summary = f"Covers {section_name}"
        chapter_summaries.append(f"{section_name}: {summary}")

    part_conclusion = await generate_part_conclusion(
        topic=topic_data["topic"],
        book_name=topic_data["book_name"],
        book_plan=book_plan,
        part_name=chapter_name,
        part_number=chapter_number,
        total_parts=total_chapters,
        chapter_names=chapter_names_in_part,
        chapter_summaries=chapter_summaries,
        audience=topic_data.get("audience", "technical readers"),
        language_model=language_model
    )

    # Assemble chapter: header + intro + sections + conclusion
    chapter_parts = []

    # Part header (was chapter)
    chapter_parts.append(f"# {chapter_name}")
    chapter_parts.append("")

    # Chapter intro
    if part_intro:
        chapter_parts.append(part_intro)
        chapter_parts.append("")

    # Each section with header (now chapters)
    for section_header, section_content in section_contents:
        chapter_parts.append(f"## {section_header}")
        chapter_parts.append("")
        # Strip any duplicate header that LLM might have added
        content = section_content.strip()
        if content.startswith(f"## {section_header}"):
            content = content[len(f"## {section_header}"):].strip()
        chapter_parts.append(content)
        chapter_parts.append("")

    # Part conclusion (Why It Matters)
    if part_conclusion:
        chapter_parts.append("## Why It Matters")
        chapter_parts.append("")
        chapter_parts.append(part_conclusion)
        chapter_parts.append("")

    # Per-chapter references
    # Option 1: From full citation pipeline (slow, verified)
    if citation_manager:
        chapter_refs = citation_manager.get_chapter_bibliography_markdown(chapter_name)
        if chapter_refs:
            chapter_parts.append("")
            chapter_parts.append(chapter_refs)
    # Option 2: From research papers (fast, unverified)
    elif chapter_papers:
        chapter_parts.append("")
        chapter_parts.append("### References")
        chapter_parts.append("")
        for paper in chapter_papers:
            # Format references properly, handling missing data
            authors_raw = paper.get('authors', '')
            year = paper.get('year', '')
            title = paper.get('title', 'Untitled')
            venue = paper.get('venue', '')

            # Skip bad author values
            authors = authors_raw.strip() if authors_raw else ''
            if authors.lower() in ['unknown', 'not specified', 'n/a', 'none', '']:
                authors = ''

            # Skip bad venue values
            if venue.lower() in ['unknown', 'not specified', 'n/a', 'none', 'arxiv', 'technical report']:
                venue = ''

            # Build reference line
            if authors and year and venue:
                # Full reference: Authors (Year). Title. *Venue*.
                chapter_parts.append(f"- {authors} ({year}). *{title}*. {venue}.")
            elif authors and year:
                # No venue: Authors (Year). Title.
                chapter_parts.append(f"- {authors} ({year}). *{title}*.")
            elif year and venue:
                # No authors: Title (Year). Venue.
                chapter_parts.append(f"- *{title}* ({year}). {venue}.")
            elif year:
                # Just title and year: Title (Year).
                chapter_parts.append(f"- *{title}* ({year}).")
            else:
                # Minimal: just title
                chapter_parts.append(f"- *{title}*.")
        chapter_parts.append("")

    full_chapter = "\n".join(chapter_parts)
    chapter_data = {"chapter_content": full_chapter}

    # Save the chapter
    if output_dir:
        save_to_file(output_dir, chapter_filename, full_chapter)

    return (chapter_data, style_idx)


async def write_all_sections_direct(
    topic_data: dict,
    hierarchy: dict,
    book_plan: dict,
    chapters_overview: dict,
    chapter_plans: dict,
    all_section_plans: dict,
    language_model,
    output_dir: str,
    intro_styles: List[str],
    max_chapters: Optional[int] = None,
    writing_style: Optional[object] = None,
    get_citation_instructions: Optional[callable] = None,
    get_research_context: Optional[callable] = None,
    citation_manager: Optional[object] = None,
    chapter_paper_assignments: Optional[Dict[str, List[dict]]] = None,
) -> List[tuple]:
    """
    Write all chapters by generating each subsection separately with full context.

    This is the main entry point for content generation.

    Architecture:
    - Each subsection is generated independently with full planning context
    - Sections assembled by concatenation (intro + subsections)
    - Chapters assembled by concatenation (intro + sections)

    Args:
        writing_style: Optional WritingStyle object to apply during writing
        get_citation_instructions: Optional callback function that takes (chapter_name, section_name)
            and returns citation instructions string. When provided, content generation
            is CONSTRAINED to only include verified, citable factual claims.
        get_research_context: Optional callback function that takes (chapter_name, section_name)
            and returns research context string for cutting-edge content.
        citation_manager: Optional CitationManager for per-chapter references (slow path)
        chapter_paper_assignments: Optional dict mapping chapter_name -> list of paper dicts (fast path)

    Returns:
        List of (chapter_name, chapter_content_dict) tuples
    """
    from .planning import get_chapter_plan_by_index

    # Build the full outline text for context
    full_outline = build_outline_text({"concepts": [
        {"concept": ch, "subconcepts": [
            {"subconcept": sec, "subsubconcepts": subs}
            for sec, subs in sections.items()
        ]}
        for ch, sections in hierarchy.items()
    ]})

    written_chapters = []
    style_idx = 0

    chapter_names = list(hierarchy.keys())
    total_chapters = len(chapter_names)

    if max_chapters:
        chapter_names = chapter_names[:max_chapters]
        total_chapters = len(chapter_names)

    for chapter_idx, chapter_name in enumerate(chapter_names):
        chapter_plan = get_chapter_plan_by_index(chapter_plans, chapter_idx)
        chapter_sections = hierarchy.get(chapter_name, {})
        chapter_section_plans = all_section_plans.get(chapter_name, {})

        # Get papers for this chapter (for fast references)
        # Note: chapter_name has number prefix like "1. Chapter Name"
        # but chapter_paper_assignments uses names without prefix
        chapter_papers = None
        if chapter_paper_assignments:
            # Strip number prefix (e.g., "1. " or "2. ") to match assignment keys
            import re
            base_chapter_name = re.sub(r'^\d+\.\s*', '', chapter_name)
            chapter_papers = chapter_paper_assignments.get(base_chapter_name, [])

        chapter_data, style_idx = await write_chapter_with_sections(
            topic_data=topic_data,
            full_outline=full_outline,
            book_plan=book_plan,
            chapters_overview=chapters_overview,
            chapter_name=chapter_name,
            chapter_number=chapter_idx + 1,
            total_chapters=total_chapters,
            chapter_plan=chapter_plan,
            chapter_section_plans=chapter_section_plans,
            chapter_sections=chapter_sections,
            language_model=language_model,
            output_dir=output_dir,
            intro_styles=intro_styles,
            style_idx=style_idx,
            writing_style=writing_style,
            get_citation_instructions=get_citation_instructions,
            get_research_context=get_research_context,
            citation_manager=citation_manager,
            chapter_papers=chapter_papers,
        )

        written_chapters.append((chapter_name, chapter_data))

    return written_chapters
