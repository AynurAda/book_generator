"""
Utility functions for file I/O and text processing.
"""

import os
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


def sanitize_filename(name: str, max_length: int = 40) -> str:
    """
    Sanitize a string to be safe for use in filenames.

    Args:
        name: The string to sanitize
        max_length: Maximum length for the filename

    Returns:
        A sanitized string safe for filenames
    """
    # Replace spaces and dots with underscores
    safe = name.replace(" ", "_").replace(".", "_")
    # Replace path separators and other problematic characters
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        safe = safe.replace(char, "-" if char in ['/', '\\', ':'] else "")
    # Truncate to max length
    return safe[:max_length]


def output_exists(output_dir: str, filename: str) -> bool:
    """Check if an output file already exists."""
    if output_dir is None:
        return False
    filepath = os.path.join(output_dir, filename)
    return os.path.exists(filepath)


def load_from_file(output_dir: str, filename: str) -> Optional[str]:
    """Load content from a file in the output directory."""
    if output_dir is None:
        return None
    filepath = os.path.join(output_dir, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    logger.info(f"Loaded existing: {filepath}")
    return content


def load_json_from_file(output_dir: str, filename: str) -> Optional[Any]:
    """Load JSON content from a file."""
    content = load_from_file(output_dir, filename)
    if content is None:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON from {filename}")
        return None


def save_to_file(output_dir: str, filename: str, content: str) -> str:
    """
    Save content to a file in the output directory.

    Args:
        output_dir: The output directory path
        filename: The filename to save to
        content: The content to save

    Returns:
        The full filepath that was saved
    """
    if output_dir is None:
        raise ValueError("Output directory not set")
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Saved: {filepath}")
    return filepath


def save_json_to_file(output_dir: str, filename: str, data: Any) -> str:
    """Save data as JSON to a file."""
    content = json.dumps(data, indent=2, ensure_ascii=False)
    return save_to_file(output_dir, filename, content)


def build_outline_string(results: dict) -> str:
    """
    Convert outline results to HTML-formatted table of contents.

    Used for the book's TOC in the PDF.
    """
    lines = []
    lines.append('<div class="toc-columns">')
    concepts_list = results.get("concepts", [])

    for i, concept_data in enumerate(concepts_list, 1):
        concept_name = concept_data.get("concept", "Unknown")
        subconcepts = concept_data.get("subconcepts", [])

        # Start paragraph with chapter title
        para_lines = [f"<p><strong>{i}. {concept_name}</strong><br>"]
        for j, subconcept_data in enumerate(subconcepts, 1):
            subconcept_name = subconcept_data.get("subconcept", "Unknown")
            para_lines.append(f"&nbsp;&nbsp;&nbsp;{i}.{j} {subconcept_name}<br>")

        # Remove trailing <br> from last line and close paragraph
        para_lines[-1] = para_lines[-1].replace("<br>", "</p>")
        lines.append("".join(para_lines))
        lines.append("")  # Empty line between chapters

    lines.append('</div>')
    return "\n".join(lines)


def build_outline_text(results: dict) -> str:
    """
    Convert outline results to full text format including all three levels.

    Used for planning stages that need complete visibility of the book structure.
    """
    lines = []
    concepts_list = results.get("concepts", [])

    for i, concept_data in enumerate(concepts_list, 1):
        concept_name = concept_data.get("concept", "Unknown")
        subconcepts = concept_data.get("subconcepts", [])
        lines.append(f"{i}. {concept_name}")

        for j, subconcept_data in enumerate(subconcepts, 1):
            subconcept_name = subconcept_data.get("subconcept", "Unknown")
            subsubconcepts = subconcept_data.get("subsubconcepts", [])
            lines.append(f"   {i}.{j} {subconcept_name}")

            # Include all subsection topics
            for k, subsubconcept in enumerate(subsubconcepts, 1):
                lines.append(f"      {i}.{j}.{k} {subsubconcept}")

    return "\n".join(lines)


def build_outline_text_short(results: dict) -> str:
    """
    Convert outline results to short text format (chapters and sections only).

    Used for book display (table of contents) where subsections are too detailed.
    """
    lines = []
    concepts_list = results.get("concepts", [])

    for i, concept_data in enumerate(concepts_list, 1):
        concept_name = concept_data.get("concept", "Unknown")
        subconcepts = concept_data.get("subconcepts", [])
        lines.append(f"{i}. {concept_name}")

        for j, subconcept_data in enumerate(subconcepts, 1):
            subconcept_name = subconcept_data.get("subconcept", "Unknown")
            lines.append(f"   {i}.{j} {subconcept_name}")

    return "\n".join(lines)


def extract_hierarchy(outline_results: dict) -> dict:
    """
    Extract the full hierarchy: chapters -> sections -> subsections.

    Returns a nested dictionary structure.
    """
    hierarchy = {}
    concepts_list = outline_results.get("concepts", [])

    for i, concept_data in enumerate(concepts_list, 1):
        chapter_name = concept_data.get("concept", "Unknown")
        chapter_key = f"{i}. {chapter_name}"
        hierarchy[chapter_key] = {}

        subconcepts = concept_data.get("subconcepts", [])
        for j, subconcept_data in enumerate(subconcepts, 1):
            section_name = subconcept_data.get("subconcept", "Unknown")
            section_key = f"{i}.{j} {section_name}"
            subsubconcepts = subconcept_data.get("subsubconcepts", [])

            hierarchy[chapter_key][section_key] = [
                f"{i}.{j}.{k} {ss}" for k, ss in enumerate(subsubconcepts, 1)
            ]

    return hierarchy


def get_chapter_names(outline_results: dict) -> list:
    """Get list of chapter names from outline."""
    chapter_names = []
    concepts_list = outline_results.get("concepts", [])

    for i, concept_data in enumerate(concepts_list, 1):
        chapter_name = concept_data.get("concept", "Unknown")
        chapter_names.append(f"{i}. {chapter_name}")

    return chapter_names
