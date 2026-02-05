"""
Research manager for providing context to pipeline stages.
"""

import logging
from typing import Dict, List, Optional

from .models import FieldKnowledge

logger = logging.getLogger(__name__)


class ResearchManager:
    """
    Manages research data and provides context for pipeline stages.

    This class holds the structured FieldKnowledge from deep research
    and provides methods to retrieve relevant context for each stage
    of the book generation pipeline.
    """

    def __init__(self, field_knowledge: FieldKnowledge):
        """
        Initialize the manager with parsed research.

        Args:
            field_knowledge: Structured research data (or dict)
        """
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

        self._paper_index = self._build_paper_index()
        self._framework_index = self._build_framework_index()

    def _build_paper_index(self) -> Dict[str, List[dict]]:
        """Build keyword index for paper retrieval."""
        index: Dict[str, List[dict]] = {}

        for paper in self.papers:
            # Extract keywords from title, problem, and method (dict access)
            text = f"{paper.get('title', '')} {paper.get('problem', '')} {paper.get('method', '')}".lower()
            words = set(text.split())

            for word in words:
                # Skip short words and common words
                if len(word) > 3 and word not in {"this", "that", "with", "from", "have"}:
                    if word not in index:
                        index[word] = []
                    if paper not in index[word]:
                        index[word].append(paper)

        return index

    def _build_framework_index(self) -> Dict[str, List[dict]]:
        """Build keyword index for framework retrieval."""
        index: Dict[str, List[dict]] = {}

        for fw in self.frameworks:
            text = f"{fw.get('name', '')} {fw.get('description', '')} {fw.get('approach', '')}".lower()
            words = set(text.split())

            for word in words:
                if len(word) > 3:
                    if word not in index:
                        index[word] = []
                    if fw not in index[word]:
                        index[word].append(fw)

        return index

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

    def for_chapter_planning(self, chapter_title: str) -> str:
        """
        Get context for planning a specific chapter.

        Args:
            chapter_title: The chapter title/topic

        Returns:
            Relevant paper briefs for this chapter
        """
        relevant_papers = self._find_relevant_papers(chapter_title, top_k=10)
        relevant_frameworks = self._find_relevant_frameworks(chapter_title, top_k=5)

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

    def for_section_writing(self, chapter: str, section: str) -> str:
        """
        Get context for writing a specific section.

        Args:
            chapter: The chapter title
            section: The section title

        Returns:
            Full paper details for relevant papers
        """
        query = f"{chapter} {section}"
        relevant_papers = self._find_relevant_papers(query, top_k=4)
        relevant_frameworks = self._find_relevant_frameworks(query, top_k=3)

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

    def _find_relevant_papers(self, query: str, top_k: int = 5) -> List[dict]:
        """
        Find papers relevant to a query using keyword matching.

        Args:
            query: Search query
            top_k: Maximum papers to return

        Returns:
            List of relevant papers (as dicts)
        """
        query_words = set(query.lower().split())

        paper_scores: Dict[str, int] = {}

        for word in query_words:
            if word in self._paper_index:
                for paper in self._paper_index[word]:
                    paper_id = paper.get('title', '')
                    paper_scores[paper_id] = paper_scores.get(paper_id, 0) + 1

        # Sort by score
        sorted_papers = sorted(
            paper_scores.items(), key=lambda x: x[1], reverse=True
        )

        # Get paper dicts
        result = []
        for title, _ in sorted_papers[:top_k]:
            for p in self.papers:
                if p.get('title') == title:
                    result.append(p)
                    break

        return result

    def _find_relevant_frameworks(self, query: str, top_k: int = 3) -> List[dict]:
        """
        Find frameworks relevant to a query.

        Args:
            query: Search query
            top_k: Maximum frameworks to return

        Returns:
            List of relevant frameworks (as dicts)
        """
        query_words = set(query.lower().split())

        fw_scores: Dict[str, int] = {}

        for word in query_words:
            if word in self._framework_index:
                for fw in self._framework_index[word]:
                    fw_scores[fw.get('name', '')] = fw_scores.get(fw.get('name', ''), 0) + 1

        sorted_fws = sorted(fw_scores.items(), key=lambda x: x[1], reverse=True)

        result = []
        for name, _ in sorted_fws[:top_k]:
            for fw in self.frameworks:
                if fw.get('name') == name:
                    result.append(fw)
                    break

        return result

    def classify_chapter(self, chapter_title: str) -> str:
        """
        Classify chapter as 'foundational' or 'cutting-edge'.

        Args:
            chapter_title: The chapter title

        Returns:
            'foundational' or 'cutting-edge'
        """
        relevant_papers = self._find_relevant_papers(chapter_title, top_k=10)

        # If we have 3+ relevant recent papers, it's cutting-edge
        if len(relevant_papers) >= 3:
            return "cutting-edge"

        # Check for foundational keywords
        foundational_keywords = {
            "introduction", "basics", "fundamentals", "history",
            "background", "principles", "foundations", "overview",
            "what is", "getting started"
        }

        title_lower = chapter_title.lower()
        for keyword in foundational_keywords:
            if keyword in title_lower:
                return "foundational"

        # Default to foundational if few papers found
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
