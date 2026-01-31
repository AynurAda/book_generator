"""
Content generation for subsections and sections.

This module handles the generation of actual book content:
- Subsection content (explanations, analogies, examples)
- Section rewriting (combining subsections into coherent sections)
- Direct section writing (writing sections directly from topic names)
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
from .planning import format_book_plan, format_chapters_overview, format_chapter_plan, format_section_plan

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
        temperature=1.0,
        instructions="""Generate rigorous content for this book subsection.

TARGET AUDIENCE: Write for the specified audience.
- Match the technical depth to their expected background
- Use terminology appropriate to their field
- Address concepts they would find valuable

LANGUAGE STYLE: Write with CLARITY and RIGOR:
- Define technical terms precisely when first used
- Be precise and accurate throughout
- Explain the "why" alongside the "what"
- Maintain textbook quality

Your content should:

1. CONCEPT EXPLANATION:
   - Explain core concepts clearly and thoroughly
   - Define key terms and their relationships
   - Build understanding progressively with logical flow
   - Prioritize precision over simplification

2. EXAMPLES (use judiciously):
   - Provide concrete, domain-relevant examples that illuminate the concept
   - Examples should come from the SAME FIELD as the book topic
   - For technical audiences, use technical examples (code, algorithms, systems)
   - Show how concepts apply in real scenarios within the domain

CRITICAL - ANALOGIES:
- Use analogies SPARINGLY - only when a concept genuinely benefits from comparison
- When used, analogies MUST be relevant to the audience and topic domain
- AVOID generic analogies (cooking, sports, traffic, etc.) - they often feel patronizing
- For technical audiences, prefer precise explanation over loose analogies
- If an analogy doesn't add significant clarity, omit it entirely
- One well-chosen analogy per section maximum, if any

Do NOT include introductions or summaries - these will be added during section assembly."""
    )

    input_data = SectionInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        audience=topic_data.get("audience", "technical readers"),
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
    from .planning import get_chapter_plan_by_index

    all_generated = {}
    subsection_counter = 1

    chapter_names = list(hierarchy.keys())
    if max_chapters:
        chapter_names = chapter_names[:max_chapters]

    for chapter_idx, chapter_name in enumerate(chapter_names):
        chapter_plan = get_chapter_plan_by_index(chapter_plans, chapter_idx)
        section_plans = all_section_plans.get(chapter_name, {})
        chapter_sections = hierarchy.get(chapter_name, {})

        all_generated[chapter_name] = {}

        section_plans_list = section_plans.get("section_plans", [])

        for section_idx, (section_name, subsections) in enumerate(chapter_sections.items()):
            section_plan = section_plans_list[section_idx] if section_idx < len(section_plans_list) else None
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
    book_plan: dict,
    chapters_overview: dict,
    chapter_plan: dict,
    section_plan: dict,
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
    from .planning import format_book_plan, format_chapters_overview, format_chapter_plan, format_section_plan

    logger.info(f"Rewriting section: {section_name}")

    generator = synalinks.Generator(
        data_model=ChapterOutput,
        language_model=language_model,
        temperature=1.0,
        instructions=f"""Rewrite the subsections into a single, coherent book section.

You have access to the full book plan, chapters overview, chapter plan, and section plan.
Use this context to understand what this section needs to accomplish and how it fits
into the broader narrative.

TARGET AUDIENCE: Write for the specified audience with appropriate technical depth.

LANGUAGE STYLE: Write with CLARITY and RIGOR:
- Precise and technically accurate throughout
- Clear logical flow between concepts
- Professional textbook quality

INTRODUCTION STYLE: {intro_style}

CRITICAL - MAINTAIN COMPREHENSIVE DEPTH:
- Keep ALL technical content from the subsections - do not summarize or condense
- The rewritten section should be AT LEAST as long as the combined subsections
- Every concept, example, and detail from the input should appear in the output
- Add transitions and flow, but do NOT remove substantive content
- If anything, EXPAND on concepts where the section plan indicates importance

Your rewritten section should:
1. Begin with the specified introduction style
2. Flow naturally between topics with clear logical connections
3. PRESERVE all technical information from the subsections
4. Add smooth transitions between ideas
5. End with a synthesis or forward reference

CRITICAL GUIDELINES:
- Preserve technical precision - do not oversimplify
- Remove or reduce generic analogies (cooking, sports, etc.)
- Keep only analogies that are domain-relevant and genuinely illuminating
- Respect the reader's intelligence - avoid over-explanation
- Maintain consistent technical terminology

