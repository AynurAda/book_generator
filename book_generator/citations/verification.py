"""
Claim verification using Gemini with Google Search grounding.

This module verifies factual claims by asking Gemini to find
and cite authoritative sources using Google Search grounding.

PRINCIPLE: Be conservative. False citations are worse than no citations.
"""

import logging
import json
import re
import os
from typing import List, Optional, Tuple
import asyncio

from google import genai
from google.genai import types

from .models import Claim, VerifiedCitation

logger = logging.getLogger(__name__)

# Initialize client globally
_client = None

def _get_client():
    """Get or create the GenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        _client = genai.Client(api_key=api_key)
    return _client


async def verify_claim_with_gemini(
    claim: Claim,
    topic_context: str,
    confidence_threshold: float = 0.75,
) -> Optional[VerifiedCitation]:
    """
    Verify a claim using Gemini with Google Search grounding.

    Gemini searches the web via Google Search, finds sources, and returns
    whether the claim is supported with citations.

    Args:
        claim: The claim to verify
        topic_context: Book topic for context
        confidence_threshold: Minimum confidence to accept

    Returns:
        VerifiedCitation if verified, None otherwise
    """
    try:
        client = _get_client()
    except ValueError as e:
        logger.error(str(e))
        return None

    # Craft a verification prompt that demands strict evidence from original sources
    verification_prompt = f"""You are a rigorous fact-checker. Verify this claim with ORIGINAL/PRIMARY sources.

CLAIM TO VERIFY:
"{claim.content}"

CONTEXT: This claim is from a book about {topic_context}.

YOUR TASK:
1. Use Google Search to find the ORIGINAL source (the paper, documentation, or publication where this was FIRST stated)
2. Determine if the claim is DIRECTLY supported by evidence
3. Be STRICT - only verify if you find explicit support

CRITICAL - ORIGINAL SOURCES ONLY:
- For research findings: cite the ORIGINAL paper, not blog posts or news articles ABOUT the paper
- For statistics: cite the PRIMARY source (the study, survey, or report that collected the data)
- For quotes/attributions: cite where the person ORIGINALLY said/wrote it
- For software/tools: cite official documentation or the original announcement
- DO NOT cite Wikipedia, news summaries, blog posts, or secondary sources
- If you can only find secondary sources, mark as NOT VERIFIED

STRICT RULES:
- The source must DIRECTLY state or strongly imply the claim
- Partial support = NOT VERIFIED
- Inference or deduction = NOT VERIFIED
- If the claim has specific numbers/dates, they must match exactly
- When in doubt, mark as NOT VERIFIED

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "verified": true/false,
    "confidence": 0.0-1.0,
    "source_url": "URL of the ORIGINAL/PRIMARY source (empty if not verified)",
    "source_title": "Title of the original source",
    "authors": "Original author names",
    "year": "Original publication year",
    "supporting_quote": "Exact quote or close paraphrase from the ORIGINAL source",
    "explanation": "Brief explanation including why this is the original source"
}}

