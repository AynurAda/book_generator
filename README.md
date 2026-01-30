# Book Generator

AI-powered book generation using the [Synalinks](https://github.com/synalinks/synalinks) framework.

Generate comprehensive, well-structured educational books from a simple topic description. The system uses a multi-stage pipeline with hierarchical planning to ensure coherent content with minimal repetition.

## Features

- **Multi-stage pipeline**: Outline → Reorganization → Planning → Content → Polish → PDF
- **Hierarchical planning**: Book → Chapter → Section plans for coherent narrative
- **Smart reorganization**: Automatically orders chapters by conceptual evolution
- **Professional PDF output**: Styled book with cover, TOC, and proper typography
- **AI-generated covers**: Uses Google's Imagen 4.0 for cover art
- **Resume capability**: Continue from where you left off after interruption
- **Test mode**: Generate a subset for quick iteration

## Installation

### Prerequisites

- Python 3.10+
- System dependencies for WeasyPrint:
  - **macOS**: `brew install pango`
  - **Ubuntu/Debian**: `apt-get install libpango-1.0-0 libpangocairo-1.0-0`
  - **Windows**: See [WeasyPrint docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)

### Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd book-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API key
```

## Usage

### Basic Usage

Edit `main.py` to configure your book:

```python
CONFIG = {
    "topic": "Your Topic Here",
    "goal": "What the book should cover and achieve",
    "book_name": "Your Book Title",
    "subtitle": "A descriptive subtitle",
    "authors": "Author Names",
}
```

Then run:

```bash
python main.py
```

### Command Line Options

```bash
# Generate full book
python main.py

# Test mode (2 chapters only)
python main.py --test

# Test mode with custom chapter count
python main.py --test --chapters 3

# Resume from previous run
python main.py --resume output/20240115_143022
```

### Output

Generated files are saved in `output/YYYYMMDD_HHMMSS/`:

```
output/
└── 20240115_143022/
    ├── 00_topic.txt                # Input configuration
    ├── 01_outline.json             # Generated outline
    ├── 01_outline_reorganized.json # Reorganized outline (if changed)
    ├── 02_book_plan.json           # Book-level plan
    ├── 02_chapter_plans.json       # Chapter plans
    ├── 02_section_plans_*.json     # Section plans
    ├── 03_subsection_*.txt         # Individual subsections
    ├── 04_chapter_*.txt            # Rewritten chapters
    ├── 05_polished_*.txt           # Polished chapters
    ├── book_cover.png              # Generated cover
    ├── 06_full_book.txt            # Final book (Markdown)
    └── 06_full_book.pdf            # Final book (PDF)
```

## Pipeline Stages

```mermaid
flowchart LR
    A[Topic] --> B[Outline]
    B --> C[Reorganize]
    C --> D[Plan]
    D --> E[Generate]
    E --> F[Rewrite]
    F --> G[Polish]
    G --> H[Cover]
    H --> I[PDF]
```

1. **Outline Generation**: Multi-branch extraction → merge → expand to 3 levels
2. **Outline Reorganization**: Reorder chapters by conceptual/temporal evolution
3. **Hierarchical Planning**: Book plan → Chapter plans → Section plans
4. **Subsection Generation**: Generate content with full context
5. **Section Rewriting**: Combine subsections into flowing prose
6. **Chapter Polishing**: Final quality pass for cohesion
7. **Cover Generation**: AI-generated book cover
8. **PDF Assembly**: Professional formatted PDF

See [WORKFLOW.md](WORKFLOW.md) for detailed documentation.

## Project Structure

```
book_generator/
├── __init__.py      # Package initialization
├── config.py        # Configuration management
├── models.py        # Synalinks data models
├── utils.py         # File I/O and helpers
├── outline.py       # Outline generation & reorganization
├── planning.py      # Hierarchical planning
├── content.py       # Content generation & rewriting
├── polish.py        # Chapter polishing
├── cover.py         # Cover image generation
├── pdf.py           # PDF generation
└── pipeline.py      # Main orchestration

main.py              # Entry point
requirements.txt     # Dependencies
WORKFLOW.md          # Technical documentation
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for LLM and image generation |

### Book Configuration

| Field | Description |
|-------|-------------|
| `topic` | The main subject of the book |
| `goal` | What the book should cover and achieve |
| `book_name` | The title of the book |
| `subtitle` | Subtitle for the cover |
| `authors` | Author attribution |
| `test_mode` | Generate limited chapters for testing |
| `test_max_chapters` | Number of chapters in test mode |
| `resume_from_dir` | Directory to resume from |
| `model_name` | LLM model to use |

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with [Synalinks](https://github.com/synalinks/synalinks) framework
- PDF generation by [WeasyPrint](https://weasyprint.org/)
- Cover images by Google Imagen
