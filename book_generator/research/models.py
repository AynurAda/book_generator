"""
Synalinks DataModels for deep research.
"""

from typing import List, Optional
import synalinks


class ResearchQuery(synalinks.DataModel):
    """A single research question for deep research."""

    question: str = synalinks.Field(
        description="A conceptual research question focused on understanding methods, theories, and ideas"
    )
    focus_area: str = synalinks.Field(
        description="The aspect of the field this question explores (e.g., 'theoretical advances', 'new methods')"
    )


class ResearchQueries(synalinks.DataModel):
    """Collection of research queries to run."""

    queries: List[ResearchQuery] = synalinks.Field(
        description="3-5 research questions to discover cutting-edge knowledge for the book"
    )


class Paper(synalinks.DataModel):
    """A research paper extracted from deep research."""

    title: str = synalinks.Field(description="Paper title")
    authors: str = synalinks.Field(description="Author names")
    year: int = synalinks.Field(description="Publication year")
    venue: str = synalinks.Field(
        description="Publication venue (NeurIPS, ICML, arXiv, etc.)"
    )

    problem: str = synalinks.Field(description="What problem does this paper solve?")
    method: str = synalinks.Field(description="Key approach or contribution")
    results: str = synalinks.Field(description="Main findings")
    significance: str = synalinks.Field(description="Why this paper matters")


class Framework(synalinks.DataModel):
    """A tool or framework extracted from deep research."""

    name: str = synalinks.Field(description="Framework/library name (e.g., 'PyTorch', 'Scallop')")
    description: str = synalinks.Field(description="What it does in 1-2 sentences")
    approach: str = synalinks.Field(description="How it works conceptually")
    use_cases: str = synalinks.Field(description="What problems it solves, when to use it")
    url: Optional[str] = synalinks.Field(
        default=None, description="GitHub URL or project website for readers to explore"
    )


class FieldKnowledge(synalinks.DataModel):
    """Structured knowledge extracted from deep research."""

    summary: str = synalinks.Field(
        description="2-3 paragraph overview of the current state of the field"
    )
    themes: List[str] = synalinks.Field(
        description="Major research themes and directions"
    )
    papers: List[Paper] = synalinks.Field(
        description="Key papers mentioned in the research"
    )
    frameworks: List[Framework] = synalinks.Field(
        description="Tools and frameworks mentioned"
    )
    open_problems: List[str] = synalinks.Field(
        description="Unsolved challenges and active research questions"
    )


class BookTopic(synalinks.DataModel):
    """Input for research query generation."""

    topic: str = synalinks.Field(description="The book topic")
    goal: str = synalinks.Field(description="What the book aims to achieve")
    audience: str = synalinks.Field(description="Target readers")


class RawResearch(synalinks.DataModel):
    """Raw research text to be parsed."""

    research_text: str = synalinks.Field(
        description="The combined output from all deep research queries"
    )
