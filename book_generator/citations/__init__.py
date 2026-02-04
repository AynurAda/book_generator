"""
Citation generation and verification system.

This module handles:
- Extracting factual claims from outlines
- Finding and downloading sources
- Verifying claims against source passages
- Injecting citations into content generation
"""

from .models import (
    Claim,
    Source,
    Passage,
    VerifiedCitation,
    CitationContext,
)
from .pipeline import run_citation_pipeline
from .injection import get_citation_context_for_section

__all__ = [
    "Claim",
    "Source",
    "Passage",
    "VerifiedCitation",
    "CitationContext",
    "run_citation_pipeline",
    "get_citation_context_for_section",
]
