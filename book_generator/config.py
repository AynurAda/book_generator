"""
Configuration management for the book generator.
"""

import os
import random
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration for book generation."""

    # Book metadata
    topic: str = ""
    goal: str = ""
    book_name: str = ""
    subtitle: str = "A comprehensive guide"
    authors: str = "AI Assistant"
    audience: str = "technical readers with some background in the field"

    # Generation settings
    test_mode: bool = False
    test_max_chapters: int = 2

    # Resume settings
    resume_from_dir: Optional[str] = None

    # Interactive approval
    interactive_outline_approval: bool = True  # Prompt user to approve outline before continuing

    # Plan quality control
    plan_critique_enabled: bool = True  # Enable self-critique loop for plan generation
    plan_critique_max_attempts: int = 5  # Max revision attempts per plan

    # Default outline (optional) - if provided and enabled, skip outline generation
    default_outline: Optional[dict] = None
    use_default_outline: bool = True  # Set to false to ignore default_outline even if defined

    # Chapter limit (optional) - if provided, select most important chapters
    num_chapters: Optional[int] = None

    # Focus areas (optional) - guides chapter selection when num_chapters is set
    focus: Optional[str] = None

    # Output directory (set during runtime)
    output_dir: Optional[str] = None

    # Model settings
    model_name: str = "gemini/gemini-3-flash-preview"

    # Author settings
    author_key: Optional[str] = None  # Key from authors.AUTHOR_PROFILES, None for no styling

    # Illustration settings
    enable_illustrations: bool = False  # Whether to add illustrations to chapters
    enable_generated_images: bool = True  # Whether to generate AI images (vs just Mermaid)
    image_model: str = "gemini/gemini-3-pro-image-preview"  # Model for image generation

    # Cover settings
    # Available styles: humorous, abstract, cyberpunk, minimalist, watercolor,
    # vintage, blueprint, surreal, isometric, papercraft, neon_noir,
    # botanical, bauhaus, pixel_art, art_deco
    cover_style: str = "abstract"

    # Citation settings
    enable_citations: bool = False  # Enable full citation verification pipeline (slow)
    enable_chapter_references: bool = False  # Fast: add references from research papers at end of each chapter
    citation_confidence_threshold: float = 0.75  # Minimum confidence to accept a citation
    skip_low_importance_claims: bool = True  # Skip verification for low-importance claims

    # Deep research settings
    enable_research: bool = False  # Enable Gemini Deep Research for cutting-edge content
    research_max_queries: int = 5  # Maximum research queries to run
    research_cache: bool = True  # Cache research results for reuse

    # Stage 2 research settings (requires mcp-graphiti Docker container running)
    enable_stage2_research: bool = False  # Enable Stage 2 with knowledge graph
    graphiti_mcp_url: str = "http://localhost:8000/mcp/"  # mcp-graphiti SSE endpoint
    graphiti_group_id: str = "book_research"  # Namespace for this book's research

    # Reader mode override for testing (bypasses Branch decision)
    reader_mode_override: Optional[str] = None  # 'practitioner', 'academic', or 'hybrid'

    # Introduction styles for variety (will be shuffled at runtime)
    intro_styles: List[str] = field(default_factory=lambda: [
        # Question-based openings
        "Start with a thought-provoking question that challenges common assumptions",
        "Open with a fundamental question that this section aims to answer",
        "Begin by asking what would happen if a key assumption were violated",

        # Problem-based openings
        "Begin with a concrete real-world problem or challenge that this concept solves",
        "Open with a practical scenario where this concept makes a critical difference",
        "Start by describing a limitation of existing approaches that motivates this topic",
        "Begin with a failure case that illustrates why this concept matters",

        # Context-based openings
        "Open with a brief historical context or evolution of the idea",
        "Start by connecting to what was covered in previous sections, then pivot to the new topic",
        "Begin by situating this concept within the broader landscape of the field",
        "Open with the intellectual lineage - what ideas led to this development",

        # Insight-based openings
        "Begin with a surprising fact or counterintuitive insight",
        "Start with a key observation that motivates the entire discussion",
        "Open with a paradox or tension that this concept helps resolve",
        "Begin with a commonly held misconception and why it falls short",

        # Definition-based openings
        "Start by defining the core problem space before introducing the solution",
        "Begin with a precise definition that anchors the subsequent discussion",
        "Open by distinguishing this concept from related but distinct ideas",
        "Start by establishing what this concept is NOT, to clarify scope",

        # Motivation-based openings
        "Begin by explaining why practitioners care about this topic",
        "Open with the practical benefits that mastering this concept provides",
        "Start with the gap in capabilities that this concept addresses",
        "Begin by describing what becomes possible once this concept is understood",

        # Example-based openings
        "Start with a concrete example that illustrates the core idea immediately",
        "Open with a running example that will be developed throughout the section",
        "Begin with a minimal case that captures the essence of the concept",

        # Contrast-based openings
        "Start by contrasting naive and sophisticated approaches to the problem",
        "Open by comparing how different fields approach similar challenges",
        "Begin by showing what changes when this concept is applied versus ignored",

        # Forward-looking openings
        "Start by previewing the key insights this section will develop",
        "Open with a roadmap of the conceptual territory to be covered",
        "Begin by stating the main claim and indicating how it will be supported",
    ])

    def setup_output_dir(self, base_path: str = ".") -> str:
        """Create or use output directory for this run."""
        if self.resume_from_dir:
            self.output_dir = os.path.join(base_path, self.resume_from_dir)
            if not os.path.exists(self.output_dir):
                raise ValueError(f"Resume directory does not exist: {self.output_dir}")
            logger.info(f"RESUMING from directory: {self.output_dir}")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = os.path.join(base_path, "output", timestamp)
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"Output directory: {self.output_dir}")
        return self.output_dir

    def get_topic_data(self) -> dict:
        """Get topic data as dictionary for generators."""
        return {
            "topic": self.topic,
            "goal": self.goal,
            "book_name": self.book_name,
            "audience": self.audience,
        }

    def shuffle_intro_styles(self) -> None:
        """Shuffle introduction styles for variety across book generations."""
        random.shuffle(self.intro_styles)
        logger.info(f"Shuffled {len(self.intro_styles)} introduction styles")

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create config from dictionary."""
        # Parse default_outline if provided, enabled, and not empty
        default_outline = None
        use_default_outline = data.get("use_default_outline", True)
        if use_default_outline and "default_outline" in data and data["default_outline"]:
            default_outline = cls._parse_outline(data["default_outline"])

        return cls(
            topic=data.get("topic", ""),
            goal=data.get("goal", ""),
            book_name=data.get("book_name", ""),
            subtitle=data.get("subtitle", "A comprehensive guide"),
            authors=data.get("authors", "AI Assistant"),
            audience=data.get("audience", "technical readers with some background in the field"),
            test_mode=data.get("test_mode", False),
            test_max_chapters=data.get("test_max_chapters", 2),
            resume_from_dir=data.get("resume_from_dir"),
            interactive_outline_approval=data.get("interactive_outline_approval", True),
            plan_critique_enabled=data.get("plan_critique_enabled", True),
            plan_critique_max_attempts=data.get("plan_critique_max_attempts", 5),
            default_outline=default_outline,
            use_default_outline=use_default_outline,
            num_chapters=data.get("num_chapters"),
            focus=data.get("focus"),
            model_name=data.get("model_name", "gemini/gemini-3-flash-preview"),
            author_key=data.get("author_key"),
            enable_illustrations=data.get("enable_illustrations", False),
            enable_generated_images=data.get("enable_generated_images", True),
            image_model=data.get("image_model", "gemini/gemini-3-pro-image-preview"),
            cover_style=data.get("cover_style", "humorous"),
            enable_citations=data.get("enable_citations", False),
            enable_chapter_references=data.get("enable_chapter_references", False),
            citation_confidence_threshold=data.get("citation_confidence_threshold", 0.75),
            skip_low_importance_claims=data.get("skip_low_importance_claims", True),
            enable_research=data.get("enable_research", False),
            research_max_queries=data.get("research_max_queries", 5),
            research_cache=data.get("research_cache", True),
            enable_stage2_research=data.get("enable_stage2_research", False),
            graphiti_mcp_url=data.get("graphiti_mcp_url", "http://localhost:8000/mcp/"),
            graphiti_group_id=data.get("graphiti_group_id", "book_research"),
            reader_mode_override=data.get("reader_mode_override"),
        )

    @staticmethod
    def _parse_outline(outline_data: list) -> dict:
        """Parse outline from YAML format to DeepHierarchy format.

        YAML format:
        - concept: "Chapter Name"
          subconcepts:
            - subconcept: "Section Name"
              subsubconcepts:
                - "Subsection 1"
                - "Subsection 2"

        Returns dict in DeepHierarchy format:
        {"concepts": [{"concept": "...", "subconcepts": [...]}]}
        """
        concepts = []
        for chapter in outline_data:
            concept_entry = {
                "concept": chapter.get("concept", ""),
                "subconcepts": []
            }
            for section in chapter.get("subconcepts", []):
                subconcept_entry = {
                    "subconcept": section.get("subconcept", ""),
                    "subsubconcepts": section.get("subsubconcepts", [])
                }
                concept_entry["subconcepts"].append(subconcept_entry)
            concepts.append(concept_entry)
        return {"concepts": concepts}


# Default configuration instance
default_config = Config()
