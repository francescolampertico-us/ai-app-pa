# Eval Case 02 — Organization stakeholder with disclosures

## Input
```bash
python3 tools/stakeholder_briefing/execution/run.py \
  --name "Heritage Foundation" \
  --purpose "Understand their position on federal AI regulation" \
  --your-org "Progressive Tech Coalition" \
  --no-news \
  --out "./output"
```

## Acceptance Criteria
- Profile identifies Heritage Foundation as a conservative think tank with leadership and key programs.
- Policy positions reflect their known stance on regulation with evidence (not generic assertions).
- Disclosure section attempts LDA/IRS 990 lookup for Heritage Foundation; absence of results is reported, not fabricated.
- Talking points are forward-looking — focused on finding common ground or understanding their position on AI regulation, not just listing their past statements.
- Framing reflects Progressive Tech Coalition's perspective throughout.
- News section absent (skipped via `--no-news`).
