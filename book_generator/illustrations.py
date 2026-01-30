"""
Illustration generation for book chapters.

This module handles:
- Analyzing content for illustration opportunities
- Generating Mermaid diagrams for concepts
- Generating images using AI image models
- Embedding illustrations in chapter content
"""

import os
import re
import logging
import base64
from typing import List, Optional, Dict, Any

import synalinks

from .models import (
    IllustrationAnalysisInput,
    IllustrationOpportunities,
    MermaidDiagramInput,
    MermaidDiagramOutput,
    ImagePromptInput,
    ImagePromptOutput,
)
from .utils import output_exists, load_json_from_file, save_to_file, save_json_to_file, sanitize_filename

logger = logging.getLogger(__name__)


async def analyze_illustration_opportunities(
    chapter_content: str,
    chapter_name: str,
    topic: str,
    audience: str,
    language_model,
) -> List[Dict[str, Any]]:
    """
    Analyze chapter content to identify where illustrations would be helpful.

    Returns:
        List of illustration opportunities with type, location, and description
    """
    logger.info(f"Analyzing illustration opportunities for: {chapter_name}")

    generator = synalinks.Generator(
        data_model=IllustrationOpportunities,
        language_model=language_model,
        temperature=1.0,
        instructions="""Analyze this chapter content and identify where visual illustrations would
significantly enhance understanding.

For each opportunity, determine:
1. The TYPE of illustration that would work best:
   - "mermaid_flowchart": For processes, workflows, decision trees
   - "mermaid_sequence": For interactions, communication patterns, protocols
   - "mermaid_class": For relationships, hierarchies, structures
   - "mermaid_state": For state machines, lifecycle diagrams
   - "mermaid_mindmap": For concept relationships, topic overviews
   - "generated_image": For conceptual visualizations, abstract concepts, analogies

2. The LOCATION: Quote the exact sentence or paragraph AFTER which the illustration should appear

3. A DESCRIPTION of what the illustration should show

GUIDELINES:
- Only suggest illustrations that ADD VALUE - don't illustrate obvious things
- Prefer Mermaid diagrams for technical/structural content
- Use generated images for abstract concepts, analogies, or visual metaphors
- Maximum 3-5 illustrations per chapter to avoid clutter
- Consider the target audience when deciding complexity

Be selective - quality over quantity."""
    )

    input_data = IllustrationAnalysisInput(
        chapter_content=chapter_content,
        chapter_name=chapter_name,
        topic=topic,
        audience=audience
    )

    result = await generator(input_data)
    opportunities = result.get_json().get("opportunities", [])

    return opportunities


async def generate_mermaid_diagram(
    diagram_type: str,
    description: str,
    context: str,
    language_model,
) -> Optional[str]:
    """
    Generate a Mermaid diagram based on the description.

    Returns:
        Mermaid diagram code as string, or None if generation fails
    """
    logger.info(f"Generating Mermaid {diagram_type} diagram")

    # Map types to Mermaid syntax hints
    type_hints = {
        "mermaid_flowchart": "Use 'flowchart TD' or 'flowchart LR' syntax",
        "mermaid_sequence": "Use 'sequenceDiagram' syntax with participants and messages",
        "mermaid_class": "Use 'classDiagram' syntax with classes and relationships",
        "mermaid_state": "Use 'stateDiagram-v2' syntax with states and transitions",
        "mermaid_mindmap": "Use 'mindmap' syntax with root and branches",
    }

    syntax_hint = type_hints.get(diagram_type, "Use appropriate Mermaid syntax")

    generator = synalinks.Generator(
        data_model=MermaidDiagramOutput,
        language_model=language_model,
        temperature=1.0,
        instructions=f"""Generate a Mermaid diagram based on the description.

DIAGRAM TYPE: {diagram_type}
SYNTAX HINT: {syntax_hint}

REQUIREMENTS:
1. Output ONLY valid Mermaid code (no markdown code fences)
2. Keep the diagram clear and readable
3. Use meaningful node/participant names
4. Don't overcomplicate - focus on key relationships
5. Ensure proper Mermaid syntax

COMMON PATTERNS:
- flowchart TD: A[Start] --> B[Process] --> C[End]
- sequenceDiagram: participant A / A->>B: Message
- classDiagram: class Name / ClassA --|> ClassB
- stateDiagram-v2: [*] --> State1 / State1 --> State2
- mindmap: root((Topic)) / Branch1 / SubBranch

Generate clean, syntactically correct Mermaid code."""
    )

    input_data = MermaidDiagramInput(
        diagram_type=diagram_type,
        description=description,
        context=context
    )

    try:
        result = await generator(input_data)
        mermaid_code = result.get_json().get("mermaid_code", "")

        # Clean up the code - remove any markdown fences if present
        mermaid_code = mermaid_code.strip()
        if mermaid_code.startswith("```"):
            lines = mermaid_code.split("\n")
            mermaid_code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        return mermaid_code
    except Exception as e:
        logger.warning(f"Mermaid diagram generation failed: {e}")
        return None


