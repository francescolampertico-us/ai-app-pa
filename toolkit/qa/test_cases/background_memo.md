# Background Memo — Canonical Manual Cases

Use the web page at `/background-memo`.

## BM-SMK-01

- Tool: Background Memo
- Goal: Validate a standard organization memo with clear structure and links.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Subject:
  `Jagello 2000`
- Memo Date:
  `April 13, 2026`
- Sections:

```text
Overview of Activities
Key Leadership
U.S. and NATO Relations
Funding and Membership
Relevant Publications
```

- Additional Context:
  `Czech defense think tank founded by Zbyněk Pavlačík. Focus on transatlantic security cooperation. Hosts annual Prague NATO Days event, the largest public NATO airshow in the world.`
- Source Files:
  none
- Entity Name In Filings:
  `Jagello 2000`
- Sources:
  `lda`, `fara`

### Optional setup / preconditions

- Leave IRS 990 off for this first pass because it is unlikely to help this subject.

### What to verify

- Header, overview, fast facts, requested sections, and links all appear.
- Fast facts are specific but not fabricated.
- Section headings match exactly what was requested.
- Disclosure add-ons do not overwhelm the memo if little is found.

### Pass / fail rules

- Pass: the memo is structurally correct, readable, and exportable.
- Fail: requested headings are missing, links are obviously fake, or output ignores the provided context.

### Known risks this case covers

- section rendering
- context grounding
- link plausibility

### If it fails, log bug as

`Background Memo smoke case fails on structure or context grounding`

### Regression candidate

yes

## BM-EDGE-01

- Tool: Background Memo
- Goal: Check person-focused memo behavior with many sections and a stronger need for restraint.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Subject:
  `Zbyněk Pavlačík`
- Memo Date:
  `April 13, 2026`
- Sections:

```text
Current Role
Institutional Affiliations
Public Commentary
NATO and Security Network
Potential Relevance to U.S. Stakeholders
```

- Additional Context:
  `Founder of Jagello 2000 and a Czech defense policy figure associated with NATO Days. Keep speculative claims low and avoid unsupported personal details.`
- Source Files:
  none
- Entity Name In Filings:
  leave blank
- Sources:
  `lda`

### Optional setup / preconditions

- This is mainly a hallucination-discipline test.

### What to verify

- The memo handles a person subject without inventing biography details.
- Section-heavy structure still renders cleanly.
- Tone stays professional and cautious.

### Pass / fail rules

- Pass: output is useful and restrained.
- Fail: it invents personal facts, unsupported affiliations, or fake links.

### Known risks this case covers

- person-profile hallucinations
- section-heavy formatting
- restraint under limited facts

### If it fails, log bug as

`Background Memo invents unsupported details for person-focused memo`

### Regression candidate

yes

## Regression placeholder

- Add the first confirmed background memo bug here after it is fixed.
