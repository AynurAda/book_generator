"""
Fictional author profiles and style filtering.

This module handles:
- Author persona definitions
- Style filtering to rewrite content in author's voice
- About the Author section generation
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

import synalinks

from .models import AuthorStyleInput, StyledContent, AboutAuthorInput, AboutAuthorOutput
from .utils import output_exists, load_from_file, save_to_file

logger = logging.getLogger(__name__)


@dataclass
class AuthorProfile:
    """A fictional author's profile and writing characteristics."""

    name: str
    pen_name: str  # Display name for the book
    background: str  # Fictional biography
    expertise: str  # Area of expertise
    writing_style: str  # Description of writing approach
    humor_style: str  # Type of humor they use
    complexity_level: str  # accessible, moderate, technical, academic
    tone: str  # warm, conversational, formal, witty, etc.
    signature_elements: list = field(default_factory=list)  # Characteristic phrases/patterns
    style_instructions: str = ""  # Detailed instructions for the LLM


# =============================================================================
# PREDEFINED AUTHOR PROFILES
# =============================================================================

AUTHOR_PROFILES: Dict[str, AuthorProfile] = {
    "warm_educator": AuthorProfile(
        name="Dr. Alexandra Chen",
        pen_name="Alexandra Chen",
        background="""Dr. Alexandra Chen spent fifteen years as a research scientist before
turning to technical writing. Her work bridges the gap between academic rigor and
practical understanding. She lives in Seattle and believes clarity is the highest
form of respect for readers.""",
        expertise="Clear technical communication that maintains rigor",
        writing_style="Clear, engaging, well-paced explanations",
        humor_style="Occasional light touches that don't distract from content",
        complexity_level="accessible",
        tone="clear, engaging, respectful",
        signature_elements=[
            "Clear explanations that build understanding",
            "Occasional clarifying examples when genuinely helpful",
            "Logical flow between concepts",
            "Emphasis on understanding over memorization",
        ],
        style_instructions="""Rewrite content to be clear and engaging while maintaining full rigor.

CORE PRINCIPLES:
1. **Clarity first**: Make every sentence earn its place
2. **Respect intelligence**: Assume capable readers learning new material
3. **Rigor always**: Never sacrifice accuracy for accessibility
4. **Judicious examples**: Use analogies only when they genuinely illuminate, not as decoration
5. **Natural flow**: Guide readers through logical progressions

WHAT TO DO:
- Ensure clear logical flow between ideas
- Explain the "why" behind concepts, not just the "what"
- Use precise language while remaining readable
- Add brief clarifying phrases where technical terms first appear
- Maintain engagement through well-structured prose

WHAT TO AVOID:
- Excessive analogies or metaphors (use sparingly, only when they truly clarify)
- Patronizing explanations or "dumbing down"
- Forced humor or personality quirks
- Over-explaining obvious points
- Repetitive sentence structures

The result should read like a well-written textbook - clear, engaging, and rigorous."""
    ),

    "pragmatic_engineer": AuthorProfile(
        name="Marcus Rodriguez",
        pen_name="Marcus Rodriguez",
        background="""Marcus Rodriguez has two decades of experience building production systems.
A former principal engineer at multiple companies, he brings hard-won practical
insights to technical writing. His focus is on what actually works in practice,
informed by both successes and failures.""",
        expertise="Practical insights grounded in real-world experience",
        writing_style="Direct, practical, grounded in experience",
        humor_style="Occasional dry observations, never forced",
        complexity_level="moderate",
        tone="direct, practical, honest",
        signature_elements=[
            "Focus on practical implications",
            "Honest discussion of trade-offs",
            "Grounded in real-world constraints",
            "Direct recommendations where appropriate",
        ],
        style_instructions="""Rewrite content with a practical, experience-informed perspective while maintaining rigor.

CORE PRINCIPLES:
1. **Practical focus**: Emphasize real-world applicability
2. **Trade-off awareness**: Acknowledge that choices have costs and benefits
3. **Honest assessment**: Be direct about limitations and challenges
4. **Grounded perspective**: Keep theoretical content connected to practice
5. **Full rigor**: Practical doesn't mean imprecise

WHAT TO DO:
- Highlight practical implications of concepts
- Discuss trade-offs where relevant
- Be direct about what works and what doesn't
- Connect theory to application
- Maintain technical precision throughout

WHAT TO AVOID:
- Overusing "junior engineer" / "senior engineer" framings
- Repetitive industry anecdotes or war stories
- Excessive informality or forced personality
- Analogies that don't add clarity
- Patronizing explanations

The result should read like a rigorous technical text written by someone with deep practical experience."""
    ),

    "curious_explorer": AuthorProfile(
        name="Dr. Priya Sharma",
        pen_name="Priya Sharma",
        background="""Dr. Priya Sharma holds a PhD in cognitive science with research experience
spanning neuroscience and AI. She brings an interdisciplinary perspective to technical
writing, drawing connections across fields where they illuminate understanding.""",
        expertise="Interdisciplinary connections that deepen understanding",
        writing_style="Thoughtful, connection-finding, intellectually engaging",
        humor_style="Intellectual curiosity, not forced levity",
        complexity_level="moderate",
        tone="thoughtful, curious, rigorous",
        signature_elements=[
            "Illuminating connections to related concepts",
            "Historical or conceptual context where valuable",
            "Building intuition alongside formalism",
            "Questions that guide understanding",
        ],
        style_instructions="""Rewrite content with intellectual depth and meaningful connections while maintaining rigor.

CORE PRINCIPLES:
1. **Meaningful connections**: Draw links to other concepts only when they deepen understanding
2. **Historical context**: Include origins or evolution of ideas when it illuminates
3. **Intuition and formalism**: Build understanding through both
4. **Genuine depth**: Explore ideas thoroughly, not superficially
5. **Full rigor**: Curiosity enhances precision, never replaces it

WHAT TO DO:
- Connect concepts to broader intellectual context where valuable
- Explain the reasoning behind design choices
- Build intuitive understanding alongside formal definitions
- Use questions that genuinely guide the reader's thinking

WHAT TO AVOID:
- Tangents that don't serve understanding
- Excessive "isn't this fascinating?" enthusiasm
- Analogies for their own sake
- Forced interdisciplinary connections
- Patronizing wonder at basic concepts

The result should read like rigorous technical writing with intellectual depth and meaningful context."""
    ),

    "no_nonsense_expert": AuthorProfile(
        name="Professor James Blackwood",
        pen_name="J.R. Blackwood",
        background="""Professor James Blackwood has thirty years of teaching and research
experience at leading institutions. He is known for cutting through unnecessary
complexity to reveal essential principles. He respects readers' time and intelligence.""",
        expertise="Precise exposition of core principles",
        writing_style="Precise, structured, elegantly clear",
        humor_style="Rare, understated, never at the expense of clarity",
        complexity_level="technical",
        tone="authoritative, clear, respectful",
        signature_elements=[
            "Crystal-clear definitions",
            "Structured logical progression",
            "Precise language",
            "Focus on fundamentals",
        ],
        style_instructions="""Rewrite content with precision and clarity, respecting readers' intelligence.

CORE PRINCIPLES:
1. **Precision**: Every term used deliberately and correctly
2. **Structure**: Clear logical progression of ideas
3. **Respect**: Assume intelligent readers learning new material
4. **Fundamentals**: Emphasize principles that enable deeper understanding
5. **Economy**: No unnecessary words or diversions

WHAT TO DO:
- Define terms precisely when introduced
- Structure exposition logically
- Make connections between ideas explicit
- Focus on the essential aspects of each concept
- Write with confident clarity

WHAT TO AVOID:
- Unnecessary jargon or complexity
- Diversions from the main thread
- Condescension or over-explanation
- Decoration or filler
- Ambiguity where precision is possible

The result should read like an exemplary textbook - precise, clear, well-structured, and respectful of the reader."""
    ),
}


