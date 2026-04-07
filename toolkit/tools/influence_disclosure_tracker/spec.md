# Influence Disclosure Tracker

## Purpose
Collect lobbying (LDA), foreign principal (FARA), and nonprofit tax (IRS 990) disclosure records for specified entities over a date range, and produce normalized CSV tables plus a markdown summary report.

## When to use
- Rapid scans of LDA, FARA, and/or IRS 990 disclosures tied to a company, organization, or media outlet.
- Internal research to support public affairs monitoring and briefing.

## Inputs (Directive)
### Required
- `entities` - comma-separated list of entities to search.
- `from` - start date (`YYYY-MM-DD`).
- `to` - end date (`YYYY-MM-DD`).

### Optional
- `sources` - `lda`, `fara`, `irs990` (comma-separated).
- `mode` - `basic` (fast API lookup) or `deep` (XML parse + LLM enrichment for subjective PA relevance tags).
- `out` - output base folder.
- `max_results` - per-source cap on results.
- `cache_dir` - location for cached API responses.

## Output Contract
The tool writes a run folder under `<out>/<entity_or_multiple>/` containing:
- `master_results.csv` (merged, normalized hit list with match confidence)
- `lda_*.csv` tables (filings, issues, lobbyists)
- `fara_*.csv` tables (registrants, foreign principals, documents, short forms)
- `irs990_organizations.csv` and `irs990_filings.csv` (basic mode)
- `report.md` (summary with executive section and match confidence table)

### Deep mode additional outputs (mode=deep)
- `irs990_deep_lobbying.csv` — Schedule C lobbying expenditures
- `irs990_deep_officers.csv` — Part VII officers, titles, compensation
- `irs990_deep_grants.csv` — Schedule I domestic grants and recipients
- `irs990_deep_related.csv` — Schedule R related organizations
- `irs990_deep_enrichments.csv` — LLM-derived PA relevance scores, issue tags, influence signals, risk flags

## Limitations / Failure Modes
- **Match confidence:** string matching includes fuzzy and partial matches; anything below 100% should be verified manually.
- **API rate limits:** LDA endpoints throttle requests; large queries may take time.
- **FARA bulk data:** FARA uses bulk CSV downloads cached for 24 hours; first run downloads ~3 MB.
- **IRS 990 API:** ProPublica's nonprofit API is free but rate-limited; throttled to 0.5s between requests.
- **IRS 990 XML availability:** Not all filings have XML available; deep mode falls back gracefully.
- **LLM enrichment (deep mode):** Requires `OPENAI_API_KEY`. PA relevance scores are subjective and must be reviewed.
- **Manual verification:** entries, dates, and filing URLs must be reviewed before external use.

## Human Review Checklist (Risk: Yellow)
- Confirm entity matches for fuzzy/contains hits.
- Check all reported dates fall inside the intended range.
- Spot-check filing/document URLs for accuracy.
- Review LLM-generated PA relevance scores and tags (deep mode) — these are interpretive, not factual.
- Validate any sensitive claims before distribution.
