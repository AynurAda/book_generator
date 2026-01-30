"""
Synalinks data models for book generation.

This module contains all the structured data models used throughout
the book generation pipeline.
"""

import synalinks


# =============================================================================
# Input Models
# =============================================================================

class Topic(synalinks.DataModel):
    """Initial book specification."""
    topic: str = synalinks.Field(description="The topic for which to write a book")
    goal: str = synalinks.Field(description="The goal of the book")
    book_name: str = synalinks.Field(description="The name of the book to be generated")


class OutlineReorganizationInput(synalinks.DataModel):
    """Input for reorganizing the book outline."""
    topic: str = synalinks.Field(description="The main topic of the book")
    goal: str = synalinks.Field(description="The goal of the book")
    current_outline: str = synalinks.Field(description="The current outline as a formatted string")


class BookPlanInput(synalinks.DataModel):
    """Input for generating the book plan."""
    topic: str = synalinks.Field(description="The main topic of the book")
    goal: str = synalinks.Field(description="The goal of the book")
    book_name: str = synalinks.Field(description="The name of the book")
    full_outline: str = synalinks.Field(description="The complete book outline")


class ChapterPlansInput(synalinks.DataModel):
    """Input for generating chapter plans."""
    topic: str = synalinks.Field(description="The main topic of the book")
    goal: str = synalinks.Field(description="The goal of the book")
    book_name: str = synalinks.Field(description="The name of the book")
    full_outline: str = synalinks.Field(description="The complete book outline")
    book_plan: str = synalinks.Field(description="The high-level book plan")
    chapters: str = synalinks.Field(description="List of chapter names to plan")


class SectionPlansInput(synalinks.DataModel):
    """Input for generating section plans within a chapter."""
    topic: str = synalinks.Field(description="The main topic of the book")
    goal: str = synalinks.Field(description="The goal of the book")
    book_name: str = synalinks.Field(description="The name of the book")
    book_plan: str = synalinks.Field(description="The high-level book plan")
    chapter_plan: str = synalinks.Field(description="The plan for this chapter")
    chapter_name: str = synalinks.Field(description="The name of the chapter")
    sections: str = synalinks.Field(description="List of section names in this chapter")
    subsections_by_section: str = synalinks.Field(description="Mapping of sections to their subsections")


class SectionInput(synalinks.DataModel):
    """Input for generating a book subsection."""
    topic: str = synalinks.Field(description="The main topic of the book")
    goal: str = synalinks.Field(description="The goal of the book")
    book_name: str = synalinks.Field(description="The name of the book")
    audience: str = synalinks.Field(description="The target audience for the book")
    book_plan: str = synalinks.Field(description="The high-level book plan")
    chapter_plan: str = synalinks.Field(description="The plan for the current chapter")
    section_plan: str = synalinks.Field(description="The plan for the current section")
    current_subsection: str = synalinks.Field(description="The specific subsection to generate content for")


class ChapterInput(synalinks.DataModel):
    """Input for rewriting sections into a coherent chapter."""
    topic: str = synalinks.Field(description="The main topic of the book")
    goal: str = synalinks.Field(description="The goal of the book")
    book_name: str = synalinks.Field(description="The name of the book")
    audience: str = synalinks.Field(description="The target audience for the book")
    chapter_title: str = synalinks.Field(description="The title of the chapter")
    subsections_content: str = synalinks.Field(description="The generated content for each subsection")
    previous_chapter_summary: str = synalinks.Field(description="Brief summary of the previous chapter for context")
    next_chapter_summary: str = synalinks.Field(description="Brief summary of the next chapter for context")
    intro_style: str = synalinks.Field(description="The style to use for the section introduction")


class ChapterPolishInput(synalinks.DataModel):
    """Input for polishing a chapter."""
    topic: str = synalinks.Field(description="The main topic of the book")
    goal: str = synalinks.Field(description="The goal of the book")
    book_name: str = synalinks.Field(description="The name of the book")
    audience: str = synalinks.Field(description="The target audience for the book")
    chapter_name: str = synalinks.Field(description="The name of the chapter being polished")
    chapter_number: int = synalinks.Field(description="The chapter number (1-indexed)")
    total_chapters: int = synalinks.Field(description="Total number of chapters in the book")
    chapter_plan: str = synalinks.Field(description="The plan for this chapter")
    chapter_content: str = synalinks.Field(description="The current chapter content to polish")
    previous_chapter_summary: str = synalinks.Field(description="Summary of previous chapter")
    next_chapter_summary: str = synalinks.Field(description="Summary of next chapter")


# =============================================================================
# Output Models
# =============================================================================

