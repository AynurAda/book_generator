"""
Outline generation and reorganization.

This module handles the creation of the book's hierarchical outline
and its optional reorganization based on conceptual evolution.

Key features:
- Vision-guided outline generation
- Research-informed outline generation (post-research)
- Role-tagged chapters for better critique
- Organization logic based on reader mode
"""

import logging
import synalinks

from .models import (
    Topic,
    ConceptExtractor,
    MergedConcepts,
    EnrichmentAdditions,
    ConceptWithSubconcepts,
    HierarchicalConcepts,
    SubconceptWithDetails,
    ConceptDeep,
    DeepHierarchy,
    OutlineReorganizationInput,
    ReorganizedOutline,
    CoverageCheckInput,
    CoverageAssessment,
    MissingConceptsAddition,
    ChapterPrioritizationInput,
    PrioritizedChapters,
    VisionGuidedConceptInput,
    # New research-informed models
    ReaderMode,
    ChapterRole,
    RoleTaggedChapter,
    ResearchInformedOutline,
    ResearchInformedOutlineInput,
    TaxonomyDetectionInput,
    TaxonomyDetectionOutput,
)
from .utils import build_outline_text, output_exists, load_json_from_file, save_json_to_file, save_to_file
from .vision import format_book_vision

logger = logging.getLogger(__name__)


async def check_coverage(
    topic: str,
    goal: str,
    concepts: list,
    language_model
) -> tuple:
    """
    Check if current concepts adequately cover the goal.

    Returns:
        Tuple of (coverage_adequate: bool, missing_topics: list)
    """
    concepts_text = "\n".join(f"- {c}" for c in concepts)

    input_data = CoverageCheckInput(
        topic=topic,
        goal=goal,
        current_concepts=concepts_text
    )

    generator = synalinks.Generator(
        data_model=CoverageAssessment,
        language_model=language_model,
        temperature=1.0,
        instructions="""Carefully analyze if the current concepts adequately cover what the goal specifies.

The goal describes what the book SHOULD cover. Compare each requirement in the goal against the concepts.

Be strict: if a topic mentioned in the goal is not clearly covered by any concept, it's MISSING.

Examples of missing coverage:
- Goal mentions "AUTOSAR" but no concept covers AUTOSAR → missing
- Goal mentions "real-time constraints" but no concept covers real-time → missing
- Goal mentions "hardware accelerators" but no concept covers hardware → missing"""
    )

    result = await generator(input_data)
    if result is None:
        return (True, [])  # Assume adequate if check fails

    data = result.get_json()
    return (data.get("coverage_adequate", True), data.get("missing_topics", []))


async def generate_missing_concepts(
    topic: str,
    goal: str,
    current_concepts: list,
    missing_topics: list,
    language_model
) -> list:
    """
    Generate concepts to cover the missing topics.

    Returns:
        List of new concept names
    """
    concepts_text = "\n".join(f"- {c}" for c in current_concepts)
    missing_text = "\n".join(f"- {t}" for t in missing_topics)

    input_data = CoverageCheckInput(
        topic=topic,
        goal=f"{goal}\n\n=== MISSING TOPICS TO COVER ===\n{missing_text}",
        current_concepts=concepts_text
    )

    generator = synalinks.Generator(
        data_model=MissingConceptsAddition,
        language_model=language_model,
        temperature=1.0,
        instructions="""Generate new main concepts to cover the missing topics.

Each new concept should:
- Directly address one or more of the missing topics
- Be at the same level as the existing main concepts (not too broad, not too narrow)
- Use clear, descriptive names

Do NOT repeat concepts that already exist."""
    )

    result = await generator(input_data)
    if result is None:
        return []

    return result.get_json().get("new_concepts", [])


