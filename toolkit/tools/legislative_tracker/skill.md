# Skill - Legislative Tracker (DOE-aligned)

Use the Directive -> Orchestration -> Execution pattern to run this tool reliably.

## Directive (what you must decide before running)

### Required
- **Query**: search terms for bill discovery (e.g., `artificial intelligence`, `data privacy`).

### Optional (common)
- **State**: two-letter code, `US` for federal, `ALL` for all (`--state US`).
- **Year**: legislative session year (`--year 2026`).
- **Bill ID**: direct LegiScan bill ID for lookup (`--bill-id 1234567`).
- **Summarize**: generate AI analysis (`--summarize`).
- **Watchlist**: manage tracked bills (`--watchlist add|remove|list|refresh`).
- **Output**: base output folder (`--out /path/to/output`).

### Prereqs
- Set `LEGISCAN_API_KEY` environment variable (free from legiscan.com).
- Set `OPENAI_API_KEY` for bill summarization features.

## Orchestration (how the tool gathers and prepares information)
1) Parse query and optional filters (state, year).
2) Query LegiScan API `/search` endpoint; cache results.
3) For bill detail: fetch `/getBill` and `/getBillText`; decode base64 text.
4) For summarization: send bill text + metadata to LLM with structured prompt.
5) For watchlist: read/update local JSON; on refresh, re-fetch status for all tracked bills.
6) Write output files (JSON, markdown) to output directory.

## Execution (how to run)

### Search for bills
```bash
python3 tools/legislative_tracker/execution/run.py \
  --query "artificial intelligence" \
  --state US \
  --year 2026 \
  --out "./output"
```

### Get bill detail and AI summary
```bash
python3 tools/legislative_tracker/execution/run.py \
  --bill-id 1234567 \
  --summarize \
  --out "./output"
```

### Manage watchlist
```bash
# Add a bill
python3 tools/legislative_tracker/execution/run.py --watchlist add --bill-id 1234567

# List tracked bills
python3 tools/legislative_tracker/execution/run.py --watchlist list

# Check for status changes
python3 tools/legislative_tracker/execution/run.py --watchlist refresh
```

## Output contract (format expectations)
- `search_results.json` — bill search results with metadata.
- `bill_summary.md` — AI-generated analysis with overview, provisions, impact, talking points.
- `watchlist.json` — persisted tracked bills with status history.
- `report.md` — combined report for export.

## Non-negotiables
- Never fabricate bill numbers, sponsor names, vote counts, or status.
- Always include "Assumptions & Unknowns" in AI summaries.
- Always present BOTH sides in talking points (for AND against).
- Flag any bill text that was unavailable or incomplete.
- Cache API responses to respect rate limits.
