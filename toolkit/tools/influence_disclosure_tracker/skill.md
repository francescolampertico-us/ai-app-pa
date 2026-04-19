---
name: influence-disclosure-tracker
description: Search and cross-reference lobbying (LDA), foreign agent (FARA), and nonprofit (IRS 990) disclosure records for any entity. Use when the user wants to track influence activity, check if an organization has filed lobbying disclosures, find foreign agent registrations, look up nonprofit financials, or build a disclosure summary report.
---

# Influence Disclosure Tracker

## Goal
Cross-reference an entity across three federal disclosure databases — LDA (lobbying), FARA (foreign agents), and IRS Form 990 (nonprofits) — and produce normalized CSV tables and a markdown summary report.

## Inputs
- `entities` — comma-separated list of organizations or individuals to search (required)
- `filing_years` — comma-separated years, e.g. `2022,2023,2024` (omit for all years)
- `quarters` — subset of Q1–Q4 (default: all four)
- `sources` — any combination of `lda`, `fara`, `irs990` (default: all three)
- `search_field` — `client` (entity is lobbying client), `registrant` (entity is a lobbying firm), or `both` (default: `both`)
- `mode` — `basic` (default) or `deep` (XML parse + LLM enrichment for IRS 990)
- `from` / `to` — date range override in `YYYY-MM-DD` (optional; derived from `filing_years` if omitted)
- `max_results` — cap per source per entity (default: 500)

## Prereqs
- Set `LDA_API_KEY` for higher LDA rate limits (optional; unauthenticated requests are throttled).
- FARA uses bulk CSV downloads from `efile.fara.gov`, cached locally for 24 hours — no key needed.
- IRS 990 uses the ProPublica Nonprofit Explorer API — no key needed.
- `rapidfuzz`, `requests`, `pandas`, `python-dateutil` must be installed.

## Process
1. For each entity, query each selected source in parallel:
   - **LDA**: call `lda.senate.gov/api/v1/filings/` filtering by `filing_year`; apply fuzzy name matching against client and registrant fields; auto-expand to `both` fields if the initial scoped search returns zero matches.
   - **FARA**: download bulk CSVs; filter registrants and foreign principals whose active period overlaps the requested year range; apply fuzzy matching against both registrant and foreign principal name columns.
   - **IRS 990**: query ProPublica by EIN/name; return filing metadata with PDF links.
2. Apply three-tier matching (exact → contains → fuzzy) at a configurable threshold (default 85).
3. Write normalized CSV tables to the output directory.
4. Generate `report.md` with an Executive Summary source-status table, per-source sections gated to selected sources only, and a matching confidence appendix.

## Output
- `master_results.csv` — unified match-level results with source, match type, and confidence
- `lda_filings.csv`, `lda_issues.csv`, `lda_lobbyists.csv` — LDA detail tables
- `fara_registrants.csv`, `fara_foreign_principals.csv`, `fara_documents.csv` — FARA detail tables
- `irs990_organizations.csv`, `irs990_filings.csv` — IRS 990 filings with PDF links
- `report.md` — narrative summary with Executive Summary, per-source sections, and match confidence appendix

## Rules
- Never fabricate entity names, filing dates, dollar amounts, or registration numbers.
- Always declare match confidence; flag fuzzy or contains matches for human review before external use.
- If a source is not selected, it must not appear anywhere in the report.
- IRS 990 XML data has a 1–3 year filing lag; absence of current-year data is expected.
- FARA active-period filtering applies: only show registrants and foreign principals whose registration overlaps the requested date range.
