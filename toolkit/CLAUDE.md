# CLAUDE.md — Public Affairs AI Toolkit

## Project context
Capstone project building AI-powered tools for public affairs professionals. Grounded in 5 expert interviews and a 28-source literature review on generative AI in PA practice.

## Repository structure
```
capstone_project/
├── toolkit/          # Python tool execution layer (10 tools + Remy)
├── fastapi-backend/  # FastAPI REST API wrapping the toolkit
└── web-app/          # Vite + React frontend (primary interface)
```

## Architecture: DOE pattern
Every tool follows Directive-Orchestration-Execution:
- **Directive:** User specifies intent (topic, queries, entities, date range)
- **Orchestration:** Tool gathers and processes data (APIs, filtering, LLM calls)
- **Execution:** Tool produces verified output (docx, CSV, markdown)

## LLM model policy
Uses ChangeAgent (OpenAI-compatible endpoint). Two-tier approach:
- **Fast model** — default for extraction passes, structured outputs, tool calls, variants, clip cleaner, hearing memo draft pass
- **Full model** — final high-stakes synthesis only: background memo, stakeholder briefing, messaging strategy, legislative tracker synthesis pass, hearing memo polish pass

The hearing memo uses a two-pass architecture: fast model for extraction, full model for final prose polish.

## Frontend: Vite + React
**Entry:** `cd web-app && npm run dev` (http://localhost:5173)

The Vite app is the **primary interface**. Streamlit is retired.

Pages:
- `src/pages/` — one component per tool
- `src/hooks/useFastApiJob.js` — shared job polling hook
- All tool calls go through FastAPI at `http://localhost:8000`

## Backend: FastAPI
**Entry:** `cd fastapi-backend && python3 -m uvicorn main:app --reload --port 8000`

- `api/routers/tools.py` — all tool handlers (`_handle_*` functions)
- `api/routers/jobs.py` — job creation and status polling
- `api/routers/remy.py` — Remy assistant endpoint
- Loads env from `toolkit/.env`

## Toolkit: Python tools
**Entry:** `python3 tools/<tool_id>/execution/run.py --help`

### Tools built (10)
Media Clips, Media Clip Cleaner, Influence Tracker, Hearing Memo, Legislative Tracker, Messaging Matrix, Stakeholder Briefing, Media List Builder, Stakeholder Map, Background Memo

### Adding a new tool
1. Copy `templates/tool/` to `tools/<new_tool_id>/`
2. Fill `tool.yaml`, `spec.md`, `skill.md`
3. Write execution code in `execution/run.py`
4. Add handler in `fastapi-backend/api/routers/tools.py`
5. Add page in `web-app/src/pages/`
6. Register in `tool-registry.yaml`

## Non-negotiables
- Never fabricate facts, names, titles, dates, or sources
- Always declare a risk level (green/yellow/red) in tool.yaml
- Keep each tool self-contained under `tools/<tool_id>/`
- Don't change output contracts without bumping version in tool.yaml

## File reading priority
1. This file (CLAUDE.md)
2. `tool-registry.yaml` — canonical tool index
3. The specific tool's `spec.md` and `skill.md` before modifying it
4. `toolkit/qa/test_cases/<tool>.md` — acceptance criteria for the tool

## QA Bug Shortcuts
- If the user says `Fix BUG-XXXX`, treat `toolkit/qa/bugs/BUG-XXXX.md` as the canonical fix brief.
- Before editing code for that request, also read any linked files in the brief, especially:
  - `toolkit/qa/test_cases/<tool>.md`
  - `toolkit/qa/regressions/regression_suite.md`
  - relevant tool `spec.md` / `skill.md`
- Scope the fix to the bug brief unless the user explicitly broadens it.
- After making the fix, report:
  - what changed
  - which files changed
  - which QA case(s) and regression(s) should be rerun
- The same rule applies to `Fix BUG-0001 and BUG-0002`: read each bug brief first, then implement the requested fixes.

## Claude Code Skills
Workspace skills (`.claude/skills/`, Claude Code-invocable):
- `add-tool` — scaffold a new tool package from template
- `clip-cleaner` — run the media clip cleaner pipeline
- `disclosure-tracker` — run the influence disclosure tracker
- `eval-tool` — run evaluation harness for a tool
- `handoff` — generate a session handoff prompt and update CLAUDE.md Project State
- `hearing-memo` — run the hearing memo pipeline
- `legislative-tracker` — run the legislative tracker
- `media-clips` — run the media clips pipeline
- `messaging-matrix` — run the messaging matrix pipeline

Per-tool skills (canonical spec for each tool, not workspace-invocable):
- `toolkit/tools/<tool_id>/skill.md` — one per tool, used by Claude as tool context

## Commit conventions
- Small, focused commits — `<verb> <what>`
- Tag milestones: `v0.1.0-prototype`, `v1.0.0-final`

## Project State
**Last updated:** 2026-04-23

**Status:** All 10 tools deployed. Live at ai-app-pa.vercel.app (Vercel frontend + Railway backend).

**Deployment:**
- Frontend: Vercel (auto-deploys from `main` on push)
- Backend: Railway (Dockerfile build, env vars set in Railway dashboard)
- Backend URL set via `VITE_API_URL` env var in Vercel

**Known issues:**
- IRS 990: empty for current year by design (1–3 year filing lag)
- GNews intermittent on cloud IPs — tools have graceful fallbacks
