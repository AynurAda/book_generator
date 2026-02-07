# Book Generator Architecture

A neuro-symbolic book generation system built on the Synalinks framework. Generates comprehensive, well-structured books from a topic specification with optional deep research, citation verification, and knowledge graph integration.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           BOOK GENERATOR                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Config (YAML)  →  Research  →  Pipeline  →  Content  →  PDF Assembly   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Pipeline Stages

The generation flows through these stages:

```
1. DEEP RESEARCH (Stage 1)   Gemini Deep Research for cutting-edge content
        ↓
2. BOOK VISION               Generate vision with reader_mode (Branch decision)
        ↓
3. DRAFT OUTLINE             Initial outline for research query generation
        ↓
4. RESEARCH-INFORMED OUTLINE New outline based on discovered papers/themes
        ↓
5. OUTLINE APPROVAL          Interactive: approve / edit / regenerate
        ↓
6. REORGANIZATION            Reorder chapters for conceptual flow
        ↓
7. PRIORITIZATION            Select N most important chapters (optional)
        ↓
8. SUBSUBCONCEPTS            Generate subsections for each section
        ↓
9. PAPER ASSIGNMENT          Assign papers to chapters (prevents repetition)
        ↓
10. HIERARCHICAL PLANNING    Book plan → Chapter plans → Section plans
        ↓
11. STAGE 2 RESEARCH         arXiv papers + Knowledge Graph (optional)
        ↓
12. CITATION PIPELINE        Plan claims → Verify with sources (optional)
        ↓
13. CONTENT GENERATION       Write subsections → Assemble sections → Chapters
                             (with subsection-level research distribution)
        ↓
13. ILLUSTRATIONS            Add Mermaid diagrams / AI images (optional)
        ↓
14. INTRODUCTION             Generate book introduction
        ↓
15. COVER GENERATION         AI-generated book cover
        ↓
16. PDF ASSEMBLY             Markdown → HTML → PDF with WeasyPrint
```

## Directory Structure

```
book_generator/
├── __init__.py
├── config.py           # Configuration dataclass, YAML parsing
├── pipeline.py         # Main orchestration (generate_book)
├── models.py           # Synalinks DataModels for all inputs/outputs
├── outline.py          # Concept extraction, hierarchy building
├── planning.py         # Book/chapter/section plan generation
├── content.py          # Subsection/section/chapter writing
├── vision.py           # Book vision generation with reader_mode
├── pdf.py              # Markdown → PDF conversion
├── cover.py            # Cover image generation
├── authors.py          # Author profiles and styling
├── illustrations.py    # Mermaid diagrams and AI images
├── utils.py            # File I/O, formatting utilities
│
├── research/           # Deep research subsystem (NEW)
│   ├── __init__.py
│   ├── models.py       # Paper, Framework, FieldKnowledge DataModels
│   ├── gemini_client.py    # Gemini Deep Research API client
│   ├── query_generator.py  # Generate research queries from outline
│   ├── parser.py           # Parse research results into structured data
│   ├── manager.py          # ResearchManager - orchestrates research
│   ├── arxiv_fetcher.py    # arXiv API client (Stage 2)
│   └── stage2.py           # MCP-based knowledge graph pipeline
│
└── citations/          # Citation verification subsystem
    ├── __init__.py
    ├── models.py       # Claim, VerifiedCitation, etc.
    ├── pipeline.py     # Citation pipeline orchestration
    ├── claim_planning.py   # Plan claims per subsection
    ├── verification.py     # Verify claims with Gemini Search
    └── injection.py        # Format citation instructions
```

## Configuration (YAML)

```yaml
# Book metadata
topic: "Your Topic"
goal: "What the book should cover"
book_name: "Book Title"
audience: "Target readers"

# Model settings
model_name: "gemini/gemini-3-flash-preview"

# Generation options
num_chapters: 5              # Limit chapters (optional)
focus: "specific focus"      # Guide chapter selection

# Deep research (Stage 1)
enable_research: true        # Enable Gemini Deep Research
research_max_queries: 5      # Maximum research queries
research_cache: true         # Cache research results

# Stage 2 research (requires mcp-graphiti)
enable_stage2_research: false    # Enable arXiv + Knowledge Graph
graphiti_mcp_url: "http://localhost:8000/sse"
graphiti_group_id: "book_research"

# Reader mode override (for testing)
reader_mode_override: null   # 'practitioner', 'academic', or 'hybrid'

# Features
enable_citations: true       # Enable citation verification
enable_illustrations: true   # Add diagrams
cover_style: "abstract"      # Cover style

# Quality control
plan_critique_enabled: true
plan_critique_max_attempts: 5

# Resume from previous run
resume_from_dir: "output/20260204_160106"
```

