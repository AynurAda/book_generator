# Book Generator Workflow

This document describes the workflow logic for the AI-powered book generation system built with Synalinks.

## Overview

The book generator creates comprehensive educational books through a multi-stage pipeline that ensures coherent, well-structured content with minimal repetition.

```
Topic Input → Outline Generation → Outline Reorganization → Hierarchical Planning → Subsection Generation → Assembly → Cover → Final Book
              (8 branches + enrich)  (temporal/conceptual)   (Book → Chapter → Section)   (3 branches each)     (concatenate)
```

```mermaid
flowchart TD
    subgraph Stage1["Stage 1: Outline Generation"]
        A[Topic Input] --> B1[Branch 1<br/>temp=1.0]
        A --> B2[Branch 2<br/>temp=1.0]
        A --> B3[Branch 3-8<br/>temp=1.0]
        B1 --> C[Merge & Deduplicate]
        B2 --> C
        B3 --> C
        C --> C2[Enrich Main Concepts<br/>add missing important ones]
        C2 --> D[Expand Subconcepts]
        D --> E[Review & Enrich]
        E --> F[Expand Sub-subconcepts]
        F --> G[Verify Relevance]
        G --> H[DeepHierarchy<br/>3-level outline]
    end

    subgraph Stage1b["Stage 1b: Outline Reorganization"]
        H --> H1{Analyze for<br/>evolution pattern}
        H1 -->|Has evolution| H2[Reorder chapters<br/>by temporal/conceptual flow]
        H1 -->|No evolution| H3[Keep original order]
        H2 --> H4[Reorganized Outline]
        H3 --> H4
    end

    subgraph Stage2["Stage 2: Hierarchical Planning"]
        H4 --> I[Generate Book Plan]
        I --> J1[Generate Chapters Overview<br/>one-shot for coherence]
        J1 --> J2[Generate Chapter Plans<br/>per chapter with overview context]
        J2 --> K[Generate Section Plans<br/>per chapter with full context]
    end

    subgraph Stage3["Stage 3: Subsection Generation"]
        K --> L{For each chapter}
        L --> L1[Generate Chapter Intro<br/>puts chapter in book context]
        L1 --> L2{For each section}
        L2 --> L3[Generate Section Intro<br/>previews subsections]
        L3 --> L4{For each subsection}
        L4 --> M1[Branch 1<br/>temp=1.0]
        L4 --> M2[Branch 2<br/>temp=1.0]
        L4 --> M3[Branch 3<br/>temp=1.0]
        M1 --> M4[Merge & Consolidate<br/>select best version]
        M2 --> M4
        M3 --> M4
        M4 --> L4
        M4 --> N[Concatenate subsections<br/>with section intro]
        N --> L2
        N --> O[Concatenate sections<br/>with chapter intro]
        O --> L
    end

    subgraph Stage4["Stage 4: Cover Generation"]
        O --> CVR[Generate cover<br/>with Imagen 4.0]
        CVR --> CVRIMG[book_cover.png]
    end

    subgraph Stage5["Stage 5: Final Assembly & PDF"]
        CVRIMG --> Y[Combine all chapters]
        Y --> Z[Add cover & TOC]
        Z --> TXT[06_full_book.txt]
        Z --> PDF[Generate PDF<br/>with cover]
        PDF --> BOOK[06_full_book.pdf]
    end

    style Stage1 fill:#e1f5fe
    style Stage1b fill:#e0f7fa
    style Stage2 fill:#fff3e0
    style Stage3 fill:#e8f5e9
    style Stage4 fill:#fff9c4
    style Stage5 fill:#f3e5f5
```

```mermaid
flowchart LR
    subgraph Hierarchy["Book Structure Hierarchy"]
        direction TB
        Book["📚 Book<br/>(1 book plan)"]
        Book --> Ch1["📖 Chapter 1"]
        Book --> Ch2["📖 Chapter 2"]
        Book --> ChN["📖 Chapter N"]

        Ch1 --> S11["📄 Section 1.1"]
        Ch1 --> S12["📄 Section 1.2"]

        S11 --> SS111["📝 1.1.1 Subsection"]
        S11 --> SS112["📝 1.1.2 Subsection"]
        S11 --> SS113["📝 1.1.3 Subsection"]
    end

    subgraph Planning["Planning Context Flow"]
        direction TB
        BP["Book Plan"] --> CO["Chapters Overview<br/>(all chapters coherence)"]
        CO --> CP["Chapter Plan<br/>(per chapter)"]
        BP --> SP["Section Plan"]
        CO --> SP
        CP --> SP
        BP --> DW["Direct Write<br/>(per section)"]
        CO --> DW
        CP --> DW
        SP --> DW
    end

    style Hierarchy fill:#e3f2fd
    style Planning fill:#fff8e1
```

