# Eval Case 02 — China Daily (2024–2025, FARA-only)

## Input
```bash
python3 tools/influence_disclosure_tracker/execution/run.py \
  --entities "China Daily" \
  --filing-years "2024,2025" \
  --sources "fara" \
  --out "./output" \
  --max-results 500
```

## Acceptance Criteria
- `fara_documents.csv` contains no rows with `document_date` outside 2024–2025.
- Foreign principals whose active period does not overlap 2024–2025 are excluded.
- `report.md` Executive Summary shows FARA with record count; LDA and IRS 990 sections are fully absent (not selected).
- Foreign principals are not duplicated under the same registrant in the report.
