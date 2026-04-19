---
name: legislative-tracker
description: Search, track, preview, and summarize legislation with LegiScan. Use when the user wants to find bills, monitor a watchlist, generate a quick bill preview, or produce a verified bill summary grounded in official bill text.
---

# Legislative Tracker

## Goal
Find legislation, monitor tracked bills, and generate either:
- a quick metadata preview, or
- a verified summary supported by official bill text.

## Inputs
- `query` for bill search
- optional `state`
- optional `year`
- optional `bill_id`
- optional `--summarize`
- optional `--watchlist add|remove|list|refresh`
- optional `--out`

## Prereqs
- `LEGISCAN_API_KEY` must be set.
- The configured summarization API key must be set.

## Process
1. Search bills with LegiScan and return bill metadata.
2. For bill detail, fetch the bill record and available text versions.
3. For preview mode, generate a fast metadata-only preview.
4. For detailed summary mode, normalize bill text, extract directly supported facts, and compose a verified summary only if every displayed line is traceable to the source text.
5. For watchlist actions, update the local tracked-bills store and refresh status snapshots as needed.

## Output
- `search_results.json` for bill searches
- `bill_summary.md` for preview, verified summary, or refusal diagnostics
- `watchlist.json` for tracked bills
- `report.md` for combined export output

## Rules
- Never fabricate bill numbers, sponsors, status, dates, or provisions.
- Never present a preview as if it were a verified summary.
- Never emit a verified summary unless the bill text is usable and every displayed line is traceable.
- Refuse the verified summary when source text is missing or traceability fails.