## Pipeline Stages

### Stage 1: Outline Generation

**Input:** `Topic` (topic, goal, book_name)

**Process:**
1. **Multi-branch concept extraction** - 8 parallel generators (temperature=1.0) independently extract main concepts from the topic
2. **Merge & deduplicate** - All branches are merged and deduplicated into a unified concept list
3. **Enrich main concepts** - Review and add any important missing main concepts:
   - Foundational/theoretical concepts
   - Historical/evolution concepts
   - Practical/application concepts
   - Advanced/emerging concepts
   - Cross-cutting themes
   - Methodology concepts
4. **Subconcept expansion** - Each main concept is expanded with 5-10 specific subconcepts
5. **Review & enrich subconcepts** - A review pass adds any missing subconcepts
6. **Sub-subconcept expansion** - Each subconcept is expanded with 3-7 detailed sub-subconcepts
7. **Relevance verification** - Final pass removes off-topic or too-generic items

**Output:** `DeepHierarchy` - 3-level hierarchy (Concepts → Subconcepts → Sub-subconcepts)

**Files saved:**
- `01_outline.json` - Full outline in JSON format
- `01_outline.txt` - Human-readable outline

---

### Stage 1b: Outline Reorganization

**Input:** `OutlineReorganizationInput` (topic, goal, current_outline)

**Process:**
The LLM analyzes the generated outline to determine if reorganizing chapters would better reflect:
1. **Historical/temporal evolution** - How concepts developed over time
2. **Conceptual progression** - Foundational concepts before advanced ones
3. **Logical dependencies** - Concepts that build on each other

If reorganization makes sense:
- Identifies the optimal order that tells a coherent story of how ideas evolved
- Ensures foundational/prerequisite concepts come before those that depend on them
- Maintains narrative flow from simpler to more complex ideas
- Reorders chapters without losing any content

If the current order is already optimal or reorganization doesn't apply:
- Keeps the original order
- Explains why reorganization wasn't needed

**Output:** `ReorganizedOutline` (should_reorganize, reasoning, chapter_order)

**Files saved:**
- `01_outline_reorganized.json` - Reorganized outline (only if changed)
- `01_outline_reorganized.txt` - Human-readable reorganized outline (only if changed)

---

### Stage 2: Hierarchical Planning

Planning happens at four levels: book → chapters overview → individual chapter plans → sections. This ensures coherent narrative flow throughout while giving each chapter focused attention.

#### 2a: Book Plan Generation

**Input:** `BookPlanInput` (topic, goal, book_name, full_outline)

**Note:** The `full_outline` includes all three levels (concepts → subconcepts → subsubconcepts), giving the planner complete visibility of every topic that will be covered in the book.

**Process:**
- Generate high-level book plan covering the overall narrative arc
- Describe how chapters connect and build upon each other
- Define what readers will learn and key takeaways

**Output:** `BookPlan` (book_summary, narrative_arc, chapter_connections)

**Files saved:**
- `02_book_plan.json` - Book plan in JSON format
- `02_book_plan.txt` - Human-readable book plan

#### 2b: Chapters Overview Generation (One-Shot for Coherence)

**Input:** `ChaptersOverviewInput` (topic, goal, book_name, full_outline, book_plan, chapters)

**Note:** The `full_outline` includes all three levels, so the overview planner sees every subsection topic when planning chapter connections.

**Process:**
- Generate a high-level overview of ALL chapters in a single LLM call
- This provides the "birds-eye view" showing how chapters connect
- Includes narrative flow and brief role for each chapter
- Generated once for coherence, then used as context for individual chapter planning

**Output:** `ChaptersOverview` (narrative_flow, chapter_briefs: List of `ChapterBrief`)

