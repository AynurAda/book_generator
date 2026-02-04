#!/usr/bin/env python3
"""
Book Generator - AI-powered book generation using Synalinks.

Usage:
    python main.py --config configs/ai_agent_memory.yaml
    python main.py --config configs/neurosymbolic.yaml --chapters 5
    python main.py --config configs/embedded_systems.yaml --resume output/20240115_143022

Available configs:
    configs/neurosymbolic.yaml      - Neurosymbolic AI Handbook
    configs/embedded_systems.yaml   - Embedded Systems Architecture Handbook
    configs/ai_agent_memory.yaml    - AI Agent Memory Handbook
"""

import asyncio
import argparse
import sys
import os

import yaml

from book_generator.config import Config
from book_generator.pipeline import generate_book


def load_config(config_path: str) -> dict:
    """Load configuration from a YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def list_configs():
    """List available config files."""
    configs_dir = os.path.join(os.path.dirname(__file__), 'configs')
    if os.path.exists(configs_dir):
        configs = [f for f in os.listdir(configs_dir) if f.endswith('.yaml')]
        return configs
    return []


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate a comprehensive book using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --config configs/ai_agent_memory.yaml
  python main.py --config configs/neurosymbolic.yaml --chapters 5
  python main.py --config configs/embedded_systems.yaml -n 3
  python main.py --list                              List available configs
        """
    )

    parser.add_argument(
        "--config", "-c",
        type=str,
        metavar="FILE",
        help="Path to YAML config file (e.g., configs/ai_agent_memory.yaml)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available config files"
    )
    parser.add_argument(
        "--resume", "-r",
        type=str,
        metavar="DIR",
        help="Resume from a previous output directory"
    )
    parser.add_argument(
        "--chapters", "-n",
        type=int,
        default=None,
        help="Limit to N chapters (default: all chapters)"
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # List configs if requested
    if args.list:
        print("Available configs:")
        for config_file in list_configs():
            print(f"  configs/{config_file}")
        sys.exit(0)

    # Require config file
    if not args.config:
        print("Error: --config is required")
        print("Use --list to see available configs")
        print("Example: python main.py --config configs/ai_agent_memory.yaml")
        sys.exit(1)

    # Load config from file
    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)

    config_dict = load_config(args.config)
    config = Config.from_dict(config_dict)

    # Backward compatibility: if test_mode is set in config, use test_max_chapters
    if config.test_mode and config.num_chapters is None:
        config.num_chapters = config.test_max_chapters

    # Override with command line arguments (CLI takes precedence)
    if args.chapters:
        config.num_chapters = args.chapters

    if args.resume:
        config.resume_from_dir = args.resume

    # Display configuration
    print("=" * 60)
    print("BOOK GENERATOR")
    print("=" * 60)
    print(f"Config: {args.config}")
    print(f"Topic: {config.topic}")
    print(f"Book Name: {config.book_name}")
    print(f"Audience: {config.audience}")
    print(f"Chapters: {config.num_chapters or 'all'}")
    if config.author_key:
        from book_generator.authors import get_author_profile
        style = get_author_profile(config.author_key)
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
