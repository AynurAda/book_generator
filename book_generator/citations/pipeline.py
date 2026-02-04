"""
Main citation pipeline orchestration.

This module coordinates the full citation workflow:
1. Extract claims from outline
2. Find sources for claims
3. Download and process sources
4. Verify claims against sources
5. Build citation context for content generation
"""

import logging
import os
from typing import List, Tuple, Optional, Callable
import asyncio

import synalinks

from .models import Claim, Source, Passage, VerifiedCitation, CitationContext
from .extraction import extract_all_claims
from .discovery import find_sources_for_claims
from .documents import process_source_to_passages
from .knowledge_base import create_citation_knowledge_base, CitationStore
from .verification import verify_all_claims
from .injection import (
    remove_unverified_claims_from_outline,
    format_bibliography,
)
from ..utils import save_json_to_file, save_to_file

logger = logging.getLogger(__name__)


async def run_citation_pipeline(
    outline: dict,
    topic: str,
    goal: str,
    output_dir: str,
    language_model,
    embedding_model,
    search_func: Optional[Callable] = None,
    confidence_threshold: float = 0.75,
    skip_low_importance: bool = True,
) -> Tuple[dict, CitationStore, List[Claim]]:
    """
    Run the complete citation verification pipeline.

    Args:
        outline: Book outline with concepts/subconcepts
        topic: Book topic
        goal: Book goal
        output_dir: Directory for outputs
        language_model: Synalinks language model
        embedding_model: Synalinks embedding model
        search_func: Optional custom search function for sources
        confidence_threshold: Minimum confidence to accept citations
        skip_low_importance: Skip verification for low importance claims

    Returns:
        Tuple of:
        - Modified outline with citation metadata
        - CitationStore with all verified citations
        - List of all claims (for reference)
    """
    logger.info("="*60)
    logger.info("STARTING CITATION PIPELINE")
    logger.info("="*60)

    citations_dir = os.path.join(output_dir, "citations")
    os.makedirs(citations_dir, exist_ok=True)

    # =========================================================================
    # PHASE 1: Extract Claims
    # =========================================================================
    logger.info("\n[PHASE 1] Extracting claims from outline...")

    all_claims = await extract_all_claims(
        outline=outline,
        topic=topic,
        goal=goal,
        language_model=language_model,
    )

    # Save claims for debugging
    claims_data = [
        {
            "id": c.id,
            "content": c.content,
            "chapter": c.chapter,
            "section": c.section,
            "type": c.claim_type,
            "importance": c.importance,
        }
        for c in all_claims
    ]
    save_json_to_file(claims_data, os.path.join(citations_dir, "01_extracted_claims.json"))

    # Filter claims to verify
    if skip_low_importance:
        claims_to_verify = [c for c in all_claims if c.importance != "low"]
        logger.info(f"Verifying {len(claims_to_verify)}/{len(all_claims)} claims (skipping low importance)")
    else:
        claims_to_verify = all_claims

    # =========================================================================
    # PHASE 2: Find Sources
    # =========================================================================
    logger.info("\n[PHASE 2] Finding sources for claims...")

    claim_to_sources, all_sources = await find_sources_for_claims(
        claims=claims_to_verify,
        topic_context=topic,
        language_model=language_model,
        search_func=search_func,
    )

    # Save sources for debugging
    sources_data = [
        {
            "id": s.id,
            "title": s.title,
            "url": s.url,
            "authors": s.authors,
            "year": s.year,
            "type": s.source_type,
        }
        for s in all_sources
    ]
    save_json_to_file(sources_data, os.path.join(citations_dir, "02_found_sources.json"))

    if not all_sources:
        logger.warning("No sources found! Returning original outline.")
        return outline, CitationStore(None), all_claims

    # =========================================================================
    # PHASE 3: Download and Process Sources
    # =========================================================================
    logger.info("\n[PHASE 3] Downloading and processing sources...")

    all_passages = []
    valid_sources = []

    for source in all_sources:
        passages = await process_source_to_passages(source, citations_dir)
        if passages:
            valid_sources.append(source)
            all_passages.extend(passages)

    logger.info(f"Processed {len(valid_sources)}/{len(all_sources)} sources")
    logger.info(f"Created {len(all_passages)} passages")

    if not all_passages:
        logger.warning("No passages extracted! Returning original outline.")
        return outline, CitationStore(None), all_claims

    # =========================================================================
    # PHASE 4: Build Knowledge Base
    # =========================================================================
    logger.info("\n[PHASE 4] Building citation knowledge base...")

    kb = await create_citation_knowledge_base(citations_dir, embedding_model)
    citation_store = CitationStore(kb)

    await citation_store.add_sources(valid_sources)
    await citation_store.add_passages(all_passages)

    # =========================================================================
    # PHASE 5: Verify Claims
    # =========================================================================
    logger.info("\n[PHASE 5] Verifying claims against sources...")

    verified_citations, unverified_claims = await verify_all_claims(
        claims=claims_to_verify,
        citation_store=citation_store,
        language_model=language_model,
        confidence_threshold=confidence_threshold,
    )

    # Save verification results
    verified_data = [
        {
            "claim_id": vc.claim_id,
            "source_id": vc.source_id,
            "confidence": vc.confidence,
            "citation": vc.citation_text,
            "quote": vc.supporting_quote[:200] + "..." if len(vc.supporting_quote) > 200 else vc.supporting_quote,
        }
        for vc in verified_citations
    ]
    save_json_to_file(verified_data, os.path.join(citations_dir, "03_verified_citations.json"))

    unverified_data = [
        {
            "id": c.id,
            "content": c.content,
            "chapter": c.chapter,
            "section": c.section,
            "importance": c.importance,
        }
        for c in unverified_claims
    ]
    save_json_to_file(unverified_data, os.path.join(citations_dir, "04_unverified_claims.json"))

    # =========================================================================
    # PHASE 6: Modify Outline
    # =========================================================================
    logger.info("\n[PHASE 6] Updating outline with citation metadata...")

    modified_outline = remove_unverified_claims_from_outline(
        outline=outline,
        unverified_claims=unverified_claims,
    )

    # Generate bibliography
    bibliography = format_bibliography(citation_store)
    save_to_file(bibliography, os.path.join(citations_dir, "05_bibliography.md"))

    # =========================================================================
    # Summary
    # =========================================================================
    logger.info("\n" + "="*60)
    logger.info("CITATION PIPELINE COMPLETE")
    logger.info("="*60)
    logger.info(f"Total claims: {len(all_claims)}")
    logger.info(f"Claims verified: {len(verified_citations)}")
    logger.info(f"Claims unverified: {len(unverified_claims)}")
    logger.info(f"Verification rate: {len(verified_citations)/len(claims_to_verify)*100:.1f}%")
    logger.info(f"Sources used: {len(valid_sources)}")
    logger.info(f"References: {len(citation_store.get_all_references())}")
    logger.info("="*60)

    return modified_outline, citation_store, all_claims


async def quick_citation_check(
    claims_sample: List[str],
    topic: str,
    language_model,
) -> dict:
    """
    Quick check to estimate citation feasibility for a set of claims.

    Useful for previewing how many claims might be verifiable
    before running the full pipeline.

    Args:
        claims_sample: Sample claim texts
        topic: Topic context
        language_model: Language model

    Returns:
        Dict with feasibility estimates
    """
    # This would do a quick search and estimate
    # Implementation depends on available search APIs
    return {
        "total_claims": len(claims_sample),
        "estimated_verifiable": "unknown",
        "recommendation": "Run full pipeline for accurate results"
    }
