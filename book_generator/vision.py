"""
Book Vision generation module.

This module handles generating a high-level book vision BEFORE concept generation.
The vision establishes the book's purpose, reader journey, and key themes,
which then guide concept generation to ensure better alignment with the book's focus.

Key features:
- Reader mode decision using synalinks.Branch (practitioner/academic/hybrid)
- Each branch generates a mode-specific vision with appropriate instructions
- Non-selected branches return None, merged with | operator
- Informed vision update after research completes
"""

import logging
import synalinks

from .models import (
    BookVisionInput,
    BookVision,
    ReaderMode,
    InformedVision,
    InformedVisionInput,
)
from .utils import (
    output_exists,
    load_json_from_file,
    save_to_file,
    save_json_to_file,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Mode-Specific Vision Instructions
# =============================================================================

PRACTITIONER_VISION_INSTRUCTIONS = """Generate a PRACTITIONER-focused book vision.

READER MODE: PRACTITIONER (Problem-Centric Organization)
- Readers want to BUILD and IMPLEMENT
- Organize around PROBLEMS and CAPABILITIES (what can readers do?)
- Minimize historical context (just enough to understand why)
- Skip formal proofs (focus on intuition and implementation)
- Assume prerequisites (don't teach basics)
- Chapters should be somewhat self-sufficient (can read out of order)

Set reader_mode to "practitioner" in your output.

For the vision:
1. CORE THESIS: What capability will readers gain? Be specific about what they'll build.
2. READER JOURNEY: Before (can't build X) → After (can build X with confidence)
3. KEY THEMES: Focus on practical skills and implementation patterns
4. SCOPE: Exclude theoretical foundations that don't directly enable building
5. UNIQUE ANGLE: What practical approach makes this different?
6. PREREQUISITES: What should practitioners already know?"""

ACADEMIC_VISION_INSTRUCTIONS = """Generate an ACADEMIC-focused book vision.

READER MODE: ACADEMIC (Evolution-Centric Organization)
- Readers want to UNDERSTAND deeply
- Organize around EVOLUTION of ideas (how did we get here?)
- Include historical context (intellectual lineage matters)
- Include formal proofs where they illuminate
- Teach prerequisites as needed (build from foundations)
- Chapters should be sequential (build on each other)

Set reader_mode to "academic" in your output.

For the vision:
1. CORE THESIS: What deep insight will readers understand? Be specific about the intellectual contribution.
2. READER JOURNEY: Before (misconceptions) → After (deep understanding)
3. KEY THEMES: Focus on theoretical foundations and conceptual development
4. SCOPE: Include necessary foundations, exclude tangential applications
5. UNIQUE ANGLE: What theoretical perspective makes this different?
6. PREREQUISITES: What background is assumed vs taught?"""

HYBRID_VISION_INSTRUCTIONS = """Generate a HYBRID book vision balancing theory and practice.

READER MODE: HYBRID (Balanced Organization)
- Readers want BOTH understanding AND practical skills
- Balance theoretical depth with practical application
- Include enough theory to understand deeply
- Include enough practice to apply knowledge
- Some chapters sequential (foundational), some self-sufficient (applied)

Set reader_mode to "hybrid" in your output.

For the vision:
1. CORE THESIS: What understanding enables what capability?
2. READER JOURNEY: Before (gap in both theory and practice) → After (integrated knowledge)
3. KEY THEMES: Balance foundational concepts with practical applications
4. SCOPE: Include core theory AND key applications
5. UNIQUE ANGLE: How does this integrate theory and practice uniquely?
6. PREREQUISITES: What's assumed, what's taught, what's optional?"""


def format_book_vision(vision: dict) -> str:
    """Format book vision as readable text for use in prompts."""
    reader_mode = vision.get('reader_mode', 'academic')
    mode_description = {
        'practitioner': 'Problem-Centric (focus on building/implementing)',
        'academic': 'Evolution-Centric (focus on understanding/research)',
        'hybrid': 'Hybrid (balance of theory and practice)',
    }.get(reader_mode, reader_mode)

    return f"""BOOK VISION
===========

READER MODE: {mode_description}

CORE THESIS:
{vision.get('core_thesis', 'N/A')}

READER JOURNEY:
{vision.get('reader_journey', 'N/A')}

KEY THEMES (concepts MUST cover these):
{chr(10).join(f"- {theme}" for theme in vision.get('key_themes', []))}

SCOPE BOUNDARIES (what NOT to include):
{vision.get('scope_boundaries', 'N/A')}

UNIQUE ANGLE:
{vision.get('unique_angle', 'N/A')}

PREREQUISITE KNOWLEDGE:
{vision.get('prerequisite_knowledge', 'N/A')}
"""


async def generate_book_vision(
    topic_data: dict,
    language_model,
    output_dir: str = None,
    research_context: str = None,
    reader_mode_override: str = None,
) -> dict:
    """
    Generate the book vision before concept generation.

    Uses synalinks.Branch to:
    1. Decide reader_mode (practitioner/academic/hybrid) based on goal
    2. Execute the appropriate mode-specific vision generator
    3. Only the selected branch runs; others return None

    The vision establishes:
    - Reader mode (determines organization logic throughout)
    - Core thesis (the one key insight)
    - Reader journey (before/after transformation)
    - Key themes (must be covered)
    - Scope boundaries (what to exclude)
    - Unique angle (differentiation)
    - Prerequisites (what's assumed)

    Args:
        topic_data: Dict with topic, goal, book_name, audience
        language_model: The LLM to use
        output_dir: Optional directory to save outputs
        research_context: Optional research context for vision
        reader_mode_override: Optional override for reader mode (bypasses Branch decision)

    Returns:
        Dictionary with book vision data including reader_mode
    """
    # Check for existing vision
    if output_dir and output_exists(output_dir, "00_book_vision.json"):
        existing = load_json_from_file(output_dir, "00_book_vision.json")
        if existing:
            logger.info("Loaded existing book vision")
            return existing

    logger.info("Generating book vision with reader mode decision...")

    input_data = BookVisionInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        audience=topic_data.get("audience", "technical readers")
    )

    # Add research context to instructions if available
    research_prefix = ""
    if research_context:
        research_prefix = f"""You have access to recent research findings about this field.
Use this knowledge to inform your vision - ensure the book covers cutting-edge developments.

RECENT RESEARCH SUMMARY:
{research_context}

---

"""

    # If reader_mode is overridden, use a single Generator with the appropriate instructions
    if reader_mode_override:
        logger.info(f"Reader mode override: {reader_mode_override}")
        mode_instructions = {
            "practitioner": PRACTITIONER_VISION_INSTRUCTIONS,
            "academic": ACADEMIC_VISION_INSTRUCTIONS,
            "hybrid": HYBRID_VISION_INSTRUCTIONS,
        }.get(reader_mode_override, ACADEMIC_VISION_INSTRUCTIONS)

        generator = synalinks.Generator(
            data_model=BookVision,
            language_model=language_model,
            temperature=1.0,
            instructions=research_prefix + mode_instructions,
        )
        result = await generator(input_data)
        result_dict = result.get_json() if result else {}
        result_dict['reader_mode'] = reader_mode_override

    else:
        # Use synalinks.Branch to decide reader mode AND generate appropriate vision
        # Branch internally makes the decision and only executes the selected branch
        (practitioner_vision, academic_vision, hybrid_vision) = await synalinks.Branch(
            question="""Based on the book's goal, topic, and audience, what type of organization is most appropriate?

PRACTITIONER: Goal emphasizes "build", "implement", "use", "production", "hands-on", "deploy", "code", "develop", "create", "tutorial", "guide"
→ Readers want to DO something practical. Organize around problems and capabilities.

ACADEMIC: Goal emphasizes "understand", "research", "comprehensive", "theory", "foundations", "survey", "formal", "proof", "rigorous"
→ Readers want to UNDERSTAND deeply. Organize around evolution of ideas.

HYBRID: Goal has BOTH practical AND theoretical emphasis, or explicitly mentions both
→ Balance of theory and practice.

If the intent is unclear, choose "academic" (more comprehensive coverage).""",
            labels=["practitioner", "academic", "hybrid"],
            branches=[
                synalinks.Generator(
                    data_model=BookVision,
                    language_model=language_model,
                    temperature=1.0,
                    instructions=research_prefix + PRACTITIONER_VISION_INSTRUCTIONS,
                ),
                synalinks.Generator(
                    data_model=BookVision,
                    language_model=language_model,
                    temperature=1.0,
                    instructions=research_prefix + ACADEMIC_VISION_INSTRUCTIONS,
                ),
                synalinks.Generator(
                    data_model=BookVision,
                    language_model=language_model,
                    temperature=1.0,
                    instructions=research_prefix + HYBRID_VISION_INSTRUCTIONS,
                ),
            ],
            language_model=language_model,
            temperature=1.0,
            return_decision=False,
            inject_decision=False,
        )(input_data)

        # Merge branches - only one should be non-None
        # Note: Python's | operator doesn't work on None, so check explicitly
        if practitioner_vision is not None:
            final_vision = practitioner_vision
        elif academic_vision is not None:
            final_vision = academic_vision
        elif hybrid_vision is not None:
            final_vision = hybrid_vision
        else:
            final_vision = None

        if final_vision is None:
            logger.warning("All vision branches returned None, using fallback")
            # Fallback to academic mode
            fallback_gen = synalinks.Generator(
                data_model=BookVision,
                language_model=language_model,
                temperature=1.0,
                instructions=research_prefix + ACADEMIC_VISION_INSTRUCTIONS,
            )
            final_vision = await fallback_gen(input_data)

        result_dict = final_vision.get_json() if final_vision else {}

    # Save the vision
    if output_dir:
        save_json_to_file(output_dir, "00_book_vision.json", result_dict)
        save_to_file(output_dir, "00_book_vision.txt", format_book_vision(result_dict))

    reader_mode = result_dict.get('reader_mode', 'academic')
    logger.info(f"Generated book vision with reader_mode={reader_mode}, {len(result_dict.get('key_themes', []))} key themes")

    return result_dict