Write in flowing prose. You may use sub-headers (###) for major topic shifts if helpful.
The section header (### Section Name) will be added separately."""
    )

    formatted_content = format_subsections_for_rewrite(subsections_content)

    input_data = ChapterInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        audience=topic_data.get("audience", "technical readers"),
        book_plan=format_book_plan(book_plan),
        chapters_overview=format_chapters_overview(chapters_overview),
        chapter_plan=format_chapter_plan(chapter_plan),
        section_plan=format_section_plan(section_plan) if section_plan else "No specific section plan available.",
        chapter_title=chapter_name,
        section_name=section_name,
        subsections_content=formatted_content,
        previous_section_summary=previous_summary or "This is the first section.",
        next_section_summary=next_summary or "This is the last section.",
        intro_style=intro_style
    )

    result = await generator(input_data)
    return result.get_json().get("chapter_content", "")


async def rewrite_sections(
    topic_data: dict,
    all_generated: dict,
    book_plan: dict,
    chapters_overview: dict,
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
    from .planning import get_chapter_plan_by_index

    rewritten_chapters = []
    style_idx = 0

    for chapter_idx, (chapter_name, sections) in enumerate(all_generated.items()):
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

        chapter_plan = get_chapter_plan_by_index(chapter_plans, chapter_idx)
        chapter_content_parts = []

        # Get section plans for this chapter
        chapter_section_plans = all_section_plans.get(chapter_name, {})
        section_plans_list = chapter_section_plans.get("section_plans", [])

        section_names = list(sections.keys())
        for i, (section_name, subsections) in enumerate(sections.items()):
            if not subsections:
                continue

            # Get the section plan for this specific section
            section_plan = section_plans_list[i] if i < len(section_plans_list) else None

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
                book_plan,
                chapters_overview,
                chapter_plan,
                section_plan,
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


# =============================================================================
# DIRECT WRITE MODE - Write sections directly from topic names
# =============================================================================

async def write_section_direct(
    topic_data: dict,
    chapter_name: str,
    section_name: str,
    subsection_names: List[str],
    book_plan: dict,
    chapters_overview: dict,
    chapter_plan: dict,
    section_plan: dict,
    previous_summary: str,
    next_summary: str,
    intro_style: str,
    language_model,
    writing_style: Optional[object] = None
) -> str:
    """
    Write a section directly from subsection topic names (no pre-generation).

    This is more efficient than generating individual subsections then rewriting.
    The LLM writes comprehensive flowing prose covering all topics directly.

    Args:
        writing_style: Optional WritingStyle object to apply during writing

    Returns:
        The section content as flowing prose
    """
    logger.info(f"Writing section directly: {section_name}")

    # Format subsection names as a list of topics to cover
    topics_to_cover = "\n".join(f"- {name}" for name in subsection_names)

    # Build style instructions if a writing style is provided
    style_section = ""
    if writing_style:
        style_section = f"""
=== WRITING STYLE ===

{writing_style.style_instructions}

The style instructions above describe HOW to write. Apply this style while maintaining
all depth requirements below. Style does NOT mean shorter - it means different voice/tone.

"""

    generator = synalinks.Generator(
        data_model=ChapterOutput,
        language_model=language_model,
        temperature=1.0,
        instructions=f"""{style_section}Write comprehensive book content for this section.

You are given a list of TOPICS TO COVER. Write flowing, professional prose that
thoroughly explains each topic. This is direct authoring - write the actual book content.

You have access to the full book plan, chapters overview, chapter plan, and section plan.
Use this context to understand what depth and coverage is expected.

TARGET AUDIENCE: Write for the specified audience with appropriate technical depth.

LANGUAGE STYLE: Write with CLARITY and RIGOR:
- Precise and technically accurate throughout
- Clear logical flow between concepts
- Professional textbook quality

INTRODUCTION STYLE: {intro_style}

=== CRITICAL: DEPTH REQUIREMENTS ===

Each topic in the list MUST receive DEEP, THOROUGH treatment. This means:

1. MINIMUM LENGTH PER TOPIC: 500-1000 words (or more if needed to fully explain)
   - A brief mention or summary is NOT acceptable
   - Each topic deserves comprehensive, textbook-quality coverage
   - If a concept is complex, use MORE words, not fewer

2. REQUIRED COVERAGE FOR EACH TOPIC:
   - DEFINITION: What is this concept? Define it precisely and completely
   - MECHANICS: How does it work? Explain the underlying principles in detail
   - SIGNIFICANCE: Why does this matter? What problems does it solve? Why should readers care?
   - EXAMPLES: Multiple concrete, specific examples that illustrate different aspects
   - NUANCES: Edge cases, common misconceptions, limitations, and important caveats
   - CONNECTIONS: How does this relate to other concepts in the section/chapter?

3. TOTAL SECTION LENGTH: With N topics, expect roughly N × 500-1000 words
   - A section with 3 topics should be at least 1500-3000 words
   - A section with 5 topics should be at least 2500-5000 words
   - This is a COMPREHENSIVE TEXTBOOK, not a summary or overview

DO NOT:
- Mention a topic in 1-2 sentences and move on
- Write a "survey" that superficially touches each topic
- Sacrifice depth for brevity
- Assume the reader already knows these concepts

Your section should:
1. Begin with the specified introduction style
2. Flow naturally between topics with clear logical connections
3. Give each topic the DEEP treatment it deserves
4. Add smooth transitions between ideas
5. End with a synthesis or forward reference

CRITICAL GUIDELINES:
- Preserve technical precision - do not oversimplify
- Use analogies sparingly and only when they genuinely illuminate
- Respect the reader's intelligence
- Maintain consistent technical terminology

Write in flowing prose. Use sub-headers (####) for each major topic to organize the content.
The section header (### Section Name) will be added separately."""
    )

    input_data = ChapterInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        audience=topic_data.get("audience", "technical readers"),
        book_plan=format_book_plan(book_plan),
        chapters_overview=format_chapters_overview(chapters_overview),
        chapter_plan=format_chapter_plan(chapter_plan),
        section_plan=format_section_plan(section_plan) if section_plan else "No specific section plan available.",
        chapter_title=chapter_name,
        section_name=section_name,
        subsections_content=f"TOPICS TO COVER:\n{topics_to_cover}",
        previous_section_summary=previous_summary or "This is the first section.",
        next_section_summary=next_summary or "This is the last section.",
        intro_style=intro_style
    )

    result = await generator(input_data)
    return result.get_json().get("chapter_content", "")