## Core Components

### 1. Research System (`research/`)

Two-stage research pipeline for cutting-edge content:

```
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 1: GEMINI DEEP RESEARCH                                       │
│                                                                     │
│ Input: topic, goal, draft outline                                   │
│ Process: Gemini searches web for papers, methods, frameworks        │
│ Output: FieldKnowledge {papers, frameworks, themes, open_problems}  │
│                                                                     │
│ Parsing (LLM):                                                      │
│   Raw text → Structured Paper objects with:                         │
│   - title, authors, year, venue                                     │
│   - problem, method, results, significance                          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ RESEARCH-INFORMED OUTLINE (LLM via Branch)                          │
│                                                                     │
│ Decision 1: Does research reveal a taxonomy?                        │
│   YES → Use taxonomy-based organization                             │
│   NO  → Use reader_mode organization                                │
│                                                                     │
│ Decision 2 (if no taxonomy): What reader_mode?                      │
│   PRACTITIONER → Problem-centric (group by capability)              │
│   ACADEMIC → Evolution-centric (group by conceptual development)    │
│                                                                     │
│ Output: Role-tagged chapters with relevant_papers assigned          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 2: arXiv + KNOWLEDGE GRAPH (Optional)                         │
│                                                                     │
│ For each chapter's relevant_papers:                                 │
│   1. Search arXiv by paper title                                    │
│   2. Fetch full abstract, authors, PDF link                         │
│   3. Optionally download PDF + extract full text (PyMuPDF)          │
│   4. Add to Graphiti knowledge graph (if mcp-graphiti running)      │
│                                                                     │
│ Uses: arxiv Python library (handles rate limits automatically)      │
│ Uses: Synalinks MultiServerMCPClient for mcp-graphiti               │
└─────────────────────────────────────────────────────────────────────┘
```

#### arXiv Fetcher (`arxiv_fetcher.py`)

```python
from book_generator.research import search_arxiv, search_arxiv_by_id

# Search by title
papers = await search_arxiv("Attention Is All You Need", max_results=5)

# Fetch by arXiv ID
paper = await search_arxiv_by_id("1706.03762")

# Download PDF and extract text
paper = await download_and_extract_pdf(paper, cache_dir="/tmp/arxiv")
print(paper.full_text)       # Extracted text
print(paper.sections)        # {abstract, introduction, method, results, conclusion}
```

#### Stage 2 MCP Pipeline (`stage2.py`)

```python
from book_generator.research import Stage2MCPPipeline

# Initialize (connects to mcp-graphiti if running)
stage2 = Stage2MCPPipeline(
    graphiti_url="http://localhost:8000/sse",
    group_id="book_research",
)
await stage2.initialize()  # Returns False if mcp-graphiti unavailable

# Add paper to knowledge graph
await stage2.add_paper({"title": "...", "abstract": "..."})

# Search knowledge graph
facts = await stage2.search_research("attention mechanisms")

# Get context for chapter writing
context = await stage2.get_context_for_chapter(
    chapter_name="Transformer Architecture",
    key_concepts=["attention", "self-attention", "multi-head"],
)
```

### 2. Reader Modes

Reader mode is inferred from the goal using a Synalinks Branch:

| Mode | Organization | Characteristics |
|------|--------------|-----------------|
| **Practitioner** | Problem-centric | "How to use it", minimal history, self-sufficient chapters |
| **Academic** | Evolution-centric | "How it fits in literature", formal proofs, sequential |
| **Hybrid** | Mixed | Both practical and theoretical emphasis |

```python
# Inferred from goal keywords:
# Practitioner: "build", "implement", "deploy", "hands-on", "tutorial"
# Academic: "understand", "research", "comprehensive", "theory"

# Can be overridden in config:
reader_mode_override: "practitioner"
```

### 3. Chapter Roles

Each chapter is tagged with a role for mode-aware critique:

