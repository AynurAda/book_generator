# Polaris

> **Take anyone to the cutting edge of any knowledge domain. In hours, not years.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Gemini 3](https://img.shields.io/badge/Gemini_3-API-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Built with Synalinks](https://img.shields.io/badge/Built%20with-Synalinks-orange)](https://github.com/SynaLinks/synalinks)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## The Problem

The book you need doesn't exist.

The knowledge is out there — scattered across papers, videos, blogs, and textbooks. But none of it is written for **your specific goal**, in **your domain**, at **your level**, in **your language**.

A decade-long pipeline stands between breakthrough and accessibility:
1. Research happens → 2. Years of validation → 3. Practitioners adopt → 4. Cross-domain diffusion → 5. Textbooks → 6. Courses → 7. **Finally** you can learn it

**We collapse this entire pipeline to hours.**

---

## What Polaris Does

**Synthesize the exact book each person needs — from wherever they are to the cutting edge.**

Not personalized. Not adapted. **Synthesized from scratch** for one person:

| Dimension | How It Shapes Your Book |
|-----------|------------------------|
| **Your exact knowledge state** | What you know, what you think you know but don't, the gaps you don't know exist |
| **Your specific goal** | Not "learn ML" but "build a trading bot using reinforcement learning for illiquid markets" |
| **Your domain** | Every example, analogy, and case study speaks your professional language |
| **Your learning style** | Visual, textual, example-driven, theory-first — however your brain works |
| **Your constraints** | 20-minute focus windows, accessibility needs, your pace |

---

## Gemini 3 Features Used

Polaris orchestrates **four Gemini 3 capabilities** across a 16-stage neuro-symbolic pipeline:

| Gemini Capability | Model / API | What It Does |
|---|---|---|
| **Deep Research** | `deep-research-pro-preview-12-2025` | Discovers cutting-edge papers and frameworks *before* the outline is finalized |
| **Gemini 3 Flash** | `gemini-3-flash-preview` | Powers 90+ type-safe generators via Synalinks — vision, planning, critique, content |
| **Gemini 3 Pro Image** | `gemini-3-pro-image-preview` | Generates book covers (15 styles) and in-chapter illustrations |
| **Search Grounding** | Gemini + Google Search | Verifies citations against primary sources; resolves arXiv paper IDs |

---

## Architecture

```
 1. Deep Research          Gemini discovers cutting-edge papers
 2. Book Vision            Reader mode decision (practitioner/academic/hybrid)
 3. Draft Outline          Initial structure for research queries
 4. Research-Informed      Outline rebuilt from discovered papers
 5. Outline Approval       Interactive review
 6. Reorganization         Conceptual flow ordering
 7. Prioritization         Select most important chapters
 8. Subsubconcepts         Generate subsection detail
 9. Paper Assignment       Each paper → one chapter (prevents repetition)
10. Hierarchical Planning  Book → chapter → section plans with self-critique
11. Stage 2 Research       arXiv papers + optional knowledge graph (MCP)
12. Citation Pipeline      Plan claims → verify with Gemini Search → constrain content
13. Content Generation     Bottom-up: subsections → sections → chapters
14. Illustrations          Mermaid diagrams + AI images
15. Introduction + Cover   Book intro and AI-generated cover
16. PDF Assembly           Markdown → HTML → PDF
```

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for full technical details.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/AynurAda/book_generator.git
cd book_generator

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Generate
python main.py --config configs/neurosymbolic.yaml --chapters 3
```

Your book will be in `output/<timestamp>/06_full_book.pdf`

### Web Platform

```bash
# Start backend
python run_api.py

# Start frontend (separate terminal)
cd web && npm install && npm run dev
```

Visit `http://localhost:3000` for the Polaris web builder.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Research-First Structure** | Gemini Deep Research discovers papers BEFORE the outline is finalized |
| **Reader Mode Intelligence** | Synalinks Branch decides practitioner/academic/hybrid, reshaping the entire book |
| **Two-Level Anti-Repetition** | Each paper → one chapter, each concept → one subsection, each subsection → unique example domain |
| **Claim-First Citations** | Plan claims before writing, verify with Gemini Search, reject unverified |
| **90+ Type-Safe DataModels** | Synalinks prevents hallucination cascades across 16 pipeline stages |
| **Self-Critique Loops** | Mode-aware critique adapts to chapter roles (IMPLEMENTATION vs ACADEMIC vs FRONTIERS) |
| **15 Cover Styles** | From minimalist to cyberpunk, generated by Gemini 3 Pro Image |
| **5 Writing Styles** | WaitButWhy, O'Reilly, textbook, practical, For Dummies |
| **Resumable** | All intermediates cached — resume from any stage |

---

## Demo Notes

> **Hackathon submission** — All 16 pipeline stages are implemented and functional. Two features are disabled in the live demo via config toggles (not missing code):
> - **In-chapter illustrations** — Disabled for faster generation. Code: `book_generator/illustrations.py`
> - **Knowledge graph (mcp-graphiti)** — Requires Neo4j infrastructure. Code: `book_generator/research/stage2.py`
>
> See [DEVPOST.md](DEVPOST.md#demo-scope--roadmap) for full feature status table.

---

## Tech Stack

- **[Synalinks](https://github.com/SynaLinks/synalinks)** — Neuro-symbolic LLM framework (DataModel, Generator, Branch, Decision)
- **[Google Gemini 3](https://ai.google.dev/)** — Content generation, Deep Research, image generation, Search Grounding
- **[FastAPI](https://fastapi.tiangolo.com/)** — REST API with background job tracking
- **[Next.js 14](https://nextjs.org/)** — Web platform (App Router, Tailwind, Shadcn/ui, Framer Motion)
- **[WeasyPrint](https://weasyprint.org/)** — PDF generation
- **[mcp-graphiti](https://github.com/rawr-ai/mcp-graphiti)** — Optional knowledge graph via MCP

---

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Full technical architecture (16 stages, data flow, design decisions)
- **[DEVPOST.md](DEVPOST.md)** — Hackathon submission writeup
- **[MVP_PLAN.md](MVP_PLAN.md)** — Product roadmap

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>Knowledge, perfectly tailored. For everyone.</b><br>
  <i>Take anyone to the cutting edge. No barriers.</i>
</p>
