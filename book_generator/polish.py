"""
Chapter polishing for final quality improvement.

This module handles the final polish pass that improves:
- Cohesion between sections
- Transitions and flow
- Detail and clarity
- Prose quality
"""

import logging
from typing import List

import synalinks

from .models import ChapterPolishInput, PolishedChapter
from .utils import sanitize_filename, output_exists, load_from_file, save_to_file
from .planning import format_book_plan, format_chapter_plan, get_chapter_plan_by_name

logger = logging.getLogger(__name__)


async def polish_chapter(
    topic_data: dict,
    chapter_name: str,
    chapter_content: str,
    chapter_number: int,
    total_chapters: int,
    chapter_plan: dict,
    previous_summary: str,
    next_summary: str,
    language_model,
    output_dir: str
) -> dict:
    """
    Polish a single chapter for improved quality.

    Returns:
        Dictionary with polished chapter content
    """
    safe_chapter = sanitize_filename(chapter_name)
    filename = f"05_polished_{chapter_number:03d}_{safe_chapter}.txt"

    # Check for existing polished chapter
    if output_dir and output_exists(output_dir, filename):
        existing = load_from_file(output_dir, filename)
        if existing:
            logger.info(f"Loaded existing polished chapter: {chapter_name}")
            return {"chapter_content": existing}

    logger.info(f"Polishing chapter {chapter_number}: {chapter_name}")

    generator = synalinks.Generator(
        data_model=PolishedChapter,
        language_model=language_model,
        instructions="""Polish this chapter into publication-ready quality.

TARGET AUDIENCE: Calibrate for the specified audience's technical level.

LANGUAGE STYLE: Prioritize CLARITY and RIGOR:
- Technically precise and accurate throughout
- Clear logical flow and well-structured prose
- Professional textbook quality writing

Your polished chapter should:

1. COHESION: Sections should read as one unified piece
2. TRANSITIONS: Add smooth, logical transitions between sections
3. REDUNDANCY: Remove repetitive content across sections
4. NARRATIVE: Create a clear arc from introduction through synthesis
5. PROSE: Professional book standards - clear, precise, well-structured
6. CONTINUITY: Reference previous/next chapters where natural

CRITICAL - QUALITY CONTROL:
- REMOVE or REDUCE generic analogies (cooking, sports, traffic, gardening, etc.)
- Keep ONLY analogies that are domain-relevant and genuinely clarifying
- Do NOT add new analogies - remove weak ones instead
- Respect reader intelligence - avoid over-explanation or patronizing tone
- Maintain technical precision - do not oversimplify
- Prefer concrete domain examples over loose comparisons

The chapter should read like a professional textbook chapter.

STRUCTURE:
- Start with a ## Chapter heading
- Keep all section headings (### Section Name)
- Maintain all substantive technical content
- Do NOT add filler introductions like "In this chapter..." """
    )

    input_data = ChapterPolishInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        audience=topic_data.get("audience", "technical readers"),
        chapter_name=chapter_name,
        chapter_number=chapter_number,
        total_chapters=total_chapters,
        chapter_plan=format_chapter_plan(chapter_plan),
        chapter_content=chapter_content,
        previous_chapter_summary=previous_summary or "This is the first chapter.",
        next_chapter_summary=next_summary or "This is the last chapter."
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    # Save the polished chapter
    if output_dir:
        save_to_file(output_dir, filename, result_dict.get("chapter_content", ""))

    return result_dict


async def polish_chapters(
    topic_data: dict,
    rewritten_chapters: List[tuple],
    chapter_plans: dict,
    language_model,
    output_dir: str
) -> List[tuple]:
    """
    Polish all chapters for final quality.

    Returns:
        List of (chapter_name, polished_content_dict) tuples
    """
    polished_chapters = []
    total_chapters = len(rewritten_chapters)

    for i, (chapter_name, chapter_data) in enumerate(rewritten_chapters, 1):
        chapter_content = chapter_data.get("chapter_content", "")
        chapter_plan = get_chapter_plan_by_name(chapter_plans, chapter_name)

        # Get context for continuity
        prev_summary = ""
        next_summary = ""

        if i > 1:
            prev_name = rewritten_chapters[i-2][0]
            prev_plan = get_chapter_plan_by_name(chapter_plans, prev_name)
            prev_summary = prev_plan.get("chapter_summary", "") if prev_plan else ""

        if i < total_chapters:
            next_name = rewritten_chapters[i][0]
            next_plan = get_chapter_plan_by_name(chapter_plans, next_name)
            next_summary = next_plan.get("chapter_summary", "") if next_plan else ""

        try:
            polished = await polish_chapter(
                topic_data,
                chapter_name,
                chapter_content,
                i,
                total_chapters,
                chapter_plan,
                prev_summary,
                next_summary,
                language_model,
                output_dir
            )
            polished_chapters.append((chapter_name, polished))
        except Exception as e:
            logger.warning(f"Polish failed for chapter {i}: {e}")
            polished_chapters.append((chapter_name, chapter_data))

    return polished_chapters
