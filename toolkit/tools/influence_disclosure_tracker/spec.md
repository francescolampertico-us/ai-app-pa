# Influence Disclosure Tracker

## Purpose
Cross-reference an entity across LDA (lobbying), FARA (foreign agents), and IRS 990 (nonprofits) to produce normalized CSV tables and a per-source markdown summary report. Unselected sources are fully suppressed from the report.

## When to use
- Rapid scans of LDA, FARA, and/or IRS 990 disclosures tied to a company, organization, or individual.
- Internal research to support public affairs monitoring, client intelligence, and briefing preparation.

## Inputs (Directive)

### Required
- `entities` — comma-separated list of entities to search.

### Optional
- `filing_years` — comma-separated years, e.g. `2022,2023,2024` (preferred over `from`/`to` for year-level filtering).
- `from` / `to` — date range in `YYYY-MM-DD`; derived from `filing_years` if omitted.
- `sources` — any combination of `lda`, `fara`, `irs990` (default: all three).
- `search_field` — `client` (entity is a lobbying client), `registrant` (entity is a lobbying firm), or `both` (default).
- `mode` — `basic` (default) or `deep` (XML parse + LLM enrichment for IRS 990).
- `out` — output base folder.
- `max_results` — per-source cap (default: 500).
- `cache_dir` — location for cached API responses.

## Output Contract
The tool writes a run folder under `<out>/` containing:
- `master_results.csv` — unified match list with source, match type, and confidence score
- `lda_filings.csv`, `lda_issues.csv`, `lda_lobbyists.csv` — LDA detail tables
- `fara_registrants.csv`, `fara_foreign_principals.csv`, `fara_documents.csv` — FARA detail tables
- `irs990_organizations.csv`, `irs990_filings.csv` — IRS 990 filings with PDF links
- `report.md` — narrative summary with Executive Summary source-status table, per-source sections (gated to selected sources), and a matching confidence appendix

### Deep mode additional outputs (`mode=deep`)
- `irs990_deep_lobbying.csv` — Schedule C lobbying expenditures
- `irs990_deep_officers.csv` — Part VII officers, titles, compensation
- `irs990_deep_grants.csv` — Schedule I domestic grants and recipients
- `irs990_deep_related.csv` — Schedule R related organizations
- `irs990_deep_enrichments.csv` — LLM-derived PA relevance scores, issue tags, influence signals, risk flags

## Limitations / Failure Modes
- **Match confidence:** fuzzy and partial matches are flagged; anything below 100% must be verified manually.
- **LDA rate limits:** `lda.senate.gov` throttles unauthenticated requests; set `LDA_API_KEY` for higher limits.
- **FARA bulk data:** bulk CSVs are cached for 24 hours; first run downloads ~3 MB.
- **IRS 990 filing lag:** ProPublica data has a 1–3 year lag; absence of current-year filings is expected.
- **IRS 990 XML availability:** XML is not available for all filings; the tool surfaces PDF links instead.
- **LLM enrichment (deep mode):** Requires an LLM API key. PA relevance scores are interpretive and must be reviewed.
- **FARA active-period filtering:** Only registrants and foreign principals whose active period overlaps the searched date range are included.
- **Manual verification:** entity matches, dates, amounts, and filing URLs must be reviewed before external use.

## Human Review Checklist (Risk: Yellow)
- Confirm entity matches for fuzzy/contains hits before citing in external materials.
- Check that all reported dates fall inside the intended range.
- Spot-check filing and document URLs for accuracy.
- Review LLM-generated PA relevance scores and tags (deep mode) — these are interpretive, not factual.
- Validate any sensitive claims before distribution.
