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
<!-- Updated by /handoff skill — keeps session context across conversations -->

**Last session:** 2026-03-31 (committed) + 2026-04-01 (new tools)

**Tools built (9):**
1. `hearing_memo` (v1.0.0) — congressional hearing memos from transcripts. YouTube transcript support.
2. `media_clips` (v1.0.0) — daily media monitoring from Google News
3. `influence_disclosure_tracker` (v0.2.0) — LDA + FARA + IRS 990. Deep mode extracts XML schedules + LLM enrichment.
4. `messaging_matrix` (v0.1.0) — Message Map grid, 7 output variants. Style guides + personalization.
5. `legislative_tracker` (v0.1.0) — LegiScan API search, track, summarize.
6. `stakeholder_briefing` (v0.1.0) — Pre-meeting one-pager with profile, positions, disclosures, news, talking points.
7. `media_list_builder` (v0.1.0) — Targeted media pitch list by issue, location, media type. Excel export.
8. `media_clip_cleaner` (v0.3.0) — embedded in Media Clips + standalone. LLM mode default.
9. `stakeholder_map_builder` (v0.1.0) — Discovers + classifies all actors on a policy issue. LDA + LegiScan + news. Interactive network graph (Plotly/networkx). Excel (actors + relationships) + DOCX.

**What was done last session (2026-04-01):**
- Committed Stakeholder Briefing + Media List Builder + app updates (4 commits, all clean)
- Built Stakeholder Map Builder tool: `tools/stakeholder_map_builder/`
  - Actor discovery: LDA topic search (registrants + clients), LegiScan bill sponsors, GNews context
  - Single gpt-4o classification call: stance (proponent/opponent/neutral/unknown), type, influence tier, evidence
  - Relationship extraction: lobbies-for (LDA registrant→client) + co-sponsors (LegiScan)
  - Interactive Plotly network graph: color=stance, size=influence, shape=type, dashed=lobbies-for, solid=co-sponsors
  - Excel: 2 sheets (Actors 10-col + Relationships 4-col), color-coded Stance column
  - DOCX: narrative organized by stance, relationships, coalitions, strategic notes
  - All exports smoke-tested with mock data
  - Installed: networkx + plotly
- App pages now: 1-Hearing Memo, 2-Media Clips, 3-Disclosure Tracker, 4-Legislative Tracker, 5-Literature Review, 6-Messaging Matrix, 7-Stakeholder Briefing, 8-Media List Builder, 9-Stakeholder Map Builder

**Uncommitted files:** None — all committed.

**Next priorities:**
1. End-to-end live test of Stakeholder Map Builder (run with "AI regulation" or "drug pricing")
2. Messaging Matrix fine-tuning (style injection polish)
3. Polish and test all tools end-to-end before Apr 26 final submission
4. Optional: additional tool if needed (Crisis Response Brief is highest-value remaining)

**Known issues:**
- IRS 990 Schedule I grants show "(Individual)" for recipients when orgs redact names — EINs still captured
- Stakeholder Briefing: FARA search on "Senate Commerce Committee" returns spurious fuzzy matches (Eco Corporation) — consider raising threshold for FARA in briefing context
- Media List Builder: `openpyxl` must be installed (`pip3 install openpyxl`)
- Stakeholder Map Builder: networkx + plotly must be installed (`pip3 install networkx plotly`)
- Streamlit entry: `streamlit run app/streamlit_app.py` from toolkit root
- `youtube-transcript-api` v1.x: `YouTubeTranscriptApi().fetch(video_id, languages=['en'])`
