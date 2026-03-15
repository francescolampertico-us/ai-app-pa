# Example 01 - Expected Output Characteristics

- Output folder created under `./output/Multiple_Entities/`.
- `report.md` includes an executive summary per entity.
- `report.md` includes an LDA filings summary table or an explicit "no filings found" message.
- `report.md` includes a FARA highlights summary or an explicit "no records matched" message.
- `report.md` includes a matching confidence table.
- CSV artifacts include `master_results.csv`.
- CSV artifacts include `lda_*.csv` tables (filings, issues, lobbyists) when LDA is enabled.
- CSV artifacts include `fara_*.csv` tables (registrants, foreign principals, documents, short forms) when FARA is enabled.
- Match confidence values are reported as percentages; any non-100% matches are flagged for manual review.
