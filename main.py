#!/usr/bin/env python3
"""
Book Generator - AI-powered book generation using Synalinks.

Usage:
    python main.py                     # Run with default configuration
    python main.py --test              # Run in test mode (limited chapters)
    python main.py --resume <dir>      # Resume from a previous run

Example configurations can be set in the CONFIG dictionary below.
"""

import asyncio
import argparse
import sys

from book_generator.config import Config
from book_generator.pipeline import generate_book


# =============================================================================
# CONFIGURATION
# =============================================================================
# Modify this dictionary to configure your book generation

CONFIG = {
    # Book metadata
    "topic": "Neuro-symbolic AI",
    "goal": "a comprehensive handbook of neurosymbolic AI covering main concepts for building neurosymbolic programs. Focus on concepts, not deployment or ethics.",
    "book_name": "Neurosymbolic AI Handbook",
    "subtitle": "Advances in Neurosymbolic AI in the Age of LLMs",
    "authors": "Aynur Adanbekova, Gemini & Claude",
    "audience": "ML researchers and practitioners who want to understand and build neuro-symbolic systems",

    # Generation settings
    "test_mode": False,
    "test_max_chapters": 1,
    "resume_from_dir": 'output/20260130_203255',  # Set to "output/YYYYMMDD_HHMMSS" to resume

    # Model settings
    "model_name": "gemini/gemini-3-flash-preview",

    # Writing style (None for no styling, or one of:)
    # - "waitbutwhy": Conversational, simple language, breaks down complex topics
    # - "for_dummies": Step-by-step, assumes no prior knowledge, friendly
    # - "oreilly": Technical but clear, practical focus, for practitioners
    # - "textbook": Rigorous and structured, academic style
    # - "practical": Minimal theory, focused on application
    "author_key": "waitbutwhy",

    # Illustration settings
    "enable_illustrations": True,  # Set to True to add Mermaid diagrams and images
    "enable_generated_images": True,  # Set to False for Mermaid diagrams only
    "image_model": "gemini/imagen-3.0-generate-002",  # AI image generation model
}


# =============================================================================
# MAIN
# =============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a comprehensive book using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          Generate book with default config
  python main.py --test                   Test mode (2 chapters only)
  python main.py --resume output/20240115_143022  Resume from previous run
        """
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode with limited chapters"
    )
    parser.add_argument(
        "--resume",
        type=str,
        metavar="DIR",
        help="Resume from a previous output directory"
    )
    parser.add_argument(
        "--chapters",
        type=int,
        default=2,
        help="Number of chapters in test mode (default: 2)"
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Create configuration from defaults
    config = Config.from_dict(CONFIG)

    # Override with command line arguments
    if args.test:
        config.test_mode = True
        config.test_max_chapters = args.chapters

    if args.resume:
        config.resume_from_dir = args.resume

    # Display configuration
    print("=" * 60)
    print("BOOK GENERATOR")
    print("=" * 60)
    print(f"Topic: {config.topic}")
    print(f"Book Name: {config.book_name}")
    print(f"Audience: {config.audience}")
    print(f"Test Mode: {config.test_mode}")
    if config.author_key:
        from book_generator.authors import get_writing_style
        style = get_writing_style(config.author_key)
        if style:
            print(f"Writing Style: {config.author_key} - {style.description}")
    if config.enable_illustrations:
        print(f"Illustrations: Enabled (images: {config.enable_generated_images})")
    if config.resume_from_dir:
        print(f"Resuming from: {config.resume_from_dir}")
    print("=" * 60)
    print()

    # Generate the book
    try:
        pdf_path = await generate_book(config)
        print()
        print("=" * 60)
        print("SUCCESS!")
        print(f"Book generated at: {pdf_path}")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\nGeneration interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during generation: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