async def generate_main_concepts(topic_input: Topic, language_model, book_vision: dict = None) -> list:
    """
    Generate and enrich main concepts using multi-branch approach.

    If book_vision is provided, concepts are generated with vision guidance
    to ensure alignment with the book's focus and key themes.

    Args:
        topic_input: Topic DataModel with topic, goal, book_name
        language_model: The LLM to use
        book_vision: Optional book vision dict to guide concept generation

    Returns:
        List of main concept names
    """
    # Build vision-guided instructions if vision is provided
    if book_vision:
        vision_text = format_book_vision(book_vision)
        vision_guidance = f"""
IMPORTANT: Generate concepts that align with this BOOK VISION:

{vision_text}

Your concepts MUST:
1. Cover ALL key themes listed in the vision
2. Stay WITHIN the scope boundaries (don't include out-of-scope topics)
3. Support the reader journey described
4. Align with the unique angle of this book

Do NOT generate concepts that fall outside the scope boundaries."""

        # Create vision-guided input
        vision_input = VisionGuidedConceptInput(
            topic=topic_input.topic,
            goal=topic_input.goal,
            book_name=topic_input.book_name,
            book_vision=vision_text
        )

        # Multi-branch concept extraction with vision guidance
        gen = synalinks.Generator(
            data_model=ConceptExtractor,
            language_model=language_model,
            temperature=1.0,
            instructions=vision_guidance
        )

        branch1 = await gen(vision_input)
        branch2 = await gen(vision_input)
        branch3 = await gen(vision_input)
        branch4 = await gen(vision_input)
    else:
        # Original behavior without vision
        gen = synalinks.Generator(
            data_model=ConceptExtractor,
            language_model=language_model,
            temperature=1.0
        )

        branch1 = await gen(topic_input)
        branch2 = await gen(topic_input)
        branch3 = await gen(topic_input)
        branch4 = await gen(topic_input)

    merged = branch1 & branch2 & branch3 & branch4

    # Merge and dedupe
    merge_instructions = "Deduplicate and consolidate concepts from all branches."
    if book_vision:
        themes = book_vision.get("key_themes", [])
        scope = book_vision.get("scope_boundaries", "")
        merge_instructions += f"""

IMPORTANT: Ensure the final list:
1. Covers these key themes: {', '.join(themes)}
2. Does NOT include concepts outside scope: {scope}
3. Orders concepts logically for the reader journey"""

    merge_gen = synalinks.Generator(
        data_model=MergedConcepts,
        description="Deduplicate and consolidate concepts from all branches",
        language_model=language_model,
        temperature=1.0,
        instructions=merge_instructions
    )

    if book_vision:
        vision_input = VisionGuidedConceptInput(
            topic=topic_input.topic,
            goal=topic_input.goal,
            book_name=topic_input.book_name,
            book_vision=format_book_vision(book_vision)
        )
        merged_concepts = await merge_gen(vision_input & merged)
    else:
        merged_concepts = await merge_gen(topic_input & merged)

    # Enrichment phase
    enrichment_instructions = """Identify important main concepts that are MISSING.
Think about: FOUNDATIONAL, HISTORICAL, PRACTICAL, ADVANCED, CROSS-CUTTING, and METHODOLOGY concepts.
ONLY output concepts that are genuinely MISSING."""

    if book_vision:
        themes = book_vision.get("key_themes", [])
        enrichment_instructions += f"""

CRITICAL: Check if these KEY THEMES from the book vision are covered:
{chr(10).join(f"- {t}" for t in themes)}

If any theme is NOT covered by existing concepts, add a concept for it.
Stay within the scope boundaries."""

    enrich_gen = synalinks.Generator(
        data_model=EnrichmentAdditions,
        language_model=language_model,
        temperature=1.0,
        instructions=enrichment_instructions
    )

    if book_vision:
        vision_input = VisionGuidedConceptInput(
            topic=topic_input.topic,
            goal=topic_input.goal,
            book_name=topic_input.book_name,
            book_vision=format_book_vision(book_vision)
        )
        enrich1 = await enrich_gen(vision_input & merged_concepts)
        enrich2 = await enrich_gen(vision_input & merged_concepts)
        enrich3 = await enrich_gen(vision_input & merged_concepts)
    else:
        enrich1 = await enrich_gen(topic_input & merged_concepts)
        enrich2 = await enrich_gen(topic_input & merged_concepts)
        enrich3 = await enrich_gen(topic_input & merged_concepts)

    merged_enrichments = enrich1 & enrich2 & enrich3

    # Final merge
    final_instructions = "Combine original concepts with enrichments. Deduplicate and order logically."
    if book_vision:
        final_instructions += """

Final check: Ensure ALL key themes are represented and no out-of-scope concepts remain."""

    final_gen = synalinks.Generator(
        data_model=MergedConcepts,
        language_model=language_model,
        temperature=1.0,
        instructions=final_instructions
    )

    if book_vision:
        vision_input = VisionGuidedConceptInput(
            topic=topic_input.topic,
            goal=topic_input.goal,
            book_name=topic_input.book_name,
            book_vision=format_book_vision(book_vision)
        )
        enriched = await final_gen(vision_input & merged_concepts & merged_enrichments)
    else:
        enriched = await final_gen(topic_input & merged_concepts & merged_enrichments)

    return enriched.get_json().get("main_concepts", [])


