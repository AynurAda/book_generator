"""
Content generation for subsections and sections.

This module handles the generation of actual book content:
- Subsection content (explanations, analogies, examples)
- Section rewriting (combining subsections into coherent sections)
"""

import logging
from typing import List, Optional

import synalinks

from .models import SectionInput, SectionOutput, ChapterInput, ChapterOutput
from .utils import (
    sanitize_filename,
    output_exists,
    load_from_file,
    load_json_from_file,
    save_to_file,
    save_json_to_file,
    format_subsections_for_rewrite,
)
from .planning import format_book_plan, format_chapter_plan, format_section_plan, get_section_plan_by_name

logger = logging.getLogger(__name__)


async def generate_subsection(
    topic_data: dict,
    book_plan: dict,
    chapter_plan: dict,
    section_plan: dict,
    subsection_name: str,
    language_model,
    output_dir: str,
    subsection_num: int
) -> Optional[dict]:
    """
    Generate content for a single subsection.

    Returns:
        Dictionary with subsection content, or None if already exists
    """
    safe_name = sanitize_filename(subsection_name)
    txt_filename = f"03_subsection_{subsection_num:03d}_{safe_name}.txt"
    json_filename = f"03_subsection_{subsection_num:03d}_{safe_name}.json"

    # Check for existing content
    if output_dir and output_exists(output_dir, txt_filename):
        existing = load_json_from_file(output_dir, json_filename)
        if existing:
            logger.info(f"Loaded existing subsection: {subsection_name}")
            return existing

    logger.info(f"Generating subsection: {subsection_name}")

    generator = synalinks.Generator(
        data_model=SectionOutput,
        language_model=language_model,
        instructions="""Generate comprehensive content for this book subsection.

Your content should:
1. CONCEPT EXPLANATION:
   - Explain the core concepts clearly and thoroughly
   - Define key terms and their relationships
   - Build understanding progressively

2. ANALOGIES AND EXAMPLES:
   - Provide relatable analogies to clarify concepts
   - Include practical, real-world examples
   - Show how concepts apply in practice

Write in an engaging, educational tone. Be thorough but concise.
Do NOT include introductions or summaries - these will be added during section assembly."""
    )

    input_data = SectionInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        book_plan=format_book_plan(book_plan),
        chapter_plan=format_chapter_plan(chapter_plan),
        section_plan=format_section_plan(section_plan),
        current_subsection=subsection_name
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    # Save the content
    if output_dir:
        content = f"=== {subsection_name} ===\n\n"
        content += f"CONCEPT EXPLANATION:\n{result_dict.get('concept_explanation', '')}\n\n"
        content += f"ANALOGIES AND EXAMPLES:\n{result_dict.get('analogies_and_examples', '')}"

        save_to_file(output_dir, txt_filename, content)
        save_json_to_file(output_dir, json_filename, result_dict)

    return result_dict


async def generate_all_subsections(
    topic_data: dict,
    book_plan: dict,
    chapter_plans: dict,
    all_section_plans: dict,
    hierarchy: dict,
    language_model,
    output_dir: str,
    max_chapters: Optional[int] = None
) -> dict:
    """
    Generate content for all subsections in the book.

    Returns:
        Nested dictionary: chapter -> section -> [(subsection_name, content)]
    """
    from .planning import get_chapter_plan_by_name

    all_generated = {}
    subsection_counter = 1

    chapter_names = list(hierarchy.keys())
    if max_chapters:
        chapter_names = chapter_names[:max_chapters]

    for chapter_name in chapter_names:
        chapter_plan = get_chapter_plan_by_name(chapter_plans, chapter_name)
        section_plans = all_section_plans.get(chapter_name, {})
        chapter_sections = hierarchy.get(chapter_name, {})

        all_generated[chapter_name] = {}

        for section_name, subsections in chapter_sections.items():
            section_plan = get_section_plan_by_name(section_plans, section_name)
            section_content = []

            for subsection_name in subsections:
                content = await generate_subsection(
                    topic_data,
                    book_plan,
                    chapter_plan,
                    section_plan,
                    subsection_name,
                    language_model,
                    output_dir,
                    subsection_counter
                )

                if content:
                    formatted = (
                        f"{content.get('concept_explanation', '')}\n\n"
                        f"{content.get('analogies_and_examples', '')}"
                    )
                    section_content.append((subsection_name, formatted))

                subsection_counter += 1

            all_generated[chapter_name][section_name] = section_content

    return all_generated


