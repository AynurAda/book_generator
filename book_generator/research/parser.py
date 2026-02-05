"""
Research parsing using Synalinks.

Extracts structured data from raw deep research output.
"""

import logging
from typing import Dict

import synalinks

from .models import RawResearch, FieldKnowledge

logger = logging.getLogger(__name__)


PARSING_INSTRUCTIONS = """Extract structured information from this research output.

For the SUMMARY:
- Write 2-3 paragraphs capturing the current state of the field
- Focus on what's new, what's changing, and where things are heading
- Make it useful for someone writing a book about this topic

For PAPERS:
- Extract EVERY paper mentioned with full details
- Include: title, authors, year, venue, problem, method, results, significance
- Be thorough - don't skip papers just because details are sparse

For FRAMEWORKS:
- Extract EVERY tool, library, or framework mentioned
- Include: name, what it does, how it works, what it's good for
- Include URLs if mentioned

For THEMES:
- Identify the major research directions and trends
- These should be broad enough to be chapter topics

For OPEN_PROBLEMS:
- List unsolved challenges and active research questions
- These represent the frontier of the field

Be comprehensive - extract ALL information, not just highlights."""


async def build_parser_program(
    language_model: synalinks.LanguageModel,
) -> synalinks.Program:
    """
    Build a Synalinks program that parses research into structured data.

    Args:
        language_model: The language model to use

    Returns:
        A Synalinks Program for research parsing
    """
    inputs = synalinks.Input(data_model=RawResearch)

    outputs = await synalinks.Generator(
        data_model=FieldKnowledge,
        language_model=language_model,
        instructions=PARSING_INSTRUCTIONS,
        temperature=1.0,
    )(inputs)

    return synalinks.Program(
        inputs=inputs,
        outputs=outputs,
        name="research_parser",
        description="Parses raw research text into structured FieldKnowledge",
    )


async def parse_research(
    raw_outputs: Dict[str, str],
    language_model: synalinks.LanguageModel,
) -> FieldKnowledge:
    """
    Parse raw research outputs into structured FieldKnowledge.

    Args:
        raw_outputs: Dict mapping query names to research text
        language_model: The language model to use

    Returns:
        Structured FieldKnowledge object
    """
    # Combine all research outputs
    combined_parts = []
    for name, text in raw_outputs.items():
        if not text.startswith("ERROR:"):
            combined_parts.append(f"=== {name} ===\n\n{text}")

    combined = "\n\n---\n\n".join(combined_parts)

    logger.info(f"Parsing {len(combined)} chars of research text")
    logger.debug(f"Combined text from {len(combined_parts)} queries")

    program = await build_parser_program(language_model)

    input_data = RawResearch(research_text=combined)
    result = await program(input_data)

    if result is None:
        logger.error("Research parsing failed - LLM returned None")
        # Return empty FieldKnowledge
        return FieldKnowledge(
            summary="Research parsing failed.",
            themes=[],
            papers=[],
            frameworks=[],
            open_problems=[],
        )

    # Get JSON and construct FieldKnowledge (consistent with codebase pattern)
    data = result.get_json()

    logger.info(
        f"Parsed research: {len(data.get('papers', []))} papers, "
        f"{len(data.get('frameworks', []))} frameworks, "
        f"{len(data.get('themes', []))} themes"
    )

    return FieldKnowledge(**data)
