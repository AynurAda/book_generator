"""
Book Generator - AI-powered book generation using Synalinks.

This package provides a multi-stage pipeline for generating comprehensive
educational books from a topic description.
"""

from .config import Config
from .models import Topic
from .authors import AUTHOR_PROFILES, get_author_profile, list_available_authors

__version__ = "1.0.0"
__all__ = ["Config", "Topic", "AUTHOR_PROFILES", "get_author_profile", "list_available_authors"]
