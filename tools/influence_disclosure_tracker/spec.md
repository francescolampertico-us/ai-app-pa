# Influence Disclosure Tracker

## Purpose
Collect lobbying and foreign principal disclosure records for specified entities over a date range, and produce normalized CSV tables plus a markdown summary report.

## When to use
- Rapid scans of LDA and/or FARA disclosures tied to a company, organization, or media outlet.
- Internal research to support public affairs monitoring and briefing.

## Inputs (Directive)
### Required
- `entities` - comma-separated list of entities to search.
- `from` - start date (`YYYY-MM-DD`).
- `to` - end date (`YYYY-MM-DD`).

### Optional
- `sources` - `lda`, `fara`, or both (comma-separated).
- `out` - output base folder.
- `max_results` - per-source cap on results.
- `cache_dir` - location for cached API responses.

## Output Contract
The tool writes a run folder under `<out>/<entity_or_multiple>/` containing:
- `master_results.csv` (merged, normalized hit list with match confidence)
- `lda_*.csv` tables (filings, issues, lobbyists)
- `fara_*.csv` tables (registrants, foreign principals, documents, short forms)
- `report.md` (summary with executive section and match confidence table)

## Limitations / Failure Modes
- **Match confidence:** string matching includes fuzzy and partial matches; anything below 100% should be verified manually.
- **API rate limits:** LDA and FARA endpoints throttle requests; large queries may take time.
- **FARA index dependency:** FARA searches require a one-time local index build (`--build-fara-index`).
- **Manual verification:** entries, dates, and filing URLs must be reviewed before external use.

## Human Review Checklist (Risk: Yellow)
- Confirm entity matches for fuzzy/contains hits.
- Check all reported dates fall inside the intended range.
- Spot-check filing/document URLs for accuracy.
- Validate any sensitive claims before distribution.
