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
    ChaptersOverviewInput,
    ChaptersOverview,
    SingleChapterPlanInput,
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
        temperature=1.0,
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


async def generate_chapters_overview(
    topic_data: dict,
    outline_results: dict,
    book_plan: dict,
    language_model,
    output_dir: str,
    max_chapters: Optional[int] = None
) -> dict:
    """
    Stage 1: Generate a coherent overview of all chapters in one shot.

    This provides the "big picture" view of how chapters connect,
    which will be used as context for individual chapter planning.

    Returns:
        Dictionary with chapters overview data
    """
    # Check for existing overview
    if output_dir and output_exists(output_dir, "02_chapters_overview.json"):
        existing = load_json_from_file(output_dir, "02_chapters_overview.json")
        if existing:
            logger.info("Loaded existing chapters overview")
            return existing

    logger.info("Generating chapters overview (stage 1: coherence planning)...")

    outline_text = build_outline_text(outline_results)
    chapter_names = get_chapter_names(outline_results)

    if max_chapters:
        chapter_names = chapter_names[:max_chapters]

    book_plan_text = format_book_plan(book_plan)

    generator = synalinks.Generator(
        data_model=ChaptersOverview,
        language_model=language_model,
        temperature=1.0,
        instructions="""Generate a coherent overview of all chapters in this book.

Your task is to create a "birds-eye view" that shows how all chapters fit together.
This overview will guide detailed planning for each individual chapter.

For the narrative_flow:
- Describe the learning journey from first chapter to last
- Explain how concepts build upon each other
- Identify key transitions and turning points

For each chapter_brief:
- chapter_name: Use the EXACT chapter name provided (do not modify it)
- brief_role: 1-2 sentences on what this chapter accomplishes
- key_concepts: The main ideas introduced or developed
- builds_on: What prerequisite knowledge is needed (or "None - foundational chapter")
- leads_to: What this enables the reader to understand next

This overview ensures coherent cross-chapter planning."""
    )

    input_data = ChaptersOverviewInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        full_outline=outline_text,
        book_plan=book_plan_text,
        chapters="\n".join(chapter_names)
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    # Save the overview
    if output_dir:
        save_json_to_file(output_dir, "02_chapters_overview.json", result_dict)
        save_to_file(output_dir, "02_chapters_overview.txt", format_chapters_overview(result_dict))

    return result_dict


def format_chapters_overview(overview: dict) -> str:
    """Format chapters overview as readable text."""
    lines = ["CHAPTERS OVERVIEW", "=" * 50, ""]
    lines.append("NARRATIVE FLOW:")
    lines.append(overview.get("narrative_flow", "N/A"))
    lines.append("")
    lines.append("CHAPTER BRIEFS:")
    lines.append("-" * 40)

    for brief in overview.get("chapter_briefs", []):
        lines.append(f"\n{brief.get('chapter_name', 'Unknown')}:")
        lines.append(f"  Role: {brief.get('brief_role', 'N/A')}")
        lines.append(f"  Key concepts: {brief.get('key_concepts', 'N/A')}")
        lines.append(f"  Builds on: {brief.get('builds_on', 'N/A')}")
        lines.append(f"  Leads to: {brief.get('leads_to', 'N/A')}")

    return "\n".join(lines)


async def generate_single_chapter_plan(
    topic_data: dict,
    book_plan: dict,
    chapters_overview: dict,
    chapter_name: str,
    chapter_number: int,
    total_chapters: int,
    outline_text: str,
    language_model,
    output_dir: str
) -> dict:
    """
    Stage 2: Generate a detailed plan for a single chapter.

    Uses the chapters overview for coherence while focusing on one chapter.

    Returns:
        Dictionary with chapter plan data (matching ChapterPlan model)
    """
    from .utils import sanitize_filename

    safe_chapter = sanitize_filename(chapter_name)
    filename = f"02_chapter_plan_{chapter_number:02d}_{safe_chapter}.json"

    # Check for existing plan
    if output_dir and output_exists(output_dir, filename):
        existing = load_json_from_file(output_dir, filename)
        if existing:
            logger.info(f"Loaded existing plan for chapter {chapter_number}: {chapter_name}")
            return existing

    logger.info(f"Generating plan for chapter {chapter_number}/{total_chapters}: {chapter_name}")

    book_plan_text = format_book_plan(book_plan)
    overview_text = format_chapters_overview(chapters_overview)

    generator = synalinks.Generator(
        data_model=ChapterPlan,
        language_model=language_model,
        temperature=1.0,
        instructions="""Generate a detailed plan for this specific chapter.

You have access to the full chapters overview showing how all chapters connect.
Use this context to ensure your plan is coherent with the rest of the book.

For this chapter, provide:
- chapter_name: Use the EXACT chapter name provided (do not modify it)
- chapter_summary: 2-3 paragraphs detailing what this chapter covers
- role_in_book: How this chapter fits into the overall narrative
- connection_to_previous: Specific concepts/skills from prior chapters this builds on
- connection_to_next: What this chapter prepares the reader for

Be specific about content, not generic. Reference actual concepts from the outline."""
    )

    input_data = SingleChapterPlanInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        full_outline=outline_text,
        book_plan=book_plan_text,
        chapters_overview=overview_text,
        chapter_name=chapter_name,
        chapter_number=chapter_number,
        total_chapters=total_chapters
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    # Save the plan
    if output_dir:
        save_json_to_file(output_dir, filename, result_dict)

    return result_dict


