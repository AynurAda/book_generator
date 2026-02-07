"""
Stage 2 Research Pipeline using mcp-graphiti via Synalinks MCP.

This module provides knowledge graph integration for the book generator:
- Connects to mcp-graphiti MCP server using Synalinks' MultiServerMCPClient
- Adds papers to the knowledge graph as memories
- Searches for relationships and entities
- Provides research context for chapter writing
- Uses LLM-generated queries for smart knowledge graph search

mcp-graphiti MCP Tools (actual names with graphiti_ prefix):
- graphiti_add_memory: Add content to knowledge graph
- graphiti_search_nodes: Find entity nodes
- graphiti_search_memory_facts: Find relationships/facts
- graphiti_get_episodes: Retrieve recent episodes
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Union

import synalinks

logger = logging.getLogger(__name__)


# =============================================================================
# Synalinks DataModels for Smart Query Generation
# =============================================================================

class SectionQueryInput(synalinks.DataModel):
    """Input for generating KG search queries."""
    chapter_name: str = synalinks.Field(description="Name of the chapter")
    section_name: str = synalinks.Field(description="Name of the section")
    section_plan: str = synalinks.Field(description="Full section plan with objectives and key points")
    book_topic: str = synalinks.Field(description="The book's main topic for context")


class KGSearchQueries(synalinks.DataModel):
    """Generated queries for knowledge graph search."""
    queries: List[str] = synalinks.Field(
        description="3 targeted search queries to find relevant research facts. "
                    "Each query should be specific and target different aspects: "
                    "methods, papers, concepts, or applications."
    )
    paper_titles: List[str] = synalinks.Field(
        description="Specific paper titles mentioned in the section plan that should be searched. "
                    "Extract exact or partial titles of academic papers referenced."
    )


QUERY_GENERATION_INSTRUCTIONS = """Generate search queries for a knowledge graph containing academic research on the book's topic.

The knowledge graph stores:
- FACTS: Relationships between concepts (e.g., "Transformers use self-attention")
- ENTITIES: Concepts, methods, papers, researchers

Generate 3 targeted queries that will retrieve relevant facts for writing this section.
Each query should:
1. Be specific to concepts/methods in the section plan
2. Target different aspects (theory, implementation, applications)
3. Use technical terminology from the field

