# Strategitect — AI-Powered Public Affairs Toolkit

A capstone project building AI-powered tools for public affairs professionals. Grounded in practitioner interviews and backed by a 41-source literature review.

**Author:** Francesco Lampertico — M.A. Political Communication, American University (May 2026)

**Live app:** [ai-app-pa.vercel.app](https://ai-app-pa.vercel.app)

---

## Overview

The toolkit integrates generative AI into core PA workflows. Every tool follows the **DOE pattern** (Directive → Orchestration → Execution): the user specifies intent, the system gathers and processes data via APIs and LLM calls, and the tool produces a professional-grade output file.

---

## Tool Catalog

| # | Tool | Status |
|---|------|--------|
| 1 | Congressional Hearing Memo Generator | ✅ Complete |
| 2 | Media Clips | ✅ Complete |
| 3 | Media Clip Cleaner | ✅ Complete |
| 4 | Influence Tracker | ✅ Complete |
| 5 | Legislative Tracker | ✅ Complete |
| 6 | Messaging Matrix | ✅ Complete |
| 7 | Stakeholder Briefing | ✅ Complete |
| 8 | Media List Builder | ✅ Complete |
| 9 | Stakeholder Map | ✅ Complete |
| 10 | Background Memo | ✅ Complete |

---

## Tool Pipelines

Tools are designed to chain together:

- **Media Clips → Media Clip Cleaner** — scrape coverage, clean article text for report
- **Influence Tracker → Stakeholder Map → Stakeholder Briefing** — disclosure data builds maps, maps feed briefings
- **Legislative Tracker → Hearing Memo Generator** — bill context feeds hearing analysis
- **Background Memo → Messaging Matrix** — research feeds message development

---

## Architecture

### Frontend — Vite + React
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

## Repository Structure

```
capstone_project/
├── toolkit/            # Python execution layer — 10 tool packages
├── fastapi-backend/    # REST API wrapping the toolkit (FastAPI + uvicorn)
└── web-app/            # Vite + React frontend — primary interface
```

---

## Literature Review

Covers AI adoption in public affairs, GenAI performance evidence, task allocation frameworks, and tool-building approaches. Available in `literature_review/`.