Each `ChapterBrief` contains: chapter_name, brief_role, key_concepts, builds_on, leads_to

**Files saved:**
- `02_chapters_overview.json` - Chapters overview in JSON format
- `02_chapters_overview.txt` - Human-readable chapters overview

#### 2c: Individual Chapter Plans Generation (Per-Chapter with Full Context)

**Input:** `SingleChapterPlanInput` (topic, goal, book_name, full_outline, book_plan, chapters_overview, chapter_name, chapter_number, total_chapters)

**Process:**
- For each chapter individually, generate a detailed plan
- Uses the chapters overview as context for coherence
- Each plan uses the EXACT chapter name provided (no name drift)
- Plans are generated one at a time for focused attention

**Output:** `ChapterPlan` (chapter_name, chapter_summary, role_in_book, connection_to_previous, connection_to_next)

**Files saved:**
- `02_chapter_plan_NN_<chapter>.json` - Individual chapter plan files
- `02_chapter_plans.json` - Combined chapter plans in JSON format

**Why two-stage chapter planning?**
- **Stage 1 (one-shot overview)**: Ensures coherence - the LLM sees all chapters together to plan cross-chapter connections
- **Stage 2 (per-chapter plans)**: Ensures quality - each chapter gets focused attention with exact name matching

#### 2d: Section Plans Generation (Per-Chapter with Full Context)

**Input:** `SectionPlansInput` (topic, goal, book_name, book_plan, chapters_overview, chapter_plan, chapter_name, sections, subsections_by_section)

**Process:**
- For each chapter, generate plans for all sections
- Receives full context: book plan, chapters overview, and chapter plan
- Each section plan describes its content, role in the chapter, and overview of subsections

**Output:** `ChapterSectionPlans` (chapter_name, section_plans: List of `SectionPlan`)

**Files saved:**
- `02_section_plans_<chapter>.json` - Section plans for each chapter

**Why hierarchical planning with full context?** Each level receives all context from above:
- Book plan provides overall narrative arc
- Chapters overview provides cross-chapter coherence
- Chapter plan provides specific chapter goals
This ensures coherence and prevents overlap at every level.

---

### Stage 3: Subsection Generation (with Multi-Branch Selection)

**Architecture:**
Each subsection is generated separately with full planning context, using multi-branch generation for quality:

```
For each chapter:
  1. Generate chapter introduction (puts chapter in book context)
  For each section:
    2. Generate section introduction (previews subsections)
    For each subsection:
      3. Generate 3 branches in parallel (temp=1.0)
      4. Merge branches with & operator
      5. Consolidate to select/refine best version
    6. Concatenate: section intro + subsections
  7. Concatenate: chapter header + chapter intro + sections
```

**Inputs:**

- `SubsectionInput` (topic, goal, book_name, audience, full_outline, book_plan, chapters_overview, chapter_name, chapter_plan, section_name, section_plan, subsection_name) + optional `WritingStyle`
- `SectionIntroInput` (topic, book_name, chapter_name, section_name, section_plan, subsection_names, intro_style)
- `ChapterIntroInput` (topic, book_name, book_plan, chapters_overview, chapter_name, chapter_number, total_chapters, chapter_plan, section_names)

**Process:**

1. **Chapter Introduction**: Each chapter starts with an introduction that:
   - Places the chapter in the context of the ENTIRE BOOK narrative
   - Explains what the reader has learned so far (if not first chapter)
   - Previews what the chapter covers and why it matters
   - Connects to the book's overall goal
   - 3-4 paragraphs in flowing prose

2. **Section Introduction**: Each section starts with an introduction that:
   - Sets context for what the section covers
   - Explains why these topics matter
   - Previews what the reader will learn
   - Uses a rotating intro style for variety
   - 2-3 paragraphs in flowing prose

3. **Subsection Generation (Multi-Branch)**:
   - Generate 3 versions in parallel using separate generators
   - Each generator has temperature=1.0 for diversity
   - Merge all branches using `&` operator
   - Consolidate with a final generator that selects/refines the best version
   - This follows the same synalinks pattern used in outline generation

4. **Assembly by Concatenation**:
   - Subsections concatenated with `####` headers
   - Section = section intro + subsections
   - Chapter = chapter header (`##`) + chapter intro + sections (`###`)
   - No rewriting needed - full context ensures coherent output

