"""
Book cover generation using AI image models.

Uses Synalinks to dynamically generate cover prompts based on
the book's content, then generates the image with the configured model.
"""

import os
import logging
from typing import Optional, Literal

import synalinks

from .models import CoverPromptInput, CoverPromptOutput

logger = logging.getLogger(__name__)

CoverStyle = Literal[
    "humorous",      # New Yorker editorial cartoon style
    "abstract",      # Clean geometric shapes, modern
    "cyberpunk",     # Neon, dark, Love Death Robots style
    "minimalist",    # Ultra-clean, single focal point
    "watercolor",    # Soft, artistic, painterly
    "vintage",       # Retro scientific illustration
    "blueprint",     # Technical drawing aesthetic
    "surreal",       # Dali-esque dreamlike imagery
    "isometric",     # 3D isometric technical art
    "papercraft",    # Paper cut-out layered style
    "neon_noir",     # Dark with glowing elements
    "botanical",     # Nature-inspired scientific illustration
    "bauhaus",       # Bold geometric Bauhaus style
    "pixel_art",     # Retro 8-bit/16-bit aesthetic
    "art_deco",      # 1920s glamorous geometric
]

STYLE_INSTRUCTIONS = {
    "humorous": """Editorial cartoon illustration, New Yorker magazine style, muted watercolor palette.
Create a witty visual metaphor or clever scene that captures the essence of the book's topic.
Use anthropomorphized objects or clever visual puns. Charming character design, genuinely funny visual storytelling.
Soft colors, clean lines, whimsical but intelligent humor.""",

    "abstract": """Clean, modern abstract book cover art.
Use geometric shapes, gradients, and a sophisticated color palette.
Create an evocative composition that suggests the book's themes without being literal.
Professional, striking, suitable for a technical audience. Minimal but impactful.""",

    "cyberpunk": """Cinematic illustration in the style of Love Death and Robots animated anthology.
High contrast lighting with dramatic shadows. Cyberpunk and sci-fi aesthetic.
Rich saturated colors with neon accents (deep purples, electric blues, hot pinks).
Dark, moody atmosphere with glowing elements. Photorealistic yet stylized digital art.""",

    "minimalist": """Ultra-minimalist book cover design.
Single powerful focal element on a clean background. Maximum negative space.
One or two colors only. The visual should be immediately recognizable and memorable.
Scandinavian design sensibility - less is more. Bold, confident, sophisticated.""",

    "watercolor": """Soft, ethereal watercolor illustration.
Flowing colors that blend organically. Artistic and contemplative mood.
Suggest the book's themes through abstract or semi-abstract forms.
Gentle color palette with occasional bold accents. Painterly texture visible.""",

    "vintage": """Vintage scientific illustration style, 19th century aesthetic.
Detailed line work with subtle color washes. Reminiscent of old encyclopedia plates.
Elegant, scholarly, timeless quality. Sepia or muted earth tones with occasional color.
Cross-hatching and fine detail work. Frames or borders optional.""",

    "blueprint": """Technical blueprint or architectural drawing aesthetic.
White or light lines on deep blue background. Grid lines and measurement marks.
Schematic representations of concepts from the book. Engineering precision.
Technical annotations (but NO readable text). Clean, precise, authoritative.""",

    "surreal": """Surrealist art style inspired by Dalí and Magritte.
Dreamlike imagery with unexpected juxtapositions. Photorealistic rendering of impossible scenes.
Visual metaphors made literal. Thought-provoking and slightly unsettling.
Rich colors, dramatic lighting, meticulous detail in service of the impossible.""",

    "isometric": """Isometric 3D illustration style.
Technical but approachable. Clean lines and flat colors with subtle shading.
Build a scene or system that represents the book's concepts.
Video game aesthetic meets technical diagram. Engaging and detailed.""",

    "papercraft": """Paper cut-out layered illustration style.
Visible layers creating depth. Soft shadows between paper layers.
Textured paper surfaces. Handcrafted, tactile quality.
Warm, inviting, artistic. Colors should feel like quality craft paper.""",

    "neon_noir": """Dark noir aesthetic with neon lighting accents.
Predominantly black and very dark colors. Selective neon glows in cyan, magenta, or orange.
Mysterious, sophisticated, high-tech feeling. Urban night atmosphere.
Strong contrast between darkness and light sources. Cinematic mood.""",

    "botanical": """Scientific botanical illustration meets the book's topic.
Detailed naturalistic rendering. Concepts visualized as organic forms or ecosystems.
Elegant scientific accuracy. Cream or white background.
Fine linework with delicate color. Museum-quality natural history aesthetic.""",

    "bauhaus": """Bold Bauhaus design movement style.
Primary colors (red, blue, yellow) plus black on white or cream.
Strong geometric shapes - circles, triangles, rectangles.
Typography-inspired composition (but NO actual text).
Confident, revolutionary, timeless modernist design.""",

    "pixel_art": """High-quality pixel art illustration.
16-bit era video game aesthetic but with sophisticated composition.
Limited but well-chosen color palette. Visible pixels as intentional style choice.
Nostalgic yet fresh. Scene or character that represents the book's themes.""",

    "art_deco": """Glamorous Art Deco style from the 1920s-30s.
Bold geometric patterns, symmetry, and elegant lines.
Gold, black, cream, and jewel tones. Sunburst motifs, stepped forms.
Luxurious and sophisticated. Gatsby-era elegance meets the book's topic.""",
}


