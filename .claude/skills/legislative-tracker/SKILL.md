---
name: legislative-tracker
description: Search, track, and summarize legislation via LegiScan API. Use when user asks to find bills, track legislation, summarize a bill, check legislative status, or monitor policy topics.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Legislative Tracker

## Goal
Search for bills by keyword across federal and state jurisdictions, maintain a watchlist of tracked bills, and generate AI-powered plain-language summaries with impact analysis and talking points.

## Inputs
- **query**: Search keywords — REQUIRED for search mode
- **state**: Two-letter state code, `US` for federal, `ALL` for all (optional, default: US)
- **year**: Legislative session year (optional, default: current)
- **bill_id**: LegiScan bill ID for detail/summary (required for detail and watchlist add/remove)
- **summarize**: Flag to generate AI analysis (optional)
- **watchlist**: Action: `add`, `remove`, `list`, or `refresh` (optional)
- **out**: Output directory (optional)

## Scripts
- `tools/legislative_tracker/execution/run.py` — Full pipeline: search, detail, summarize, watchlist

## Process

### Step 1: Search for bills
```bash
python3 tools/legislative_tracker/execution/run.py \
  --query "KEYWORDS" \
  --state US \
  --year 2026 \
  --out "output/legislative"
```

### Step 2: Get bill detail and AI summary
```bash
python3 tools/legislative_tracker/execution/run.py \
  --bill-id BILL_ID \
  --summarize \
  --out "output/legislative"
```

### Step 3: Manage watchlist
```bash
# Add a bill
python3 tools/legislative_tracker/execution/run.py --watchlist add --bill-id BILL_ID

# List tracked bills
python3 tools/legislative_tracker/execution/run.py --watchlist list

# Check for status changes
python3 tools/legislative_tracker/execution/run.py --watchlist refresh
```

### Step 4: Human review reminder
Notify user to verify:
- Bill numbers and titles match official sources
- AI summary accurately reflects bill provisions (spot-check against full text)
- Talking points are balanced (for AND against)
- Sponsor names and party affiliations are correct
- Status information is current

## Output
**Deliverables:**
- `search_results.json` — bill search results with metadata
- `bill_summary.md` — AI-generated analysis with overview, provisions, impact, talking points
- `watchlist.json` — persisted tracked bills with status history
- `report.md` — combined markdown report

## Edge Cases
- **No API key**: Set `LEGISCAN_API_KEY` env var (free from legiscan.com)
- **No results**: Try broader keywords or different state/year
- **Bill text unavailable**: Summary will note this; uses metadata only
- **Very long bills**: Automatically chunked and synthesized
- **Rate limits**: Free tier allows 30,000 requests/month; cache prevents repeat calls