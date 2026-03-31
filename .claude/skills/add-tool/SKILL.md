---
name: add-tool
description: Scaffold and register a new tool in the toolkit. Use when user asks to create a new tool, add a tool, scaffold a tool package, or start building the next tool.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Add New Tool to Toolkit

## Goal
Scaffold a complete tool package from the template, fill in metadata and specs, create the execution skeleton, and register it in tool-registry.yaml.

## Inputs
- **tool_id**: Snake_case identifier (e.g. `bill_summary_generator`)
- **tool_name**: Human-readable name (e.g. "Bill/Regulation Summary Generator")
- **description**: One-line description of what the tool does
- **digiacomo_workflow**: Which DiGiacomo workflow number(s) it maps to
- **risk_level**: `green`, `yellow`, or `red`
- **required_inputs**: List of required input fields
- **optional_inputs**: List of optional input fields
- **output_format**: Expected output format (e.g. `markdown + docx`)

## Process

### Step 1: Copy template
```bash
cp -r templates/tool/ tools/TOOL_ID/
```

### Step 2: Fill tool.yaml
Read `templates/tool/tool.yaml` for the structure, then edit `tools/TOOL_ID/tool.yaml` with:
- id, name, version (start at 0.1.0), risk_level
- description
- inputs (required + optional)
- outputs (format + artifacts)

### Step 3: Fill spec.md
Edit `tools/TOOL_ID/spec.md` with:
- Purpose
- When to use
- Inputs (required + optional with descriptions)
- Output contract (exact structure and quality requirements)
- Failure modes
- Human review checklist (if yellow/red risk)
- Known limitations

### Step 4: Fill skill.md
Edit `tools/TOOL_ID/skill.md` with:
- Instruction core for the tool
- Exact output format rules and heading family
- Non-negotiables (no fabrication, verification steps)

### Step 5: Create execution skeleton
```bash
mkdir -p tools/TOOL_ID/execution
```
Create `tools/TOOL_ID/execution/run.py` with:
- argparse CLI matching the inputs in tool.yaml
- Stub functions for each pipeline stage
- `if __name__ == "__main__"` entry point

### Step 6: Create example and eval directories
```bash
mkdir -p tools/TOOL_ID/examples tools/TOOL_ID/eval
```

### Step 7: Register in tool-registry.yaml
Append the new tool entry to `tool-registry.yaml` following the existing format.

### Step 8: Create Claude Code skill
Create `.claude/skills/TOOL_ID/SKILL.md` following the pattern of existing skills in `.claude/skills/`.

### Step 9: Verify
```bash
python3 tools/TOOL_ID/execution/run.py --help
```
Confirm the CLI runs without error and shows the expected arguments.

## Output
**Deliverable:** A complete tool package at `tools/TOOL_ID/` registered in `tool-registry.yaml` with a corresponding Claude Code skill.

## Checklist
- [ ] tool.yaml filled with correct metadata
- [ ] spec.md has purpose, inputs, output contract, failure modes, review checklist
- [ ] skill.md has instruction core and output format rules
- [ ] execution/run.py has CLI and stub functions
- [ ] Registered in tool-registry.yaml
- [ ] Claude Code skill created in .claude/skills/
