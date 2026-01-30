"""
Main pipeline orchestration for book generation.

This module coordinates all stages of book generation from
outline creation to final PDF assembly.
"""

import os
import json
import logging
from typing import Optional

import synalinks

from .config import Config
from .models import Topic, IntroductionInput, BookIntroduction
from .utils import (
    build_outline_string,
    build_outline_text,
    output_exists,
    load_json_from_file,
    save_to_file,
    save_json_to_file,
    get_chapter_names,
)
from .outline import build_outline_pipeline, reorganize_outline
from .planning import run_hierarchical_planning
from .content import generate_all_subsections, rewrite_sections
from .polish import polish_chapters
from .cover import generate_cover
from .pdf import generate_pdf
from .authors import get_author_profile, style_all_chapters, generate_about_author
from .illustrations import illustrate_all_chapters

logger = logging.getLogger(__name__)


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


async def generate_book(config: Config) -> str:
    """
    Generate a complete book from the given configuration.

    This is the main entry point that coordinates all pipeline stages:
    1. Outline generation
    2. Outline reorganization
    3. Hierarchical planning
    4. Subsection content generation
    5. Section rewriting
    6. Chapter polishing
    7. Cover generation
    8. PDF assembly

    Args:
        config: The book generation configuration

    Returns:
        Path to the generated PDF
    """
    # Setup output directory
    base_path = os.path.dirname(os.path.dirname(__file__))
    output_dir = config.setup_output_dir(base_path)

    # Shuffle introduction styles for variety
    config.shuffle_intro_styles()

    # Get topic data
    topic_data = config.get_topic_data()

    # Log configuration
    if config.test_mode:
        logger.info("=== TEST MODE ENABLED ===")
        logger.info(f"Max chapters: {config.test_max_chapters}")
        save_to_file(output_dir, "00_test_mode.txt", f"TEST MODE\nMax chapters: {config.test_max_chapters}")

    save_to_file(
        output_dir,
        "00_topic.txt",
        f"Topic: {topic_data['topic']}\nGoal: {topic_data['goal']}\nBook Name: {topic_data['book_name']}"
    )

    # Initialize language model
    language_model = synalinks.LanguageModel(model=config.model_name)

    # ==========================================================================
    # STAGE 1: OUTLINE GENERATION
    # ==========================================================================
    logger.info("Starting outline generation...")

    results = None
    if config.resume_from_dir and output_exists(output_dir, "01_outline.json"):
        results = load_json_from_file(output_dir, "01_outline.json")
        if results:
            logger.info("Loaded existing outline from file")

    if results is None:
        outline_program = await build_outline_pipeline(language_model)
        topic_input = Topic(
            topic=topic_data["topic"],
            goal=topic_data["goal"],
            book_name=topic_data["book_name"]
        )
        results = await outline_program(topic_input)

        # Save outline
        save_json_to_file(output_dir, "01_outline.json", results.get_json())
        results = results.get_json()

    save_to_file(output_dir, "01_outline.txt", build_outline_text(results))

    # Display outline
    concepts_list = results.get("concepts", [])
    print(f"\n{'='*60}")
    print(f"Generated {len(concepts_list)} main concepts (3-level hierarchy):")
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
    # STAGE 1b: OUTLINE REORGANIZATION
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
        results, was_reorganized, reorg_reasoning = await reorganize_outline(
            topic_data, results, language_model
        )
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
    # STAGE 2: HIERARCHICAL PLANNING
    # ==========================================================================
    logger.info("Starting hierarchical planning...")

    max_chapters = config.test_max_chapters if config.test_mode else None

    book_plan, chapters_overview, chapter_plans, all_section_plans, hierarchy = await run_hierarchical_planning(
        topic_data, results, language_model, output_dir, max_chapters
    )

    print(f"\n{'='*60}")
    print("Hierarchical planning complete:")
    print(f"  - Book plan: {'generated' if book_plan else 'failed'}")
    print(f"  - Chapters overview: {'generated' if chapters_overview else 'failed'}")
    print(f"  - Chapter plans: {len(chapter_plans.get('chapter_plans', [])) if chapter_plans else 0}")
    print(f"  - Section plans: {len(all_section_plans)} chapters")
    print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 3: SUBSECTION GENERATION
    # ==========================================================================
    logger.info("Generating subsections with hierarchical context...")

    all_generated = await generate_all_subsections(
        topic_data, book_plan, chapter_plans, all_section_plans, hierarchy,
        language_model, output_dir, max_chapters
    )

    total_subsections = sum(
        len(subs) for sections in all_generated.values() for subs in sections.values()
    )
    print(f"\n{'='*60}")
    print(f"Generated content for {total_subsections} subsections")
    print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 4: SECTION REWRITING
    # ==========================================================================
    logger.info("Rewriting subsections into coherent sections...")

    rewritten_chapters = await rewrite_sections(
        topic_data, all_generated, book_plan, chapters_overview, chapter_plans,
        all_section_plans, language_model, output_dir, config.intro_styles
    )

    print(f"\n{'='*60}")
    print(f"Rewritten {len(rewritten_chapters)} chapters")
    print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 5: CHAPTER POLISHING
    # ==========================================================================
    logger.info("Polishing chapters for final cohesion and flow...")

    polished_chapters = await polish_chapters(
        topic_data, rewritten_chapters, book_plan, chapters_overview, chapter_plans,
        language_model, output_dir
    )

    print(f"\n{'='*60}")
    print(f"Polished {len(polished_chapters)} chapters")
    print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 5b: AUTHOR STYLE APPLICATION (Optional)
    # ==========================================================================
    final_chapters = polished_chapters
    writing_style = None
    about_author = ""

    if config.author_key:
        writing_style = get_author_profile(config.author_key)
        if writing_style:
            logger.info(f"Applying writing style: {writing_style.key}")

            final_chapters = await style_all_chapters(
                polished_chapters, writing_style, language_model, output_dir
            )

            print(f"\n{'='*60}")
            print(f"Applied '{writing_style.key}' style to {len(final_chapters)} chapters")
            print(f"{'='*60}\n")

            # Generate About the Author section (only if style has a name)
            if writing_style.name:
                about_author = await generate_about_author(
                    writing_style,
                    topic_data["book_name"],
                    topic_data["topic"],
                    language_model,
                    output_dir
                )
                print(f"Generated About the Author section")
        else:
            logger.warning(f"Writing style not found: {config.author_key}")

    # ==========================================================================
    # STAGE 5c: ILLUSTRATION GENERATION (Optional)
    # ==========================================================================
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
        topic_data, book_plan, build_outline_text(results),
        language_model, output_dir
    )

    print(f"\n{'='*60}")
    print("Generated book introduction")
    print(f"{'='*60}\n")

    # ==========================================================================
    # STAGE 7: COVER GENERATION
    # ==========================================================================
    logger.info("Generating book cover...")

    # Use style's name for author display if configured
    display_authors = config.authors
    if writing_style and writing_style.name:
        display_authors = writing_style.name

    cover_path = os.path.join(output_dir, "book_cover.png")
    generate_cover(
        topic_data["book_name"],
        config.subtitle,
        display_authors,
        cover_path
    )

    # ==========================================================================
    # STAGE 8: FINAL ASSEMBLY & PDF
    # ==========================================================================
    logger.info("Assembling final book...")

    # Build the book content
    combined_output = []

    # Add About the Author section (before TOC)
    if about_author:
        combined_output.append("## About the Author\n\n")
        combined_output.append(f"{about_author}\n\n")
        combined_output.append("---\n\n")

    # Add Table of Contents
    combined_output.append('<div class="toc">\n\n')
    combined_output.append("<h2>Table of Contents</h2>\n\n")
    combined_output.append(build_outline_string(results))
    combined_output.append("\n</div>\n\n")

    # Add introduction
    if introduction:
        combined_output.append("## Introduction\n\n")
        combined_output.append(f"{introduction}\n\n")

    # Add chapters
    for chapter_title, chapter_content in final_chapters:
        if chapter_content:
            combined_output.append(f"{chapter_content.get('chapter_content', '')}\n\n")
        else:
            combined_output.append(f"## {chapter_title}\n\n")
            combined_output.append("*Content generation failed for this chapter*\n\n")

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
