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
    3. Expands with subconcepts
    4. Reviews and enriches
    5. Expands to sub-subconcepts
    6. Verifies relevance

    Returns:
        A synalinks Program for outline generation
    """
    inputs = synalinks.Input(data_model=Topic)

    # Multi-branch concept extraction with high temperature for diversity
    branches = []
    for i in range(8):
        branch = await synalinks.Generator(
            data_model=ConceptExtractor,
            language_model=language_model,
            instructions="""You are designing the table of contents for a comprehensive book on the given topic.

Extract 10-15 main concepts that MUST be covered. Focus on:
- Core theoretical foundations
- Key techniques and methods
- Important applications
- Essential background knowledge

Be comprehensive but focused on the topic. Avoid generic concepts."""
        )(inputs, hint=f"Branch {i+1}: Generate a diverse set of concepts")
        branches.append(branch)

    # Merge all branches
    merged = synalinks.Concatenate()(branches)

    # Deduplicate and consolidate
    merged_concepts = await synalinks.Generator(
        data_model=MergedConcepts,
        language_model=language_model,
        instructions="""Consolidate the concepts from all branches into a single, deduplicated list.

- Merge similar concepts into broader categories
- Remove exact or near duplicates
- Keep 12-18 main concepts that comprehensively cover the topic
- Ensure logical grouping"""
    )(merged)

    # Expand each concept with subconcepts
    hierarchical = await synalinks.Generator(
        data_model=HierarchicalConcepts,
        language_model=language_model,
        instructions="""For each main concept, generate 3-5 specific subconcepts.

Subconcepts should be:
- Specific techniques, methods, or topics within the main concept
- Detailed enough to form a book section
- Logically organized within the concept"""
    )(merged_concepts)

    # Review and add missing concepts
    reviewed = await synalinks.Generator(
        data_model=HierarchicalConcepts,
        language_model=language_model,
        instructions="""Review the hierarchical concepts and add any missing important topics.

- Add concepts that are essential but were missed
- Add subconcepts where coverage is thin
- Ensure comprehensive coverage of the field
- Do NOT remove anything, only add"""
    )(hierarchical)

    # Expand to three-level hierarchy (sub-subconcepts)
    deep_hierarchy = await synalinks.Generator(
        data_model=DeepHierarchy,
        language_model=language_model,
        instructions="""Expand each subconcept with 3-7 specific sub-subconcepts.

Sub-subconcepts should be:
- Concrete, specific topics that can be explained in 2-3 paragraphs
- Building blocks for the book's content
- Properly scoped (not too broad or too narrow)"""
    )(reviewed)

    # Final relevance verification
    final = await synalinks.Generator(
        data_model=DeepHierarchy,
        language_model=language_model,
        instructions="""Verify the outline for relevance and completeness.

- Remove any off-topic or tangential items
- Remove items that are too generic or vague
- Ensure everything directly relates to the book's topic and goal
- Maintain the 3-level hierarchy structure"""
    )(deep_hierarchy)

    return synalinks.Program(inputs=inputs, outputs=final)


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
        instructions="""You are an expert at organizing educational content.

Analyze the book outline and determine if reorganizing chapters would better reflect:
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
