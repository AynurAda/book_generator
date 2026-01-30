"""
Book Generator - AI-powered book generation using Synalinks.

This package provides a multi-stage pipeline for generating comprehensive
educational books from a topic description.
"""

from .config import Config
from .models import Topic

__version__ = "1.0.0"
__all__ = ["Config", "Topic"]