def add_text_overlay(
    image_path: str,
    output_path: str,
    title: str,
    subtitle: str,
    authors: str
) -> str:
    """
    Add title, subtitle, and author text to a cover image.

    Args:
        image_path: Path to the source image
        output_path: Path to save the final cover
        title: Book title
        subtitle: Book subtitle
        authors: Author names

    Returns:
        Path to the final cover image
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow not installed. Skipping text overlay.")
        return image_path

    img = Image.open(image_path)
    width, height = img.size

    # Calculate font sizes based on image dimensions
    title_size = int(height * 0.036)
    subtitle_size = int(height * 0.021)
    author_size = int(height * 0.019)

    # Try to find system fonts
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]

    title_font = subtitle_font = author_font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                title_font = ImageFont.truetype(fp, title_size)
                subtitle_font = ImageFont.truetype(fp, subtitle_size)
                author_font = ImageFont.truetype(fp, author_size)
                break
            except Exception:
                continue

    if not title_font:
        title_font = ImageFont.load_default()
        subtitle_font = author_font = title_font

    # Create semi-transparent overlay for text readability
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Bottom banner for text
    banner_height = int(height * 0.13)
    banner_y = height - banner_height
    overlay_draw.rectangle([(0, banner_y), (width, height)], fill=(40, 40, 40, 230))

    # Composite overlay onto image
    img = Image.alpha_composite(img.convert('RGBA'), overlay)
    draw = ImageDraw.Draw(img)

    # Draw title (centered)
    title_upper = title.upper()
    title_bbox = draw.textbbox((0, 0), title_upper, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (width - title_w) // 2
    title_y = banner_y + int(banner_height * 0.12)
    draw.text((title_x, title_y), title_upper, font=title_font, fill=(255, 255, 255))

    # Draw subtitle
    sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (width - sub_w) // 2
    sub_y = title_y + title_size + 4
    draw.text((sub_x, sub_y), subtitle, font=subtitle_font, fill=(200, 200, 200))

    # Draw authors
    auth_bbox = draw.textbbox((0, 0), authors, font=author_font)
    auth_w = auth_bbox[2] - auth_bbox[0]
    auth_x = (width - auth_w) // 2
    auth_y = sub_y + subtitle_size + 6
    draw.text((auth_x, auth_y), authors, font=author_font, fill=(170, 170, 170))

    # Save as RGB (PDF doesn't support RGBA)
    img.convert('RGB').save(output_path, quality=95)
    logger.info(f"Added text overlay to cover: {output_path}")

    return output_path


async def generate_cover_prompt(
    book_name: str,
    topic: str,
    goal: str,
    audience: str,
    key_concepts: str,
    style: CoverStyle,
    language_model
) -> str:
    """
    Use Synalinks to dynamically generate a cover prompt based on book content.

    Args:
        book_name: The book title
        topic: The main topic
        goal: What the book aims to teach
        audience: Target audience
        key_concepts: Main concepts/chapters
        style: The desired cover style
        language_model: Synalinks language model instance

    Returns:
        The generated image prompt
    """
    style_instruction = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["abstract"])

    generator = synalinks.Generator(
        data_model=CoverPromptOutput,
        language_model=language_model,
        instructions=f"""You are a creative director designing a book cover.

STYLE REQUIREMENT:
{style_instruction}

Your task is to create an image generation prompt that:
1. Visually represents the SPECIFIC content and themes of THIS book (not generic imagery)
2. Appeals to the target audience
3. Follows the style guidelines exactly
4. Creates a memorable, striking visual that would make someone pick up the book

Think about:
- What visual metaphor best captures this book's unique contribution?
- What would instantly communicate the subject matter to the target audience?
- How can you make abstract concepts visually concrete and interesting?

