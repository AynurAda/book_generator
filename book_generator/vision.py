"""
Book Vision generation module.

This module handles generating a high-level book vision BEFORE concept generation.
The vision establishes the book's purpose, reader journey, and key themes,
which then guide concept generation to ensure better alignment with the book's focus.

Architecture follows Synalinks patterns:
- Multi-branch generation with temperature=1.0 for diversity
- Merge branches with & operator for self-consistency
- Final consolidation pass to synthesize best elements
"""

import logging
import synalinks

from .models import (
    BookVisionInput,
    BookVision,
)
from .utils import (
    output_exists,
    load_json_from_file,
    save_to_file,
    save_json_to_file,
)

logger = logging.getLogger(__name__)


def format_book_vision(vision: dict) -> str:
    """Format book vision as readable text for use in prompts."""
    return f"""BOOK VISION
===========

CORE THESIS:
{vision.get('core_thesis', 'N/A')}

READER JOURNEY:
{vision.get('reader_journey', 'N/A')}

KEY THEMES (concepts MUST cover these):
{chr(10).join(f"- {theme}" for theme in vision.get('key_themes', []))}

SCOPE BOUNDARIES (what NOT to include):
{vision.get('scope_boundaries', 'N/A')}

UNIQUE ANGLE:
{vision.get('unique_angle', 'N/A')}

PREREQUISITE KNOWLEDGE:
{vision.get('prerequisite_knowledge', 'N/A')}
"""


async def generate_book_vision(
    topic_data: dict,
    language_model,
    output_dir: str = None,
    research_context: str = None,
) -> dict:
    """
    Generate the book vision before concept generation.

    Uses multi-branch self-consistency pattern:
    1. Generate 3 diverse vision proposals (temperature=1.0)
    2. Merge with & operator
    3. Synthesize final vision from best elements

    The vision establishes:
    - Core thesis (the one key insight)
    - Reader journey (before/after transformation)
    - Key themes (must be covered)
    - Scope boundaries (what to exclude)
    - Unique angle (differentiation)
    - Prerequisites (what's assumed)

    This vision then guides concept generation to ensure alignment.

    Args:
        topic_data: Dict with topic, goal, book_name, audience
        language_model: The LLM to use
        output_dir: Optional directory to save outputs

    Returns:
        Dictionary with book vision data
    """
    # Check for existing vision
    if output_dir and output_exists(output_dir, "00_book_vision.json"):
        existing = load_json_from_file(output_dir, "00_book_vision.json")
        if existing:
            logger.info("Loaded existing book vision")
            return existing

    logger.info("Generating book vision (multi-branch self-consistency)...")

    input_data = BookVisionInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        audience=topic_data.get("audience", "technical readers")
    )

    # Build instructions with optional research context
    base_instructions = """Propose a VISION for this book that will guide all content generation.

Think carefully about what makes this book focused and valuable.

1. CORE THESIS: What is the ONE central insight? Be specific, not generic.
   Bad: "AI is transforming industries."
   Good: "Neuro-symbolic AI enables AI that can both learn patterns AND reason logically."

2. READER JOURNEY: Describe the transformation.
   - BEFORE: What can't readers do? What do they misunderstand?
   - AFTER: What capabilities will they gain?

3. KEY THEMES: 3-5 NON-NEGOTIABLE topics that MUST be covered.
   Every concept must connect to at least one theme.
   Be specific: not "fundamentals" but "memory safety without garbage collection"

4. SCOPE BOUNDARIES: What is explicitly OUT OF SCOPE?
   This prevents concept sprawl.

5. UNIQUE ANGLE: What makes this treatment special?

6. PREREQUISITES: What knowledge is assumed?

The goal is FOCUS. A great book is focused and deep, not comprehensive."""

    if research_context:
        base_instructions = f"""You have access to recent research findings about this field.
Use this knowledge to inform your vision - ensure the book covers cutting-edge developments.

RECENT RESEARCH SUMMARY:
{research_context}

---

{base_instructions}

IMPORTANT: Your key themes should incorporate the recent advances discovered in the research."""

    # Branch generator - each branch proposes a vision
    branch_generator = synalinks.Generator(
        data_model=BookVision,
        language_model=language_model,
        temperature=1.0,
        instructions=base_instructions,
    )

    # Generate 3 diverse vision proposals (multi-branch pattern)
    branch1 = await branch_generator(input_data)
    branch2 = await branch_generator(input_data)
    branch3 = await branch_generator(input_data)

    # Merge branches with & operator
    merged_visions = branch1 & branch2 & branch3

    # Final synthesis pass - consolidate best elements
    synthesis_generator = synalinks.Generator(
        data_model=BookVision,
        language_model=language_model,
        temperature=1.0,
        instructions="""You have 3 vision proposals for this book. Synthesize them into ONE final vision.

For each element, choose the BEST version from the proposals or combine their strengths:

1. CORE THESIS: Pick the most specific and insightful thesis
2. READER JOURNEY: Combine the clearest before/after descriptions
3. KEY THEMES: Consolidate into 3-5 essential themes (dedupe, keep most important)
4. SCOPE BOUNDARIES: Combine all exclusions mentioned
5. UNIQUE ANGLE: Pick or synthesize the most compelling angle
6. PREREQUISITES: Consolidate prerequisite requirements

The final vision should be sharper and more focused than any individual proposal."""
    )

    final_vision = await synthesis_generator(input_data & merged_visions)
    result_dict = final_vision.get_json()

    # Save the vision
    if output_dir:
        save_json_to_file(output_dir, "00_book_vision.json", result_dict)
        save_to_file(output_dir, "00_book_vision.txt", format_book_vision(result_dict))

    logger.info(f"Generated book vision with {len(result_dict.get('key_themes', []))} key themes")

    return result_dict


async def check_vision_alignment(
    vision: dict,
    concepts: list,
    language_model
) -> tuple:
    """
    Check if generated concepts align with the book vision.

    Args:
        vision: The book vision dict
        concepts: List of concept names
        language_model: The LLM to use

    Returns:
        Tuple of (aligned: bool, missing_themes: list, out_of_scope: list)
    """
    from .models import CoverageCheckInput, CoverageAssessment

    themes = vision.get("key_themes", [])
    scope_boundaries = vision.get("scope_boundaries", "")

    concepts_text = "\n".join(f"- {c}" for c in concepts)
    themes_text = "\n".join(f"- {t}" for t in themes)

    input_data = CoverageCheckInput(
        topic=vision.get("core_thesis", ""),
        goal=f"""The book MUST cover these key themes:
{themes_text}

The book should NOT cover (out of scope):
{scope_boundaries}""",
        current_concepts=concepts_text
    )

    generator = synalinks.Generator(
        data_model=CoverageAssessment,
        language_model=language_model,
        temperature=1.0,
        instructions="""Check if concepts align with the book's vision.

1. THEME COVERAGE: Does every key theme have at least one concept covering it?
2. SCOPE VIOLATION: Are any concepts outside the stated scope boundaries?
3. FOCUS: Are there concepts that don't connect to any key theme?

Be strict: concepts should serve the vision, not sprawl beyond it."""
    )

    result = await generator(input_data)
    if result is None:
        return (True, [], [])

    data = result.get_json()
    return (
        data.get("coverage_adequate", True),
        data.get("missing_topics", []),
        data.get("covered_topics", [])
    )
