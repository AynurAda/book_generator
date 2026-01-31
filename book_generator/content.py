"""
Content generation for subsections, sections, and chapters.

This module handles the generation of actual book content:
- Subsection content (individual topic explanations with multi-branch generation)
- Section introductions
- Chapter introductions
- Final assembly by concatenation
"""

import asyncio
import logging
from typing import List, Optional, Dict

import synalinks

from .models import (
    SubsectionInput, SubsectionContent,
    SectionIntroInput, SectionIntro,
    ChapterIntroInput, ChapterIntro,
)
from .utils import (
    sanitize_filename,
    output_exists,
    load_from_file,
    load_json_from_file,
    save_to_file,
    save_json_to_file,
    build_outline_text,
)
from .planning import (
    format_book_plan,
    format_chapters_overview,
    format_chapter_plan,
    format_section_plan,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SUBSECTION GENERATION
# =============================================================================

async def generate_subsection(
    subsection_input: SubsectionInput,
    language_model,
    writing_style: Optional[object] = None
) -> str:
    """
    Generate a single subsection with full planning context.

    The subsection_input contains all context needed:
    - topic, goal, book_name, audience
    - full_outline (entire book structure)
    - book_plan (high-level book strategy)
    - chapters_overview (all chapters summary)
    - chapter_name, chapter_plan (current chapter context)
    - section_name, section_plan (current section context)
    - subsection_name (the specific topic to write)

    Returns:
        The subsection content
    """
    # Build style instructions if provided
    style_section = ""
    if writing_style:
        style_section = f"""
=== WRITING STYLE ===

{writing_style.style_instructions}

Apply this style while maintaining all depth requirements. Style does NOT mean shorter.

"""

    instructions = f"""{style_section}Write comprehensive content for this specific subsection/topic.

You have access to the full book context: book plan, chapters overview, chapter plan, and section plan.
Use this context to understand what depth and coverage is expected.

TARGET AUDIENCE: Write for the specified audience with appropriate technical depth.

LANGUAGE STYLE: Write with CLARITY and RIGOR:
- Precise and technically accurate throughout
- Clear logical flow between concepts
- Professional textbook quality

=== CRITICAL: DEPTH REQUIREMENTS ===

This subsection MUST receive DEEP, THOROUGH treatment:

1. MINIMUM LENGTH: 500-1000 words (or more if needed to fully explain)
   - A brief mention or summary is NOT acceptable
   - This topic deserves comprehensive, textbook-quality coverage

2. REQUIRED COVERAGE:
   - DEFINITION: What is this concept? Define it precisely and completely
   - MECHANICS: How does it work? Explain the underlying principles in detail
   - SIGNIFICANCE: Why does this matter? What problems does it solve?
   - EXAMPLES: Multiple concrete, specific examples that illustrate different aspects
   - NUANCES: Edge cases, common misconceptions, limitations, caveats
   - CONNECTIONS: How does this relate to other concepts in the section/chapter?

=== CRITICAL: EXPLANATION APPROACH ===

Every explanation MUST be:

1. STEP-BY-STEP: Break down complex ideas into sequential, logical steps
   - Start from first principles
   - Build understanding incrementally
   - Make the reasoning process explicit

2. SELF-CONTAINED: This subsection should stand on its own
   - Define ALL terms when first used - do not assume prior knowledge
   - Include necessary background within the explanation

3. NO ASSUMED PRIOR KNOWLEDGE:
   - Explain jargon and technical terms immediately upon use
   - Do not skip "obvious" steps
   - Include the "why" behind every "what"

4. IN-DEPTH, NOT SURFACE-LEVEL:
   - Go beyond definitions to true understanding
   - Explain the intuition behind formal concepts
   - Show how things work internally

FORMATTING:
- Do NOT use markdown headers (no #, ##, ###, ####)
- You CAN use numbered sections like "**1. Topic Name**" to organize content
- Use **bold** for section titles and emphasis"""

    generator = synalinks.Generator(
        data_model=SubsectionContent,
        language_model=language_model,
        temperature=1.0,
        instructions=instructions
    )

    result = await generator(subsection_input)
    return result.get_json().get("content", "")


async def generate_section_intro(
    topic: str,
    book_name: str,
    chapter_name: str,
    section_name: str,
    section_plan: str,
    subsection_names: List[str],
    intro_style: str,
    language_model
) -> str:
    """
    Generate an introduction for a section.

    Returns:
        The section introduction (2-3 paragraphs)
    """
    generator = synalinks.Generator(
        data_model=SectionIntro,
        language_model=language_model,
        temperature=1.0,
        instructions=f"""Write a section introduction in WaitButWhy style (Tim Urban's blog).

OPENING APPROACH: {intro_style}

1-2 short paragraphs that set up what this section covers and why it matters.
No headers. No formal academic tone."""
    )

    subsections_list = "\n".join(f"- {name}" for name in subsection_names)

    input_data = SectionIntroInput(
        topic=topic,
        book_name=book_name,
        chapter_name=chapter_name,
        section_name=section_name,
        section_plan=section_plan or "No specific plan available",
        subsection_names=subsections_list,
        intro_style=intro_style
    )

    result = await generator(input_data)
    return result.get_json().get("introduction", "")


async def generate_part_intro(
    topic: str,
    book_name: str,
    book_plan: dict,
    chapters_overview: dict,
    part_name: str,
    part_number: int,
    total_parts: int,
    part_plan: dict,
    chapter_names: List[str],
    chapter_plans: List[dict],
    language_model
) -> str:
    """
    Generate an introduction for a part that shows how chapters fit together
    and how this part fits into the overall book.

    Returns:
        The part introduction
    """
    generator = synalinks.Generator(
        data_model=ChapterIntro,
        language_model=language_model,
        temperature=1.0,
        instructions="""Write a part introduction in WaitButWhy style (Tim Urban's blog).

You have access to:
- The overall book plan and narrative arc
- This part's plan
- Detailed plans for EACH chapter within this part

Your intro should:
1. Put this part in context of the OVERALL BOOK JOURNEY (what came before, what comes after)
2. Explain the UNIFYING THEME of this part - what ties all the chapters together
3. Show how the chapters BUILD ON EACH OTHER within this part
4. Give the reader a sense of the intellectual journey through this part

2-3 paragraphs. Show the connections and flow, not just a list of topics.
No headers. No formal academic tone."""
    )

    # Format chapters list
    chapters_list = "\n".join(f"- {name}" for name in chapter_names)

    # Format detailed chapter plans
    chapter_plans_text = []
    for i, (name, plan) in enumerate(zip(chapter_names, chapter_plans)):
        plan_text = format_section_plan(plan) if plan else "No detailed plan"
        chapter_plans_text.append(f"Chapter {name}:\n{plan_text}")
    chapter_plans_detail = "\n\n".join(chapter_plans_text)

    input_data = ChapterIntroInput(
        topic=topic,
        book_name=book_name,
        book_plan=format_book_plan(book_plan),
        chapters_overview=format_chapters_overview(chapters_overview),
        chapter_name=part_name,
        chapter_number=part_number,
        total_chapters=total_parts,
        chapter_plan=format_chapter_plan(part_plan),
        section_names=chapters_list,
        chapter_plans_detail=chapter_plans_detail
    )

    result = await generator(input_data)
    return result.get_json().get("introduction", "")


async def write_section_with_subsections(
    topic_data: dict,
    full_outline: str,
    book_plan: dict,
    chapters_overview: dict,
    chapter_name: str,
    chapter_plan: dict,
    section_name: str,
    section_plan: dict,
    subsection_names: List[str],
    intro_style: str,
    language_model,
    output_dir: str,
    section_num: int,
    writing_style: Optional[object] = None
) -> str:
    """
    Write a complete section by generating each subsection separately with full context,
    then concatenating them with a section intro.

    This provides more detail and rigor than writing the whole section at once.

    Returns:
        The complete section content
    """
    safe_section = sanitize_filename(section_name)
    section_filename = f"03_section_{section_num:03d}_{safe_section}.txt"

    # Check for existing content
    if output_dir and output_exists(output_dir, section_filename):
        existing = load_from_file(output_dir, section_filename)
        if existing:
            logger.info(f"Loaded existing section: {section_name}")
            return existing

    logger.info(f"Writing section: {section_name} ({len(subsection_names)} subsections)")

    # Generate section introduction
    section_intro = await generate_section_intro(
        topic=topic_data["topic"],
        book_name=topic_data["book_name"],
        chapter_name=chapter_name,
        section_name=section_name,
        section_plan=format_section_plan(section_plan) if section_plan else None,
        subsection_names=subsection_names,
        intro_style=intro_style,
        language_model=language_model
    )

    # Generate each subsection with full context
    subsection_contents = []
    for i, subsection_name in enumerate(subsection_names):
        logger.info(f"  Generating subsection {i+1}/{len(subsection_names)}: {subsection_name}")

        subsection_input = SubsectionInput(
            topic=topic_data["topic"],
            goal=topic_data["goal"],
            book_name=topic_data["book_name"],
            audience=topic_data.get("audience", "technical readers"),
            full_outline=full_outline,
            book_plan=format_book_plan(book_plan),
            chapters_overview=format_chapters_overview(chapters_overview),
            chapter_name=chapter_name,
            chapter_plan=format_chapter_plan(chapter_plan),
            section_name=section_name,
            section_plan=format_section_plan(section_plan) if section_plan else "No specific plan",
            subsection_name=subsection_name
        )

        content = await generate_subsection(
            subsection_input=subsection_input,
            language_model=language_model,
            writing_style=writing_style
        )

        if content:
            subsection_contents.append((subsection_name, content))

    # Assemble section: intro + subsections
    section_parts = []

    # Add section intro
    if section_intro:
        section_parts.append(section_intro)
        section_parts.append("")  # Blank line

    # Add each subsection with its header (now sections)
    for subsection_name, content in subsection_contents:
        section_parts.append(f"### {subsection_name}")
        section_parts.append("")
        section_parts.append(content)
        section_parts.append("")  # Blank line between subsections

    section_content = "\n".join(section_parts)

    # Save the section
    if output_dir:
        save_to_file(output_dir, section_filename, section_content)

    return section_content


async def write_chapter_with_sections(
    topic_data: dict,
    full_outline: str,
    book_plan: dict,
    chapters_overview: dict,
    chapter_name: str,
    chapter_number: int,
    total_chapters: int,
    chapter_plan: dict,
    chapter_section_plans: dict,
    chapter_sections: Dict[str, List[str]],
    language_model,
    output_dir: str,
    intro_styles: List[str],
    style_idx: int,
    writing_style: Optional[object] = None
) -> tuple:
    """
    Write a complete chapter by:
    1. Generating a chapter introduction
    2. Generating each section (which generates each subsection separately)
    3. Concatenating everything

    Returns:
        Tuple of (chapter_content, new_style_idx)
    """
    safe_chapter = sanitize_filename(chapter_name)
    chapter_filename = f"04_chapter_{safe_chapter}.txt"

    # Check for existing chapter
    if output_dir and output_exists(output_dir, chapter_filename):
        existing = load_from_file(output_dir, chapter_filename)
        if existing:
            logger.info(f"Loaded existing chapter: {chapter_name}")
            return ({"chapter_content": existing}, style_idx)

    logger.info(f"Writing chapter {chapter_number}/{total_chapters}: {chapter_name}")

    chapter_names_in_part = list(chapter_sections.keys())
    chapter_plans_in_part = chapter_section_plans.get("section_plans", [])

    # Generate part introduction
    part_intro = await generate_part_intro(
        topic=topic_data["topic"],
        book_name=topic_data["book_name"],
        book_plan=book_plan,
        chapters_overview=chapters_overview,
        part_name=chapter_name,
        part_number=chapter_number,
        total_parts=total_chapters,
        part_plan=chapter_plan,
        chapter_names=chapter_names_in_part,
        chapter_plans=chapter_plans_in_part,
        language_model=language_model
    )

    # Generate each section
    section_contents = []
    section_counter = (chapter_number - 1) * 100  # Section numbering for file naming

    for i, (section_name, subsection_names) in enumerate(chapter_sections.items()):
        if not subsection_names:
            continue

        section_plan = section_plans_list[i] if i < len(section_plans_list) else None

        # Get intro style (rotating)
        intro_style = intro_styles[style_idx % len(intro_styles)]
        style_idx += 1

        section_content = await write_section_with_subsections(
            topic_data=topic_data,
            full_outline=full_outline,
            book_plan=book_plan,
            chapters_overview=chapters_overview,
            chapter_name=chapter_name,
            chapter_plan=chapter_plan,
            section_name=section_name,
            section_plan=section_plan,
            subsection_names=subsection_names,
            intro_style=intro_style,
            language_model=language_model,
            output_dir=output_dir,
            section_num=section_counter + i + 1,
            writing_style=writing_style
        )

        section_contents.append((section_name, section_content))

    # Assemble chapter: header + intro + sections
    chapter_parts = []

    # Part header (was chapter)
    chapter_parts.append(f"# {chapter_name}")
    chapter_parts.append("")

    # Chapter intro
    if part_intro:
        chapter_parts.append(part_intro)
        chapter_parts.append("")

    # Each section with header (now chapters)
    for section_header, section_content in section_contents:
        chapter_parts.append(f"## {section_header}")
        chapter_parts.append("")
        chapter_parts.append(section_content)
        chapter_parts.append("")

    full_chapter = "\n".join(chapter_parts)
    chapter_data = {"chapter_content": full_chapter}

    # Save the chapter
    if output_dir:
        save_to_file(output_dir, chapter_filename, full_chapter)

    return (chapter_data, style_idx)


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
    Write all chapters by generating each subsection separately with full context.

    This is the main entry point for content generation.

    Architecture:
    - Each subsection is generated independently with full planning context
    - Sections assembled by concatenation (intro + subsections)
    - Chapters assembled by concatenation (intro + sections)

    Args:
        writing_style: Optional WritingStyle object to apply during writing

    Returns:
        List of (chapter_name, chapter_content_dict) tuples
    """
    from .planning import get_chapter_plan_by_index

    # Build the full outline text for context
    full_outline = build_outline_text({"concepts": [
        {"concept": ch, "subconcepts": [
            {"subconcept": sec, "subsubconcepts": subs}
            for sec, subs in sections.items()
        ]}
        for ch, sections in hierarchy.items()
    ]})

    written_chapters = []
    style_idx = 0

    chapter_names = list(hierarchy.keys())
    total_chapters = len(chapter_names)

    if max_chapters:
        chapter_names = chapter_names[:max_chapters]
        total_chapters = len(chapter_names)

    for chapter_idx, chapter_name in enumerate(chapter_names):
        chapter_plan = get_chapter_plan_by_index(chapter_plans, chapter_idx)
        chapter_sections = hierarchy.get(chapter_name, {})
        chapter_section_plans = all_section_plans.get(chapter_name, {})

        chapter_data, style_idx = await write_chapter_with_sections(
            topic_data=topic_data,
            full_outline=full_outline,
            book_plan=book_plan,
            chapters_overview=chapters_overview,
            chapter_name=chapter_name,
            chapter_number=chapter_idx + 1,
            total_chapters=total_chapters,
            chapter_plan=chapter_plan,
            chapter_section_plans=chapter_section_plans,
            chapter_sections=chapter_sections,
            language_model=language_model,
            output_dir=output_dir,
            intro_styles=intro_styles,
            style_idx=style_idx,
            writing_style=writing_style
        )

        written_chapters.append((chapter_name, chapter_data))

    return written_chapters
