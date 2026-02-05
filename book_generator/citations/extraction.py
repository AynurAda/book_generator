"""
Claim extraction from book outlines.

Extracts factual claims that need citation verification
from the chapter outline before content generation.
"""

import logging
from typing import List
import hashlib

import synalinks

from .models import (
    Claim,
    ClaimExtractionInput,
    ExtractedClaims,
)

logger = logging.getLogger(__name__)


def generate_claim_id(chapter: str, section: str, index: int) -> str:
    """Generate a unique claim ID."""
    base = f"{chapter}_{section}_{index}"
    return hashlib.md5(base.encode()).hexdigest()[:12]


async def extract_claims_from_chapter(
    chapter_name: str,
    sections: list[dict],
    topic: str,
    goal: str,
    language_model,
) -> List[Claim]:
    """
    Extract all factual claims from a chapter's outline.

    Args:
        chapter_name: Name of the chapter
        sections: List of section dicts with subconcepts
        topic: Book topic for context
        goal: Book goal for context
        language_model: Synalinks language model

    Returns:
        List of Claim objects that need verification
    """
    logger.info(f"Extracting claims from chapter: {chapter_name}")

    # Format sections for the prompt
    sections_text = ""
    for section in sections:
        section_name = section.get("subconcept", "")
        subsections = section.get("subsubconcepts", [])
        sections_text += f"\n## {section_name}\n"
        for sub in subsections:
            sections_text += f"  - {sub}\n"

    extractor = synalinks.Generator(
        data_model=ExtractedClaims,
        language_model=language_model,
        temperature=1.0,
        instructions="""You are a fact-checker analyzing a book outline to identify claims that need citations.

TASK: Extract ALL factual claims from this chapter outline that would require a citation in an academic or professional book.

A FACTUAL CLAIM is any statement that:
1. **Statistics/Numbers**: "X% of systems use...", "Performance improved by Y..."
2. **Research Findings**: "Studies show...", "Research demonstrates..."
3. **Definitions**: Technical definitions that have authoritative sources
4. **Attributions**: "Proposed by X", "First introduced in Y paper"
5. **Historical Facts**: "In 2020, company X released...", "The field emerged from..."
6. **Technical Specifications**: "The algorithm has O(n) complexity...", "Requires minimum X memory"

For each claim, determine:
- **content**: The specific factual claim (be precise)
- **section**: Which section it belongs to
- **subsection**: Which subsection (if applicable)
- **claim_type**: One of: statistic, research_finding, definition, attribution, historical, technical
- **importance**: critical (book fails without it), high (key point), medium (supporting), low (nice to have)

BE THOROUGH: Every factual statement that a skeptical reader might question needs a citation.
DO NOT include: opinions, explanations, examples the author creates, or general knowledge."""
    )

    input_data = ClaimExtractionInput(
        chapter_name=chapter_name,
        sections=sections_text,
        topic=topic,
        goal=goal,
    )

    result = await extractor(input_data)
    result_dict = result.get_json()

    claims = []
    for i, claim_data in enumerate(result_dict.get("claims", [])):
        # Handle both dict and object access patterns
        if isinstance(claim_data, dict):
            content = claim_data.get("content", "")
            section = claim_data.get("section", "")
            subsection = claim_data.get("subsection")
            claim_type = claim_data.get("claim_type", "technical")
            importance = claim_data.get("importance", "medium")
        else:
            # Object-style access
            content = getattr(claim_data, "content", "")
            section = getattr(claim_data, "section", "")
            subsection = getattr(claim_data, "subsection", None)
            claim_type = getattr(claim_data, "claim_type", "technical")
            importance = getattr(claim_data, "importance", "medium")

        claim = Claim(
            id=generate_claim_id(chapter_name, section, i),
            content=content,
            chapter=chapter_name,
            section=section,
            subsection=subsection,
            claim_type=claim_type,
            importance=importance,
        )
        claims.append(claim)

    logger.info(f"Extracted {len(claims)} claims from {chapter_name}")
    return claims


async def extract_all_claims(
    outline: dict,
    topic: str,
    goal: str,
    language_model,
) -> List[Claim]:
    """
    Extract claims from all chapters in the outline.

    Args:
        outline: Full book outline with concepts/subconcepts
        topic: Book topic
        goal: Book goal
        language_model: Synalinks language model

    Returns:
        List of all claims needing verification
    """
    all_claims = []

    concepts = outline.get("concepts", [])
    for chapter in concepts:
        chapter_name = chapter.get("concept", "")
        sections = chapter.get("subconcepts", [])

        if not chapter_name or not sections:
            continue

        chapter_claims = await extract_claims_from_chapter(
            chapter_name=chapter_name,
            sections=sections,
            topic=topic,
            goal=goal,
            language_model=language_model,
        )
        all_claims.extend(chapter_claims)

    logger.info(f"Total claims extracted: {len(all_claims)}")

    # Log breakdown by importance
    critical = sum(1 for c in all_claims if c.importance == "critical")
    high = sum(1 for c in all_claims if c.importance == "high")
    medium = sum(1 for c in all_claims if c.importance == "medium")
    low = sum(1 for c in all_claims if c.importance == "low")
    logger.info(f"Claim importance: {critical} critical, {high} high, {medium} medium, {low} low")

    return all_claims