def get_author_profile(author_key: str) -> Optional[AuthorProfile]:
    """Get an author profile by key."""
    return AUTHOR_PROFILES.get(author_key)


def list_available_authors() -> list:
    """List all available author profiles."""
    return [
        {
            "key": key,
            "name": profile.pen_name,
            "style": profile.writing_style,
            "tone": profile.tone,
        }
        for key, profile in AUTHOR_PROFILES.items()
    ]


async def apply_author_style(
    content: str,
    author_profile: AuthorProfile,
    chapter_name: str,
    language_model,
    output_dir: str,
    chapter_number: int
) -> str:
    """
    Apply an author's style to chapter content.

    Returns:
        The styled content
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

    logger.info(f"Applying {author_profile.pen_name}'s style to: {chapter_name}")

    generator = synalinks.Generator(
        data_model=StyledContent,
        language_model=language_model,
        instructions=f"""Refine the provided content with the voice of {author_profile.pen_name}.

AUTHOR: {author_profile.pen_name}
STYLE: {author_profile.writing_style}
TONE: {author_profile.tone}

STYLE GUIDELINES:
{author_profile.style_instructions}

CRITICAL REQUIREMENTS - RIGOR AND RESPECT:

1. **MAINTAIN TEXTBOOK QUALITY**: The output must read like a professional textbook.
   Style adjustments should be subtle, not transformative.

