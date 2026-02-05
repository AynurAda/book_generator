"""
Deep research module for cutting-edge book generation.

Uses Gemini Deep Research API to discover recent advances,
then Synalinks to parse and structure the knowledge.
"""

from .models import (
    ResearchQuery,
    ResearchQueries,
    Paper,
    Framework,
    FieldKnowledge,
    BookTopic,
    RawResearch,
)
from .gemini_client import DeepResearchClient
from .query_generator import generate_research_queries
from .parser import parse_research
from .manager import ResearchManager

__all__ = [
    "ResearchQuery",
    "ResearchQueries",
    "Paper",
    "Framework",
    "FieldKnowledge",
    "BookTopic",
    "RawResearch",
    "DeepResearchClient",
    "generate_research_queries",
    "parse_research",
    "ResearchManager",
]