**Consolidation Selection Criteria (in order of importance):**
1. COMPREHENSIVENESS: Does it cover the topic thoroughly?
2. DEPTH OF EXPLANATION: Step-by-step explanations that build understanding
3. SELF-CONTAINED: Can it be understood without prior knowledge?
4. EXAMPLES: Are there concrete, helpful examples?
5. CLARITY AND FLOW: Is it well-organized and readable?

**Output:** Consolidated best version (or synthesis of strongest elements)

**Introduction Styles (rotated per section to avoid repetition):**
- Question-based openings (thought-provoking, fundamental questions)
- Problem-based openings (real-world problems, practical scenarios)
- Context-based openings (historical context, connections to previous sections)
- Insight-based openings (surprising facts, paradoxes, misconceptions)
- Definition-based openings (problem space definition, distinguishing concepts)
- Motivation-based openings (why practitioners care, practical benefits)
- Example-based openings (concrete examples, running examples)
- Contrast-based openings (naive vs sophisticated approaches)
- Forward-looking openings (previews, roadmaps)

**Depth Requirements:**
- **500-1000 words per subsection** (or more if needed to fully explain)
- Each subsection gets comprehensive, textbook-quality coverage

**Explanation Approach:**
- **STEP-BY-STEP**: Break down complex ideas into sequential, logical steps. Start from first principles, build understanding incrementally, make reasoning explicit.
- **SELF-CONTAINED**: Define ALL terms when first used. Each subsection should stand on its own - a reader should understand without reading previous chapters.
- **NO ASSUMED PRIOR KNOWLEDGE**: Explain jargon immediately, don't skip "obvious" steps, build from ground zero for each concept, include the "why" behind every "what".
- **IN-DEPTH**: Go beyond definitions to true understanding. Explain intuition behind formal concepts, show how things work internally, address "how" and "why" questions.

**Required Coverage for Each Subsection:**
- DEFINITION: What is this concept? Define it precisely and completely
- MECHANICS: How does it work? Explain the underlying principles in detail
- SIGNIFICANCE: Why does this matter? What problems does it solve?
- EXAMPLES: Multiple concrete, specific examples that illustrate different aspects
- NUANCES: Edge cases, common misconceptions, limitations, important caveats
- CONNECTIONS: How does this relate to other concepts in the section/chapter?

**Files saved:**
- `03_section_NNN_<name>.txt` - Each complete section (intro + subsections)
- `04_chapter_<name>.txt` - Each complete chapter (intro + sections)

---

### Stage 4: Cover Generation

**Process:**
- Generate a professional book cover using Google's Imagen 4.0 model
- Cover includes: book title, subtitle, and authors
- The prompt is kept minimal to let the AI decide the best visual design

**Input:** Book metadata (title, subtitle, authors from config)

**Output:** PNG image suitable for book cover (3:4 aspect ratio)

**Files saved:**
- `book_cover.png` - Generated book cover image

---

### Stage 5: Final Book Assembly & PDF Generation

**Process:**
- Combine all chapters into a single document
- Add cover image as the first page
- Add table of contents
- Convert markdown to styled PDF with professional book formatting

**PDF Features:**
- A4 page size with proper margins
- Full-page cover image on first page
- Two-column table of contents
- Serif font (Georgia) for readability
- Automatic page numbers (except on cover)
- Chapter titles in header
- Page breaks before each chapter
- Styled headings, blockquotes, and code blocks
- Justified text with hyphenation

**Files saved:**
- `06_full_book.txt` - Complete book (Markdown)
- `06_full_book.pdf` - Complete book (PDF with cover)

---

## Data Models

