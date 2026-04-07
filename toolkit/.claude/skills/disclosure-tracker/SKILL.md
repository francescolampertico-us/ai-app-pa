---
name: disclosure-tracker
description: Search LDA lobbying and FARA foreign agent disclosure records for entities. Use when user asks to check lobbying disclosures, search FARA, find LDA filings, track influence, or investigate foreign agent registrations.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Influence Disclosure Tracker

## Goal
Collect LDA and FARA disclosure records for specified entities and produce normalized CSV tables plus a markdown summary report.

## Inputs
- **entities**: Comma-separated list of entities to search — REQUIRED
- **sources**: `lda`, `fara`, or `lda,fara` (optional, defaults to both)
- **search_field**: `client`, `registrant`, or `both` (optional, defaults to both)
- **filing_years**: Comma-separated years, e.g. `2024,2025` (optional)
- **filing_periods**: Comma-separated quarters: `Q1,Q2,Q3,Q4` (optional)
- **from_date**: Start date `YYYY-MM-DD` (optional)
- **to_date**: End date `YYYY-MM-DD` (optional)
- **fuzzy_threshold**: Match threshold 0-100 (optional, default 85)
- **out**: Output base folder (optional)
- **max_results**: Per-source cap (optional)

## Scripts
- `tools/influence_disclosure_tracker/execution/run.py` — Full pipeline: LDA API query + FARA bulk CSV search → normalize → CSV + report

## Process

### Step 1: Run the tracker
```bash
python3 tools/influence_disclosure_tracker/execution/run.py \
  --entities "ENTITY1,ENTITY2" \
  --sources "lda,fara" \
  --search-field both \
  --filing-years "2024,2025" \
  --out "output/disclosures"
```

Add optional parameters:
- `--from FROM_DATE --to TO_DATE` for date range filtering
- `--fuzzy-threshold 90` to tighten match precision
- `--max-results 50` to limit results
- `--dry-run` to preview configuration without executing

### Step 2: Review results
- Read `report.md` in the output folder for the executive summary
- Check `master_results.csv` for the merged hit list with match confidence
- Review match confidence scores — anything below 100% needs manual verification

### Step 3: Examine detail CSVs
LDA outputs:
- `lda_filings.csv` — filing records
- `lda_issues.csv` — lobbying issue areas
- `lda_lobbyists.csv` — individual lobbyists

FARA outputs:
- `fara_registrants.csv` — registered foreign agents
- `fara_foreign_principals.csv` — foreign principal details
- `fara_documents.csv` — filed documents with PDF links
- `fara_short_forms.csv` — supplemental statements

### Step 4: Human review reminder
Notify user to verify:
- Entity matches for fuzzy/contains hits (especially < 100% confidence)
- Date ranges fall inside intended period
- Filing/document URLs are accurate (spot-check)
- Sensitive claims before external distribution

## Output
**Deliverables:**
- `report.md` — executive summary with match confidence table
- `master_results.csv` — merged normalized results
- Source-specific CSVs (LDA and/or FARA)

## Edge Cases
- **No results found**: Entity may not have disclosures; try broader search or check spelling
- **FARA first run slow**: Downloads ~3 MB of bulk CSVs; cached for 24 hours after
- **LDA rate limits**: Large queries may take longer; be patient
- **Fuzzy false positives**: Lower threshold catches more but increases noise
