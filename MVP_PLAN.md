# MVP Website Plan: Knowledge Synthesizer

## Product Vision

**Tagline**: "Synthesize any field. Through the lens of yours."

**What We Do**:
We synthesize scattered knowledge — papers, blogs, videos, podcasts, documentation — into a coherent, structured book written entirely through the lens of YOUR domain.

**The Synthesis Problem**:
Knowledge exists. Understanding doesn't come pre-packaged.

You want to learn neuro-symbolic AI. The information is out there — hundreds of papers, dozens of blog posts, conference talks, Twitter threads, textbooks. But:
- It's fragmented across sources
- Each source assumes different backgrounds
- Nobody connects it to YOUR world
- You spend 100+ hours and still lack a coherent mental model

**Our Solution**:
We don't summarize. We don't aggregate. We **synthesize**.

We take fragmented knowledge and forge it into a unified, coherent book — one that speaks YOUR professional language, uses YOUR domain's examples, and builds mental models YOU can apply.

---

## The Core Insight: Domain-Native Learning

This is not "a book with some applied chapters at the end."

This is **every chapter, every example, every explanation** written through the lens of your domain.

**Generic book on Neuro-symbolic AI:**
```
Chapter 5: Knowledge Graph Fundamentals
- Nodes represent entities
- Edges represent relationships
- Example: A social network graph with users and friendships
- Example: A movie database with actors and films
```

**Your book — "Neuro-symbolic AI for Enterprise Agent Builders":**
```
Chapter 5: Knowledge Graphs for Enterprise Systems
- Nodes represent business entities (customers, products, policies)
- Edges represent business relationships (owns, governs, requires)
- Example: Modeling SAP hierarchies as knowledge graphs
- Example: Representing compliance rules as queryable graph structures
- Code: Building an enterprise ontology with LangChain + Neo4j
```

**Same concepts. Your language. Your examples. Your world.**

---

## What is Synthesis?

Synthesis is NOT:
- ❌ Summarization (making things shorter)
- ❌ Aggregation (piling things together)
- ❌ Translation (changing languages)
- ❌ AI-generated content (hallucinated text)

Synthesis IS:
- ✅ **Integration**: Connecting ideas from multiple sources into coherent whole
- ✅ **Structuring**: Organizing fragmented knowledge into learnable progression
- ✅ **Contextualization**: Grounding abstract concepts in YOUR concrete domain
- ✅ **Mental Model Building**: Creating frameworks you can think with

> "Synthesis is the art of making the implicit connections explicit,
> and making abstract knowledge concrete in YOUR context."

---

## Target User (ICP)

**Who they are:**
- Indie researchers & intellectually curious professionals
- Technical founders exploring adjacent domains
- Investors doing deep dives before major decisions
- ML engineers learning new paradigms
- Domain experts adding technical capabilities

**The Synthesis Mindset:**
- They don't want to be spoon-fed — they want to deeply understand
- They value structure and mental models over facts
- They know information exists — they need it organized and contextualized
- They're willing to pay for time saved and understanding gained

**Their Pain:**
- "I've read 50 papers and still can't explain this field coherently"
- "Every resource assumes I'm someone else"
- "I understand the theory but can't connect it to my work"
- "I need a book that doesn't exist"

---

## MVP Feature Set

