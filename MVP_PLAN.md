# MVP Website Plan: Personal Knowledge Synthesizer

## Product Vision

**Tagline**: "Learn any field. Apply it to yours."

**Core Value Proposition**:
For curious, self-directed minds who want to deeply understand a field but find information scattered across papers, blogs, videos, and podcasts — we synthesize it into a coherent, personalized book tailored to your background, goals, **and your specific domain of application**.

**The Key Insight**:
Generic books teach you *about* a topic. We teach you how to *apply* it to YOUR world.

> "I don't just want to learn neuro-symbolic AI. I want to learn how to use it for building enterprise AI agents."

> "I don't just want to understand quantum computing. I want to know what it means for cryptography in my fintech startup."

> "I don't just want to read about knowledge graphs. I want to apply them to drug discovery in my biotech research."

**This is the killer feature**: Every book ends with applied chapters specific to YOUR domain.

---

## Target User (ICP)

**Who they are:**
- Indie researchers & intellectually curious professionals
- Technical founders exploring new domains
- Investors doing deep dives
- Advanced hobbyists ("serious amateurs")
- ML engineers, developers learning new fields

**What they value:**
- Depth over breadth
- Structure and mental models
- Understanding, not just summaries
- Permanent artifacts over subscriptions
- Source transparency

**Pain points:**
- Information is fragmented (papers, blogs, videos, podcasts)
- Generic books don't apply to their specific domain/use case
- Spend 100s of hours consuming content, still lack coherent mental model
- Existing AI summaries are shallow

---

## MVP Feature Set

### Core Flow (V1)

```
1. User Input
   ├── Topic: "Neuro-symbolic AI"
   ├── Goal: "Understand how to combine LLMs with knowledge graphs"
   ├── Focus: "Agentic reasoning, RAG, practical implementation"
   ├── Background: "ML engineer, familiar with transformers"
   └── 🎯 Application Domain: "Building AI agents for enterprise"  ← THE KEY INPUT

2. Outline Generation
   ├── AI generates comprehensive outline
   ├── User can edit/approve
   ├── Prioritization by focus areas
   ├── Chapter selection (if limited)
   └── 🎯 Applied chapters generated for their domain

3. Book Generation
   ├── Hierarchical planning
   ├── Quality-controlled content
   ├── Section-by-section with depth
   ├── Examples translated to their domain context
   └── 🎯 Final "Application" chapters: "Neuro-symbolic AI for Enterprise Agents"

4. Delivery
   ├── PDF download
   ├── Web reader (optional)
   └── Raw markdown (for power users)
```

### The "Applied Domain" Difference

**Without domain application** (generic book):
```
Chapter 15: Knowledge Graphs in Practice
- General examples
- Abstract use cases
- "This could be applied to..."
```

**With domain application** (personalized book):
```
Chapter 15: Knowledge Graphs for Enterprise AI Agents
- How to model enterprise workflows as knowledge graphs
- Integrating with existing enterprise systems (SAP, Salesforce)
- Case study: Building an agent that navigates corporate policies
- Code examples using LangChain + Neo4j for enterprise
```

**This is not just personalization. It's translation.**
We translate abstract knowledge into their professional language.

### MVP Pages

1. **Landing Page** - Value prop, demo, pricing
2. **Book Builder** - Multi-step form for inputs
3. **Outline Review** - Interactive outline editing
4. **Generation Status** - Progress tracking
5. **Library** - User's generated books
6. **Book Viewer** - Read online (optional for V1)

---

## Pricing Model (V1)

### Pay-per-Book (Primary)

| Tier | Pages | Price | Features |
|------|-------|-------|----------|
| **Field Guide** | 50-80 | $49 | Core synthesis, 8-10 chapters |
| **Deep Dive** | 100-200 | $99 | Comprehensive, 15-20 chapters, **1 applied domain chapter** |
| **Masterwork** | 200-400 | $199 | Full depth, **3 applied domain chapters**, source bibliography |

### Add-ons

| Add-on | Price | Description |
|--------|-------|-------------|
| **🎯 Applied Domain Chapter** | $29 | Additional "Apply to X" chapter (e.g., "...for Healthcare", "...for Robotics") |
| **🎯 Multi-Domain Bundle** | $69 | 3 additional applied chapters |
| Update Pass | $19 | Re-run with latest sources |
| Source Bibliography | $9 | Curated reading list with annotations |
| Multiple Formats | $9 | EPUB + MOBI + Markdown |

### Domain Application Examples

The same core book can be applied to completely different domains:

**Core Topic: Neuro-symbolic AI**

