"""
Outline generation and reorganization.

This module handles the creation of the book's hierarchical outline
and its optional reorganization based on conceptual evolution.
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
)
from .utils import build_outline_text

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


async def generate_main_concepts(topic_input: Topic, language_model) -> list:
    """
    Generate and enrich main concepts using multi-branch approach.

    Returns:
        List of main concept names
    """
    # Multi-branch concept extraction (run in parallel via asyncio)
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
    merge_gen = synalinks.Generator(
        data_model=MergedConcepts,
        description="Deduplicate and consolidate concepts from all branches",
        language_model=language_model,
        temperature=1.0
    )
    merged_concepts = await merge_gen(topic_input & merged)

    # Enrichment phase
    enrichment_instructions = """Identify important main concepts that are MISSING.
Think about: FOUNDATIONAL, HISTORICAL, PRACTICAL, ADVANCED, CROSS-CUTTING, and METHODOLOGY concepts.
ONLY output concepts that are genuinely MISSING."""

    enrich_gen = synalinks.Generator(
        data_model=EnrichmentAdditions,
        language_model=language_model,
        temperature=1.0,
        instructions=enrichment_instructions
    )

    enrich1 = await enrich_gen(topic_input & merged_concepts)
    enrich2 = await enrich_gen(topic_input & merged_concepts)
    enrich3 = await enrich_gen(topic_input & merged_concepts)

    merged_enrichments = enrich1 & enrich2 & enrich3

    # Final merge
    final_gen = synalinks.Generator(
        data_model=MergedConcepts,
        language_model=language_model,
        temperature=1.0,
        instructions="Combine original concepts with enrichments. Deduplicate and order logically."
    )
    enriched = await final_gen(topic_input & merged_concepts & merged_enrichments)

    return enriched.get_json().get("main_concepts", [])


async def expand_to_hierarchy(topic_input: Topic, concepts: list, language_model) -> dict:
    """
    Expand main concepts to full 3-level hierarchy.

    Returns:
        The complete hierarchy dict
    """
    # Create combined input with topic and concepts
    concepts_data = MergedConcepts(
        thinking=["Expanding concepts to hierarchy"],
        main_concepts=concepts
    )

    combined_input = topic_input & concepts_data

    # Step 1: Generate subconcepts for each main concept
    hierarchy_gen = synalinks.Generator(
        data_model=HierarchicalConcepts,
        instructions="For each main concept provided, generate ALL relevant subconcepts that belong to that domain. Be comprehensive.",
        language_model=language_model,
        temperature=1.0
    )
    hierarchy = await hierarchy_gen(combined_input)

    # Step 2: Review and add missing
    review_gen = synalinks.Generator(
        data_model=HierarchicalConcepts,
        instructions="Review the provided concepts and subconcepts. Add any important main concepts that are missing, and add any missing subconcepts to existing concepts.",
        language_model=language_model,
        temperature=1.0
    )
    reviewed = await review_gen(topic_input & hierarchy)

    # Step 3: Expand to sub-subconcepts
    deep_gen = synalinks.Generator(
        data_model=DeepHierarchy,
        instructions="For each subconcept provided, generate ALL relevant sub-subconcepts. Be comprehensive.",
        language_model=language_model,
        temperature=1.0
    )
    deep = await deep_gen(topic_input & reviewed)

    # Step 4: Verify relevance
    verify_gen = synalinks.Generator(
        data_model=DeepHierarchy,
        instructions="Verify each concept is relevant to the book topic and goal. Remove off-topic items.",
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


async def generate_outline_with_coverage(topic_data: dict, language_model, max_coverage_attempts: int = 3) -> dict:
    """
    Generate outline with coverage checking loop.

    This ensures the generated concepts adequately cover all topics specified in the goal.

    Args:
        topic_data: Dict with topic, goal, book_name
        language_model: The LLM to use
        max_coverage_attempts: Max attempts to fix coverage (default 3)

    Returns:
        The complete hierarchy dict
    """
    topic_input = Topic(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"]
    )

    # Step 1: Generate initial main concepts
    logger.info("Generating main concepts...")
    concepts = await generate_main_concepts(topic_input, language_model)
    logger.info(f"Generated {len(concepts)} main concepts")

    # Step 2: Coverage check loop
    for attempt in range(max_coverage_attempts):
        logger.info(f"Checking coverage (attempt {attempt + 1}/{max_coverage_attempts})...")

        adequate, missing = await check_coverage(
            topic=topic_data["topic"],
            goal=topic_data["goal"],
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
                    goal=topic_data["goal"],
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
    hierarchy = await expand_to_hierarchy(topic_input, concepts, language_model)

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
