"""
Citation generation and verification system.

CLAIM-FIRST APPROACH:
1. Plan claims for each subsection BEFORE writing
2. Verify all planned claims with Perplexity
3. Content generation is STRICTLY constrained to verified claims only

This ensures NO unverified factual claims can appear in the final text.
"""

from .models import (
    Claim,
    Source,
    Passage,
    VerifiedCitation,
    CitationContext,
)
from .pipeline import run_citation_pipeline, CitationManager
from .claim_planning import (
    plan_all_subsection_claims,
    SubsectionClaimPlan,
    PlannedClaim,
)
from .injection import (
    format_citation_instructions,
    remove_unverified_claims_from_outline,
    format_bibliography,
)

__all__ = [
    "Claim",
    "Source",
    "Passage",
    "VerifiedCitation",
    "CitationContext",
    "CitationManager",
    "run_citation_pipeline",
    "plan_all_subsection_claims",
    "SubsectionClaimPlan",
    "PlannedClaim",
    "format_citation_instructions",
    "remove_unverified_claims_from_outline",
    "format_bibliography",
]
