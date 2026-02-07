"""
Deep research module for cutting-edge book generation.

Uses Gemini Deep Research API to discover recent advances,
then Synalinks to parse and structure the knowledge.

Stage 2 research adds:
- arXiv API integration for paper abstracts and PDFs
- mcp-graphiti knowledge graph for entity/relationship tracking
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

# Stage 2: arXiv fetcher
from .arxiv_fetcher import (
    ArxivPaper,
    search_arxiv,
    search_arxiv_by_id,
    search_arxiv_with_gemini,
    batch_search_arxiv_with_gemini,
    download_and_extract_pdf,
    fetch_papers_for_chapter,
    format_paper_for_context,
)

# Stage 2: MCP pipeline
from .stage2 import (
    Stage2MCPPipeline,
    Stage2ArxivFallback,
    run_stage2_research,
)

__all__ = [
    # Models
    "ResearchQuery",
    "ResearchQueries",
    "Paper",
    "Framework",
    "FieldKnowledge",
    "BookTopic",
    "RawResearch",
    # Stage 1
    "DeepResearchClient",
    "generate_research_queries",
    "parse_research",
    "ResearchManager",
    # Stage 2: arXiv
    "ArxivPaper",
    "search_arxiv",
    "search_arxiv_by_id",
    "search_arxiv_with_gemini",
    "batch_search_arxiv_with_gemini",
    "download_and_extract_pdf",
    "fetch_papers_for_chapter",
    "format_paper_for_context",
    # Stage 2: MCP
    "Stage2MCPPipeline",
    "Stage2ArxivFallback",
    "run_stage2_research",
]