async def expand_to_hierarchy(
    topic_input: Topic,
    concepts: list,
    language_model,
    book_vision: dict = None
) -> dict:
    """
    Expand main concepts to full 3-level hierarchy.

    If book_vision is provided, the hierarchy is generated with
    vision guidance to ensure focus alignment.

    Args:
        topic_input: Topic DataModel
        concepts: List of main concept names
        language_model: The LLM to use
        book_vision: Optional vision dict for guidance

    Returns:
        The complete hierarchy dict
    """
    # Create combined input with topic and concepts
    concepts_data = MergedConcepts(
        thinking=["Expanding concepts to hierarchy"],
        main_concepts=concepts
    )

    combined_input = topic_input & concepts_data

    # Build vision guidance if provided
    vision_guidance = ""
    if book_vision:
        vision_guidance = f"""

VISION GUIDANCE:
- Core thesis: {book_vision.get('core_thesis', '')}
- Key themes: {', '.join(book_vision.get('key_themes', []))}
- Scope boundaries (EXCLUDE these): {book_vision.get('scope_boundaries', '')}

Ensure subconcepts align with the vision and stay within scope."""

    # Step 1: Generate subconcepts for each main concept
    hierarchy_gen = synalinks.Generator(
        data_model=HierarchicalConcepts,
        instructions=f"For each main concept provided, generate ALL relevant subconcepts that belong to that domain. Be comprehensive.{vision_guidance}",
        language_model=language_model,
        temperature=1.0
    )
    hierarchy = await hierarchy_gen(combined_input)

    # Step 2: Review and add missing
    review_instructions = "Review the provided concepts and subconcepts. Add any important main concepts that are missing, and add any missing subconcepts to existing concepts."
    if book_vision:
        themes = book_vision.get("key_themes", [])
        review_instructions += f"""

IMPORTANT: Ensure the hierarchy covers these key themes:
{chr(10).join(f"- {t}" for t in themes)}

Do NOT add concepts outside the scope boundaries."""

    review_gen = synalinks.Generator(
        data_model=HierarchicalConcepts,
        instructions=review_instructions,
        language_model=language_model,
        temperature=1.0
    )
    reviewed = await review_gen(topic_input & hierarchy)

    # Step 3: Expand to sub-subconcepts
    deep_instructions = "For each subconcept provided, generate ALL relevant sub-subconcepts. Be comprehensive."
    if book_vision:
        deep_instructions += f"""

Keep sub-subconcepts focused on the book's unique angle: {book_vision.get('unique_angle', '')}
Stay within scope boundaries."""

    deep_gen = synalinks.Generator(
        data_model=DeepHierarchy,
        instructions=deep_instructions,
        language_model=language_model,
        temperature=1.0
    )
    deep = await deep_gen(topic_input & reviewed)

    # Step 4: Verify relevance (stricter with vision)
    verify_instructions = "Verify each concept is relevant to the book topic and goal. Remove off-topic items."
    if book_vision:
        verify_instructions = f"""Verify each concept aligns with the book vision.

REMOVE any concept that:
1. Falls outside the scope boundaries: {book_vision.get('scope_boundaries', '')}
2. Does not connect to any key theme: {', '.join(book_vision.get('key_themes', []))}
3. Is not relevant to the core thesis: {book_vision.get('core_thesis', '')}

Keep the hierarchy FOCUSED."""

    verify_gen = synalinks.Generator(
        data_model=DeepHierarchy,
        instructions=verify_instructions,
        language_model=language_model,
        temperature=1.0
    )
    result = await verify_gen(topic_input & deep)

    return result.get_json()


async def build_outline_pipeline(language_model) -> synalinks.Program:
    """
    Build outline generation as a callable program.

    Note: This is kept for backwards compatibility but the actual generation
    now uses generate_outline_with_coverage() for better coverage checking.
    """
    inputs = synalinks.Input(data_model=Topic)

    branch1 = await synalinks.Generator(
        data_model=ConceptExtractor,
        language_model=language_model,
        temperature=1.0
    )(inputs)

    branch2 = await synalinks.Generator(
        data_model=ConceptExtractor,
        language_model=language_model,
        temperature=1.0
    )(inputs)

    branch3 = await synalinks.Generator(
        data_model=ConceptExtractor,
        language_model=language_model,
        temperature=1.0
    )(inputs)

    branch4 = await synalinks.Generator(
        data_model=ConceptExtractor,
        language_model=language_model,
        temperature=1.0
    )(inputs)

    merged = branch1 & branch2 & branch3 & branch4

    merged_concepts = await synalinks.Generator(
        data_model=MergedConcepts,
        description="Deduplicate and consolidate concepts",
        language_model=language_model,
        temperature=1.0
    )(inputs & merged)

    enrichment_instructions = """Identify important main concepts that are MISSING."""

    enrich1 = await synalinks.Generator(
        data_model=EnrichmentAdditions,
        language_model=language_model,
        temperature=1.0,
        instructions=enrichment_instructions
    )(inputs & merged_concepts)

    enrich2 = await synalinks.Generator(
        data_model=EnrichmentAdditions,
        language_model=language_model,
        temperature=1.0,
        instructions=enrichment_instructions
    )(inputs & merged_concepts)

    enrich3 = await synalinks.Generator(
        data_model=EnrichmentAdditions,
        language_model=language_model,
        temperature=1.0,
        instructions=enrichment_instructions
    )(inputs & merged_concepts)

    merged_enrichments = enrich1 & enrich2 & enrich3

    enriched_concepts = await synalinks.Generator(
        data_model=MergedConcepts,
        language_model=language_model,
        temperature=1.0,
        instructions="Combine and deduplicate all concepts"
    )(inputs & merged_concepts & merged_enrichments)

    hierarchy = await synalinks.Generator(
        data_model=HierarchicalConcepts,
        instructions="Generate subconcepts for each main concept",
        language_model=language_model,
        temperature=1.0
    )(inputs & enriched_concepts)

    reviewed = await synalinks.Generator(
        data_model=HierarchicalConcepts,
        instructions="Review and add missing concepts/subconcepts",
        language_model=language_model,
        temperature=1.0
    )(inputs & hierarchy)

    deep = await synalinks.Generator(
        data_model=DeepHierarchy,
        instructions="Generate sub-subconcepts for each subconcept",
        language_model=language_model,
        temperature=1.0
    )(inputs & reviewed)

    outputs = await synalinks.Generator(
        data_model=DeepHierarchy,
        instructions="Verify relevance and remove off-topic items",
        language_model=language_model,
        temperature=1.0
    )(inputs & deep)

    return synalinks.Program(
        inputs=inputs,
        outputs=outputs,
        name="verified_concept_extractor",
        description="Extract and verify three-level hierarchy of concepts for book writing",
    )


