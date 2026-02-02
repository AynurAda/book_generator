"""
Writing styles for book generation.

This module defines different writing styles that can be applied to book content.
Styles focus on HOW to write (sentence structure, complexity, tone) not WHO is writing.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

import synalinks

from .models import AuthorStyleInput, StyledContent, AboutAuthorInput, AboutAuthorOutput
from .utils import output_exists, load_from_file, save_to_file

logger = logging.getLogger(__name__)


@dataclass
class WritingStyle:
    """A writing style configuration."""

    key: str  # Internal identifier
    name: str  # Display name for the book cover
    description: str  # Brief description of the style
    style_instructions: str  # Concrete instructions for the LLM


# =============================================================================
# WRITING STYLES
# =============================================================================

WRITING_STYLES: Dict[str, WritingStyle] = {

    "waitbutwhy": WritingStyle(
        key="waitbutwhy",
        name="",
        description="WaitButWhy blog style - conversational, clear explanations with deep dives",
        style_instructions="""Rewrite this content in the style of WaitButWhy blog.

STYLE CHARACTERISTICS:
- Conversational, engaging tone that makes complex topics accessible
- Deep dives that thoroughly explore topics (WaitButWhy posts are famously LONG)
- Clear explanations that build understanding step by step
- Occasional humor and relatable observations
- Uses analogies where they genuinely illuminate concepts

IMPORTANT CLARIFICATIONS:
- PRESERVE ALL DEPTH AND DETAIL - WaitButWhy is known for comprehensive coverage
- Do NOT condense or summarize - expand explanations where helpful
- Do NOT patronize the reader - they are intelligent, just learning this topic
- Keep technical accuracy - accessible doesn't mean dumbed down
- Maintain the same comprehensive scope as the original"""
    ),

    "for_dummies": WritingStyle(
        key="for_dummies",
        name="",
        description="For Dummies series style - accessible, step-by-step",
        style_instructions="""Rewrite this content in the style of the "For Dummies" book series.

IMPORTANT CLARIFICATIONS:
- Use analogies where they genuinely help understanding, not after every concept
- Do NOT patronize the reader - they are intelligent, just new to this topic
- Keep technical accuracy - accessible doesn't mean imprecise"""
    ),

    "oreilly": WritingStyle(
        key="oreilly",
        name="",
        description="O'Reilly technical book style - practical, clear, for practitioners",
        style_instructions="""Rewrite this content in the style of O'Reilly technical books.

IMPORTANT CLARIFICATIONS:
- Use analogies sparingly and only when they clarify complex concepts
- Respect the reader as a fellow practitioner
- Maintain technical precision throughout"""
    ),

    "textbook": WritingStyle(
        key="textbook",
        name="",
        description="Academic textbook style - rigorous, structured, formal",
        style_instructions="""Rewrite this content in a clear academic textbook style.

IMPORTANT CLARIFICATIONS:
- Analogies are acceptable where pedagogically valuable, but prioritize precision
- Assume an intelligent reader learning the material
- Maintain rigor and formal structure"""
    ),

    "practical": WritingStyle(
        key="practical",
        name="",
        description="Practical guide style - application-focused, minimal theory",
        style_instructions="""Rewrite this content as a practical, application-focused guide.

IMPORTANT CLARIFICATIONS:
- Use examples that show real application, not just analogies
- Respect the reader's time and intelligence
- Keep what's needed to apply the knowledge, trim excess theory"""
    ),
}


# =============================================================================
# COMPATIBILITY ALIASES (map old author_key names to new styles)
# =============================================================================

AUTHOR_PROFILES = {
    "warm_educator": WRITING_STYLES["waitbutwhy"],
    "pragmatic_engineer": WRITING_STYLES["practical"],
    "curious_explorer": WRITING_STYLES["oreilly"],
    "no_nonsense_expert": WRITING_STYLES["textbook"],
    # Direct style names also work
    **WRITING_STYLES
}


def get_author_profile(style_key: str) -> Optional[WritingStyle]:
    """Get a writing style by key."""
    return AUTHOR_PROFILES.get(style_key)


def list_available_authors() -> list:
    """List all available writing styles."""
    return [
        {
            "key": style.key,
            "name": style.name or "(uses configured author)",
            "description": style.description,
        }
        for style in WRITING_STYLES.values()
    ]


async def apply_author_style(
    content: str,
    style: WritingStyle,
    chapter_name: str,
    language_model,
    output_dir: str,
    chapter_number: int
) -> str:
    """
    Apply a writing style to chapter content.
    """
    from .utils import sanitize_filename

    safe_chapter = sanitize_filename(chapter_name)
    filename = f"07_styled_{chapter_number:03d}_{safe_chapter}.txt"

    # Check for existing styled content
    if output_dir and output_exists(output_dir, filename):
        existing = load_from_file(output_dir, filename)
        if existing:
            logger.info(f"Loaded existing styled chapter: {chapter_name}")
            return existing

    logger.info(f"Applying '{style.key}' style to: {chapter_name}")

    generator = synalinks.Generator(
        data_model=StyledContent,
        language_model=language_model,
        temperature=1.0,
        instructions=f"""{style.style_instructions}

CRITICAL - PRESERVE COMPREHENSIVE DEPTH:
- Keep ALL technical content, details, and explanations
- Maintain the SAME LENGTH or make it LONGER with better explanations
- The same section structure and headings
- All examples, edge cases, and nuances
- Do NOT summarize, condense, or shorten any section

IMPORTANT - DO NOT:
- Add references to any author or persona
- Remove any substantive content
- Change the meaning of any technical content
- Shorten or condense the material"""
    )

    input_data = AuthorStyleInput(
        original_content=content,
        author_name=style.key,  # Just pass the style key, not a persona
        author_style=style.description,
        author_tone="clear",
        chapter_name=chapter_name
    )

    result = await generator(input_data)
    styled_content = result.get_json().get("styled_content", content)

    # Save the styled content
    if output_dir:
        save_to_file(output_dir, filename, styled_content)

    return styled_content


async def generate_about_author(
    style: WritingStyle,
    book_name: str,
    topic: str,
    language_model,
    output_dir: str
) -> str:
    """
    Generate an About the Author section.

    Since we're using styles not personas, this returns empty unless
    a custom author name is configured.
    """
    # With pure styles (no persona), skip About the Author
    if not style.name:
        return ""

    filename = "08_about_author.txt"

    if output_dir and output_exists(output_dir, filename):
        existing = load_from_file(output_dir, filename)
        if existing:
            return existing

    # If there's a name, generate a brief professional bio
    generator = synalinks.Generator(
        data_model=AboutAuthorOutput,
        language_model=language_model,
        temperature=1.0,
        instructions="""Write a brief, professional author bio (2-3 sentences).
Keep it simple and factual. Do not invent elaborate backstories."""
    )

    input_data = AboutAuthorInput(
        author_name=style.name,
        author_background="Technical writer",
        author_expertise=topic,
        book_name=book_name,
        book_topic=topic
    )

    result = await generator(input_data)
    about_content = result.get_json().get("about_author", "")

    if output_dir and about_content:
        save_to_file(output_dir, filename, about_content)

    return about_content
