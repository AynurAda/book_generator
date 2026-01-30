"""
Hierarchical planning for book structure.

This module handles the generation of plans at three levels:
- Book plan (overall narrative arc)
- Chapter plans (each chapter's role and connections)
- Section plans (detailed section breakdowns)
"""

import logging
from typing import Optional

import synalinks

from .models import (
    BookPlanInput,
    BookPlan,
    ChapterPlansInput,
    AllChapterPlans,
    ChapterPlan,
    SectionPlansInput,
    ChapterSectionPlans,
    SectionPlan,
)
from .utils import (
    build_outline_text,
    get_chapter_names,
    extract_hierarchy,
    output_exists,
    load_json_from_file,
    save_to_file,
    save_json_to_file,
)

logger = logging.getLogger(__name__)


async def generate_book_plan(
    topic_data: dict,
    outline_results: dict,
    language_model,
    output_dir: str
) -> dict:
    """
    Generate the high-level book plan.

    Returns:
        Dictionary with book plan data
    """
    # Check for existing plan
    if output_dir and output_exists(output_dir, "02_book_plan.json"):
        existing = load_json_from_file(output_dir, "02_book_plan.json")
        if existing:
            logger.info("Loaded existing book plan")
            return existing

    logger.info("Generating book plan...")

    outline_text = build_outline_text(outline_results)

    generator = synalinks.Generator(
        data_model=BookPlan,
        language_model=language_model,
        instructions="""Create a comprehensive plan for the book.

The plan should:
- Provide a 2-3 paragraph overview of what the book covers
- Describe the narrative arc from beginning to end
- Explain how chapters connect and build upon each other
- Identify key themes that run throughout

This plan will guide all subsequent content generation."""
    )

    input_data = BookPlanInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        full_outline=outline_text
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    # Save the plan
    if output_dir:
        save_json_to_file(output_dir, "02_book_plan.json", result_dict)
        save_to_file(output_dir, "02_book_plan.txt", format_book_plan(result_dict))

    return result_dict


def format_book_plan(book_plan: dict) -> str:
    """Format book plan as readable text."""
    return f"""BOOK PLAN
=========

SUMMARY:
{book_plan.get('book_summary', 'N/A')}

NARRATIVE ARC:
{book_plan.get('narrative_arc', 'N/A')}

CHAPTER CONNECTIONS:
{book_plan.get('chapter_connections', 'N/A')}
"""


async def generate_chapter_plans(
    topic_data: dict,
    outline_results: dict,
    book_plan: dict,
    language_model,
    output_dir: str,
    max_chapters: Optional[int] = None
) -> dict:
    """
    Generate plans for all chapters.

    Args:
        max_chapters: If set, only plan this many chapters (for test mode)

    Returns:
        Dictionary with chapter plans
    """
    # Check for existing plans
    if output_dir and output_exists(output_dir, "02_chapter_plans.json"):
        existing = load_json_from_file(output_dir, "02_chapter_plans.json")
        if existing:
            logger.info("Loaded existing chapter plans")
            return existing

    logger.info("Generating chapter plans...")

    outline_text = build_outline_text(outline_results)
    chapter_names = get_chapter_names(outline_results)

    if max_chapters:
        chapter_names = chapter_names[:max_chapters]

    book_plan_text = format_book_plan(book_plan)

    generator = synalinks.Generator(
        data_model=AllChapterPlans,
        language_model=language_model,
        instructions="""Generate detailed plans for each chapter listed.

For each chapter, provide:
- A 2-3 paragraph summary of its content
- Its role in the overall book narrative
- How it connects to the previous chapter
- How it leads into the next chapter

Ensure chapters flow logically and build upon each other."""
    )

    input_data = ChapterPlansInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        full_outline=outline_text,
        book_plan=book_plan_text,
        chapters="\n".join(chapter_names)
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    # Save the plans
    if output_dir:
        save_json_to_file(output_dir, "02_chapter_plans.json", result_dict)

    return result_dict


def get_chapter_plan_by_name(chapter_plans: dict, chapter_name: str) -> Optional[dict]:
    """Get a specific chapter's plan by name."""
    plans_list = chapter_plans.get("chapter_plans", [])
    chapter_base = chapter_name.split(". ", 1)[-1] if ". " in chapter_name else chapter_name

    for plan in plans_list:
        plan_name = plan.get("chapter_name", "")
        plan_base = plan_name.split(". ", 1)[-1] if ". " in plan_name else plan_name

        if plan_base.lower() == chapter_base.lower():
            return plan
        if chapter_base.lower() in plan_name.lower() or plan_base.lower() in chapter_name.lower():
            return plan

    logger.warning(f"No plan found for chapter: {chapter_name}")
    return None


