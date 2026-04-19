# Eval Case 06: UI summarize rendering from search and watchlist

## Scenario
- Run the canonical web flow at `/legislative`
- Use the `LT-SMK-01` inputs from the QA test case
- Summarize once from a selected search result
- Add the bill to watchlist, then summarize from the watchlist path

## Acceptance Criteria
- [ ] Search-path summarize renders visible summary output
- [ ] Watchlist-path summarize renders visible summary output
- [ ] Summary download is available in both paths
- [ ] Bill detail download is available in both paths
- [ ] Coverage and caveat banners appear when present
