# Known Issues & Improvements

Tracking file for identified issues from code review (2026-02-07).

## CRITICAL

- [x] **#2 XSS Vulnerability in ConceptGraph3D.tsx** — String interpolation with unsanitized node data into HTML labels. Fixed: escape HTML entities before rendering.
- [x] **#3 CORS Misconfiguration in api_server.py** — `allow_methods=["*"]` too permissive, origins hardcoded. Fixed: explicit methods, env-driven origins.
- [ ] **#1 Exposed API Keys in .env** — Real API keys (OpenAI, Gemini, Perplexity, OpenRouter) present in .env file. Rotate all keys immediately and verify they were never committed to git history.
- [ ] **#4 No Authentication on API Server** — Anyone can submit generation requests and download outputs. No rate limiting.

## HIGH

- [ ] **#5 `pipeline.py` generate_book() is 750+ lines** — Should be broken into stage-specific functions or modules.
- [ ] **#6 Inconsistent Error Handling** — Mix of return None, raise, and log-and-continue. `traceback.print_exc()` in pipeline.py should use `logger.exception()`.
- [x] **#7 In-Memory Job Store** — Replaced in-memory dict with SQLite-backed `JobStore` (`job_store.py`). WAL mode, thread-safe, survives restarts. DB path configurable via `JOB_STORE_DB` env var.
- [x] **#8 No Input Validation on API Routes** — Added Pydantic validators with length limits and enum constraints on `GenerateRequest`. Added `Config.__post_init__()` validation. Frontend routes now validate lengths, types, UUID format, and email format before forwarding.
- [x] **#9 Hardcoded Magic Numbers in content.py** — `full_research[:6000]`, `max_attempts = 5`, etc. Fixed: extracted to `constants.py`.
- [ ] **#10 No Test Suite** — Only 2 integration tests, no unit tests, no pytest config, no CI/CD.

## MODERATE

- [ ] **#11 models.py is 1000+ lines** — Should split into submodules (models/vision.py, models/outline.py, etc.).
- [x] **#12 Frontend page.tsx is 850+ lines** — Extracted into 7 component files (`HeroSection`, `UserStoriesSection`, `SynthesisSection`, `RoadmapSection`, `WaitlistSection`, `Footer`) + `constants/userStories.ts`. `page.tsx` reduced to ~100-line composition shell.
- [x] **#13 No Form Persistence in Builder** — Added localStorage persistence (`polaris-builder` key). Form data, job ID, and step restored on mount, persisted on change, cleared on reset.
- [x] **#14 Frontend Polling is Too Aggressive** — Replaced fixed 3s `setInterval` with exponential backoff `setTimeout` chain (3s initial, 1.5x multiplier, 30s cap, 10 error max).
- [ ] **#15 Missing Accessibility** — No form labels, 3D graph inaccessible, color-only indicators, broken heading hierarchy.
- [ ] **#16 No Image Optimization** — Uses `<img>` instead of Next.js `<Image>`. No lazy loading or WebP.
- [ ] **#17 Waitlist API is a Stub** — In-memory storage, no database, no email service.
- [ ] **#18 vision.py Copy-Pasted Instruction Blocks** — Three near-identical blocks for practitioner/academic/hybrid. Should parameterize.

## LOW

- [ ] **#19 Type hints could be stricter** — Many `Optional[object]` and untyped `dict` across Python codebase.
- [ ] **#20 cover.py hardcoded pixel ratios** — Font sizes based on magic number ratios.
- [ ] **#21 pdf.py silent LaTeX fallback** — If latex2mathml is missing, math rendering silently skipped.
- [ ] **#22 No requirements-dev.txt** — Test dependencies not separated.
- [ ] **#23 tools/convert_to_pdf.py hardcoded paths** — Input/output paths not configurable via CLI args.
- [ ] **#24 Missing ESLint a11y plugin** — No eslint-plugin-jsx-a11y configured.
- [ ] **#25 Framer Motion infinite animations** — Could cause jank on low-end devices.
