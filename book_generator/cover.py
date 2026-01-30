"""
Book cover generation using Google's Imagen model.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def generate_cover(
    book_name: str,
    subtitle: str,
    authors: str,
    output_path: str
) -> Optional[str]:
    """
    Generate a book cover image using Imagen 4.0.

    Args:
        book_name: The title of the book
        subtitle: The book's subtitle
        authors: The author names
        output_path: Path to save the cover image

    Returns:
        The output path if successful, None otherwise
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning("google-genai not installed. Skipping cover generation.")
        return None

    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        logger.warning("No API key found for cover generation. Skipping.")
        return None

    logger.info("Generating book cover...")

    client = genai.Client(api_key=api_key)

    prompt = f"""Book cover for a technical book about autonomous AI agents.

Title: "{book_name}"
Subtitle: "{subtitle}"
Authors: {authors}"""

    try:
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="3:4",
            )
        )

        if response.generated_images:
            image = response.generated_images[0]

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            image.image.save(output_path)
            logger.info(f"Cover saved to: {output_path}")
            return output_path
        else:
            logger.warning("No cover image generated")
            return None

    except Exception as e:
        logger.warning(f"Cover generation failed: {e}")
        return None
