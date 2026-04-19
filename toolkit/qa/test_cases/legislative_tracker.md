# Legislative Tracker — Canonical Manual Cases

Use the web page at `/legislative`.

## LT-SMK-01

- Tool: Legislative Tracker
- Goal: Validate a standard federal keyword search and bill summary flow.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Search mode:
  `Broad Search`
- Keywords / Topic:
  `artificial intelligence`
- Jurisdiction:
  `US (Federal)`
- Year:
  `2026`
- Results:
  `Top 10`

### Optional setup / preconditions

- Requires working LegiScan access.

### What to verify

- Search returns a ranked result list.
- Selecting a bill works.
- Summarize action returns a readable bill summary.
- Watchlist add still works for a selected bill.

### Pass / fail rules

- Pass: search, select, summarize, and track all work in one session.
- Fail: search breaks, selected bill context is lost, or summary/watchlist actions fail.

### Known risks this case covers

- end-to-end search flow
- summarize action
- watchlist integration

### If it fails, log bug as

`Legislative Tracker smoke flow fails across search, summary, or tracking`

### Regression candidate

yes

## LT-EDGE-01

- Tool: Legislative Tracker
- Goal: Validate a state-scoped search with ambiguous terms and relevance handling.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Search mode:
  `Broad Search`
- Keywords / Topic:
  `data privacy`
- Jurisdiction:
  `CA`
- Year:
  `2026`
- Results:
  `Top 5`

### Optional setup / preconditions

- Expect some noisy search results because the topic is broad.

### What to verify

- The tool still surfaces plausibly relevant bills.
- The result count setting is respected.
- State scoping is honored.
- Empty or weak-result handling stays clear if no strong match appears.

### Pass / fail rules

- Pass: results are state-scoped, usable, and the page remains stable.
- Fail: federal bills bleed into state view, result limits are ignored, or the UI becomes misleading.

### Known risks this case covers

- jurisdiction filtering
- ambiguous keyword ranking
- result count control

### If it fails, log bug as

`Legislative Tracker mishandles state-scoped ambiguous search`

### Regression candidate

yes

## Regression placeholder

- Add the first confirmed legislative tracker bug here after it is fixed.
