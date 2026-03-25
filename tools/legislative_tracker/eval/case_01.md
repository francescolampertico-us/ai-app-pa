# Eval Case 01: Basic search returns results

## Input
```bash
python3 run.py --query "data privacy" --state US --year 2026 --out /tmp/test_lt
```

## Acceptance Criteria
- [ ] Command exits with code 0
- [ ] `search_results.json` exists in output directory
- [ ] `report.md` exists in output directory
- [ ] JSON contains a list of bill objects
- [ ] Each bill object has: bill_id, number, title, state, status
- [ ] No fabricated bill numbers (all should be real LegiScan IDs)
