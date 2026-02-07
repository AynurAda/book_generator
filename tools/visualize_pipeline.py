#!/usr/bin/env python3
"""
Visualize the Learner book generation pipeline using Synalinks.

This script creates a visual representation of the entire book generation
pipeline, showing the flow of data through each stage.
"""

import asyncio
import synalinks
from synalinks.utils import plot_program


# =============================================================================
# Stage 1: Structure - Concept Extraction & Outline
# =============================================================================

class TopicInput(synalinks.DataModel):
    """User's book request."""
    topic: str = synalinks.Field(description="The main topic of the book")
    goal: str = synalinks.Field(description="What the reader should achieve")
    audience: str = synalinks.Field(description="Target audience background")
    book_name: str = synalinks.Field(description="Title of the book")


class ExtractedConcepts(synalinks.DataModel):
    """Extracted concepts from multiple angles."""
    main_concepts: list[str] = synalinks.Field(description="Core concepts to cover")
    foundational_concepts: list[str] = synalinks.Field(description="Prerequisites")
    advanced_concepts: list[str] = synalinks.Field(description="Advanced topics")


class VerifiedOutline(synalinks.DataModel):
    """Outline after coverage verification."""
    chapters: list[str] = synalinks.Field(description="Ordered list of chapters")
    coverage_score: float = synalinks.Field(description="How well concepts are covered")
    approved: bool = synalinks.Field(description="User approval status")


# =============================================================================
# Stage 2: Planning
# =============================================================================

class BookPlan(synalinks.DataModel):
    """High-level book plan with critique."""
    vision: str = synalinks.Field(description="Book's pedagogical vision")
    progression: str = synalinks.Field(description="Learning progression strategy")
    unique_value: str = synalinks.Field(description="What makes this book special")
    critique_addressed: bool = synalinks.Field(description="Self-critique incorporated")


class ChaptersOverview(synalinks.DataModel):
    """Overview of all chapters and their connections."""
    chapter_summaries: list[str] = synalinks.Field(description="Summary of each chapter")
    chapter_connections: list[str] = synalinks.Field(description="How chapters connect")


class SectionPlan(synalinks.DataModel):
    """Detailed plan for each section."""
    section_name: str = synalinks.Field(description="Name of the section")
    subsections: list[str] = synalinks.Field(description="Subsections to generate")
    learning_objectives: list[str] = synalinks.Field(description="What reader will learn")


# =============================================================================
# Stage 3: Content Generation
# =============================================================================

class SubsectionContent(synalinks.DataModel):
    """Generated subsection content."""
    title: str = synalinks.Field(description="Subsection title")
    content: str = synalinks.Field(description="Markdown content")
    quality_score: float = synalinks.Field(description="Quality assessment")


class QualityFeedback(synalinks.DataModel):
    """Quality control feedback."""
    passed: bool = synalinks.Field(description="Passes quality threshold")
    issues: list[str] = synalinks.Field(description="Issues found")
    suggestions: list[str] = synalinks.Field(description="Improvement suggestions")


class AssembledChapter(synalinks.DataModel):
    """Complete chapter with all sections."""
    chapter_title: str = synalinks.Field(description="Chapter title")
    chapter_content: str = synalinks.Field(description="Full chapter markdown")
    illustration_concepts: list[str] = synalinks.Field(description="Concepts to illustrate")


# =============================================================================
# Stage 4: Polish & Output
# =============================================================================

class Illustration(synalinks.DataModel):
    """Generated illustration."""
    concept: str = synalinks.Field(description="Concept being illustrated")
    image_path: str = synalinks.Field(description="Path to generated image")
    caption: str = synalinks.Field(description="Figure caption")


class CoverDesign(synalinks.DataModel):
    """Book cover design."""
    visual_concept: str = synalinks.Field(description="Core visual concept")
    image_prompt: str = synalinks.Field(description="Prompt for image generation")
    cover_path: str = synalinks.Field(description="Path to cover image")


class FinalBook(synalinks.DataModel):
    """The complete generated book."""
    pdf_path: str = synalinks.Field(description="Path to final PDF")
    total_pages: int = synalinks.Field(description="Number of pages")
    chapters_count: int = synalinks.Field(description="Number of chapters")


# =============================================================================
# Pipeline Modules
# =============================================================================