ONLY output valid JSON, nothing else."""

    # Configure grounding with Google Search
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        temperature=1.0,
        max_output_tokens=4096,
        response_mime_type="application/json",
    )

    try:
        # Run in executor to not block async loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=verification_prompt,
                config=config,
            )
        )

        content = response.text

        # Parse the JSON response
        try:
            if content.strip():
                verification = json.loads(content)
            else:
                logger.warning(f"Empty response from Gemini for claim {claim.id}")
                return None
        except json.JSONDecodeError as e:
            # Log the full content to understand what's wrong
            logger.warning(f"JSON parse error for claim {claim.id}: {e}")
            logger.warning(f"Content length: {len(content)}, first 500 chars: {content[:500]}")

            # Fallback: try to find JSON in response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    verification = json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning(f"Fallback JSON parse also failed")
                    return None
            else:
                logger.warning(f"No JSON object found in response")
                return None

        # Check if verified with sufficient confidence
        is_verified = verification.get("verified", False)
        confidence = float(verification.get("confidence", 0))
        explanation = verification.get("explanation", "No explanation provided")

        if not is_verified or confidence < confidence_threshold:
            reason = "not verified by source" if not is_verified else f"confidence too low ({confidence:.2f} < {confidence_threshold})"
            logger.warning(f"UNVERIFIED: {claim.content[:60]}...")
            logger.warning(f"  Reason: {reason}")
            logger.warning(f"  Explanation: {explanation[:100]}...")
            return None

        # Build citation - get URL from response
        source_url = verification.get("source_url", "")

        # Also try to get from grounding metadata if available
        if not source_url and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                chunks = getattr(candidate.grounding_metadata, 'grounding_chunks', [])
                for chunk in chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        if hasattr(chunk.web, 'uri') and chunk.web.uri:
                            source_url = chunk.web.uri
                            if not verification.get("source_title") and hasattr(chunk.web, 'title'):
                                verification["source_title"] = chunk.web.title
                            break

        if not source_url:
            logger.warning(f"Claim verified but no source URL provided")
            return None

        # Reject Wikipedia (explicitly a secondary source by design)
        if "wikipedia.org" in source_url.lower():
            logger.warning(f"Rejected Wikipedia source: {source_url}")
            return None

        # Format citation text
        authors_raw = verification.get("authors", "")
        year_raw = verification.get("year", "")
        title = verification.get("source_title", "Unknown Source")

        # Clean up authors - treat empty, "Unknown", "N/A", etc. as no author
        authors = authors_raw.strip() if authors_raw else ""
        if authors.lower() in ["unknown", "n/a", "none", "", "not specified", "not available"]:
            authors = ""

        # Clean up year
        year = year_raw.strip() if year_raw else ""
        if year.lower() in ["unknown", "n/a", "none", "", "n.d.", "not specified"]:
            year = "n.d."

        # Create short citation (for in-text use)
        if authors:
            first_author = authors.split(",")[0].split()[-1] if " " in authors.split(",")[0] else authors.split(",")[0]
            if "," in authors or " and " in authors.lower():
                citation_text = f"{first_author} et al., {year}"
            else:
                citation_text = f"{first_author}, {year}"
        else:
            # Use title-based citation when no author
            short_title = title[:30] + "..." if len(title) > 30 else title
            citation_text = f'"{short_title}", {year}'

        # Full reference (APA-style)
        if authors:
            full_reference = f"{authors} ({year}). {title}. Retrieved from {source_url}"
        else:
            # No author - start with title (APA style for web sources)
            full_reference = f"{title}. ({year}). Retrieved from {source_url}"

        verified_citation = VerifiedCitation(
            id=f"cite_{claim.id}",
            claim_id=claim.id,
            source_id=source_url,  # Use URL as source ID
            passage_id="",
            confidence=confidence,
            supporting_quote=verification.get("supporting_quote", ""),
            citation_text=citation_text,
            full_reference=full_reference,
        )

        logger.info(f"Claim VERIFIED: {claim.content[:50]}... -> {citation_text}")
        return verified_citation

    except Exception as e:
        logger.error(f"Verification failed for claim {claim.id}: {e}")
        return None


async def verify_all_claims(
    claims: List[Claim],
    topic_context: str,
    confidence_threshold: float = 0.75,
    max_concurrent: int = 10,
    delay_between_requests: float = 0.2,
    citations_dir: Optional[str] = None,
    all_claims: Optional[List[Claim]] = None,
    existing_verified: Optional[List[VerifiedCitation]] = None,
    existing_unverified: Optional[List[Claim]] = None,
) -> Tuple[List[VerifiedCitation], List[Claim]]:
    """
    Verify all claims using Gemini with Google Search grounding.

    Args:
        claims: List of claims to verify
        topic_context: Book topic for context
        confidence_threshold: Minimum confidence to accept
        max_concurrent: Max concurrent API calls
        delay_between_requests: Delay between requests (rate limiting)
        citations_dir: Directory to save incremental results (optional)
        all_claims: Full list of claims for looking up content (optional)
        existing_verified: Already verified citations to include in saves
        existing_unverified: Already unverified claims to include in saves

    Returns:
        Tuple of (verified_citations, unverified_claims) - only NEW results
    """
    import threading

    verified_citations = []
    unverified_claims = []
    save_lock = threading.Lock()

    # Include existing results in incremental saves
    cached_verified = list(existing_verified) if existing_verified else []
    cached_unverified = list(existing_unverified) if existing_unverified else []

    # For looking up claim content when saving
    claims_lookup = {c.id: c for c in (all_claims or claims)}

    total = len(claims)
    logger.info(f"Starting verification of {total} claims with Gemini Search Grounding...")

    def save_incremental():
        """Save current results to disk (thread-safe), including cached results."""
        if not citations_dir:
            return
        try:
            with save_lock:
                # Combine cached + new verified
                all_verified = cached_verified + verified_citations
                verified_data = [
                    {
                        "claim_id": vc.claim_id,
                        "claim_content": claims_lookup[vc.claim_id].content if vc.claim_id in claims_lookup else "",
                        "citation": vc.citation_text,
                        "confidence": vc.confidence,
                        "source_url": vc.source_id,
                        "quote": vc.supporting_quote[:300] if vc.supporting_quote else "",
                        "full_reference": vc.full_reference,
                    }
                    for vc in all_verified
                ]
                with open(f"{citations_dir}/02_verified_citations.json", "w") as f:
                    import json
                    json.dump(verified_data, f, indent=2)

                # Combine cached + new unverified
                all_unverified = cached_unverified + unverified_claims
                unverified_data = [
                    {
                        "id": c.id,
                        "content": c.content,
                        "chapter": c.chapter,
                        "section": c.section,
                        "subsection": c.subsection,
                        "importance": c.importance,
                    }
                    for c in all_unverified
                ]
                with open(f"{citations_dir}/03_unverified_claims.json", "w") as f:
                    import json
                    json.dump(unverified_data, f, indent=2)

                logger.info(f"Saved incremental: {len(all_verified)} verified, {len(all_unverified)} unverified")
        except Exception as e:
            logger.warning(f"Failed to save incremental results: {e}")

    # Process with rate limiting
    semaphore = asyncio.Semaphore(max_concurrent)
    processed_count = [0]  # Use list for mutable counter in closure

    async def verify_with_limit(claim: Claim, index: int):
        async with semaphore:
            logger.info(f"Verifying claim {index + 1}/{total}: {claim.content[:40]}...")
            result = await verify_claim_with_gemini(
                claim=claim,
                topic_context=topic_context,
                confidence_threshold=confidence_threshold,
            )
            # Rate limiting delay
            await asyncio.sleep(delay_between_requests)

            # Process result immediately and save
            if result:
                verified_citations.append(result)
            else:
                unverified_claims.append(claim)

            processed_count[0] += 1
            if citations_dir:
                save_incremental()

            return claim, result

    # Run verifications - results are saved incrementally inside verify_with_limit
    tasks = [verify_with_limit(claim, i) for i, claim in enumerate(claims)]
    await asyncio.gather(*tasks, return_exceptions=True)

    # Final save to ensure everything is persisted
    save_incremental()

    # Summary
    verified_count = len(verified_citations)
    unverified_count = len(unverified_claims)
    rate = (verified_count / total * 100) if total > 0 else 0

    logger.info("="*50)
    logger.info(f"VERIFICATION COMPLETE")
    logger.info(f"Total claims: {total}")
    logger.info(f"Verified: {verified_count} ({rate:.1f}%)")
    logger.info(f"Unverified: {unverified_count}")
    logger.info("="*50)

    # Log unverified critical/high importance claims
    critical_unverified = [c for c in unverified_claims if c.importance == "critical"]
    high_unverified = [c for c in unverified_claims if c.importance == "high"]

    if critical_unverified:
        logger.warning(f"CRITICAL claims unverified ({len(critical_unverified)}):")
        for c in critical_unverified[:5]:
            logger.warning(f"  - {c.content[:60]}...")

    if high_unverified:
        logger.warning(f"HIGH importance claims unverified ({len(high_unverified)}):")
        for c in high_unverified[:5]:
            logger.warning(f"  - {c.content[:60]}...")

    return verified_citations, unverified_claims
