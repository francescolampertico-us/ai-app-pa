# Stakeholder Map — Canonical Manual Cases

Use the web page at `/stakeholders`.

## SMB-SMK-01

- Tool: Stakeholder Map
- Goal: Validate the main issue-discovery workflow with table, summary, and exports.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Policy Issue:
  `AI regulation`
- Scope:
  `Federal`
- State:
  leave blank
- Include Types:
  `Legislators`, `Lobbyists`, `Corporations`, `Nonprofits`

### Optional setup / preconditions

- LegiScan access improves this case; without it, legislators may be thin or absent.

### What to verify

- The run completes and shows actor data.
- Network analysis tab renders.
- Actor tables and detail modal work.
- HTML, DOCX, spreadsheet, and JSON downloads are available.

### Pass / fail rules

- Pass: the map is navigable, output artifacts exist, and the issue landscape feels plausible.
- Fail: no usable actor set appears, tabs break, or exports are missing/broken.

### Known risks this case covers

- end-to-end stakeholder discovery
- network analysis rendering
- artifact generation

### If it fails, log bug as

`Stakeholder Map smoke case fails to build a usable map`

### Regression candidate

yes

## SMB-EDGE-01

- Tool: Stakeholder Map
- Goal: Check lower-signal federal issue handling and current UI filter behavior.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Policy Issue:
  `data center water use`
- Include Types:
  `Legislators`, `Corporations`, `Nonprofits`

### Optional setup / preconditions

- The current UI is federal-only. Do not test state scope here unless the page adds that control later.
- This case may return fewer actors than the smoke case. That is acceptable if the output remains coherent.

### What to verify

- Federal-only behavior is clear and consistent in the UI.
- Low-signal input does not collapse into garbage actors or a broken graph.
- Confidence labels and evidence still look plausible.

### Pass / fail rules

- Pass: smaller output remains interpretable and the page stays consistent with its current federal-only scope.
- Fail: actor classification becomes obviously random, the UI implies unsupported state scoping, or the page breaks on thin data.

### Known risks this case covers

- federal-only UI clarity
- low-signal issue handling
- confidence/evidence presentation

### If it fails, log bug as

`Stakeholder Map mishandles low-signal issue mapping or federal-only scope clarity`

### Regression candidate

yes

## Regression placeholder

- Start with `REG-0002` in [regression_suite.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/regressions/regression_suite.md).
