# Media List Builder — Canonical Manual Cases

Use the web page at `/media-list`.

## MLB-SMK-01

- Tool: Media List Builder
- Goal: Validate a standard national policy media list with downloadable outputs.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Policy Issue To Pitch:
  `AI safety regulation and mandatory pre-deployment testing requirements`
- Geographic Scope:
  `National (US)`
- Target number of contacts:
  `20`
- Media Types:
  `Mainstream`, `Print`, `Broadcast (TV/Radio)`, `Digital / Online`, `Trade / Policy`

### Optional setup / preconditions

- Leave podcast unchecked for the first pass to keep the expected list tighter.

### What to verify

- Contacts load with names, outlets, roles, and pitch angles.
- Type filtering works.
- Markdown, JSON, and spreadsheet downloads work.
- Contact quality looks plausible rather than random.

### Pass / fail rules

- Pass: output is coherent, varied, and exportable.
- Fail: output is mostly duplicates, clearly wrong beats, or downloads fail.

### Known risks this case covers

- contact generation
- output export wiring
- media type filtering

### If it fails, log bug as

`Media List Builder smoke run produces unusable or broken contact output`

### Regression candidate

yes

## MLB-EDGE-01

- Tool: Media List Builder
- Goal: Check narrow niche topic handling and low-result resilience.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Policy Issue To Pitch:
  `State insurance regulation for AI-enabled prior authorization tools`
- Geographic Scope:
  `State`
- State value:
  `California`
- Target number of contacts:
  `10`
- Media Types:
  `Trade / Policy`, `Digital / Online`

### Optional setup / preconditions

- Expect a smaller and more uneven result set than the smoke case.

### What to verify

- The tool still returns targeted contacts rather than padding with obviously irrelevant names.
- Small result sets are presented cleanly.
- Pitch angles remain tied to the niche issue.

### Pass / fail rules

- Pass: fewer results are acceptable if the output remains targeted and usable.
- Fail: the tool hallucinates filler contacts or ignores the scope/topic constraints.

### Known risks this case covers

- niche topic handling
- low-result behavior
- geography sensitivity

### If it fails, log bug as

`Media List Builder fails on narrow issue and state-scoped search`

### Regression candidate

yes

## Regression placeholder

- Add the first confirmed media list bug here after it is fixed.
