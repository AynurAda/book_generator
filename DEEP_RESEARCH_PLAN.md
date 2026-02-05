# Deep Research Integration Plan

## Goal

Make the book generator produce **cutting-edge** books by using Gemini Deep Research to discover recent advances, papers, frameworks, and ideas that the LLM doesn't know about (post training cutoff).

## Key Insight

```
OLD: LLM knows content → Research adds citations (research is 20%)
NEW: Research DISCOVERS content → LLM synthesizes/explains (research is 70% for cutting-edge chapters)
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    BOOK GENERATION REQUEST                      │
│                    (topic, goal, audience)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│         STAGE 0a: GENERATE RESEARCH QUERIES                     │
│         (Synalinks Generator)                                   │
│                                                                 │
│  LLM generates 3-5 conceptual research questions dynamically    │
│  based on topic + goal.                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│         STAGE 0b: RUN DEEP RESEARCH                             │
│         (Gemini Interactions API - NOT Synalinks)               │
│                                                                 │
│  - Agent: 'deep-research-pro-preview-12-2025'                   │
│  - Async with polling                                           │
│  - Cache results in output_dir/00_research/                     │
│                                                                 │
│  Cost: ~$0.30 per query, ~$1.50 for 5 queries                   │
│  Time: ~5-10 min per query                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│         STAGE 0c: PARSE INTO STRUCTURED DATA                    │
│         (Synalinks Generator)                                   │
│                                                                 │
│  ONE LLM call with all research text (~17K tokens)              │
│  Extract → FieldKnowledge (structured)                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              EXISTING PIPELINE (research-informed)              │
│                                                                 │
│  Vision      ← FieldKnowledge.summary                           │
│  Outline     ← FieldKnowledge.summary + themes                  │
│  Planning    ← relevant paper briefs per chapter                │
│  Writing     ← full paper details for cutting-edge sections     │
│  Citations   ← papers already have sources                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Models (Synalinks DataModel)

```python
import synalinks
from typing import List, Optional


class ResearchQuery(synalinks.DataModel):
    """A single research question for deep research."""
    question: str = synalinks.Field(
        description="A conceptual research question focused on understanding methods, theories, and ideas - not statistics or trends"
    )
    focus_area: str = synalinks.Field(
        description="The aspect of the field this question explores (e.g., 'theoretical advances', 'new methods', 'open problems')"
    )


class ResearchQueries(synalinks.DataModel):
    """Collection of research queries to run."""
    queries: List[ResearchQuery] = synalinks.Field(
        description="3-5 research questions that will help write a cutting-edge book on this topic"
    )


class Paper(synalinks.DataModel):
    """A research paper extracted from deep research."""
    title: str = synalinks.Field(description="Paper title")
    authors: str = synalinks.Field(description="Author names")
    year: int = synalinks.Field(description="Publication year")
    venue: str = synalinks.Field(description="Publication venue (NeurIPS, ICML, arXiv, etc.)")

    problem: str = synalinks.Field(description="What problem does this paper solve?")
    method: str = synalinks.Field(description="Key approach or contribution")
    results: str = synalinks.Field(description="Main findings")
    significance: str = synalinks.Field(description="Why this paper matters")


class Framework(synalinks.DataModel):
    """A tool or framework extracted from deep research."""
    name: str = synalinks.Field(description="Framework name")
    description: str = synalinks.Field(description="What it does")
    approach: str = synalinks.Field(description="How it works conceptually")
    use_cases: str = synalinks.Field(description="What it's good for")
    url: Optional[str] = synalinks.Field(description="Project URL if mentioned")