async def check_vision_alignment(
    vision: dict,
    concepts: list,
    language_model
) -> tuple:
    """
    Check if generated concepts align with the book vision.

    Args:
        vision: The book vision dict
        concepts: List of concept names
        language_model: The LLM to use

    Returns:
        Tuple of (aligned: bool, missing_themes: list, out_of_scope: list)
    """
    from .models import CoverageCheckInput, CoverageAssessment

    themes = vision.get("key_themes", [])
    scope_boundaries = vision.get("scope_boundaries", "")

    concepts_text = "\n".join(f"- {c}" for c in concepts)
    themes_text = "\n".join(f"- {t}" for t in themes)

    input_data = CoverageCheckInput(
        topic=vision.get("core_thesis", ""),
        goal=f"""The book MUST cover these key themes:
{themes_text}

The book should NOT cover (out of scope):
{scope_boundaries}""",
        current_concepts=concepts_text
    )

    generator = synalinks.Generator(
        data_model=CoverageAssessment,
        language_model=language_model,
        temperature=1.0,
        instructions="""Check if concepts align with the book's vision.

1. THEME COVERAGE: Does every key theme have at least one concept covering it?
2. SCOPE VIOLATION: Are any concepts outside the stated scope boundaries?
3. FOCUS: Are there concepts that don't connect to any key theme?

Be strict: concepts should serve the vision, not sprawl beyond it."""
    )

    result = await generator(input_data)
    if result is None:
        return (True, [], [])

    data = result.get_json()
    return (
        data.get("coverage_adequate", True),
        data.get("missing_topics", []),
        data.get("covered_topics", [])
    )


