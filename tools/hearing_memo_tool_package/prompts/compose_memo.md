# Prompt - Compose Hearing Memo

## Role

You are writing a Mercury-style congressional hearing summary memo from a validated hearing record.

## Inputs

- structured hearing record
- style guide
- approved heading policy
- default or provided confidentiality footer

## Output

Return a finished memo with this exact top-level structure:
1. FROM / DATE / SUBJECT block
2. display title
3. Hearing Overview
4. Committee Leadership Opening Statements
5. Witnesses Introductions and Testimonies
6. Q&A
7. confidentiality footer

## Memo-family rules

### Overview
- one paragraph only
- high level and thematic
- include committee, hearing title, date, and time
- do not name individual speakers unless unavoidable
- avoid detailed evidence, recommendations, or witness-by-witness recap

### Opening statements
- create one subsection per leadership speaker
- use heading style such as:
  - Chairman Rick Scott (R-FL)
  - Ranking Member Kirsten Gillibrand (D-NY)
- in body text, use short forms such as "Chairman Scott" and "Ranking Member Gillibrand"
- preserve each speaker's main frame and major policy emphasis

### Witnesses
- create one subsection per witness
- preserve verified honorific + affiliation in the subsection heading
- usually summarize testimony in one or two short paragraphs
- keep attribution clear when witnesses make strong claims

### Q&A
- organize by member heading, not by issue cluster
- use heading style such as:
  - Senator Tommy Tuberville (R-AL)
  - Senator Ashley Moody (R-FL)
  - Chairman Rick Scott (R-FL)
- summarize the material sequence of questions and answers in compact prose
- if the chair delivers substantive closing remarks, place them at the end of the chair subsection rather than creating a new section

## Rules

- use the approved headings exactly
- do not create extra top-level sections
- do not expose internal reasoning
- do not invent details not present in the hearing record
- do not overstate significance
- do not place reviewer notes inside the memo body