| User's Domain | Applied Chapter Title |
|---------------|----------------------|
| Enterprise Software | "Building Symbolic-Neural Agents for Enterprise Automation" |
| Healthcare | "Neuro-symbolic Reasoning for Clinical Decision Support" |
| Legal Tech | "Combining LLMs with Legal Ontologies for Contract Analysis" |
| Robotics | "Symbolic Planning with Neural Perception for Robot Tasks" |
| Finance | "Knowledge Graphs + LLMs for Financial Risk Assessment" |
| Education | "Adaptive Learning Systems with Neuro-symbolic Tutors" |

**This is where the real value lives.**

### Optional Subscription (V2)

- $19/mo - "Living Library"
- Continuous updates as field evolves
- Unlimited regenerations
- Add chapters on demand

---

## Tech Stack Recommendation

### Frontend
- **Next.js 14** - React with App Router
- **Tailwind CSS** - Rapid styling
- **Shadcn/ui** - Component library
- **Framer Motion** - Animations

### Backend
- **Python/FastAPI** - API server (existing book_generator)
- **Celery + Redis** - Job queue for long-running generation
- **PostgreSQL** - User data, book metadata
- **S3/R2** - Book file storage

### Auth & Payments
- **Clerk** or **NextAuth** - Authentication
- **Stripe** - Payments (one-time + subscriptions)

### Infrastructure
- **Vercel** - Frontend hosting
- **Railway** or **Fly.io** - Backend API
- **Cloudflare R2** - File storage (cheaper than S3)

---

## MVP User Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         LANDING PAGE                            │
│                                                                 │
│              "Learn any field. Apply it to yours."              │
│                                                                 │
│    ┌─────────────────────────────────────────────────────┐     │
│    │  I want to learn [neuro-symbolic AI    ▼]           │     │
│    │  and apply it to [enterprise AI agents ▼]           │     │
│    │                                                     │     │
│    │              [Create My Book →]                     │     │
│    └─────────────────────────────────────────────────────┘     │
│                                                                 │
│  "The book you'd write if you had 6 months and read everything" │
│                                                                 │
│  [See Demo: Neuro-symbolic AI for Agent Builders]              │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BOOK BUILDER                             │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  Step 1: What do you want to learn?                            │
│  ═══════════════════════════════════════════════════════════   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Topic: [Neuro-symbolic AI                              ]│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  Step 2: 🎯 Where will you APPLY this? (This is the magic)    │
│  ═══════════════════════════════════════════════════════════   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Your domain: [Building enterprise AI agents           ]│   │
│  │                                                         │   │
│  │ Examples: "healthcare diagnostics", "legal tech",       │   │
│  │ "robotics", "financial analysis", "education tech"     │   │
│  └─────────────────────────────────────────────────────────┘   │
│  💡 We'll include dedicated chapters applying every concept   │
│     to YOUR specific domain                                    │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  Step 3: What's your specific goal?                            │
│  ═══════════════════════════════════════════════════════════   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ I want to understand how to combine LLMs with          │   │
│  │ knowledge graphs for building reasoning agents...      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 4: What areas should we focus on? (optional)             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ☑ LLMs + symbolic reasoning                            │   │
│  │ ☑ Knowledge graphs                                     │   │
│  │ ☑ Agentic architectures                                │   │
│  │ ☐ Probabilistic reasoning                              │   │
│  │ ☐ Program synthesis                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Step 5: Your background (so we calibrate depth)               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [ML engineer ▼] familiar with [transformers, Python   ]│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│                    [Generate Outline →]                         │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTLINE PREVIEW                            │
│                                                                 │
│  Your book: "Neuro-symbolic AI for Agent Builders"             │
│  Estimated: 150-200 pages | 18 chapters                        │
│                                                                 │
│  □ 1. Historical Evolution of AI Paradigms                     │
│  ☑ 2. Limitations: Why Pure Approaches Fail                    │
│  ☑ 3. Knowledge Graphs: The Symbolic Foundation                │
│  ☑ 4. LLMs Meet Symbolic Reasoning                             │
│  ☑ 5. RAG: Retrieval as Symbol Access                          │
│  ☑ 6. Agentic Architectures with Symbolic Backbones            │
│  ...                                                            │
│                                                                 │
│  [Edit Outline]  [Select Chapters]  [Proceed to Payment →]     │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CHECKOUT                                │
│                                                                 │
│  Your Personal Book                                             │
│  "Neuro-symbolic AI for Agent Builders"                        │
│  18 chapters • ~180 pages                                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Deep Dive Package                              $99     │   │
│  │ ☑ Full book PDF                                        │   │
│  │ ☑ Markdown source                                      │   │
│  │ ☐ Add: Applied to Enterprise (+$29)                    │   │
│  │ ☐ Add: Source Bibliography (+$9)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│                      Total: $99                                 │
│                    [Pay with Stripe]                            │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GENERATION STATUS                            │
│                                                                 │
│  ⏳ Generating your book...                                     │
│                                                                 │
│  ████████████░░░░░░░░ 45%                                      │
│                                                                 │
│  ✓ Outline finalized                                           │
│  ✓ Book plan created                                           │
│  ✓ Chapter 1-8 complete                                        │
│  → Writing Chapter 9: RAG Architectures...                     │
│  ○ Chapters 10-18                                              │
│  ○ Final assembly                                              │
│                                                                 │
│  Estimated time remaining: ~15 minutes                         │
│  We'll email you when it's ready!                              │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR LIBRARY                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📚 Neuro-symbolic AI for Agent Builders                │   │
│  │ Generated: Feb 2, 2026 • 182 pages                      │   │
│  │ [Download PDF] [Read Online] [Get Updates]              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📚 Quantum Computing for Software Engineers            │   │
│  │ Generated: Jan 15, 2026 • 95 pages                      │   │
│  │ [Download PDF] [Read Online] [Get Updates]              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Differentiation & Messaging