| Role | Purpose |
|------|---------|
| `PROBLEM_MOTIVATION` | Why this matters |
| `ESSENTIAL_BACKGROUND` | Just-enough theory (practitioner) |
| `PREREQUISITES` | Formal background (academic) |
| `LANDSCAPE` | Survey of approaches |
| `DEEP_METHOD` | Detailed key approach |
| `IMPLEMENTATION` | Code, patterns |
| `CASE_STUDY` | Real applications |
| `HISTORICAL` | Field evolution (academic) |
| `FORMAL_THEORY` | Proofs (academic) |
| `FRONTIERS` | Open problems |

### 4. Synalinks DataModels (`models.py`)

All structured data uses Synalinks DataModels for type-safe LLM interactions:

```python
class BookVision(synalinks.DataModel):
    """Book vision with reader mode."""
    reader_mode: str = synalinks.Field(
        description="Reader mode: practitioner, academic, or hybrid"
    )
    core_thesis: str
    reader_journey: str
    key_themes: list[str]
    scope_boundaries: str
    unique_angle: str

class RoleTaggedChapter(synalinks.DataModel):
    """Chapter with role for mode-aware critique."""
    chapter_name: str
    role: str  # PROBLEM_MOTIVATION, LANDSCAPE, DEEP_METHOD, etc.
    key_concepts: list[str]
    relevant_papers: list[str]  # Assigned by LLM from research
    sections: list[str]

class ResearchInformedOutline(synalinks.DataModel):
    """Outline generated with research context."""
    organization_logic: str  # taxonomy, problem_centric, evolution_centric
    taxonomy_source: str     # If taxonomy-based, cite source
    chapters: list[RoleTaggedChapter]

# Research distribution for subsections (prevents repetition)
class SubsectionResearchAssignment(synalinks.DataModel):
    """Research assignment for a single subsection."""
    subsection_name: str
    assigned_concepts: list[str]   # Concepts this subsection covers
    example_domain: str            # Unique domain (healthcare, robotics, etc.)
    focus_area: str                # What aspect to emphasize

class ResearchDistributionPlan(synalinks.DataModel):
    """Plan for distributing research across subsections."""
    assignments: list[SubsectionResearchAssignment]
```

### 5. Hierarchical Planning (`planning.py`)

Planning follows a top-down hierarchy with mode-aware critique:

```
Book Plan (overall narrative arc)
    ↓
Chapters Overview (how chapters connect)
    ↓
Chapter Plans (per-chapter goals, connections)
    ↓
Section Plans (per-section details, subsection flow)
```

Each plan includes:
- **Thinking**: Step-by-step reasoning (chain-of-thought)
- **Content**: The actual plan details
- **Critique loop**: Role-aware self-assessment and revision

### 6. Content Generation (`content.py`)

Content is generated bottom-up with full context and **two-level research distribution planning**:

```
Subsection (atomic unit)
    ↓ concatenate
Section (intro + subsections)
    ↓ concatenate
Chapter (intro + sections + conclusion)
```

#### Two-Level Research Distribution (Prevents Repetition)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CHAPTER-LEVEL (Outline Stage)                    │
│                                                                     │
│  generate_research_informed_outline()                               │
│    → RoleTaggedChapter.relevant_papers = ["Paper A", "Paper B"]     │
│    → Each paper assigned to ONE chapter only                        │
│                                                                     │
│  Result: chapter_paper_assignments = {                              │
│    "Chapter 1: Differentiable Logic": ["Paper A", "Paper B"],       │
│    "Chapter 2: LLMs as Workers": ["Paper C", "Paper D"],            │
│  }                                                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SECTION-LEVEL (Content Stage)                    │
│                                                                     │
│  for_section_writing(chapter, section, assigned_papers=["A", "B"])  │
│    → Only Paper A and Paper B returned as context                   │
│    → Not all papers from research                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SUBSECTION-LEVEL (Content Stage)                 │
│                                                                     │
│  plan_research_distribution(research_context, subsections)          │
│    → Subsection 1: concepts=["LoCo-LMs"], domain="healthcare"       │
│    → Subsection 2: concepts=["DeepLog"], domain="robotics"          │
│    → Subsection 3: concepts=["Semantic Loss"], domain="finance"     │
│                                                                     │
│  Each subsection gets ONLY its assigned concepts and domain         │
└─────────────────────────────────────────────────────────────────────┘
```

This prevents:
- Same papers being explained in every chapter
- Same research concepts being repeated in every subsection
- Same example domains being reused

Each subsection generator receives:
- Full book outline
- Book plan and vision (including reader_mode)
- **Assigned** research context (only papers/concepts for this subsection)
- Chapter and section plans
- Citation constraints (if enabled)
- Previous subsections (for flow and safety check)

### 7. Citation Pipeline (`citations/`)

Optional claim-first citation system:

```
PHASE 1: Claim Planning
├── For each subsection, LLM plans specific factual claims
├── Claims categorized: critical / high / medium / low importance
└── Saved to: citations/01_planned_claims.json