class ConceptExtractor(synalinks.DataModel):
    """Branch output for concept extraction."""
    main_concepts: list[str] = synalinks.Field(
        description="A list of main concepts that must be covered by the book"
    )
    thinking: list[str] = synalinks.Field(
        description="Your step by step thinking"
    )


class MergedConcepts(synalinks.DataModel):
    """Deduplicated concept list after merging branches."""
    main_concepts: list[str] = synalinks.Field(
        description="Comprehensive deduplicated list of main concepts from all branches"
    )


class ConceptWithSubconcepts(synalinks.DataModel):
    """A main concept with its related subconcepts."""
    concept: str = synalinks.Field(description="The main concept name")
    subconcepts: list[str] = synalinks.Field(
        description="Specific subconcepts, techniques, or topics belonging to this main concept domain"
    )
    thinking: list[str] = synalinks.Field(
        description="Your step by step thinking"
    )


class HierarchicalConcepts(synalinks.DataModel):
    """Full hierarchy of concepts with their subconcepts."""
    concepts: list[ConceptWithSubconcepts] = synalinks.Field(
        description="List of main concepts, each with their detailed subconcepts"
    )
    thinking: list[str] = synalinks.Field(
        description="Your step by step thinking"
    )


class SubconceptWithDetails(synalinks.DataModel):
    """A subconcept with its sub-subconcepts."""
    subconcept: str = synalinks.Field(description="The subconcept name")
    subsubconcepts: list[str] = synalinks.Field(
        description="Specific sub-subconcepts, techniques, or details belonging to this subconcept"
    )


class ConceptDeep(synalinks.DataModel):
    """A main concept with subconcepts expanded to sub-subconcepts."""
    concept: str = synalinks.Field(description="The main concept name")
    subconcepts: list[SubconceptWithDetails] = synalinks.Field(
        description="Subconcepts each with their own sub-subconcepts"
    )


class DeepHierarchy(synalinks.DataModel):
    """Three-level hierarchy: concepts -> subconcepts -> sub-subconcepts."""
    concepts: list[ConceptDeep] = synalinks.Field(
        description="Complete three-level hierarchy of concepts"
    )


class ReorganizedOutline(synalinks.DataModel):
    """Output containing the reorganized outline following conceptual/temporal evolution."""
    should_reorganize: bool = synalinks.Field(
        description="Whether reorganization makes sense for this topic"
    )
    reasoning: str = synalinks.Field(
        description="Explanation of why reorganization is or isn't needed"
    )
    chapter_order: list[int] = synalinks.Field(
        description="New order of chapters as 1-based indices. Include ALL chapters."
    )


class BookPlan(synalinks.DataModel):
    """High-level plan for the entire book."""
    book_summary: str = synalinks.Field(
        description="2-3 paragraph overview of the book"
    )
    narrative_arc: str = synalinks.Field(
        description="Description of how the book progresses"
    )
    chapter_connections: str = synalinks.Field(
        description="How the chapters connect and build upon each other"
    )


class ChapterPlan(synalinks.DataModel):
    """Plan for a single chapter."""
    chapter_name: str = synalinks.Field(description="The name of the chapter")
    chapter_summary: str = synalinks.Field(
        description="2-3 paragraph summary of what this chapter covers"
    )
    role_in_book: str = synalinks.Field(
        description="How this chapter fits into the overall book narrative"
    )
    connection_to_previous: str = synalinks.Field(
        description="How this chapter builds on the previous chapter"
    )
    connection_to_next: str = synalinks.Field(
        description="How this chapter leads into the next chapter"
    )


class AllChapterPlans(synalinks.DataModel):
    """Plans for all chapters in the book."""
    chapter_plans: list[ChapterPlan] = synalinks.Field(
        description="List of plans for each chapter"
    )


class SectionPlan(synalinks.DataModel):
    """Plan for a single section within a chapter."""
    section_name: str = synalinks.Field(description="The name of the section")
    section_summary: str = synalinks.Field(
        description="Summary of what this section covers"
    )
    role_in_chapter: str = synalinks.Field(
        description="How this section contributes to the chapter"
    )
    subsections_overview: str = synalinks.Field(
        description="Brief overview of subsections and their connections"
    )


class ChapterSectionPlans(synalinks.DataModel):
    """Section plans for a single chapter."""
    chapter_name: str = synalinks.Field(description="The name of the chapter")
    section_plans: list[SectionPlan] = synalinks.Field(
        description="List of section plans for this chapter"
    )


class SectionOutput(synalinks.DataModel):
    """Output for a generated book section."""
    concept_explanation: str = synalinks.Field(
        description="Clear and thorough explanation of the core concepts"
    )
    analogies_and_examples: str = synalinks.Field(
        description="Relatable analogies and practical examples"
    )