### What We're NOT
❌ "AI-written book"
❌ "Summary tool"
❌ "Knowledge aggregator"
❌ "Another ChatGPT wrapper"
❌ "Generic textbook generator"

### What We ARE
✅ "Personal research synthesis"
✅ "A book written for your curiosity AND your career"
✅ "From scattered ideas to applied expertise"
✅ "Learn any field. Apply it to yours."
✅ "Translation layer between abstract knowledge and your domain"

### Hero Copy Options

> **"Learn any field. Apply it to yours."** ← Primary

> "The book that teaches you X *for your world*."

> "If this book didn't exist, we wrote it for you — and for your use case."

> "Stop learning theory. Start applying knowledge."

> "Every chapter ends with: how does this apply to YOUR domain?"

> "Generic books teach you about. We teach you how to apply."

### Domain-Focused Messaging Examples

**For the landing page:**
> "I learned neuro-symbolic AI. But I needed to know how it applies to **legal tech**.
> This book gave me that."
> — Sarah, Legal AI Founder

**For the builder:**
> "Tell us your domain. We'll translate every concept into YOUR professional language."

**For checkout:**
> "Your book includes 2 applied chapters specifically for: **Enterprise AI Agents**"

---

## MVP Milestones

### Week 1-2: Foundation
- [ ] Set up Next.js project with Tailwind
- [ ] Landing page with waitlist
- [ ] Basic auth (Clerk)
- [ ] Book builder form UI

### Week 3-4: Backend Integration
- [ ] FastAPI wrapper around book_generator
- [ ] Job queue for async generation
- [ ] Progress tracking WebSocket/polling
- [ ] File storage (R2)

### Week 5-6: Core Flow
- [ ] Outline preview & editing
- [ ] Stripe checkout integration
- [ ] Generation status page
- [ ] Email notifications

### Week 7-8: Polish & Launch
- [ ] User library page
- [ ] PDF viewer/download
- [ ] Error handling & edge cases
- [ ] Beta user testing
- [ ] Launch to waitlist

---

## Demo Strategy

Create ONE exceptional demo book:
- **Topic**: Neuro-symbolic AI
- **Focus**: LLMs + Knowledge Graphs + Agents
- **Make it public** as the showcase
- Let users browse chapters
- "Want one like this? Build yours →"

---

## Open Questions

1. **Generation time**: How long is acceptable? (Currently ~30-60 min for full book)
   - Mitigation: Email when ready, show progress, allow background generation

2. **Quality consistency**: How to ensure every book is good?
   - Mitigation: Quality control loop, human review for first N books

3. **Source grounding**: Should we cite specific papers/sources?
   - V1: No (too complex)
   - V2: Yes, as premium feature

4. **Regeneration policy**: What if user doesn't like the result?
   - One free regeneration? Partial refund?

5. **Book length control**: User expectation vs. actual output
   - Clear estimates upfront, set expectations

---

## Next Steps

1. Finalize tech stack decisions
2. Create wireframes/mockups
3. Set up project repository
4. Build landing page + waitlist
5. Integrate book_generator as API
6. Beta test with 10-20 users
7. Iterate based on feedback
8. Launch
