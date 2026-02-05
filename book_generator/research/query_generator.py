"""
Research query generation using Synalinks.

Dynamically generates research questions based on book topic and goal.
"""

import logging
from typing import List

import synalinks

from .models import BookTopic, ResearchQueries

logger = logging.getLogger(__name__)


QUERY_GENERATION_INSTRUCTIONS = """Generate 3-5 research questions to discover cutting-edge knowledge for this book.

The questions should help uncover:
- New theoretical frameworks and paradigms (focus on 2024-2025)
- Recent methods and how they work conceptually
- Important papers and their key contributions
- Current tools, frameworks, and libraries
- Open problems and future research directions

Each question should be:
- Conceptually focused (asking about IDEAS and METHODS, not statistics)
- Open-ended enough for deep research
- Specific enough to get actionable knowledge

DO NOT ask about:
- Industry statistics, market trends, or adoption rates
- Company valuations or funding
- Popularity rankings

The goal is to discover knowledge that will help write an educational, cutting-edge book."""


async def build_query_generator_program(
    language_model: synalinks.LanguageModel,
) -> synalinks.Program:
    """
    Build a Synalinks program that generates research queries.

    Args:
        language_model: The language model to use

    Returns:
        A Synalinks Program for query generation
    """
    inputs = synalinks.Input(data_model=BookTopic)

    outputs = await synalinks.Generator(
        data_model=ResearchQueries,
        language_model=language_model,
        instructions=QUERY_GENERATION_INSTRUCTIONS,
        temperature=1.0,
    )(inputs)

    return synalinks.Program(
        inputs=inputs,
        outputs=outputs,
        name="research_query_generator",
        description="Generates research queries for deep research based on book topic",
    )


async def generate_research_queries(
    topic: str,
    goal: str,
    audience: str,
    language_model: synalinks.LanguageModel,
) -> List[str]:
    """
    Generate research queries for a book topic.

    Args:
        topic: The book topic
        goal: What the book aims to achieve
        audience: Target readers
        language_model: The language model to use

    Returns:
        List of research question strings
    """
    logger.info(f"Generating research queries for topic: {topic}")

    program = await build_query_generator_program(language_model)

    input_data = BookTopic(
        topic=topic,
        goal=goal,
        audience=audience,
    )

    result = await program(input_data)

    if result is None:
        logger.error("Query generation failed - LLM returned None")
        return []

    # Get JSON and extract queries (consistent with codebase pattern)
    data = result.get_json()
    queries = [q["question"] for q in data["queries"]]

    logger.info(f"Generated {len(queries)} research queries")
    for i, q in enumerate(queries):
        logger.debug(f"  Query {i + 1}: {q[:80]}...")

    return queries