async def create_pipeline_visualization():
    """Create a visual representation of the book generation pipeline."""

    # Create a simple language model for building the pipeline
    # (we won't actually run it, just visualize the structure)
    language_model = synalinks.LanguageModel(
        model="gemini/gemini-2.0-flash",
        # We're not actually calling it, just building the graph
    )

    # =========================================================================
    # Stage 1: Structure
    # =========================================================================

    # Input: User's book specification
    topic_input = synalinks.Input(data_model=TopicInput, name="User Input")

    # Multi-angle concept extraction
    concept_extractor = synalinks.Generator(
        data_model=ExtractedConcepts,
        language_model=language_model,
        name="Multi-Angle Concept Extraction"
    )
    extracted_concepts = await concept_extractor(topic_input)

    # Coverage verification loop
    coverage_verifier = synalinks.Generator(
        data_model=VerifiedOutline,
        language_model=language_model,
        name="Coverage Verification Loop"
    )
    verified_outline = await coverage_verifier(extracted_concepts)

    # =========================================================================
    # Stage 2: Planning
    # =========================================================================

    # Book plan with self-critique
    book_planner = synalinks.Generator(
        data_model=BookPlan,
        language_model=language_model,
        name="Book Plan (with Critique)"
    )
    book_plan = await book_planner(verified_outline)

    # Chapters overview - how chapters connect
    chapters_overview_gen = synalinks.Generator(
        data_model=ChaptersOverview,
        language_model=language_model,
        name="Chapters Overview"
    )
    chapters_overview = await chapters_overview_gen(book_plan)

    # Section planning for each chapter
    section_planner = synalinks.Generator(
        data_model=SectionPlan,
        language_model=language_model,
        name="Section Planning"
    )
    section_plans = await section_planner(chapters_overview)

    # =========================================================================
    # Stage 3: Content Generation
    # =========================================================================

    # Generate subsection content
    subsection_generator = synalinks.Generator(
        data_model=SubsectionContent,
        language_model=language_model,
        name="Subsection Generation"
    )
    subsection_content = await subsection_generator(section_plans)

    # Quality control loop
    quality_controller = synalinks.Generator(
        data_model=QualityFeedback,
        language_model=language_model,
        name="Quality Control Loop"
    )
    quality_feedback = await quality_controller(subsection_content)

    # Assemble chapter from subsections
    chapter_assembler = synalinks.Generator(
        data_model=AssembledChapter,
        language_model=language_model,
        name="Chapter Assembly"
    )
    assembled_chapter = await chapter_assembler(quality_feedback)

    # =========================================================================
    # Stage 4: Polish & Output
    # =========================================================================

    # Generate illustrations
    illustration_generator = synalinks.Generator(
        data_model=Illustration,
        language_model=language_model,
        name="Illustration Generation"
    )
    illustrations = await illustration_generator(assembled_chapter)

    # Dynamic cover generation
    cover_generator = synalinks.Generator(
        data_model=CoverDesign,
        language_model=language_model,
        name="Dynamic Cover Generation"
    )
    cover_design = await cover_generator(illustrations)

    # Final PDF assembly
    pdf_assembler = synalinks.Generator(
        data_model=FinalBook,
        language_model=language_model,
        name="PDF Assembly"
    )
    final_book = await pdf_assembler(cover_design)

    # =========================================================================
    # Create Program and Visualize
    # =========================================================================

    program = synalinks.Program(
        inputs=topic_input,
        outputs=final_book,
        name="Learner: Personalized Book Generator"
    )

    return program


async def main():
    """Generate the pipeline visualization."""
    print("Creating Learner pipeline visualization...")

    program = await create_pipeline_visualization()

    # Save visualization to multiple formats
    output_dir = "/Users/aynur/aynur/synalinks_test/output"

    # Create output directory if it doesn't exist
    import os
    os.makedirs(output_dir, exist_ok=True)

    # Generate vertical layout (top to bottom)
    print("\nGenerating vertical pipeline diagram...")
    plot_program(
        program,
        to_file="pipeline_vertical.png",
        to_folder=output_dir,
        show_schemas=True,
        show_module_names=True,
        rankdir="TB",  # Top to Bottom
        dpi=300,
        expand_nested=True,
    )
    print(f"  Saved to: {output_dir}/pipeline_vertical.png")

    # Generate horizontal layout (left to right)
    print("Generating horizontal pipeline diagram...")
    plot_program(
        program,
        to_file="pipeline_horizontal.png",
        to_folder=output_dir,
        show_schemas=True,
        show_module_names=True,
        rankdir="LR",  # Left to Right
        dpi=300,
        expand_nested=True,
    )
    print(f"  Saved to: {output_dir}/pipeline_horizontal.png")

    # Generate simplified version without schemas
    print("Generating simplified pipeline diagram...")
    plot_program(
        program,
        to_file="pipeline_simple.png",
        to_folder=output_dir,
        show_schemas=False,
        show_module_names=True,
        rankdir="TB",
        dpi=200,
    )
    print(f"  Saved to: {output_dir}/pipeline_simple.png")

    # Print program summary
    print("\n" + "="*60)
    print("LEARNER PIPELINE SUMMARY")
    print("="*60)
    program.summary()

    print("\nVisualization complete!")
    print(f"Check the output directory: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
