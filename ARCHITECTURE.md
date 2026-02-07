# Polaris Architecture

A neuro-symbolic book generation platform built on the Synalinks framework. Synthesizes personalized, research-backed books from a topic specification using Gemini 3, with deep research, citation verification, and an optional knowledge graph.

## Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              POLARIS PLATFORM                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌────────────────────────────────────────────────┐     │
│  │  Next.js Web  │────▶│  FastAPI Server (api_server.py)                │     │
│  │  (Builder UI) │◀────│  POST /api/generate → Background Job          │     │
│  └──────────────┘     └────────────────────┬───────────────────────────┘     │
│                                             │                                │
│  ┌──────────────┐                          ▼                                │
│  │  CLI          │────▶ ┌──────────────────────────────────────────┐        │
│  │  (main.py)    │      │  Generation Pipeline (pipeline.py)       │        │
│  └──────────────┘      │                                          │        │
│                         │  Research → Vision → Outline → Planning  │        │
│                         │  → Citations → Content → PDF Assembly    │        │
│                         └──────────────────────────────────────────┘        │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  Gemini 3 Flash │ Gemini Deep Research │ Gemini 3 Pro Image │ Gemini Search │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Gemini 3 Integration

Four distinct Gemini capabilities power the platform:

| Capability | Model / API | Usage |
|---|---|---|
| **Content Generation** | `gemini-3-flash-preview` | All Synalinks Generators (vision, outline, planning, content, critique) |
| **Deep Research** | `deep-research-pro-preview-12-2025` | Discover cutting-edge papers and frameworks via Interactions API |
| **Image Generation** | `gemini-3-pro-image-preview` | Book covers (15 styles) and in-chapter illustrations |
| **Search Grounding** | Gemini + Google Search | Citation verification and arXiv ID resolution |

## Pipeline Stages

The generation flows through 16 stages:

```
 1. DEEP RESEARCH (Stage 1)     Gemini Deep Research for cutting-edge content
         ↓
 2. BOOK VISION                 Generate vision with reader_mode (Branch decision)
         ↓
 3. DRAFT OUTLINE               Initial outline for research query generation
         ↓
 4. RESEARCH-INFORMED OUTLINE   New outline based on discovered papers/themes
         ↓
 5. OUTLINE APPROVAL            Interactive: approve / edit / regenerate
         ↓
 6. REORGANIZATION              Reorder chapters for conceptual flow
         ↓
 7. PRIORITIZATION              Select N most important chapters (optional)
         ↓
 8. SUBSUBCONCEPTS              Generate subsections for each section
         ↓
 9. PAPER ASSIGNMENT            Assign papers to chapters (prevents repetition)
         ↓
10. HIERARCHICAL PLANNING       Book plan → Chapter plans → Section plans
         ↓
11. STAGE 2 RESEARCH            arXiv papers + Knowledge Graph (optional)
         ↓
12. CITATION PIPELINE           Plan claims → Verify with sources (optional)
         ↓
13. CONTENT GENERATION          Write subsections → Assemble sections → Chapters
                                (with subsection-level research distribution)
         ↓
14. ILLUSTRATIONS               Add Mermaid diagrams / AI images (optional)
         ↓
15. INTRODUCTION + COVER        Generate book intro and AI-generated cover
         ↓
16. PDF ASSEMBLY                Markdown → HTML → PDF with WeasyPrint
```

## Directory Structure

