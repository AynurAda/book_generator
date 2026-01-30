"""
Configuration management for the book generator.
"""

import os
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

    # Output directory (set during runtime)
    output_dir: Optional[str] = None

    # Model settings
    model_name: str = "gemini/gemini-3-flash-preview"

    # Author settings
    author_key: Optional[str] = None  # Key from authors.AUTHOR_PROFILES, None for no styling

    # Introduction styles for variety
    intro_styles: List[str] = field(default_factory=lambda: [
        "Start with a thought-provoking question that challenges common assumptions",
        "Begin with a concrete real-world problem or challenge that this concept solves",
        "Open with a brief historical context or evolution of the idea",
        "Start by connecting to what was covered in previous chapters, then pivot to the new topic",
        "Begin with a surprising fact or counterintuitive insight",
        "Open with a practical scenario where this concept makes a critical difference",
        "Start by defining the core problem space before introducing the solution",
        "Begin with a comparison to a familiar concept from another domain",
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
            model_name=data.get("model_name", "gemini/gemini-3-flash-preview"),
            author_key=data.get("author_key"),
        )


# Default configuration instance
default_config = Config()
