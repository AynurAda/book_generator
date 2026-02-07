"""
Research parsing using Synalinks with quality assurance.

Uses Synalinks patterns (Branch, Generator, DataModel) for all logic.
No regex, no keyword matching, no dirty hacks.
"""

import logging
from typing import Dict, List

import synalinks

from .models import RawResearch, FieldKnowledge, Paper

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

class PaperList(synalinks.DataModel):
    """Extracted papers from research text."""
    papers: List[Paper] = synalinks.Field(
        description="ALL papers, studies, and research works mentioned in the text"
    )


class ExtractionAssessment(synalinks.DataModel):
    """Assessment of paper extraction completeness."""
    is_complete: bool = synalinks.Field(
        description="True if we have extracted most/all papers mentioned in the text"
    )
    missing_papers: List[str] = synalinks.Field(
        description="Brief descriptions of papers that appear to be missing from extraction"
    )
    confidence: str = synalinks.Field(
        description="Confidence level: 'high', 'medium', or 'low'"
    )


class PaperCountEstimate(synalinks.DataModel):
    """Estimate of papers in research text."""
    estimated_count: int = synalinks.Field(
        description="Estimated number of distinct papers mentioned in the text"
    )
    reasoning: str = synalinks.Field(
        description="Brief explanation of how this estimate was derived"
    )


class MissingPapersInput(synalinks.DataModel):
    """Input for extracting missing papers."""
    original_text: str = synalinks.Field(description="The original research text")
    already_extracted: str = synalinks.Field(description="Papers already extracted")
    missing_hints: str = synalinks.Field(description="Hints about what papers are missing")


# =============================================================================
# Instructions
# =============================================================================

OVERVIEW_INSTRUCTIONS = """Extract the high-level structure from this research output.

For the SUMMARY:
- Write 2-3 paragraphs capturing the current state of the field
- Focus on what's new, what's changing, and where things are heading
- Make it useful for someone writing a book about this topic

For THEMES:
- Identify ALL major research themes and directions mentioned
- These should be broad enough to be chapter topics
- Be exhaustive - list every theme you can identify

For FRAMEWORKS (CRITICAL - be thorough):
- Extract EVERY tool, library, framework, or open-source project mentioned
- This helps readers know what tools exist in the field
- For each framework include:
  * name: The exact project/library name
  * description: What it does in 1-2 sentences
  * approach: How it works conceptually
  * use_cases: What problems it solves, when to use it
  * url: GitHub URL or project website if mentioned (for reader reference)

For OPEN_PROBLEMS:
- List ALL unsolved challenges and active research questions
- These represent the frontier of the field

Leave the papers list empty - papers will be extracted separately."""


PAPER_EXTRACTION_INSTRUCTIONS = """Extract ALL papers mentioned in this research text.

Your task is to find EVERY paper, study, or research work mentioned. Look for:
- Explicit paper titles
- Papers referenced by author name and year
- Studies mentioned by name
- Works cited with references
- Any research described with enough detail to be a paper

For EACH paper found, extract:
- title: The paper title (reconstruct if not explicit)
- authors: Author names (use "Unknown" if not stated)
- year: Publication year (estimate from context if needed)
- venue: Where published (use "Unknown" if not stated)
- problem: What problem does this paper address?
- method: What is the key approach or contribution?
- results: What were the main findings?
- significance: Why does this paper matter?

BE EXHAUSTIVE. It's better to extract a paper with sparse details than to miss it entirely."""


MISSING_PAPERS_INSTRUCTIONS = """Extract papers that were MISSED in the previous extraction.

You are given:
1. The original research text
2. Papers that were already extracted
3. Hints about what might be missing

Find and extract papers that:
- Were mentioned but not yet extracted
- Match the missing hints provided
- Are distinct from already-extracted papers

Only extract NEW papers not in the already-extracted list."""


ESTIMATE_INSTRUCTIONS = """Estimate how many distinct papers are mentioned in this research text.

Count carefully:
- Each unique paper title or study name
- Papers referenced by author and year
- Distinct research works described
- Citations at the end of sections

Do NOT count:
- Multiple mentions of the same paper
- General references to "research" or "studies" without specifics
- Frameworks or tools (only count their associated papers)

Provide your best estimate and explain your reasoning."""


ASSESSMENT_INSTRUCTIONS = """Assess whether the paper extraction is complete.

You are given:
1. The original research text
2. The papers that were extracted

Determine:
1. Have we extracted most of the papers mentioned?
2. Are there significant papers that appear to be missing?
3. How confident are you in this assessment?

If papers are missing, describe them briefly so they can be found in a follow-up extraction."""