async def generate_concept_image(
    description: str,
    context: str,
    chapter_name: str,
    image_number: int,
    language_model,
    output_dir: str,
    image_model: str = "gemini/imagen-3.0-generate-002"
) -> Optional[str]:
    """
    Generate a concept image using AI image generation.

    Returns:
        Path to the generated image, or None if generation fails
    """
    logger.info(f"Generating concept image for: {description[:50]}...")

    # First, use LLM to create an optimized image prompt
    prompt_generator = synalinks.Generator(
        data_model=ImagePromptOutput,
        language_model=language_model,
        temperature=1.0,
        instructions="""Create an optimized prompt for AI image generation.

The image should:
1. Visualize the concept clearly and memorably
2. Be suitable for a technical/educational book
3. Use clean, professional style (not cartoonish unless appropriate)
4. Avoid text in the image (text renders poorly)
5. Focus on visual metaphors and abstract representations

Create a detailed, specific prompt that will generate a high-quality educational illustration.
Include style guidance like: "clean illustration style", "technical diagram aesthetic", "minimalist design", etc."""
    )

    prompt_input = ImagePromptInput(
        concept_description=description,
        context=context,
        chapter_name=chapter_name
    )

    try:
        prompt_result = await prompt_generator(prompt_input)
        image_prompt = prompt_result.get_json().get("image_prompt", description)

        # Generate image using the image model
        # Note: This assumes the image model API is available through synalinks or similar
        try:
            import google.generativeai as genai
            from PIL import Image
            import io

            # Configure the image model
            imagen = genai.ImageGenerationModel(image_model.split("/")[-1])

            # Generate the image
            response = imagen.generate_images(
                prompt=image_prompt,
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_only_high",
            )

            if response.images:
                # Save the image
                safe_chapter = sanitize_filename(chapter_name)
                image_filename = f"img_{safe_chapter}_{image_number:02d}.png"
                image_path = os.path.join(output_dir, image_filename)

                # Save image from response
                response.images[0].save(image_path)

                logger.info(f"Generated image: {image_filename}")
                return image_path

        except ImportError:
            logger.warning("google-generativeai not available for image generation")
            return None
        except Exception as e:
            logger.warning(f"Image generation failed: {e}")
            return None

    except Exception as e:
        logger.warning(f"Image prompt generation failed: {e}")
        return None


def embed_mermaid_in_content(content: str, location_text: str, mermaid_code: str, caption: str) -> str:
    """
    Embed a Mermaid diagram in the content after the specified location.

    Returns:
        Content with embedded Mermaid diagram
    """
    if not location_text or not mermaid_code:
        return content

    # Create the Mermaid block
    mermaid_block = f"\n\n```mermaid\n{mermaid_code}\n```\n*{caption}*\n\n"

    # Find and insert after the location text
    # Try exact match first
    if location_text in content:
        return content.replace(location_text, location_text + mermaid_block, 1)

    # Try finding a partial match (first 100 chars)
    partial = location_text[:100] if len(location_text) > 100 else location_text
    if partial in content:
        # Find the end of the paragraph
        idx = content.find(partial)
        end_idx = content.find("\n\n", idx)
        if end_idx == -1:
            end_idx = len(content)
        return content[:end_idx] + mermaid_block + content[end_idx:]

    # If no match found, append at the end of the section
    logger.warning(f"Could not find location for diagram, appending to content")
    return content + mermaid_block


