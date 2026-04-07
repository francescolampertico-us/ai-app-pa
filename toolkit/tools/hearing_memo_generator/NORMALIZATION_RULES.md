# Normalization Rules

## Purpose

Normalization happens before extraction. Its job is to remove format noise without changing meaning.

## Global rules

- preserve all substantive content
- never delete speaker names
- never rewrite claims during cleanup
- keep a log of cleanup actions if the app supports it
- if a cleanup rule might destroy meaning, do not apply it automatically

## Rule set by artifact type

### 1. Cover and vendor noise
Remove or demote:
- repeated vendor headers
- repeated footer strings
- copyright notices
- support phone numbers
- page-number clutter

Do not remove:
- official hearing title
- explicit hearing date
- official speaker or witness roster

### 2. Publication metadata vs hearing metadata
Track separately:
- publication timestamp
- hearing date
- hearing time
- memo date

Rules:
- publication time is not the hearing time unless explicitly stated as such
- if both exist, preserve both in extraction notes
- if they conflict, flag the conflict

### 3. Timestamp cleanup
Strip inline timestamps such as:
- `(00:21)`
- `00:21`
- similar transcript timing markers

But do not strip:
- hearing time in metadata
- dates
- numbered legislative references

### 4. Speaker label cleanup
Normalize speaker tags such as:
- `SMITH:`
- `Rep. Rich McCormick (R-Ga.)`
- `>> Thank you, Commissioner Brands.`

Rules:
- preserve the most informative label available
- map later shorthand back to the canonical speaker when supported
- do not merge two speakers because of similar names

### 5. Paragraph rebuilding
Rebuild paragraphs when:
- line breaks are clearly due to PDF wrapping
- sentences are broken mid-line
- hyphenation is artificial

Do not rebuild across:
- speaker changes
- panel changes
- obvious section boundaries

### 6. Panel detection
Signals of panel changes may include:
- explicit `Panel I` / `Panel II`
- fresh witness introductions
- moderator statements introducing the next group
- long title cards in transcript exports

If not clear, keep one panel and flag uncertainty.

### 7. Weak metadata handling
If metadata is missing:
- leave field null
- flag it for review
- do not infer from general subject matter alone

## Output expectation

Normalization should produce:
- cleaned text
- detected source profile
- metadata candidates
- cleanup notes
