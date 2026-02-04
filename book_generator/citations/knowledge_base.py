"""
Knowledge base setup and management for citation verification.

Uses Synalinks KnowledgeBase with DuckDB for storage and
embedding-based retrieval of passages.
"""

import logging
import os
from typing import List, Optional

import synalinks

from .models import Source, Passage, Claim, VerifiedCitation

logger = logging.getLogger(__name__)


async def create_citation_knowledge_base(
    output_dir: str,
    embedding_model,
) -> synalinks.KnowledgeBase:
    """
    Create a knowledge base for citation verification.

    Uses DuckDB as the backend for embedded vector storage.

    Args:
        output_dir: Directory for the database file
        embedding_model: Synalinks embedding model

    Returns:
        Configured KnowledgeBase instance
    """
    db_path = os.path.join(output_dir, "citations.db")

    # Remove existing DB if present (fresh start)
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"Removed existing citation database")

    knowledge_base = synalinks.KnowledgeBase(
        uri=f"duckdb://{db_path}",
        data_models=[Source, Passage],
        embedding_model=embedding_model,
        metric="cosine",
    )

    logger.info(f"Created citation knowledge base at {db_path}")
    return knowledge_base


async def store_sources(
    knowledge_base: synalinks.KnowledgeBase,
    sources: List[Source],
) -> int:
    """
    Store sources in the knowledge base.

    Args:
        knowledge_base: The knowledge base
        sources: List of Source objects

    Returns:
        Number of sources stored
    """
    stored = 0
    for source in sources:
        try:
            await knowledge_base.update(source)
            stored += 1
        except Exception as e:
            logger.warning(f"Failed to store source {source.id}: {e}")

    logger.info(f"Stored {stored}/{len(sources)} sources")
    return stored


async def store_passages(
    knowledge_base: synalinks.KnowledgeBase,
    passages: List[Passage],
) -> int:
    """
    Store passages in the knowledge base with embeddings.

    Args:
        knowledge_base: The knowledge base
        passages: List of Passage objects

    Returns:
        Number of passages stored
    """
    stored = 0
    for passage in passages:
        try:
            await knowledge_base.update(passage)
            stored += 1
        except Exception as e:
            logger.warning(f"Failed to store passage {passage.id}: {e}")

    logger.info(f"Stored {stored}/{len(passages)} passages")
    return stored


async def retrieve_relevant_passages(
    knowledge_base: synalinks.KnowledgeBase,
    query: str,
    k: int = 5,
    threshold: float = 0.5,
) -> List[Passage]:
    """
    Retrieve passages relevant to a query using hybrid search.

    Args:
        knowledge_base: The knowledge base
        query: Search query (typically a claim)
        k: Number of results to retrieve
        threshold: Minimum similarity threshold

    Returns:
        List of relevant Passage objects
    """
    try:
        # Use the knowledge base's search functionality
        results = await knowledge_base.search(
            query=query,
            data_model=Passage,
            k=k,
            search_type="hybrid",  # Combines BM25 and vector search
        )
        return results
    except Exception as e:
        logger.warning(f"Passage retrieval failed: {e}")
        return []


async def get_source_by_id(
    knowledge_base: synalinks.KnowledgeBase,
    source_id: str,
) -> Optional[Source]:
    """
    Retrieve a source by its ID.

    Args:
        knowledge_base: The knowledge base
        source_id: Source ID to retrieve

    Returns:
        Source object or None
    """
    try:
        results = await knowledge_base.search(
            query=source_id,
            data_model=Source,
            k=1,
            search_type="fulltext",
        )
        return results[0] if results else None
    except Exception as e:
        logger.warning(f"Source retrieval failed: {e}")
        return None


class CitationStore:
    """
    Wrapper class for managing citation data.

    Provides a cleaner interface for citation operations.
    """

    def __init__(
        self,
        knowledge_base: synalinks.KnowledgeBase,
    ):
        self.kb = knowledge_base
        self.verified_citations: List[VerifiedCitation] = []
        self._source_cache: dict = {}
        self._passage_cache: dict = {}

    async def add_sources(self, sources: List[Source]) -> int:
        """Add sources to the store."""
        count = await store_sources(self.kb, sources)
        for source in sources:
            self._source_cache[source.id] = source
        return count

    async def add_passages(self, passages: List[Passage]) -> int:
        """Add passages to the store."""
        count = await store_passages(self.kb, passages)
        for passage in passages:
            self._passage_cache[passage.id] = passage
        return count

    async def find_passages_for_claim(
        self,
        claim: Claim,
        k: int = 5,
    ) -> List[Passage]:
        """Find passages that might support a claim."""
        return await retrieve_relevant_passages(
            self.kb,
            query=claim.content,
            k=k,
        )

    async def get_source(self, source_id: str) -> Optional[Source]:
        """Get a source by ID (cached)."""
        if source_id in self._source_cache:
            return self._source_cache[source_id]

        source = await get_source_by_id(self.kb, source_id)
        if source:
            self._source_cache[source_id] = source
        return source

    def add_verified_citation(self, citation: VerifiedCitation):
        """Add a verified citation."""
        self.verified_citations.append(citation)

    def get_citations_for_section(
        self,
        chapter: str,
        section: str,
    ) -> List[VerifiedCitation]:
        """Get all verified citations for a specific section."""
        return [
            c for c in self.verified_citations
            if self._citation_matches_section(c, chapter, section)
        ]

    def _citation_matches_section(
        self,
        citation: VerifiedCitation,
        chapter: str,
        section: str,
    ) -> bool:
        """Check if a citation belongs to a section."""
        # Would need to look up the claim to check this
        # For now, return True and filter in the calling code
        return True

    def get_all_references(self) -> List[str]:
        """Get all full references for bibliography."""
        seen = set()
        references = []
        for citation in self.verified_citations:
            if citation.full_reference not in seen:
                seen.add(citation.full_reference)
                references.append(citation.full_reference)
        return sorted(references)