async def generate_outline_with_coverage(
    topic_data: dict,
    language_model,
    max_coverage_attempts: int = 3,
    book_vision: dict = None,
    research_context: str = None,
) -> dict:
    """
    Generate outline with coverage checking loop.

    If book_vision is provided, concepts are generated with vision guidance
    and coverage is checked against the vision's key themes.

    If research_context is provided, it's included in the coverage check
    to ensure cutting-edge topics are covered.

    Args:
        topic_data: Dict with topic, goal, book_name
        language_model: The LLM to use
        max_coverage_attempts: Max attempts to fix coverage (default 3)
        book_vision: Optional book vision dict to guide concept generation
        research_context: Optional research context for coverage checking

    Returns:
        The complete hierarchy dict
    """
    topic_input = Topic(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"]
    )

    # Step 1: Generate initial main concepts (with vision if provided)
    if book_vision:
        logger.info("Generating vision-guided main concepts...")
    else:
        logger.info("Generating main concepts...")

    concepts = await generate_main_concepts(topic_input, language_model, book_vision)
    logger.info(f"Generated {len(concepts)} main concepts")

    # Step 2: Coverage check loop
    # If we have a vision, check against key themes + goal
    # Otherwise, just check against goal
    check_goal = topic_data["goal"]
    if book_vision:
        themes = book_vision.get("key_themes", [])
        if themes:
            themes_text = "\n".join(f"- {t}" for t in themes)
            check_goal = f"""{topic_data["goal"]}

CRITICAL - The book MUST cover these KEY THEMES from the vision:
{themes_text}"""

    # Add research context to coverage check if available
    if research_context:
        check_goal = f"""{check_goal}

CUTTING-EDGE RESEARCH - The book should also address these recent developments:
{research_context}"""

    for attempt in range(max_coverage_attempts):
        logger.info(f"Checking coverage (attempt {attempt + 1}/{max_coverage_attempts})...")

        adequate, missing = await check_coverage(
            topic=topic_data["topic"],
            goal=check_goal,
            concepts=concepts,
            language_model=language_model
        )

        if adequate:
            logger.info("Coverage check: PASSED")
            break
        else:
            logger.info(f"Coverage check: MISSING TOPICS - {missing}")

            if attempt < max_coverage_attempts - 1:
                # Generate concepts for missing topics
                new_concepts = await generate_missing_concepts(
                    topic=topic_data["topic"],
                    goal=check_goal,
                    current_concepts=concepts,
                    missing_topics=missing,
                    language_model=language_model
                )

                if new_concepts:
                    logger.info(f"Adding {len(new_concepts)} new concepts: {new_concepts}")
                    concepts.extend(new_concepts)
                else:
                    logger.warning("No new concepts generated, stopping coverage loop")
                    break
            else:
                logger.warning("Max coverage attempts reached, proceeding with current concepts")

    # Step 3: Expand to full hierarchy
    logger.info("Expanding concepts to full hierarchy...")
    hierarchy = await expand_to_hierarchy(topic_input, concepts, language_model, book_vision)

    return hierarchy


async def reorganize_outline(
    topic_data: dict,
    outline_results: dict,
    language_model
) -> tuple:
    """
    Analyze and potentially reorganize the outline for better conceptual flow.

    Args:
        topic_data: Dictionary with topic, goal, book_name
        outline_results: The generated outline hierarchy
        language_model: The language model to use

    Returns:
        Tuple of (reorganized_results, was_reorganized, reasoning, analysis_dict)
    """
    logger.info("Analyzing outline for conceptual/temporal reorganization...")

    outline_text = build_outline_text(outline_results)

    generator = synalinks.Generator(
        data_model=ReorganizedOutline,
        language_model=language_model,
        temperature=1.0,
        instructions="""You are an expert at organizing educational content to follow the natural evolution of ideas.

Analyze the given book outline and determine if reorganizing the chapters would better reflect:
1. Historical/temporal evolution (how concepts developed over time)
2. Conceptual progression (foundational concepts before advanced ones)
3. Logical dependencies (concepts that build on each other)

If reorganization makes sense:
- Identify the optimal order for a coherent narrative
- Ensure prerequisites come before dependent concepts
- Maintain flow from simpler to more complex

If the current order is already optimal:
- Set should_reorganize to False
- Explain why the current order works

IMPORTANT:
- Do NOT lose any chapters - include ALL indices in chapter_order
- Use 1-based indexing (first chapter is 1)
- The chapter_order list must have the same length as the number of chapters"""
    )

    input_data = OutlineReorganizationInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        current_outline=outline_text
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    if result_dict.get("should_reorganize", False):
        chapter_order = result_dict.get("chapter_order", [])
        concepts_list = outline_results.get("concepts", [])

        # Validate chapter order
        if len(chapter_order) != len(concepts_list):
            logger.warning(
                f"Invalid chapter_order length ({len(chapter_order)} vs {len(concepts_list)}). "
                "Keeping original order."
            )
            return outline_results, False, "Invalid reorganization - keeping original order", result_dict

        if set(chapter_order) != set(range(1, len(concepts_list) + 1)):
            logger.warning("Invalid chapter indices. Keeping original order.")
            return outline_results, False, "Invalid reorganization - keeping original order", result_dict

        # Reorder the concepts
        reordered_concepts = [concepts_list[i - 1] for i in chapter_order]
        reorganized_results = {"concepts": reordered_concepts}

        reasoning = result_dict.get("reasoning", "Reorganized based on conceptual evolution")
        logger.info(f"Outline reorganized: {reasoning}")

        return reorganized_results, True, reasoning, result_dict
    else:
        reasoning = result_dict.get("reasoning", "Current order is optimal")
        logger.info(f"Keeping original order: {reasoning}")
        return outline_results, False, reasoning, result_dict


