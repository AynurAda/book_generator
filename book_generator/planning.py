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
    # Plan critique models
    BookPlanCritiqueInput,
    BookPlanCritique,
    BookPlanRevisionInput,
    ChaptersOverviewCritiqueInput,
    ChaptersOverviewCritique,
    ChaptersOverviewRevisionInput,
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
    output_dir: str,
    book_vision: dict = None
) -> dict:
    """
    Generate the high-level book plan.

    Args:
        topic_data: Dict with topic, goal, book_name
        outline_results: The generated outline hierarchy
        language_model: The LLM to use
        output_dir: Directory to save outputs
        book_vision: Optional book vision for alignment guidance

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

    # Build vision-guided instructions if vision is provided
    instructions = """Create a comprehensive plan for the book.

The plan should:
- Provide a 2-3 paragraph overview of what the book covers
- Describe the narrative arc from beginning to end
- Explain how chapters connect and build upon each other
- Identify key themes that run throughout

This plan will guide all subsequent content generation."""

    if book_vision:
        vision_guidance = f"""

IMPORTANT: Align this plan with the BOOK VISION:

CORE THESIS: {book_vision.get('core_thesis', '')}

READER JOURNEY: {book_vision.get('reader_journey', '')}

KEY THEMES: {', '.join(book_vision.get('key_themes', []))}

UNIQUE ANGLE: {book_vision.get('unique_angle', '')}

Ensure the book plan:
1. Supports the core thesis throughout
2. Delivers the reader journey described
3. Emphasizes the key themes
4. Maintains the unique angle"""
        instructions += vision_guidance

    generator = synalinks.Generator(
        data_model=BookPlan,
        language_model=language_model,
        temperature=1.0,
        instructions=instructions
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


# =============================================================================
# Plan Critique Functions
# =============================================================================

async def critique_book_plan(
    topic_data: dict,
    book_plan: dict,
    outline_summary: str,
    language_model
) -> dict:
    """
    Critique a generated book plan for quality issues.

    Returns:
        Dictionary with critique assessment
    """
    logger.info("Critiquing book plan...")

    generator = synalinks.Generator(
        data_model=BookPlanCritique,
        language_model=language_model,
        temperature=1.0,
        instructions="""You are a critical editor reviewing a book plan. Your job is to identify issues that would make the plan less useful for guiding content generation.

CRITIQUE CRITERIA:

1. SPECIFICITY: The plan should reference actual concepts from the outline, not generic statements.
   - BAD: "This book covers important topics in the field"
   - GOOD: "This book progresses from foundational concepts like X and Y to advanced topics like Z"

2. ALIGNMENT: The plan should clearly address the stated goal.
   - Check: Does the narrative arc actually lead to the goal being achieved?
   - Check: Are all key aspects of the goal reflected in the plan?

3. COHERENCE: The narrative arc and chapter connections should make logical sense.
   - Check: Do chapters build on each other in a sensible order?
   - Check: Is there a clear progression (simple→complex, foundational→applied, etc.)?

BE STRICT but FAIR:
- If the plan is vague in places but mostly specific, note the vague parts
- If the plan generally aligns with the goal but misses something, note what's missing
- Set verdict to 'pass' only if issues are minor or absent
- Set verdict to 'needs_revision' if there are substantive issues to fix"""
    )

    input_data = BookPlanCritiqueInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        outline_summary=outline_summary,
        book_plan=format_book_plan(book_plan)
    )

    result = await generator(input_data)
    return result.get_json()


async def revise_book_plan(
    topic_data: dict,
    original_plan: dict,
    critique: dict,
    outline_summary: str,
    language_model
) -> dict:
    """
    Revise a book plan based on critique feedback.

    Returns:
        Revised book plan dictionary
    """
    logger.info("Revising book plan based on critique...")

    # Compile issues into a summary
    issues = []
    if critique.get("specificity_issues"):
        issues.append("SPECIFICITY ISSUES:\n- " + "\n- ".join(critique["specificity_issues"]))
    if critique.get("alignment_issues"):
        issues.append("ALIGNMENT ISSUES:\n- " + "\n- ".join(critique["alignment_issues"]))
    if critique.get("coherence_issues"):
        issues.append("COHERENCE ISSUES:\n- " + "\n- ".join(critique["coherence_issues"]))

    critique_issues = "\n\n".join(issues) if issues else "Minor issues noted"

    generator = synalinks.Generator(
        data_model=BookPlan,
        language_model=language_model,
        temperature=1.0,
        instructions="""Revise the book plan to fix the identified issues.

