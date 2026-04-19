# Eval Case 01 — Legislator (news + disclosures skipped)

## Input
```bash
python3 tools/stakeholder_briefing/execution/run.py \
  --name "Sen. Maria Cantwell" \
  --purpose "Discuss support for the AI Safety Act and potential co-sponsorship" \
  --organization "Senate Commerce Committee" \
  --your-org "TechForward Alliance" \
  --no-disclosures \
  --no-news \
  --out "./output"
```

## Acceptance Criteria
- Profile section includes her role on the Senate Commerce Committee.
- Policy positions mention AI governance or technology regulation with specific evidence.
- Talking points are framed from TechForward Alliance's perspective and forward-looking — centered on the co-sponsorship objective, not just recapping past statements.
- Key questions section present with at least 2 questions.
- No disclosure or news sections appear (both skipped).
- No fabricated quotes or specific statistics presented as fact.
