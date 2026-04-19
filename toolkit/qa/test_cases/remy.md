# Remy — Canonical Manual Cases

Use the page at `/remy`.

## REMY-SMK-01

- Tool: Remy
- Goal: Validate a normal routing request that should produce a tool-aware response.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Model:
  `gpt-4.1-mini`
- Message:
  `Run a background memo on Jagello 2000 with sections: Overview of Activities, Key Leadership, U.S. Presence.`

### What to verify

- Remy returns a coherent assistant response.
- If a tool event appears, it links to the correct tool page.
- Any artifact links render correctly when present.

### Pass / fail rules

- Pass: the assistant responds coherently and any tool-event UI is usable.
- Fail: the message flow breaks, tool events render incorrectly, or the tool link is wrong.

### Regression candidate

yes

## REMY-EDGE-01

- Tool: Remy
- Goal: Check graceful handling of an ambiguous or upstream-constrained request.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Model:
  `ChangeAgent`
- Message:
  `Help me do something with the toolkit, but I have not decided which tool yet.`

### What to verify

- Remy asks for clarification or narrows the task instead of hallucinating a completed workflow.
- If rate-limited or otherwise blocked, the message stays readable and points the user back to direct tool use.

### Pass / fail rules

- Pass: ambiguous input leads to a usable clarification path or a clear fallback message.
- Fail: it invents tool results, crashes, or returns an unusable error.

### Regression candidate

yes