class FieldKnowledge(synalinks.DataModel):
    """Structured knowledge extracted from deep research."""
    summary: str = synalinks.Field(
        description="2-3 paragraph overview of the current state of the field"
    )
    themes: List[str] = synalinks.Field(
        description="Major research themes and directions"
    )
    papers: List[Paper] = synalinks.Field(
        description="Key papers mentioned in the research"
    )
    frameworks: List[Framework] = synalinks.Field(
        description="Tools and frameworks mentioned"
    )
    open_problems: List[str] = synalinks.Field(
        description="Unsolved challenges and active research questions"
    )
```

---

## Stage 0a: Query Generation (Synalinks)

```python
import synalinks


class BookTopic(synalinks.DataModel):
    """Input for research query generation."""
    topic: str = synalinks.Field(description="The book topic")
    goal: str = synalinks.Field(description="What the book aims to achieve")
    audience: str = synalinks.Field(description="Target readers")


async def build_query_generator(language_model) -> synalinks.Program:
    """Build a program that generates research queries for a book topic."""

    inputs = synalinks.Input(data_model=BookTopic)

    outputs = await synalinks.Generator(
        data_model=ResearchQueries,
        language_model=language_model,
        instructions="""Generate 3-5 research questions to discover cutting-edge knowledge for this book.

Focus on questions that will reveal:
- New theoretical frameworks and paradigms (2024-2025)
- Recent methods and how they work conceptually
- Important papers and their contributions
- Current tools and frameworks
- Open problems and future directions

DO NOT ask about:
- Industry statistics or market trends
- Company names or funding
- Popularity metrics

Each question should help the book author UNDERSTAND and EXPLAIN new ideas to readers."""
    )(inputs)

    return synalinks.Program(
        inputs=inputs,
        outputs=outputs,
        name="research_query_generator",
    )


# Usage:
async def generate_queries(topic_data: dict, language_model) -> List[str]:
    program = await build_query_generator(language_model)

    input_data = BookTopic(
        topic=topic_data["topic"],
        goal=topic_data["goal"],
        audience=topic_data.get("audience", "technical readers"),
    )

    result = await program(input_data)
    return [q.question for q in result.queries]
```

---

## Stage 0b: Deep Research (Gemini API)

```python
import time
from google import genai


class DeepResearchClient:
    """Wrapper for Gemini Deep Research API."""

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.agent = 'deep-research-pro-preview-12-2025'

    async def research(self, query: str, timeout: int = 1800) -> str:
        """Run a deep research query and return the result."""

        interaction = self.client.interactions.create(
            input=query,
            agent=self.agent,
            background=True,
        )

        start_time = time.time()

        while True:
            interaction = self.client.interactions.get(interaction.id)

            if interaction.status == "completed":
                if hasattr(interaction, 'outputs') and interaction.outputs:
                    return interaction.outputs[-1].text
                return ""

            elif interaction.status == "failed":
                raise Exception(f"Research failed: {getattr(interaction, 'error', 'Unknown')}")

            if time.time() - start_time > timeout:
                raise Exception("Research timed out")

            time.sleep(10)

    async def research_all(self, queries: List[str]) -> Dict[str, str]:
        """Run multiple queries and return results keyed by query."""
        results = {}
        for i, query in enumerate(queries):
            results[f"query_{i}"] = await self.research(query)
        return results
```

---

## Stage 0c: Parse into Structured Data (Synalinks)

```python
class RawResearch(synalinks.DataModel):
    """Raw research text to be parsed."""
    research_text: str = synalinks.Field(
        description="The combined output from all deep research queries"
    )


async def build_research_parser(language_model) -> synalinks.Program:
    """Build a program that extracts structured data from research."""

    inputs = synalinks.Input(data_model=RawResearch)

    outputs = await synalinks.Generator(
        data_model=FieldKnowledge,
        language_model=language_model,
        instructions="""Extract structured information from this research output.

For the summary: Write 2-3 paragraphs capturing the current state of the field.

For papers: Extract every paper mentioned with full details (problem, method, results, significance).

For frameworks: Extract every tool or library mentioned with how it works.

For themes: Identify the major research directions.

For open_problems: List unsolved challenges and active research questions.

Be thorough - extract ALL papers and frameworks mentioned, not just a few examples."""
    )(inputs)

    return synalinks.Program(
        inputs=inputs,
        outputs=outputs,
        name="research_parser",
    )