def outline_needs_subsubconcepts(outline: dict) -> bool:
    """Check if the outline is missing subsubconcepts."""
    for concept in outline.get("concepts", []):
        for subconcept in concept.get("subconcepts", []):
            if subconcept.get("subsubconcepts"):
                return False  # At least one has content
    return True  # All empty


async def generate_subsubconcepts(
    topic_data: dict,
    outline: dict,
    language_model
) -> dict:
    """
    Generate subsubconcepts for an outline that doesn't have them.

    This is used when a default outline is provided with only
    concepts and subconcepts.

    Args:
        topic_data: Dict with topic, goal, book_name
        outline: The outline with concepts and subconcepts
        language_model: The LLM to use

    Returns:
        The outline with subsubconcepts populated
    """
    logger.info("Generating subsubconcepts for outline...")

    topic_input = Topic(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"]
    )

    # Convert outline to HierarchicalConcepts format for the generator
    hierarchical_concepts = []
    for concept_data in outline.get("concepts", []):
        hierarchical_concepts.append(ConceptWithSubconcepts(
            concept=concept_data.get("concept", ""),
            subconcepts=[s.get("subconcept", "") for s in concept_data.get("subconcepts", [])],
            thinking=["Expanding subconcepts to subsubconcepts"]
        ))

    hierarchy_input = HierarchicalConcepts(
        thinking=["Generating subsubconcepts for provided outline"],
        concepts=hierarchical_concepts
    )

    # Generate sub-subconcepts
    deep_gen = synalinks.Generator(
        data_model=DeepHierarchy,
        instructions="""For each subconcept provided, generate 3-5 specific sub-subconcepts that would be covered in that section.

Sub-subconcepts should be:
- Specific enough to be a single topic/concept
- Comprehensive coverage of the subconcept
- Logically ordered (foundational before advanced)
- Relevant to the book's topic and goal""",
        language_model=language_model,
        temperature=1.0
    )
    deep = await deep_gen(topic_input & hierarchy_input)

    # Verify relevance
    verify_gen = synalinks.Generator(
        data_model=DeepHierarchy,
        instructions="Verify each sub-subconcept is relevant to the book topic and goal. Remove off-topic items.",
        language_model=language_model,
        temperature=1.0
    )
    result = await verify_gen(topic_input & deep)

    logger.info("Subsubconcepts generated successfully")
    return result.get_json()