async def rewrite_section(
    topic_data: dict,
    chapter_name: str,
    section_name: str,
    subsections_content: List[tuple],
    chapter_plan: dict,
    previous_summary: str,
    next_summary: str,
    intro_style: str,
    language_model
) -> str:
    """
    Rewrite a section by combining its subsections into coherent prose.

    Returns:
        The rewritten section content
    """
    logger.info(f"Rewriting section: {section_name}")

    generator = synalinks.Generator(
        data_model=ChapterOutput,
        language_model=language_model,
        instructions=f"""Rewrite the subsections into a single, coherent book section.

INTRODUCTION STYLE: {intro_style}

Your rewritten section should:
1. Begin with the specified introduction style
2. Flow naturally between topics
3. Maintain all key information from the subsections
4. Eliminate redundancy and repetition
5. Add smooth transitions between ideas
6. Create a clear narrative arc
7. End with a synthesis or forward reference

Write in flowing prose without bullet points or sub-headers within the section.
The section header (## Section Name) will be added separately."""
    )

    formatted_content = format_subsections_for_rewrite(subsections_content)

    input_data = ChapterInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        chapter_title=chapter_name,
        subsections_content=formatted_content,
        previous_chapter_summary=previous_summary or "This is the first section.",
        next_chapter_summary=next_summary or "This is the last section.",
        intro_style=intro_style
    )

    result = await generator(input_data)
    return result.get_json().get("chapter_content", "")


async def rewrite_sections(
    topic_data: dict,
    all_generated: dict,
    book_plan: dict,
    chapter_plans: dict,
    all_section_plans: dict,
    language_model,
    output_dir: str,
    intro_styles: List[str]
) -> List[tuple]:
    """
    Rewrite all sections into coherent chapters.

    Returns:
        List of (chapter_name, chapter_content_dict) tuples
    """
    from .planning import get_chapter_plan_by_name

    rewritten_chapters = []
    style_idx = 0

    for chapter_name, sections in all_generated.items():
        safe_chapter = sanitize_filename(chapter_name)
        chapter_filename = f"04_chapter_{safe_chapter}.txt"

        # Check for existing rewritten chapter
        if output_dir and output_exists(output_dir, chapter_filename):
            existing = load_from_file(output_dir, chapter_filename)
            if existing:
                logger.info(f"Loaded existing rewritten chapter: {chapter_name}")
                rewritten_chapters.append((chapter_name, {"chapter_content": existing}))
                continue

        logger.info(f"Rewriting chapter: {chapter_name}")

        chapter_plan = get_chapter_plan_by_name(chapter_plans, chapter_name)
        chapter_content_parts = []

        section_names = list(sections.keys())
        for i, (section_name, subsections) in enumerate(sections.items()):
            if not subsections:
                continue

            # Get context for transitions
            prev_summary = section_names[i-1] if i > 0 else ""
            next_summary = section_names[i+1] if i < len(section_names) - 1 else ""

            # Get intro style (rotating)
            intro_style = intro_styles[style_idx % len(intro_styles)]
            style_idx += 1

            section_content = await rewrite_section(
                topic_data,
                chapter_name,
                section_name,
                subsections,
                chapter_plan,
                prev_summary,
                next_summary,
                intro_style,
                language_model
            )

            # Add section header
            section_header = section_name.split(" ", 1)[-1] if " " in section_name else section_name
            chapter_content_parts.append(f"### {section_header}\n\n{section_content}")

        # Combine all sections
        full_chapter = "\n\n".join(chapter_content_parts)
        chapter_data = {"chapter_content": full_chapter}

        # Save the chapter
        if output_dir:
            save_to_file(output_dir, chapter_filename, full_chapter)

        rewritten_chapters.append((chapter_name, chapter_data))

    return rewritten_chapters
