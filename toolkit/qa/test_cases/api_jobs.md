# API / Jobs — Canonical Manual Cases

Use the backend endpoints directly or via the Playwright API suite.

## API-SMK-01

- Tool: API / Jobs
- Goal: Validate core backend health and registry endpoints.
- Priority: P0
- Scenario type: smoke

### Exact checks

- `GET /health`
- `GET /api/tools`

### What to verify

- Health returns `{"status":"healthy"}`.
- Tool registry returns the current tool list and includes handler availability metadata.

### Pass / fail rules

- Pass: both endpoints return valid JSON with expected semantics.
- Fail: either endpoint errors or returns malformed data.

### Regression candidate

yes

## API-EDGE-01

- Tool: API / Jobs
- Goal: Check expected validation and not-found behavior.
- Priority: P1
- Scenario type: edge

### Exact checks

- Unknown tool on `POST /api/tools/execute/<bad-tool>`
- Missing `job_id` on `POST /api/tools/open-email-draft`
- Missing job on `GET /api/jobs/<bad-id>/status`
- Missing artifact on `GET /api/jobs/<real-id>/artifacts/<bad-index>`

### What to verify

- The API returns `400` or `404` appropriately.
- Error messages remain readable enough for debugging.

### Pass / fail rules

- Pass: endpoint failures are explicit and correctly typed.
- Fail: endpoints return the wrong code or a broken/unhelpful payload.

### Regression candidate

yes
