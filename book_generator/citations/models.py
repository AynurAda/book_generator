"""
Data models for the citation system.

These models define the structure of claims, sources, passages,
and verified citations used throughout the citation pipeline.
"""

from typing import Optional, Literal
import synalinks


# =============================================================================
# Core Entity Models (for Knowledge Base)
# =============================================================================

class Claim(synalinks.DataModel):
    """A factual claim extracted from the outline that needs citation."""
    id: str = synalinks.Field(
        description="Unique claim identifier (chapter_section_index)"
    )
    content: str = synalinks.Field(
        description="The factual claim text that needs to be supported"
    )
    chapter: str = synalinks.Field(
        description="Chapter name this claim belongs to"
    )
    section: str = synalinks.Field(
        description="Section name within the chapter"
    )
    subsection: Optional[str] = synalinks.Field(
        default=None,
        description="Subsection name if applicable"
    )
    claim_type: str = synalinks.Field(
        description="Type: statistic, research_finding, definition, attribution, historical, technical"
    )
    importance: str = synalinks.Field(
        default="medium",
        description="Importance level: critical, high, medium, low"
    )


class Source(synalinks.DataModel):
    """A source document that may support claims."""
    id: str = synalinks.Field(
        description="Unique source identifier"
    )
    title: str = synalinks.Field(
        description="Document/paper/article title"
    )
    url: str = synalinks.Field(
        description="Source URL"
    )
    authors: str = synalinks.Field(
        description="Author names (comma-separated)"
    )
    year: str = synalinks.Field(
        description="Publication year"
    )
    source_type: str = synalinks.Field(
        description="Type: paper, article, documentation, book, website"
    )
    pdf_path: Optional[str] = synalinks.Field(
        default=None,
        description="Local path to downloaded PDF if available"
    )
    content_hash: Optional[str] = synalinks.Field(
        default=None,
        description="Hash of content for deduplication"
    )


class Passage(synalinks.DataModel):
    """A chunk of text from a source document."""
    id: str = synalinks.Field(
        description="Unique passage identifier (source_id_chunk_index)"
    )
    content: str = synalinks.Field(
        description="The passage text content"
    )
    source_id: str = synalinks.Field(
        description="Reference to parent Source"
    )
    page_number: Optional[int] = synalinks.Field(
        default=None,
        description="Page number in source document"
    )
    section_title: Optional[str] = synalinks.Field(
        default=None,
        description="Section title in source if identifiable"
    )


class VerifiedCitation(synalinks.DataModel):
    """A verified relationship between a claim and supporting source."""
    id: str = synalinks.Field(
        description="Unique citation identifier"
    )
    claim_id: str = synalinks.Field(
        description="The claim being cited"
    )
    source_id: str = synalinks.Field(
        description="The supporting source"
    )
    passage_id: str = synalinks.Field(
        description="Specific passage that supports the claim"
    )
    confidence: float = synalinks.Field(
        description="Verification confidence score 0.0-1.0"
    )
    supporting_quote: str = synalinks.Field(
        description="Direct quote from passage that supports claim"
    )
    citation_text: str = synalinks.Field(
        description="Formatted citation string (e.g., 'Smith et al., 2023')"
    )
    full_reference: str = synalinks.Field(
        description="Full bibliographic reference"
    )


# =============================================================================
# Pipeline Input/Output Models
# =============================================================================

class ClaimExtractionInput(synalinks.DataModel):
    """Input for extracting claims from a chapter outline."""
    chapter_name: str = synalinks.Field(
        description="Name of the chapter"
    )
    sections: str = synalinks.Field(
        description="Formatted list of sections and subsections"
    )
    topic: str = synalinks.Field(
        description="Book topic for context"
    )
    goal: str = synalinks.Field(
        description="Book goal for context"
    )


class ExtractedClaimItem(synalinks.DataModel):
    """A single extracted claim from the outline."""
    content: str = synalinks.Field(
        description="The factual claim text"
    )
    section: str = synalinks.Field(
        description="Section name this claim belongs to"
    )
    subsection: str = synalinks.Field(
        default="",
        description="Subsection name if applicable"
    )
    claim_type: str = synalinks.Field(
        description="Type: statistic, research_finding, definition, attribution, historical, technical"
    )
    importance: str = synalinks.Field(
        description="Importance level: critical, high, medium, low"
    )


class ExtractedClaims(synalinks.DataModel):
    """Output from claim extraction."""
    thinking: list[str] = synalinks.Field(
        description="Step-by-step reasoning about what claims exist"
    )
    claims: list[ExtractedClaimItem] = synalinks.Field(
        description="List of extracted claims"
    )


class SourceSearchInput(synalinks.DataModel):
    """Input for searching sources for a claim."""
    claim_content: str = synalinks.Field(
        description="The claim to find sources for"
    )
    claim_type: str = synalinks.Field(
        description="Type of claim"
    )
    topic_context: str = synalinks.Field(
        description="Book topic for search context"
    )


class SearchQueries(synalinks.DataModel):
    """Generated search queries for finding sources."""
    thinking: list[str] = synalinks.Field(
        description="Reasoning about what to search for"
    )
    academic_queries: list[str] = synalinks.Field(
        description="Queries for academic sources (papers, journals)"
    )
    documentation_queries: list[str] = synalinks.Field(
        description="Queries for technical documentation"
    )
    general_queries: list[str] = synalinks.Field(
        description="Queries for general authoritative sources"
    )


class VerificationInput(synalinks.DataModel):
    """Input for verifying if a passage supports a claim."""
    claim: str = synalinks.Field(
        description="The factual claim to verify"
    )
    passage: str = synalinks.Field(
        description="The passage that might support the claim"
    )
    source_info: str = synalinks.Field(
        description="Source metadata (title, authors, year)"
    )


class VerificationResult(synalinks.DataModel):
    """Result of verifying a claim against a passage."""
    thinking: list[str] = synalinks.Field(
        description="Step-by-step verification reasoning"
    )
    is_supported: bool = synalinks.Field(
        description="Does the passage directly support the claim?"
    )
    confidence: float = synalinks.Field(
        description="Confidence score 0.0-1.0"
    )
    support_type: str = synalinks.Field(
        description="Type: direct_quote, paraphrase, inference, not_supported"
    )
    supporting_quote: str = synalinks.Field(
        description="The specific quote that supports (empty if not supported)"
    )
    explanation: str = synalinks.Field(
        description="Explanation of why it does/doesn't support"
    )


# =============================================================================
# Citation Context for Content Generation
# =============================================================================

class CitableClaimEntry(synalinks.DataModel):
    """A single citable claim with its citation info."""
    claim: str = synalinks.Field(
        description="The factual claim that can be made"
    )
    citation: str = synalinks.Field(
        description="Inline citation to use (e.g., 'Smith et al., 2023')"
    )
    source_quote: str = synalinks.Field(
        description="Supporting quote from source for accuracy"
    )


class CitationContext(synalinks.DataModel):
    """
    Citation context passed to content generation.

    This is the KEY structure that constrains content generation
    to only include verified, citable claims.
    """
    section_name: str = synalinks.Field(
        description="The section being generated"
    )
    allowed_claims: list[CitableClaimEntry] = synalinks.Field(
        description="List of claims that CAN be made (with their citations)"
    )
    citation_format: str = synalinks.Field(
        description="How to format inline citations"
    )
    references: list[str] = synalinks.Field(
        description="Full references for the bibliography"
    )
