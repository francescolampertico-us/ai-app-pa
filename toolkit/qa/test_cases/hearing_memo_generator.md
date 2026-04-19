# Hearing Memo Generator — Canonical Manual Cases

Use the web page at `/memos`.

## HM-SMK-01

- Tool: Hearing Memo Generator
- Goal: Validate the happy path for transcript ingestion, memo composition, verification, and downloads.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Upload hearing transcript: use a known-good local transcript or PDF if you already have one from prior eval work.
- If no local fixture is available, use this YouTube URL:
  `https://www.youtube.com/watch?v=8L0Q1r9wM1Y`
- FROM Field:
  `TechForward Alliance`
- Memo Date:
  `Monday, April 13, 2026`
- Subject Override:
  `Congressional Hearing Memo`
- Advanced Options:
  - Override hearing title: leave blank
  - Override committee name: leave blank
  - Override hearing date: leave blank
  - Override hearing time: leave blank
  - Confidentiality footer: leave blank

### Optional setup / preconditions

- If the YouTube transcript path is unstable, prefer a local transcript fixture from prior hearing memo eval work.
- API connectivity and model access should be available.

### What to verify

- The run completes and shows a memo preview.
- Verification returns either `PASS` or a reviewable set of flags rather than a broken result.
- The memo follows the required top-level structure in order.
- The overview stays high-level and does not turn into speaker-by-speaker narration.
- DOCX, markdown/text, and JSON downloads work.

### Pass / fail rules

- Pass: memo renders, artifacts download, and the structure matches the spec.
- Fail: missing required sections, broken downloads, malformed memo, or unusable verification output.

### Known risks this case covers

- transcript ingestion path
- verification summary visibility
- artifact wiring

### If it fails, log bug as

`Hearing Memo smoke flow fails on standard transcript`

### Regression candidate

yes

## HM-EDGE-01

- Tool: Hearing Memo Generator
- Goal: Verify advanced overrides can rescue weak auto-detection and still produce a usable memo.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Upload hearing transcript: use a noisy or partially labeled transcript if available.
- If no file is available, reuse the smoke URL and force metadata through overrides.
- YouTube URL:
  `https://www.youtube.com/watch?v=8L0Q1r9wM1Y`
- FROM Field:
  `Policy Operations`
- Memo Date:
  `Monday, April 13, 2026`
- Subject Override:
  `Hearing Memo - AI Oversight`
- Advanced Options:
  - Override hearing title:
    `Oversight Hearing on Artificial Intelligence Risk Management`
  - Override committee name:
    `Senate Commerce Committee`
  - Override hearing date:
    `March 13, 2026`
  - Override hearing time:
    `10:00 AM`
  - Confidentiality footer:
    `Confidential - Not for Public Consumption`

### Optional setup / preconditions

- Best run with a transcript that has weak metadata or messy speaker labeling.

### What to verify

- Overrides appear in the output instead of bad auto-detected metadata.
- The confidentiality footer appears once in the content layer.
- Q&A remains grouped by member rather than by topic.
- Verification flags are relevant and not contradictory.

### Pass / fail rules

- Pass: overrides are honored and output remains structurally correct.
- Fail: overrides are ignored, duplicated, or create malformed headings/footer behavior.

### Known risks this case covers

- metadata override handling
- footer duplication
- Q&A structure drift

### If it fails, log bug as

`Hearing Memo ignores or corrupts metadata overrides`

### Regression candidate

yes

## Regression placeholder

- Start with `REG-0001` in [regression_suite.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/regressions/regression_suite.md).
