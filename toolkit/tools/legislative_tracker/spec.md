# Legislative Tracker

## Purpose
Search, track, and summarize legislation across federal and state jurisdictions. Combines bill discovery (keyword search), monitoring (persistent watchlist), and AI-powered analysis (plain-language summaries with impact assessment and talking points).

## When to use
- Scanning for bills related to a policy topic across jurisdictions.
- Monitoring known bills for status changes (committee action, floor vote, enactment).
- Generating a plain-language summary of a bill for a briefing, meeting prep, or messaging.
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
  - **Plain-Language Summary** — 2-3 paragraphs explaining what the bill does
  - **Key Provisions** — bulleted list of major provisions
  - **Potential Impact** — analysis of who is affected and how
  - **Talking Points FOR** — 3-5 arguments in favor
  - **Talking Points AGAINST** — 3-5 arguments against
  - **Status & Next Steps** — where the bill stands and what's likely next
  - **Assumptions & Unknowns** — what the summary cannot determine

### Watchlist
- `watchlist.json` — persisted list of tracked bills with status snapshots.
- On refresh: flags any bills whose status changed since last check.

## Limitations / Failure Modes
- **API key required**: LegiScan requires a free API key; tool will error without it.
- **Rate limits**: Free tier allows 30,000 requests/month. Heavy usage across many states may hit limits.
- **Bill text availability**: Not all bills have full text available via API; some return only summaries.
- **AI summary accuracy**: LLM may miss political subtext or coalition dynamics (DiGiacomo 2025 warning). Human review essential.
- **Stale status**: Bill status is cached; real-time changes may not reflect immediately.
- **Long bills**: Very long bills are chunked for summarization; synthesis may lose nuance.

## Human Review Checklist (Risk: Yellow)
- Confirm bill numbers and titles match official sources (legislature website).
- Spot-check AI summary against actual bill text for accuracy.
- Verify talking points are balanced and not one-sided.
- Validate sponsor names and party affiliations.
- Check status is current before using in external communications.
- Review "Assumptions & Unknowns" section — do not present uncertain claims as facts.
