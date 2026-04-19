# Eval Case 01 — Microsoft (2022–2024, LDA-only, Client scope)

## Input
```bash
python3 tools/influence_disclosure_tracker/execution/run.py \
  --entities "Microsoft" \
  --filing-years "2022,2023,2024" \
  --sources "lda" \
  --search-field "client" \
  --out "./output" \
  --max-results 500
```

## Acceptance Criteria
- `master_results.csv` contains LDA rows for Microsoft with `filing_year` in 2022, 2023, 2024.
- `lda_filings.csv` shows multiple lobbying firms (registrants) with non-zero amounts.
- `report.md` Executive Summary shows LDA with filing count and total spend; FARA and IRS 990 sections are fully absent (not selected).
- Matching confidence appendix lists Microsoft Corporation at 100% confidence.
