# Eval Case 02 — Paywall / extraction failure scenario

## Input
topic: India
queries:
  - site:ft.com India
period: 7d

## Acceptance criteria
- Report still builds even if full text cannot be extracted.
- Clips with extraction failure contain [PASTE FULL TEXT HERE].
- Human review checklist is followed before distribution (manual fill of paywalled text).