def embed_image_in_content(content: str, location_text: str, image_path: str, caption: str) -> str:
    """
    Embed an image in the content after the specified location.

    Returns:
        Content with embedded image
    """
    if not location_text or not image_path:
        return content

    # Create the image block (relative path for markdown)
    image_filename = os.path.basename(image_path)
    image_block = f"\n\n![{caption}]({image_filename})\n*{caption}*\n\n"

    # Find and insert after the location text
    if location_text in content:
        return content.replace(location_text, location_text + image_block, 1)

    # Try partial match
    partial = location_text[:100] if len(location_text) > 100 else location_text
    if partial in content:
        idx = content.find(partial)
        end_idx = content.find("\n\n", idx)
        if end_idx == -1:
            end_idx = len(content)
        return content[:end_idx] + image_block + content[end_idx:]

    logger.warning(f"Could not find location for image, appending to content")
    return content + image_block


async def illustrate_chapter(
    chapter_content: str,
    chapter_name: str,
    chapter_number: int,
    topic: str,
    audience: str,
    language_model,
    output_dir: str,
    enable_images: bool = True,
    image_model: str = "gemini/imagen-3.0-generate-002"
) -> str:
    """
    Add illustrations to a chapter based on LLM analysis.

    Returns:
        Chapter content with embedded illustrations
    """
    safe_chapter = sanitize_filename(chapter_name)
    illustrated_filename = f"09_illustrated_{chapter_number:03d}_{safe_chapter}.txt"
    analysis_filename = f"09_illustration_analysis_{chapter_number:03d}_{safe_chapter}.json"

    # Check for existing illustrated content
    if output_dir and output_exists(output_dir, illustrated_filename):
        existing = load_json_from_file(output_dir, illustrated_filename.replace('.txt', '.json'))
        if existing:
            logger.info(f"Loaded existing illustrated chapter: {chapter_name}")
            return existing.get("content", chapter_content)

    logger.info(f"Illustrating chapter: {chapter_name}")

    # Analyze for illustration opportunities
    opportunities = await analyze_illustration_opportunities(
        chapter_content, chapter_name, topic, audience, language_model
    )

    if output_dir:
        save_json_to_file(output_dir, analysis_filename, {"opportunities": opportunities})

    if not opportunities:
        logger.info(f"No illustration opportunities identified for: {chapter_name}")
        return chapter_content

    logger.info(f"Found {len(opportunities)} illustration opportunities")

    # Process each opportunity
    illustrated_content = chapter_content
    image_counter = 1

    for opp in opportunities:
        ill_type = opp.get("illustration_type", "")
        location = opp.get("location", "")
        description = opp.get("description", "")
        caption = opp.get("caption", description[:50] + "...")

        if ill_type.startswith("mermaid_"):
            # Generate Mermaid diagram
            mermaid_code = await generate_mermaid_diagram(
                ill_type, description, chapter_content[:500], language_model
            )
            if mermaid_code:
                illustrated_content = embed_mermaid_in_content(
                    illustrated_content, location, mermaid_code, caption
                )
                logger.info(f"Added Mermaid diagram: {caption[:30]}...")

        elif ill_type == "generated_image" and enable_images:
            # Generate AI image
            image_path = await generate_concept_image(
                description, chapter_content[:500], chapter_name,
                image_counter, language_model, output_dir, image_model
            )
            if image_path:
                illustrated_content = embed_image_in_content(
                    illustrated_content, location, image_path, caption
                )
                image_counter += 1
                logger.info(f"Added generated image: {caption[:30]}...")

    # Save the illustrated content
    if output_dir:
        save_to_file(output_dir, illustrated_filename, illustrated_content)
        save_json_to_file(
            output_dir,
            illustrated_filename.replace('.txt', '.json'),
            {"content": illustrated_content}
        )

    return illustrated_content


async def illustrate_all_chapters(
    chapters: List[tuple],
    topic: str,
    audience: str,
    language_model,
    output_dir: str,
    enable_images: bool = True,
    image_model: str = "gemini/imagen-3.0-generate-002"
) -> List[tuple]:
    """
    Add illustrations to all chapters.

    Returns:
        List of (chapter_name, illustrated_content_dict) tuples
    """
    illustrated_chapters = []

    for i, (chapter_name, chapter_data) in enumerate(chapters, 1):
        content = chapter_data.get("chapter_content", "")

        if not content:
            illustrated_chapters.append((chapter_name, chapter_data))
            continue

        try:
            illustrated_content = await illustrate_chapter(
                content, chapter_name, i, topic, audience,
                language_model, output_dir, enable_images, image_model
            )
            illustrated_chapters.append((chapter_name, {"chapter_content": illustrated_content}))
        except Exception as e:
            logger.warning(f"Illustration failed for chapter {i}: {e}")
            illustrated_chapters.append((chapter_name, chapter_data))

    return illustrated_chapters
