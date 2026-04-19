# Messaging Matrix — Canonical Manual Cases

Use the web page at `/messaging`.

## MM-SMK-01

- Tool: Messaging Matrix
- Goal: Validate a full-context message map plus key deliverables.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Core Policy Position:
  `Support the AI Safety and Innovation Act — mandatory pre-deployment safety testing protects consumers without stifling innovation.`
- Core Messages:
  leave blank
- Supporting Facts / Proof Points:

```text
$500 million authorization for the new NIST AI safety institute
Pre-deployment testing threshold tied to large-scale frontier systems
Safe harbor for firms that comply with the testing standard
Senate committee vote: 19-7
```

- Supporting Context:

```text
The bill establishes a federal pre-deployment testing requirement for the most capable AI systems, creates a NIST-led safety evaluation framework, and gives companies a compliance safe harbor if they complete the required testing. Supporters argue it protects consumers while preserving innovation by focusing only on frontier systems above a high compute threshold.
```

- Organization Name:
  `TechForward Alliance`
- Primary Target Audience:
  `Senate Commerce Committee members`
- Deliverables:
  `Hill Talking Points`, `News Release`, `Social Media`, `Grassroots Email`, `Op-Ed Draft`

### Optional setup / preconditions

- No file upload needed for the first pass.

### What to verify

- Message Map loads with one clear overarching message and distinct pillars.
- Proof points use the provided facts rather than invented specifics.
- Each selected deliverable appears and feels structurally correct.
- DOCX, markdown, and JSON downloads work.

### Pass / fail rules

- Pass: message map and deliverables are specific, internally consistent, and exportable.
- Fail: output is generic despite context, facts are invented, or exports fail.

### Known risks this case covers

- context grounding
- variant generation
- export wiring

### If it fails, log bug as

`Messaging Matrix smoke case produces generic or broken deliverables`

### Regression candidate

yes

## MM-EDGE-01

- Tool: Messaging Matrix
- Goal: Check thin-context behavior and output discipline when the tool has very little grounding.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Core Policy Position:
  `Support a bipartisan permitting reform package to speed clean energy and transmission projects.`
- Core Messages:
  leave blank
- Supporting Facts / Proof Points:
  leave blank
- Supporting Context:
  `Limited context provided. Keep claims cautious and avoid specific statistics unless directly supported.`
- Organization Name:
  `Grid Modernization Coalition`
- Primary Target Audience:
  `Moderate Senate offices`
- Deliverables:
  `Hill Talking Points`, `Social Media`

### Optional setup / preconditions

- This is a quality-discipline test, not a data-rich test.

### What to verify

- The tool stays useful without pretending to know unsupported facts.
- Messaging remains cautious and plausible.
- Shorter deliverable set is respected.

### Pass / fail rules

- Pass: output is strategically usable and careful about unsupported specifics.
- Fail: it hallucinates legislative numbers, fake votes, or fake quotes.

### Known risks this case covers

- hallucination risk under thin context
- variant selection fidelity
- factual restraint

### If it fails, log bug as

`Messaging Matrix hallucinates specifics when context is thin`

### Regression candidate

yes

## Regression placeholder

- Add the first confirmed messaging matrix bug here after it is fixed.
