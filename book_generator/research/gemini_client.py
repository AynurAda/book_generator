"""
Gemini Deep Research API client.

This is the only part that doesn't use Synalinks - it uses
the native Gemini Interactions API for deep research.
"""

import os
import time
import json
import asyncio
import logging
from typing import Dict, List, Optional
from pathlib import Path

from google import genai

logger = logging.getLogger(__name__)


class DeepResearchClient:
    """Wrapper for Gemini Deep Research API."""

    AGENT = "deep-research-pro-preview-12-2025"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the client.

        Args:
            api_key: Gemini API key. If not provided, uses GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY env var or pass api_key."
            )
        self.client = genai.Client(api_key=self.api_key)

    async def research(
        self,
        query: str,
        timeout: int = 1800,
        poll_interval: int = 10,
    ) -> str:
        """
        Run a deep research query and return the result.

        Args:
            query: The research question
            timeout: Maximum time to wait in seconds (default 30 min)
            poll_interval: Seconds between status checks

        Returns:
            The research output text
        """
        logger.info(f"Starting deep research: {query[:100]}...")

        interaction = self.client.interactions.create(
            input=query,
            agent=self.AGENT,
            background=True,
        )

        logger.info(f"Research job created: {interaction.id}")

        start_time = time.time()

        while True:
            interaction = self.client.interactions.get(interaction.id)
            elapsed = time.time() - start_time

            if interaction.status == "completed":
                logger.info(f"Research completed in {elapsed:.0f}s")
                if hasattr(interaction, "outputs") and interaction.outputs:
                    return interaction.outputs[-1].text
                return ""

            elif interaction.status == "failed":
                error = getattr(interaction, "error", "Unknown error")
                logger.error(f"Research failed: {error}")
                raise Exception(f"Deep research failed: {error}")

            if elapsed > timeout:
                logger.error(f"Research timed out after {timeout}s")
                raise Exception(f"Deep research timed out after {timeout}s")

            logger.debug(f"Status: {interaction.status} ({elapsed:.0f}s)")
            await asyncio.sleep(poll_interval)

    async def research_all(
        self,
        queries: List[str],
        cache_dir: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Run multiple research queries sequentially.

        Args:
            queries: List of research questions
            cache_dir: Optional directory to cache results

        Returns:
            Dict mapping query index to result text
        """
        results = {}

        for i, query in enumerate(queries):
            cache_file = None
            if cache_dir:
                cache_file = Path(cache_dir) / f"research_query_{i}.txt"
                if cache_file.exists():
                    logger.info(f"Loading cached result for query {i}")
                    results[f"query_{i}"] = cache_file.read_text()
                    continue

            logger.info(f"Running query {i + 1}/{len(queries)}")

            try:
                result = await self.research(query)
                results[f"query_{i}"] = result

                if cache_file:
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(result)
                    logger.info(f"Cached result to {cache_file}")

            except Exception as e:
                logger.error(f"Query {i} failed: {e}")
                results[f"query_{i}"] = f"ERROR: {e}"

        return results

    async def research_all_parallel(
        self,
        queries: List[str],
        cache_dir: Optional[str] = None,
        max_concurrent: int = 3,
    ) -> Dict[str, str]:
        """
        Run multiple research queries in parallel.

        Args:
            queries: List of research questions
            cache_dir: Optional directory to cache results
            max_concurrent: Maximum concurrent requests

        Returns:
            Dict mapping query index to result text
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(i: int, query: str) -> tuple:
            async with semaphore:
                cache_file = None
                if cache_dir:
                    cache_file = Path(cache_dir) / f"research_query_{i}.txt"
                    if cache_file.exists():
                        logger.info(f"Loading cached result for query {i}")
                        return f"query_{i}", cache_file.read_text()

                try:
                    result = await self.research(query)

                    if cache_file:
                        cache_file.parent.mkdir(parents=True, exist_ok=True)
                        cache_file.write_text(result)

                    return f"query_{i}", result
                except Exception as e:
                    logger.error(f"Query {i} failed: {e}")
                    return f"query_{i}", f"ERROR: {e}"

        tasks = [run_with_semaphore(i, q) for i, q in enumerate(queries)]
        results_list = await asyncio.gather(*tasks)

        return dict(results_list)
