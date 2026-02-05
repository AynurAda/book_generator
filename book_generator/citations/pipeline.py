"""
Claim-first citation pipeline.

FLOW:
1. Plan claims for each subsection (LLM explicitly lists what facts it will state)
2. Verify each planned claim with Perplexity
3. Build citation context that STRICTLY constrains content generation
4. Content generation can ONLY use verified claims

This ensures NO unverified factual claims can appear in the final text.
"""

import logging
import os
from typing import List, Tuple, Dict, Optional
import asyncio

from .models import Claim, VerifiedCitation
from .claim_planning import plan_all_subsection_claims, SubsectionClaimPlan
from .verification import verify_all_claims
from .injection import remove_unverified_claims_from_outline
from ..utils import save_json_to_file, save_to_file, load_json_from_file, output_exists

logger = logging.getLogger(__name__)


class CitationManager:
    """
    Manages citations for a book generation run.

    Provides STRICT citation constraints for content generation.
    Content generators can ONLY make claims that appear in verified_citations.
    """

    def __init__(
        self,
        claims: List[Claim],
        verified_citations: List[VerifiedCitation],
        unverified_claims: List[Claim],
        subsection_plans: Optional[Dict[str, SubsectionClaimPlan]] = None,
    ):
        self.claims = claims
        self.verified_citations = verified_citations
        self.unverified_claims = unverified_claims
        self.subsection_plans = subsection_plans or {}

        # Build lookup tables
        self._claim_by_id: Dict[str, Claim] = {c.id: c for c in claims}
        self._citation_by_claim: Dict[str, VerifiedCitation] = {
            vc.claim_id: vc for vc in verified_citations
        }

        # Index claims by section AND subsection
        self._claims_by_section: Dict[str, List[Claim]] = {}
        self._claims_by_subsection: Dict[str, List[Claim]] = {}

        for claim in claims:
            # Section-level index
            section_key = f"{claim.chapter}::{claim.section}"
            if section_key not in self._claims_by_section:
                self._claims_by_section[section_key] = []
            self._claims_by_section[section_key].append(claim)

            # Subsection-level index
            if claim.subsection:
                subsection_key = f"{claim.chapter}::{claim.section}::{claim.subsection}"
                if subsection_key not in self._claims_by_subsection:
                    self._claims_by_subsection[subsection_key] = []
                self._claims_by_subsection[subsection_key].append(claim)

    def get_subsection_citation_instructions(
        self,
        chapter: str,
        section: str,
        subsection: str,
    ) -> str:
        """
        Get STRICT citation instructions for a specific subsection.

        The generator is ONLY allowed to make factual claims from the
        verified list. Any other factual claim is FORBIDDEN.
        """
        key = f"{chapter}::{section}::{subsection}"
        subsection_claims = self._claims_by_subsection.get(key, [])

        # Get conceptual points from plan (these don't need citations)
        conceptual_points = []
        if key in self.subsection_plans:
            plan = self.subsection_plans[key]
            plan_dict = plan.get_json() if hasattr(plan, 'get_json') else {}
            conceptual_points = plan_dict.get("conceptual_points", [])

        # Build verified claims list
        verified_claims = []
        unverified_in_subsection = []

        for claim in subsection_claims:
            citation = self._citation_by_claim.get(claim.id)
            if citation:
                verified_claims.append({
                    "claim": claim.content,
                    "citation": citation.citation_text,
                    "source_quote": citation.supporting_quote[:300] if citation.supporting_quote else "",
                })
            else:
                unverified_in_subsection.append(claim.content)

        return format_strict_citation_instructions(
            subsection_name=subsection,
            verified_claims=verified_claims,
            unverified_claims=unverified_in_subsection,
            conceptual_points=conceptual_points,
        )

    def get_citation_instructions(self, chapter: str, section: str) -> str:
        """
        Get citation instructions for a section (aggregates all subsections).

        For backwards compatibility. Prefer get_subsection_citation_instructions.
        """
        section_key = f"{chapter}::{section}"
        section_claims = self._claims_by_section.get(section_key, [])

        verified_claims = []
        unverified_claims = []

        for claim in section_claims:
            citation = self._citation_by_claim.get(claim.id)
            if citation:
                verified_claims.append({
                    "claim": claim.content,
                    "citation": citation.citation_text,
                    "source_quote": citation.supporting_quote[:200] if citation.supporting_quote else "",
                })
            else:
                unverified_claims.append(claim.content)

        return format_strict_citation_instructions(
            subsection_name=section,
            verified_claims=verified_claims,
            unverified_claims=unverified_claims,
            conceptual_points=[],
        )

    def get_all_references(self) -> List[str]:
        """Get all full references for bibliography."""
        seen = set()
        references = []
        for citation in self.verified_citations:
            if citation.full_reference not in seen:
                seen.add(citation.full_reference)
                references.append(citation.full_reference)
        return sorted(references)

    def get_bibliography_markdown(self) -> str:
        """Get formatted bibliography."""
        references = self.get_all_references()
        if not references:
            return ""

        lines = ["## References", ""]
        for ref in references:
            lines.append(f"- {ref}")
            lines.append("")
        return "\n".join(lines)


