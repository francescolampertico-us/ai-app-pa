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
<!-- Updated by /continue skill — keeps session context across conversations -->

**Last session:** 2026-03-30

**Tools built (5):**
1. `hearing_memo` (v1.0.0) — congressional hearing memos from transcripts. YouTube transcript support added.
2. `media_clips` (v1.0.0) — daily media monitoring from Google News
3. `influence_disclosure_tracker` (v0.2.0) — LDA + FARA + IRS 990 search. Deep mode extracts XML schedules (C, F, I, J, R) + LLM enrichment.
4. `messaging_matrix` (v0.1.0) — Message Map grid format (overarching message -> 3 key messages -> 3 supporting facts). 7 output variants including Media Talking Points and Speech Draft.
5. `legislative_tracker` — status TBD

**What was done last session (2026-03-30):**
- Expanded IRS 990 deep extraction: added `xml_parser.py` methods for org profile, financials, Schedule J compensation, Schedule F foreign activity
- Updated `irs990_client.py` Phase 2 to save to new tables: `irs990_deep_profile`, `irs990_deep_compensation`, expanded `irs990_deep_grants` and `irs990_deep_lobbying`
- Updated `io_utils.py` with new table schemas and dataset entries
- Updated `report.py` with sections for org profile, financial breakdown, lobbying, compensation, and grants
- Tested deep mode end-to-end with Heritage Foundation — all tables populated correctly
- Created `/handoff` skill (`.claude/skills/handoff/SKILL.md`) for session continuity
- Added Project State section to CLAUDE.md

**What was done in prior sessions (2026-03-22 to 2026-03-29):**
- Built Messaging Matrix v0.1.0: Message Map grid format, 7 variants (Hill Talking Points, Op-Ed, Social Media, Press Release, One-Pager, Media Talking Points, Speech Draft)
- Restructured Message House -> Message Map (overarching message -> 3 key messages -> 3 supporting facts)
- Wired `style_samples/message_matrix/instructions/` and `examples/` into generator pipeline
- Added YouTube transcript support to Hearing Memo (`app/pages/1_Hearing_Memo.py`)
- Built IRS 990 integration for Disclosure Tracker: ProPublica API search, basic + deep mode, XML parser, LLM enrichment
- Fixed master_results schema mismatch, filing_years init, LLM enricher JSON parsing
- Messaging Matrix plan exists at `.claude/plans/glittery-snuggling-hickey.md` for Enhancement 1 (richer inputs), Enhancement 2 (new variants — done), Enhancement 3 (personal writing style)

**Uncommitted files** (nothing committed yet — all work is staged/unstaged):
- Modified: `CLAUDE.md`, `io_utils.py`, `report.py`, `run.py`, `lda_client.py`, `tool.yaml`, `spec.md`, `skill.md`, `1_Hearing_Memo.py`, `3_Disclosure_Tracker.py`, `5_Messaging_Matrix.py`, `streamlit_app.py`, `app/requirements.txt`, `tool-registry.yaml`, and more
- New: `irs990_client.py`, `xml_parser.py`, `llm_enricher.py`, `tools/messaging_matrix/` (entire tool), `.claude/skills/handoff/`

**Next priorities:**
1. Messaging Matrix enhancements (plan at `.claude/plans/glittery-snuggling-hickey.md`): style samples folder, `context_reader.py` for PDF/DOCX upload, `style_analyzer.py` for personal writing style, Streamlit UI updates
2. Update Streamlit page `3_Disclosure_Tracker.py` with expanders for new deep tables (profile, grants, compensation)
3. Build remaining tools from capstone plan (legislative tracker, others TBD)
4. Commit all accumulated work

**Known issues:**
- IRS 990 Schedule I grants show "(Individual)" for recipients when orgs redact business names in filings — EINs still captured for cross-referencing
- Deep mode runs LLM enrichment on every fuzzy match (not just exact), which burns API credits on irrelevant orgs — consider filtering by confidence threshold
- Streamlit app entry point is `app/streamlit_app.py` (not `app/Home.py`), run with full path: `/Users/francescolampertico/Library/Python/3.9/bin/streamlit run app/streamlit_app.py`
- `youtube-transcript-api` v1.x uses instance methods: `YouTubeTranscriptApi().fetch(video_id, languages=['en'])`
