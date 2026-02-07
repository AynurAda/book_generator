"""
Main pipeline orchestration for book generation.

This module coordinates all stages of book generation from
outline creation to final PDF assembly.
"""

import os
import json
import logging
import subprocess
import tempfile
from typing import Optional

import yaml
import synalinks

from .config import Config
from .models import Topic, IntroductionInput, BookIntroduction
from .utils import (
    build_outline_string,
    build_outline_text,
    build_outline_text_short,
    output_exists,
    load_json_from_file,
    save_to_file,
    save_json_to_file,
    get_chapter_names,
)
from .outline import (
    build_outline_pipeline,
    reorganize_outline,
    generate_outline_with_coverage,
    outline_needs_subsubconcepts,
    generate_subsubconcepts,
    prioritize_chapters,
    generate_research_informed_outline,
    convert_research_outline_to_hierarchy,
)
from .planning import run_hierarchical_planning
from .vision import generate_book_vision, format_book_vision
from .content import write_all_sections_direct
from .cover import generate_cover
from .pdf import generate_pdf
from .authors import get_author_profile, generate_about_author
from .illustrations import illustrate_all_chapters
from .citations import run_citation_pipeline, CitationManager
from .research import (
    DeepResearchClient,
    generate_research_queries,
    parse_research,
    ResearchManager,
    run_stage2_research,
    Stage2MCPPipeline,
    Stage2ArxivFallback,
)

logger = logging.getLogger(__name__)


class PaperMatchInput(synalinks.DataModel):
    """Input for paper matching Decision."""
    query_title: str = synalinks.Field(description="The paper title to match")


async def match_paper_title_to_dict(
    query_title: str,
    all_papers: list,
    language_model,
) -> Optional[dict]:
    """
    Use synalinks.Decision to match a paper title to a full paper dict.

    Args:
        query_title: The paper title from the outline (may include year)
        all_papers: List of paper dicts from research
        language_model: The LLM to use for matching

    Returns:
        The matched paper dict, or None if no match found
    """
    if not all_papers:
        return None

    # Build labels from paper titles
    labels = [p.get("title", f"Paper {i+1}") for i, p in enumerate(all_papers)]

    # Format papers list for the prompt
    papers_text = "\n".join(
        f"  {i+1}. {p.get('title', 'Unknown')} ({p.get('year', 'N/A')})"
        for i, p in enumerate(all_papers)
    )

    match_input = PaperMatchInput(query_title=query_title)

    try:
        decision = await synalinks.Decision(
            question=f"""Which paper from the research database matches this title?

QUERY TITLE: "{query_title}"

AVAILABLE PAPERS:
{papers_text}

Select the paper that best matches the query title. The query may include a year suffix like "(2024)" that should help identify the correct paper.""",
            labels=labels,
            language_model=language_model,
            temperature=1.0,
        )(match_input)

        if decision is None:
            logger.debug(f"    Paper decision returned None for '{query_title[:40]}...'")
            return None

        decision_json = decision.get_json()
        selected_label = decision_json.get("choice")

        if selected_label:
            for i, label in enumerate(labels):
                if label == selected_label:
                    logger.info(f"    Matched: '{query_title[:30]}...' → '{selected_label[:30]}...'")
                    return all_papers[i]
        else:
            logger.debug(f"    Paper decision has no 'choice': {decision_json}")
    except Exception as e:
        logger.error(f"Paper matching failed for '{query_title[:40]}...': {e}")

    return None


def outline_to_editable_yaml(results: dict) -> str:
    """Convert outline to a simple YAML format for editing.

    Format:
    - Chapter Name:
        - Section 1
        - Section 2
    """
    lines = ["# Edit this outline. Delete lines to remove, add new lines to add."]
    lines.append("# Format: '- Chapter:' followed by indented '  - Section' lines")
    lines.append("# Subsubconcepts are auto-generated, you only edit chapters and sections.")
    lines.append("")

    for concept_data in results.get("concepts", []):
        concept_name = concept_data.get("concept", "Unknown")
        lines.append(f"- {concept_name}:")
        for subconcept_data in concept_data.get("subconcepts", []):
            subconcept_name = subconcept_data.get("subconcept", "Unknown")
            lines.append(f"    - {subconcept_name}")
        lines.append("")

    return "\n".join(lines)


