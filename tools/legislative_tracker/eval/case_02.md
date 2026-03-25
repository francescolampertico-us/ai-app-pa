# Eval Case 02: Bill detail retrieval

## Input
```bash
python3 run.py --bill-id <VALID_BILL_ID> --out /tmp/test_lt
```

## Acceptance Criteria
- [ ] Command exits with code 0
- [ ] Bill detail includes: number, title, state, status, sponsors, history
- [ ] Sponsors include name and party
- [ ] History entries include date and action
- [ ] No fabricated data
