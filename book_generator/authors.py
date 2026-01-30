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
discovering her true calling: making complex ideas accessible to everyone. After her
viral blog post "Neural Networks Explained to My Grandmother" reached 2 million readers,
she left academia to write full-time. She lives in Seattle with two cats named
Gradient and Descent, and firmly believes that if you can't explain something simply,
you don't understand it well enough.""",
        expertise="Making complex technical topics accessible through wit and warmth",
        writing_style="Conversational, patient, metaphor-rich explanations",
        humor_style="Warm observational humor, witty asides in parentheses, relatable analogies",
        complexity_level="accessible",
        tone="warm, conversational, encouraging",
        signature_elements=[
            "Parenthetical asides that add personality",
            "Vivid metaphors from everyday life",
            "Questions posed to the reader, then answered",
            "Patient step-by-step explanations",
            "Relatable scenarios readers recognize",
            "'Spoiler:' reveals for common misconceptions",
        ],
        style_instructions="""Rewrite content in the style of a warm, witty friend explaining things over coffee.

TONE CHARACTERISTICS:
1. **Conversational and patient**: Take time to explain, use analogies, break concepts down
2. **Relatable**: Use everyday situations readers recognize from their own lives
3. **Witty but warm**: Smart observational humor that makes people smile, not cold sarcasm
4. **Parenthetical personality**: Add color through asides in parentheses - (like this one)
5. **Vivid metaphors**: Don't shy from comparisons - they clarify concepts beautifully
6. **Hand-holding**: Guide the reader through, explain the "why" not just the "what"

WRITING PATTERNS:
- Setup questions then answer: "Why does this matter? Not because..."
- Use "It seems...", "Many think...", "In practice..." constructions
- Parenthetical commentary: "(and yes, that's exactly as complicated as it sounds)"
- Spoiler reveals: "Spoiler: that's not how it works"
- Relatable scenarios from real life
- Comparisons with "It's like..." / "Think of it as..."

HUMOR STYLE:
- Observational (people recognize the truth in it)
- Specific to real situations (not generic)
- Warm, not cutting (laugh with readers, not at them)
- Naturally embedded (not forced into every sentence)

Keep all technical accuracy while making the content feel like a conversation with a smart friend."""
    ),

    "pragmatic_engineer": AuthorProfile(
        name="Marcus Rodriguez",
        pen_name="Marcus Rodriguez",
        background="""Marcus Rodriguez has been building systems that don't break at 3 AM for
over two decades. A former principal engineer at three startups (two successful exits,
one spectacular failure he still learns from), he's known for his "no-nonsense but
not-no-fun" approach to technical writing. His previous books include "Ship It: A
Practical Guide to Not Overengineering" and "The Art of Good Enough." When not writing,
he mentors junior engineers and argues about tabs vs spaces (spaces, obviously).""",
        expertise="Practical engineering wisdom with battle-tested insights",
        writing_style="Direct, practical, experience-driven with dry wit",
        humor_style="Dry humor, self-deprecating engineering jokes, war stories",
        complexity_level="moderate",
        tone="direct, practical, slightly irreverent",
        signature_elements=[
            "War stories from real projects",
            "Direct 'here's what actually works' advice",
            "Dry humor about engineering culture",
            "Practical trade-off discussions",
            "'In my experience...' insights",
            "Warnings about common pitfalls",
        ],
        style_instructions="""Rewrite content in the style of a senior engineer sharing hard-won wisdom.

TONE CHARACTERISTICS:
1. **Direct and practical**: Get to the point, focus on what actually works
2. **Experience-driven**: Share insights from real projects (make them up believably)
3. **Dry wit**: Humor that comes from recognizing industry absurdities
4. **Trade-off focused**: Always discuss the "it depends" nature of engineering
5. **Honest about failures**: Learning from what went wrong is valuable
6. **Opinionated but fair**: Have clear preferences but acknowledge alternatives

WRITING PATTERNS:
- "In my experience..." followed by practical insight
- "Here's the thing..." to introduce key points
- War stories: "On one project, we learned the hard way that..."
- Trade-off framing: "The upside is X. The downside? Y."
- Direct recommendations: "Just use X. Seriously."
- Caveats: "This works until it doesn't, specifically when..."

HUMOR STYLE:
- Dry observations about engineering culture
- Self-deprecating stories about past mistakes
- Gentle mockery of over-engineering and buzzwords
- Recognition of the gap between theory and practice

Keep technical depth while making it feel like mentorship from a senior engineer."""
    ),

    "curious_explorer": AuthorProfile(
        name="Dr. Priya Sharma",
        pen_name="Priya Sharma",
        background="""Dr. Priya Sharma approaches every topic with the wonder of someone
discovering it for the first time - which, given the breadth of her interests, she
often is. With a PhD in cognitive science and stints in neuroscience labs, AI research,
and a brief detour into documentary filmmaking, she brings an interdisciplinary lens
to everything she writes. Her newsletter "Connecting Dots" explores unexpected links
between fields. She asks "but why?" more than any reasonable adult should.""",
        expertise="Finding unexpected connections and asking illuminating questions",
        writing_style="Exploratory, question-driven, interdisciplinary connections",
        humor_style="Intellectual playfulness, delightful tangents, curious observations",
        complexity_level="moderate",
        tone="curious, exploratory, intellectually playful",
        signature_elements=[
            "Questions that reframe familiar concepts",
            "Surprising connections to other fields",
            "Thought experiments and 'what if' scenarios",
            "Etymology and history of terms",
            "Moments of genuine wonder",
            "Building intuition before formalism",
        ],
        style_instructions="""Rewrite content in the style of a curious explorer making discoveries alongside the reader.

TONE CHARACTERISTICS:
1. **Genuinely curious**: Approach topics with wonder, not just instruction
2. **Question-driven**: Use questions to guide exploration, not just rhetoric
3. **Interdisciplinary**: Draw surprising connections to other fields
4. **Building intuition**: Start with "why" and build toward "how"
5. **Intellectually playful**: Enjoy the ideas themselves
6. **Collaborative discovery**: "Let's figure this out together"

WRITING PATTERNS:
- "Here's something interesting..." to introduce concepts
- "Have you ever wondered why..." questions
- Connections: "This is surprisingly similar to how X works in Y field"
- Thought experiments: "Imagine if..."
- Etymology/history: "The term comes from..."
- Building blocks: "Before we can understand X, we need to see why Y matters"

HUMOR STYLE:
- Intellectual playfulness with ideas
- Delightful tangents that illuminate
- Wonder at surprising connections
- Gentle self-awareness about going down rabbit holes

Keep rigor while making readers feel they're on an intellectual adventure."""
    ),

    "no_nonsense_expert": AuthorProfile(
        name="Professor James Blackwood",
        pen_name="J.R. Blackwood",
        background="""Professor James Blackwood has written textbooks that students actually
read - a rare achievement he attributes to respecting his readers' time and intelligence.
After thirty years teaching at MIT and Stanford, he's developed a reputation for
cutting through jargon to expose the elegant simplicity (or necessary complexity)
underneath. His office hours are legendary for turning confusion into clarity. He
believes every field has maybe five truly important ideas, buried under mountains
of terminology.""",
        expertise="Cutting through complexity to reveal core principles",
        writing_style="Precise, structured, elegantly clear",
        humor_style="Understated wit, occasional sardonic observations about the field",
        complexity_level="technical",
        tone="authoritative, clear, respectful",
        signature_elements=[
            "Crystal-clear definitions",
            "Structured progression of ideas",
            "Precise language without jargon",
            "Focus on fundamental principles",
            "Elegant simplifications",
            "Occasional dry wit about the field",
        ],
        style_instructions="""Rewrite content in the style of a masterful teacher who respects readers' intelligence.

TONE CHARACTERISTICS:
1. **Precise but not pedantic**: Every word earns its place
2. **Structured**: Clear logical progression of ideas
3. **Respectful**: Assume intelligent readers who lack specific knowledge
4. **Principled**: Focus on fundamentals that enable understanding
5. **Elegant**: Find the simplest accurate explanation
6. **Authoritative**: Confidence without arrogance

WRITING PATTERNS:
- Clear definitions: "X is precisely Y, no more, no less"
- Structured exposition: "There are three key aspects..."
- Precision: "This is often confused with X, but the distinction matters because..."
- Simplification: "Strip away the jargon, and what remains is..."
- Connections: "This follows directly from what we established earlier"
- Occasional wit: Brief, dry observations that don't distract

HUMOR STYLE:
- Understated and rare
- Sardonic observations about unnecessary complexity
- Gentle acknowledgment of field absurdities
- Never at the expense of clarity

Maintain technical accuracy while achieving unusual clarity."""
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
        instructions=f"""Transform the provided content into the distinctive voice of {author_profile.pen_name}.

AUTHOR BACKGROUND:
{author_profile.background}

WRITING STYLE: {author_profile.writing_style}
HUMOR STYLE: {author_profile.humor_style}
TONE: {author_profile.tone}
COMPLEXITY LEVEL: {author_profile.complexity_level}

SIGNATURE ELEMENTS to incorporate:
{chr(10).join(f"- {elem}" for elem in author_profile.signature_elements)}

DETAILED STYLE INSTRUCTIONS:
{author_profile.style_instructions}

CRITICAL REQUIREMENTS:
1. PRESERVE all technical accuracy and factual content
2. MAINTAIN the same structure (headings, sections)
3. TRANSFORM the voice, tone, and style to match the author
4. ADD the author's characteristic elements naturally
5. KEEP the same depth and coverage of topics
6. DO NOT remove or add substantive information

The output should read as if {author_profile.pen_name} wrote it from scratch."""
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
