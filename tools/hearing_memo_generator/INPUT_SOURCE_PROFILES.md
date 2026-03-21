# Input Source Profiles

## Purpose

These profiles define the source families the tool must support from day one. The point is not to name vendors. The point is to handle their recurring structural patterns predictably.

## Profile 1 - Licensed transcript PDF

### Typical characteristics
- branded cover page
- publication timestamp separate from hearing date
- separate speaker and witness roster pages
- repeated copyright and footer noise
- cleaner transcript body after front matter

### Extraction implications
- do not confuse publication timestamp with hearing date
- use roster pages to build the participant list
- skip or strip licensing language before content extraction
- prefer transcript body for substantive summaries

### Common failure modes
- title captured from a truncated cover-page label
- roster page copied into summary prose
- wrong hearing date if publication date is used

## Profile 2 - Article-style transcript PDF

### Typical characteristics
- transcript starts on page 1
- title and publication datetime appear above body text
- no clean witness roster before testimony
- footer or vendor mark repeated on each page

### Extraction implications
- treat top-line datetime as possible publication metadata unless hearing date is also confirmed in body text
- scan the full document for witness introductions
- avoid letting footer strings contaminate speaker attribution

### Common failure modes
- publication datetime mistaken for hearing start time
- witness section underdeveloped because no roster is present up front
- body text broken by page footer carryover

## Profile 3 - Exported video transcript PDF

### Typical characteristics
- video title or URL at top
- timestamps embedded throughout
- lower-fidelity punctuation and paragraphing
- continuous transcript across multiple panels
- witness names often appear only when introduced later

### Extraction implications
- strip timestamps before summarization
- infer metadata only from explicit statements in transcript
- split panels when witness introductions or moderator transitions make the break clear
- apply stricter uncertainty handling

### Common failure modes
- timestamps leak into the final memo
- poor punctuation causes bad speaker segmentation
- second panel content gets collapsed into the first panel

## Profile 4 - Cleaned notes or internal transcript draft

### Typical characteristics
- prose is already partially normalized
- some metadata may be added manually
- witness affiliations may be incomplete
- ordering may follow the target memo rather than transcript chronology

### Extraction implications
- preserve manual metadata if it is internally consistent
- still run verification for dates, titles, and affiliations
- do not assume missing facts from formatting confidence alone

## Decision rule

If the app cannot classify the source confidently, it should:
1. fall back to `generic_text`
2. apply conservative cleanup only
3. raise a reviewer note that source typing was uncertain
