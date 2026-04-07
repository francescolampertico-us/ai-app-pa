# AI-Powered Public Affairs Toolkit

A capstone project building AI-powered tools for public affairs professionals. Grounded in the DiGiacomo (2025) framework for PA management, validated through practitioner interviews, and backed by a 41-source literature review.

**Author:** Francesco Lampertico — M.A. Political Communication, American University (May 2026)  
**Deadline:** April 26, 2026

---

## Overview

The toolkit integrates generative AI into 8 core PA workflows identified by DiGiacomo (2025). Every tool follows the **DOE pattern** (Directive → Orchestration → Execution): the user specifies intent, the system gathers and processes data via APIs and LLM calls, and the tool produces a verified, professional-grade output file.

---

## Repository Structure

```
capstone_project/
├── toolkit/            # Python execution layer — 10 tool packages
├── fastapi-backend/    # REST API wrapping the toolkit (FastAPI + uvicorn)
└── web-app/            # Vite + React frontend — primary interface
```

---

## Tool Catalog

| # | Tool | DiGiacomo Workflow | Status |
|---|------|--------------------|--------|
| 1 | Congressional Hearing Memo Generator | #3 Briefing Creation | ✅ Complete |
| 2 | Media Clips | #1 Legislative Monitoring | ✅ Complete |
| 3 | Media Clip Cleaner | #1 Legislative Monitoring | ✅ Complete |
| 4 | Influence Disclosure Tracker | #2 Stakeholder Analysis | ✅ Complete |
| 5 | Legislative Tracker | #1 Legislative Monitoring | ✅ Complete |
| 6 | Messaging Matrix | #4 Advocacy Campaign, #5 Digital PA | ✅ Complete |
| 7 | Stakeholder Briefing | #3 Briefing Creation | ✅ Complete |
| 8 | Media List Builder | #1 Legislative Monitoring | ✅ Complete |
| 9 | Stakeholder Map Builder | #2 Stakeholder Analysis, #4 Advocacy Campaign | ✅ Complete |
| 10 | Background Memo Generator | #3 Briefing Creation | ✅ Complete |

---

## DiGiacomo Framework Coverage

| # | PA Workflow | Tools |
|---|-------------|-------|
| 1 | Legislative & Regulatory Monitoring | Media Clips, Legislative Tracker, Media List Builder |
| 2 | Stakeholder Mapping & Analysis | Influence Disclosure Tracker, Stakeholder Map Builder |
| 3 | Position Paper & Briefing Creation | Hearing Memo Generator, Stakeholder Briefing, Background Memo Generator |
| 4 | Advocacy Campaign Planning | Messaging Matrix, Stakeholder Map Builder |
| 5 | Digital Public Affairs | Messaging Matrix, Media Clip Cleaner |
| 6 | Crisis Communication | — |
| 7 | Institutional Relationship Management | — |
| 8 | Performance Measurement | — |

---

## Tool Pipelines

Tools are designed to chain together:

- **Media Clips → Media Clip Cleaner** — scrape coverage, clean article text for report
- **Influence Disclosure Tracker → Stakeholder Map Builder → Stakeholder Briefing** — disclosure data builds maps, maps feed briefings
- **Legislative Tracker → Hearing Memo Generator** — bill context feeds hearing analysis
- **Background Memo → Messaging Matrix** — research feeds message development

---

## Architecture

### Frontend — Vite + React
The toolkit was initially prototyped in Streamlit. As complexity grew, it was rebuilt in Vite + React for full async support, professional UI, and proper job state management.

**Entry:** `cd web-app && npm run dev` → http://localhost:5173

Each tool has a self-contained page component. All tool calls go through a shared custom hook (`useFastApiJob`) that POSTs inputs to the FastAPI backend, receives a job ID, and polls for completion every 2 seconds. Results and downloadable artifacts are rendered inline when the job completes.

### Backend — FastAPI
**Entry:** `cd fastapi-backend && python3 -m uvicorn main:app --reload --port 8000`

- `api/routers/tools.py` — one `_handle_*` function per tool
- `api/routers/jobs.py` — job creation, status polling, artifact serving
- `api/routers/remy.py` — Remy AI assistant endpoint
- Credentials loaded from `toolkit/.env`

### Toolkit — Python
**Entry:** `python3 toolkit/tools/<tool_id>/execution/run.py --help`

Each tool package: `tool.yaml` (contract + version), `spec.md` (tool card), `execution/` (Python), `examples/`, `eval/`.

### LLM Model Policy
- **`gpt-4.1-mini`** — extraction passes, structured outputs, tool calls, variants
- **`gpt-4.1`** — final synthesis only: memo generation, briefings, strategy writeups, hearing memo polish pass

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
OPENAI_API_KEY=...
LEGISCAN_API_KEY=...
```

---

## Literature Review

Covers AI adoption in public affairs, GenAI performance evidence, task allocation frameworks (Mollick 2024), and tool-building approaches (DOE framework). Available in `literature_review/`.
