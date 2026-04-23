# AGENTS.md — Public Affairs AI Tools Repo

## Project overview
This repo packages public affairs AI tools as maintainable “tool packages”:
- tools/<tool_id> contains: tool.yaml, spec.md, skill.md, examples/, eval/, and optional execution/ code.
- workflows/ contains SOP-style playbooks linking tools together.
- tool-registry.yaml is the canonical index of tools.

## Must-read files before changes
- README.md
- IMPLEMENTATION_PLAN.md
- tool-registry.yaml
- workflows/media_clips_daily.md
- STYLE_GUIDE.md and RISK_POLICY.md

## Conventions
- Keep each tool self-contained under tools/<tool_id>.
- Don’t change output contracts casually; bump tool version in tool.yaml when behavior changes.
- Respect risk levels (green/yellow/red) and review checklists.
- Prefer small commits and keep docs consistent with code.
- For manual QA, use the central system in `toolkit/qa/` and the `manual-qa-orchestrator` skill; do not invent ad hoc test tracking in chat.

## Suggested commands
- Python help checks: `python3 tools/<tool_id>/execution/*.py --help`
- Dependency installs (tool-local): `python3 -m pip install -r tools/<tool_id>/requirements.txt`