# =============================================================================
# Synalinks Programs
# =============================================================================

async def build_overview_program(lm: synalinks.LanguageModel) -> synalinks.Program:
    """Build program for overview extraction."""
    inputs = synalinks.Input(data_model=RawResearch)
    outputs = await synalinks.Generator(
        data_model=FieldKnowledge,
        language_model=lm,
        instructions=OVERVIEW_INSTRUCTIONS,
        temperature=1.0,
    )(inputs)
    return synalinks.Program(inputs=inputs, outputs=outputs, name="overview_parser")


async def build_paper_extractor(lm: synalinks.LanguageModel) -> synalinks.Program:
    """Build program for paper extraction."""
    inputs = synalinks.Input(data_model=RawResearch)
    outputs = await synalinks.Generator(
        data_model=PaperList,
        language_model=lm,
        instructions=PAPER_EXTRACTION_INSTRUCTIONS,
        temperature=1.0,
    )(inputs)
    return synalinks.Program(inputs=inputs, outputs=outputs, name="paper_extractor")


async def build_missing_paper_extractor(lm: synalinks.LanguageModel) -> synalinks.Program:
    """Build program for extracting missing papers."""
    inputs = synalinks.Input(data_model=MissingPapersInput)
    outputs = await synalinks.Generator(
        data_model=PaperList,
        language_model=lm,
        instructions=MISSING_PAPERS_INSTRUCTIONS,
        temperature=1.0,
    )(inputs)
    return synalinks.Program(inputs=inputs, outputs=outputs, name="missing_paper_extractor")


async def build_estimator(lm: synalinks.LanguageModel) -> synalinks.Program:
    """Build program for estimating paper count."""
    inputs = synalinks.Input(data_model=RawResearch)
    outputs = await synalinks.Generator(
        data_model=PaperCountEstimate,
        language_model=lm,
        instructions=ESTIMATE_INSTRUCTIONS,
        temperature=1.0,
    )(inputs)
    return synalinks.Program(inputs=inputs, outputs=outputs, name="paper_estimator")


async def build_assessor(lm: synalinks.LanguageModel) -> synalinks.Program:
    """Build program for assessing extraction completeness."""

    class AssessmentInput(synalinks.DataModel):
        research_text: str = synalinks.Field(description="Original research text")
        extracted_papers: str = synalinks.Field(description="List of extracted paper titles")

    inputs = synalinks.Input(data_model=AssessmentInput)
    outputs = await synalinks.Generator(
        data_model=ExtractionAssessment,
        language_model=lm,
        instructions=ASSESSMENT_INSTRUCTIONS,
        temperature=1.0,
    )(inputs)
    return synalinks.Program(inputs=inputs, outputs=outputs, name="extraction_assessor")


# =============================================================================
# Main Parsing Logic
# =============================================================================

