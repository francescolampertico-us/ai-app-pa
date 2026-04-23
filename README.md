# Strategitect — Architecture for Public Affairs Strategy

Integrating Generative AI into Public Affairs Practice.

**Author:** Francesco Lampertico — M.A. Political Communication, American University (May 2026)
**Live app:** [ai-app-pa.vercel.app](https://ai-app-pa.vercel.app)

---

## Research Question

> How can Generative Artificial Intelligence be systematically integrated into day-to-day Public Affairs practice?

---

## The Problem

Public affairs professionals operate under compounding pressures: 53% cite political instability as their top challenge, 51% cite information overload, and 38% report teams too small for the volume of work. At the same time, AI adoption in the field remains fragmented — 53.8% of government affairs professionals report using AI, 46.2% do not, and use is heavily dependent on individual initiative rather than systematic integration.

---

## Methodology

The project followed four phases:

1. **Problem Framing** — Five semi-structured expert interviews with public affairs practitioners (VP of Policy, Woodwell Climate Research Center; Managing Director, Clyde; Partner, Beekeeper Group; Partner, Tiber Creek Group; Founder, Unfiltered Media / Co-CEO, Change Agent)
2. **Task Prioritization** — Qualitative transcript analysis and 28-source literature review
3. **Prototype Development** — Modular system design and software development
4. **Testing and Refinement** — Prototype testing and iterative output review

---

## What Was Built

The research identified four application domains for AI integration in PA. Three were implemented as working tools; one (Sentiment Analysis) remains a future opportunity.

| Domain | Status |
|--------|--------|
| Policy Monitoring and Legislative Tracking | ✅ Implemented |
| Stakeholder Mapping and Network Analysis | ✅ Implemented |
| Content Generation and Drafting Support | ✅ Implemented |
| Sentiment Analysis and Public Opinion Tracking | 🔲 Future |

### Tool Catalog

| # | Tool | Domain |
|---|------|--------|
| 1 | Hearing Memo | Intelligence Gathering |
| 2 | Media Clips | Intelligence Gathering |
| 3 | Media Clip Cleaner | Intelligence Gathering |
| 4 | Legislative Tracker | Intelligence Gathering |
| 5 | Influence Tracker | Intelligence Gathering |
| 6 | Background Memo | Intelligence Gathering |
| 7 | Stakeholder Map | Stakeholder Preparation |
| 8 | Stakeholder Briefing | Stakeholder Preparation |
| 9 | Media List Builder | Stakeholder Preparation |
| 10 | Messaging Matrix | Content Generation |

Plus **Remy** — an AI assistant that routes work across tools, collects inputs, and executes pipelines from a single conversational interface.

---

## Tool Design: The DOE Pattern

Every tool follows the same three-phase structure:

- **Directive** — The user specifies intent: topic, entities, date range, format
- **Orchestration** — The tool gathers and processes data via APIs and LLM calls
- **Execution** — The tool produces a review-ready output (DOCX, CSV, or Markdown)

All outputs require human review before use. The system is designed for augmentation, not autonomous judgment.

---

## Tool Pipelines

Tools are designed to chain together:

- **Media Clips → Media Clip Cleaner** — scrape coverage, clean paywalled articles
- **Influence Tracker → Stakeholder Map → Stakeholder Briefing** — disclosure data builds maps, maps feed briefings
- **Legislative Tracker → Hearing Memo** — bill context feeds hearing analysis
- **Background Memo → Messaging Matrix** — research feeds message development

---

## Key Interview Findings

1. **Barriers to adoption** — Resistance stems from professional culture and pricing models, not technical capability. Several firms reported clients banning AI use by contract.
2. **Current use** — AI adds the most value in synthesis and first drafts. Practitioners describe it as a starting point, not a final product.
3. **Limits in practice** — Accuracy, missing context, data sensitivity, and trust remain persistent constraints in high-stakes work.
4. **Future opportunity** — The most promising direction is using AI to test strategy before deployment: message simulation, stakeholder modeling, reputation in AI-mediated environments.

---

## Architecture

### Frontend — Vite + React
**Entry:** `cd web-app && npm run dev` → http://localhost:5173

Self-contained page per tool. All calls go through a shared `useFastApiJob` hook that POSTs inputs to the backend, receives a job ID, and polls for completion every 2 seconds. Results and downloadable artifacts render inline.

### Backend — FastAPI
**Entry:** `cd fastapi-backend && python3 -m uvicorn main:app --reload --port 8000`

- `api/routers/tools.py` — one handler per tool
- `api/routers/jobs.py` — job creation, status polling, artifact serving
- `api/routers/remy.py` — Remy AI assistant endpoint
- Credentials loaded from `toolkit/.env`

### Toolkit — Python
**Entry:** `python3 toolkit/tools/<tool_id>/execution/run.py --help`

Each tool package contains: `tool.yaml` (contract + version), `spec.md` (tool card), `execution/` (Python source), `examples/`, `eval/`.

---

## Repository Structure

```
capstone_project/
├── toolkit/            # Python execution layer — 10 tool packages + QA
├── fastapi-backend/    # REST API wrapping the toolkit (FastAPI + uvicorn)
├── web-app/            # Vite + React frontend — primary interface
├── knowledge/          # Practitioner interviews and literature
├── literature_review/  # 28-source annotated literature review
└── brand-toolkit/      # Design system and output style guidelines
```

---

## Running Locally

```bash
# Backend
cd fastapi-backend
python3 -m uvicorn main:app --reload --port 8000

# Frontend
cd web-app
npm install
npm run dev
```

Requires `toolkit/.env` with:
```
CHANGE_AGENT_API_KEY=...
BRAVE_SEARCH_API_KEY=...
LEGISCAN_API_KEY=...
```

---

## Limitations

This is a research prototype. Key limitations include: small interview sample (5 practitioners), no quantitative benchmarking of output quality, uneven module maturity across tools, and no testing at organizational scale. All outputs require professional review before distribution.

Full limitations documented in the [research landing page](https://ai-app-pa.vercel.app).
