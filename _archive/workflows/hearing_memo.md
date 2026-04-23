# Workflow - Hearing Memo (V1)

## Product format
- **Repo + app**
  - Repo: prompts, schemas, rules, evaluation, and reference outputs.
  - App: UI, file upload, runtime orchestration, reviewer interface, export delivery.

## Inputs
- Transcript file (PDF or text).
- Optional overrides: hearing title/date/time, committee, memo FROM/DATE/SUBJECT.

## System steps
1. Normalize transcript (remove noise, rebuild paragraphs).
2. Extract hearing record (metadata, speakers, witness roster, Q&A clusters).
3. Compose memo using the fixed heading family.
4. Verify metadata, headings, Q&A organization, and footer.
5. Export DOCX + text + verification JSON.

## Human review (required)
Reviewer checks:
- Hearing title, committee, and dates.
- Witness names and affiliations.
- Overview abstraction level.
- Q&A grouping by member.
- Resolution of all verification flags.

## Export
- Content layer includes confidentiality line once.
- Page footer repetition is handled in export only.

## Not supposed to do
- No autonomous external distribution.
- No invented names, titles, affiliations, or dates.
- No topic-clustered Q&A for this memo family.
