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
- `add-tool` — Scaffold and register a new tool package (automates the workflow above)
- `eval-tool` — Run a tool's eval cases and report pass/fail

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