2. **PRESERVE TECHNICAL RIGOR**: All technical content, definitions, and explanations
   must remain precise and accurate. Never sacrifice precision for style.

3. **RESPECT READER INTELLIGENCE**: Assume readers are intelligent adults learning
   new material. Never patronize, over-explain obvious points, or treat readers
   as if they need hand-holding.

4. **USE ANALOGIES SPARINGLY**: Only include an analogy if it genuinely clarifies
   a complex concept. Most technical content does not need analogies. When in doubt,
   leave it out. Excessive analogies hurt rigor and annoy knowledgeable readers.

5. **AVOID FORCED PERSONALITY**: Do not add humor, asides, or stylistic flourishes
   that feel forced or distract from the content. Subtle voice is fine; performance is not.

6. **NO REPETITIVE TROPES**: Avoid repeatedly using the same framings, metaphors,
   or patterns (e.g., "junior vs senior engineer", "imagine you're a...", etc.)

7. **STRUCTURE PRESERVATION**: Keep the same headings, sections, and overall organization.

The goal is refined clarity with a subtle authorial voice - NOT a dramatic rewrite.
Think: 10% style adjustment, 90% the same rigorous content."""
    )

    input_data = AuthorStyleInput(
        original_content=content,
        author_name=author_profile.pen_name,
        author_style=author_profile.writing_style,
        author_tone=author_profile.tone,
        chapter_name=chapter_name
    )

    result = await generator(input_data)
    styled_content = result.get_json().get("styled_content", content)

    # Save the styled content
    if output_dir:
        save_to_file(output_dir, filename, styled_content)

    return styled_content


async def generate_about_author(
    author_profile: AuthorProfile,
    book_name: str,
    topic: str,
    language_model,
    output_dir: str
) -> str:
    """
    Generate the About the Author section.

    Returns:
        The about author content
    """
    filename = "08_about_author.txt"

    # Check for existing about author
    if output_dir and output_exists(output_dir, filename):
        existing = load_from_file(output_dir, filename)
        if existing:
            logger.info("Loaded existing About the Author section")
            return existing

    logger.info(f"Generating About the Author for {author_profile.pen_name}...")

    generator = synalinks.Generator(
        data_model=AboutAuthorOutput,
        language_model=language_model,
        instructions="""Write an engaging "About the Author" section for this book.

The section should:
1. Introduce the author naturally and warmly
2. Highlight their expertise relevant to this book's topic
3. Include interesting personal details that make them relatable
4. Mention any previous works or achievements
5. End with a personal touch (hobbies, where they live, etc.)

Write 2-3 paragraphs in a warm, professional tone.
Do NOT use headers - just flowing prose.
Make it feel authentic and interesting, not like a dry CV."""
    )

    input_data = AboutAuthorInput(
        author_name=author_profile.pen_name,
        author_background=author_profile.background,
        author_expertise=author_profile.expertise,
        book_name=book_name,
        book_topic=topic
    )

    result = await generator(input_data)
    about_content = result.get_json().get("about_author", "")

    # Save the about author section
    if output_dir:
        save_to_file(output_dir, filename, about_content)

    return about_content


async def style_all_chapters(
    polished_chapters: list,
    author_profile: AuthorProfile,
    language_model,
    output_dir: str
) -> list:
    """
    Apply author style to all chapters.

    Returns:
        List of (chapter_name, styled_content) tuples
    """
    styled_chapters = []

    for i, (chapter_name, chapter_data) in enumerate(polished_chapters, 1):
        content = chapter_data.get("chapter_content", "")

        if not content:
            styled_chapters.append((chapter_name, chapter_data))
            continue

        try:
            styled_content = await apply_author_style(
                content,
                author_profile,
                chapter_name,
                language_model,
                output_dir,
                i
            )
            styled_chapters.append((chapter_name, {"chapter_content": styled_content}))
        except Exception as e:
            logger.warning(f"Style application failed for chapter {i}: {e}")
            styled_chapters.append((chapter_name, chapter_data))

    return styled_chapters