IMPORTANT:
- Keep what's good about the original plan
- Fix the specific issues identified in the critique
- Make the plan MORE SPECIFIC by referencing actual concepts
- Ensure the narrative arc clearly leads to the goal
- Make chapter connections concrete and logical

Do NOT start from scratch - improve the existing plan."""
    )

    input_data = BookPlanRevisionInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        outline_summary=outline_summary,
        original_plan=format_book_plan(original_plan),
        critique_issues=critique_issues,
        revision_guidance=critique.get("revision_guidance", "Address the issues noted above")
    )

    result = await generator(input_data)
    return result.get_json()


async def generate_book_plan_with_critique(
    topic_data: dict,
    outline_results: dict,
    language_model,
    output_dir: str,
    max_attempts: int = 2,
    book_vision: dict = None
) -> dict:
    """
    Generate book plan with self-critique loop.

    Generates initial plan, critiques it, and revises if needed.

    Args:
        topic_data: Dict with topic, goal, book_name
        outline_results: The generated outline hierarchy
        language_model: The LLM to use
        output_dir: Directory to save outputs
        max_attempts: Maximum revision attempts (default 2)
        book_vision: Optional book vision for alignment guidance

    Returns:
        Dictionary with book plan data
    """
    # Check for existing plan (skip critique if resuming)
    if output_dir and output_exists(output_dir, "02_book_plan.json"):
        existing = load_json_from_file(output_dir, "02_book_plan.json")
        if existing:
            logger.info("Loaded existing book plan")
            return existing

    # Generate outline summary for critique context
    outline_summary = build_outline_text(outline_results)

    # Generate initial plan (with vision guidance)
    logger.info("Generating initial book plan...")
    plan = await _generate_book_plan_internal(
        topic_data, outline_results, language_model, book_vision
    )

    # Critique loop
    for attempt in range(max_attempts):
        critique = await critique_book_plan(topic_data, plan, outline_summary, language_model)

        # Save critique for debugging
        if output_dir:
            save_json_to_file(output_dir, f"02_book_plan_critique_{attempt + 1}.json", critique)

        if critique.get("verdict") == "pass":
            logger.info(f"Book plan passed critique (attempt {attempt + 1})")
            break
        else:
            logger.info(f"Book plan needs revision (attempt {attempt + 1}): {critique.get('revision_guidance', 'See issues')}")

            if attempt < max_attempts - 1:
                # Revise the plan
                plan = await revise_book_plan(topic_data, plan, critique, outline_summary, language_model)
            else:
                logger.warning("Max revision attempts reached, using last version")

    # Save final plan
    if output_dir:
        save_json_to_file(output_dir, "02_book_plan.json", plan)
        save_to_file(output_dir, "02_book_plan.txt", format_book_plan(plan))

    return plan


async def _generate_book_plan_internal(
    topic_data: dict,
    outline_results: dict,
    language_model,
    book_vision: dict = None
) -> dict:
    """Internal book plan generation without caching."""
    outline_text = build_outline_text(outline_results)

    instructions = """Create a comprehensive plan for the book.

The plan should:
- Provide a 2-3 paragraph overview of what the book covers
- Describe the narrative arc from beginning to end
- Explain how chapters connect and build upon each other
- Identify key themes that run throughout

IMPORTANT: Be SPECIFIC. Reference actual concepts from the outline.
- BAD: "The book covers fundamental and advanced topics"
- GOOD: "The book begins with [specific concept] and progresses through [specific concepts] to reach [specific advanced topic]"

This plan will guide all subsequent content generation."""

    if book_vision:
        instructions += f"""

ALIGN WITH BOOK VISION:
- Core thesis: {book_vision.get('core_thesis', '')}
- Reader journey: {book_vision.get('reader_journey', '')}
- Key themes: {', '.join(book_vision.get('key_themes', []))}
- Unique angle: {book_vision.get('unique_angle', '')}

The plan must support achieving the reader journey and emphasize the key themes."""

    generator = synalinks.Generator(
        data_model=BookPlan,
        language_model=language_model,
        temperature=1.0,
        instructions=instructions
    )

    input_data = BookPlanInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        full_outline=outline_text
    )

    result = await generator(input_data)
    return result.get_json()


async def critique_chapters_overview(
    topic_data: dict,
    chapters_overview: dict,
    book_plan: dict,
    language_model
) -> dict:
    """
    Critique a generated chapters overview for quality issues.

    Returns:
        Dictionary with critique assessment
    """
    logger.info("Critiquing chapters overview...")

    generator = synalinks.Generator(
        data_model=ChaptersOverviewCritique,
        language_model=language_model,
        temperature=1.0,
        instructions="""You are a critical editor reviewing a chapters overview. Your job is to identify issues that would make the overview less useful for guiding chapter planning.