async def generate_chapter_plans(
    topic_data: dict,
    outline_results: dict,
    book_plan: dict,
    language_model,
    output_dir: str,
    max_chapters: Optional[int] = None
) -> tuple:
    """
    Generate plans for all chapters using two-stage approach.

    Stage 1: Generate a coherent overview of all chapters (one-shot for coherence)
    Stage 2: Generate detailed plans for each chapter individually

    Args:
        max_chapters: If set, only plan this many chapters (for test mode)

    Returns:
        Tuple of (chapters_overview, chapter_plans_dict)
    """
    outline_text = build_outline_text(outline_results)
    chapter_names = get_chapter_names(outline_results)

    if max_chapters:
        chapter_names = chapter_names[:max_chapters]

    total_chapters = len(chapter_names)

    # ==========================================================================
    # STAGE 1: Generate chapters overview (one-shot for coherence)
    # ==========================================================================
    chapters_overview = await generate_chapters_overview(
        topic_data, outline_results, book_plan, language_model, output_dir, max_chapters
    )

    # ==========================================================================
    # STAGE 2: Generate detailed plans for each chapter individually
    # ==========================================================================
    # Check for existing combined plans file
    if output_dir and output_exists(output_dir, "02_chapter_plans.json"):
        existing = load_json_from_file(output_dir, "02_chapter_plans.json")
        if existing and len(existing.get("chapter_plans", [])) == total_chapters:
            logger.info("Loaded existing chapter plans")
            return chapters_overview, existing

    logger.info(f"Generating detailed plans for {total_chapters} chapters (stage 2)...")

    chapter_plans_list = []

    for i, chapter_name in enumerate(chapter_names, 1):
        chapter_plan = await generate_single_chapter_plan(
            topic_data=topic_data,
            book_plan=book_plan,
            chapters_overview=chapters_overview,
            chapter_name=chapter_name,
            chapter_number=i,
            total_chapters=total_chapters,
            outline_text=outline_text,
            language_model=language_model,
            output_dir=output_dir
        )
        chapter_plans_list.append(chapter_plan)

    # Combine into the expected format
    result_dict = {"chapter_plans": chapter_plans_list}

    # Save the combined plans
    if output_dir:
        save_json_to_file(output_dir, "02_chapter_plans.json", result_dict)

    return chapters_overview, result_dict


def get_chapter_plan_by_index(chapter_plans: dict, index: int) -> Optional[dict]:
    """Get a chapter plan by index (0-based)."""
    plans_list = chapter_plans.get("chapter_plans", [])
    if 0 <= index < len(plans_list):
        return plans_list[index]
    return None


async def generate_section_plans(
    topic_data: dict,
    book_plan: dict,
    chapters_overview: dict,
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
    chapters_overview_text = format_chapters_overview(chapters_overview)
    chapter_plan_text = format_chapter_plan(chapter_plan)

    sections = list(sections_with_subsections.keys())
    subsections_text = "\n".join([
        f"{section}:\n  - " + "\n  - ".join(subs)
        for section, subs in sections_with_subsections.items()
    ])

    generator = synalinks.Generator(
        data_model=ChapterSectionPlans,
        language_model=language_model,
        temperature=1.0,
        instructions="""Generate detailed plans for each section in this chapter.

You have access to the full book plan and chapters overview for context.
Use this to ensure sections connect well with the broader narrative.

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
        chapters_overview=chapters_overview_text,
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
        Tuple of (book_plan, chapters_overview, chapter_plans, all_section_plans, hierarchy)
    """
    # Generate book plan
    book_plan = await generate_book_plan(
        topic_data, outline_results, language_model, output_dir
    )

    # Generate chapter plans (two-stage: overview + individual plans)
    chapters_overview, chapter_plans = await generate_chapter_plans(
        topic_data, outline_results, book_plan, language_model, output_dir, max_chapters
    )

    # Extract hierarchy for section planning
    hierarchy = extract_hierarchy(outline_results)

    # Generate section plans for each chapter
    all_section_plans = {}
    chapter_names = get_chapter_names(outline_results)

    if max_chapters:
        chapter_names = chapter_names[:max_chapters]

    # With two-stage planning, chapter plans are generated per-chapter in order
    chapter_plans_list = chapter_plans.get("chapter_plans", [])

    for i, chapter_name in enumerate(chapter_names):
        # Get plan by index (plans are generated in order)
        chapter_plan = get_chapter_plan_by_index(chapter_plans, i)

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
                chapters_overview,
                chapter_plan,
                chapter_name,
                sections_with_subsections,
                language_model,
                output_dir
            )
            all_section_plans[chapter_name] = section_plans

    return book_plan, chapters_overview, chapter_plans, all_section_plans, hierarchy
