# Test Case Template

## Case ID
`<TOOL>-SMK-01`

## Tool
`<tool name>`

## Goal
One-sentence description of what this case proves.

## Priority
`P0` | `P1` | `P2`

## Scenario Type
`smoke` | `edge` | `failure-mode` | `regression`

## Exact App Inputs
List every field exactly as the tester should enter it.

## Optional Setup / Preconditions
- App page
- Required API keys or environment assumptions
- Files to upload if relevant

## What To Verify
- Output structure
- User-visible behavior
- Downloaded artifacts
- Data quality checks

## Pass / Fail Rules
- `Pass:` clear acceptance criteria
- `Fail:` concrete reasons to log a bug

## Known Risks This Case Covers
- Risk 1
- Risk 2

## If It Fails, Log Bug As
Suggested bug title prefix.

## Regression Candidate
`yes` | `no`