# =============================================================================
# Informed Vision (Post-Research Update)
# =============================================================================

async def update_vision_with_research(
    original_vision: dict,
    research_manager,
    final_outline: dict,
    topic_data: dict,
    language_model,
    output_dir: str = None,
) -> dict:
    """
    Update the book vision with research insights.

    This creates an "Informed Vision" that incorporates:
    - Specific papers that are central to the topic
    - The actual landscape of the field (not just LLM priors)
    - What's truly cutting-edge vs established
    - Key insights research revealed

    This informed vision guides writing to reference actual papers,
    not generic concepts.

    Args:
        original_vision: The original BookVision dict
        research_manager: ResearchManager with parsed research
        final_outline: The research-informed outline
        topic_data: Dict with topic, goal, book_name
        language_model: The LLM to use
        output_dir: Optional directory to save outputs

    Returns:
        Dictionary with InformedVision data
    """
    # Check for existing informed vision
    if output_dir and output_exists(output_dir, "00_informed_vision.json"):
        existing = load_json_from_file(output_dir, "00_informed_vision.json")
        if existing:
            logger.info("Loaded existing informed vision")
            return existing

    logger.info("Updating vision with research insights...")

    # Format research findings
    papers = research_manager.get_all_papers() if research_manager else []
    papers_text = "\n".join([
        f"- {p.get('title', 'Unknown')} ({p.get('authors', 'Unknown')}, {p.get('year', 'N/A')}): {p.get('significance', 'N/A')}"
        for p in papers[:15]  # Top 15 papers
    ])

    themes = research_manager.get_themes() if research_manager else []
    themes_text = "\n".join(f"- {t}" for t in themes)

    research_summary = research_manager.summary if research_manager else ""

    # Format outline summary
    outline_chapters = []
    if isinstance(final_outline, dict) and 'chapters' in final_outline:
        # Research-informed outline format
        for ch in final_outline.get('chapters', []):
            outline_chapters.append(f"- {ch.get('chapter_name', 'Unknown')} ({ch.get('role', 'N/A')})")
    elif isinstance(final_outline, dict) and 'concepts' in final_outline:
        # Standard outline format
        for ch in final_outline.get('concepts', []):
            outline_chapters.append(f"- {ch.get('concept', 'Unknown')}")
    outline_text = "\n".join(outline_chapters)

    input_data = InformedVisionInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        original_vision=format_book_vision(original_vision),
        research_summary=research_summary,
        research_papers=papers_text,
        final_outline_summary=outline_text
    )

    generator = synalinks.Generator(
        data_model=InformedVision,
        language_model=language_model,
        temperature=1.0,
        instructions="""Update the book vision with specific insights from research.

Based on the research findings, determine:

1. KEY_PAPERS: Which specific papers are central to this book's topic?
   List the 5-10 most important papers that MUST be referenced.

2. ACTUAL_LANDSCAPE: What is the real landscape of this field?
   Not generic knowledge, but what research revealed about current state.

3. CENTRAL_METHODS: What key methods/frameworks must the book cover?
   Be specific - name actual techniques, not generic categories.

4. CUTTING_EDGE_INSIGHTS: What's truly cutting-edge vs established?
   Help the author distinguish between foundational and frontier content.

5. UPDATED_SCOPE: How should scope be refined based on research?
   What should be added or removed from the original scope?

This informed vision will guide writing to reference REAL discoveries,
not generic concepts. Be specific and concrete."""
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    # Merge with original vision
    informed_vision = {
        **original_vision,
        "informed": result_dict,
    }

    # Save the informed vision
    if output_dir:
        save_json_to_file(output_dir, "00_informed_vision.json", informed_vision)
        save_to_file(output_dir, "00_informed_vision.txt", format_informed_vision(informed_vision))

    logger.info(f"Generated informed vision with {len(result_dict.get('key_papers', []))} key papers")

    return informed_vision


def format_informed_vision(vision: dict) -> str:
    """Format informed vision as readable text."""
    base = format_book_vision(vision)

    informed = vision.get("informed", {})
    if not informed:
        return base

    return f"""{base}

=== RESEARCH-INFORMED UPDATES ===

KEY PAPERS:
{chr(10).join(f"- {p}" for p in informed.get('key_papers', []))}

ACTUAL LANDSCAPE:
{informed.get('actual_landscape', 'N/A')}

CENTRAL METHODS:
{chr(10).join(f"- {m}" for m in informed.get('central_methods', []))}

CUTTING-EDGE INSIGHTS:
{chr(10).join(f"- {i}" for i in informed.get('cutting_edge_insights', []))}

UPDATED SCOPE:
{informed.get('updated_scope', 'N/A')}
"""
