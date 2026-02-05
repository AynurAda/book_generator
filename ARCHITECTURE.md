# Book Generator Architecture

A neuro-symbolic book generation system built on the Synalinks framework. Generates comprehensive, well-structured books from a topic specification with optional citation verification.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           BOOK GENERATOR                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Config (YAML)  →  Pipeline  →  Content Generation  →  PDF Assembly     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Pipeline Stages

The generation flows through these stages:

```
1. BOOK VISION           Generate high-level vision, themes, scope
        ↓
2. OUTLINE GENERATION    Extract concepts → Build hierarchy (3 levels)
        ↓
3. OUTLINE APPROVAL      Interactive: approve / edit / regenerate
        ↓
4. REORGANIZATION        Reorder chapters for conceptual flow
        ↓
5. PRIORITIZATION        Select N most important chapters (optional)
        ↓
6. SUBSUBCONCEPTS        Generate subsections for each section
        ↓
7. HIERARCHICAL PLANNING Book plan → Chapter plans → Section plans
        ↓
8. CITATION PIPELINE     Plan claims → Verify with sources (optional)
        ↓
9. CONTENT GENERATION    Write subsections → Assemble sections → Chapters
        ↓
10. ILLUSTRATIONS        Add Mermaid diagrams / AI images (optional)
        ↓
11. INTRODUCTION         Generate book introduction
        ↓
12. COVER GENERATION     AI-generated book cover
        ↓
13. PDF ASSEMBLY         Markdown → HTML → PDF with WeasyPrint
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
├── vision.py           # Book vision generation
├── pdf.py              # Markdown → PDF conversion
├── cover.py            # Cover image generation
├── authors.py          # Author profiles and styling
├── illustrations.py    # Mermaid diagrams and AI images
├── utils.py            # File I/O, formatting utilities
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

### 1. Synalinks DataModels (`models.py`)

All structured data uses Synalinks DataModels for type-safe LLM interactions:

```python
class SubsectionContent(synalinks.DataModel):
    """Output for a generated subsection."""
    content: str = synalinks.Field(
        description="The complete subsection content as flowing textbook prose."
    )

class BookPlan(synalinks.DataModel):
    thinking: list[str]      # Chain-of-thought reasoning
    book_summary: str
    narrative_arc: str
    chapter_connections: str
```

### 2. Hierarchical Planning (`planning.py`)

Planning follows a top-down hierarchy:

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
- **Critique loop**: Self-assessment and revision (up to 5 attempts)

### 3. Content Generation (`content.py`)

Content is generated bottom-up with full context:

```
Subsection (atomic unit)
    ↓ concatenate
Section (intro + subsections)
    ↓ concatenate
Chapter (intro + sections + conclusion)
```

Each subsection generator receives:
- Full book outline
- Book plan
- Chapters overview
- Chapter plan
- Section plan
- Citation constraints (if enabled)

### 4. Citation Pipeline (`citations/`)

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

### Outline Structure

Three-level hierarchy:

```python
{
    "concepts": [
        {
            "concept": "Chapter Name",
            "subconcepts": [
                {
                    "subconcept": "Section Name",
                    "subsubconcepts": ["Subsection 1", "Subsection 2"]
                }
            ]
        }
    ]
}
```

### Plan Structure

```python
# Book Plan
{
    "thinking": ["Step 1...", "Step 2..."],
    "book_summary": "Overview...",
    "narrative_arc": "How the book progresses...",
    "chapter_connections": "How chapters relate..."
}

# Section Plan
{
    "thinking": [...],
    "section_name": "...",
    "section_summary": "...",
    "role_in_chapter": "...",
    "subsections_overview": "..."
}
```

## Output Files

Each run creates a timestamped directory:

```
output/20260204_160106/
├── 00_topic.txt                    # Input topic
├── 00_book_vision.json             # Generated vision
├── 01_outline.json                 # Initial outline
├── 01_outline_reorganized.json     # After reorganization
├── 01_outline_prioritized.json     # After chapter selection
├── 01_outline_final.json           # With subsubconcepts
├── 02_book_plan.json               # Book-level plan
├── 02_chapters_overview.json       # All chapters overview
├── 02_chapter_plans.json           # Individual chapter plans
├── 02_section_plans_*.json         # Section plans per chapter
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

## Resume Capability

The pipeline supports resuming from any point:

```bash
python main.py --config config.yaml --resume output/20260204_160106
```

Cached artifacts:
- ✅ Book vision
- ✅ Outline (all stages)
- ✅ All plans (book, chapter, section)
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

### Plan Critique Loop

Each major plan goes through self-critique:

```python
for attempt in range(max_attempts):  # default: 5
    plan = generate_plan()
    critique = critique_plan()

    if critique.verdict == "pass":
        break
    else:
        plan = revise_plan(critique.guidance)
```

### Section Quality Check

After generating sections:
1. Check for repeated examples
2. Check for repeated concepts
3. Check for style issues
4. Check for coverage gaps
5. Regenerate if needed (up to 5 attempts)

## Key Design Decisions

1. **Claim-First Citations**: Plan factual claims BEFORE writing, verify them, then constrain generation. Prevents hallucinated citations.

2. **Hierarchical Planning**: Top-down planning ensures coherence. Each level provides context for the next.

3. **Bottom-Up Assembly**: Write atomic subsections, concatenate up. No rewriting = preserves verified content.

4. **Full Context**: Every generator receives the complete book context (outline, plans, etc.) for coherent output.

5. **Caching Everything**: All intermediate artifacts saved to disk. Resume from any point.

6. **Temperature = 1.0**: Required for Gemini 3 models to avoid infinite loops.

## Environment Variables

```bash
GEMINI_API_KEY=your_key_here  # For content generation and verification
```

## Running

```bash
# New generation
caffeinate python main.py --config configs/your_config.yaml

# Resume from previous
caffeinate python main.py --config configs/your_config.yaml --resume output/TIMESTAMP

# List available configs
python main.py --list
```

## Dependencies

- **synalinks**: Neuro-symbolic LLM framework
- **litellm**: Multi-provider LLM routing
- **weasyprint**: HTML → PDF conversion
- **pyyaml**: Configuration parsing
- **python-dotenv**: Environment variable loading
