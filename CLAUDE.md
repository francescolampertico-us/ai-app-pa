# CLAUDE.md — Public Affairs AI Toolkit

## Project context
This is a capstone project building AI-powered tools for public affairs professionals. Every tool maps to a workflow from the DiGiacomo (2025) PA management framework. The repository is the single source of truth for tool definitions, governance, and evaluation.

## Architecture: DOE pattern
Every tool follows Directive-Orchestration-Execution:
- **Directive:** User specifies intent (topic, queries, entities, date range)
- **Orchestration:** Tool gathers and processes data (APIs, filtering, LLM calls)
- **Execution:** Tool produces verified output (docx, CSV, markdown)

## Build and validation flow

### Running a tool
```bash
python3 tools/<tool_id>/execution/run.py --help
python3 -m pip install -r tools/<tool_id>/requirements.txt
```

### Adding a new tool
1. Copy `templates/tool/` to `tools/<new_tool_id>/`
2. Fill `tool.yaml` (metadata + input/output contract + risk level)
3. Fill `spec.md` (when to use, failure modes, review checklist)
4. Fill `skill.md` (instruction core + output format rules)
5. Write execution code in `execution/`
6. Add 2+ examples in `examples/`
7. Add 2+ eval cases in `eval/`
8. Register in `tool-registry.yaml`

### Validation checklist (run after every change)
- Tool runs without error: `python3 tools/<tool_id>/execution/run.py --help`
- Output matches the contract in `spec.md`
- `tool-registry.yaml` is up to date
- Risk level declared in `tool.yaml`

## Non-negotiables
- Never fabricate facts, names, titles, dates, or sources
- Always declare a risk level (green/yellow/red) in tool.yaml
- Always include a verification or review step in the pipeline
- Respect the STYLE_GUIDE.md for all output text
- Keep each tool self-contained under `tools/<tool_id>/`
- Don't change output contracts without bumping version in tool.yaml

## File reading priority
When working on this repo, always read these first:
1. This file (CLAUDE.md)
2. `tool-registry.yaml` — canonical tool index
3. `STYLE_GUIDE.md` — house output standards
4. `RISK_POLICY.md` — risk levels and review requirements
5. The specific tool's `spec.md` and `skill.md` before modifying it

## Streamlit app
The app lives in `app/` and wraps each tool as a page. Each page:
- Imports the tool's Python functions directly (no shell subprocess)
- Collects inputs via Streamlit widgets
- Shows results inline + offers file download
- Displays risk level badge

## Claude Code Skills

Skills are on-demand instruction bundles in `.claude/skills/`. Only the frontmatter (~60 tokens) loads into context by default — the full skill loads only when invoked. This keeps the context window clean while giving Claude access to all tools.

### Available skills
- `hearing-memo` — Generate congressional hearing memos from transcripts
- `media-clips` — Daily media monitoring reports from Google News
- `clip-cleaner` — Clean pasted article text for clips reports
- `disclosure-tracker` — Search LDA/FARA disclosure records
- `messaging-matrix` — Generate messaging matrices with multiple output variants
- `background-memo` — Generate a background memo on a client, organization, issue, or individual
- `add-tool` — Scaffold and register a new tool package (automates the workflow above)
- `eval-tool` — Run a tool's eval cases and report pass/fail
- `handoff` — End-of-session handoff: updates Project State below and generates a resume prompt

### Skill architecture (Saraev pattern)
Each skill = `SKILL.md` (orchestrator) + existing `tools/*/execution/` scripts (deterministic execution). The LLM handles decisions and error recovery; Python scripts handle computation. This prevents error compounding (90% accuracy per LLM step = 59% over 5 steps).

### Self-annealing
When a skill encounters an error: fix the script, test it, update the SKILL.md with what you learned. The system gets stronger over time.

## Subagents

Development subagents live in `.claude/agents/`. They run on Sonnet (cheaper, larger context) and return results to the parent agent.

### Available subagents
- `research` — Deep research with web search for API exploration, data source investigation
- `code-reviewer` — Zero-context code review; returns issues by severity with PASS/FAIL verdict
- `qa` — Generates tests, runs them, reports pass/fail

### Development workflow: write → review → QA → fix → ship
1. **Write** — Make changes in the parent agent
2. **Review** — Spawn `code-reviewer` on changed files (read-only, reports back)
3. **QA** — Spawn `qa` on changed files (generates + runs tests, reports back)
4. **Fix** — Parent agent reads reports and applies fixes
5. **Ship** — Only after review passes and tests pass

Spawn review and QA in parallel when reviewing independent files.

## Commit conventions
- Small, focused commits
- Message format: `<verb> <what>` (e.g., "Add stakeholder_briefing tool package")
- Tag milestones: `v0.1.0-prototype`, `v1.0.0-final`

## Project State
<!-- Updated by /handoff skill — keeps session context across conversations -->

**Last session:** 2026-04-03

**Tools built (10):** Media Clips, Media Clip Cleaner, Disclosure Tracker, Hearing Memo, Legislative Tracker, Messaging Matrix, Stakeholder Briefing, Media List Builder, Stakeholder Map Builder, Background Memo Generator

**App assistant:** Remy (`app/pages/0_Remy.py` + `app/remy_assistant.py`) — tool-aware in-app PA assistant. Routes work, collects missing inputs, executes toolkit tools via OpenAI function-calling loop. Not a tool; not in tool-registry.yaml.

**What was done this session:**

*Background Memo Generator — polished (2026-04-02):*
- `execution/research.py` — GNews → `googlenewsdecoder` → trafilatura pipeline; up to 5 articles × 3000 chars each
- `execution/generator.py` — rewrote system prompt for house style; added `research_context` and `disclosure_context` params; auto-appends lobbying section when LDA/FARA filings found
- `execution/export.py` — renamed "Relevant Links" → "Links"; removed unused imports
- `app/pages/9_Background_Memo.py` — disclosure auto-runs all years; file upload (PDF/DOCX/TXT/MD); web research step
- Bug fix: disclosure tracker path fixed with `Path.rglob("report.md")`

*Remy — new in-app assistant (2026-04-03):*
- `app/pages/0_Remy.py` — Streamlit chat UI; page `0_` prefix puts it first in sidebar
- `app/remy_assistant.py` — OpenAI function-calling loop; loads tool catalog from `tool-registry.yaml`; dispatches to tool CLI entry points; returns text + tool_events with artifact download links
- `app/shared.py` — sidebar updated to include Remy (page 0) and Background Memo (page 9)
- `app/streamlit_app.py` — home page updated: Remy featured at top, tool catalog grid updated

**Next priorities:**
1. End-to-end test Background Memo Generator with "Institut Macaya" — verify disclosure section appears with TSG Advocates DC, $90k
2. End-to-end test with "Jagello 2000" — verify web research produces specific content
3. Test Remy end-to-end: tool routing, input collection, execution
4. Polish and test remaining tools before Apr 26 final submission

**Known issues:**
- Background Memo: GNews may return few results for niche subjects — file upload is the fallback
- Background Memo: Disclosure section only added if LDA/FARA filings found
- Stakeholder Map Builder: Network Analysis still untested end-to-end
- IRS 990 Filing History empty for current year (by design — 1-3 year lag)
- Streamlit entry: `python3 -m streamlit run app/streamlit_app.py` from `toolkit/` root