```
polaris/
├── book_generator/                 # Core Python package
│   ├── __init__.py
│   ├── config.py                   # Configuration dataclass, YAML parsing
│   ├── pipeline.py                 # Main orchestration (generate_book)
│   ├── models.py                   # 90+ Synalinks DataModels
│   ├── outline.py                  # Concept extraction, hierarchy, coverage
│   ├── planning.py                 # Book/chapter/section plans with critique
│   ├── content.py                  # Subsection/section/chapter writing
│   ├── vision.py                   # Book vision with reader_mode (Branch)
│   ├── pdf.py                      # Markdown → PDF conversion (WeasyPrint)
│   ├── cover.py                    # AI-generated cover (15 styles)
│   ├── authors.py                  # Writing styles (waitbutwhy, oreilly, etc.)
│   ├── illustrations.py            # Mermaid diagrams and AI images
│   ├── utils.py                    # File I/O, formatting utilities
│   ├── api_server.py               # FastAPI server with job tracking
│   │
│   ├── research/                   # Deep research subsystem
│   │   ├── __init__.py
│   │   ├── models.py               # Paper, Framework, FieldKnowledge
│   │   ├── gemini_client.py        # Gemini Deep Research API client
│   │   ├── query_generator.py      # Generate research queries from outline
│   │   ├── parser.py               # Parse research results → structured data
│   │   ├── manager.py              # ResearchManager orchestration
│   │   ├── arxiv_fetcher.py        # arXiv API + Gemini Search for ID resolution
│   │   └── stage2.py               # MCP-based knowledge graph pipeline
│   │
│   └── citations/                  # Citation verification subsystem
│       ├── __init__.py
│       ├── models.py               # Claim, VerifiedCitation, SubsectionClaimPlan
│       ├── pipeline.py             # CitationManager orchestration
│       ├── claim_planning.py       # Plan claims per subsection
│       ├── verification.py         # Verify claims with Gemini Search Grounding
│       ├── injection.py            # Format citation constraints for generators
│       ├── extraction.py           # Extract claims from text
│       ├── discovery.py            # Source discovery
│       ├── documents.py            # Document management
│       └── knowledge_base.py       # Citation knowledge base
│
├── web/                            # Next.js 14 frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Landing page (Polaris brand)
│   │   │   ├── builder/page.tsx    # 5-step book builder wizard
│   │   │   ├── layout.tsx          # Root layout
│   │   │   └── api/                # Next.js API routes
│   │   │       ├── generate/       # Proxy to FastAPI backend
│   │   │       └── waitlist/       # Waitlist signup
│   │   └── components/
│   │       ├── ConceptGraph3D.tsx   # 3D concept visualization
│   │       └── ui/                 # Shadcn/ui components
│   ├── public/avatars/             # User story avatars
│   └── package.json
│
├── configs/                        # YAML configuration files
│   ├── neurosymbolic.yaml
│   ├── neurosymbolic_finance.yaml
│   ├── ai_agent_memory.yaml
│   └── embedded_systems.yaml
│
├── tests/                          # Test suite
│   ├── test_deep_research.py       # Gemini Deep Research API tests
│   └── test_gemini_grounding.py    # Citation verification tests
│
├── tools/                          # Utility scripts
│   ├── convert_to_pdf.py           # Standalone Markdown → PDF
│   └── visualize_pipeline.py       # Pipeline visualization
│
├── output/                         # Generated books (timestamped)
├── examples/                       # Sample outputs
│
├── main.py                         # CLI entry point
├── run_api.py                      # FastAPI server launcher
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
└── LICENSE                         # MIT
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
image_model: "gemini/gemini-3-pro-image-preview"

# Generation options
num_chapters: 5              # Limit chapters (optional)
focus: "specific focus"      # Guide chapter selection
author_key: "waitbutwhy"     # Writing style (optional)

# Deep research (Stage 1)
enable_research: true        # Enable Gemini Deep Research
research_max_queries: 5      # Maximum research queries
research_cache: true         # Cache research results

# Stage 2 research (requires mcp-graphiti)
enable_stage2_research: false
graphiti_mcp_url: "http://localhost:8000/mcp/"
graphiti_group_id: "book_research"

# Reader mode override (for testing)
reader_mode_override: null   # 'practitioner', 'academic', or 'hybrid'

# Features
enable_citations: true       # Citation verification pipeline
enable_chapter_references: true  # Fast: add references from research papers
enable_illustrations: true   # Add diagrams and AI images
cover_style: "abstract"      # Cover style (15 options)

# Quality control
plan_critique_enabled: true
plan_critique_max_attempts: 5

# Resume from previous run
resume_from_dir: "output/20260204_160106"

# Default outline (optional) - skip outline generation
use_default_outline: true
default_outline:
  - concept: "Chapter Name"
    subconcepts:
      - subconcept: "Section Name"
        subsubconcepts:
          - "Subsection 1"
          - "Subsection 2"
```

