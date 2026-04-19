# Legislative Tracker Evaluation Rubric

## Scoring dimensions

Score each dimension from 1 to 5.

### 1. Factual grounding
- Bill number, title, status, and sponsors match source metadata
- No invented provisions, agencies, dates, or thresholds
- Numeric claims are traceable to evidence or metadata

### 2. Provision coverage
- Major operative provisions are surfaced
- Section references appear where available
- Long-bill summaries report realistic extraction coverage

### 3. Uncertainty calibration
- Bills without complete usable source text are blocked honestly
- Amendment-heavy bills are blocked if traceability cannot be preserved
- Refusal diagnostics are explicit and useful

### 4. Stakeholder usefulness
- Verified summary is useful as a plain-language translation of the bill text
- Summary stays within legal mechanics and does not drift into unsupported interpretation
- Section references are available where helpful

### 5. Structural compliance
- All seven required sections are present
- Summary reads like an analyst brief rather than raw notes
- Coverage and validation state are surfaced in JSON/app payloads

### 6. UI success
- Completed summarize jobs always produce visible output
- Download controls for summary and bill detail are available
- Search-path and watchlist-path summarization both render correctly

## Automatic fail conditions

Fail immediately if any of the following occurs:
- unsupported provision appears in the summary
- wrong sponsor, title, or status
- invented number, date, agency, or threshold
- any verified summary appears when full usable bill text is unavailable
- inferred impact or analyst argument appears inside the verified source summary
- completed summarize job produces no visible output in the UI