async def prioritize_chapters(
    topic_data: dict,
    outline: dict,
    num_chapters: int,
    focus: str,
    language_model
) -> dict:
    """
    Select the most important chapters based on goal, audience, and focus.

    Args:
        topic_data: Dict with topic, goal, book_name, audience
        outline: The full outline with all chapters
        num_chapters: Number of chapters to select
        focus: Specific focus areas to prioritize
        language_model: The LLM to use

    Returns:
        Filtered outline with only the selected chapters
    """
    logger.info(f"Prioritizing {num_chapters} chapters from {len(outline.get('concepts', []))} available...")

    # Build chapter descriptions
    chapters_text = []
    for i, concept in enumerate(outline.get("concepts", []), 1):
        concept_name = concept.get("concept", "Unknown")
        subconcepts = [s.get("subconcept", "") for s in concept.get("subconcepts", [])]
        subconcepts_str = ", ".join(subconcepts[:5])  # First 5 for brevity
        if len(subconcepts) > 5:
            subconcepts_str += f", ... ({len(subconcepts)} total)"
        chapters_text.append(f"{i}. {concept_name}\n   Sections: {subconcepts_str}")

    available_chapters = "\n".join(chapters_text)

    input_data = ChapterPrioritizationInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        audience=topic_data.get("audience", "technical readers"),
        focus=focus or "general coverage",
        num_chapters=num_chapters,
        available_chapters=available_chapters
    )

    generator = synalinks.Generator(
        data_model=PrioritizedChapters,
        language_model=language_model,
        temperature=1.0,
        instructions=f"""Select exactly {num_chapters} chapters that are MOST important for the given goal, audience, and focus.

FOCUS AREAS: {focus}

Prioritization criteria:
1. RELEVANCE TO FOCUS: Chapters directly related to the focus areas are highest priority
2. FOUNDATIONAL VALUE: Include essential prerequisites for understanding the focus
3. PRACTICAL VALUE: Prefer chapters with practical applications for the audience
4. COHERENCE: Selected chapters should form a coherent learning path

IMPORTANT:
- Return exactly {num_chapters} chapter indices
- Use 1-based indexing (first chapter is 1)
- Order them by importance (most important first)
- Ensure the selection covers the focus areas comprehensively"""
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    selected_indices = result_dict.get("selected_indices", [])

    # Validate indices
    concepts_list = outline.get("concepts", [])
    valid_indices = [i for i in selected_indices if 1 <= i <= len(concepts_list)]

    if len(valid_indices) != num_chapters:
        logger.warning(f"Got {len(valid_indices)} valid indices, expected {num_chapters}. Using what we have.")

    # Build filtered outline
    selected_concepts = [concepts_list[i - 1] for i in valid_indices]

    # Log selection reasoning
    reasoning = result_dict.get("reasoning_per_chapter", [])
    logger.info(f"Selected {len(selected_concepts)} chapters:")
    for i, idx in enumerate(valid_indices):
        concept_name = concepts_list[idx - 1].get("concept", "Unknown")
        reason = reasoning[i] if i < len(reasoning) else "No reason provided"
        logger.info(f"  {i+1}. {concept_name} - {reason}")

    return {"concepts": selected_concepts}


# =============================================================================
# Research-Informed Outline Generation
# =============================================================================

PROBLEM_CENTRIC_INSTRUCTIONS = """Generate a PROBLEM-CENTRIC outline for PRACTITIONERS.

Organization Logic: Group by CAPABILITY/PROBLEM
- "What can I build with this?"
- "How do I solve this problem?"
- Chapters should be somewhat self-sufficient (can read out of order)

Example structure:
- Chapter: "Building Explainable AI Systems" (IMPLEMENTATION role)
  - Using Logic Tensor Networks
  - Using Scallop
  - Choosing your approach
- Chapter: "Adding Reasoning to LLMs" (DEEP_METHOD role)
  - Chain-of-Thought patterns
  - Tool use and function calling

Assign appropriate ROLES to chapters:
- PROBLEM_MOTIVATION: Why this matters
- ESSENTIAL_BACKGROUND: Just-enough theory
- LANDSCAPE: Survey of approaches
- DEEP_METHOD: Detailed key approach
- IMPLEMENTATION: Code and patterns
- CASE_STUDY: Real applications
- FRONTIERS: Open problems

CRITICAL - PAPER ASSIGNMENT:
For each chapter, you MUST populate the `relevant_papers` field with papers from the research.
- Look at the KEY PAPERS/METHODS list in the research findings
- Assign each paper to the ONE chapter where it's most relevant
- Each paper should appear in only ONE chapter (no duplicates)
- Use exact paper titles from the research
- This prevents repetition during content generation

IMPORTANT: Base structure on the RESEARCH FINDINGS provided."""

EVOLUTION_CENTRIC_INSTRUCTIONS = """Generate an EVOLUTION-CENTRIC outline for ACADEMICS.

Organization Logic: Group by TEMPORAL/CONCEPTUAL EVOLUTION
- "How did ideas develop?"
- "What's the intellectual lineage?"
- Chapters should build sequentially on each other

Example structure:
- Chapter: "The Symbolic AI Era (1956-1987)" (HISTORICAL role)
  - Logic programming
  - Expert systems
  - The knowledge acquisition bottleneck
- Chapter: "The Connectionist Revolution (1986-2012)" (HISTORICAL role)
  - Backpropagation and neural networks
  - The statistical learning paradigm
- Chapter: "The Neuro-Symbolic Synthesis (2018-present)" (LANDSCAPE role)
  - Differentiable logic
  - Neural theorem proving

Assign appropriate ROLES to chapters:
- PROBLEM_MOTIVATION: Why this matters
- PREREQUISITES: Formal background
- HISTORICAL: Field evolution
- LANDSCAPE: Survey of approaches
- DEEP_METHOD: Detailed key approach
- FORMAL_THEORY: Proofs
- FRONTIERS: Open problems

CRITICAL - PAPER ASSIGNMENT:
For each chapter, you MUST populate the `relevant_papers` field with papers from the research.
- Look at the KEY PAPERS/METHODS list in the research findings
- Assign each paper to the ONE chapter where it's most relevant
- Each paper should appear in only ONE chapter (no duplicates)
- Use exact paper titles from the research
- This prevents repetition during content generation

IMPORTANT: Base structure on the RESEARCH FINDINGS provided."""

TAXONOMY_BASED_INSTRUCTIONS = """Generate a TAXONOMY-BASED outline using categories from research.

The research revealed a natural taxonomy/categorization for this field.
Use that taxonomy as the organizing principle.

Example (if research revealed Kautz's 6 types for neuro-symbolic AI):
- Chapter: "Type 1: Symbolic[Neuro]" (DEEP_METHOD role)
- Chapter: "Type 2: Neuro|Symbolic" (DEEP_METHOD role)
- Chapter: "Type 3: Neuro:Symbolic→" (DEEP_METHOD role)
...

Assign appropriate ROLES to chapters based on their function.

CRITICAL - PAPER ASSIGNMENT:
For each chapter, you MUST populate the `relevant_papers` field with papers from the research.
- Look at the KEY PAPERS/METHODS list in the research findings
- Assign each paper to the ONE chapter where it's most relevant
- Each paper should appear in only ONE chapter (no duplicates)
- Use exact paper titles from the research
- This prevents repetition during content generation

IMPORTANT: The taxonomy should come from the RESEARCH FINDINGS.
Cite the source of the taxonomy in your output."""


async def generate_research_informed_outline(
    topic_data: dict,
    book_vision: dict,
    research_manager,
    initial_outline: dict,
    language_model,
    output_dir: str = None,
) -> dict:
    """
    Generate a NEW outline informed by research findings.

    This is the "real" outline - the initial outline exists only to
    generate research queries. This outline reflects what research discovered.

    Uses synalinks.Branch to select organization logic based on reader_mode:
    - practitioner → Problem-Centric
    - academic → Evolution-Centric
    - If research reveals a natural taxonomy → Taxonomy-Based

    Args:
        topic_data: Dict with topic, goal, book_name
        book_vision: The generated book vision (contains reader_mode)
        research_manager: ResearchManager with parsed research
        initial_outline: The draft outline used for research queries
        language_model: The LLM to use
        output_dir: Optional directory to save outputs

    Returns:
        ResearchInformedOutline dict with role-tagged chapters
    """
    # Check for existing research-informed outline
    if output_dir and output_exists(output_dir, "01_research_informed_outline.json"):
        existing = load_json_from_file(output_dir, "01_research_informed_outline.json")
        if existing:
            logger.info("Loaded existing research-informed outline")
            return existing

    logger.info("Generating research-informed outline...")

    reader_mode = book_vision.get('reader_mode', 'academic')

    # Build research context
    research_summary = research_manager.summary if research_manager else ""
    research_themes = research_manager.get_themes() if research_manager else []
    research_papers = research_manager.get_all_papers() if research_manager else []

    themes_text = "\n".join(f"- {t}" for t in research_themes)
    papers_text = "\n".join([
        f"- {p.get('title', 'Unknown')} ({p.get('year', 'N/A')}): {p.get('method', 'N/A')}"
        for p in research_papers[:20]
    ])

    # Summarize initial outline (if provided)
    initial_outline_text = ""
    if initial_outline:
        initial_chapters = []
        for concept in initial_outline.get('concepts', []):
            sections = [s.get('subconcept', '') for s in concept.get('subconcepts', [])]
            initial_chapters.append(f"- {concept.get('concept', '')}: {', '.join(sections[:3])}")
        initial_outline_text = "\n".join(initial_chapters)

    # Build research context block
    initial_outline_section = ""
    if initial_outline_text:
        initial_outline_section = f"""
INITIAL OUTLINE (for reference, can be restructured):
{initial_outline_text}
"""

    research_context = f"""
=== RESEARCH FINDINGS ===

FIELD SUMMARY:
{research_summary}

KEY THEMES DISCOVERED:
{themes_text}

KEY PAPERS/METHODS:
{papers_text}
{initial_outline_section}
=== END RESEARCH ===

Generate a NEW outline structure based on these research findings.
The structure should reflect what research actually discovered about the field.
"""

    input_data = ResearchInformedOutlineInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        reader_mode=reader_mode,
        initial_outline_summary=initial_outline_text,
        research_summary=research_summary,
        research_papers=papers_text,
        research_themes=themes_text,
    )

    # Check if research revealed a natural taxonomy using LLM decision
    has_taxonomy, taxonomy_name, taxonomy_categories = await detect_taxonomy_in_research(
        research_manager, language_model
    )

    if has_taxonomy:
        # Use taxonomy-based organization with discovered taxonomy info
        logger.info(f"Using taxonomy-based organization: {taxonomy_name}")
        categories_text = "\n".join(f"- {c}" for c in taxonomy_categories) if taxonomy_categories else "N/A"
        taxonomy_instructions = f"""
DISCOVERED TAXONOMY: {taxonomy_name}
CATEGORIES:
{categories_text}

Use these categories from the research as the organizing principle for chapters.
Each major category should typically become a chapter (or part of a chapter).

""" + TAXONOMY_BASED_INSTRUCTIONS

        generator = synalinks.Generator(
            data_model=ResearchInformedOutline,
            language_model=language_model,
            temperature=1.0,
            instructions=research_context + taxonomy_instructions,
        )
        result = await generator(input_data)
    else:
        # Use Branch to select organization based on reader_mode
        (practitioner_outline, academic_outline, hybrid_outline) = await synalinks.Branch(
            question=f"""The reader_mode is "{reader_mode}". Which organization logic should be used?

If reader_mode is "practitioner" → choose "problem_centric"
If reader_mode is "academic" → choose "evolution_centric"
If reader_mode is "hybrid" → choose "evolution_centric" (with practical examples)""",
            labels=["problem_centric", "evolution_centric", "hybrid"],
            branches=[
                synalinks.Generator(
                    data_model=ResearchInformedOutline,
                    language_model=language_model,
                    temperature=1.0,
                    instructions=research_context + PROBLEM_CENTRIC_INSTRUCTIONS,
                ),
                synalinks.Generator(
                    data_model=ResearchInformedOutline,
                    language_model=language_model,
                    temperature=1.0,
                    instructions=research_context + EVOLUTION_CENTRIC_INSTRUCTIONS,
                ),
                synalinks.Generator(
                    data_model=ResearchInformedOutline,
                    language_model=language_model,
                    temperature=1.0,
                    instructions=research_context + EVOLUTION_CENTRIC_INSTRUCTIONS,  # Hybrid uses evolution with practical focus
                ),
            ],
            language_model=language_model,
            temperature=1.0,
            return_decision=False,
            inject_decision=False,
        )(input_data)

        # Merge branches - only one should be non-None
        # Note: Python's | operator doesn't work on None, so check explicitly
        if practitioner_outline is not None:
            result = practitioner_outline
        elif academic_outline is not None:
            result = academic_outline
        elif hybrid_outline is not None:
            result = hybrid_outline
        else:
            result = None

    if result is None:
        logger.warning("Research-informed outline generation failed, using initial outline")
        return initial_outline

    result_dict = result.get_json()

    # Save the outline
    if output_dir:
        save_json_to_file(output_dir, "01_research_informed_outline.json", result_dict)
        save_to_file(output_dir, "01_research_informed_outline.txt",
                     format_research_informed_outline(result_dict))

    logger.info(f"Generated research-informed outline with {len(result_dict.get('chapters', []))} chapters")

    return result_dict