async def extract_papers_with_quality_loop(
    text: str,
    language_model: synalinks.LanguageModel,
    max_iterations: int = 3,
) -> List[dict]:
    """
    Extract papers using Synalinks Branch for quality control.

    Uses LLM to:
    1. Estimate expected paper count
    2. Extract papers
    3. Assess if extraction is complete
    4. Extract missing papers if needed (via Branch)
    """
    logger.info("[QA] ═══════════════════════════════════════════════════")
    logger.info("[QA] PAPER EXTRACTION WITH LLM QUALITY CONTROL")
    logger.info("[QA] ═══════════════════════════════════════════════════")

    # Step 1: Estimate paper count using LLM
    logger.info("[QA] Step 1: Estimating paper count...")
    estimator = await build_estimator(language_model)
    estimate_result = await estimator(RawResearch(research_text=text))

    if estimate_result:
        estimate_data = estimate_result.get_json()
        estimated_count = estimate_data.get('estimated_count', 10)
        reasoning = estimate_data.get('reasoning', '')
        logger.info(f"[QA] Estimated {estimated_count} papers: {reasoning[:100]}...")
    else:
        estimated_count = 10
        logger.warning("[QA] Estimation failed, using default of 10")

    # Step 2: Initial paper extraction
    logger.info("[QA] Step 2: Initial paper extraction...")
    extractor = await build_paper_extractor(language_model)
    result = await extractor(RawResearch(research_text=text))

    if result is None:
        logger.error("[QA] Initial extraction failed")
        return []

    all_papers = result.get_json().get('papers', [])
    logger.info(f"[QA] Initial extraction: {len(all_papers)} papers")

    # Step 3: Quality loop using Branch
    assessor = await build_assessor(language_model)
    missing_extractor = await build_missing_paper_extractor(language_model)

    for iteration in range(max_iterations):
        logger.info(f"[QA] Step 3.{iteration + 1}: Assessing extraction completeness...")

        # Format extracted papers for assessment
        extracted_titles = "\n".join([
            f"- {p.get('title', 'Unknown')} ({p.get('year', '?')})"
            for p in all_papers
        ])

        # Create assessment input
        class AssessmentInput(synalinks.DataModel):
            research_text: str = synalinks.Field(description="Original research text")
            extracted_papers: str = synalinks.Field(description="List of extracted paper titles")

        assessment_input = AssessmentInput(
            research_text=text,
            extracted_papers=extracted_titles,
        )

        # Use Branch to decide: complete or need more extraction
        inputs = synalinks.Input(data_model=AssessmentInput)

        # Branch: Complete (return identity) vs Incomplete (extract more)
        (complete_output, incomplete_output) = await synalinks.Branch(
            question=f"""Assess the paper extraction:

EXTRACTED ({len(all_papers)} papers):
{extracted_titles[:2000]}

ESTIMATED: ~{estimated_count} papers in the text

Is extraction COMPLETE (we found most papers, minor gaps acceptable)
or INCOMPLETE (significant papers are clearly missing)?""",
            labels=["complete", "incomplete"],
            branches=[
                # Complete: just return the assessment
                synalinks.Generator(
                    data_model=ExtractionAssessment,
                    language_model=language_model,
                    instructions="Confirm extraction is complete. Set is_complete=True, missing_papers=[], confidence='high'.",
                    temperature=1.0,
                ),
                # Incomplete: return assessment with missing paper hints
                synalinks.Generator(
                    data_model=ExtractionAssessment,
                    language_model=language_model,
                    instructions=ASSESSMENT_INSTRUCTIONS,
                    temperature=1.0,
                ),
            ],
            language_model=language_model,
            temperature=1.0,
        )(assessment_input)

        # Merge branch outputs
        assessment = complete_output | incomplete_output

        if assessment is None:
            logger.warning("[QA] Assessment failed, stopping iteration")
            break

        assessment_data = assessment.get_json()
        is_complete = assessment_data.get('is_complete', True)
        missing_hints = assessment_data.get('missing_papers', [])
        confidence = assessment_data.get('confidence', 'unknown')

        logger.info(f"[QA] Assessment: complete={is_complete}, confidence={confidence}")

        if is_complete:
            logger.info("[QA] ✓ Extraction deemed complete by LLM")
            break

        if not missing_hints:
            logger.info("[QA] No missing paper hints provided, stopping")
            break

        # Extract missing papers
        logger.info(f"[QA] Extracting {len(missing_hints)} potentially missing papers...")

        missing_input = MissingPapersInput(
            original_text=text,
            already_extracted=extracted_titles,
            missing_hints="\n".join([f"- {hint}" for hint in missing_hints]),
        )

        missing_result = await missing_extractor(missing_input)

        if missing_result:
            new_papers = missing_result.get_json().get('papers', [])

            # Deduplicate by title (using LLM-friendly approach - just check exact matches)
            existing_titles = {p.get('title', '').lower().strip() for p in all_papers}
            added = 0
            for paper in new_papers:
                title = paper.get('title', '').lower().strip()
                if title and title not in existing_titles:
                    all_papers.append(paper)
                    existing_titles.add(title)
                    added += 1

            logger.info(f"[QA] Added {added} new papers (total: {len(all_papers)})")

            if added == 0:
                logger.info("[QA] No new papers found, stopping iteration")
                break
        else:
            logger.warning("[QA] Missing paper extraction failed")
            break

    logger.info(f"[QA] ═══════════════════════════════════════════════════")
    logger.info(f"[QA] Final extraction: {len(all_papers)} papers (estimated: {estimated_count})")
    logger.info(f"[QA] ═══════════════════════════════════════════════════")

    return all_papers


