"""
arXiv paper fetcher with full PDF text extraction.

This module provides functionality to:
- Search arXiv using Gemini with Google Search grounding (primary method)
- Fallback to arxiv library for direct ID lookups
- Extract full text using arxiv2text (simpler than PyMuPDF)
- Parse common paper sections (abstract, introduction, method, results, conclusion)
"""

import os
import re
import json
import logging
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional

import arxiv
import litellm
from arxiv2text import arxiv_to_text

logger = logging.getLogger(__name__)


# =============================================================================
# Gemini Search-Grounded arXiv Lookup
# =============================================================================

async def search_arxiv_with_gemini(
    paper_title: str,
    model: str = "gemini/gemini-3-flash-preview",
    max_retries: int = 2,
) -> Optional[str]:
    """
    Use Gemini with Google Search grounding to find arXiv ID for a paper.

    This is more reliable than fuzzy title matching because Gemini can
    understand paper titles and find the correct arXiv page.

    Args:
        paper_title: The paper title to search for
        model: Gemini model to use (must support Google Search)
        max_retries: Number of retry attempts

    Returns:
        arXiv ID (e.g., "1706.03762") or None if not found
    """
    prompt = f"""Find the arXiv paper ID for this academic paper:

Title: "{paper_title}"

Search for this paper on arXiv and return ONLY the arXiv ID in the format like "1706.03762" or "2301.00001".
If you find the paper, respond with just the ID number, nothing else.
If you cannot find this exact paper on arXiv, respond with "NOT_FOUND".

Important: Only return an arXiv ID if you are confident it matches the paper title."""

    for attempt in range(max_retries):
        try:
            response = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0,  # Required for Gemini 3 models
                max_tokens=100,
                tools=[{"googleSearch": {}}],  # Google Search grounding (camelCase)
            )

            result = response.choices[0].message.content.strip()
            logger.debug(f"[arXiv-Gemini] Response for '{paper_title[:40]}...': {result}")

            # Check if not found
            if "NOT_FOUND" in result.upper() or "not found" in result.lower():
                return None

            # Extract arXiv ID pattern (e.g., 1706.03762, 2301.00001, cs/0001001)
            arxiv_patterns = [
                r'\b(\d{4}\.\d{4,5}(?:v\d+)?)\b',  # New format: 1706.03762
                r'\b([a-z-]+/\d{7}(?:v\d+)?)\b',    # Old format: cs/0001001
            ]

            for pattern in arxiv_patterns:
                match = re.search(pattern, result)
                if match:
                    arxiv_id = match.group(1)
                    # Remove version suffix if present
                    arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
                    logger.info(f"[arXiv-Gemini] Found: {arxiv_id} for '{paper_title[:40]}...'")
                    return arxiv_id

            logger.debug(f"[arXiv-Gemini] No arXiv ID pattern in response: {result}")
            return None

        except Exception as e:
            logger.warning(f"[arXiv-Gemini] Error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)

    return None


async def batch_search_arxiv_with_gemini(
    paper_titles: List[str],
    model: str = "gemini/gemini-3-flash-preview",
    batch_size: int = 5,
) -> Dict[str, Optional[str]]:
    """
    Batch search for multiple papers using Gemini with Google Search.

    Processes papers in batches to avoid rate limiting.

    Args:
        paper_titles: List of paper titles to search
        model: Gemini model to use
        batch_size: Number of papers to search in parallel

    Returns:
        Dict mapping paper titles to arXiv IDs (or None if not found)
    """
    results = {}

    for i in range(0, len(paper_titles), batch_size):
        batch = paper_titles[i:i + batch_size]
        logger.info(f"[arXiv-Gemini] Batch {i//batch_size + 1}: searching {len(batch)} papers...")

        # Search in parallel within batch
        tasks = [search_arxiv_with_gemini(title, model) for title in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for title, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                logger.warning(f"[arXiv-Gemini] Exception for '{title[:40]}...': {result}")
                results[title] = None
            else:
                results[title] = result

        # Small delay between batches to avoid rate limiting
        if i + batch_size < len(paper_titles):
            await asyncio.sleep(0.5)

    found = sum(1 for v in results.values() if v is not None)
    logger.info(f"[arXiv-Gemini] Found {found}/{len(paper_titles)} papers on arXiv")
    return results


@dataclass
class ArxivPaper:
    """Represents an arXiv paper with metadata and extracted content."""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    published: str
    pdf_url: str
    full_text: str = ""  # Extracted from PDF
    sections: Dict[str, str] = field(default_factory=dict)  # {intro, method, results, conclusion}


def _convert_arxiv_result(result: arxiv.Result) -> ArxivPaper:
    """Convert arxiv.Result to our ArxivPaper dataclass."""
    # Extract arXiv ID from entry_id URL
    # Format: http://arxiv.org/abs/1706.03762v7
    arxiv_id = result.entry_id.split("/abs/")[-1] if result.entry_id else ""

    return ArxivPaper(
        arxiv_id=arxiv_id,
        title=result.title.replace("\n", " ").strip(),
        authors=[author.name for author in result.authors],
        abstract=result.summary.strip(),
        published=result.published.strftime("%Y-%m-%d") if result.published else "",
        pdf_url=result.pdf_url or "",
    )


async def search_arxiv(
    query: str,
    max_results: int = 20,
    max_retries: int = 3,
) -> List[ArxivPaper]:
    """
    Search arXiv by title/query.

    Args:
        query: Search query (title search by default)
        max_results: Maximum number of results to return
        max_retries: Maximum number of retry attempts

    Returns:
        List of ArxivPaper objects with metadata (no full text yet)
    """
    def _search_sync():
        # Use all-field search for better recall (not just title)
        # arXiv's ti: search is too restrictive for fuzzy title matching
        search = arxiv.Search(
            query=query,  # Search all fields, not just title
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        client = arxiv.Client()
        return list(client.results(search))

    for attempt in range(max_retries):
        try:
            # Run synchronous arxiv library in thread pool
            results = await asyncio.to_thread(_search_sync)
            return [_convert_arxiv_result(r) for r in results]

        except arxiv.HTTPError as e:
            if "429" in str(e) or "rate" in str(e).lower():
                wait_time = 3 * (attempt + 2)
                logger.warning(f"arXiv rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
                continue
            logger.warning(f"arXiv search failed: {e}")
            return []
        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return []

    logger.warning(f"arXiv search exhausted retries for query: {query[:50]}...")
    return []


async def search_arxiv_by_id(arxiv_id: str) -> Optional[ArxivPaper]:
    """
    Fetch a specific paper by arXiv ID.

    Args:
        arxiv_id: The arXiv paper ID (e.g., "1706.03762")

    Returns:
        ArxivPaper object or None if not found
    """
    def _search_by_id_sync():
        search = arxiv.Search(id_list=[arxiv_id])
        client = arxiv.Client()
        return list(client.results(search))

    try:
        results = await asyncio.to_thread(_search_by_id_sync)
        if results:
            return _convert_arxiv_result(results[0])
        return None

    except Exception as e:
        logger.warning(f"Failed to fetch arXiv paper {arxiv_id}: {e}")
        return None


async def download_and_extract_pdf(
    paper: ArxivPaper,
    cache_dir: str,
    max_chars: int = 100000,
) -> ArxivPaper:
    """
    Extract full text from arXiv paper using arxiv2text.

    Args:
        paper: ArxivPaper with pdf_url
        cache_dir: Directory to cache extracted text
        max_chars: Maximum characters to extract (to limit memory)

    Returns:
        ArxivPaper with full_text and sections populated
    """
    if not paper.pdf_url:
        logger.warning(f"No PDF URL for paper: {paper.title[:50]}...")
        return paper

    os.makedirs(cache_dir, exist_ok=True)

    # Sanitize arxiv_id for filename
    safe_id = paper.arxiv_id.replace("/", "_").replace(":", "_")
    text_path = os.path.join(cache_dir, f"{safe_id}.txt")

    # Check text cache first
    if os.path.exists(text_path):
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                paper.full_text = f.read()
            paper.sections = _extract_sections(paper.full_text)
            logger.debug(f"Loaded cached text for {paper.arxiv_id}")
            return paper
        except Exception as e:
            logger.warning(f"Failed to load cached text: {e}")

    # Extract text using arxiv2text (handles download + extraction)
    try:
        def _extract_sync():
            return arxiv_to_text(paper.pdf_url)

        full_text = await asyncio.to_thread(_extract_sync)

        if full_text:
            # Limit text size
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars]

            paper.full_text = full_text
            paper.sections = _extract_sections(full_text)

            # Cache extracted text
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(full_text)

            logger.info(f"Extracted {len(full_text)} chars from {paper.arxiv_id}")
        else:
            logger.warning(f"No text extracted from {paper.arxiv_id}")

    except Exception as e:
        logger.warning(f"Failed to extract text from {paper.arxiv_id}: {e}")

    return paper


def _extract_sections(text: str) -> Dict[str, str]:
    """
    Extract common paper sections from text.

    Looks for section markers and extracts ~2000 chars after each.

    Args:
        text: Full paper text

    Returns:
        Dict with section names as keys and content as values
    """
    sections = {}
    text_lower = text.lower()

    # Common section markers and their variations
    markers = {
        'abstract': ['abstract'],
        'introduction': ['introduction', '1 introduction', '1. introduction', 'i. introduction'],
        'method': [
            'method', 'methodology', 'approach', 'methods',
            '3 method', '3. method', '2 method', '2. method',
            'iii. method', 'ii. method',
            'proposed method', 'our approach'
        ],
        'results': [
            'results', 'experiments', 'experimental results',
            '4 results', '4. results', '5 results', '5. results',
            'iv. results', 'v. results',
            'evaluation', 'experimental evaluation'
        ],
        'conclusion': [
            'conclusion', 'conclusions', 'discussion', 'summary',
            'concluding remarks', 'final remarks',
            '6 conclusion', '7 conclusion', '8 conclusion',
            'vi. conclusion', 'vii. conclusion'
        ],
    }

    for section_name, patterns in markers.items():
        for pattern in patterns:
            idx = text_lower.find(pattern)
            if idx != -1:
                # Extract ~2000 chars after the marker
                start_idx = idx
                end_idx = min(idx + 2000, len(text))
                sections[section_name] = text[start_idx:end_idx]
                break

    return sections


async def fetch_papers_for_chapter(
    paper_titles: List[str],
    cache_dir: str,
    download_pdfs: bool = False,
) -> List[ArxivPaper]:
    """
    Fetch papers for a chapter by their titles.

    Args:
        paper_titles: List of paper titles to search for
        cache_dir: Directory to cache PDFs
        download_pdfs: Whether to download and extract full PDFs

    Returns:
        List of ArxivPaper objects (with or without full text)
    """
    papers = []

    for title in paper_titles:
        # Search by title (get best match)
        search_results = await search_arxiv(title, max_results=3)

        if not search_results:
            logger.debug(f"No arXiv results for: {title[:50]}...")
            continue

        # Take the first (most relevant) result
        paper = search_results[0]

        if download_pdfs:
            paper = await download_and_extract_pdf(paper, cache_dir)

        papers.append(paper)

    logger.info(f"Fetched {len(papers)}/{len(paper_titles)} papers from arXiv")
    return papers


def format_paper_for_context(paper: ArxivPaper, include_sections: bool = True) -> str:
    """
    Format a paper for use as context in LLM prompts.

    Args:
        paper: ArxivPaper object
        include_sections: Whether to include extracted sections

    Returns:
        Formatted string with paper information
    """
    lines = [
        f"**{paper.title}**",
        f"Authors: {', '.join(paper.authors[:5])}{'...' if len(paper.authors) > 5 else ''}",
        f"Published: {paper.published}",
        f"arXiv: {paper.arxiv_id}",
        "",
        f"Abstract: {paper.abstract}",
    ]

    if include_sections and paper.sections:
        if 'method' in paper.sections:
            lines.append("")
            lines.append(f"Method excerpt: {paper.sections['method'][:1000]}...")

        if 'results' in paper.sections:
            lines.append("")
            lines.append(f"Results excerpt: {paper.sections['results'][:500]}...")

    return "\n".join(lines)
