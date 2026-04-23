# Public Affairs AI Toolkit

Python execution layer for the Strategitect capstone project. Contains all 10 tool packages, the QA system, scaffolding templates, and the canonical tool registry.

## Structure

```
toolkit/
├── tools/              # One package per tool (contract + spec + execution + examples + eval)
├── qa/                 # QA infrastructure: test cases, bug tracker, regression suite, run logs
├── templates/          # Scaffolding for adding new tools (tool.yaml, spec.md, skill.md)
├── tool-registry.yaml  # Canonical index of all tools (app-readable)
└── .claude/skills/     # Claude Code-invocable skills (add-tool, handoff, etc.)
```

## Tool Catalog

| ID | Tool | Version | Risk |
|----|------|---------|------|
| `media_clips` | Media Clips | 0.1.0 | yellow |
| `media_clip_cleaner` | Media Clip Cleaner | 0.3.0 | green |
| `influence_disclosure_tracker` | Influence Tracker | 0.2.0 | yellow |
| `hearing_memo_generator` | Congressional Hearing Memo | 1.0.0 | yellow |
| `legislative_tracker` | Legislative Tracker | 0.1.0 | yellow |
| `messaging_matrix` | Messaging Matrix | 0.1.0 | yellow |
| `stakeholder_briefing` | Stakeholder Briefing | 0.1.0 | yellow |
| `media_list_builder` | Media List Builder | 0.1.0 | yellow |
| `stakeholder_map` | Stakeholder Map | 0.1.0 | yellow |
| `background_memo_generator` | Background Memo | 0.1.0 | yellow |

## Adding a New Tool

1. Copy `templates/tool/` → `tools/<tool_id>/`
2. Fill in `tool.yaml`, `spec.md`, `skill.md`
3. Write execution code in `execution/run.py`
4. Add handler in `fastapi-backend/api/routers/tools.py`
5. Add page in `web-app/src/pages/`
6. Register in `tool-registry.yaml`

## Running a Tool Locally

```bash
python3 tools/<tool_id>/execution/run.py --help
```

Requires `toolkit/.env` with:
```
CHANGE_AGENT_API_KEY=...
BRAVE_SEARCH_API_KEY=...
LEGISCAN_API_KEY=...
```