PHASE 2: Verification (Gemini Search Grounding)
├── Each claim verified against web sources
├── Must find ORIGINAL/PRIMARY sources
├── Wikipedia and secondary sources rejected
└── Saved to: citations/02_verified_citations.json

PHASE 3: Content Constraints
├── Verified claims → ALLOWED (must cite)
├── Unverified claims → FORBIDDEN
└── Original analysis/speculation → ALLOWED (framed appropriately)
```

## Data Flow

### Outline Structure (Research-Informed)

```python
{
    "organization_logic": "problem_centric",
    "taxonomy_source": "",
    "chapters": [
        {
            "chapter_name": "Building with Transformers",
            "role": "IMPLEMENTATION",
            "key_concepts": ["attention", "embeddings"],
            "relevant_papers": [
                "Attention Is All You Need (Vaswani 2017)",
                "BERT: Pre-training of Deep Bidirectional..."
            ],
            "sections": ["Self-Attention", "Multi-Head Attention"]
        }
    ]
}
```

### Research Context for Writing

```python
# ResearchManager provides context for each stage:
research_manager.for_vision()         # High-level themes
research_manager.for_outline()        # Papers + themes for structure
research_manager.for_section_writing(section_name)  # Relevant papers
```

## Output Files

Each run creates a timestamped directory:

```
output/20260204_160106/
├── 00_topic.txt                    # Input topic
├── 00_book_vision.json             # Vision with reader_mode
├── 00_research/                    # Research artifacts (if enabled)
│   ├── queries.json                # Generated research queries
│   ├── raw_research_*.json         # Raw Gemini responses
│   ├── field_knowledge.json        # Parsed papers, frameworks, themes
│   └── arxiv_cache/                # Downloaded PDFs and extracted text
├── 01_outline.json                 # Initial outline
├── 01_research_informed_outline.json   # After research (NEW)
├── 01_outline_reorganized.json     # After reorganization
├── 01_outline_prioritized.json     # After chapter selection
├── 01_outline_final.json           # With subsubconcepts
├── 02_book_plan.json               # Book-level plan
├── 02_chapters_overview.json       # All chapters overview
├── 02_chapter_plans.json           # Individual chapter plans
├── 02_section_plans_*.json         # Section plans per chapter
├── 03_stage2_research.json         # Stage 2 results (if enabled)
├── 03_section_*.txt                # Generated sections
├── 04_chapter_*.txt                # Assembled chapters
├── 06_full_book.txt                # Complete book (markdown)
├── 06_full_book.pdf                # Final PDF
├── book_cover.png                  # Generated cover
│
└── citations/                      # If citations enabled
    ├── 01_planned_claims.json
    ├── 01_subsection_plans.json
    ├── 02_verified_citations.json
    ├── 03_unverified_claims.json
    └── 04_bibliography.md
```

## mcp-graphiti Integration

Stage 2 research uses mcp-graphiti for knowledge graph functionality via Synalinks MCP:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BOOK GENERATOR (Python)                          │
│                                                                     │
│  Stage2MCPPipeline                                                  │
│    │                                                                │
│    └── synalinks.MultiServerMCPClient ─────────────────┐           │
│        (connects to MCP server)                         │           │
└─────────────────────────────────────────────────────────│───────────┘
                                                          │ MCP Protocol
                                                          │ (HTTP SSE)
                                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                mcp-graphiti (Docker Container)                       │
│                                                                     │
│  MCP Server (http://localhost:8000/sse)                             │
│    ├── add_episode    - Add paper to knowledge graph                │
│    ├── search_nodes   - Find entities                               │
│    ├── search_facts   - Find relationships                          │
│    └── get_episodes   - Retrieve recent additions                   │
│                                                                     │
│  Neo4j Database (graph storage)                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Starting mcp-graphiti:**
```bash
# Clone mcp-graphiti repo
git clone https://github.com/rawr-ai/mcp-graphiti
cd mcp-graphiti

