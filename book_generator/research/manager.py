"""
Research manager for providing context to pipeline stages.
"""

import logging
from typing import Dict, List, Optional

import synalinks

from .models import FieldKnowledge

logger = logging.getLogger(__name__)


class PaperQueryInput(synalinks.DataModel):
    """Input for paper relevance query."""
    query: str = synalinks.Field(description="The search query")


class FrameworkQueryInput(synalinks.DataModel):
    """Input for framework relevance query."""
    query: str = synalinks.Field(description="The search query")


class ChapterClassificationInput(synalinks.DataModel):
    """Input for chapter classification."""
    chapter_title: str = synalinks.Field(description="The chapter title to classify")
    num_relevant_papers: int = synalinks.Field(description="Number of relevant papers found")


class ResearchManager:
    """
    Manages research data and provides context for pipeline stages.

    This class holds the structured FieldKnowledge from deep research
    and provides methods to retrieve relevant context for each stage
    of the book generation pipeline.

    Uses synalinks.Decision for ALL matching operations. No keyword matching.
    """

    def __init__(self, field_knowledge: FieldKnowledge, language_model: "synalinks.LanguageModel"):
        """
        Initialize the manager with parsed research.

        Args:
            field_knowledge: Structured research data (or dict)
            language_model: Language model for LLM-based matching (REQUIRED).
                           All matching uses synalinks.Decision.

        Raises:
            ValueError: If language_model is not provided.
        """
        if language_model is None:
            raise ValueError("ResearchManager requires a language_model for LLM-based matching. "
                           "All matching operations use synalinks.Decision.")

        # Handle both FieldKnowledge objects and raw dicts
        if isinstance(field_knowledge, dict):
            self._data = field_knowledge
        else:
            self._data = field_knowledge.get_json() if hasattr(field_knowledge, 'get_json') else vars(field_knowledge)

        # Ensure nested objects are accessible as dicts
        self.summary = self._data.get("summary", "")
        self.themes = self._data.get("themes", [])
        self.open_problems = self._data.get("open_problems", [])
        self.papers = self._data.get("papers", [])
        self.frameworks = self._data.get("frameworks", [])

        self.language_model = language_model

    def for_vision(self) -> str:
        """
        Get context for vision generation stage.

        Returns:
            Summary of the field state
        """
        return self.summary

    def for_outline(self) -> str:
        """
        Get context for outline generation stage.

        Returns:
            Summary plus themes to ensure coverage
        """
        themes = "\n".join(f"- {t}" for t in self.themes)
        open_problems = "\n".join(f"- {p}" for p in self.open_problems[:5])

        return f"""{self.summary}

Key themes that should be covered in the book:
{themes}

Open problems and future directions to address:
{open_problems}"""

    async def for_chapter_planning(self, chapter_title: str) -> str:
        """
        Get context for planning a specific chapter.

        Args:
            chapter_title: The chapter title/topic

        Returns:
            Relevant paper briefs for this chapter
        """
        relevant_papers = await self._find_relevant_papers(chapter_title, top_k=10)
        relevant_frameworks = await self._find_relevant_frameworks(chapter_title, top_k=5)

        if not relevant_papers and not relevant_frameworks:
            return ""

        lines = ["Recent research relevant to this chapter:"]

        for p in relevant_papers:
            lines.append(f"\n**{p.get('title', 'Unknown')}** ({p.get('authors', 'Unknown')}, {p.get('year', 'N/A')})")
            lines.append(f"- Problem: {p.get('problem', 'N/A')}")
            lines.append(f"- Approach: {p.get('method', 'N/A')}")

        if relevant_frameworks:
            lines.append("\n\nRelevant frameworks/tools:")
            for fw in relevant_frameworks:
                lines.append(f"\n**{fw.get('name', 'Unknown')}**: {fw.get('description', 'N/A')}")

        return "\n".join(lines)

    async def for_section_writing(self, chapter: str, section: str, assigned_papers: List[str] = None) -> str:
        """
        Get context for writing a specific section.

        Args:
            chapter: The chapter title
            section: The section title
            assigned_papers: Optional list of paper titles assigned to this chapter.
                             If provided, only these papers will be included.

        Returns:
            Full paper details for relevant papers
        """
        query = f"{chapter} {section}"

        if assigned_papers:
            # Filter to only papers assigned to this chapter using LLM
            relevant_papers = await self._filter_papers_by_titles(assigned_papers)
            logger.debug(f"Using {len(relevant_papers)} assigned papers for {chapter}")
        else:
            # Find relevant papers using LLM
            relevant_papers = await self._find_relevant_papers(query, top_k=4)

        relevant_frameworks = await self._find_relevant_frameworks(query, top_k=3)

        if not relevant_papers and not relevant_frameworks:
            return ""

        lines = ["Use these recent findings in your writing:"]

        for p in relevant_papers:
            lines.append(f"\n**{p.get('title', 'Unknown')}** ({p.get('authors', 'Unknown')}, {p.get('year', 'N/A')}, {p.get('venue', 'N/A')})")
            lines.append(f"- Problem: {p.get('problem', 'N/A')}")
            lines.append(f"- Method: {p.get('method', 'N/A')}")
            lines.append(f"- Results: {p.get('results', 'N/A')}")
            lines.append(f"- Significance: {p.get('significance', 'N/A')}")

        if relevant_frameworks:
            lines.append("\n\nRelevant frameworks to mention:")
            for fw in relevant_frameworks:
                lines.append(f"\n**{fw.get('name', 'Unknown')}**")
                lines.append(f"- What: {fw.get('description', 'N/A')}")
                lines.append(f"- How: {fw.get('approach', 'N/A')}")
                lines.append(f"- Use cases: {fw.get('use_cases', 'N/A')}")

        return "\n".join(lines)

    async def _find_relevant_papers(self, query: str, top_k: int = 5) -> List[dict]:
        """
        Find papers relevant to a query using synalinks.Decision.

        Args:
            query: Search query
            top_k: Maximum papers to return

        Returns:
            List of relevant papers (as dicts)
        """
        if not self.papers:
            return []

        # Build paper descriptions for Decision
        paper_labels = []
        paper_descriptions = []
        for i, p in enumerate(self.papers):
            title = p.get('title', f'Paper {i+1}')
            paper_labels.append(title)
            paper_descriptions.append(
                f"{title} ({p.get('year', 'N/A')}): {p.get('problem', 'N/A')[:100]}"
            )

        papers_text = "\n".join(f"  {i+1}. {desc}" for i, desc in enumerate(paper_descriptions))

        # Use Decision to select relevant papers (multi-select simulation via multiple calls)
        selected_papers = []
        remaining_papers = list(self.papers)
        remaining_labels = list(paper_labels)

        for _ in range(min(top_k, len(self.papers))):
            if not remaining_labels:
                break

            papers_list = "\n".join(
                f"  {i+1}. {remaining_labels[i]} ({remaining_papers[i].get('year', 'N/A')})"
                for i in range(len(remaining_labels))
            )

            try:
                query_input = PaperQueryInput(query=query)
                decision = await synalinks.Decision(
                    question=f"""Which paper is MOST relevant to this query?

QUERY: "{query}"

AVAILABLE PAPERS:
{papers_list}

Select the single most relevant paper, or select "None relevant" if no papers match.""",
                    labels=remaining_labels + ["None relevant"],
                    language_model=self.language_model,
                    temperature=1.0,
                )(query_input)

                if decision is None:
                    break

                selected_label = decision.get_json().get("label")
                if selected_label and selected_label != "None relevant":
                    # Find and add the selected paper
                    for i, label in enumerate(remaining_labels):
                        if label == selected_label:
                            selected_papers.append(remaining_papers[i])
                            # Remove from remaining
                            remaining_labels.pop(i)
                            remaining_papers.pop(i)
                            break
                else:
                    break  # No more relevant papers
            except Exception as e:
                logger.warning(f"Paper selection failed: {e}")
                break

        return selected_papers

    async def _filter_papers_by_titles(self, paper_titles: List[str]) -> List[dict]:
        """
        Filter papers to only those matching the given titles using synalinks.Decision.

        Args:
            paper_titles: List of paper titles to filter by

        Returns:
            List of matching papers (as dicts)
        """
        if not paper_titles or not self.papers:
            return []

        result = []
        all_paper_titles = [p.get('title', '') for p in self.papers]

        for query_title in paper_titles:
            # Use Decision to find the best match
            papers_text = "\n".join(
                f"  {i+1}. {title} ({self.papers[i].get('year', 'N/A')})"
                for i, title in enumerate(all_paper_titles)
            )

            try:
                query_input = PaperQueryInput(query=query_title)
                decision = await synalinks.Decision(
                    question=f"""Which paper from the database matches this title?

QUERY TITLE: "{query_title}"

AVAILABLE PAPERS:
{papers_text}

Select the paper that best matches the query title. The query may include a year suffix.""",
                    labels=all_paper_titles + ["No match"],
                    language_model=self.language_model,
                    temperature=1.0,
                )(query_input)

                if decision is None:
                    continue

                selected_label = decision.get_json().get("label")
                if selected_label and selected_label != "No match":
                    for i, title in enumerate(all_paper_titles):
                        if title == selected_label and self.papers[i] not in result:
                            result.append(self.papers[i])
                            break
            except Exception as e:
                logger.warning(f"Paper title matching failed for '{query_title[:40]}...': {e}")

        return result

    async def _find_relevant_frameworks(self, query: str, top_k: int = 3) -> List[dict]:
        """
        Find frameworks relevant to a query using synalinks.Decision.

        Args:
            query: Search query
            top_k: Maximum frameworks to return

        Returns:
            List of relevant frameworks (as dicts)
        """
        if not self.frameworks:
            return []

        fw_labels = [fw.get('name', f'Framework {i+1}') for i, fw in enumerate(self.frameworks)]
        fw_text = "\n".join(
            f"  {i+1}. {fw.get('name', 'Unknown')}: {fw.get('description', 'N/A')[:80]}"
            for i, fw in enumerate(self.frameworks)
        )

        selected_frameworks = []
        remaining_fws = list(self.frameworks)
        remaining_labels = list(fw_labels)

        for _ in range(min(top_k, len(self.frameworks))):
            if not remaining_labels:
                break

            fws_list = "\n".join(
                f"  {i+1}. {remaining_labels[i]}: {remaining_fws[i].get('description', 'N/A')[:60]}"
                for i in range(len(remaining_labels))
            )

            try:
                query_input = FrameworkQueryInput(query=query)
                decision = await synalinks.Decision(
                    question=f"""Which framework/tool is MOST relevant to this query?

QUERY: "{query}"

AVAILABLE FRAMEWORKS:
{fws_list}

Select the single most relevant framework, or select "None relevant" if none match.""",
                    labels=remaining_labels + ["None relevant"],
                    language_model=self.language_model,
                    temperature=1.0,
                )(query_input)

                if decision is None:
                    break

                selected_label = decision.get_json().get("label")
                if selected_label and selected_label != "None relevant":
                    for i, label in enumerate(remaining_labels):
                        if label == selected_label:
                            selected_frameworks.append(remaining_fws[i])
                            remaining_labels.pop(i)
                            remaining_fws.pop(i)
                            break
                else:
                    break
            except Exception as e:
                logger.warning(f"Framework selection failed: {e}")
                break

        return selected_frameworks

    async def classify_chapter(self, chapter_title: str) -> str:
        """
        Classify chapter as 'foundational' or 'cutting-edge' using synalinks.Decision.

        Args:
            chapter_title: The chapter title

        Returns:
            'foundational' or 'cutting-edge'
        """
        relevant_papers = await self._find_relevant_papers(chapter_title, top_k=10)
        num_papers = len(relevant_papers)

        # Use synalinks.Decision to classify the chapter
        try:
            classification_input = ChapterClassificationInput(
                chapter_title=chapter_title,
                num_relevant_papers=num_papers,
            )

            decision = await synalinks.Decision(
                question=f"""Classify this chapter as 'foundational' or 'cutting-edge'.

CHAPTER TITLE: "{chapter_title}"
NUMBER OF RECENT RESEARCH PAPERS FOUND: {num_papers}

FOUNDATIONAL chapters cover:
- Introductory material, basics, fundamentals
- Historical background, principles, foundations
- Getting started guides, overviews
- Established concepts that are prerequisites

CUTTING-EDGE chapters cover:
- Recent research advances (indicated by many relevant papers)
- Novel methods and techniques
- State-of-the-art approaches
- Active research areas

Classify this chapter:""",
                labels=["foundational", "cutting-edge"],
                language_model=self.language_model,
                temperature=1.0,
            )(classification_input)

            if decision is None:
                return "foundational"

            selected_label = decision.get_json().get("label")
            return selected_label if selected_label in ["foundational", "cutting-edge"] else "foundational"

        except Exception as e:
            logger.error(f"Chapter classification failed for '{chapter_title[:40]}...': {e}")
            # Safe default when LLM call fails (no keyword matching)
            return "foundational"

    def get_all_papers(self) -> List[dict]:
        """Get all papers from research."""
        return self.papers

    def get_all_frameworks(self) -> List[dict]:
        """Get all frameworks from research."""
        return self.frameworks

    def get_themes(self) -> List[str]:
        """Get research themes."""
        return self.themes

    def get_open_problems(self) -> List[str]:
        """Get open problems."""
        return self.open_problems
