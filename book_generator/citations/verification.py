"""
Claim verification against source passages.

This is the critical module that determines whether a passage
actually supports a claim - the gatekeeper preventing hallucination.
"""

import logging
from typing import List, Optional, Tuple

import synalinks

from .models import (
    Claim,
    Source,
    Passage,
    VerifiedCitation,
    VerificationInput,
    VerificationResult,
)
from .knowledge_base import CitationStore

logger = logging.getLogger(__name__)


def format_citation_text(source: Source, page: Optional[int] = None) -> str:
    """
    Format an inline citation.

    Args:
        source: The source being cited
        page: Optional page number

    Returns:
        Formatted citation like "Smith et al., 2023" or "Smith et al., 2023, p. 42"
    """
    authors = source.authors
    year = source.year or "n.d."

    # Simplify author string
    if "," in authors:
        # Multiple authors - use first + et al.
        first_author = authors.split(",")[0].strip()
        if " " in first_author:
            first_author = first_author.split()[-1]  # Last name
        citation = f"{first_author} et al., {year}"
    else:
        # Single author - use last name
        if " " in authors:
            author = authors.split()[-1]
        else:
            author = authors
        citation = f"{author}, {year}"

    if page:
        citation += f", p. {page}"

    return citation


def format_full_reference(source: Source) -> str:
    """
    Format a full bibliographic reference.

    Args:
        source: The source

    Returns:
        Full reference string
    """
    parts = []

    if source.authors:
        parts.append(source.authors)

    if source.year:
        parts.append(f"({source.year})")

    if source.title:
        parts.append(f"*{source.title}*")

    if source.url:
        parts.append(f"Retrieved from {source.url}")

    return ". ".join(parts) + "."


async def verify_claim_against_passage(
    claim: Claim,
    passage: Passage,
    source: Source,
    language_model,
) -> VerificationResult:
    """
    Verify if a passage supports a claim.

    This is the CRITICAL function - it must be conservative.
    False positives (claiming support when there isn't) are much
    worse than false negatives.

    Args:
        claim: The claim to verify
        passage: The candidate supporting passage
        source: The source the passage comes from
        language_model: Synalinks language model

    Returns:
        VerificationResult with support determination
    """
    verifier = synalinks.Generator(
        data_model=VerificationResult,
        language_model=language_model,
        instructions="""You are a rigorous fact-checker verifying if a passage supports a claim.

YOUR TASK: Determine if the PASSAGE provides DIRECT SUPPORT for the CLAIM.

STRICT RULES - A claim is ONLY supported if:
1. **DIRECT SUPPORT**: The passage explicitly states or directly implies the claim
2. **SPECIFICITY MATCH**: The numbers, names, dates must match exactly
3. **NO INFERENCE**: You cannot infer or deduce support - it must be explicit
4. **NO PARTIAL MATCH**: "Close enough" is NOT supported

SUPPORT TYPES:
- **direct_quote**: Passage contains nearly verbatim the claim
- **paraphrase**: Passage says the same thing in different words
- **inference**: Would require reasoning to connect (NOT VALID SUPPORT)
- **not_supported**: Passage doesn't support the claim

CONFIDENCE SCORING:
- 0.9-1.0: Direct quote or very close paraphrase with exact details
- 0.7-0.9: Clear paraphrase, same meaning, matching specifics
- 0.5-0.7: Related but requires some interpretation (REJECT)
- 0.0-0.5: Not supported or only tangentially related (REJECT)

BE CONSERVATIVE: When in doubt, mark as NOT supported.
False citations are worse than missing citations.

If supported, extract the EXACT QUOTE from the passage that supports the claim."""
    )

    source_info = f"Title: {source.title}\nAuthors: {source.authors}\nYear: {source.year}"

    input_data = VerificationInput(
        claim=claim.content,
        passage=passage.content,
        source_info=source_info,
    )

    result = await verifier(input_data)
    return result


async def verify_claim(
    claim: Claim,
    citation_store: CitationStore,
    language_model,
    confidence_threshold: float = 0.75,
    max_passages: int = 5,
) -> Optional[VerifiedCitation]:
    """
    Attempt to verify a claim against the knowledge base.

    Args:
        claim: The claim to verify
        citation_store: CitationStore with passages
        language_model: Synalinks language model
        confidence_threshold: Minimum confidence to accept
        max_passages: Maximum passages to check

    Returns:
        VerifiedCitation if verified, None otherwise
    """
    logger.info(f"Verifying claim: {claim.content[:50]}...")

    # Find relevant passages
    passages = await citation_store.find_passages_for_claim(claim, k=max_passages)

    if not passages:
        logger.info(f"No passages found for claim {claim.id}")
        return None

    # Check each passage
    for passage in passages:
        # Get the source for this passage
        source = await citation_store.get_source(passage.source_id)
        if not source:
            continue

        # Verify
        result = await verify_claim_against_passage(
            claim=claim,
            passage=passage,
            source=source,
            language_model=language_model,
        )

        result_dict = result.get_json()

        # Check if supported with sufficient confidence
        if (result_dict.get("is_supported", False) and
            result_dict.get("confidence", 0) >= confidence_threshold and
            result_dict.get("support_type") in ["direct_quote", "paraphrase"]):

            citation = VerifiedCitation(
                id=f"cite_{claim.id}_{passage.id}",
                claim_id=claim.id,
                source_id=source.id,
                passage_id=passage.id,
                confidence=result_dict["confidence"],
                supporting_quote=result_dict.get("supporting_quote", ""),
                citation_text=format_citation_text(source, passage.page_number),
                full_reference=format_full_reference(source),
            )

            logger.info(f"Claim verified with confidence {citation.confidence:.2f}")
            return citation

    logger.info(f"Claim could not be verified: {claim.id}")
    return None


async def verify_all_claims(
    claims: List[Claim],
    citation_store: CitationStore,
    language_model,
    confidence_threshold: float = 0.75,
) -> Tuple[List[VerifiedCitation], List[Claim]]:
    """
    Verify all claims and separate into verified and unverified.

    Args:
        claims: All claims to verify
        citation_store: CitationStore with passages
        language_model: Synalinks language model
        confidence_threshold: Minimum confidence

    Returns:
        Tuple of (verified_citations, unverified_claims)
    """
    verified_citations = []
    unverified_claims = []

    for claim in claims:
        citation = await verify_claim(
            claim=claim,
            citation_store=citation_store,
            language_model=language_model,
            confidence_threshold=confidence_threshold,
        )

        if citation:
            verified_citations.append(citation)
            citation_store.add_verified_citation(citation)
        else:
            unverified_claims.append(claim)

    # Log summary
    total = len(claims)
    verified = len(verified_citations)
    unverified = len(unverified_claims)

    logger.info(f"Verification complete: {verified}/{total} verified, {unverified}/{total} unverified")

    # Log by importance
    critical_unverified = [c for c in unverified_claims if c.importance == "critical"]
    high_unverified = [c for c in unverified_claims if c.importance == "high"]

    if critical_unverified:
        logger.warning(f"CRITICAL claims unverified: {len(critical_unverified)}")
        for c in critical_unverified:
            logger.warning(f"  - {c.content[:60]}...")

    if high_unverified:
        logger.warning(f"HIGH importance claims unverified: {len(high_unverified)}")

    return verified_citations, unverified_claims
