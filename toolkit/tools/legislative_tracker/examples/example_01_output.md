# Example 1: Expected output structure

## search_results.json (excerpt)
```json
[
  {
    "bill_id": 1234567,
    "number": "HR 1234",
    "title": "Artificial Intelligence Accountability Act of 2026",
    "state": "US",
    "status": "Introduced",
    "last_action": "Referred to the Committee on Science, Space, and Technology",
    "last_action_date": "2026-02-15",
    "url": "https://legiscan.com/US/bill/HR1234/2026",
    "relevance": 98
  }
]
```

## report.md (excerpt)
```markdown
# Legislative Search Report

**Query:** artificial intelligence
**Jurisdiction:** US
**Year:** 2026
**Results:** 15 bills found

| # | Bill | State | Status | Last Action | Date |
|---|------|-------|--------|-------------|------|
| 1 | HR 1234 — Artificial Intelligence Accountability Act | US | Introduced | Referred to Committee | 2026-02-15 |
```