class ChapterOutput(synalinks.DataModel):
    """Output for rewritten chapter content."""
    chapter_content: str = synalinks.Field(
        description="The complete rewritten chapter content"
    )


class PolishedChapter(synalinks.DataModel):
    """Final polished chapter with improved flow and detail."""
    chapter_content: str = synalinks.Field(
        description="The polished chapter content"
    )


class IntroductionInput(synalinks.DataModel):
    """Input for generating the book introduction."""
    topic: str = synalinks.Field(description="The main topic of the book")
    goal: str = synalinks.Field(description="The goal of the book")
    book_name: str = synalinks.Field(description="The name of the book")
    audience: str = synalinks.Field(description="The target audience for the book")
    book_plan: str = synalinks.Field(description="The high-level book plan")
    outline: str = synalinks.Field(description="The complete book outline")


class BookIntroduction(synalinks.DataModel):
    """Generated book introduction."""
    introduction: str = synalinks.Field(
        description="The complete introduction section for the book"
    )


# =============================================================================
# Author Style Models
# =============================================================================

class AuthorStyleInput(synalinks.DataModel):
    """Input for applying author style to content."""
    original_content: str = synalinks.Field(description="The original chapter content to restyle")
    author_name: str = synalinks.Field(description="The author's name")
    author_style: str = synalinks.Field(description="Description of the author's writing style")
    author_tone: str = synalinks.Field(description="The author's characteristic tone")
    chapter_name: str = synalinks.Field(description="The name of the chapter being styled")


class StyledContent(synalinks.DataModel):
    """Output for author-styled content."""
    styled_content: str = synalinks.Field(
        description="The content rewritten in the author's distinctive voice and style"
    )


class AboutAuthorInput(synalinks.DataModel):
    """Input for generating About the Author section."""
    author_name: str = synalinks.Field(description="The author's pen name")
    author_background: str = synalinks.Field(description="The author's biographical background")
    author_expertise: str = synalinks.Field(description="The author's area of expertise")
    book_name: str = synalinks.Field(description="The name of the book")
    book_topic: str = synalinks.Field(description="The main topic of the book")


class AboutAuthorOutput(synalinks.DataModel):
    """Output for About the Author section."""
    about_author: str = synalinks.Field(
        description="The complete About the Author section in flowing prose"
    )


# =============================================================================
# Illustration Models
# =============================================================================

class IllustrationAnalysisInput(synalinks.DataModel):
    """Input for analyzing illustration opportunities in content."""
    chapter_content: str = synalinks.Field(description="The chapter content to analyze")
    chapter_name: str = synalinks.Field(description="The name of the chapter")
    topic: str = synalinks.Field(description="The main topic of the book")
    audience: str = synalinks.Field(description="The target audience")


class IllustrationOpportunity(synalinks.DataModel):
    """A single illustration opportunity."""
    illustration_type: str = synalinks.Field(
        description="Type: mermaid_flowchart, mermaid_sequence, mermaid_class, mermaid_state, mermaid_mindmap, or generated_image"
    )
    location: str = synalinks.Field(
        description="The exact text after which to place the illustration"
    )
    description: str = synalinks.Field(
        description="What the illustration should show"
    )
    caption: str = synalinks.Field(
        description="A brief caption for the illustration"
    )


class IllustrationOpportunities(synalinks.DataModel):
    """Collection of illustration opportunities for a chapter."""
    opportunities: list[IllustrationOpportunity] = synalinks.Field(
        description="List of illustration opportunities identified in the content"
    )


class MermaidDiagramInput(synalinks.DataModel):
    """Input for generating a Mermaid diagram."""
    diagram_type: str = synalinks.Field(description="The type of Mermaid diagram to generate")
    description: str = synalinks.Field(description="What the diagram should illustrate")
    context: str = synalinks.Field(description="Surrounding context from the chapter")


class MermaidDiagramOutput(synalinks.DataModel):
    """Output containing generated Mermaid diagram code."""
    mermaid_code: str = synalinks.Field(
        description="Valid Mermaid diagram code (no markdown fences)"
    )


class ImagePromptInput(synalinks.DataModel):
    """Input for generating an image prompt."""
    concept_description: str = synalinks.Field(description="The concept to visualize")
    context: str = synalinks.Field(description="Context from the chapter")
    chapter_name: str = synalinks.Field(description="The chapter name")


class ImagePromptOutput(synalinks.DataModel):
    """Output containing optimized image generation prompt."""
    image_prompt: str = synalinks.Field(
        description="Optimized prompt for AI image generation"
    )