# Usage:
async def parse_research(raw_outputs: Dict[str, str], language_model) -> FieldKnowledge:
    """Parse raw research outputs into structured FieldKnowledge."""

    # Combine all research outputs
    combined = "\n\n---\n\n".join(raw_outputs.values())

    program = await build_research_parser(language_model)

    input_data = RawResearch(research_text=combined)
    result = await program(input_data)

    return result
```

---

## ResearchManager Class

```python
class ResearchManager:
    """Manages research data and provides context for pipeline stages."""

    def __init__(self, field_knowledge: FieldKnowledge):
        self.fk = field_knowledge
        self._paper_index = self._build_paper_index()

    def _build_paper_index(self) -> Dict[str, List[Paper]]:
        """Index papers by keywords for retrieval."""
        index = {}
        for paper in self.fk.papers:
            # Extract keywords from title and method
            words = set(paper.title.lower().split() + paper.method.lower().split())
            for word in words:
                if len(word) > 3:  # Skip short words
                    if word not in index:
                        index[word] = []
                    index[word].append(paper)
        return index

    def for_vision(self) -> str:
        """Context for vision generation stage."""
        return self.fk.summary

    def for_outline(self) -> str:
        """Context for outline generation stage."""
        themes = "\n".join(f"- {t}" for t in self.fk.themes)
        return f"{self.fk.summary}\n\nKey themes that should be covered:\n{themes}"

    def for_chapter_planning(self, chapter_title: str) -> str:
        """Context for planning a specific chapter."""
        relevant = self._find_relevant_papers(chapter_title, top_k=10)

        if not relevant:
            return ""

        lines = ["Relevant recent research for this chapter:"]
        for p in relevant:
            lines.append(f"\n**{p.title}** ({p.authors}, {p.year})")
            lines.append(f"- Problem: {p.problem}")
            lines.append(f"- Method: {p.method}")

        return "\n".join(lines)

    def for_section_writing(self, chapter: str, section: str) -> str:
        """Context for writing a specific section."""
        query = f"{chapter} {section}"
        relevant = self._find_relevant_papers(query, top_k=4)

        if not relevant:
            return ""

        lines = ["Use these recent findings in your writing:"]
        for p in relevant:
            lines.append(f"\n**{p.title}** ({p.authors}, {p.year})")
            lines.append(f"- Problem: {p.problem}")
            lines.append(f"- Method: {p.method}")
            lines.append(f"- Results: {p.results}")
            lines.append(f"- Significance: {p.significance}")

        return "\n".join(lines)

    def _find_relevant_papers(self, query: str, top_k: int = 5) -> List[Paper]:
        """Find papers relevant to a query using keyword matching."""
        query_words = set(query.lower().split())

        paper_scores = {}
        for word in query_words:
            if word in self._paper_index:
                for paper in self._paper_index[word]:
                    paper_id = paper.title
                    paper_scores[paper_id] = paper_scores.get(paper_id, 0) + 1

        # Sort by score and return top_k
        sorted_papers = sorted(paper_scores.items(), key=lambda x: x[1], reverse=True)

        result = []
        for title, _ in sorted_papers[:top_k]:
            for p in self.fk.papers:
                if p.title == title:
                    result.append(p)
                    break

        return result

    def classify_chapter(self, chapter_title: str) -> str:
        """Classify chapter as 'foundational' or 'cutting-edge'."""
        relevant = self._find_relevant_papers(chapter_title)
        if len(relevant) >= 3:
            return "cutting-edge"
        return "foundational"
