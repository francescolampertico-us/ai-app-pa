# CLAUDE.md — Public Affairs AI Toolkit

## Project context
Capstone project building AI-powered tools for public affairs professionals. Every tool maps to a workflow from the DiGiacomo (2025) PA management framework.

**Deadline:** April 26, 2026 — ~20 days remaining.

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
- **`gpt-4.1-mini`** — default for almost everything: extraction passes, structured outputs, tool calls, variants, clip cleaner, hearing memo draft pass
- **`gpt-4.1`** — final high-stakes synthesis only: background memo, stakeholder briefing, messaging strategy (Message House), legislative tracker synthesis pass, hearing memo polish pass

The hearing memo uses a two-pass architecture: mini for extraction, 4.1 for final prose polish.

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
Media Clips, Media Clip Cleaner, Influence Disclosure Tracker, Hearing Memo Generator, Legislative Tracker, Messaging Matrix, Stakeholder Briefing, Media List Builder, Stakeholder Map Builder, Background Memo Generator

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
3. `STYLE_GUIDE.md` — house output standards
4. `RISK_POLICY.md` — risk levels and review requirements
5. The specific tool's `spec.md` and `skill.md` before modifying it

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
- `background-memo` — generate a background memo DOCX via the toolkit pipeline
- `handoff` — generate a session handoff prompt and update CLAUDE.md Project State

Per-tool skills (canonical spec for each tool, not workspace-invocable):
- `toolkit/tools/<tool_id>/skill.md` — one per tool, used by Claude as tool context

## Commit conventions
- Small, focused commits — `<verb> <what>`
- Tag milestones: `v0.1.0-prototype`, `v1.0.0-final`

## Project State
**Last updated:** 2026-04-06

**Status:** All 10 tools wired into Vite frontend + FastAPI backend. Streamlit retired.

**What was done (2026-04-06):**
- Migrated to Vite + FastAPI as sole interface; Streamlit retired
- Fixed `gpt-5-mini` → `gpt-4o-mini` → `gpt-4.1-mini` / `gpt-4.1` across all tools
- Model policy: 4.1-mini for extraction/variants, 4.1 for final synthesis only
- Hearing memo: two-pass architecture (mini draft → 4.1 polish)
- Legislative tracker: relevance-sorted results + max-results dropdown (Best match / Top 5 / 10 / 25 / All)
- Influence tracker: fixed YearDropdown double-toggle bug; DataTable download button always visible in header
- Media Clips: standalone Clip Cleaner section always visible; email draft section clearly separated
- Repo root moved from `toolkit/` to `capstone_project/` — web-app and fastapi-backend now tracked

**Known issues:**
- Stakeholder Map Builder: Network Analysis untested end-to-end
- IRS 990: empty for current year by design (1–3 year filing lag)
- Hearing Memo: degrades gracefully (local extraction) if OpenAI key unavailable

**Next priorities (20 days to Apr 26):**
1. End-to-end test all 10 tools with real inputs
2. Polish UI/UX — error messages, loading states, edge cases
3. Final submission prep
