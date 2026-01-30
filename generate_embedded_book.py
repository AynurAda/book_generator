#!/usr/bin/env python3
"""
Embedded Systems Architecture Book Generator

Generates a comprehensive book covering:
- Embedded SW Architecture (Bare metal, RTOS, Scheduling, HAL)
- AUTOSAR Classic Architecture
- Real-Time Constraints
- HPC Hardware Platforms
"""

import asyncio
import sys

from book_generator.config import Config
from book_generator.pipeline import generate_book


CONFIG = {
    # Book metadata
    "topic": "Embedded Systems Architecture",
    "goal": """A comprehensive handbook covering embedded software architecture and real-time systems.

The book should cover:
1. Embedded SW Architecture fundamentals:
   - Bare metal vs. RTOS comparison (FreeRTOS, Zephyr, VxWorks, QNX, etc.)
   - Scheduling models: cyclic executive, event-driven, time-triggered architectures
   - Software layers: device drivers, Hardware Abstraction Layer (HAL), middleware

2. AUTOSAR Classic Architecture:
   - Runtime Environment (RTE) and Basic Software (BSW) structure
   - Software Components (SWCs) and their compositions
   - Timing concepts, runnables, and scheduling
   - Diagnostics stack (UDS, DTC) and communication stack (CAN, LIN, FlexRay, Ethernet)

3. Real-Time Constraints:
   - Determinism and predictability requirements
   - Worst-Case Execution Time (WCET) analysis methods
   - Low-level timing design, budgeting, and verification

4. HPC Hardware Platforms for Embedded:
   - Multi-core CPU architectures and their challenges
   - GPU computing and hardware accelerators (DSP, NPU, FPGA)
   - Memory hierarchy, caches, and memory-mapped I/O
   - Virtualization and hypervisors in embedded systems

Focus on practical knowledge for embedded systems engineers. Include architecture diagrams, timing diagrams, and real-world examples.""",

    "book_name": "Embedded Systems Architecture Handbook",
    "subtitle": "From Bare Metal to AUTOSAR and Real-Time HPC",
    "authors": "Yernar Nukezhanov",
    "audience": "Embedded systems engineers, automotive software developers, and real-time systems practitioners who want to understand modern embedded architectures from low-level drivers to AUTOSAR and high-performance computing platforms",

    # Generation settings
    "test_mode": True,
    "test_max_chapters": 2,
    "resume_from_dir": None,

    # Model settings
    "model_name": "gemini/gemini-3-flash-preview",

    # Writing style
    "author_key": "waitbutwhy",  # O'Reilly technical book style - practical and clear

    # Illustration settings
    "enable_illustrations": True,
    "enable_generated_images": True,  # Mermaid diagrams only for technical content
    "image_model": "gemini/gemini-3-pro-image-preview",
}


async def main():
    """Main entry point."""
    config = Config.from_dict(CONFIG)

    # Display configuration
    print("=" * 60)
    print("EMBEDDED SYSTEMS ARCHITECTURE BOOK GENERATOR")
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
