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

**Last session:** 2026-04-01 (uncommitted changes — commit before next session)

**Tools built (9):** unchanged — see previous entries.

**What was done this session:**

*Disclosure Tracker (`tools/influence_disclosure_tracker/execution/report.py`):*
- Removed explanatory sentences from Schedule C and Schedule I sections (user found them unnecessary)
- Added note when Filing History is empty: IRS 990s lag 1-3 years, advises trying earlier years

*Media List Builder:*
- `tools/media_list_builder/execution/generator.py` — strengthened system prompt: podcasts must be policy-focused (named examples: Eye on AI, Hard Fork, Big Technology Podcast); `outlet_website` added to JSON schema with `https://` prefix; `previous_story_url` must be full URL or empty string
- `tools/media_list_builder/execution/export.py` — split "Previous Coverage" into two columns: "Previous Story" + "Story URL"; added "Website" column
- `app/pages/7_Media_List_Builder.py` (was 8) — added `_fix_url()` normalizer (adds `https://`, strips blanks/placeholders); `outlet_website` and `previous_story_url` rendered as `st.column_config.LinkColumn`

*App shell — page renumbering:*
- Literature Review moved from `5_` to `99_` (appears after all tools in sidebar)
- Tools renumbered: Messaging Matrix=5, Stakeholder Briefing=6, Media List Builder=7, Stakeholder Map Builder=8
- `app/shared.py` — sidebar now has "Tools" and "Reference" headings; Literature Review under Reference
- `app/streamlit_app.py` — added Reference section with Literature Review card; fixed TOOL_PAGES for all 9 tools (was missing 3)

*Stakeholder Map Builder — network analysis upgrade (Varone et al. 2016):*
- `tools/stakeholder_map_builder/execution/analytics.py` — **new file**: computes degree centrality, betweenness centrality, greedy modularity communities, broker identification (actors bridging proponent+opponent sides), multi-venue detection, deterministic strategic summary
- `tools/stakeholder_map_builder/execution/graph.py` — broker nodes now get gold border (thickness ∝ betweenness, capped 6px); centrality shown in hover; legend annotation updated
- `tools/stakeholder_map_builder/execution/generator.py` — secondary dedup by normalized name (merges client_X + lobbyist_X same org); classification prompt now allows LLM to use known policy positions (reduces "Unknown" classifications); issue_areas trimmed to 2 (was 1)
- `app/pages/8_Stakeholder_Map_Builder.py` — calls `analytics.py` after `build_map()`; new "🔬 Network Analysis" tab (tab 2 of 6): metrics row, bridge actors table, centrality rankings (betweenness vs degree), structural communities, multi-venue actors, strategic summary; betweenness + degree + community columns added to Proponents/Opponents/All Actors tabs

**Uncommitted files (all need to be committed):**
- `app/pages/5_Messaging_Matrix.py` (renamed from 6)
- `app/pages/6_Stakeholder_Briefing.py` (renamed from 7)
- `app/pages/7_Media_List_Builder.py` (renamed from 8, modified)
- `app/pages/8_Stakeholder_Map_Builder.py` (renamed from 9, modified)
- `app/pages/99_Literature_Review.py` (renamed from 5)
- `app/shared.py` (modified)
- `app/streamlit_app.py` (modified)
- `tools/influence_disclosure_tracker/execution/report.py` (modified)
- `tools/media_list_builder/execution/export.py` (modified)
- `tools/media_list_builder/execution/generator.py` (modified)
- `tools/stakeholder_map_builder/execution/analytics.py` (new)
- `tools/stakeholder_map_builder/execution/generator.py` (modified)
- `tools/stakeholder_map_builder/execution/graph.py` (modified)

**Next priorities:**
1. Commit all uncommitted changes above
2. End-to-end test Stakeholder Map Builder with "AI safety regulation" — verify Network Analysis tab renders, broker actors appear with gold border, strategic summary is coherent
3. End-to-end test Media List Builder — verify podcast results are policy-specific, website + story URLs are clickable
4. Polish and test remaining tools before Apr 26 final submission
5. Optional: Crisis Response Brief (highest-value remaining tool)

**Known issues:**
- Stakeholder Map Builder: "Unknown" stance still common for lobbyist firms (by design — firms classified unknown, clients classified by known position)
- Media List Builder: LLM may still omit `outlet_website` for some contacts; `_fix_url()` in page 7 handles missing protocol
- IRS 990 Filing History empty when searching current year (2025/2026) — by design, IRS 990s lag 1-3 years
- Streamlit entry: `streamlit run app/streamlit_app.py` from `toolkit/` root
- `youtube-transcript-api` v1.x: `YouTubeTranscriptApi().fetch(video_id, languages=['en'])`
