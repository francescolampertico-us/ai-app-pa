# Skill - Congressional Hearing Memo Generator

## Objective

Transform hearing source material into a Mercury-style congressional hearing memo that matches the approved structure, naming conventions, and paragraph rhythm reflected in the submitted reference memo.

## Tool posture

This is not a generic summarization tool.
It is a controlled memo-writing workflow with:
- extraction before drafting
- a fixed memo family
- tight heading policy
- member-by-member Q&A routing
- factual verification before export

## Target memo family

Default structure:
1. FROM / DATE / SUBJECT
2. display title
3. Hearing Overview
4. Committee Leadership Opening Statements
5. Witnesses Introductions and Testimonies
6. Q&A
7. confidentiality footer

Default behavior:
- overview stays high level
- opening statements are summarized speaker by speaker
- witness testimony is summarized witness by witness
- Q&A is grouped by member heading, not by topic cluster
- chair closing remarks, if material, are folded into the chair's Q&A subsection

## Workflow

### Stage 1 - Detect structure
Determine:
- committee name
- hearing title
- hearing date and time
- memo date if provided separately
- whether the hearing uses chair + ranking member or co-chair structure
- witness roster and verified affiliations
- whether Q&A is substantial enough to merit multiple member subsections
- whether chair closing remarks should be folded into the Q&A section

### Stage 2 - Build structured hearing record
Create a hearing record with fields for:
- metadata
- leadership speakers
- witness roster
- opening-statement summaries
- witness-testimony summaries
- Q&A exchanges grouped by member
- closing remarks attachment target
- unresolved metadata items

### Stage 3 - Compose memo
Write the memo using the style guide.
Non-negotiable composition rules:
- use the approved headings exactly
- use the preferred speaker-label formats
- keep the overview general and non-granular
- preserve the descriptive, memo-like prose rhythm
- do not add extra top-level sections

### Stage 4 - Verify
Check:
- metadata line completeness
- day/date consistency
- title consistency
- heading compliance
- speaker heading format
- witness affiliation completeness
- whether closing remarks are placed correctly
- confidentiality footer presence
- unsupported claims

## Heading routing policy

Default headings:
- Hearing Overview
- Committee Leadership Opening Statements
- Witnesses Introductions and Testimonies
- Q&A

Use `Co-Chairs Opening Remarks` only when the hearing is genuinely organized around co-chairs or commissioners rather than committee leadership.

## Speaker-label policy

In subsection headings:
- prefer "Chairman Rick Scott (R-FL)" style
- prefer "Ranking Member Kirsten Gillibrand (D-NY)" style
- prefer "Senator Tommy Tuberville (R-AL)" style
- preserve witness honorific + affiliation in heading

In prose:
- use shorter forms such as "Chairman Scott," "Ranking Member Gillibrand," "Sen. Tuberville," "Hon. Yoho," "Mr. Chang"

## Compression rules

- compress without flattening the memo
- keep distinct ideas in separate paragraphs
- prefer 2 to 4 sentence paragraphs
- when a witness or member covers both diagnosis and solution, usually split across two paragraphs
- keep Q&A useful and sequential, but not transcript-like

## Factual fidelity rules

- every material claim must be traceable to source text or verified metadata
- if metadata conflicts, flag it
- do not guess titles or affiliations
- do not convert rhetorical testimony into asserted fact without attribution

## Reviewer handoff

Reviewer notes should be generated separately from the memo body.
They may include:
- unresolved metadata conflicts
- affiliation uncertainties
- suggested factual checks
