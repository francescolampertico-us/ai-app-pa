# Implementation Plan - Congressional Hearing Memo Generator

## 1. Objective

Build a reliable workflow that converts congressional hearing materials into Mercury-style professional summary memos.

The submitted memo is now the primary style reference. The tool should target that memo family's:
- section order
- heading choices
- speaker-label conventions
- paragraph rhythm
- Q&A organization
- footer behavior

This remains a controlled memo-production tool, not a generic summarizer.

## 2. Key implementation change from V1

The first package version captured the broad structure, but it was still too generic.
The submitted memo shows that quality depends on reproducing the format logic, not just the section list.

The updated system therefore locks in:
- exact preferred headings
- exact preferred speaker naming conventions
- high-level overview writing
- member-by-member Q&A grouping
- no separate closing section by default
- a single inline confidentiality footer, with repeated page footers handled by export formatting

## 3. Four-layer pipeline

1. ingest and normalize
2. extract structured hearing data
3. compose memo in the approved memo family
4. verify facts, structure, and style compliance

## 4. Repo-first decisions

The repo must define:
- exact section names
- speaker-label policy
- witness-heading policy
- overview abstraction level
- paragraph-length targets
- Q&A grouping rule
- confidentiality text behavior
- verification rules for date/day conflicts

These decisions should not be improvised in the app.

## 5. Updated output contract

### Metadata block
Exactly three lines:
- FROM:
- DATE:
- SUBJECT:

### Display title
Official hearing title alone.

### Top-level sections
- Hearing Overview
- Committee Leadership Opening Statements
- Witnesses Introductions and Testimonies
- Q&A

### Subsection logic
- opening statements: one subsection per leadership speaker
- witnesses: one subsection per witness
- Q&A: one subsection per participating member whose exchanges are material
- chair closing remarks are appended within the chair's Q&A subsection when relevant

### Footer
Default:
- Confidential - Not for Public Consumption or Distribution

## 6. Data model updates

The structured extraction layer should explicitly capture:
- memo_from
- memo_date
- hearing_date
- hearing_time
- subject_line
- display_title
- opening_section_heading
- witness_section_heading
- qa_section_heading
- leadership_speakers[]
- witnesses[]
- qa_by_member[]
- chair_closing_summary
- confidentiality_footer_text
- metadata_conflicts[]

This allows the composer to reproduce the memo family accurately.

## 7. Composition rules that must be encoded

The composer should:
- keep the overview general and thematic
- avoid naming speakers in the overview unless absolutely necessary
- use full speaker-role headings and shorter prose references
- split dense content into two short paragraphs when that improves readability
- preserve attribution carefully when witnesses make strong claims
- avoid extra headings such as "Closing Remarks" unless explicitly requested

## 8. Verification rules that must be encoded

The verifier should check:
- memo date vs hearing date distinction
- day-of-week correctness
- title consistency between SUBJECT and display title
- subsection heading format compliance
- whether Q&A is grouped by member rather than by topic when using this memo family
- whether chair closing was incorrectly lifted into a new top-level section
- footer presence and exact text
- unsupported claims or overconfident paraphrases

## 9. Evaluation strategy

Use the submitted memo as the canonical style reference and create test cases for:
- high-level overview writing
- long-form subject line generation
- correct role labels in subsection headings
- witness heading formatting with honorifics and affiliations
- sequential member-by-member Q&A summaries
- folding chair closing remarks into the chair subsection
- metadata conflict flagging

## 10. Risks and controls

### Main risks
- generic or robotic prose
- wrong heading string
- wrong speaker-label style
- missing or invented affiliations
- over-detailed overview
- incorrect closing-section handling
- day/date errors

### Controls
- explicit memo family in style guide
- structured extraction fields for routing
- verification pass
- human review gate
- section-level acceptance tests

## 11. MVP scope

V1 should build:
- transcript ingestion
- structured extraction
- Mercury-style memo composition
- verification output
- docx export with page footer support

Do not build yet:
- automated issue tagging across multiple hearings
- committee-monitoring dashboard
- autonomous client distribution

## 12. Repo structure recommendation

```text
hearing-memo-tool/
  README.md
  IMPLEMENTATION_PLAN.md
  STYLE_GUIDE.md
  RISK_POLICY.md
  AGENT_BOUNDARIES.md
  CHANGELOG_V2.md
  tool.yaml
  skill.md
  schema/
    hearing_record.schema.json
    memo_output.schema.json
  prompts/
    extract_hearing.md
    compose_memo.md
    verify_memo.md
  eval/
    EVALUATION_RUBRIC.md
    TEST_CASES.md
  examples/
    STYLE_REFERENCE_NOTES.md
```