### Core Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. DEFINE YOUR SYNTHESIS                                       │
│                                                                 │
│  Topic: What field do you want to master?                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Neuro-symbolic AI                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Domain Lens: Through what professional lens?                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Building enterprise AI agents                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│  💡 Every chapter will use examples from YOUR domain            │
│                                                                 │
│  Goal: What do you want to be able to DO?                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Design hybrid LLM + knowledge graph architectures       │   │
│  │ for enterprise reasoning systems                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Background: What do you already know?                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ML engineer, familiar with transformers and Python      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│                    [Generate Outline →]                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. REVIEW & EDIT YOUR OUTLINE                                  │
│                                                                 │
│  "Neuro-symbolic AI for Enterprise Agent Builders"              │
│  18 chapters • ~180 pages • Tailored to YOUR domain             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ PART I: FOUNDATIONS                                     │   │
│  │ ☑ 1. The Limits of Pure Approaches                      │   │
│  │      └─ Why enterprise AI needs both neural & symbolic  │   │
│  │ ☑ 2. Knowledge Representation for Business              │   │
│  │      └─ Ontologies, taxonomies, enterprise semantics    │   │
│  │                                                         │   │
│  │ PART II: CORE TECHNIQUES                                │   │
│  │ ☑ 3. Knowledge Graphs in Enterprise Context             │   │
│  │      └─ Modeling SAP, Salesforce, business rules        │   │
│  │ ☑ 4. LLMs as Reasoning Engines                          │   │
│  │      └─ Prompt patterns for structured enterprise tasks │   │
│  │ □ 5. Probabilistic Logic (skip for now)                 │   │
│  │ ☑ 6. RAG for Enterprise Knowledge                       │   │
│  │      └─ Connecting LLMs to corporate knowledge bases    │   │
│  │ ...                                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ ✏️  Edit Outline │  │ ➕ Add Chapter   │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                 │
│  You control the structure. Add, remove, reorder, rename.       │
│                                                                 │
│           [Approve & Continue →]    [Regenerate Outline]        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. SYNTHESIS IN PROGRESS                                       │
│                                                                 │
│  ⏳ Synthesizing your book...                                   │
│                                                                 │
│  ████████████████░░░░░░░░ 65%                                  │
│                                                                 │
│  ✓ Outline finalized                                           │
│  ✓ Book structure planned                                      │
│  ✓ Chapters 1-6 synthesized                                    │
│  → Synthesizing Chapter 7: Agentic Architectures...            │
│  ○ Chapters 8-15                                               │
│  ○ Quality review & refinement                                 │
│  ○ Final assembly                                              │
│                                                                 │
│  We'll email you when your synthesis is complete.               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. YOUR SYNTHESIZED KNOWLEDGE                                  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📚 Neuro-symbolic AI for Enterprise Agent Builders      │   │
│  │                                                         │   │
│  │ 182 pages • 15 chapters • Synthesized Feb 2, 2026       │   │
│  │                                                         │   │
│  │ Every example drawn from enterprise AI contexts.         │   │
│  │ Code samples use LangChain, Neo4j, enterprise APIs.     │   │
│  │                                                         │   │
│  │ [📖 Read Online] [⬇️ Download PDF] [📝 Get Markdown]    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Want to synthesize for a different domain?                     │
│  Same topic through a Healthcare lens → [Create Variant]        │
└─────────────────────────────────────────────────────────────────┘
```

### Key Feature: Outline Control

The outline is YOURS to shape:

| Action | What You Can Do |
|--------|----------------|
| **Exclude** | Uncheck chapters you don't need |
| **Add** | Request additional chapters on specific topics |
| **Reorder** | Drag chapters to change learning progression |
| **Rename** | Adjust chapter titles to match your terminology |
| **Expand** | Request deeper coverage of specific sections |
| **Focus** | Mark priority chapters for extra depth |

**Why this matters:**
- You know what you need better than any algorithm
- Your learning path should match YOUR gaps
- Some chapters may be review, others need depth
- The book should fit YOUR mental model

---

## Pricing Model

### Synthesis Tiers

| Tier | What You Get | Price |
|------|-------------|-------|
| **Primer** | 8-10 chapters, ~80 pages, core concepts synthesized for your domain | $49 |
| **Deep Synthesis** | 15-20 chapters, ~180 pages, comprehensive coverage with your domain throughout | $99 |
| **Masterwork** | 25+ chapters, ~350 pages, exhaustive synthesis with advanced topics | $199 |

All tiers include:
- ✅ Full domain adaptation (every chapter, every example)
- ✅ Outline editing before generation
- ✅ PDF + Markdown download
- ✅ One free regeneration

### Add-ons

| Add-on | Price | Description |
|--------|-------|-------------|
| Additional Domain Variant | $39 | Same content, different domain lens (e.g., now for Healthcare) |
| Source Bibliography | $19 | Curated reading list with annotations for going deeper |
| Priority Generation | $29 | Jump the queue, get your book faster |

---

## Product Positioning

### The Synthesis Positioning

**Category**: Knowledge Synthesis Platform

**One-liner**: "We synthesize scattered knowledge into coherent books tailored to your domain."

**Elevator Pitch**:
> "You know that feeling when you've read dozens of papers and blog posts but still can't explain a field coherently? We solve that. We synthesize fragmented knowledge — papers, blogs, videos, documentation — into a structured book written entirely through the lens of YOUR professional domain. Every example, every explanation, speaks your language."

### Positioning Against Alternatives

| Alternative | Their Approach | Our Approach |
|-------------|---------------|--------------|
| **Books** | Generic, one-size-fits-all | Synthesized for YOUR domain |
| **ChatGPT** | Answers questions, no structure | Builds coherent mental models |
| **Courses** | Fixed curriculum, passive | Tailored to your gaps, you control outline |
| **Research** | Time-consuming, fragmented | We do the synthesis, you get the understanding |
| **Summaries** | Shallow, lose nuance | Deep, preserves and connects concepts |

### What We Say vs. Don't Say

**Say:**
- "Synthesize" — implies integration, structure, coherence
- "Through your lens" — domain adaptation
- "Mental models" — understanding, not just information
- "Tailored" — personalization with purpose
- "Coherent" — the key outcome

**Don't Say:**
- "AI-generated" — implies low quality, no human value
- "Summary" — implies shallow
- "Automated" — implies impersonal
- "Content" — implies commodity

### Hero Messages

**Primary:**
> "Synthesize any field. Through the lens of yours."

**Supporting:**
> "The book that doesn't exist — until you need it."

> "From scattered papers to coherent understanding."

> "Stop drowning in information. Start building mental models."

> "Every field, explained in YOUR professional language."

> "We read everything. You get the synthesis."

### Social Proof Angles

> "I needed to understand knowledge graphs for legal tech.
> I'd read 30 papers. Still couldn't connect the dots.
> This gave me the mental model I was missing — in my language."
> — Legal Tech Founder

> "As an investor, I need to go deep fast.
> This synthesized 6 months of research into a weekend read.
> Every example was from my world."
> — Deep Tech VC

---

## Tech Stack

### Frontend
- **Next.js 14** with App Router
- **Tailwind CSS** + **Shadcn/ui**
- **Framer Motion** for polish

### Backend
- **Python/FastAPI** wrapping book_generator
- **Celery + Redis** for async generation
- **PostgreSQL** for users, books, outlines
- **Cloudflare R2** for file storage

### Auth & Payments
- **Clerk** for authentication
- **Stripe** for payments

### Infrastructure
- **Vercel** for frontend
- **Railway** or **Fly.io** for backend
- **Resend** for email notifications

---

## MVP Milestones

### Phase 1: Foundation (Week 1-2)
- [ ] Next.js project setup
- [ ] Landing page with waitlist
- [ ] Core messaging and positioning
- [ ] Demo book showcase

### Phase 2: Book Builder (Week 3-4)
- [ ] Multi-step input form
- [ ] FastAPI wrapper for book_generator
- [ ] Outline generation endpoint
- [ ] Outline preview UI

### Phase 3: Outline Editing (Week 5-6)
- [ ] Interactive outline editor
- [ ] Chapter toggle/reorder
- [ ] Add/remove chapters
- [ ] Save edited outline

### Phase 4: Generation Flow (Week 7-8)
- [ ] Stripe checkout
- [ ] Async generation with Celery
- [ ] Progress tracking (WebSocket/polling)
- [ ] Email on completion

### Phase 5: Delivery (Week 9-10)
- [ ] User library page
- [ ] PDF/Markdown download
- [ ] Basic web reader
- [ ] Beta testing

---

## Demo Strategy

Create ONE exceptional demo synthesis:

**Topic**: Neuro-symbolic AI
**Domain Lens**: Enterprise AI Agent Builders
**Format**: Public, browsable, shows domain adaptation

Let visitors:
- Browse full table of contents
- Read 2-3 sample chapters
- See how examples are domain-adapted
- "Want yours? Tell us your domain →"

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Waitlist signups | 500 before launch |
| Conversion (waitlist → paid) | 10% |
| First-month revenue | $5,000 |
| NPS | 50+ |
| Completion rate | 80% of books downloaded |

---

## Open Questions

1. **Generation time**: Currently 30-60 min. Acceptable with email notification?

2. **Outline editing UX**: How sophisticated? Simple toggles vs. full editor?

3. **Domain validation**: How do we ensure domain adaptation is good?

4. **Regeneration policy**: One free? Unlimited edits before generation?

5. **Multi-domain**: Same core, different lenses — how to price?

---

## Next Steps

1. ✅ Define product positioning (this document)
2. [ ] Create landing page copy
3. [ ] Build waitlist page
4. [ ] Design outline editor mockups
5. [ ] Set up FastAPI endpoints
6. [ ] Generate demo book
7. [ ] Beta test with 10 users
8. [ ] Launch