CRITICAL RULES:
- NO HUMANS or realistic human faces (unless essential to the concept - prefer objects, symbols, abstractions)
- NO TEXT, WORDS, LETTERS, or LABELS of any kind in the image
- The image must work WITHOUT the title - it should visually communicate the book's essence
- Be SPECIFIC to this book's content, not generic to the field"""
    )

    input_data = CoverPromptInput(
        book_name=book_name,
        topic=topic,
        goal=goal,
        audience=audience,
        key_concepts=key_concepts,
        cover_style=style
    )

    result = await generator(input_data)
    result_dict = result.get_json()

    prompt = result_dict.get("image_prompt", "")

    # Ensure the no-text instruction is present
    if "NO TEXT" not in prompt.upper():
        prompt += "\n\nCRITICAL: NO TEXT, NO WORDS, NO LETTERS, NO LABELS anywhere in the image."

    logger.info(f"Generated cover prompt for style '{style}':\n{prompt[:200]}...")

    return prompt


def get_cover_prompt(book_name: str, style: CoverStyle = "humorous") -> str:
    """
    DEPRECATED: Use generate_cover_prompt() for dynamic prompt generation.

    This is a fallback that returns a generic prompt.
    """
    style_instruction = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["abstract"])

    return f"""{style_instruction}

Subject: Create a compelling visual for a book titled "{book_name}".
The image should capture the essence of the subject matter in a visually striking way.

CRITICAL: NO TEXT, NO WORDS, NO LETTERS, NO LABELS anywhere in the image."""


async def generate_cover(
    book_name: str,
    subtitle: str,
    authors: str,
    output_path: str,
    style: CoverStyle = "humorous",
    topic: str = None,
    goal: str = None,
    audience: str = None,
    key_concepts: str = None,
    language_model = None,
    image_model: str = "gemini/gemini-3-pro-image-preview"
) -> Optional[str]:
    """
    Generate a book cover image.

    Uses Synalinks to dynamically generate the cover prompt based on
    the book's actual content, then generates the image.

    Args:
        book_name: The title of the book
        subtitle: The book's subtitle
        authors: The author names
        output_path: Path to save the cover image
        style: Cover style (see CoverStyle for options)
        topic: The main topic of the book (for dynamic prompt)
        goal: The goal of the book (for dynamic prompt)
        audience: Target audience (for dynamic prompt)
        key_concepts: Main concepts/chapters (for dynamic prompt)
        language_model: Synalinks language model (for dynamic prompt)
        image_model: The image generation model to use

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

    logger.info(f"Generating {style} book cover with {image_model}...")

    # Generate prompt dynamically if we have the required context
    if language_model and topic and goal:
        prompt = await generate_cover_prompt(
            book_name=book_name,
            topic=topic,
            goal=goal,
            audience=audience or "technical readers",
            key_concepts=key_concepts or "",
            style=style,
            language_model=language_model
        )
    else:
        # Fallback to generic prompt
        logger.info("Using fallback cover prompt (no language model provided)")
        prompt = get_cover_prompt(book_name, style)

    # Save the prompt for debugging
    output_dir = os.path.dirname(output_path)
    if output_dir:
        prompt_path = os.path.join(output_dir, "cover_prompt.txt")
        with open(prompt_path, 'w') as f:
            f.write(f"Style: {style}\nModel: {image_model}\n\n{prompt}")
        logger.info(f"Cover prompt saved to: {prompt_path}")

    client = genai.Client(api_key=api_key)

    # Extract model name (remove prefix like "gemini/")
    model_id = image_model.split("/")[-1] if "/" in image_model else image_model

    # Ensure output directory exists
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    temp_path = output_path.replace('.png', '_illustration.png')

    try:
        # Use generate_content API for Gemini models
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            )
        )

        # Extract image from response
        image_saved = False
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    import base64
                    image_data = part.inline_data.data
                    if isinstance(image_data, str):
                        image_data = base64.b64decode(image_data)
                    with open(temp_path, 'wb') as f:
                        f.write(image_data)
                    logger.info(f"Cover illustration saved to: {temp_path}")
                    image_saved = True
                    break

        if image_saved:
            add_text_overlay(temp_path, output_path, book_name, subtitle, authors)
            if os.path.exists(temp_path) and temp_path != output_path:
                os.remove(temp_path)
            return output_path
        else:
            logger.warning("No cover image generated")
            return None

    except Exception as e:
        logger.warning(f"Cover generation failed: {e}")
        return None


def list_cover_styles() -> list[str]:
    """Return list of available cover styles."""
    return list(STYLE_INSTRUCTIONS.keys())