### Input Models
| Model | Fields | Purpose |
|-------|--------|---------|
| `Topic` | topic, goal, book_name | Initial book specification |
| `OutlineReorganizationInput` | topic, goal, current_outline | Input for outline reorganization analysis |
| `BookPlanInput` | topic, goal, book_name, full_outline | Input for book plan generation |
| `ChaptersOverviewInput` | topic, goal, book_name, full_outline, book_plan, chapters | Input for chapters overview generation |
| `SingleChapterPlanInput` | topic, goal, book_name, full_outline, book_plan, chapters_overview, chapter_name, chapter_number, total_chapters | Input for individual chapter plan generation |
| `SectionPlansInput` | topic, goal, book_name, book_plan, chapters_overview, chapter_plan, chapter_name, sections, subsections_by_section | Input for section plans generation |
| `SubsectionInput` | topic, goal, book_name, audience, full_outline, book_plan, chapters_overview, chapter_name, chapter_plan, section_name, section_plan, subsection_name | Input for subsection generation (with full context) |
| `SectionIntroInput` | topic, book_name, chapter_name, section_name, section_plan, subsection_names, intro_style | Input for section intro generation |
| `ChapterIntroInput` | topic, book_name, book_plan, chapters_overview, chapter_name, chapter_number, total_chapters, chapter_plan, section_names | Input for chapter intro generation |

### Output Models
| Model | Fields | Purpose |
|-------|--------|---------|
| `DeepHierarchy` | concepts (list of ConceptDeep) | 3-level outline structure |
| `ReorganizedOutline` | should_reorganize, reasoning, chapter_order | Outline reorganization decision and new order |
| `BookPlan` | book_summary, narrative_arc, chapter_connections | High-level book plan |
| `ChaptersOverview` | narrative_flow, chapter_briefs (list of ChapterBrief) | High-level overview of all chapters for coherence |
| `AllChapterPlans` | chapter_plans (list of ChapterPlan) | Plans for all chapters (combined) |
| `ChapterSectionPlans` | chapter_name, section_plans (list of SectionPlan) | Section plans for one chapter |
| `SubsectionContent` | content | Single subsection content from one branch |
| `ConsolidatedSubsection` | content | Best/synthesized subsection from multi-branch consolidation |
| `SectionIntro` | introduction | Section introduction (2-3 paragraphs) |
| `ChapterIntro` | introduction | Chapter introduction that puts it in book context |

### Planning Models
| Model | Fields | Purpose |
|-------|--------|---------|
| `ChapterBrief` | chapter_name, brief_role, key_concepts, builds_on, leads_to | Brief overview of a chapter's role (used in ChaptersOverview) |
| `ChapterPlan` | chapter_name, chapter_summary, role_in_book, connection_to_previous, connection_to_next | Detailed plan for a single chapter |
| `SectionPlan` | section_name, section_summary, role_in_chapter, subsections_overview | Plan for a single section |

### Intermediate Models
| Model | Fields | Purpose |
|-------|--------|---------|
| `ConceptExtractor` | main_concepts, thinking | Branch output for concept extraction |
| `MergedConcepts` | main_concepts | Deduplicated concept list |
| `HierarchicalConcepts` | concepts (list of ConceptWithSubconcepts), thinking | 2-level hierarchy |
| `ConceptDeep` | concept, subconcepts (list of SubconceptWithDetails) | Concept with nested subconcepts |

---

## Output Directory Structure

Each run creates a timestamped directory under `output/`:

```
output/
└── YYYYMMDD_HHMMSS/
    ├── 00_topic.txt                    # Input topic, goal, book name
    ├── 00_test_mode.txt                # Test mode indicator (if enabled)
    ├── 01_outline.json                 # Full outline (JSON)
    ├── 01_outline.txt                  # Full outline (readable)
    ├── 01_outline_reorganized.json     # Reorganized outline (if changed)
    ├── 01_outline_reorganized.txt      # Reorganized outline (if changed)
    ├── 02_book_plan.json               # Book-level plan (JSON)
    ├── 02_book_plan.txt                # Book-level plan (readable)
    ├── 02_chapters_overview.json       # Chapters overview for coherence (JSON)
    ├── 02_chapters_overview.txt        # Chapters overview (readable)
    ├── 02_chapter_plan_01_*.json       # Individual chapter plans (JSON)
    ├── 02_chapter_plan_02_*.json
    ├── ...
    ├── 02_chapter_plans.json           # All chapter plans combined (JSON)
    ├── 02_section_plans_*.json         # Section plans per chapter
    ├── 03_section_001_*.txt            # Sections (intro + subsections)
    ├── 03_section_002_*.txt
    ├── ...
    ├── 04_chapter_*.txt                # Chapters (intro + sections)
    ├── ...
    ├── book_cover.png                  # Generated book cover image
    ├── 06_full_book.txt                # Final combined book (Markdown)
    └── 06_full_book.pdf                # Final combined book (PDF with cover)
```

