"""
Internal constants for the book generator content pipeline.

These are tuning parameters used during content generation.
Adjust them here rather than hunting through the code.
"""

# Maximum quality-check retry attempts before accepting the last version
MAX_QUALITY_CHECK_ATTEMPTS = 5

# Character limit when truncating full research context for prompts
RESEARCH_CONTEXT_CHAR_LIMIT = 6000

# Maximum number of banned (other-subsection) concepts shown in prompts
MAX_BANNED_CONCEPTS_DISPLAY = 10

# Multiplier for section file numbering offset (chapter_number - 1) * this
SECTION_NUMBERING_MULTIPLIER = 100
