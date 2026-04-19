# Example 1: Search for AI-related federal legislation

## Directive
Search for bills related to artificial intelligence at the federal level in the current session.

## CLI Command
```bash
python3 tools/legislative_tracker/execution/run.py \
  --query "artificial intelligence" \
  --state US \
  --year 2026 \
  --out "./output/ai_bills"
```

## Expected behavior
- Queries LegiScan `/search` endpoint for "artificial intelligence" in US Congress
- Returns list of matching bills with metadata (number, title, status, sponsors)
- Search results support direct `Preview`, `Detailed`, and `Track` actions in the app
- Saves `search_results.json` and `report.md` to output directory
