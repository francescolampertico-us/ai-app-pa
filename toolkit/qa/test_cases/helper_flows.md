# Helper Flows — Canonical Manual Cases

Use the helper UI inside `/media-clips` and `/media-list`, plus direct backend calls when needed.

## HELP-SMK-01

- Tool: Helper Flows
- Goal: Validate the two user-facing helper endpoints with normal success cases.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Media Clips Mail helper:
  run a clips report first, then use:
  - `To`: `recipient@example.com`
  - `From`: leave blank
- Media List pitch helper:
  run a media list first, open one contact, then click `Generate Pitch`

### What to verify

- Mail helper returns a success state and attempts to open a Mail draft.
- Pitch helper returns a subject and body instead of an empty modal.

### Pass / fail rules

- Pass: both helpers complete with visible success output.
- Fail: either helper silently fails, returns empty content, or misroutes the action.

### Regression candidate

yes

## HELP-EDGE-01

- Tool: Helper Flows
- Goal: Check validation failures on missing required inputs.
- Priority: P1
- Scenario type: edge

### Exact checks

- Mail helper with missing `job_id` or missing `To`
- Pitch helper with missing `contact` or missing `issue`

### What to verify

- The backend returns explicit validation errors.
- The UI helper surfaces do not pretend the action succeeded.

### Pass / fail rules

- Pass: validation failures are clear and non-destructive.
- Fail: helpers fail silently or show a false success state.

### Regression candidate

yes
