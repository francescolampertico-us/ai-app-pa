# Influence Disclosure Tracker — Canonical Manual Cases

Use the web page at `/influence`.

## IDT-SMK-01

- Tool: Influence Disclosure Tracker
- Goal: Validate a normal single-entity disclosure search with readable report output and CSV tables.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Entities:
  `OpenAI`
- Years:
  select `2024` and `2025`
- Sources:
  select `LDA`, `FARA`, `IRS 990`
- Mode:
  `Basic`
- Match filter after run:
  leave default until results load

### Optional setup / preconditions

- Use a current environment with access to disclosure source APIs.
- Sparse IRS 990 data for the newest year is acceptable if handled clearly.

### What to verify

- The run completes without the page breaking.
- The report renders with a clear summary.
- Table downloads work.
- Year selection behaves correctly.
- Empty-source states are explained instead of silently failing.

### Pass / fail rules

- Pass: report and data tables load, filters work, and downloads are available.
- Fail: year selector breaks, report is unusable, or tables/downloads fail.

### Known risks this case covers

- year selector behavior
- multi-source joins
- empty data handling

### If it fails, log bug as

`Disclosure Tracker smoke run breaks on single-entity search`

### Regression candidate

yes

## IDT-EDGE-01

- Tool: Influence Disclosure Tracker
- Goal: Check multi-entity comparison with sparse-year handling and partial results.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Entities:
  `TikTok, ByteDance`
- Years:
  select `2025`
- Sources:
  select `LDA` and `FARA`
- Mode:
  `Basic`

### Optional setup / preconditions

- Expect some sparse or no-hit behavior depending on source and year.

### What to verify

- The tool distinguishes entities instead of collapsing them into one blob.
- Partial/no-hit states do not crash the page.
- The markdown report still explains what was found.
- Filtered downloads remain usable.

### Pass / fail rules

- Pass: mixed-result output remains understandable and exportable.
- Fail: one entity wipes out the other, empty states are broken, or report text is misleading.

### Known risks this case covers

- multi-entity normalization
- sparse-year handling
- report clarity under partial hits

### If it fails, log bug as

`Disclosure Tracker mishandles multi-entity sparse-year search`

### Regression candidate

yes

## IDT-REG-990PDF-01

- Tool: Influence Disclosure Tracker
- Goal: Verify that deep-mode IRS 990 enrichment can backtrack to an older PDF-backed filing and pull PDF-derived summary detail into the report.
- Priority: P0
- Scenario type: regression

### Exact app inputs

- Entities:
  `OpenAI`
- Years:
  select `2023`
- Sources:
  select `IRS 990`
- Mode:
  `Deep`

### Optional setup / preconditions

- Use a current environment with outbound access to the ProPublica nonprofit API and IRS-hosted filing PDFs.
- This case is specifically meant to catch the pattern where the newest filing year has summary data but no XML/PDF document link, while an older eligible year has a PDF.

### What to verify

- The run completes without breaking the page.
- The deep source table shows a `pdf` source instead of `none` for the matched organization.
- The deep source note explains when a newer no-link year was skipped in favor of an older usable filing.
- The report includes the PDF fallback note and at least one narrative excerpt or other deep-profile detail from the filing.

### Pass / fail rules

- Pass: deep mode backtracks to a usable PDF-backed filing and the report contains PDF-derived organization detail.
- Fail: the run reports `no eligible XML or PDF filing document was available`, or the report contains only basic filing rows with no deep-profile content.

### Known risks this case covers

- deep filing selection
- ProPublica PDF fetch fallback
- OCR-backed PDF extraction
- report population from PDF-derived deep profile

### If it fails, log bug as

`Disclosure Tracker deep mode misses PDF-backed IRS 990 detail when latest year has no document link`

### Regression candidate

yes

## Regression placeholder

- Add the first confirmed disclosure bug here after it is fixed.
