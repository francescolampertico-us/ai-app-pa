# Legislative Tracker

## Purpose
Search, track, and summarize legislation across federal and state jurisdictions. Combines bill discovery (keyword search), monitoring (persistent watchlist), and ChangeAgent-powered source-text translation that only emits a verified summary when every displayed line is supported by the bill text.

## When to use
- Scanning for bills related to a policy topic across jurisdictions.
- Monitoring known bills for status changes (committee action, floor vote, enactment).
- Generating a plain-language summary of a bill for a briefing, meeting prep, or messaging.
- Generating a verified source summary grounded directly in bill text and official bill metadata.
- Feeding bill context into downstream tools (Stakeholder Briefing, Meeting Prep Brief, Messaging Matrix).

## Inputs (Directive)
### Required
- `query` — search keywords or phrases (e.g., "artificial intelligence", "data privacy").

### Optional
- `state` — two-letter state code, `US` for federal, or `ALL` for all jurisdictions.
- `year` — legislative session year.
- `bill_id` — LegiScan bill ID for direct lookup.
- `--summarize` — generate AI summary for a specific bill.
- `--watchlist add|remove|list|refresh` — manage the bill watchlist.
- `--out` — output directory.

## Output Contract
Depending on the operation:

### Search
- `search_results.json` — array of bill objects with: bill_id, number, title, state, status, last_action, last_action_date, url, sponsors.

### Summarize
- `bill_summary.md` — structured markdown report containing:
  - **Bill Overview** — number, title, state, status, sponsors, last action
  - **Verified Source Summary** — emitted only when the tool has complete usable bill text and all displayed lines are text-supported
  - Otherwise: **Summary Unavailable** diagnostics explaining why a verified summary could not be produced
- `result_data` from the app/backend summarize action also includes:
  - `summary_status`
  - `source_status`
  - `extraction_status`
  - `verification_status`
  - `validation_flags`
  - `unsupported_claims`
  - `traceability_report`
  - `model_path`

### Watchlist
- `watchlist.json` — persisted list of tracked bills with status snapshots.
- On refresh: flags any bills whose status changed since last check.

## Limitations / Failure Modes
- **API key required**: LegiScan requires a free API key; tool will error without it.
- **ChangeAgent required**: Summarization requires ChangeAgent credentials and proxy routing.
- **Rate limits**: Free tier allows 30,000 requests/month. Heavy usage across many states may hit limits.
- **Bill text availability**: If complete usable bill text is unavailable, the tool must refuse to produce a verified summary.
- **Amendment-heavy text**: Strike/insert drafting can block verified summary generation if the extracted claims cannot be traced cleanly.
- **AI summary accuracy**: Verified summaries are constrained to direct textual support; unsupported lines are blocked rather than shown.
- **Stale status**: Bill status is cached; real-time changes may not reflect immediately.
- **Long bills**: Very long bills are chunked section-by-section; verified output is allowed only if extraction and traceability remain complete.

## Human Review Checklist (Risk: Yellow)
- Confirm bill numbers and titles match official sources (legislature website).
- Spot-check AI summary against actual bill text for accuracy.
- Verify talking points are balanced and not one-sided.
- Validate sponsor names and party affiliations.
- Check status is current before using in external communications.
- Review "Assumptions & Unknowns" section — do not present uncertain claims as facts.