def format_strict_citation_instructions(
    subsection_name: str,
    verified_claims: List[dict],
    unverified_claims: List[str],
    conceptual_points: List[str],
) -> str:
    """
    Format STRICT citation instructions.

    The generator is FORBIDDEN from making any factual claim
    not in the verified list.
    """
    parts = []

    parts.append(f"""
=== STRICT CITATION POLICY FOR: {subsection_name} ===

You are writing content for this subsection. You MUST follow these rules EXACTLY.
""")

    if verified_claims:
        claims_text = "\n".join([
            f"  [{i+1}] CLAIM: \"{c['claim']}\"\n      CITE AS: ({c['citation']})\n      SOURCE: \"{c['source_quote'][:150]}...\""
            for i, c in enumerate(verified_claims)
        ])

        parts.append(f"""
=== VERIFIED CLAIMS (you MAY use these - MUST cite) ===

{claims_text}

RULES FOR VERIFIED CLAIMS:
- You MAY include any of these claims in your text
- When you use a claim, you MUST include its citation
- Use the exact citation format provided
- You may paraphrase slightly, but keep the factual content accurate
""")
    else:
        parts.append("""
=== NO VERIFIED CLAIMS AVAILABLE ===

No factual claims were verified for this subsection.
You must write using ONLY conceptual explanations and examples.
DO NOT state any specific facts, statistics, or attributions.
""")

    if unverified_claims:
        unverified_text = "\n".join([f"  - {c}" for c in unverified_claims])

        parts.append(f"""
=== FORBIDDEN CLAIMS (verification failed - DO NOT USE) ===

The following claims could NOT be verified and are FORBIDDEN:

{unverified_text}

DO NOT state these as facts. DO NOT paraphrase these. DO NOT imply these.
If you need to discuss these topics, use hedging language:
- "One approach is..." (not "Research shows...")
- "It's commonly believed that..." (not "Studies demonstrate...")
- "Some practitioners suggest..." (not "Evidence indicates...")
""")

    if conceptual_points:
        concepts_text = "\n".join([f"  - {p}" for p in conceptual_points])
        parts.append(f"""
=== CONCEPTUAL POINTS (no citation needed) ===

These are explanations/examples you planned that don't require citations:

{concepts_text}

You may freely use these conceptual points in your writing.
""")

    parts.append("""
=== ABSOLUTE RULES ===

1. FORBIDDEN: Stating unverified claims AS FACTS
2. FORBIDDEN: Statistics, percentages, or numbers without citation
3. FORBIDDEN: Attributions ("proposed by X", "developed at Y") without citation
4. FORBIDDEN: Research findings ("studies show", "research demonstrates") without citation
5. REQUIRED: Every verified claim you use MUST include its citation

ALLOWED WITHOUT CITATION:
- Conceptual explanations ("Attention works by...")
- Examples you create ("Suppose we have a network that...")
- Logical reasoning ("This implies that...")
- Definitions from first principles ("A transformer is a type of model that...")

ORIGINAL ANALYSIS & SPECULATION (encouraged, but frame appropriately):
- Novel interpretations: "One way to think about this is..."
- Synthesis/connections: "This suggests a potential connection to..."
- Mental models: "A useful mental model here is..."
- Future directions: "Looking ahead, this could enable..."
- Author insights: "What makes this particularly interesting is..."
- Speculation: "One could imagine...", "This opens the possibility that..."

The key distinction: You CAN share original ideas, interpretations, and speculation.
Just don't present them as established facts or research findings.
""")

    return "\n".join(parts)


