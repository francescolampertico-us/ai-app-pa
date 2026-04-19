# Manual QA System

This folder is the lightweight manual QA system for the app.

Use it when testing real workflows in the web app. It is designed for three roles:

- You run the app manually and judge output quality.
- Codex coordinates the test process, gives exact inputs, logs outcomes, and prepares bug briefs.
- Claude handles code and prompt fixes using Codex-prepared bug briefs.

## Operating rules

1. Reuse canonical test cases before inventing new ones.
2. Log every executed case in the monthly run log.
3. Create a bug brief only for confirmed defects.
4. Add a regression check only after a fix or when a failure is important enough to guard permanently.
5. Keep the system lean. If a file stops helping, simplify it.

## Folder map

- [test_index.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_index.md) — master coverage board
- [test_cases/](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases) — canonical manual cases per tool
- [runs/2026-04.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/runs/2026-04.md) — append-only run log for the current month
- [bugs/bug_backlog.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/bugs/bug_backlog.md) — confirmed bug tracker
- [regressions/regression_suite.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/regressions/regression_suite.md) — must-rerun checks after fixes
- [templates/](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/templates) — reusable templates

## Standard workflow

1. Pick a tool from [test_index.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_index.md).
2. Ask Codex for the next recommended case from `toolkit/qa/test_cases/<tool>.md`.
3. Codex returns:
   - case ID and case name
   - exact field-by-field inputs to paste/select
   - expected output/artifact shape
   - short manual review checklist
4. Run the case in the app.
5. Report results back to Codex in this structure:

```md
Tool: <tool name>
Case ID: <case id>
Outcome: pass | fail | partial | blocked
Notes: <1-5 lines>
Evidence: <key output excerpt, screenshot note, or artifact note>
```

6. Codex updates:
   - [runs/YYYY-MM.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/runs/2026-04.md)
   - [bugs/bug_backlog.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/bugs/bug_backlog.md) if needed
   - [bugs/BUG-XXXX.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/bugs) for Claude-ready bug briefs
   - [regressions/regression_suite.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/regressions/regression_suite.md) if the bug merits a guardrail

## Claude shortcut

Once a bug brief exists, you can usually give Claude a very short instruction:

```md
Fix BUG-0001
```

Claude should then read:

- `toolkit/qa/bugs/BUG-0001.md`
- any linked canonical test case
- any linked regression entry

That keeps the workflow fast without losing the full bug context.

## How Codex should generate test inputs

Codex should build test instructions in this order:

1. Existing spec, example, and eval files under `toolkit/tools/<tool_id>/`
2. Canonical inputs in `toolkit/tool-registry.yaml`
3. The manual cases in `toolkit/qa/test_cases/<tool_id>.md`

Codex should default to canonical cases so repeated runs stay comparable.

## What counts as a bug

Log a bug when the tool:

- breaks the stated output contract
- produces clearly wrong or misleading output
- ignores critical user inputs
- fails the UI flow or artifact downloads
- regresses on a previously fixed behavior

Do not log bugs for:

- expected thin-data outcomes that are already documented
- subjective quality concerns without a concrete failure
- missing external data caused by third-party source limits unless the app handles it badly

## Maintenance

- Keep one run log file per month.
- Keep bug IDs sequential: `BUG-0001`, `BUG-0002`, and so on.
- Keep regression IDs sequential: `REG-0001`, `REG-0002`, and so on.
- Update [test_index.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_index.md) when a tool gains a new canonical case or a stable regression.
