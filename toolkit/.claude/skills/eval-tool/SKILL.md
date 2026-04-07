---
name: eval-tool
description: Run evaluation cases for a toolkit tool and report pass/fail results. Use when user asks to evaluate a tool, run eval cases, test a tool, or check tool quality.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Tool Evaluation Runner

## Goal
Run a tool's eval cases against its spec.md contract and report which acceptance criteria pass or fail.

## Inputs
- **tool_id**: The tool to evaluate (e.g. `hearing_memo_generator`)
- **case**: Specific eval case to run (optional, defaults to all cases)

## Process

### Step 1: Read the tool's spec and eval cases
```bash
# Read the output contract
cat tools/TOOL_ID/spec.md
```
```bash
# List available eval cases
ls tools/TOOL_ID/eval/
```

### Step 2: Read each eval case
Each eval case in `tools/TOOL_ID/eval/` should contain:
- Input specification (what to feed the tool)
- Acceptance criteria (bulleted checks)

Read each case file to understand what to test.

### Step 3: Run the tool for each case
```bash
python3 tools/TOOL_ID/execution/run.py [ARGS_FROM_EVAL_CASE]
```

### Step 4: Check acceptance criteria
For each eval case, verify:
- Required headings/sections present in output
- No fabricated names, titles, dates, or facts
- Tone and style match STYLE_GUIDE.md
- Risk-level-appropriate caveats included
- Format matches the output contract in spec.md
- Verification flags (if tool has verification step)

### Step 5: Report results
Produce a summary:

```
## Eval Results: TOOL_NAME

### Case 1: case_name
- [PASS] Required headings present
- [PASS] No fabricated content
- [FAIL] Overview too granular — mentions individual speakers
- ...

### Case 2: case_name
- [PASS] All criteria met

## Summary
- Total cases: X
- Passed: Y
- Failed: Z
- Criteria checked: N
```

## Output
**Deliverable:** Eval report printed to console or written to `tools/TOOL_ID/eval/results.md`

## Edge Cases
- **No eval cases exist**: Create placeholder cases from the spec.md, then run them
- **Tool execution fails**: Report the error as a FAIL with the stack trace
- **Missing examples**: Warn that example input/output pairs should be added
