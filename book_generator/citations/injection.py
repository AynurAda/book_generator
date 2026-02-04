"""
Citation injection into content generation.

This module creates the citation context that CONSTRAINS content
generation to only include verified, citable claims.

THE KEY PRINCIPLE:
Content generation receives a list of "allowed claims" - factual
statements that have been verified against sources. The generator
is instructed to ONLY use these claims and must cite them properly.
"""

import logging
from typing import List, Dict, Optional

from .models import (
    Claim,
    VerifiedCitation,
    CitationContext,
)
from .knowledge_base import CitationStore

logger = logging.getLogger(__name__)


def build_citation_context(
    chapter: str,
    section: str,
    claims: List[Claim],
    verified_citations: List[VerifiedCitation],
    claim_lookup: Dict[str, Claim],
) -> CitationContext:
    """
    Build a CitationContext for content generation.

    This context tells the generator exactly what claims it CAN make
    and how to cite them.

    Args:
        chapter: Chapter name
        section: Section name
        claims: Claims belonging to this section
        verified_citations: All verified citations
        claim_lookup: Mapping of claim_id to Claim

    Returns:
        CitationContext constraining content generation
    """
    # Find claims for this section that were verified
    section_claims = [c for c in claims if c.chapter == chapter and c.section == section]
    verified_claim_ids = {vc.claim_id for vc in verified_citations}

    allowed_claims = []
    references = set()

    for claim in section_claims:
        if claim.id in verified_claim_ids:
            # Find the citation for this claim
            citation = next(
                (vc for vc in verified_citations if vc.claim_id == claim.id),
                None
            )
            if citation:
                allowed_claims.append({
                    "claim": claim.content,
                    "citation": citation.citation_text,
                    "source_quote": citation.supporting_quote,
                    "importance": claim.importance,
                })
                references.add(citation.full_reference)

    return CitationContext(
        section_name=section,
        allowed_claims=allowed_claims,
        citation_format="(Author, Year) or (Author, Year, p. X)",
        references=sorted(list(references)),
    )


def get_citation_context_for_section(
    chapter: str,
    section: str,
    citation_store: CitationStore,
    claims: List[Claim],
) -> CitationContext:
    """
    Get the citation context for a specific section.

    Args:
        chapter: Chapter name
        section: Section name
        citation_store: CitationStore with verified citations
        claims: All claims

    Returns:
        CitationContext for the section
    """
    claim_lookup = {c.id: c for c in claims}

    return build_citation_context(
        chapter=chapter,
        section=section,
        claims=claims,
        verified_citations=citation_store.verified_citations,
        claim_lookup=claim_lookup,
    )


def format_citation_instructions(context: CitationContext) -> str:
    """
    Format citation context as instructions for the content generator.

    This is injected into the generator's instructions to constrain
    what factual claims can be made.

    Args:
        context: CitationContext for the section

    Returns:
        Formatted instruction string
    """
    if not context.allowed_claims:
        return """
CITATION POLICY:
This section has no verified citations. You may include:
- Explanations and conceptual discussions
- Examples you create
- General knowledge that doesn't require citation
- Logical reasoning and analysis

DO NOT include:
- Specific statistics or numbers
- Claims about research findings
- Attributions to specific people or papers
- Any factual claim that would normally require a citation

When in doubt, phrase things as explanations rather than facts.
"""

    claims_text = "\n".join([
        f"- CLAIM: \"{c['claim']}\"\n  CITE AS: {c['citation']}\n  SOURCE SAYS: \"{c['source_quote'][:200]}...\""
        for c in context.allowed_claims
    ])

    return f"""
CITATION POLICY - MANDATORY:

You MUST follow these citation rules exactly:

1. ALLOWED FACTUAL CLAIMS:
The following claims have been verified and MUST be cited when used:

{claims_text}

2. CITATION FORMAT:
Use inline citations: {context.citation_format}
Example: "Studies show X (Smith, 2023)." or "According to Smith (2023), X."

3. STRICT RULES:
- You MAY ONLY make the factual claims listed above
- Each claim MUST include its citation
- DO NOT modify the claims - use them as stated
- DO NOT add additional factual claims that aren't in the list
- DO NOT invent statistics, findings, or attributions

4. WHAT YOU CAN FREELY WRITE:
- Explanations of concepts (without claiming research support)
- Examples you create to illustrate points
- Logical reasoning and analysis
- Transitions and narrative flow
- Definitions (if not claiming authoritative source)

5. IF UNSURE:
Phrase as explanation: "One approach is to..." rather than "Research shows..."
Ask yourself: "Is this a factual claim?" If yes, it must be in the allowed list.

REMEMBER: It's better to have less content than to include unverified claims.
"""


def format_bibliography(citation_store: CitationStore) -> str:
    """
    Format the full bibliography for the book.

    Args:
        citation_store: CitationStore with all citations

    Returns:
        Formatted bibliography markdown
    """
    references = citation_store.get_all_references()

    if not references:
        return ""

    lines = ["## References", ""]
    for ref in references:
        lines.append(f"- {ref}")
        lines.append("")

    return "\n".join(lines)


def remove_unverified_claims_from_outline(
    outline: dict,
    unverified_claims: List[Claim],
) -> dict:
    """
    Modify the outline to remove or flag unverified claims.

    Rather than removing content from the outline structure itself
    (which would break the flow), we add metadata that the content
    generator can use to know what to avoid.

    Args:
        outline: The book outline
        unverified_claims: Claims that couldn't be verified

    Returns:
        Modified outline with unverified claim metadata
    """
    # Create lookup of unverified claims by section
    unverified_by_section = {}
    for claim in unverified_claims:
        key = (claim.chapter, claim.section)
        if key not in unverified_by_section:
            unverified_by_section[key] = []
        unverified_by_section[key].append(claim.content)

    # Add metadata to outline
    modified_outline = outline.copy()
    modified_outline["_unverified_claims"] = {
        f"{k[0]}::{k[1]}": v
        for k, v in unverified_by_section.items()
    }
    modified_outline["_citation_enabled"] = True

    logger.info(f"Marked {len(unverified_claims)} unverified claims in outline")

    return modified_outline


def get_unverified_claims_for_section(
    outline: dict,
    chapter: str,
    section: str,
) -> List[str]:
    """
    Get list of unverified claims for a section.

    Content generator should avoid these topics or rephrase
    them as non-factual explanations.

    Args:
        outline: Modified outline with metadata
        chapter: Chapter name
        section: Section name

    Returns:
        List of unverified claim texts
    """
    unverified = outline.get("_unverified_claims", {})
    key = f"{chapter}::{section}"
    return unverified.get(key, [])


def format_avoidance_instructions(unverified_claims: List[str]) -> str:
    """
    Format instructions for avoiding unverified claims.

    Args:
        unverified_claims: Claims to avoid

    Returns:
        Instruction string
    """
    if not unverified_claims:
        return ""

    claims_text = "\n".join([f"- {c}" for c in unverified_claims])

    return f"""
CLAIMS TO AVOID:
The following claims could not be verified and should NOT be stated as facts:

{claims_text}

If these topics are essential to the section:
- Discuss them conceptually without claiming research support
- Use phrases like "One approach is..." or "It's common to..."
- Avoid specific numbers, names, or dates related to these claims
"""