---

## Key Design Decisions

### Why outline reorganization?
The initial outline extraction captures all relevant concepts, but the order may not reflect the natural evolution of ideas. Reorganization analyzes the outline to:
- **Respect temporal evolution**: For topics with historical development, earlier concepts come first
- **Build conceptual foundations**: Prerequisites and fundamentals appear before advanced topics
- **Improve narrative flow**: The book tells a coherent story from beginning to end

This step only reorganizes if it makes sense for the topic. For topics without clear evolution patterns, the original order is preserved.

### Why full outline for planners, short outline for book display?
The system uses two outline formats:
- **Full outline** (3 levels: concepts → subconcepts → subsubconcepts): Used by planners (book plan, chapters overview, chapter plans) so they can see ALL topics that will be covered
- **Short outline** (2 levels: concepts → subconcepts): Used for book display (introduction, table of contents) where subsection detail is too granular

This ensures planners have complete visibility when designing the book structure, while the book itself shows a cleaner, more readable table of contents.

### Why multi-branch concept extraction?
Using 8 parallel generators with high temperature produces diverse concept lists. Merging and deduplicating gives comprehensive coverage that a single pass might miss.

### Why hierarchical planning?
Planning at four levels (book → chapters overview → chapter plans → sections) ensures:
- The book has a coherent narrative arc from start to finish
- All chapters are planned with awareness of each other (via chapters overview)
- Each chapter gets focused individual attention (via per-chapter planning)
- Each section understands how it contributes to its chapter
- No overlap or redundancy between parts

### Why two-stage chapter planning?
Chapter planning uses a two-stage approach:
1. **Chapters Overview (one-shot)**: Generate a high-level overview of ALL chapters in one LLM call. This ensures coherence - the LLM sees all chapters together and can plan how they connect, what builds on what, and the overall narrative flow.
2. **Individual Chapter Plans (per-chapter)**: Generate detailed plans for each chapter individually, using the overview as context. This ensures quality - each chapter gets focused attention, and the plan uses the exact chapter name (no name drift issues).

This combines the benefits of one-shot coherence with per-chapter quality and reliability.

### Why pass full context to direct write?
Each section writer receives the complete planning hierarchy:
- **Direct write**: book plan + chapters overview + chapter plan + section plan + topic names

This allows the writer to:
- Understand where the content fits in the book's narrative
- Avoid repeating content from other parts
- Write content that flows naturally with adjacent material
- Maintain consistency with the overall book goals
- **Maintain comprehensive depth** - knowing what each section should accomplish prevents content condensation

### Why generate subsections separately with full context?
Instead of writing whole sections at once, each subsection is generated independently because:
- **More detail and rigor**: Each subsection gets focused attention for comprehensive coverage
- **Full planning context**: Each subsection receives book plan, chapters overview, chapter plan, section plan, AND the full outline
- **Multi-branch quality**: 3 parallel versions with consolidation ensures the best explanation
- **No compression**: When a whole section is written at once, topics may get uneven treatment
- **Natural assembly**: Full context means subsections fit together without rewriting

### Why multi-branch generation for subsections?
Using the same synalinks pattern as outline generation:
1. Generate 3 versions in parallel with temperature=1.0 for diversity
2. Merge branches with `&` operator
3. Consolidate with a final generator that selects/refines the best version

This ensures:
- Diversity in explanations and examples
- Selection of the most comprehensive version
- Ability to synthesize the best elements from multiple branches

### Why chapter and section introductions?
- **Chapter intro**: Places the chapter in the context of the ENTIRE BOOK narrative, explains what the reader has learned so far, previews what's ahead
- **Section intro**: Sets context for the section's topics, explains why they matter, previews what the reader will learn

These intros make the book flow naturally without needing a separate rewriting pass.

### Why assembly by concatenation (no rewriting)?
After subsection generation with full context:
- Each subsection already knows where it fits in the book's narrative
- Introductions handle transitions between sections and chapters
- Simple concatenation produces coherent chapters
- Avoids content compression that occurs during "rewrite" passes

### Why apply style during subsection generation (not as separate pass)?
Testing showed that a separate styling pass caused significant content compression:
- Chapters lost 25-55% of their content when restyled
- The LLM interpreted "rewrite in this style" as "summarize in this style"
- By applying style during subsection generation, we get both style AND depth
- Style instructions are prepended to depth requirements, making it clear that style ≠ shorter