```

---

## Context Injection Per Stage

| Stage | Method | ~Tokens |
|-------|--------|---------|
| Vision | `manager.for_vision()` | 500 |
| Outline | `manager.for_outline()` | 800 |
| Chapter Planning | `manager.for_chapter_planning(chapter)` | 500-1000 |
| Section Writing (cutting-edge) | `manager.for_section_writing(chapter, section)` | 1000-2000 |
| Section Writing (foundational) | (none - uses LLM knowledge) | 0 |

---

## Config Addition

```yaml
research:
  enabled: true
  max_queries: 5
  cache: true
  cache_expiry_days: 7
```

---

## File Structure

```
book_generator/
├── research/
│   ├── __init__.py
│   ├── models.py           # Synalinks DataModels (Paper, Framework, FieldKnowledge, etc.)
│   ├── gemini_client.py    # DeepResearchClient (Gemini Interactions API)
│   ├── query_generator.py  # Synalinks Program for query generation
│   ├── parser.py           # Synalinks Program for parsing research
│   └── manager.py          # ResearchManager class
```

---

## Implementation Order

1. `models.py` - Synalinks DataModels
2. `gemini_client.py` - Deep Research API wrapper
3. `query_generator.py` - Synalinks query generation program
4. `parser.py` - Synalinks research parsing program
5. `manager.py` - ResearchManager with context retrieval
6. Integration into `pipeline.py`

---

## Cost Estimate

For a typical book with 5 research queries:
- Deep Research: 5 × $0.30 = ~$1.50
- Query generation (Synalinks): ~$0.01
- Parsing (Synalinks): ~$0.10
- **Total research cost: ~$1.60**

---

## Test Results (Feb 5-6, 2025)

Ran 3 test queries for Neurosymbolic AI:
- Query 0 (differentiable logic): 560s
- Query 1 (neural-symbolic integration): 409s
- Query 2 (program synthesis): 400s

Total: ~$0.90 for 3 queries (~62K chars of research)

Results cached in:
- `output/20260205_234203/00_research/research_query_*.txt`
- `output/20260205_234203/00_research/queries.json`
- `output/20260205_234203/00_research/raw_results.json`

---

## Implementation Status

### Completed ✅
- [x] `models.py` - Synalinks DataModels (Paper, Framework, FieldKnowledge, etc.)
- [x] `gemini_client.py` - Deep Research API wrapper with caching
- [x] `query_generator.py` - Synalinks query generation program
- [x] `parser.py` - Synalinks research parsing program
- [x] `manager.py` - ResearchManager with context retrieval (dict-based access)
- [x] Integration into `pipeline.py` with caching/resume logic
- [x] Config options (`enable_research`, `research_max_queries`, `research_cache`)
- [x] Research context injection into vision stage
- [x] Research context injection into outline stage

### TODO 🔲
- [ ] Inject research context into chapter planning stage
- [ ] Inject research context into section writing stage (cutting-edge chapters)
- [ ] Chapter classification (foundational vs cutting-edge)
- [ ] Global research cache (currently per-output-directory)
- [ ] Parallel deep research queries (currently sequential)
- [ ] Research cost tracking and display

---

## Known Issues

1. **Caching is per-output-directory**: Each run creates a new output directory, so research isn't shared across runs. Use `--resume <dir>` to reuse cached research.

2. **Synalinks returns JsonDataModel**: When accessing results from Synalinks Generator, use `.get_json()` to get dict, then construct DataModel objects. The manager works with dicts directly.

3. **Gemini 3 temperature warning**: Set `temperature=1.0` for all Generators using Gemini 3 models to avoid infinite loops.

---

## Usage

```bash
# First run (generates research)
python main.py --config configs/neurosymbolic.yaml

# Resume from cached research
python main.py --config configs/neurosymbolic.yaml --resume /path/to/output/dir
```

Config options:
```yaml
# Deep research settings
enable_research: true
research_max_queries: 3  # Number of queries to run
research_cache: true     # Cache individual query results
```