## Core Components

### 1. Research System (`research/`)

Two-stage research pipeline for cutting-edge content:

```
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 1: GEMINI DEEP RESEARCH                                       │
│                                                                     │
│ Input: topic, goal, draft outline                                   │
│ Process: Gemini Deep Research API (Interactions API, async polling)  │
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
│   1. Find arXiv ID via Gemini with Google Search (most reliable)    │
│   2. Search arXiv by ID, fetch abstract + metadata                  │
│   3. Download PDF + extract full text (arxiv2text)                  │
│   4. Add to Graphiti knowledge graph via MCP (if available)         │
│                                                                     │
│ Smart querying: LLM generates targeted queries, not keyword concat  │
│ Graceful fallback: Works without mcp-graphiti (arXiv data only)     │
└─────────────────────────────────────────────────────────────────────┘
```

#### ResearchManager (`manager.py`)

Provides context for each pipeline stage using **LLM-based matching** (synalinks.Decision), not keyword matching:

```python
research_manager.for_vision()                       # High-level field summary
research_manager.for_outline()                      # Summary + themes + open problems
research_manager.for_chapter_planning(chapter_name) # Top-10 papers, top-5 frameworks
research_manager.for_section_writing(section_name, assigned_papers=["Paper A"]) # Filtered papers
```

#### arXiv Fetcher (`arxiv_fetcher.py`)

```python
# Find arXiv ID using Gemini with Google Search (more reliable than title matching)
arxiv_id = await search_arxiv_with_gemini("Attention Is All You Need")

# Batch search with rate limiting
papers = await batch_search_arxiv_with_gemini(paper_titles, batch_size=5)

# Download PDF and extract full text
paper = await download_and_extract_pdf(paper, cache_dir="arxiv_cache/")
# paper.full_text, paper.sections (abstract, introduction, method, results, conclusion)
```

#### Stage 2 MCP Pipeline (`stage2.py`)

```python
# Initialize (connects to mcp-graphiti if running)
stage2 = Stage2MCPPipeline(
    graphiti_url="http://localhost:8000/mcp/",
    group_id="book_research",
)
await stage2.initialize()

# Smart queries generated by LLM, not keyword concatenation
context = await stage2.get_context_for_section(
    section_name="Transformer Architecture",
    section_plan="...",
    book_topic="Deep Learning",
)
```

### 2. Synalinks Framework Usage

The pipeline uses four core Synalinks primitives:

| Primitive | Usage |
|---|---|
| **DataModel** | 90+ type-safe structured outputs for all LLM interactions |
| **Generator** | Content generation with instructions, temperature, and data models |
| **Branch** | Reader mode decision (practitioner/academic/hybrid), outline organization |
| **Decision** | Paper-to-chapter matching, subsection-to-research assignment, quality routing |

### 3. Reader Modes

Reader mode is inferred from the goal using a Synalinks Branch:

| Mode | Organization | Characteristics |
|------|--------------|-----------------|
| **Practitioner** | Problem-centric | "How to use it", minimal history, self-sufficient chapters |
| **Academic** | Evolution-centric | "How it fits in literature", formal proofs, sequential |
| **Hybrid** | Mixed | Both practical and theoretical emphasis |

```python
# Inferred at vision stage from goal keywords
# Can be overridden in config:
reader_mode_override: "practitioner"
```

### 4. Chapter Roles

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

### 5. Hierarchical Planning (`planning.py`)

Top-down planning with mode-aware self-critique loops:

```
Book Plan (overall narrative arc, critique ≤ 5 attempts)
    ↓
Chapters Overview (how chapters connect, builds_on / leads_to)
    ↓
Chapter Plans (per-chapter goals, connections, research context)
    ↓
Section Plans (per-section details, subsection flow)
```

Each plan includes:
- **Thinking**: Chain-of-thought reasoning
- **Content**: The actual plan
- **Critique loop**: Role-aware self-assessment (PRACTITIONER chapters not judged for formal proofs)

### 6. Content Generation (`content.py`)

Bottom-up assembly with two-level research distribution:

```
Subsection (atomic unit, 800-1500 words)
    ↓ concatenate
Section (intro + subsections + quality check)
    ↓ concatenate
Chapter (intro + sections + conclusion + references)
```

#### Two-Level Research Distribution (Prevents Repetition)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CHAPTER-LEVEL (Outline Stage)                     │
│                                                                     │
│  RoleTaggedChapter.relevant_papers = ["Paper A", "Paper B"]         │
│  Each paper assigned to ONE chapter only                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SUBSECTION-LEVEL (Content Stage)                  │
│                                                                     │
│  plan_research_distribution(research_context, subsections)          │
│    → Subsection 1: concepts=["LoCo-LMs"], domain="healthcare"      │
│    → Subsection 2: concepts=["DeepLog"], domain="robotics"          │
│    → Subsection 3: concepts=["Semantic Loss"], domain="finance"     │
│                                                                     │
│  CONCEPT EXCLUSIVITY: Each concept → ONE subsection only            │
│  DOMAIN EXCLUSIVITY: Each subsection → unique example domain        │
└─────────────────────────────────────────────────────────────────────┘
```

Each subsection generator receives:
- Full book outline, plan, and vision (including reader_mode)
- **Exclusive** research context (only papers/concepts for THIS subsection)
- Chapter and section plans
- Citation constraints (if enabled)
- Previous subsections (for flow and anti-repetition)
- Writing style instructions (if configured)

#### Quality Control

**Prevention (before generation):**
1. Chapter-level paper assignment (each paper → one chapter)
2. Subsection-level research distribution (concepts → specific subsections)
3. Example domain assignment (each subsection → unique domain)

**Detection (after generation):**
1. Check for repeated examples, concepts, and style issues
2. Check for coverage gaps against section plan
3. Regenerate with feedback if quality fails (up to 5 attempts)

### 7. Citation Pipeline (`citations/`)

Claim-first citation system using Gemini Search Grounding:

```
PHASE 1: Claim Planning
├── For each subsection, LLM plans specific factual claims
├── Claims categorized: critical / high / medium / low importance
└── Saved to: citations/01_planned_claims.json

PHASE 2: Verification (Gemini + Google Search)
├── Each claim verified against web sources
├── Must find ORIGINAL/PRIMARY sources (not blogs, not Wikipedia)
├── Confidence scoring with configurable threshold (default 0.75)
├── Grounding metadata extracted for source URLs
└── Saved to: citations/02_verified_citations.json