CRITIQUE CRITERIA:

1. FLOW: The narrative_flow should describe actual logical progression.
   - BAD: "The book flows from basics to advanced topics"
   - GOOD: "The book opens with [concept], which establishes [foundation], enabling the reader to understand [next concept]..."

2. CONNECTIONS: Each chapter's builds_on and leads_to should reference SPECIFIC concepts.
   - BAD: builds_on: "Previous chapters" or "Earlier material"
   - GOOD: builds_on: "The memory management concepts from Chapter 3"
   - BAD: leads_to: "More advanced topics"
   - GOOD: leads_to: "The optimization techniques in Chapter 7"

3. COVERAGE: The chapters together should adequately address the book's goal.
   - Check: Is any key aspect of the goal not represented in the chapter briefs?
   - Check: Do the key_concepts for each chapter actually contribute to the goal?

BE STRICT about vague connections - they are the most common problem.
Set verdict to 'pass' only if connections are specific and flow is clear.
Set verdict to 'needs_revision' if there are vague connections or unclear flow."""
    )

    input_data = ChaptersOverviewCritiqueInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_plan=format_book_plan(book_plan),
        chapters_overview=format_chapters_overview(chapters_overview)
    )

    result = await generator(input_data)
    return result.get_json()


async def revise_chapters_overview(
    topic_data: dict,
    original_overview: dict,
    critique: dict,
    book_plan: dict,
    chapter_names: list,
    language_model
) -> dict:
    """
    Revise chapters overview based on critique feedback.

    Returns:
        Revised chapters overview dictionary
    """
    logger.info("Revising chapters overview based on critique...")

    # Compile issues
    issues = []
    if critique.get("flow_issues"):
        issues.append("FLOW ISSUES:\n- " + "\n- ".join(critique["flow_issues"]))
    if critique.get("connection_issues"):
        issues.append("CONNECTION ISSUES:\n- " + "\n- ".join(critique["connection_issues"]))
    if critique.get("coverage_issues"):
        issues.append("COVERAGE ISSUES:\n- " + "\n- ".join(critique["coverage_issues"]))

    critique_issues = "\n\n".join(issues) if issues else "Minor issues noted"

    generator = synalinks.Generator(
        data_model=ChaptersOverview,
        language_model=language_model,
        temperature=1.0,
        instructions="""Revise the chapters overview to fix the identified issues.

IMPORTANT:
- Keep what's good about the original overview
- Fix the specific issues identified in the critique
- Make builds_on and leads_to SPECIFIC - name actual concepts, not "previous material"
- Make the narrative_flow describe actual logical progression
- Ensure all chapters contribute to the book's goal

Do NOT start from scratch - improve the existing overview."""
    )

    input_data = ChaptersOverviewRevisionInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_plan=format_book_plan(book_plan),
        chapters="\n".join(chapter_names),
        original_overview=format_chapters_overview(original_overview),
        critique_issues=critique_issues,
        revision_guidance=critique.get("revision_guidance", "Address the issues noted above")
    )

    result = await generator(input_data)
    return result.get_json()


async def generate_chapters_overview_with_critique(
    topic_data: dict,
    outline_results: dict,
    book_plan: dict,
    language_model,
    output_dir: str,
    max_chapters: Optional[int] = None,
    max_attempts: int = 2
) -> dict:
    """
    Generate chapters overview with self-critique loop.

    Args:
        max_attempts: Maximum revision attempts (default 2)

    Returns:
        Dictionary with chapters overview data
    """
    # Check for existing overview
    if output_dir and output_exists(output_dir, "02_chapters_overview.json"):
        existing = load_json_from_file(output_dir, "02_chapters_overview.json")
        if existing:
            logger.info("Loaded existing chapters overview")
            return existing

    chapter_names = get_chapter_names(outline_results)
    if max_chapters:
        chapter_names = chapter_names[:max_chapters]

    # Generate initial overview
    logger.info("Generating initial chapters overview...")
    overview = await _generate_chapters_overview_internal(
        topic_data, outline_results, book_plan, language_model, max_chapters
    )

    # Critique loop
    for attempt in range(max_attempts):
        critique = await critique_chapters_overview(topic_data, overview, book_plan, language_model)

        # Save critique for debugging
        if output_dir:
            save_json_to_file(output_dir, f"02_chapters_overview_critique_{attempt + 1}.json", critique)

        if critique.get("verdict") == "pass":
            logger.info(f"Chapters overview passed critique (attempt {attempt + 1})")
            break
        else:
            logger.info(f"Chapters overview needs revision (attempt {attempt + 1}): {critique.get('revision_guidance', 'See issues')}")

            if attempt < max_attempts - 1:
                overview = await revise_chapters_overview(
                    topic_data, overview, critique, book_plan, chapter_names, language_model
                )
            else:
                logger.warning("Max revision attempts reached, using last version")

    # Save final overview
    if output_dir:
        save_json_to_file(output_dir, "02_chapters_overview.json", overview)
        save_to_file(output_dir, "02_chapters_overview.txt", format_chapters_overview(overview))

    return overview


async def _generate_chapters_overview_internal(
    topic_data: dict,
    outline_results: dict,
    book_plan: dict,
    language_model,
    max_chapters: Optional[int] = None
) -> dict:
    """Internal chapters overview generation without caching."""
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
- BE SPECIFIC: name actual concepts, not "basics" or "advanced topics"

For each chapter_brief:
- chapter_name: Use the EXACT chapter name provided (do not modify it)
- brief_role: 1-2 sentences on what this chapter accomplishes
- key_concepts: The main ideas introduced or developed
- builds_on: SPECIFIC prerequisite knowledge (name concepts, not "previous material")
- leads_to: SPECIFIC concepts this enables (name them, not "more advanced topics")

IMPORTANT: Vague connections like "builds on previous chapters" are NOT acceptable.
Be specific: "builds on the memory management model from Chapter 3" is correct."""
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
    return result.get_json()


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


