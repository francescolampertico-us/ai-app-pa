# Eval Case 01 - Microsoft (2025, LDA-only)

## Input
```bash
python3 tools/influence_disclosure_tracker/execution/run.py \
  --entities "Microsoft" \
  --from 2025-01-01 \
  --to 2025-12-31 \
  --sources "lda" \
  --out "./output" \
  --max-results 500
```

## Acceptance Criteria
- All LDA rows in `master_results.csv` have dates within 2025.
- Any `lda_*.csv` rows use `filing_year` = 2025.
- `report.md` shows the FARA section with an explicit "No FARA records matched" message.