PHASE 3: Content Constraints
├── Verified claims → ALLOWED (must cite with in-text reference)
├── Unverified claims → FORBIDDEN (must not appear in content)
├── Original analysis/speculation → ALLOWED (framed appropriately)
└── Per-subsection citation instructions injected into generators
```

### 8. Writing Styles (`authors.py`)

Configurable writing styles applied inline during content generation:

| Style Key | Description |
|---|---|
| `waitbutwhy` | Tim Urban's WaitButWhy blog style — conversational, genuine humor |
| `for_dummies` | For Dummies series — accessible, step-by-step, not patronizing |
| `oreilly` | O'Reilly technical book — practical, clear, for practitioners |
| `textbook` | Academic textbook — rigorous, structured, formal |
| `practical` | Practical guide — application-focused, minimal theory |

### 9. Cover Generation (`cover.py`)

Dynamic cover prompts generated by Synalinks, rendered by Gemini 3 Pro Image:

**Available styles:** humorous, abstract, cyberpunk, minimalist, watercolor, vintage, blueprint, surreal, isometric, papercraft, neon_noir, botanical, bauhaus, pixel_art, art_deco

Each cover includes AI-generated illustration + programmatic text overlay (title, subtitle, author) via Pillow.

### 10. Illustrations (`illustrations.py`)

Two types of in-chapter illustrations:

1. **Mermaid diagrams** — LLM analyzes content, generates Mermaid syntax for flowcharts, sequence diagrams, etc.
2. **AI images** — Gemini 3 Pro Image generates concept visualizations with content-specific prompts

## Web Platform

### Frontend (Next.js 14)

- **Landing page** (`/`) — Polaris brand, user stories (12 personas), pricing tiers, waitlist
- **Book Builder** (`/builder`) — 5-step guided wizard:
  1. Topic — What to learn
  2. Domain — Professional context for examples
  3. Goal — What you want to be able to DO
  4. Background — Existing knowledge (skip what you know)
  5. Focus — Optional emphasis areas
  6. Generation tracking — Real-time progress with stage indicators
- **Tech:** App Router, Tailwind CSS, Shadcn/ui, Framer Motion

### Backend (FastAPI)

```
POST /api/generate          Start generation job (background task)
GET  /api/generate/{id}     Poll job status and progress
GET  /api/generate/{id}/download    Download PDF
GET  /api/generate/{id}/markdown    Download Markdown
DELETE /api/generate/{id}   Cancel job
GET  /health                Health check
GET  /docs                  Swagger API docs
```

Job status tracks: PENDING → GENERATING_VISION → GENERATING_OUTLINE → PLANNING → WRITING_CONTENT → GENERATING_ILLUSTRATIONS → GENERATING_COVER → ASSEMBLING_PDF → COMPLETED

## Data Flow

### Outline Structure (Research-Informed)

```python
{
    "organization_logic": "problem_centric",  # or evolution_centric, taxonomy_based
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

## Output Files

Each run creates a timestamped directory:

```
output/20260207_192742/
├── 00_topic.txt                        # Input topic
├── 00_book_vision.json                 # Vision with reader_mode
├── 00_research/                        # Research artifacts (if enabled)
│   ├── queries.json                    # Generated research queries
│   ├── raw_research_*.json             # Raw Gemini Deep Research responses
│   ├── field_knowledge.json            # Parsed papers, frameworks, themes
│   └── arxiv_cache/                    # Downloaded PDFs and extracted text
├── 01_outline.json                     # Initial outline
├── 01_research_informed_outline.json   # After research
├── 01_outline_reorganized.json         # After reorganization
├── 01_outline_prioritized.json         # After chapter selection
├── 01_outline_final.json               # With subsubconcepts
├── 02_book_plan.json                   # Book-level plan
├── 02_chapters_overview.json           # All chapters overview
├── 02_chapter_plans.json               # Individual chapter plans
├── 02_section_plans_*.json             # Section plans per chapter
├── 03_stage2_research.json             # Stage 2 results (if enabled)
├── 03_section_*.txt                    # Generated sections
├── 04_chapter_*.txt                    # Assembled chapters
├── 06_full_book.txt                    # Complete book (markdown)
├── 06_full_book.pdf                    # Final PDF
├── book_cover.png                      # Generated cover
├── cover_prompt.txt                    # Cover generation prompt (debug)
│
└── citations/                          # If citations enabled
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
│                    BOOK GENERATOR (Python)                           │
│                                                                     │
│  Stage2MCPPipeline                                                  │
│    │                                                                │
│    └── synalinks.MultiServerMCPClient ─────────────────┐           │
│        (connects to MCP server)                         │           │
└─────────────────────────────────────────────────────────│───────────┘
                                                          │ MCP Protocol
                                                          │ (HTTP)
                                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                mcp-graphiti (Docker Container)                       │
│                                                                     │
│  MCP Server (http://localhost:8000/mcp/)                            │
│    ├── graphiti_add_memory     - Add paper to knowledge graph       │
│    ├── graphiti_search_nodes   - Find entities                      │
│    ├── graphiti_search_memory_facts  - Find relationships           │
│    └── graphiti_get_episodes   - Retrieve recent additions          │
│                                                                     │
│  Neo4j Database (graph storage)                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Starting mcp-graphiti:**
```bash
git clone https://github.com/rawr-ai/mcp-graphiti
cd mcp-graphiti
docker compose up -d
```

**Graceful fallback:** If mcp-graphiti is not running, Stage 2 continues with arXiv data only via `Stage2ArxivFallback`.

## Resume Capability

The pipeline supports resuming from any point:

```bash
python main.py --config config.yaml --resume output/20260207_192742
```

All intermediate artifacts are cached to disk. The pipeline detects existing files and skips completed stages.

## Key Design Decisions

1. **Research-First Structure**: Discover cutting-edge papers BEFORE finalizing outline. Structure reflects actual field state, not LLM priors.

2. **Reader Mode via Branch**: LLM decides practitioner/academic/hybrid based on goal. Organization adapts accordingly. Fixed at vision stage, does not change after research.

3. **Role-Tagged Chapters**: Each chapter has a purpose (IMPLEMENTATION, LANDSCAPE, etc.). Critique checks role fulfillment, not generic quality.

4. **Claim-First Citations**: Plan factual claims BEFORE writing, verify with Gemini Search Grounding, then constrain generation. Prevents hallucinated citations.

5. **Hierarchical Planning**: Top-down planning ensures coherence. Each level provides context for the next.

6. **Bottom-Up Assembly**: Write atomic subsections, concatenate up. No rewriting = preserves verified content.

7. **Full Context**: Every generator receives the complete book context (outline, plans, research) for coherent output.

8. **Caching Everything**: All intermediate artifacts saved to disk. Resume from any point.

9. **Graceful Degradation**: Each optional feature (research, Stage 2, citations, illustrations) falls back gracefully if unavailable.

10. **LLM-Based Matching**: All paper/concept matching uses synalinks.Decision, never keyword matching.

## Environment Variables

```bash
GEMINI_API_KEY=your_key_here  # Required: content generation, research, verification, images
```

## Running

### CLI

```bash
# New generation
python main.py --config configs/neurosymbolic.yaml

# Limit chapters
python main.py --config configs/neurosymbolic.yaml --chapters 5

# Resume from previous run
python main.py --config configs/neurosymbolic.yaml --resume output/20260207_192742

# List available configs
python main.py --list
```

### Web Platform

```bash
# Start FastAPI backend
python run_api.py  # Starts on port 8000

# Start Next.js frontend (in separate terminal)
cd web && npm run dev  # Starts on port 3000
```

## Dependencies

**Core:**
- `synalinks>=0.1.0` — Neuro-symbolic LLM framework
- `python-dotenv>=1.0.0` — Environment variable loading
- `google-genai>=0.1.0` — Gemini API (Deep Research, Image Gen, Search Grounding)

**PDF Generation:**
- `markdown>=3.5.0` — Markdown processing
- `weasyprint>=60.0` — HTML → PDF (requires system deps: pango, libcairo)
- `latex2mathml>=3.0.0` — Math equation rendering

**Citation Pipeline:**
- `PyMuPDF>=1.23.0` — PDF text extraction
- `beautifulsoup4>=4.12.0` — HTML parsing
- `openai>=1.0.0` — Embeddings

**API Server:**
- `fastapi>=0.109.0` — REST API framework
- `uvicorn[standard]>=0.27.0` — ASGI server
- `pydantic>=2.0.0` — Data validation

**Frontend (web/):**
- Next.js 14, React, Tailwind CSS, Shadcn/ui, Framer Motion