def parse_edited_yaml(content: str) -> dict:
    """Parse edited YAML back to outline format.

    Returns dict in DeepHierarchy format.
    """
    concepts = []
    current_concept = None

    for line in content.split("\n"):
        line = line.rstrip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue

        # Check for chapter (concept) line: "- Chapter Name:"
        if line.startswith("- ") and line.endswith(":"):
            if current_concept:
                concepts.append(current_concept)
            concept_name = line[2:-1].strip()
            current_concept = {
                "concept": concept_name,
                "subconcepts": []
            }
        # Check for section (subconcept) line: "    - Section Name"
        elif line.strip().startswith("- ") and current_concept:
            subconcept_name = line.strip()[2:].strip()
            current_concept["subconcepts"].append({
                "subconcept": subconcept_name,
                "subsubconcepts": []
            })

    # Don't forget the last concept
    if current_concept:
        concepts.append(current_concept)

    return {"concepts": concepts}


def edit_outline_interactive(results: dict, output_dir: str) -> dict:
    """Open outline in editor for user to modify.

    Returns the edited outline dict.
    """
    # Convert to editable format
    editable_content = outline_to_editable_yaml(results)

    # Create temp file
    edit_file = os.path.join(output_dir, "01_outline_edit.yaml")
    with open(edit_file, "w") as f:
        f.write(editable_content)

    # Get editor from environment
    editor = os.environ.get("EDITOR", "nano")

    print(f"\nOpening outline in {editor}...")
    print("Edit the outline, save, and close the editor to continue.")
    print(f"File: {edit_file}\n")

    # Open editor
    try:
        subprocess.run([editor, edit_file], check=True)
    except FileNotFoundError:
        # Try common editors
        for alt_editor in ["nano", "vim", "vi"]:
            try:
                subprocess.run([alt_editor, edit_file], check=True)
                break
            except FileNotFoundError:
                continue
        else:
            print(f"ERROR: Could not find an editor. Please edit {edit_file} manually and press Enter.")
            input("Press Enter when done editing...")

    # Read edited content
    with open(edit_file, "r") as f:
        edited_content = f.read()

    # Parse back to outline format
    edited_results = parse_edited_yaml(edited_content)

    # Validate
    if not edited_results.get("concepts"):
        print("WARNING: No valid chapters found in edited outline. Keeping original.")
        return results

    return edited_results


async def generate_introduction(
    topic_data: dict,
    book_plan: dict,
    outline_text: str,
    language_model,
    output_dir: str
) -> str:
    """
    Generate the book introduction.

    Returns:
        The introduction content as a string
    """
    intro_filename = "00_introduction.txt"

    # Check for existing introduction
    if output_dir and output_exists(output_dir, intro_filename):
        existing = load_json_from_file(output_dir, intro_filename.replace('.txt', '.json'))
        if existing:
            logger.info("Loaded existing introduction")
            return existing.get("introduction", "")

    logger.info("Generating book introduction...")

    from .planning import format_book_plan

    generator = synalinks.Generator(
        data_model=BookIntroduction,
        language_model=language_model,
        temperature=1.0,
        instructions="""Write a compelling introduction for this book.

TARGET AUDIENCE: Tailor the introduction specifically for the specified audience.
- Address their background and expected knowledge level
- Speak to their motivations and goals
- Use language appropriate to their expertise

LANGUAGE STYLE: Write in an ACCESSIBLE yet RIGOROUS style:
- Welcoming to readers new to the topic
- Clear about what they will learn and why it matters
- Intellectually honest about the complexity of the subject

The introduction should:
1. HOOK: Open with a compelling observation about the field
2. CONTEXT: Explain why this topic matters now
3. PROBLEM: Describe the challenges or questions the book addresses
4. APPROACH: Briefly explain the book's approach and methodology
5. ROADMAP: Give a high-level overview of what each major section covers
6. AUDIENCE: Indicate who will benefit most from this book
7. INVITATION: End with an encouraging note to the reader

Write 4-6 paragraphs. Do NOT use headers within the introduction - write in flowing prose.
The introduction will be placed after the Table of Contents."""
    )

    input_data = IntroductionInput(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        book_name=topic_data["book_name"],
        audience=topic_data.get("audience", "technical readers"),
        book_plan=format_book_plan(book_plan),
        outline=outline_text
    )

    result = await generator(input_data)
    result_dict = result.get_json()
    introduction = result_dict.get("introduction", "")

    # Save the introduction
    if output_dir:
        save_to_file(output_dir, intro_filename, introduction)
        save_json_to_file(output_dir, intro_filename.replace('.txt', '.json'), result_dict)

    return introduction


