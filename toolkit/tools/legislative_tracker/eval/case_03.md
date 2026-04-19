# Eval Case 03: Verified source summary generation

## Input
```bash
python3 run.py --bill-id <VALID_BILL_ID> --summarize --out /tmp/test_lt
```

## Acceptance Criteria
- [ ] Command exits with code 0
- [ ] `bill_summary.md` exists in output directory
- [ ] Verified summary contains all required sections:
  - [ ] Bill Overview
  - [ ] Plain-Language Summary
  - [ ] Key Provisions
  - [ ] Definitions, Thresholds, and Deadlines
  - [ ] Exemptions and Exceptions
  - [ ] Enforcement, Reporting, and Certification
  - [ ] Legislative Status
- [ ] `summary_status` is `verified`
- [ ] No unsupported claims appear in `unsupported_claims`
- [ ] No inferred policy impact or analyst argument appears in the verified summary
- [ ] Every displayed numeric/date/threshold detail is traceable to evidence
