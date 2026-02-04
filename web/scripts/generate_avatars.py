#!/usr/bin/env python3
"""
Generate avatar images for user stories using Gemini Imagen 4.
"""

import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from google import genai
from google.genai import types

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# User stories with descriptions for avatar generation
USER_STORIES = [
    {
        "name": "aynur",
        "prompt": "Professional headshot portrait of a confident woman in her early 30s, South Asian or Middle Eastern appearance, wearing smart business casual attire, warm smile, working in a modern office with trading screens in background, soft natural lighting, photorealistic style, warm color tones"
    },
    {
        "name": "marina",
        "prompt": "Portrait of a strong Brazilian woman in her 40s, determined expression showing hope and resilience, warm brown skin, sitting in a cozy home environment with sunlight streaming through window, wearing comfortable casual clothes, photorealistic style, warm golden lighting"
    },
    {
        "name": "james",
        "prompt": "Portrait of a middle-aged African American man in his 50s, kind eyes with slight weathered look, transitioning from factory worker to tech, wearing a mix of work shirt and modern hoodie, in a workshop/home office hybrid space, photorealistic style, warm industrial lighting"
    },
    {
        "name": "amir",
        "prompt": "Portrait of a young Bangladeshi man around 18-20 years old, bright eager eyes, student studying hard, surrounded by books and a laptop, modest home environment in South Asia, wearing simple casual clothes, natural warm lighting, photorealistic style"
    },
    {
        "name": "marcus",
        "prompt": "Portrait of a confident white American man in his 30s, entrepreneur vibe, slightly messy creative look, in a modern startup office, casual but stylish clothing, warm genuine smile, photorealistic style, bright natural lighting"
    },
    {
        "name": "priya",
        "prompt": "Portrait of an Indian woman journalist in her early 30s, intelligent and passionate expression, wearing professional but comfortable clothing, in a newsroom or home office with notes and research visible, warm lighting, photorealistic style"
    },
    {
        "name": "anna",
        "prompt": "Portrait of a young white woman scientist in her late 20s, wearing a lab coat over casual clothes, in a biology lab with microscopes and screens showing DNA sequences, focused but friendly expression, photorealistic style, cool blue lab lighting with warm accents"
    },
    {
        "name": "sofia",
        "prompt": "Portrait of a young Latina college student around 19-20, hopeful and determined expression, first-generation college student vibe, in a campus library or dorm room studying, casual student attire, warm natural lighting, photorealistic style"
    },
    {
        "name": "kofi",
        "prompt": "Portrait of a Ghanaian man in his 30s, small business owner, warm friendly smile, in his tailor shop with colorful African fabrics visible in background, wearing traditional African print shirt, natural warm lighting, photorealistic style"
    },
    {
        "name": "rachel",
        "prompt": "Portrait of an Australian woman in her late 20s, gentle tired but hopeful expression, living with chronic illness, in a comfortable cozy home setup with soft blankets, wearing comfortable loungewear, soft warm lighting, photorealistic style"
    },
    {
        "name": "david",
        "prompt": "Portrait of a British man in his 30s who is deaf, confident entrepreneurial expression, using sign language or near a laptop, modern home office, professional but approachable style, warm natural lighting, photorealistic style"
    },
    {
        "name": "mira",
        "prompt": "Portrait of a young South Asian Canadian woman around 22, accounting student, slightly stressed but optimistic expression, surrounded by textbooks and notes, in a library or study space, wearing casual student clothes, warm lighting, photorealistic style"
    },
]

def generate_avatar(user: dict, output_dir: Path) -> str | None:
    """Generate an avatar image for a user story."""
    name = user["name"]
    prompt = user["prompt"]
    output_path = output_dir / f"{name}.png"

    if output_path.exists():
        print(f"  Skipping {name} (already exists)")
        return str(output_path)

    print(f"  Generating avatar for {name}...")

    try:
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",  # Square for avatars
            )
        )

        if response.generated_images:
            image = response.generated_images[0]
            image.image.save(str(output_path))
            print(f"  ✓ Saved {name}.png")
            return str(output_path)
        else:
            print(f"  ✗ No image generated for {name}")
            return None

    except Exception as e:
        print(f"  ✗ Error generating {name}: {e}")
        return None


def main():
    # Output directory
    output_dir = Path(__file__).parent.parent / "public" / "avatars"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating avatars to: {output_dir}")
    print(f"Found {len(USER_STORIES)} user stories\n")

    generated = 0
    for user in USER_STORIES:
        result = generate_avatar(user, output_dir)
        if result:
            generated += 1

    print(f"\nDone! Generated {generated}/{len(USER_STORIES)} avatars")
    print(f"Images saved to: {output_dir}")


if __name__ == "__main__":
    main()