async def generate_book(config: Config, progress_callback=None) -> str:
    """
    Generate a complete book from the given configuration.

    This is the main entry point that coordinates all pipeline stages:
    1. Outline generation & reorganization
    2. Hierarchical planning (book → chapters → sections)
    3. Direct write (with optional style applied inline)
    4. Illustrations (optional)
    5. Introduction generation
    6. Cover generation
    7. Final assembly & PDF

    Args:
        config: The book generation configuration
        progress_callback: Optional async callback(stage, progress, message)
            for reporting progress to callers (e.g. API server).

    Returns:
        Path to the generated PDF
    """
    async def report_progress(stage: str, progress: int, message: str):
        if progress_callback:
            await progress_callback(stage, progress, message)
    # Setup output directory
    base_path = os.path.dirname(os.path.dirname(__file__))
    output_dir = config.setup_output_dir(base_path)

    # Shuffle introduction styles for variety
    config.shuffle_intro_styles()

    # Get topic data
    topic_data = config.get_topic_data()

    # Log configuration
    if config.num_chapters:
        logger.info(f"=== LIMITED TO {config.num_chapters} CHAPTERS ===")
        save_to_file(output_dir, "00_chapter_limit.txt", f"Chapter limit: {config.num_chapters}")

    save_to_file(
        output_dir,
        "00_topic.txt",
        f"Topic: {topic_data['topic']}\nGoal: {topic_data['goal']}\nBook Name: {topic_data['book_name']}"
    )

    # Initialize language model
    language_model = synalinks.LanguageModel(model=config.model_name)

    # ==========================================================================
    # STAGE -1: DEEP RESEARCH (optional, for cutting-edge content)
    # ==========================================================================
    research_manager = None

    if config.enable_research:
        logger.info("Starting deep research phase...")

        research_dir = os.path.join(output_dir, "00_research")
        os.makedirs(research_dir, exist_ok=True)

        # Check for cached parsed knowledge first (fastest resume path)
        cached_knowledge_file = os.path.join(research_dir, "field_knowledge.json")
        cached_queries_file = os.path.join(research_dir, "queries.json")

        if config.research_cache and os.path.exists(cached_knowledge_file):
            # Full cache hit - load parsed knowledge directly
            logger.info("Loading cached research knowledge...")
            from .research.models import FieldKnowledge
            cached_data = load_json_from_file(research_dir, "field_knowledge.json")
            if cached_data:
                field_knowledge = FieldKnowledge(**cached_data)
                research_manager = ResearchManager(field_knowledge, language_model=language_model)

                print(f"\n{'='*60}")
                print("DEEP RESEARCH (CACHED)")
                print(f"{'='*60}")
                print(f"  Papers: {len(field_knowledge.papers)}")
                print(f"  Frameworks: {len(field_knowledge.frameworks)}")
                print(f"  Themes: {len(field_knowledge.themes)}")
                print(f"{'='*60}\n")

        if research_manager is None:
            # Check for cached queries (partial resume)
            queries = None
            if config.research_cache and os.path.exists(cached_queries_file):
                cached_queries = load_json_from_file(research_dir, "queries.json")
                if cached_queries and "queries" in cached_queries:
                    queries = cached_queries["queries"]
                    logger.info(f"Loaded {len(queries)} cached queries")

            # Generate queries if not cached
            if not queries:
                logger.info("Generating research queries...")
                queries = await generate_research_queries(
                    topic=topic_data["topic"],
                    goal=topic_data["goal"],
                    audience=topic_data.get("audience", "technical readers"),
                    language_model=language_model,
                )
                save_json_to_file(research_dir, "queries.json", {"queries": queries})

            print(f"\n{'='*60}")
            print("RESEARCH QUERIES")
            print(f"{'='*60}")
            for i, q in enumerate(queries, 1):
                print(f"  {i}. {q[:80]}...")
            print(f"{'='*60}\n")

            # Check which queries already have cached results
            queries_to_run = queries[:config.research_max_queries]
            cached_count = 0
            for i in range(len(queries_to_run)):
                cache_file = os.path.join(research_dir, f"research_query_{i}.txt")
                if os.path.exists(cache_file):
                    cached_count += 1

            if cached_count > 0:
                print(f"Found {cached_count}/{len(queries_to_run)} cached query results")

            # Run deep research (client handles per-query caching)
            if cached_count < len(queries_to_run):
                logger.info(f"Running {len(queries_to_run) - cached_count} deep research queries...")
                print("Running deep research (this may take several minutes)...")
            else:
                logger.info("All queries cached, loading results...")

            client = DeepResearchClient()
            raw_results = await client.research_all(
                queries_to_run,
                cache_dir=research_dir if config.research_cache else None,
            )

            # Save raw results
            save_json_to_file(research_dir, "raw_results.json", raw_results)

            # Parse into structured data
            logger.info("Parsing research into structured data...")
            field_knowledge = await parse_research(raw_results, language_model)

            # Save parsed knowledge
            save_json_to_file(research_dir, "field_knowledge.json", field_knowledge.get_json())

            # Create manager with language model for LLM-based matching
            research_manager = ResearchManager(field_knowledge, language_model=language_model)

            print(f"\n{'='*60}")
            print("DEEP RESEARCH COMPLETE")
            print(f"{'='*60}")
            print(f"  Papers discovered: {len(field_knowledge.papers)}")
            print(f"  Frameworks found: {len(field_knowledge.frameworks)}")
            print(f"  Themes identified: {len(field_knowledge.themes)}")
            print(f"  Open problems: {len(field_knowledge.open_problems)}")
            print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 0: BOOK VISION (guides all subsequent generation)
    # ==========================================================================
    await report_progress("generating_vision", 5, "Crafting the book's core thesis and themes...")
    logger.info("Generating book vision...")

    # Get research context for vision if available
    vision_research_context = None
    if research_manager:
        vision_research_context = research_manager.for_vision()
        if vision_research_context:
            logger.info(f"Research context for vision: {len(vision_research_context)} chars")

    book_vision = await generate_book_vision(
        topic_data, language_model, output_dir,
        research_context=vision_research_context,
        reader_mode_override=config.reader_mode_override,
    )

    # Display vision summary
    print(f"\n{'='*60}")
    print("BOOK VISION")
    print(f"{'='*60}")
    print(f"\nCore Thesis: {book_vision.get('core_thesis', 'N/A')[:200]}...")
    print(f"\nKey Themes:")
    for theme in book_vision.get('key_themes', []):
        print(f"  - {theme}")
    print(f"\nScope Boundaries: {book_vision.get('scope_boundaries', 'N/A')[:150]}...")
    print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 1: OUTLINE GENERATION (vision-guided)
    # ==========================================================================
    await report_progress("generating_outline", 10, "Designing chapter structure for your domain...")
    logger.info("Starting vision-guided outline generation...")

    results = None

    # Check for default outline in config first
    if config.default_outline:
        results = config.default_outline
        logger.info("Using default outline from config")
        save_json_to_file(output_dir, "01_outline.json", results)
    elif config.resume_from_dir and output_exists(output_dir, "01_outline.json"):
        results = load_json_from_file(output_dir, "01_outline.json")
        if results:
            logger.info("Loaded existing outline from file")

    if results is None:
        # Use coverage-checked generation WITH vision guidance
        outline_research_context = None
        if research_manager:
            outline_research_context = research_manager.for_outline()
            if outline_research_context:
                logger.info(f"Research context for outline: {len(outline_research_context)} chars")

        results = await generate_outline_with_coverage(
            topic_data, language_model, book_vision=book_vision,
            research_context=outline_research_context
        )

        # Save outline
        save_json_to_file(output_dir, "01_outline.json", results)

    save_to_file(output_dir, "01_outline.txt", build_outline_text(results))

    # Display outline
    concepts_list = results.get("concepts", [])
    outline_source = "default" if config.default_outline else "generated"
    print(f"\n{'='*60}")
    print(f"Outline ({outline_source}): {len(concepts_list)} main concepts")
    print(f"{'='*60}\n")

    for i, concept_data in enumerate(concepts_list, 1):
        concept_name = concept_data.get("concept", "Unknown")
        subconcepts = concept_data.get("subconcepts", [])
        print(f"{i}. {concept_name}")
        for j, subconcept_data in enumerate(subconcepts, 1):
            subconcept_name = subconcept_data.get("subconcept", "Unknown")
            print(f"   {i}.{j} {subconcept_name}")
        print()

    # ==========================================================================
    # STAGE 1b: RESEARCH-INFORMED OUTLINE (replaces initial with research-based structure)
    # ==========================================================================
    # The initial outline was just LLM's mental model for generating research queries.
    # After research, we generate a NEW outline based on what research discovered.
    chapter_paper_assignments = {}  # chapter_name -> list of paper titles

    if research_manager and config.enable_research:
        print(f"\n{'='*60}")
        print("Generating research-informed outline...")
        print(f"{'='*60}\n")

        research_outline = await generate_research_informed_outline(
            topic_data=topic_data,
            book_vision=book_vision,
            research_manager=research_manager,
            initial_outline=results,
            language_model=language_model,
            output_dir=output_dir,
        )

        # Use the research-informed outline if generation succeeded
        if research_outline and research_outline.get("chapters"):
            # Convert research-informed outline to DeepHierarchy format
            # This replaces the initial outline with the research-informed structure
            converted_outline = convert_research_outline_to_hierarchy(research_outline)

            # Only replace if we got valid chapters
            if converted_outline.get("concepts"):
                old_chapter_count = len(results.get("concepts", []))
                results = converted_outline
                logger.info(f"Replaced initial outline ({old_chapter_count} chapters) with research-informed outline ({len(results.get('concepts', []))} chapters)")

                # Save the converted outline
                save_json_to_file(output_dir, "01_outline.json", results)
                save_to_file(output_dir, "01_outline.txt", build_outline_text(results))

                # Extract paper assignments from the research-informed outline
                for chapter in research_outline.get("chapters", []):
                    chapter_name = chapter.get("chapter_name", "")
                    papers = chapter.get("relevant_papers", [])
                    if chapter_name and papers:
                        chapter_paper_assignments[chapter_name] = papers

                print(f"Research-informed outline applied:")
                print(f"  - Chapters: {len(results.get('concepts', []))}")
                print(f"  - Organization: {research_outline.get('organization_logic', 'N/A')}")
                print(f"\nChapters:")
                for i, concept in enumerate(results.get("concepts", []), 1):
                    ch_name = concept.get("concept", "Unknown")
                    paper_count = len(chapter_paper_assignments.get(ch_name, []))
                    print(f"  {i}. {ch_name} ({paper_count} papers)")
            else:
                logger.warning("Research-informed outline conversion failed, keeping initial outline")
        else:
            logger.warning("Research-informed outline failed, using initial outline")

    # ==========================================================================
    # STAGE 1c: OUTLINE REORGANIZATION (before prioritization for best flow)
    # ==========================================================================
    was_reorganized = False
    reorg_reasoning = "Not analyzed"

    if config.resume_from_dir and output_exists(output_dir, "01_outline_reorganized.json"):
        reorganized = load_json_from_file(output_dir, "01_outline_reorganized.json")
        if reorganized:
            results = reorganized
            was_reorganized = True
            reorg_reasoning = "Loaded from file"
            logger.info("Loaded existing reorganized outline")

    if not was_reorganized:
        results, was_reorganized, reorg_reasoning, reorg_analysis = await reorganize_outline(
            topic_data, results, language_model
        )
        # Always save the reorganization analysis (includes thinking)
        save_json_to_file(output_dir, "01_reorganization_analysis.json", reorg_analysis)
        if was_reorganized:
            save_json_to_file(output_dir, "01_outline_reorganized.json", results)
            save_to_file(output_dir, "01_outline_reorganized.txt", build_outline_text(results))

    print(f"\n{'='*60}")
    if was_reorganized:
        print("Outline REORGANIZED for better conceptual flow:")
        print(f"Reason: {reorg_reasoning}")
        print("\nNew chapter order:")
        for i, concept_data in enumerate(results.get("concepts", []), 1):
            print(f"  {i}. {concept_data.get('concept', 'Unknown')}")
    else:
        print("Outline order KEPT as-is:")
        print(f"Reason: {reorg_reasoning}")
    print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 1d: CHAPTER PRIORITIZATION (after reorganization, before planning)
    # ==========================================================================
    if config.num_chapters and len(results.get("concepts", [])) > config.num_chapters:
        print(f"\n{'='*60}")
        print(f"Selecting {config.num_chapters} most important chapters...")
        if config.focus:
            print(f"Focus: {config.focus}")
        print(f"{'='*60}\n")

        results = await prioritize_chapters(
            topic_data,
            results,
            config.num_chapters,
            config.focus,
            language_model
        )

        # Save prioritized outline
        save_json_to_file(output_dir, "01_outline_prioritized.json", results)
        save_to_file(output_dir, "01_outline_prioritized.txt", build_outline_text(results))

        # Display selected chapters
        concepts_list = results.get("concepts", [])
        print(f"Selected {len(concepts_list)} chapters:")
        for i, concept_data in enumerate(concepts_list, 1):
            concept_name = concept_data.get("concept", "Unknown")
            print(f"  {i}. {concept_name}")
        print()

    # ==========================================================================
    # STAGE 1e: GENERATE SUBSUBCONCEPTS IF MISSING (only for selected chapters)
    # ==========================================================================
    if outline_needs_subsubconcepts(results):
        logger.info("Outline missing subsubconcepts, generating...")
        print(f"\n{'='*60}")
        print("Generating detailed subsections for each section...")
        print(f"{'='*60}\n")

        results = await generate_subsubconcepts(topic_data, results, language_model)
        save_json_to_file(output_dir, "01_outline_final.json", results)
        save_to_file(output_dir, "01_outline_final.txt", build_outline_text(results))

        # Count subsubconcepts
        total_subsections = sum(
            len(sub.get("subsubconcepts", []))
            for concept in results.get("concepts", [])
            for sub in concept.get("subconcepts", [])
        )
        print(f"Generated {total_subsections} subsections across all sections")

    # ==========================================================================
    # STAGE 2: HIERARCHICAL PLANNING
    # ==========================================================================
    await report_progress("planning", 25, "Creating detailed plans for each chapter...")
    logger.info("Starting hierarchical planning...")
    if config.plan_critique_enabled:
        logger.info(f"Plan critique enabled (max {config.plan_critique_max_attempts} attempts)")

    max_chapters = config.num_chapters

    book_plan, chapters_overview, chapter_plans, all_section_plans, hierarchy = await run_hierarchical_planning(
        topic_data, results, language_model, output_dir, max_chapters,
        critique_enabled=config.plan_critique_enabled,
        critique_max_attempts=config.plan_critique_max_attempts,
        book_vision=book_vision,
        research_manager=research_manager,
        chapter_paper_assignments=chapter_paper_assignments,
    )

    print(f"\n{'='*60}")
    print("Hierarchical planning complete:")
    print(f"  - Book plan: {'generated' if book_plan else 'failed'}")
    print(f"  - Chapters overview: {'generated' if chapters_overview else 'failed'}")
    print(f"  - Chapter plans: {len(chapter_plans.get('chapter_plans', [])) if chapter_plans else 0}")
    print(f"  - Section plans: {len(all_section_plans)} chapters")
    print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 2b: CLAIM-FIRST CITATION PIPELINE (Optional)
    # ==========================================================================
    citation_manager = None
    get_citation_instructions_callback = None

    if config.enable_citations:
        logger.info("Starting claim-first citation pipeline...")
        logger.info("This will plan claims for each subsection, then verify them.")

        from .planning import format_book_plan

        try:
            citation_manager = await run_citation_pipeline(
                topic_data=topic_data,
                hierarchy=hierarchy,
                book_plan=format_book_plan(book_plan),
                section_plans=all_section_plans,
                output_dir=output_dir,
                language_model=language_model,
                confidence_threshold=config.citation_confidence_threshold,
                skip_low_importance=config.skip_low_importance_claims,
                max_concurrent_verifications=5,
            )

            # Create callback for content generation (subsection-level)
            def get_citation_instructions_callback(chapter: str, section: str, subsection: str = None) -> str:
                if citation_manager:
                    if subsection:
                        return citation_manager.get_subsection_citation_instructions(chapter, section, subsection)
                    return citation_manager.get_citation_instructions(chapter, section)
                return ""

            print(f"\n{'='*60}")
            print("CLAIM-FIRST CITATION PIPELINE COMPLETE:")
            print(f"  - Claims planned: {len(citation_manager.claims)}")
            print(f"  - Claims verified: {len(citation_manager.verified_citations)}")
            print(f"  - Unverified claims: {len(citation_manager.unverified_claims)}")
            print(f"  - Unique references: {len(citation_manager.get_all_references())}")
            verification_rate = len(citation_manager.verified_citations) / len(citation_manager.claims) * 100 if citation_manager.claims else 0
            print(f"  - Verification rate: {verification_rate:.1f}%")
            print(f"{'='*60}\n")

        except Exception as e:
            logger.error(f"Citation pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            logger.info("Continuing without citation verification")
            print(f"\n{'='*60}")
            print(f"WARNING: Citation pipeline failed: {e}")
            print("Continuing without citation verification...")
            print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 2c: KNOWLEDGE GRAPH RESEARCH (Optional - requires mcp-graphiti)
    # ==========================================================================
    stage2_pipeline = None

    if config.enable_stage2_research and research_manager:
        logger.info("Starting Stage 2 research with knowledge graph...")
        logger.info("This requires mcp-graphiti Docker container running.")

        try:
            stage2_pipeline = await run_stage2_research(
                config=config,
                research_manager=research_manager,
                language_model=language_model,
            )

            if stage2_pipeline:
                print(f"\n{'='*60}")
                print("STAGE 2 KNOWLEDGE GRAPH RESEARCH COMPLETE:")
                print(f"  - Connected to: {config.graphiti_mcp_url}")
                print(f"  - Group ID: {config.graphiti_group_id}")
                print(f"  - Papers processed: {len(research_manager.get_all_papers())}")
                print(f"{'='*60}\n")
            else:
                print(f"\n{'='*60}")
                print("STAGE 2 RESEARCH SKIPPED:")
                print("  mcp-graphiti not available - using arXiv data only")
                print(f"{'='*60}\n")

        except Exception as e:
            logger.warning(f"Stage 2 research failed: {e}")
            logger.info("Continuing without knowledge graph - using arXiv data only")
            print(f"\n{'='*60}")
            print(f"WARNING: Stage 2 research failed: {e}")
            print("Continuing with Stage 1 research only...")
            print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 3: CONTENT GENERATION (Direct Write with Style)
    # ==========================================================================
    await report_progress("writing_content", 40, "Synthesizing content tailored to your background...")

    # Get writing style if configured (applied during direct write, not as separate pass)
    writing_style = None
    about_author = ""

    if config.author_key:
        writing_style = get_author_profile(config.author_key)
        if writing_style:
            logger.info(f"Writing with style: {writing_style.key}")
        else:
            logger.warning(f"Writing style not found: {config.author_key}")

    logger.info("Writing sections directly from topic names...")

    # Create research context callback for content generation
    # Uses Stage 2 pipeline if available, otherwise falls back to ResearchManager
    # Now also filters by chapter paper assignments
    get_research_context_callback = None
    _chapter_paper_assignments = chapter_paper_assignments  # Capture for closure

    if stage2_pipeline and stage2_pipeline.connected:
        logger.info("Stage 2 knowledge graph context enabled for content generation")
        logger.info("Using LLM-generated smart queries for section context")
        if _chapter_paper_assignments:
            logger.info(f"Chapter paper assignments available for {len(_chapter_paper_assignments)} chapters")

        # Capture context needed for smart query generation
        _section_plans = all_section_plans
        _book_topic = topic_data["topic"]
        _language_model = language_model

        async def get_research_context_callback(chapter: str, section: str) -> str:
            """Get research context from Stage 2 knowledge graph using smart queries (async).

            Uses Synalinks to generate targeted search queries based on section plan,
            instead of naive keyword extraction.
            """
            # Look up section plan for this section
            section_plan = ""
            chapter_plans = _section_plans.get(chapter, {})
            section_plan_list = chapter_plans.get("section_plans", [])

            # Find matching section plan (by position or name match)
            for plan in section_plan_list:
                if isinstance(plan, dict):
                    plan_section = plan.get("section_name", "")
                    if plan_section == section or section in plan_section:
                        from .planning import format_section_plan
                        section_plan = format_section_plan(plan)
                        break

            try:
                # Use smart query generation with full section context
                context = await stage2_pipeline.get_context_for_section(
                    chapter_name=chapter,
                    section_name=section,
                    section_plan=section_plan or f"Section about {section}",
                    book_topic=_book_topic,
                    language_model=_language_model,
                )
                if context:
                    return context
            except Exception as e:
                logger.warning(f"Stage 2 smart context retrieval failed: {e}")
                import traceback
                logger.debug(f"Traceback: {traceback.format_exc()}")

            # Fall back to ResearchManager with paper filtering
            if research_manager:
                # Strip number prefix (e.g., "1. ") from chapter name to match assignment keys
                import re
                base_chapter = re.sub(r'^\d+\.\s*', '', chapter)
                assigned_papers = _chapter_paper_assignments.get(base_chapter, [])
                return await research_manager.for_section_writing(chapter, section, assigned_papers=assigned_papers)
            return ""

    elif research_manager:
        logger.info("Research context enabled for content generation")
        if _chapter_paper_assignments:
            logger.info(f"Chapter paper assignments available for {len(_chapter_paper_assignments)} chapters")

        async def get_research_context_callback(chapter: str, section: str) -> str:
            # Strip number prefix (e.g., "1. ") from chapter name to match assignment keys
            import re
            base_chapter = re.sub(r'^\d+\.\s*', '', chapter)
            assigned_papers = _chapter_paper_assignments.get(base_chapter, [])
            return await research_manager.for_section_writing(chapter, section, assigned_papers=assigned_papers)

    # Build full paper dicts for fast chapter references (if enabled)
    # Uses synalinks.Decision to match paper titles to full paper dicts
    chapter_paper_dicts = None
    if config.enable_chapter_references and research_manager and _chapter_paper_assignments:
        logger.info("Building chapter reference lists using LLM matching...")
        chapter_paper_dicts = {}
        all_papers = research_manager.get_all_papers()

        for chapter_name, paper_titles in _chapter_paper_assignments.items():
            # Match paper titles to full paper dicts using synalinks.Decision
            matched_papers = []
            for title in paper_titles:
                matched_paper = await match_paper_title_to_dict(
                    query_title=title,
                    all_papers=all_papers,
                    language_model=language_model,
                )
                if matched_paper:
                    matched_papers.append(matched_paper)

            if matched_papers:
                chapter_paper_dicts[chapter_name] = matched_papers
                logger.info(f"  {chapter_name[:40]}...: {len(matched_papers)} references")

    chapters = await write_all_sections_direct(
        topic_data, hierarchy, book_plan, chapters_overview, chapter_plans,
        all_section_plans, language_model, output_dir, config.intro_styles,
        max_chapters, writing_style, get_citation_instructions_callback,
        get_research_context_callback, citation_manager, chapter_paper_dicts
    )

    total_sections = sum(len(sections) for sections in hierarchy.values())
    print(f"\n{'='*60}")
    print(f"Wrote {len(chapters)} chapters ({total_sections} sections)")
    if writing_style:
        print(f"(with '{writing_style.key}' style applied)")
    print(f"{'='*60}\n")

    # Generate About the Author section (only if style has a name)
    if writing_style and writing_style.name:
        about_author = await generate_about_author(
            writing_style,
            topic_data["book_name"],
            topic_data["topic"],
            language_model,
            output_dir
        )
        print(f"Generated About the Author section")

    final_chapters = chapters

    # ==========================================================================
    # STAGE 5c: ILLUSTRATION GENERATION (Optional)
    # ==========================================================================
    await report_progress("generating_illustrations", 75, "Creating diagrams and visualizations...")
    if config.enable_illustrations:
        logger.info("Adding illustrations to chapters...")

        final_chapters = await illustrate_all_chapters(
            final_chapters,
            topic_data["topic"],
            topic_data.get("audience", "technical readers"),
            language_model,
            output_dir,
            enable_images=config.enable_generated_images,
            image_model=config.image_model
        )

        print(f"\n{'='*60}")
        print(f"Illustrated {len(final_chapters)} chapters")
        if config.enable_generated_images:
            print(f"(with AI-generated images using {config.image_model})")
        else:
            print("(Mermaid diagrams only)")
        print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 6: INTRODUCTION GENERATION
    # ==========================================================================
    logger.info("Generating book introduction...")

    introduction = await generate_introduction(
        topic_data, book_plan, build_outline_text_short(results),
        language_model, output_dir
    )

    print(f"\n{'='*60}")
    print("Generated book introduction")
    print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 7: COVER GENERATION
    # ==========================================================================
    await report_progress("generating_cover", 85, "Designing your book cover...")
    logger.info("Generating book cover...")

    # Use style's name for author display if configured
    display_authors = config.authors
    if writing_style and writing_style.name:
        display_authors = writing_style.name

    # Get chapter names for cover prompt context
    chapter_names = [c.get("concept", "") for c in results.get("concepts", [])]
    key_concepts = "\n".join(f"- {name}" for name in chapter_names)

    cover_path = os.path.join(output_dir, "book_cover.png")
    await generate_cover(
        topic_data["book_name"],
        config.subtitle,
        display_authors,
        cover_path,
        style=config.cover_style,
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        audience=topic_data.get("audience", "technical readers"),
        key_concepts=key_concepts,
        language_model=language_model,
        image_model=config.image_model
    )

    # ==========================================================================
    # STAGE 8: FINAL ASSEMBLY & PDF
    # ==========================================================================
    await report_progress("assembling_pdf", 92, "Assembling the final PDF...")
    logger.info("Assembling final book...")

    # Build the book content
    combined_output = []

    # Add About the Author section (before TOC)
    if about_author:
        combined_output.append("# About the Author\n\n")
        combined_output.append(f"{about_author}\n\n")
        combined_output.append("---\n\n")

    # Add Table of Contents
    combined_output.append('<div class="toc">\n\n')
    combined_output.append("<h2>Table of Contents</h2>\n\n")
    combined_output.append(build_outline_string(results))
    combined_output.append("\n</div>\n\n")

    # Add introduction
    if introduction:
        combined_output.append("# Introduction\n\n")
        combined_output.append(f"{introduction}\n\n")

    # Add chapters
    for chapter_title, chapter_content in final_chapters:
        if chapter_content:
            combined_output.append(f"{chapter_content.get('chapter_content', '')}\n\n")
        else:
            combined_output.append(f"## {chapter_title}\n\n")
            combined_output.append("*Content generation failed for this chapter*\n\n")

    # Add bibliography if citations were enabled
    if citation_manager:
        bibliography = citation_manager.get_bibliography_markdown()
        if bibliography:
            combined_output.append("\n---\n\n")
            combined_output.append(bibliography)
            combined_output.append("\n")

    book_content = "".join(combined_output)
    save_to_file(output_dir, "06_full_book.txt", book_content)

    # Generate PDF
    pdf_path = os.path.join(output_dir, "06_full_book.pdf")
    generate_pdf(
        book_content,
        topic_data["book_name"],
        pdf_path,
        cover_path=cover_path if os.path.exists(cover_path) else None,
        base_url=output_dir
    )

    logger.info("Book generation complete!")
    logger.info(f"Text version: {os.path.join(output_dir, '06_full_book.txt')}")
    logger.info(f"PDF version: {pdf_path}")
    logger.info(f"Cover image: {cover_path}")

    return pdf_path
