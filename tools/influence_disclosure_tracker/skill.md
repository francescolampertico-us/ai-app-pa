# Skill - Influence Disclosure Tracker (DOE-aligned)

Use the Directive -> Orchestration -> Execution pattern to run this tool reliably.

## Directive (what you must decide before running)

### Required
- **Entities**: comma-separated list of entities (e.g., `Microsoft, OpenAI`).
- **From / To dates**: `YYYY-MM-DD` to `YYYY-MM-DD`.

### Optional (common)
- **Sources**: `lda`, `fara`, or both (`--sources "lda,fara"`).
- **Output base**: `--out /path/to/output`.
- **Max results**: `--max-results 500`.
- **Cache directory**: `--cache-dir .cache/influence_disclosure_tracker`.

### Prereqs
- If using LDA with higher throughput, set `LDA_API_KEY`.
- FARA uses bulk CSV downloads (cached 24 hours); no setup needed.

## Orchestration (how the tool gathers and prepares information)
1) Parse entities and date range.
2) Query LDA API and/or download FARA bulk CSVs (with caching).
3) Apply exact, contains, and fuzzy string matching to normalize results.
4) Write normalized CSV tables plus a markdown summary report.

## Execution (how to run)

### Example run
From the repository root:

```bash
python3 tools/influence_disclosure_tracker/execution/run.py \
  --entities "Microsoft" \
  --from 2025-01-01 \
  --to 2025-12-31 \
  --sources "lda,fara" \
  --out "./output" \
  --max-results 500
```

## Output contract (format expectations)
- `master_results.csv` with match confidence and normalized fields.
- `lda_*.csv` tables for LDA filings, issues, and lobbyists.
- `fara_*.csv` tables for registrants, foreign principals, documents, and short forms.
- `report.md` with executive summary and match confidence notes.
