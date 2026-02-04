"""
Source discovery for claims.

Uses web search to find potential sources that might
support factual claims extracted from the outline.
"""

import logging
import hashlib
import asyncio
from typing import List, Optional
import os

import synalinks

from .models import (
    Claim,
    Source,
    SourceSearchInput,
    SearchQueries,
)

logger = logging.getLogger(__name__)


def generate_source_id(url: str) -> str:
    """Generate a unique source ID from URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


async def generate_search_queries(
    claim: Claim,
    topic_context: str,
    language_model,
) -> SearchQueries:
    """
    Generate search queries for finding sources for a claim.

    Args:
        claim: The claim to find sources for
        topic_context: Book topic for context
        language_model: Synalinks language model

    Returns:
        SearchQueries with academic, documentation, and general queries
    """
    generator = synalinks.Generator(
        data_model=SearchQueries,
        language_model=language_model,
        instructions="""Generate effective search queries to find authoritative sources for this claim.

For ACADEMIC queries (papers, journals):
- Use precise technical terminology
- Include author names if the claim attributes something
- Use search operators like "site:arxiv.org" or "filetype:pdf"

For DOCUMENTATION queries:
- Target official docs, specifications, RFCs
- Use "site:docs.X.com" or "official documentation"

For GENERAL queries:
- Target authoritative websites, established organizations
- Avoid blogs, forums, or user-generated content

Generate 2-3 queries per category. Make them specific enough to find the exact claim, not just related content."""
    )

    input_data = SourceSearchInput(
        claim_content=claim.content,
        claim_type=claim.claim_type,
        topic_context=topic_context,
    )

    result = await generator(input_data)
    return result


async def search_for_sources(
    queries: SearchQueries,
    max_results_per_query: int = 5,
) -> List[dict]:
    """
    Execute search queries to find potential sources.

    Uses Perplexity search via MCP if available, otherwise falls back
    to basic web search.

    Args:
        queries: SearchQueries object with query lists
        max_results_per_query: Max results per query

    Returns:
        List of raw search result dicts
    """
    all_results = []

    # Combine all queries
    all_queries = (
        queries.get_json().get("academic_queries", []) +
        queries.get_json().get("documentation_queries", []) +
        queries.get_json().get("general_queries", [])
    )

    for query in all_queries[:6]:  # Limit to 6 queries total
        try:
            # Try using perplexity search (would be via MCP in practice)
            # For now, this is a placeholder - the actual implementation
            # would call the perplexity MCP tool
            logger.info(f"Searching: {query}")

            # Placeholder for search results
            # In real implementation, this calls:
            # results = await mcp_perplexity_search(query)
            # or
            # results = await mcp_firecrawl_search(query)

            # For now, we'll structure expected results
            # The actual search integration happens in the pipeline

        except Exception as e:
            logger.warning(f"Search failed for query '{query}': {e}")
            continue

    return all_results


def parse_search_result_to_source(result: dict) -> Optional[Source]:
    """
    Parse a search result into a Source object.

    Args:
        result: Raw search result dict

    Returns:
        Source object or None if parsing fails
    """
    try:
        url = result.get("url", "")
        if not url:
            return None

        # Extract metadata
        title = result.get("title", "Unknown Title")
        authors = result.get("authors", "Unknown")
        year = result.get("year", result.get("date", "")[:4] if result.get("date") else "")

        # Determine source type from URL
        source_type = "website"
        if "arxiv.org" in url or "doi.org" in url or ".pdf" in url:
            source_type = "paper"
        elif "docs." in url or "documentation" in url.lower():
            source_type = "documentation"
        elif any(x in url for x in ["github.com", "gitlab.com"]):
            source_type = "documentation"

        return Source(
            id=generate_source_id(url),
            title=title,
            url=url,
            authors=authors,
            year=year,
            source_type=source_type,
        )
    except Exception as e:
        logger.warning(f"Failed to parse search result: {e}")
        return None


def deduplicate_sources(sources: List[Source]) -> List[Source]:
    """
    Remove duplicate sources based on URL.

    Args:
        sources: List of Source objects

    Returns:
        Deduplicated list
    """
    seen_urls = set()
    unique_sources = []

    for source in sources:
        # Normalize URL for comparison
        normalized_url = source.url.lower().rstrip("/")
        if normalized_url not in seen_urls:
            seen_urls.add(normalized_url)
            unique_sources.append(source)

    return unique_sources


async def find_sources_for_claim(
    claim: Claim,
    topic_context: str,
    language_model,
    search_func=None,
) -> List[Source]:
    """
    Find potential sources for a single claim.

    Args:
        claim: The claim to find sources for
        topic_context: Book topic for context
        language_model: Synalinks language model
        search_func: Optional custom search function

    Returns:
        List of potential Source objects
    """
    logger.info(f"Finding sources for claim: {claim.content[:50]}...")

    # Generate search queries
    queries = await generate_search_queries(
        claim=claim,
        topic_context=topic_context,
        language_model=language_model,
    )

    # Execute searches
    if search_func:
        raw_results = await search_func(queries)
    else:
        raw_results = await search_for_sources(queries)

    # Parse results to Source objects
    sources = []
    for result in raw_results:
        source = parse_search_result_to_source(result)
        if source:
            sources.append(source)

    # Deduplicate
    sources = deduplicate_sources(sources)

    logger.info(f"Found {len(sources)} unique sources for claim")
    return sources


async def find_sources_for_claims(
    claims: List[Claim],
    topic_context: str,
    language_model,
    search_func=None,
    max_concurrent: int = 3,
) -> tuple[dict, List[Source]]:
    """
    Find sources for multiple claims with concurrency control.

    Args:
        claims: List of claims to find sources for
        topic_context: Book topic
        language_model: Synalinks language model
        search_func: Optional custom search function
        max_concurrent: Max concurrent search operations

    Returns:
        Tuple of (claim_id -> source_ids mapping, all unique sources)
    """
    claim_to_sources = {}
    all_sources = []

    # Process in batches to avoid rate limiting
    semaphore = asyncio.Semaphore(max_concurrent)

    async def find_with_limit(claim):
        async with semaphore:
            sources = await find_sources_for_claim(
                claim=claim,
                topic_context=topic_context,
                language_model=language_model,
                search_func=search_func,
            )
            return claim.id, sources

    tasks = [find_with_limit(claim) for claim in claims]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Source search failed: {result}")
            continue

        claim_id, sources = result
        claim_to_sources[claim_id] = [s.id for s in sources]
        all_sources.extend(sources)

    # Deduplicate all sources
    all_sources = deduplicate_sources(all_sources)

    logger.info(f"Total unique sources found: {len(all_sources)}")
    return claim_to_sources, all_sources