### Why concept enrichment after merging?
After 8 branches extract concepts and they're merged, a dedicated enrichment step reviews the list and adds any important missing concepts:
- Foundational/theoretical concepts that experts would consider essential
- Historical/evolution concepts showing how the field developed
- Practical/application concepts for real-world use
- Advanced/emerging concepts for cutting-edge coverage
- Cross-cutting themes that span multiple areas
- Methodology concepts covering key techniques

This happens BEFORE subconcept expansion, ensuring comprehensive coverage from the start.

### Why step-by-step, self-contained explanations?
Each explanation must be:
- **Step-by-step**: Complex ideas broken into sequential steps, starting from first principles
- **Self-contained**: All terms defined when first used; readable without prior chapters
- **No assumed knowledge**: Jargon explained immediately; "obvious" steps included
- **In-depth**: Beyond definitions to true understanding; intuition behind formal concepts

This ensures the book is accessible to readers entering at any chapter while maintaining depth.

### Why rotating intro styles at section level?
Without explicit style guidance, LLMs tend to fall into repetitive patterns (e.g., "Imagine..."). Each section gets a different introduction style from a rotating list of approaches:
1. Thought-provoking question
2. Real-world problem/challenge
3. Historical context
4. Connection to previous chapters
5. Surprising fact/counterintuitive insight
6. Practical scenario
7. Problem space definition
8. Comparison to familiar concept

---

## Test Mode

For faster iteration and testing, enable test mode by setting these variables at the top of `book.py`:

```python
TEST_MODE = True  # Set to False for full book generation
TEST_MAX_CHAPTERS = 2  # Number of chapters to rewrite in test mode
```

When `TEST_MODE = True`:
- Only the first `TEST_MAX_CHAPTERS` chapters are generated
- A `00_test_mode.txt` file is created in the output directory

Set `TEST_MODE = False` for full book generation.

---

## Resume from Crash

If the generation crashes partway through, you can resume from where it left off:

```python
RESUME_FROM_DIR = "output/20240115_143022"  # Path to previous run's output directory
```

When resuming:
- The existing output directory is reused
- **Outline**: Loaded from `01_outline.json` if it exists
- **Reorganized Outline**: Loaded from `01_outline_reorganized.json` if it exists
- **Book Plan**: Loaded from `02_book_plan.json` if it exists
- **Chapters Overview**: Loaded from `02_chapters_overview.json` if it exists
- **Chapter Plans**: Individual plans loaded from `02_chapter_plan_NN_*.json`, or combined from `02_chapter_plans.json`
- **Section Plans**: Each chapter's section plans loaded from `02_section_plans_*.json` if exists
- **Sections**: Each section is skipped if `03_section_NNN_*.txt` exists
- **Chapters**: Each chapter is skipped if `04_chapter_*.txt` exists
- Only missing outputs are generated

Set `RESUME_FROM_DIR = None` for a fresh run.

**Tip**: After a crash, check the output directory to see which files were generated, then set `RESUME_FROM_DIR` to that directory path.

---

## Extending the Workflow

### Adding new stages
1. Create input/output data models
2. Add generator function
3. Call from `main()` in appropriate order
4. Add file saving

### Customizing content style
- Adjust generator `instructions` for different writing styles
- Modify `ChapterOutput` instructions to change chapter tone/format
- Add style parameters to input models as needed

### Parallel processing
The current implementation is sequential. For parallel section writing:
```python
results = await asyncio.gather(*[write_section(s) for s in sections])
```

---

## Dependencies

Install required packages:

```bash
pip install synalinks python-dotenv markdown weasyprint google-genai
```

**Note:** `weasyprint` requires some system dependencies for PDF generation:

- **macOS:** `brew install pango`
- **Ubuntu/Debian:** `apt-get install libpango-1.0-0 libpangocairo-1.0-0`
- **Windows:** See [WeasyPrint documentation](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)

You also need a `.env` file with your API keys:
```
GEMINI_API_KEY=your_key_here
```

The `GEMINI_API_KEY` is used for both the LLM (via synalinks/litellm) and cover image generation (via Imagen 4.0).
