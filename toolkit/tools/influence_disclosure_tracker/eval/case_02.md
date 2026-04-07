# Eval Case 02 - China Daily (2024-2025, FARA-only)

## Input
```bash
python3 tools/influence_disclosure_tracker/execution/run.py \
  --entities "China Daily" \
  --from 2024-01-01 \
  --to 2025-12-31 \
  --sources "fara" \
  --out "./output" \
  --max-results 500
```

## Acceptance Criteria
- No `fara_documents.csv` rows have `document_date` after 2025-12-31.
- Foreign principals are deduped in `report.md` and do not repeat the same name under a registrant.
- `report.md` shows the LDA section with an explicit "No LDA filings found" message.