Also extract any paper titles mentioned in the section plan for direct lookup."""


# Query cache to avoid regenerating queries for similar sections
_query_cache: Dict[str, KGSearchQueries] = {}


def parse_mcp_result(result: Any) -> Union[List, Dict, str, None]:
    """
    Parse MCP tool result into usable Python data.

    MCP tools return various formats:
    - JsonDataModel with .json or .get_json() method
    - {'response': '{json string}'} - Synalinks MCP wrapper format
    - TextContent objects with text field
    - Lists of TextContent
    - Direct JSON data
    - Wrapped in 'content' field

    Args:
        result: Raw MCP tool result

    Returns:
        Parsed data (list, dict, or string)
    """
    if result is None:
        return None

    # Handle Synalinks JsonDataModel objects
    if hasattr(result, 'get_json'):
        result = result.get_json()
    elif hasattr(result, 'json') and isinstance(getattr(result, 'json'), dict):
        result = result.json

    # If already a list or dict
    if isinstance(result, (list, dict)):
        # Check if it's a list of content objects
        if isinstance(result, list) and len(result) > 0:
            first = result[0]
            if hasattr(first, 'text'):
                # List of TextContent - extract and parse text
                texts = [getattr(item, 'text', str(item)) for item in result]
                combined = "\n".join(texts)
                try:
                    return json.loads(combined)
                except json.JSONDecodeError:
                    return texts

        # Handle Synalinks MCP wrapper format: {'response': '{json}'}
        if isinstance(result, dict) and 'response' in result:
            response = result['response']
            if isinstance(response, str):
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return response
            return response

        return result

    # If it has a 'content' attribute (MCP response)
    if hasattr(result, 'content'):
        content = result.content
        if isinstance(content, list):
            # List of TextContent objects
            texts = []
            for item in content:
                if hasattr(item, 'text'):
                    texts.append(item.text)
                else:
                    texts.append(str(item))
            combined = "\n".join(texts)
            try:
                return json.loads(combined)
            except json.JSONDecodeError:
                return texts if len(texts) > 1 else (texts[0] if texts else None)
        return content

    # If it has a 'text' attribute (TextContent)
    if hasattr(result, 'text'):
        text = result.text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    # Try to parse as JSON string
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result

    # Last resort - convert to string
    return str(result)


class Stage2MCPPipeline:
    """
    Stage 2 research pipeline using Graphiti via MCP.

    Synalinks Integration:
    - MultiServerMCPClient: Connects to mcp-graphiti MCP server
    - Tool.call(): Directly invokes MCP tools (graphiti_add_memory, graphiti_search_memory_facts, etc.)

    Usage:
        pipeline = Stage2MCPPipeline(graphiti_url="http://localhost:8000/mcp/")
        if await pipeline.initialize():
            await pipeline.add_paper(paper_dict)
            context = await pipeline.get_context_for_chapter("Attention Mechanisms", ["attention", "transformer"])
    """

    def __init__(
        self,
        graphiti_url: str = "http://localhost:8000/mcp/",
        group_id: str = "book_research",
    ):
        """
        Initialize the Stage 2 pipeline.

        Args:
            graphiti_url: URL of the mcp-graphiti HTTP endpoint
            group_id: Namespace for this book's research in the knowledge graph
        """
        self.graphiti_url = graphiti_url
        self.group_id = group_id
        self.mcp_client = None
        self.tools: Dict[str, Any] = {}
        self.connected: bool = False

    async def initialize(self) -> bool:
        """
        Connect to mcp-graphiti MCP server.

        Returns:
            True if connected successfully, False if server unavailable
        """
        try:
            import synalinks

            logger.info(f"[KG] Connecting to mcp-graphiti at {self.graphiti_url}...")

            # Synalinks MCP client connects to the server
            self.mcp_client = synalinks.MultiServerMCPClient({
                "graphiti": {
                    "url": self.graphiti_url,
                    "transport": "streamable_http",
                },
            })

            # Get all available MCP tools
            all_tools = await self.mcp_client.get_tools()

            # Index tools by name for easy access
            for tool in all_tools:
                self.tools[tool.name] = tool

            self.connected = True
            logger.info(f"[KG] ✓ Connected to mcp-graphiti successfully!")
            logger.info(f"[KG]   → {len(self.tools)} tools available")
            logger.info(f"[KG]   → Tools: {', '.join(sorted(self.tools.keys()))}")
            return True

        except ImportError:
            logger.warning("[KG] ✗ Synalinks not installed or MultiServerMCPClient not available")
            self.connected = False
            return False
        except Exception as e:
            logger.warning(f"[KG] ✗ Could not connect to mcp-graphiti: {e}")
            logger.info("[KG] Stage 2 will use arXiv data only (no knowledge graph)")
            self.connected = False
            return False

    async def close(self):
        """Close the MCP client connection."""
        if self.mcp_client:
            try:
                logger.info("[KG] Closing MCP client connection...")
                await self.mcp_client.close()
                logger.info("[KG] ✓ MCP client connection closed")
            except Exception as e:
                logger.debug(f"[KG] Error closing MCP client: {e}")
            self.mcp_client = None
            self.connected = False

    async def add_paper(self, paper: dict, full_text: str = "") -> Optional[dict]:
        """
        Add a paper to the Graphiti knowledge graph.

        Uses the 'add_memory' MCP tool from mcp-graphiti.

        Args:
            paper: Paper dict with title, authors, year, abstract, method, significance
            full_text: Optional full text of the paper

        Returns:
            Result dict from add_memory, or None if failed
        """
        if not self.connected:
            return None

        add_memory = self.tools.get("graphiti_add_memory")
        if not add_memory:
            logger.error("graphiti_add_memory tool not found in mcp-graphiti")
            logger.error(f"Available tools: {list(self.tools.keys())}")
            return None

        # Build structured content
        content = {
            "type": "academic_paper",
            "title": paper.get("title", "Unknown"),
            "authors": paper.get("authors", "Unknown"),
            "year": paper.get("year", 2024),
            "venue": paper.get("venue", "Unknown"),
            "abstract": paper.get("abstract", ""),
            "problem": paper.get("problem", ""),
            "method": paper.get("method", ""),
            "results": paper.get("results", ""),
            "significance": paper.get("significance", ""),
        }

        if full_text:
            # Limit full text to avoid token limits
            content["full_text"] = full_text[:30000]

        try:
            # Build episode body as JSON string
            episode_body = json.dumps(content)
            paper_title = paper.get("title", "Unknown Paper")

            logger.info(f"[KG] Adding paper: '{paper_title[:60]}...'")
            logger.info(f"[KG]   → group_id: {self.group_id}")
            logger.info(f"[KG]   → content size: {len(episode_body)} chars")

            result = await add_memory(
                name=paper_title,
                episode_body=episode_body,
                group_id=self.group_id,
                source="json",
            )

            logger.info(f"[KG] ✓ Paper added successfully: '{paper_title[:40]}...'")
            if result:
                logger.info(f"[KG]   → result: {str(result)[:200]}")
            return result

        except Exception as e:
            logger.error(f"[KG] ✗ Failed to add paper '{paper.get('title', 'Unknown')[:40]}...': {e}")
            return None

    async def _get_fresh_tool(self, tool_name: str):
        """Get a fresh tool with an active session."""
        import synalinks

        mcp_client = synalinks.MultiServerMCPClient({
            "graphiti": {
                "url": self.graphiti_url,
                "transport": "streamable_http",
            },
        })
        tools = await mcp_client.get_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None

    async def search_research(self, query: str, max_results: int = 10) -> List[dict]:
        """
        Search the knowledge graph for relevant research.

        Uses 'search_memory_facts' MCP tool for relationship-based search.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of fact dicts from the knowledge graph
        """
        if not self.connected:
            logger.debug("[KG] search_research skipped - not connected")
            return []

        try:
            logger.info(f"[KG] Searching facts: '{query[:80]}...'")
            logger.info(f"[KG]   → group_ids: [{self.group_id}], max_facts: {max_results}")

            # Get fresh tool with active session
            search_memory_facts = await self._get_fresh_tool("graphiti_search_memory_facts")
            if not search_memory_facts:
                logger.warning("[KG] graphiti_search_memory_facts tool not found")
                return []

            # group_ids must be a list, not a single string
            results = await search_memory_facts(
                query=query,
                group_ids=[self.group_id],  # MUST be a list
                max_facts=max_results,
            )

            # DEBUG: Log raw result
            logger.info(f"[KG] Raw result type: {type(results)}")
            logger.info(f"[KG] Raw result: {str(results)[:500]}")

            # Parse MCP result into usable format
            parsed = parse_mcp_result(results)
            logger.info(f"[KG] Parsed result type: {type(parsed)}")
            logger.info(f"[KG] Parsed result: {str(parsed)[:500]}")

            # Extract fact list from parsed result
            if parsed is None:
                result_list = []
            elif isinstance(parsed, list):
                result_list = parsed
            elif isinstance(parsed, dict):
                # mcp-graphiti might return {"facts": [...]} or similar
                result_list = parsed.get("facts", parsed.get("results", parsed.get("data", [])))
                if not isinstance(result_list, list):
                    result_list = [parsed]
            elif isinstance(parsed, str):
                # If just a message like "No facts found", return empty
                if "no" in parsed.lower() and ("fact" in parsed.lower() or "found" in parsed.lower()):
                    result_list = []
                else:
                    result_list = [{"fact": parsed}]
            else:
                result_list = []

            logger.info(f"[KG] ✓ Found {len(result_list)} facts")
            for i, fact in enumerate(result_list[:3]):  # Log first 3 facts
                fact_preview = str(fact)[:100] if fact else "None"
                logger.info(f"[KG]   → fact {i+1}: {fact_preview}...")
            if len(result_list) > 3:
                logger.info(f"[KG]   → ... and {len(result_list) - 3} more facts")

            return result_list

        except Exception as e:
            logger.warning(f"[KG] ✗ Search failed: {e}")
            import traceback
            logger.debug(f"[KG] Traceback: {traceback.format_exc()}")
            return []

    async def search_entities(self, query: str, max_results: int = 10) -> List[dict]:
        """
        Search for entities in the knowledge graph.

        Uses 'search_nodes' MCP tool.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of entity dicts from the knowledge graph
        """
        if not self.connected:
            logger.debug("[KG] search_entities skipped - not connected")
            return []

        try:
            logger.info(f"[KG] Searching entities: '{query[:80]}...'")
            logger.info(f"[KG]   → group_ids: [{self.group_id}], max_nodes: {max_results}")

            # Get fresh tool with active session
            search_nodes = await self._get_fresh_tool("graphiti_search_nodes")
            if not search_nodes:
                logger.warning("[KG] graphiti_search_nodes tool not found")
                return []

            # group_ids must be a list, not a single string
            results = await search_nodes(
                query=query,
                group_ids=[self.group_id],  # MUST be a list
                max_nodes=max_results,
            )

            # Parse MCP result into usable format
            parsed = parse_mcp_result(results)
            logger.debug(f"[KG] Parsed entity result type: {type(parsed)}")

            # Extract entity list from parsed result
            if parsed is None:
                result_list = []
            elif isinstance(parsed, list):
                result_list = parsed
            elif isinstance(parsed, dict):
                # mcp-graphiti might return {"nodes": [...]} or similar
                result_list = parsed.get("nodes", parsed.get("entities", parsed.get("results", parsed.get("data", []))))
                if not isinstance(result_list, list):
                    result_list = [parsed]
            elif isinstance(parsed, str):
                # If just a message, return empty
                if "no" in parsed.lower() and ("node" in parsed.lower() or "found" in parsed.lower() or "entit" in parsed.lower()):
                    result_list = []
                else:
                    result_list = [{"name": parsed}]
            else:
                result_list = []

            logger.info(f"[KG] ✓ Found {len(result_list)} entities")
            for i, entity in enumerate(result_list[:3]):  # Log first 3 entities
                entity_preview = str(entity)[:100] if entity else "None"
                logger.info(f"[KG]   → entity {i+1}: {entity_preview}...")
            if len(result_list) > 3:
                logger.info(f"[KG]   → ... and {len(result_list) - 3} more entities")

            return result_list

        except Exception as e:
            logger.warning(f"[KG] ✗ Entity search failed: {e}")
            import traceback
            logger.debug(f"[KG] Traceback: {traceback.format_exc()}")
            return []

    async def get_context_for_chapter(
        self,
        chapter_name: str,
        key_concepts: List[str],
    ) -> str:
        """
        Get research context for writing a chapter.

        Searches the knowledge graph using multiple strategies:
        1. Search for facts (relationships)
        2. Search for entities (nodes)
        3. Combine results for comprehensive context

        Args:
            chapter_name: Name of the chapter
            key_concepts: Key concepts in the chapter

        Returns:
            Formatted context string for use in LLM prompts
        """
        if not self.connected:
            logger.debug(f"[KG] get_context_for_chapter skipped - not connected")
            return ""

        # Build search query from chapter info
        query = f"{chapter_name} {' '.join(key_concepts[:3])}"

        logger.info(f"[KG] Getting context for chapter: '{chapter_name}'")
        logger.info(f"[KG]   → key_concepts: {key_concepts[:5]}")
        logger.info(f"[KG]   → search query: '{query[:80]}...'")

        context_parts = []

        # Strategy 1: Search for facts (relationships between entities)
        facts = await self.search_research(query, max_results=50)

        if facts:
            context_parts.append("## Research Facts:")
            context_parts.append("")
            for i, fact in enumerate(facts, 1):
                if isinstance(fact, dict):
                    fact_text = fact.get("fact", str(fact))
                    context_parts.append(f"{i}. {fact_text}")
                else:
                    context_parts.append(f"{i}. {fact}")
            context_parts.append("")

        # Strategy 2: Search for entities (nodes in the graph)
        entities = await self.search_entities(query, max_results=30)

        if entities:
            context_parts.append("## Research Entities:")
            context_parts.append("")
            for i, entity in enumerate(entities, 1):
                if isinstance(entity, dict):
                    name = entity.get("name", entity.get("label", "Unknown"))
                    summary = entity.get("summary", entity.get("description", ""))
                    if summary:
                        context_parts.append(f"{i}. **{name}**: {summary[:200]}")
                    else:
                        context_parts.append(f"{i}. **{name}**")
                else:
                    context_parts.append(f"{i}. {entity}")
            context_parts.append("")

        # Strategy 3: If no facts or entities, try simpler keyword searches
        if not facts and not entities:
            # Try searching with just key concepts
            for concept in key_concepts[:3]:
                concept_facts = await self.search_research(concept, max_results=15)
                if concept_facts:
                    context_parts.append(f"## Facts for '{concept}':")
                    context_parts.append("")
                    for fact in concept_facts:
                        if isinstance(fact, dict):
                            context_parts.append(f"- {fact.get('fact', str(fact))}")
                        else:
                            context_parts.append(f"- {fact}")
                    context_parts.append("")

        if not context_parts:
            logger.info(f"[KG]   → No context found for this chapter")
            return ""

        # Build final context
        context = "\n".join(["## Research Context from Knowledge Graph:", ""] + context_parts)
        total_items = len(facts) + len(entities)
        logger.info(f"[KG] ✓ Context generated: {len(context)} chars, {total_items} items")
        logger.debug(f"[KG]   → Context preview: {context[:200]}...")

        return context

    async def generate_smart_queries(
        self,
        chapter_name: str,
        section_name: str,
        section_plan: str,
        book_topic: str,
        language_model: "synalinks.LanguageModel",
    ) -> "KGSearchQueries":
        """
        Generate smart search queries using LLM via Synalinks.

        Uses Synalinks Generator to create targeted queries based on
        section content, rather than naive string concatenation.

        Args:
            chapter_name: Name of the chapter
            section_name: Name of the section
            section_plan: Full section plan with objectives and key points
            book_topic: The book's main topic for context
            language_model: Synalinks LanguageModel for generation

        Returns:
            KGSearchQueries with targeted queries and paper titles
        """
        # Create cache key from section info
        cache_key = hashlib.md5(
            f"{chapter_name}|{section_name}|{section_plan[:500]}".encode()
        ).hexdigest()

        # Check cache first
        if cache_key in _query_cache:
            logger.info(f"[KG] Using cached queries for: '{section_name}'")
            return _query_cache[cache_key]

        logger.info(f"[KG] Generating smart queries for: '{section_name}'")
        logger.info(f"[KG]   → chapter: '{chapter_name}'")
        logger.info(f"[KG]   → book_topic: '{book_topic}'")

        try:
            # Build Synalinks Program for query generation
            inputs = synalinks.Input(data_model=SectionQueryInput)
            outputs = await synalinks.Generator(
                data_model=KGSearchQueries,
                language_model=language_model,
                instructions=QUERY_GENERATION_INSTRUCTIONS,
                temperature=1.0,
            )(inputs)

            program = synalinks.Program(
                inputs=inputs,
                outputs=outputs,
                name="kg_query_generator",
            )

            # Create input and run
            query_input = SectionQueryInput(
                chapter_name=chapter_name,
                section_name=section_name,
                section_plan=section_plan[:4000],  # Limit to avoid token overflow
                book_topic=book_topic,
            )

            result = await program(query_input)

            if result is None:
                logger.warning(f"[KG] Query generation failed, using fallback")
                # Fallback to simple queries
                fallback = KGSearchQueries(
                    queries=[
                        f"{section_name} {book_topic}",
                        chapter_name,
                        " ".join(section_name.split()[:3]),
                    ],
                    paper_titles=[],
                )
                return fallback

            # Extract result
            result_data = result.get_json()
            queries = KGSearchQueries(
                queries=result_data.get("queries", [])[:3],  # Max 3 queries
                paper_titles=result_data.get("paper_titles", []),
            )

            # Cache the result
            _query_cache[cache_key] = queries

            logger.info(f"[KG] ✓ Generated {len(queries.queries)} queries, {len(queries.paper_titles)} paper titles")
            for i, q in enumerate(queries.queries, 1):
                logger.info(f"[KG]   → Query {i}: '{q[:60]}...'")
            for title in queries.paper_titles[:3]:
                logger.info(f"[KG]   → Paper: '{title[:50]}...'")

            return queries

        except Exception as e:
            logger.warning(f"[KG] Query generation error: {e}")
            import traceback
            logger.debug(f"[KG] Traceback: {traceback.format_exc()}")
            # Fallback
            return KGSearchQueries(
                queries=[f"{section_name} {book_topic}"],
                paper_titles=[],
            )

    async def get_context_for_section(
        self,
        chapter_name: str,
        section_name: str,
        section_plan: str,
        book_topic: str,
        language_model: "synalinks.LanguageModel",
    ) -> str:
        """
        Get rich research context for writing a section using LLM-generated queries.

        This is the primary method for content generation. It:
        1. Uses Synalinks to generate smart, targeted search queries
        2. Searches for facts using each generated query
        3. Searches for paper titles mentioned in the section plan
        4. Combines all results into comprehensive context

        Args:
            chapter_name: Name of the chapter
            section_name: Name of the section
            section_plan: Full section plan with objectives and key points
            book_topic: The book's main topic
            language_model: Synalinks LanguageModel for query generation

        Returns:
            Formatted context string for use in LLM prompts
        """
        if not self.connected:
            logger.debug(f"[KG] get_context_for_section skipped - not connected")
            return ""

        logger.info(f"[KG] ═══════════════════════════════════════════════════")
        logger.info(f"[KG] Getting context for section: '{section_name}'")
        logger.info(f"[KG] ═══════════════════════════════════════════════════")

        # Step 1: Generate smart queries using Synalinks
        queries = await self.generate_smart_queries(
            chapter_name=chapter_name,
            section_name=section_name,
            section_plan=section_plan,
            book_topic=book_topic,
            language_model=language_model,
        )

        all_facts = []
        all_entities = []
        context_parts = []

        # Step 2: Search using each generated query
        for i, query in enumerate(queries.queries, 1):
            logger.info(f"[KG] Query {i}/3: '{query[:60]}...'")
            facts = await self.search_research(query, max_results=20)
            if facts:
                all_facts.extend(facts)
                logger.info(f"[KG]   → Found {len(facts)} facts")

            # Also search entities for this query
            entities = await self.search_entities(query, max_results=10)
            if entities:
                all_entities.extend(entities)

        # Step 3: Search for specific paper titles
        for title in queries.paper_titles[:5]:  # Limit to 5 paper searches
            logger.info(f"[KG] Paper search: '{title[:50]}...'")
            paper_facts = await self.search_research(title, max_results=10)
            if paper_facts:
                all_facts.extend(paper_facts)
                logger.info(f"[KG]   → Found {len(paper_facts)} facts for paper")

        # Step 4: Deduplicate facts (by string representation)
        seen_facts = set()
        unique_facts = []
        for fact in all_facts:
            fact_str = str(fact)
            if fact_str not in seen_facts:
                seen_facts.add(fact_str)
                unique_facts.append(fact)

        # Deduplicate entities
        seen_entities = set()
        unique_entities = []
        for entity in all_entities:
            entity_str = str(entity)
            if entity_str not in seen_entities:
                seen_entities.add(entity_str)
                unique_entities.append(entity)

        logger.info(f"[KG] After dedup: {len(unique_facts)} facts, {len(unique_entities)} entities")

        # Step 5: Build context
        if unique_facts:
            context_parts.append("## Research Facts:")
            context_parts.append("")
            for i, fact in enumerate(unique_facts[:50], 1):  # Limit to 50 facts
                if isinstance(fact, dict):
                    fact_text = fact.get("fact", str(fact))
                    context_parts.append(f"{i}. {fact_text}")
                else:
                    context_parts.append(f"{i}. {fact}")
            context_parts.append("")

        if unique_entities:
            context_parts.append("## Research Entities:")
            context_parts.append("")
            for i, entity in enumerate(unique_entities[:20], 1):  # Limit to 20 entities
                if isinstance(entity, dict):
                    name = entity.get("name", entity.get("label", "Unknown"))
                    summary = entity.get("summary", entity.get("description", ""))
                    if summary:
                        context_parts.append(f"{i}. **{name}**: {summary[:200]}")
                    else:
                        context_parts.append(f"{i}. **{name}**")
                else:
                    context_parts.append(f"{i}. {entity}")
            context_parts.append("")

        if not context_parts:
            logger.info(f"[KG]   → No context found for this section")
            return ""

        # Build final context
        context = "\n".join([
            "## Research Context from Knowledge Graph:",
            f"### Section: {section_name}",
            "",
        ] + context_parts)

        logger.info(f"[KG] ═══════════════════════════════════════════════════")
        logger.info(f"[KG] ✓ Section context: {len(context)} chars")
        logger.info(f"[KG]   → {len(unique_facts)} facts, {len(unique_entities)} entities")
        logger.info(f"[KG] ═══════════════════════════════════════════════════")

        return context

    async def wait_for_processing(self, max_wait_seconds: int = 60, check_interval: int = 5) -> bool:
        """
        Wait for Graphiti to process queued episodes into facts.

        Graphiti processes episodes asynchronously. After adding papers,
        we need to wait for the LLM to extract entities and relationships.

        Args:
            max_wait_seconds: Maximum time to wait
            check_interval: Seconds between checks

        Returns:
            True if facts are available, False if timeout
        """
        import asyncio

        logger.info(f"[KG] Waiting for Graphiti to process episodes into facts...")
        logger.info(f"[KG]   → max wait: {max_wait_seconds}s, check every {check_interval}s")

        elapsed = 0
        while elapsed < max_wait_seconds:
            # Try a simple search to see if facts are available
            test_results = await self.search_research("neuro-symbolic AI", max_results=5)

            if test_results:
                logger.info(f"[KG] ✓ Processing complete! Found {len(test_results)} facts after {elapsed}s")
                return True

            logger.info(f"[KG]   → {elapsed}s elapsed, still processing...")
            await asyncio.sleep(check_interval)
            elapsed += check_interval

        logger.warning(f"[KG] ⚠ Timeout after {max_wait_seconds}s - facts may not be ready yet")
        return False

    async def get_episodes(self, last_n: int = 10) -> List[dict]:
        """
        Get recent episodes from the knowledge graph.

        This retrieves raw episodes (before fact extraction).
        Useful for verifying papers were added correctly.

        Args:
            last_n: Number of recent episodes to retrieve

        Returns:
            List of episode dicts
        """
        if not self.connected:
            return []

        get_episodes = self.tools.get("graphiti_get_episodes")
        if not get_episodes:
            logger.warning("[KG] graphiti_get_episodes tool not found")
            return []

        try:
            logger.info(f"[KG] Getting last {last_n} episodes...")
            results = await get_episodes(
                group_id=self.group_id,
                last_n=last_n,
            )

            # Parse MCP result into usable format
            parsed = parse_mcp_result(results)
            logger.debug(f"[KG] Parsed episodes result type: {type(parsed)}")

            # Extract episode list from parsed result
            if parsed is None:
                result_list = []
            elif isinstance(parsed, list):
                result_list = parsed
            elif isinstance(parsed, dict):
                result_list = parsed.get("episodes", parsed.get("results", parsed.get("data", [])))
                if not isinstance(result_list, list):
                    result_list = [parsed]
            elif isinstance(parsed, str):
                # Episode count might be in message
                result_list = []
            else:
                result_list = []

            logger.info(f"[KG] ✓ Retrieved {len(result_list)} episodes")
            return result_list

        except Exception as e:
            logger.warning(f"[KG] ✗ Get episodes failed: {e}")
            import traceback
            logger.debug(f"[KG] Traceback: {traceback.format_exc()}")
            return []

    async def process_all_papers(
        self,
        papers: List[dict],
        wait_for_facts: bool = True,
        cache_dir: str = "/tmp/arxiv_cache",
        download_pdfs: bool = True,
        gemini_model: str = "gemini/gemini-3-flash-preview",
    ) -> dict:
        """
        Process all papers from Stage 1 research into the knowledge graph.

        CRITICAL: This fetches FULL TEXT from arXiv before adding to Graphiti.
        Stage 1 (Gemini) only provides titles/summaries with "Not specified" authors.
        This function:
        1. Uses Gemini with Google Search to find arXiv IDs (most reliable)
        2. Downloads PDF and extracts full text
        3. Gets real author names
        4. Adds to Graphiti WITH full text for proper knowledge extraction

        Args:
            papers: List of paper dicts from ResearchManager (Stage 1)
            wait_for_facts: Whether to wait for Graphiti to extract facts
            cache_dir: Directory to cache arXiv PDFs
            download_pdfs: Whether to download and extract full text (recommended)
            gemini_model: Gemini model for Google Search grounding

        Returns:
            Status dict with counts
        """
        from .arxiv_fetcher import (
            search_arxiv_with_gemini,
            batch_search_arxiv_with_gemini,
            search_arxiv_by_id,
            download_and_extract_pdf,
        )

        if not self.connected:
            logger.warning("[KG] process_all_papers skipped - not connected")
            return {"status": "skipped", "reason": "mcp-graphiti not connected"}

        logger.info(f"[KG] ═══════════════════════════════════════════════════")
        logger.info(f"[KG] Processing {len(papers)} papers into knowledge graph")
        logger.info(f"[KG] ═══════════════════════════════════════════════════")
        logger.info(f"[KG] Step 1: Finding arXiv IDs using Gemini + Google Search")

        # Batch search for all paper arXiv IDs using Gemini
        paper_titles = [p.get('title', '') for p in papers if p.get('title')]
        arxiv_id_map = await batch_search_arxiv_with_gemini(
            paper_titles,
            model=gemini_model,
            batch_size=5,
        )

        logger.info(f"[KG] Step 2: Fetching paper details and full text from arXiv")

        processed = 0
        failed = 0
        arxiv_found = 0

        for i, paper in enumerate(papers, 1):
            title = paper.get('title', '')
            if not title:
                failed += 1
                continue

            logger.info(f"[KG] Paper {i}/{len(papers)}: {title[:60]}...")

            try:
                # Get arXiv ID from Gemini search results
                arxiv_id = arxiv_id_map.get(title)

                if arxiv_id:
                    logger.info(f"[KG]   → arXiv ID: {arxiv_id}")

                    # Fetch paper details by ID
                    arxiv_paper = await search_arxiv_by_id(arxiv_id)

                    if arxiv_paper:
                        arxiv_found += 1
                        logger.info(f"[KG]   ✓ Found: {arxiv_paper.title[:50]}...")

                        # Update paper with arXiv metadata
                        author_str = ", ".join(arxiv_paper.authors[:5])
                        if len(arxiv_paper.authors) > 5:
                            author_str += " et al."
                        paper['authors'] = author_str
                        paper['venue'] = f"arXiv:{arxiv_paper.arxiv_id}"
                        paper['abstract'] = arxiv_paper.abstract

                        # Download and extract full text if requested
                        full_text = ""
                        if download_pdfs:
                            try:
                                arxiv_paper = await download_and_extract_pdf(
                                    arxiv_paper, cache_dir, max_chars=50000
                                )
                                full_text = arxiv_paper.full_text
                                if full_text:
                                    logger.info(f"[KG]   ✓ Extracted {len(full_text)} chars from PDF")
                            except Exception as e:
                                logger.warning(f"[KG]   PDF extraction failed: {e}")

                        # Add to Graphiti WITH full text
                        result = await self.add_paper(paper, full_text=full_text)
                        if result:
                            processed += 1
                            continue
                    else:
                        logger.warning(f"[KG]   → arXiv ID {arxiv_id} not found in arXiv API")
                else:
                    logger.info(f"[KG]   → No arXiv paper found via Google Search")

                # If arXiv lookup failed, add with original data (no full text)
                logger.info(f"[KG]   → Using Stage 1 data only (no full text)")
                result = await self.add_paper(paper, full_text="")
                if result:
                    processed += 1
                else:
                    failed += 1

            except Exception as e:
                logger.warning(f"[KG]   Error processing paper: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                failed += 1

        logger.info(f"[KG] ═══════════════════════════════════════════════════")
        logger.info(f"[KG] STAGE 2 COMPLETE:")
        logger.info(f"[KG]   Papers processed: {processed}")
        logger.info(f"[KG]   Papers with arXiv data: {arxiv_found} (full text + real authors)")
        logger.info(f"[KG]   Papers failed: {failed}")
        logger.info(f"[KG] ═══════════════════════════════════════════════════")

        # Verify episodes were added
        episodes = await self.get_episodes(last_n=5)
        if episodes:
            logger.info(f"[KG] ✓ Verified: {len(episodes)} recent episodes in graph")

        # Wait for fact extraction if requested
        # With 28+ papers, Graphiti needs significant time for LLM-based entity extraction
        facts_ready = False
        if wait_for_facts and processed > 0:
            facts_ready = await self.wait_for_processing(max_wait_seconds=600, check_interval=15)

        return {
            "status": "completed",
            "papers_processed": processed,
            "papers_with_arxiv": arxiv_found,
            "papers_failed": failed,
            "facts_ready": facts_ready,
        }


    async def diagnose_graph(self) -> dict:
        """
        Run diagnostics on the knowledge graph.

        Checks:
        - Number of episodes added
        - Whether facts are being extracted
        - Sample entities and facts

        Returns:
            Diagnostic info dict
        """
        logger.info(f"[KG] ═══════════════════════════════════════════════════")
        logger.info(f"[KG] KNOWLEDGE GRAPH DIAGNOSTICS")
        logger.info(f"[KG] ═══════════════════════════════════════════════════")

        diagnostics = {
            "connected": self.connected,
            "group_id": self.group_id,
            "tools_available": list(self.tools.keys()),
        }

        if not self.connected:
            logger.warning("[KG] Not connected - cannot run diagnostics")
            return diagnostics

        # Check episodes
        episodes = await self.get_episodes(last_n=10)
        diagnostics["episodes_count"] = len(episodes)
        logger.info(f"[KG] Episodes: {len(episodes)} in graph")
        if episodes:
            for i, ep in enumerate(episodes[:3]):
                ep_preview = str(ep)[:100]
                logger.info(f"[KG]   → Episode {i+1}: {ep_preview}...")

        # Try various search queries
        test_queries = [
            "transformer attention",
            "neural network",
            "machine learning",
            "neuro-symbolic",
            "paper",
        ]

        diagnostics["search_results"] = {}
        for query in test_queries:
            facts = await self.search_research(query, max_results=3)
            entities = await self.search_entities(query, max_results=3)
            diagnostics["search_results"][query] = {
                "facts": len(facts),
                "entities": len(entities),
            }
            logger.info(f"[KG] Query '{query}': {len(facts)} facts, {len(entities)} entities")

        logger.info(f"[KG] ═══════════════════════════════════════════════════")
        return diagnostics


async def run_stage2_research(
    config,
    research_manager,
    language_model=None,
) -> Optional[Stage2MCPPipeline]:
    """
    Run Stage 2 research with Graphiti via MCP.

    This is a convenience function that handles the full Stage 2 pipeline:
    1. Initialize connection to mcp-graphiti
    2. Process all papers from Stage 1
    3. Return the pipeline for use during content writing

    Args:
        config: Config object with graphiti settings
        research_manager: ResearchManager with Stage 1 papers
        language_model: Optional language model (for future agentic features)

    Returns:
        Stage2MCPPipeline if successful, None otherwise
    """
    # Check if Stage 2 is enabled
    if not getattr(config, 'enable_stage2_research', False):
        logger.info("[KG] Stage 2 research disabled in config")
        return None

    # Get settings from config
    graphiti_url = getattr(config, 'graphiti_mcp_url', 'http://localhost:8000/mcp/')
    group_id = getattr(config, 'graphiti_group_id', 'book_research')

    logger.info(f"[KG] ╔═══════════════════════════════════════════════════════╗")
    logger.info(f"[KG] ║          STAGE 2: KNOWLEDGE GRAPH INTEGRATION         ║")
    logger.info(f"[KG] ╚═══════════════════════════════════════════════════════╝")
    logger.info(f"[KG] MCP URL: {graphiti_url}")
    logger.info(f"[KG] Group ID: {group_id}")

    # Create pipeline
    stage2 = Stage2MCPPipeline(
        graphiti_url=graphiti_url,
        group_id=group_id,
    )

    # Try to connect (graceful failure if mcp-graphiti not running)
    if not await stage2.initialize():
        logger.warning("[KG] Stage 2 research unavailable (mcp-graphiti not running?)")
        logger.info("[KG] Continuing without knowledge graph - using arXiv data only")
        return None

    # Process all papers from Stage 1
    if research_manager:
        papers = research_manager.get_all_papers()
        logger.info(f"[KG] Found {len(papers)} papers from Stage 1 research")

        result = await stage2.process_all_papers(papers, wait_for_facts=True)

        # Run diagnostics to check if facts are available
        diagnostics = await stage2.diagnose_graph()

        if not result.get("facts_ready", False):
            logger.warning(f"[KG] ⚠ Facts may not be ready yet - Graphiti still processing")
            logger.info(f"[KG] Content generation will proceed, but KG context may be limited")

    logger.info(f"[KG] ═══════════════════════════════════════════════════════")
    logger.info(f"[KG] Stage 2 initialization complete - pipeline ready")
    logger.info(f"[KG] ═══════════════════════════════════════════════════════")

    return stage2


class Stage2ArxivFallback:
    """
    Fallback for Stage 2 when mcp-graphiti is not available.

    Uses arXiv abstracts directly without knowledge graph.
    Provides the same interface as Stage2MCPPipeline for compatibility.
    """

    def __init__(self, research_manager=None, cache_dir: str = None):
        """
        Initialize the fallback.

        Args:
            research_manager: ResearchManager with Stage 1 papers
            cache_dir: Directory for arXiv cache
        """
        self.research_manager = research_manager
        self.cache_dir = cache_dir or "/tmp/arxiv_cache"
        self.connected = True  # Always "connected" for interface compatibility
        self._arxiv_papers: Dict[str, dict] = {}
        logger.info("[KG-Fallback] Using arXiv fallback (no knowledge graph)")

    async def initialize(self) -> bool:
        """Initialize is a no-op for fallback."""
        logger.info("[KG-Fallback] Initialized (arXiv-only mode)")
        return True

    async def close(self):
        """Close is a no-op for fallback."""
        logger.debug("[KG-Fallback] Closed")
        pass

    async def fetch_arxiv_for_chapter(
        self,
        chapter_name: str,
        relevant_papers: List[str],
    ) -> str:
        """
        Fetch arXiv abstracts for papers relevant to a chapter.

        Args:
            chapter_name: Name of the chapter
            relevant_papers: Paper titles assigned to this chapter

        Returns:
            Formatted context string with paper abstracts
        """
        from .arxiv_fetcher import fetch_papers_for_chapter, format_paper_for_context

        logger.info(f"[KG-Fallback] Fetching arXiv papers for: '{chapter_name}'")
        logger.info(f"[KG-Fallback]   → {len(relevant_papers)} papers to fetch")

        papers = await fetch_papers_for_chapter(
            paper_titles=relevant_papers,
            cache_dir=self.cache_dir,
            download_pdfs=False,  # Just get abstracts for speed
        )

        if not papers:
            logger.info(f"[KG-Fallback]   → No papers found")
            return ""

        context_parts = [
            f"## arXiv Papers for '{chapter_name}':",
            "",
        ]

        for paper in papers:
            context_parts.append(format_paper_for_context(paper, include_sections=False))
            context_parts.append("")
            context_parts.append("---")
            context_parts.append("")

        context = "\n".join(context_parts)
        logger.info(f"[KG-Fallback] ✓ Fetched {len(papers)} papers, {len(context)} chars")
        return context

    async def get_context_for_chapter(
        self,
        chapter_name: str,
        key_concepts: List[str],
    ) -> str:
        """
        Get research context for a chapter (fallback implementation).

        Uses ResearchManager's existing keyword-based retrieval.

        Args:
            chapter_name: Name of the chapter
            key_concepts: Key concepts in the chapter

        Returns:
            Formatted context string
        """
        if not self.research_manager:
            logger.debug(f"[KG-Fallback] No research manager for: '{chapter_name}'")
            return ""

        logger.info(f"[KG-Fallback] Getting context for: '{chapter_name}'")
        context = await self.research_manager.for_section_writing(chapter_name, " ".join(key_concepts))
        logger.info(f"[KG-Fallback] ✓ Context: {len(context)} chars")
        return context

    async def get_context_for_section(
        self,
        chapter_name: str,
        section_name: str,
        section_plan: str,
        book_topic: str,
        language_model: "synalinks.LanguageModel",
    ) -> str:
        """
        Get research context for a section (fallback implementation).

        Uses ResearchManager's existing retrieval - no smart query generation
        since there's no knowledge graph to query.

        Args:
            chapter_name: Name of the chapter
            section_name: Name of the section
            section_plan: Full section plan (used for keyword extraction)
            book_topic: The book's main topic
            language_model: Ignored in fallback mode

        Returns:
            Formatted context string
        """
        if not self.research_manager:
            logger.debug(f"[KG-Fallback] No research manager for: '{section_name}'")
            return ""

        logger.info(f"[KG-Fallback] Getting context for section: '{section_name}'")

        # Extract key concepts from section plan
        # Simple approach: use section name + first few words of plan
        context = await self.research_manager.for_section_writing(
            chapter_name,
            f"{section_name} {section_plan[:200]}"
        )
        logger.info(f"[KG-Fallback] ✓ Section context: {len(context)} chars")
        return context
