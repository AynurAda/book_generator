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
    ConceptWithSubconcepts,
    HierarchicalConcepts,
    SubconceptWithDetails,
    ConceptDeep,
    DeepHierarchy,
    OutlineReorganizationInput,
    ReorganizedOutline,
)
from .utils import build_outline_text

logger = logging.getLogger(__name__)


async def build_outline_pipeline(language_model) -> synalinks.Program:
    """
    Build the complete outline generation pipeline.

    This creates a multi-branch pipeline that:
    1. Extracts concepts from multiple branches (temperature=1.0)
    2. Merges and deduplicates concepts
    3. Enriches main concepts - adds any important missing ones
    4. Expands with subconcepts
    5. Reviews and enriches subconcepts
    6. Expands to sub-subconcepts
    7. Verifies relevance

    Returns:
        A synalinks Program for outline generation
    """
    inputs = synalinks.Input(data_model=Topic)

    # Use temperature > 0 to get diverse outputs from each branch
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

    branch5 = await synalinks.Generator(
        data_model=ConceptExtractor,
        language_model=language_model,
        temperature=1.0
    )(inputs)

    branch6 = await synalinks.Generator(
        data_model=ConceptExtractor,
        language_model=language_model,
        temperature=1.0
    )(inputs)

    branch7 = await synalinks.Generator(
        data_model=ConceptExtractor,
        language_model=language_model,
        temperature=1.0
    )(inputs)

    branch8 = await synalinks.Generator(
        data_model=ConceptExtractor,
        language_model=language_model,
        temperature=1.0
    )(inputs)

    # Merge all branches using & operator
    merged = branch1 & branch2 & branch3 & branch4 & branch5 & branch6 & branch7 & branch8

    # Final generator to deduplicate and consolidate the merged lists
    merged_concepts = await synalinks.Generator(
        data_model=MergedConcepts,
        description="Take all the concepts from the merged branches and create a comprehensive, deduplicated list of main concepts",
        language_model=language_model,
        temperature=1.0
    )(inputs & merged)

    # Review and enrich main concepts - add any important missing ones
    enriched_concepts = await synalinks.Generator(
        data_model=MergedConcepts,
        language_model=language_model,
        temperature=1.0,
        instructions="""Review the list of main concepts for this book topic.

Your task is to identify and ADD any important main concepts that are MISSING.

Think about:
1. FOUNDATIONAL concepts - Are the theoretical/mathematical foundations covered?
2. HISTORICAL concepts - Is the evolution/history of the field represented?
3. PRACTICAL concepts - Are real-world applications and use cases included?
4. ADVANCED concepts - Are cutting-edge or emerging topics covered?
5. CROSS-CUTTING concepts - Are important themes that span multiple areas included?
6. METHODOLOGY concepts - Are key methods, techniques, and approaches covered?

For the given topic and goal:
- What would an expert consider essential that might be missing?
- What would a comprehensive textbook include that isn't here?
- What concepts are prerequisites for understanding others?

Return the COMPLETE list including both the original concepts AND any new ones you add.
Do NOT remove any existing concepts - only ADD missing important ones."""
    )(inputs & merged_concepts)

    # Expand each main concept with its subconcepts
    hierarchy = await synalinks.Generator(
        data_model=HierarchicalConcepts,
        instructions="For each main concept provided, generate ALL relevant subconcepts that belong to that domain. Be comprehensive - include every important technique, method, tool, or topic that falls under the main concept. Do not limit the number.",
        language_model=language_model,
        temperature=1.0
    )(inputs & enriched_concepts)

    # Review and add any missing concepts
    reviewed = await synalinks.Generator(
        data_model=HierarchicalConcepts,
        instructions="Review the provided concepts and subconcepts. Add any important main concepts that are missing, and add any missing subconcepts to existing concepts. Return the complete enriched hierarchy.",
        language_model=language_model,
        temperature=1.0
    )(inputs & hierarchy)

    # Expand subconcepts with sub-subconcepts
    deep = await synalinks.Generator(
        data_model=DeepHierarchy,
        instructions="For each subconcept provided, generate ALL relevant sub-subconcepts that belong to that subdomain. Be comprehensive - include every concrete technique, method, algorithm, or specific topic. Do not limit the number.",
        language_model=language_model,
        temperature=1.0
    )(inputs & reviewed)

    # Verify relevance to the book topic and goal
    outputs = await synalinks.Generator(
        data_model=DeepHierarchy,
        instructions="Review the entire hierarchy and verify each concept, subconcept, and sub-subconcept is relevant to the book topic and goal. Remove any items that are off-topic, too generic, or not directly useful for the book. Keep only what truly belongs.",
        language_model=language_model,
        temperature=1.0
    )(inputs & deep)

    return synalinks.Program(
        inputs=inputs,
        outputs=outputs,
        name="verified_concept_extractor",
        description="Extract and verify three-level hierarchy of concepts for book writing",
    )


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
        Tuple of (reorganized_results, was_reorganized, reasoning)
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
            return outline_results, False, "Invalid reorganization - keeping original order"

        if set(chapter_order) != set(range(1, len(concepts_list) + 1)):
            logger.warning("Invalid chapter indices. Keeping original order.")
            return outline_results, False, "Invalid reorganization - keeping original order"

        # Reorder the concepts
        reordered_concepts = [concepts_list[i - 1] for i in chapter_order]
        reorganized_results = {"concepts": reordered_concepts}

        reasoning = result_dict.get("reasoning", "Reorganized based on conceptual evolution")
        logger.info(f"Outline reorganized: {reasoning}")

        return reorganized_results, True, reasoning
    else:
        reasoning = result_dict.get("reasoning", "Current order is optimal")
        logger.info(f"Keeping original order: {reasoning}")
        return outline_results, False, reasoning
