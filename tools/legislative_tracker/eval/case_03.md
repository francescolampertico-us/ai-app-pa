# Eval Case 03: AI summary generation

## Input
```bash
python3 run.py --bill-id <VALID_BILL_ID> --summarize --out /tmp/test_lt
```

## Acceptance Criteria
- [ ] Command exits with code 0
- [ ] `bill_summary.md` exists in output directory
- [ ] Summary contains all required sections:
  - [ ] Plain-Language Summary
  - [ ] Key Provisions
  - [ ] Potential Impact
  - [ ] Talking Points FOR
  - [ ] Talking Points AGAINST
  - [ ] Status & Next Steps
  - [ ] Assumptions & Unknowns
- [ ] Talking points present BOTH sides (balance check)
- [ ] No fabricated provisions or sponsor names
- [ ] Human Review Checklist is included
