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

    # Output directory (set during runtime)
    output_dir: Optional[str] = None

    # Model settings
    model_name: str = "gemini/gemini-3-flash-preview"

    # Author settings
    author_key: Optional[str] = None  # Key from authors.AUTHOR_PROFILES, None for no styling

    # Illustration settings
    enable_illustrations: bool = False  # Whether to add illustrations to chapters
    enable_generated_images: bool = True  # Whether to generate AI images (vs just Mermaid)
    image_model: str = "gemini/imagen-3.0-generate-002"  # Model for image generation

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
            model_name=data.get("model_name", "gemini/gemini-3-flash-preview"),
            author_key=data.get("author_key"),
            enable_illustrations=data.get("enable_illustrations", False),
            enable_generated_images=data.get("enable_generated_images", True),
            image_model=data.get("image_model", "gemini/imagen-3.0-generate-002"),
        )


# Default configuration instance
default_config = Config()