async def parse_research(
    raw_outputs: Dict[str, str],
    language_model: synalinks.LanguageModel,
) -> FieldKnowledge:
    """
    Parse raw research outputs into structured FieldKnowledge.

    Uses pure Synalinks patterns:
    1. Generator for structured extraction
    2. Branch for quality control decisions
    3. No regex, no keyword matching

    Args:
        raw_outputs: Dict mapping query names to research text
        language_model: The language model to use

    Returns:
        Structured FieldKnowledge object
    """
    # Combine all research outputs
    combined_parts = []
    for name, text in raw_outputs.items():
        if not text.startswith("ERROR:"):
            combined_parts.append(f"=== {name} ===\n\n{text}")

    combined = "\n\n---\n\n".join(combined_parts)

    logger.info(f"[QA] ═══════════════════════════════════════════════════")
    logger.info(f"[QA] RESEARCH PARSING (Pure Synalinks)")
    logger.info(f"[QA] ═══════════════════════════════════════════════════")
    logger.info(f"[QA] Input: {len(combined)} chars from {len(combined_parts)} queries")

    # Pass 1: Extract overview
    logger.info("[QA] Pass 1: Extracting overview...")
    overview_program = await build_overview_program(language_model)
    overview_result = await overview_program(RawResearch(research_text=combined))

    if overview_result is None:
        logger.error("[QA] Overview extraction failed")
        return FieldKnowledge(
            summary="Research parsing failed.",
            themes=[],
            papers=[],
            frameworks=[],
            open_problems=[],
        )

    overview_data = overview_result.get_json()
    logger.info(f"[QA] Overview: {len(overview_data.get('themes', []))} themes, "
                f"{len(overview_data.get('frameworks', []))} frameworks")

    # Pass 2: Extract papers with quality loop
    logger.info("[QA] Pass 2: Extracting papers with quality control...")
    papers = await extract_papers_with_quality_loop(combined, language_model)

    # Build final result
    final_data = {
        'summary': overview_data.get('summary', ''),
        'themes': overview_data.get('themes', []),
        'papers': papers,
        'frameworks': overview_data.get('frameworks', []),
        'open_problems': overview_data.get('open_problems', []),
    }

    logger.info(f"[QA] ═══════════════════════════════════════════════════")
    logger.info(f"[QA] PARSING COMPLETE")
    logger.info(f"[QA]   Papers: {len(papers)}")
    logger.info(f"[QA]   Themes: {len(final_data['themes'])}")
    logger.info(f"[QA]   Frameworks: {len(final_data['frameworks'])}")
    logger.info(f"[QA]   Open Problems: {len(final_data['open_problems'])}")
    logger.info(f"[QA] ═══════════════════════════════════════════════════")

    # Log paper titles
    for i, p in enumerate(papers[:10], 1):
        title = p.get('title', 'Unknown')[:60]
        year = p.get('year', '?')
        logger.info(f"[QA]   {i}. {title}... ({year})")
    if len(papers) > 10:
        logger.info(f"[QA]   ... and {len(papers) - 10} more papers")

    # Enrich papers with missing authors from arXiv
    logger.info("[QA] Enriching papers with missing authors from arXiv...")
    papers = await enrich_paper_authors(papers)
    final_data['papers'] = papers

    return FieldKnowledge(**final_data)


async def enrich_paper_authors(papers: List[dict]) -> List[dict]:
    """
    Enrich papers that have missing authors by looking them up on arXiv.

    Papers with authors like "Not specified", "Unknown", "N/A", or empty
    will be searched on arXiv to find the real authors.

    Args:
        papers: List of paper dicts from extraction

    Returns:
        Papers with enriched author information
    """
    from .arxiv_fetcher import search_arxiv

    BAD_AUTHORS = {"not specified", "unknown", "n/a", "none", ""}

    enriched_count = 0
    for paper in papers:
        authors = paper.get('authors', '').strip().lower()

        # Check if authors need enrichment
        if authors in BAD_AUTHORS:
            title = paper.get('title', '')
            if not title:
                continue

            logger.debug(f"[arXiv] Looking up authors for: {title[:50]}...")

            try:
                # Search arXiv by title
                results = await search_arxiv(title, max_results=3)

                if results:
                    # Use the first (most relevant) result
                    arxiv_paper = results[0]

                    # Check if title is similar enough (fuzzy match)
                    arxiv_title = arxiv_paper.title.lower()
                    paper_title = title.lower()

                    # Simple similarity: check if key words match
                    paper_words = set(paper_title.split())
                    arxiv_words = set(arxiv_title.split())
                    common = paper_words & arxiv_words
                    similarity = len(common) / max(len(paper_words), 1)

                    if similarity > 0.5 and arxiv_paper.authors:
                        # Update authors
                        author_str = ", ".join(arxiv_paper.authors[:5])
                        if len(arxiv_paper.authors) > 5:
                            author_str += " et al."
                        paper['authors'] = author_str

                        # Also update other fields if missing
                        if not paper.get('venue') or paper.get('venue', '').lower() in BAD_AUTHORS:
                            paper['venue'] = f"arXiv:{arxiv_paper.arxiv_id}"

                        enriched_count += 1
                        logger.debug(f"[arXiv] ✓ Found authors: {author_str[:50]}...")

            except Exception as e:
                logger.warning(f"[arXiv] Failed to look up '{title[:40]}...': {e}")

    logger.info(f"[QA] Enriched {enriched_count} papers with arXiv author data")
    return papers
