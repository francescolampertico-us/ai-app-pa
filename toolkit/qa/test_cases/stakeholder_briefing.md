# Stakeholder Briefing — Canonical Manual Cases

Use the web page at `/stakeholder-briefing`.

## SB-SMK-01

- Tool: Stakeholder Briefing
- Goal: Validate the standard pre-meeting briefing flow for a known public official.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Stakeholder Name:
  `Sen. Maria Cantwell`
- Organization:
  `U.S. Senate`
- Meeting Purpose:
  `Discuss support for a federal AI testing and transparency framework.`
- Additional Options:
  - Your Organization:
    `TechForward Alliance`
  - Additional Context:

```text
The meeting is focused on a moderate pro-innovation framing. We want practical guardrails, not a broad slowdown on AI adoption. Emphasize safety testing, competitiveness, and clear federal standards.
```

  - Search disclosure records:
    checked
  - Fetch recent news mentions:
    checked

### Optional setup / preconditions

- No file upload needed for the first pass.

### What to verify

- Profile, policy positions, talking points, and key questions render.
- Disclosure and news tabs appear when data exists.
- Output stays relevant to the meeting purpose instead of becoming a generic biography.
- Downloads work.

### Pass / fail rules

- Pass: the briefing is structured, relevant, and exportable.
- Fail: sections are empty without explanation, tabs break, or content ignores the meeting purpose.

### Known risks this case covers

- purpose-aware synthesis
- optional disclosures/news integration
- export wiring

### If it fails, log bug as

`Stakeholder Briefing smoke case fails to produce a usable meeting brief`

### Regression candidate

yes

## SB-EDGE-01

- Tool: Stakeholder Briefing
- Goal: Check behavior for a thinner-profile stakeholder with optional toggles off.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Stakeholder Name:
  `Center for Humane Technology`
- Organization:
  leave blank
- Meeting Purpose:
  `Explore whether the organization would support a coalition letter on AI child-safety standards.`
- Additional Options:
  - Your Organization:
    `Digital Safety Working Group`
  - Additional Context:
    `Focus on coalition fit, public posture, and likely points of alignment.`
  - Search disclosure records:
    unchecked
  - Fetch recent news mentions:
    unchecked

### Optional setup / preconditions

- This tests graceful degradation when public data is thinner and optional enrichments are disabled.

### What to verify

- The tool still provides a useful profile and talking points.
- Disabled options do not leave broken sections or empty shells.
- The meeting-purpose framing still shapes the output.

### Pass / fail rules

- Pass: the result remains concise and useful despite less data.
- Fail: the page relies on missing enrichments and produces hollow or broken output.

### Known risks this case covers

- thin-profile handling
- toggle-driven rendering
- graceful degradation

### If it fails, log bug as

`Stakeholder Briefing degrades poorly when optional enrichments are disabled`

### Regression candidate

yes

## Regression placeholder

- Add the first confirmed stakeholder briefing bug here after it is fixed.
