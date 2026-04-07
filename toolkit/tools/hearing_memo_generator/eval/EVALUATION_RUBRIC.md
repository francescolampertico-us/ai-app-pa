# Evaluation Rubric - Congressional Hearing Memo Tool

## Scoring dimensions

Score each dimension from 1 to 5.

### 1. Structural compliance
Checks:
- correct FROM / DATE / SUBJECT block
- display title present
- exact approved top-level headings used
- Q&A present and grouped by member
- confidentiality footer present in the right form

### 2. Factual fidelity
Checks:
- names, roles, and affiliations correct
- memo date and hearing date distinguished correctly
- day-of-week correct
- no unsupported claims
- no overstatement of witness claims as objective fact

### 3. Memo-family fit
Checks:
- overview stays high level and thematic
- opening statements are speaker-by-speaker
- witness summaries follow the submitted memo's descriptive style
- chair closing remarks are handled inside Q&A when relevant
- no stray extra sections appear

### 4. Prose quality
Checks:
- tone is professional and neutral
- paragraphs are short and controlled
- output is readable and not robotic
- output is not transcript-like

### 5. Reviewer usability
Checks:
- memo is easy to scan
- uncertainties are surfaced outside the memo body
- output would be usable after light analyst review

## Minimum acceptable bar

A memo should not be approved unless:
- structural compliance >= 4
- factual fidelity >= 4
- memo-family fit >= 4
- prose quality >= 4
- no critical metadata errors are present

## Automatic fail conditions

Fail immediately if any of the following occurs:
- invented witness or member name
- wrong hearing title
- wrong date or wrong day not flagged
- missing approved top-level section
- non-approved heading variant
- extra closing section added without authorization
- Q&A organized in the wrong pattern for this memo family