async def generate_chapter_plans_with_critique(
    topic_data: dict,
    outline_results: dict,
    book_plan: dict,
    language_model,
    output_dir: str,
    max_chapters: Optional[int] = None,
    critique_enabled: bool = True,
    critique_max_attempts: int = 2
) -> tuple:
    """
    Generate plans for all chapters with self-critique loop on overview.

    Stage 1: Generate a coherent overview of all chapters (with critique)
    Stage 2: Generate detailed plans for each chapter individually

    Returns:
        Tuple of (chapters_overview, chapter_plans_dict)
    """
    outline_text = build_outline_text(outline_results)
    chapter_names = get_chapter_names(outline_results)

    if max_chapters:
        chapter_names = chapter_names[:max_chapters]

    total_chapters = len(chapter_names)

    # ==========================================================================
    # STAGE 1: Generate chapters overview (with or without critique)
    # ==========================================================================
    if critique_enabled and critique_max_attempts > 0:
        chapters_overview = await generate_chapters_overview_with_critique(
            topic_data, outline_results, book_plan, language_model, output_dir,
            max_chapters, critique_max_attempts
        )
    else:
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


async def generate_chapter_plans(
    topic_data: dict,
    outline_results: dict,
    book_plan: dict,
    language_model,
    output_dir: str,
    max_chapters: Optional[int] = None
) -> tuple:
    """
    Generate plans for all chapters using two-stage approach (no critique).

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
    max_chapters: Optional[int] = None,
    critique_enabled: bool = True,
    critique_max_attempts: int = 2,
    book_vision: dict = None
) -> tuple:
    """
    Run the complete hierarchical planning process.

    Args:
        topic_data: Dictionary with topic, goal, book_name
        outline_results: The generated outline hierarchy
        language_model: The language model to use
        output_dir: Directory to save outputs
        max_chapters: Maximum chapters to plan (for test mode)
        critique_enabled: Whether to enable self-critique loop for plans
        critique_max_attempts: Maximum revision attempts per plan
        book_vision: Optional book vision dict for alignment guidance

    Returns:
        Tuple of (book_plan, chapters_overview, chapter_plans, all_section_plans, hierarchy)
    """
    # Generate book plan (with or without critique)
    # Pass book_vision for alignment
    if critique_enabled and critique_max_attempts > 0:
        book_plan = await generate_book_plan_with_critique(
            topic_data, outline_results, language_model, output_dir, critique_max_attempts,
            book_vision=book_vision
        )
    else:
        book_plan = await generate_book_plan(
            topic_data, outline_results, language_model, output_dir,
            book_vision=book_vision
        )

    # Generate chapter plans (two-stage: overview + individual plans)
    chapters_overview, chapter_plans = await generate_chapter_plans_with_critique(
        topic_data, outline_results, book_plan, language_model, output_dir, max_chapters,
        critique_enabled, critique_max_attempts
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