# Start with Docker Compose
docker compose up -d
```

**Graceful fallback:** If mcp-graphiti is not running, Stage 2 continues with arXiv data only.

## Resume Capability

The pipeline supports resuming from any point:

```bash
python main.py --config config.yaml --resume output/20260204_160106
```

Cached artifacts:
- ✅ Book vision (with reader_mode)
- ✅ Research results (papers, themes, queries)
- ✅ Outline (all stages including research-informed)
- ✅ All plans (book, chapter, section)
- ✅ Stage 2 research (arXiv papers, KG additions)
- ✅ Claims and verification results
- ✅ Generated sections and chapters

## Writing Style

Content is generated in **WaitButWhy + Textbook hybrid** style:

**WaitButWhy elements:**
- Conversational, engaging tone
- Analogies and thought experiments
- "Explaining to a smart friend"

**Textbook rigor:**
- Technically precise
- Actual mechanisms and algorithms
- Comprehensive coverage

**Original thinking encouraged:**
- Novel interpretations: "One way to think about this is..."
- Speculation: "This opens the possibility that..."
- Just not presented as established fact

## Quality Control

### Plan Critique Loop (Mode-Aware)

Each major plan goes through role-aware self-critique:

```python
for attempt in range(max_attempts):  # default: 5
    plan = generate_plan()
    critique = critique_plan(book_vision=book_vision)  # Passes reader_mode

    if critique.verdict == "pass":
        break
    else:
        plan = revise_plan(critique.guidance)
```

Critique adapts based on:
- **Chapter role**: IMPLEMENTATION chapters checked for code examples
- **Reader mode**: Practitioner chapters don't require formal proofs

### Section Quality Check

**Prevention (before generation):**
1. Chapter-level paper assignment (each paper → one chapter)
2. Subsection-level research distribution (concepts → specific subsections)
3. Example domain assignment (each subsection → unique domain)

**Detection (after generation):**
1. Check for repeated examples
2. Check for repeated concepts
3. Check for style issues
4. Check for coverage gaps
5. Regenerate if needed (up to 5 attempts)

## Key Design Decisions

1. **Research-First Structure**: Discover cutting-edge papers BEFORE finalizing outline. Structure reflects actual field state, not LLM priors.

2. **Reader Mode via Branch**: LLM decides practitioner/academic based on goal. Organization adapts accordingly.

3. **Role-Tagged Chapters**: Each chapter has a purpose (IMPLEMENTATION, LANDSCAPE, etc.). Critique checks role fulfillment.

4. **Claim-First Citations**: Plan factual claims BEFORE writing, verify them, then constrain generation. Prevents hallucinated citations.

5. **Hierarchical Planning**: Top-down planning ensures coherence. Each level provides context for the next.

6. **Bottom-Up Assembly**: Write atomic subsections, concatenate up. No rewriting = preserves verified content.

7. **Full Context**: Every generator receives the complete book context (outline, plans, research, etc.) for coherent output.

8. **Caching Everything**: All intermediate artifacts saved to disk. Resume from any point.

9. **Graceful Degradation**: Each optional feature (research, Stage 2, citations) falls back gracefully if unavailable.

## Environment Variables

```bash
GEMINI_API_KEY=your_key_here  # For content generation, research, and verification
```

## Running

```bash
# New generation
caffeinate -i venv/bin/python main.py --config configs/your_config.yaml

# Resume from previous
caffeinate -i venv/bin/python main.py --config configs/your_config.yaml --resume output/TIMESTAMP

# List available configs
python main.py --list
```

## Dependencies

- **synalinks**: Neuro-symbolic LLM framework
- **litellm**: Multi-provider LLM routing
- **arxiv**: arXiv API client (Stage 2 research)
- **pymupdf**: PDF text extraction (optional, for full paper text)
- **weasyprint**: HTML → PDF conversion
- **pyyaml**: Configuration parsing
- **python-dotenv**: Environment variable loading