async def run_citation_pipeline(
    topic_data: dict,
    hierarchy: Dict[str, Dict[str, List[str]]],
    book_plan: str,
    section_plans: Dict[str, dict],
    output_dir: str,
    language_model,
    confidence_threshold: float = 0.75,
    skip_low_importance: bool = True,
    max_concurrent_verifications: int = 10,
) -> CitationManager:
    """
    Run the claim-first citation pipeline.

    FLOW:
    1. Plan claims for each subsection
    2. Verify all planned claims with Perplexity
    3. Build CitationManager with strict constraints

    Args:
        topic_data: {topic, goal, audience, book_name}
        hierarchy: {chapter: {section: [subsections]}}
        book_plan: Formatted book plan string
        section_plans: {chapter: {section_plans: [...]}}
        output_dir: Directory for outputs
        language_model: Synalinks language model
        confidence_threshold: Minimum confidence to accept citations
        skip_low_importance: Skip verification for low-importance claims
        max_concurrent_verifications: Max concurrent Perplexity API calls

    Returns:
        CitationManager for accessing citations during content generation
    """
    logger.info("=" * 60)
    logger.info("CLAIM-FIRST CITATION PIPELINE")
    logger.info("=" * 60)

    citations_dir = os.path.join(output_dir, "citations")
    os.makedirs(citations_dir, exist_ok=True)

    # =========================================================================
    # CHECK FOR CACHED RESULTS
    # =========================================================================
    cached_claims = None
    cached_verified = None
    cached_unverified = None
    cached_plans = None

    if output_exists(citations_dir, "01_planned_claims.json"):
        cached_claims = load_json_from_file(citations_dir, "01_planned_claims.json")
        logger.info(f"Found cached claims: {len(cached_claims)} claims")

    if output_exists(citations_dir, "01_subsection_plans.json"):
        cached_plans = load_json_from_file(citations_dir, "01_subsection_plans.json")
        logger.info(f"Found cached subsection plans: {len(cached_plans)} plans")

    if output_exists(citations_dir, "02_verified_citations.json"):
        cached_verified = load_json_from_file(citations_dir, "02_verified_citations.json")
        logger.info(f"Found cached verified citations: {len(cached_verified)} citations")

    if output_exists(citations_dir, "03_unverified_claims.json"):
        cached_unverified = load_json_from_file(citations_dir, "03_unverified_claims.json")
        logger.info(f"Found cached unverified claims: {len(cached_unverified)} claims")

    # =========================================================================
    # PHASE 1: Plan Claims for All Subsections (or load from cache)
    # =========================================================================
    if cached_claims and cached_plans:
        logger.info("\n[PHASE 1] Loading claims from cache...")
        # Reconstruct Claim objects from cached data
        all_claims = [
            Claim(
                id=c["id"],
                content=c["content"],
                chapter=c["chapter"],
                section=c["section"],
                subsection=c.get("subsection", ""),
                claim_type=c.get("type", "factual"),
                importance=c.get("importance", "medium"),
            )
            for c in cached_claims
        ]
        # For subsection_plans, we just use the cached dict (won't have full SubsectionClaimPlan objects)
        subsection_plans = cached_plans
        logger.info(f"Loaded {len(all_claims)} claims from cache")
    else:
        logger.info("\n[PHASE 1] Planning claims for all subsections...")

        subsection_plans, all_claims = await plan_all_subsection_claims(
            topic_data=topic_data,
            hierarchy=hierarchy,
            book_plan=book_plan,
            section_plans=section_plans,
            language_model=language_model,
            max_concurrent=10,
        )

        # Save planned claims
        claims_data = [
            {
                "id": c.id,
                "content": c.content,
                "chapter": c.chapter,
                "section": c.section,
                "subsection": c.subsection,
                "type": c.claim_type,
                "importance": c.importance,
            }
            for c in all_claims
        ]
        save_json_to_file(citations_dir, "01_planned_claims.json", claims_data)

        # Save subsection plans
        plans_data = {
            key: plan.get_json() if hasattr(plan, 'get_json') else str(plan)
            for key, plan in subsection_plans.items()
        }
        save_json_to_file(citations_dir, "01_subsection_plans.json", plans_data)

        logger.info(f"Planned {len(all_claims)} claims across {len(subsection_plans)} subsections")

    # =========================================================================
    # PHASE 2: Filter and Verify Claims (with partial resume support)
    # =========================================================================
    # Build list of claims to verify
    if skip_low_importance:
        claims_to_verify = [c for c in all_claims if c.importance != "low"]
        logger.info(f"Verifying {len(claims_to_verify)}/{len(all_claims)} claims (skipping low importance)")
    else:
        claims_to_verify = all_claims

    # Check for partial results and determine which claims still need verification
    verified_citations = []
    unverified_claims = []
    already_processed_ids = set()

    if cached_verified is not None:
        # Reconstruct already verified citations
        verified_citations = [
            VerifiedCitation(
                id=f"cite_{vc['claim_id']}",
                claim_id=vc["claim_id"],
                source_id=vc.get("source_url", ""),
                passage_id="",
                confidence=vc.get("confidence", 0.8),
                supporting_quote=vc.get("quote", ""),
                citation_text=vc.get("citation", ""),
                full_reference=vc.get("full_reference", ""),
            )
            for vc in cached_verified
        ]
        already_processed_ids.update(vc["claim_id"] for vc in cached_verified)
        logger.info(f"Found {len(verified_citations)} already verified claims in cache")

    if cached_unverified is not None:
        # Reconstruct already unverified claims
        unverified_claims = [
            Claim(
                id=c["id"],
                content=c["content"],
                chapter=c["chapter"],
                section=c["section"],
                subsection=c.get("subsection", ""),
                claim_type=c.get("type", "factual"),
                importance=c.get("importance", "medium"),
            )
            for c in cached_unverified
        ]
        already_processed_ids.update(c["id"] for c in cached_unverified)
        logger.info(f"Found {len(unverified_claims)} already unverified claims in cache")

    # Filter to only claims not yet processed
    remaining_claims = [c for c in claims_to_verify if c.id not in already_processed_ids]

    if not remaining_claims:
        if verified_citations or unverified_claims:
            logger.info("\n[PHASE 2] All claims already verified (loaded from cache)")
        else:
            logger.info("No claims to verify")
            return CitationManager(all_claims, [], [], subsection_plans)
    else:
        logger.info(f"\n[PHASE 2] Verifying {len(remaining_claims)} remaining claims with Gemini Search Grounding...")
        logger.info(f"  (Skipping {len(already_processed_ids)} already processed claims)")

        new_verified, new_unverified = await verify_all_claims(
            claims=remaining_claims,
            topic_context=topic_data["topic"],
            confidence_threshold=confidence_threshold,
            max_concurrent=max_concurrent_verifications,
            delay_between_requests=0.2,
            citations_dir=citations_dir,
            all_claims=all_claims,
            existing_verified=verified_citations,
            existing_unverified=unverified_claims,
        )

        # Merge with cached results
        verified_citations.extend(new_verified)
        unverified_claims.extend(new_unverified)

        # Save verification results
        verified_data = [
            {
                "claim_id": vc.claim_id,
                "claim_content": next((c.content for c in all_claims if c.id == vc.claim_id), ""),
                "citation": vc.citation_text,
                "confidence": vc.confidence,
                "source_url": vc.source_id,
                "quote": vc.supporting_quote[:300] if vc.supporting_quote else "",
                "full_reference": vc.full_reference,
            }
            for vc in verified_citations
        ]
        save_json_to_file(citations_dir, "02_verified_citations.json", verified_data)

        unverified_data = [
            {
                "id": c.id,
                "content": c.content,
                "chapter": c.chapter,
                "section": c.section,
                "subsection": c.subsection,
                "importance": c.importance,
            }
            for c in unverified_claims
        ]
        save_json_to_file(citations_dir, "03_unverified_claims.json", unverified_data)

    # =========================================================================
    # PHASE 3: Build Citation Manager
    # =========================================================================
    logger.info("\n[PHASE 3] Building citation manager...")

    manager = CitationManager(
        claims=all_claims,
        verified_citations=verified_citations,
        unverified_claims=unverified_claims,
        subsection_plans=subsection_plans,
    )

    # Save bibliography
    bibliography = manager.get_bibliography_markdown()
    if bibliography:
        save_to_file(citations_dir, "04_bibliography.md", bibliography)

    # =========================================================================
    # Summary
    # =========================================================================
    total = len(claims_to_verify)
    verified = len(verified_citations)
    rate = (verified / total * 100) if total > 0 else 0

    logger.info("\n" + "=" * 60)
    logger.info("CITATION PIPELINE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Subsections planned: {len(subsection_plans)}")
    logger.info(f"Claims planned: {len(all_claims)}")
    logger.info(f"Claims verified: {verified}/{total} ({rate:.1f}%)")
    logger.info(f"Unique references: {len(manager.get_all_references())}")
    logger.info(f"Output directory: {citations_dir}")

    # Log unverified claims prominently
    if unverified_claims:
        logger.info("\n" + "-" * 60)
        logger.info(f"UNVERIFIED CLAIMS ({len(unverified_claims)}) - These will be FORBIDDEN in content:")
        logger.info("-" * 60)
        for i, claim in enumerate(unverified_claims, 1):
            logger.info(f"  [{i}] ({claim.importance}) {claim.subsection or claim.section}:")
            logger.info(f"      \"{claim.content[:100]}{'...' if len(claim.content) > 100 else ''}\"")
        logger.info("-" * 60)

    # Log verified claims for reference
    if verified_citations:
        logger.info("\n" + "-" * 60)
        logger.info(f"VERIFIED CLAIMS ({len(verified_citations)}) - Available for use with citations:")
        logger.info("-" * 60)
        for i, vc in enumerate(verified_citations, 1):
            claim = next((c for c in all_claims if c.id == vc.claim_id), None)
            claim_text = claim.content[:80] if claim else "Unknown"
            logger.info(f"  [{i}] \"{claim_text}...\" → ({vc.citation_text})")
        logger.info("-" * 60)

    logger.info("=" * 60)

    return manager
