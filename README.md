# Public Affairs AI Tools (Repo)

This repository is the source of truth for my public affairs AI toolkit: **tool definitions**, **reusable skills**, **workflows**, **style and risk governance**, and **evaluation fixtures**.

It is designed so tools are:
- consistent in output quality and format
- safer for high-stakes PA contexts (review gates, non-negotiables)
- portable across platforms (Antigravity today, app/runtime later)

## Repository Structure

- `tools/` — one folder per tool (contract + spec + skill + examples + eval)
- `skills/` — reusable instruction blocks shared across tools
- `workflows/` — multi-tool playbooks (how tools combine in real PA work)
- `templates/` — templates for creating new tools consistently
- `research/` — capstone notes, interview learnings, literature, etc.
- `STYLE_GUIDE.md` — house style for outputs
- `RISK_POLICY.md` — green/yellow/red risk levels and review requirements
- `tool-registry.yaml` — index of tools (app-readable later)

## How to Add a New Tool (standard workflow)

1. Copy the template:
   - `templates/tool/` → `tools/<tool_id>/`
2. Fill in:
   - `tool.yaml` (inputs/outputs + risk)
   - `spec.md` (when to use, failure modes, review checklist)
   - `skill.md` (instruction core + format rules)
3. Add:
   - `examples/` (2–3 good runs)
   - `eval/` (at least 5 cases with acceptance criteria)
4. Register tool in `tool-registry.yaml`
5. Commit with message: `Add <tool_id> tool package`

## Current Status

- Repo scaffold: ✅
- Governance docs: ✅ (initial drafts)
- First “gold standard” tool package: ⏳ next step