async def write_all_sections_direct(
    topic_data: dict,
    hierarchy: dict,
    book_plan: dict,
    chapters_overview: dict,
    chapter_plans: dict,
    all_section_plans: dict,
    language_model,
    output_dir: str,
    intro_styles: List[str],
    max_chapters: Optional[int] = None,
    writing_style: Optional[object] = None
) -> List[tuple]:
    """
    Write all sections directly from topic names (no subsection pre-generation).

    This is the efficient alternative to generate_all_subsections + rewrite_sections.

    Args:
        writing_style: Optional WritingStyle object to apply during writing

    Returns:
        List of (chapter_name, chapter_content_dict) tuples
    """
    from .planning import get_chapter_plan_by_index

    written_chapters = []
    style_idx = 0

    chapter_names = list(hierarchy.keys())
    if max_chapters:
        chapter_names = chapter_names[:max_chapters]

    for chapter_idx, chapter_name in enumerate(chapter_names):
        safe_chapter = sanitize_filename(chapter_name)
        chapter_filename = f"04_chapter_{safe_chapter}.txt"

        # Check for existing chapter
        if output_dir and output_exists(output_dir, chapter_filename):
            existing = load_from_file(output_dir, chapter_filename)
            if existing:
                logger.info(f"Loaded existing chapter: {chapter_name}")
                written_chapters.append((chapter_name, {"chapter_content": existing}))
                continue

        logger.info(f"Writing chapter directly: {chapter_name}")

        chapter_plan = get_chapter_plan_by_index(chapter_plans, chapter_idx)
        chapter_sections = hierarchy.get(chapter_name, {})

        # Get section plans for this chapter
        chapter_section_plans = all_section_plans.get(chapter_name, {})
        section_plans_list = chapter_section_plans.get("section_plans", [])

        chapter_content_parts = []
        section_names = list(chapter_sections.keys())

        for i, (section_name, subsection_names) in enumerate(chapter_sections.items()):
            if not subsection_names:
                continue

            # Get the section plan for this specific section
            section_plan = section_plans_list[i] if i < len(section_plans_list) else None

            # Get context for transitions
            prev_summary = section_names[i-1] if i > 0 else ""
            next_summary = section_names[i+1] if i < len(section_names) - 1 else ""

            # Get intro style (rotating)
            intro_style = intro_styles[style_idx % len(intro_styles)]
            style_idx += 1

            section_content = await write_section_direct(
                topic_data,
                chapter_name,
                section_name,
                subsection_names,
                book_plan,
                chapters_overview,
                chapter_plan,
                section_plan,
                prev_summary,
                next_summary,
                intro_style,
                language_model,
                writing_style
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

        written_chapters.append((chapter_name, chapter_data))

    return written_chapters