async def detect_taxonomy_in_research(
    research_manager,
    language_model
) -> tuple:
    """
    Detect if research revealed a natural taxonomy using LLM Branch.

    This replaces the Python keyword-matching approach with a proper
    LLM decision via synalinks.Branch.

    Args:
        research_manager: ResearchManager with parsed research
        language_model: The LLM to use for decision

    Returns:
        Tuple of (has_taxonomy: bool, taxonomy_name: str, categories: list)
    """
    if not research_manager:
        return (False, "N/A", [])

    # Build research context
    themes = research_manager.get_themes() if hasattr(research_manager, 'get_themes') else []
    summary = research_manager.summary if hasattr(research_manager, 'summary') else ""
    papers = research_manager.get_all_papers() if hasattr(research_manager, 'get_all_papers') else []

    themes_text = "\n".join(f"- {t}" for t in themes)
    papers_text = "\n".join([
        f"- {p.get('title', 'Unknown')} ({p.get('year', 'N/A')}): {p.get('method', 'N/A')}"
        for p in papers[:15]
    ])

    input_data = TaxonomyDetectionInput(
        research_summary=summary,
        research_themes=themes_text,
        research_papers=papers_text,
    )

    # Use LLM to detect taxonomy - this is more robust than keyword matching
    generator = synalinks.Generator(
        data_model=TaxonomyDetectionOutput,
        language_model=language_model,
        temperature=1.0,
        instructions="""Analyze the research findings to determine if they reveal a natural
taxonomy or categorization scheme that should organize the book structure.

A taxonomy is detected if:
1. Research explicitly mentions a classification (e.g., "Kautz's 6 types of neuro-symbolic AI")
2. There's a widely-accepted categorization scheme in the field
3. The research reveals clear, non-overlapping categories that practitioners use

A taxonomy is NOT detected if:
- Categories are just loose thematic groupings
- The classification is not widely adopted
- Categories overlap significantly

Examples of taxonomies:
- "Kautz's 6 types of neuro-symbolic AI" → has_taxonomy=True
- "Three paradigms of machine learning: supervised, unsupervised, reinforcement" → has_taxonomy=True
- "Various approaches to NLP" (no specific scheme) → has_taxonomy=False

Be conservative - only return has_taxonomy=True if there's a CLEAR, NAMED taxonomy."""
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    has_taxonomy = result_dict.get("has_taxonomy", False)
    taxonomy_name = result_dict.get("taxonomy_name", "N/A")
    categories = result_dict.get("taxonomy_categories", [])

    if has_taxonomy:
        logger.info(f"Taxonomy detected via LLM: {taxonomy_name} with {len(categories)} categories")
    else:
        logger.info("No taxonomy detected - will use reader_mode organization")

    return (has_taxonomy, taxonomy_name, categories)


def format_research_informed_outline(outline: dict) -> str:
    """Format research-informed outline as readable text."""
    lines = [
        "RESEARCH-INFORMED OUTLINE",
        "=" * 50,
        "",
        f"Organization Logic: {outline.get('organization_logic', 'N/A')}",
        f"Taxonomy Source: {outline.get('taxonomy_source', 'N/A')}",
        "",
        "CHAPTERS:",
        "-" * 40,
    ]

    for i, chapter in enumerate(outline.get('chapters', []), 1):
        lines.append(f"\n{i}. {chapter.get('chapter_name', 'Unknown')} [{chapter.get('role', 'N/A')}]")
        lines.append(f"   Key concepts: {', '.join(chapter.get('key_concepts', []))}")
        if chapter.get('relevant_papers'):
            lines.append(f"   Papers: {', '.join(chapter.get('relevant_papers', [])[:3])}")
        if chapter.get('sections'):
            for section in chapter.get('sections', []):
                lines.append(f"   - {section}")

    return "\n".join(lines)


def convert_research_outline_to_hierarchy(research_outline: dict) -> dict:
    """
    Convert ResearchInformedOutline to standard DeepHierarchy format.

    This allows the research-informed outline to be used by the rest of
    the pipeline which expects the standard format.

    Args:
        research_outline: ResearchInformedOutline dict

    Returns:
        Dict in DeepHierarchy format (concepts with subconcepts)
    """
    concepts = []

    for chapter in research_outline.get('chapters', []):
        concept_entry = {
            "concept": chapter.get('chapter_name', ''),
            "role": chapter.get('role', 'DEEP_METHOD'),
            "subconcepts": []
        }

        for section in chapter.get('sections', []):
            subconcept_entry = {
                "subconcept": section,
                "subsubconcepts": []  # Will be generated later
            }
            concept_entry["subconcepts"].append(subconcept_entry)

        concepts.append(concept_entry)

    return {"concepts": concepts}