async def generate_section_plans(
    topic_data: dict,
    book_plan: dict,
    chapter_plan: dict,
    chapter_name: str,
    sections_with_subsections: dict,
    language_model,
    output_dir: str
) -> dict:
    """
    Generate plans for all sections within a chapter.

    Returns:
        Dictionary with section plans for the chapter
    """
    from .utils import sanitize_filename

    safe_chapter = sanitize_filename(chapter_name)
    filename = f"02_section_plans_{safe_chapter}.json"

    # Check for existing plans
    if output_dir and output_exists(output_dir, filename):
        existing = load_json_from_file(output_dir, filename)
        if existing:
            logger.info(f"Loaded existing section plans for {chapter_name}")
            return existing

    logger.info(f"Generating section plans for {chapter_name}...")

    book_plan_text = format_book_plan(book_plan)
    chapter_plan_text = format_chapter_plan(chapter_plan)

    sections = list(sections_with_subsections.keys())
    subsections_text = "\n".join([
        f"{section}:\n  - " + "\n  - ".join(subs)
        for section, subs in sections_with_subsections.items()
    ])

    generator = synalinks.Generator(
        data_model=ChapterSectionPlans,
        language_model=language_model,
        instructions="""Generate detailed plans for each section in this chapter.

For each section, provide:
- A summary of what the section covers
- Its role within the chapter
- An overview of how subsections connect

Ensure sections flow logically within the chapter narrative."""
    )

    input_data = SectionPlansInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        book_plan=book_plan_text,
        chapter_plan=chapter_plan_text,
        chapter_name=chapter_name,
        sections="\n".join(sections),
        subsections_by_section=subsections_text
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    # Save the plans
    if output_dir:
        save_json_to_file(output_dir, filename, result_dict)

    return result_dict


def format_chapter_plan(chapter_plan: dict) -> str:
    """Format a chapter plan as text."""
    if not chapter_plan:
        return "No chapter plan available."
    return f"""Chapter: {chapter_plan.get('chapter_name', 'Unknown')}
Summary: {chapter_plan.get('chapter_summary', 'N/A')}
Role: {chapter_plan.get('role_in_book', 'N/A')}
Previous: {chapter_plan.get('connection_to_previous', 'N/A')}
Next: {chapter_plan.get('connection_to_next', 'N/A')}"""


def get_section_plan_by_name(section_plans: dict, section_name: str) -> Optional[dict]:
    """Get a specific section's plan by name."""
    plans_list = section_plans.get("section_plans", [])
    section_base = section_name.split(" ", 1)[-1] if " " in section_name else section_name

    for plan in plans_list:
        plan_name = plan.get("section_name", "")
        plan_base = plan_name.split(" ", 1)[-1] if " " in plan_name else plan_name

        if plan_base.lower() == section_base.lower():
            return plan
        if section_base.lower() in plan_name.lower() or plan_base.lower() in section_name.lower():
            return plan

    return None


def format_section_plan(section_plan: dict) -> str:
    """Format a section plan as text."""
    if not section_plan:
        return "No section plan available."
    return f"""Section: {section_plan.get('section_name', 'Unknown')}
Summary: {section_plan.get('section_summary', 'N/A')}
Role: {section_plan.get('role_in_chapter', 'N/A')}
Subsections: {section_plan.get('subsections_overview', 'N/A')}"""


async def run_hierarchical_planning(
    topic_data: dict,
    outline_results: dict,
    language_model,
    output_dir: str,
    max_chapters: Optional[int] = None
) -> tuple:
    """
    Run the complete hierarchical planning process.

    Returns:
        Tuple of (book_plan, chapter_plans, all_section_plans, hierarchy)
    """
    # Generate book plan
    book_plan = await generate_book_plan(
        topic_data, outline_results, language_model, output_dir
    )

    # Generate chapter plans
    chapter_plans = await generate_chapter_plans(
        topic_data, outline_results, book_plan, language_model, output_dir, max_chapters
    )

    # Extract hierarchy for section planning
    hierarchy = extract_hierarchy(outline_results)

    # Generate section plans for each chapter
    all_section_plans = {}
    chapter_names = get_chapter_names(outline_results)

    if max_chapters:
        chapter_names = chapter_names[:max_chapters]

    for chapter_name in chapter_names:
        chapter_plan = get_chapter_plan_by_name(chapter_plans, chapter_name)

        # Get sections and subsections for this chapter
        chapter_sections = hierarchy.get(chapter_name, {})
        sections_with_subsections = {
            section: subsections
            for section, subsections in chapter_sections.items()
        }

        if sections_with_subsections:
            section_plans = await generate_section_plans(
                topic_data,
                book_plan,
                chapter_plan,
                chapter_name,
                sections_with_subsections,
                language_model,
                output_dir
            )
            all_section_plans[chapter_name] = section_plans

    return book_plan, chapter_plans, all_section_plans, hierarchy
