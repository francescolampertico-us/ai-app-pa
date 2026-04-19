---
name: hearing-memo-generator
description: Generate a house-style congressional hearing memo from transcript or hearing-source text using controlled headings, member-by-member Q&A routing, metadata checks, and a verification pass. Supports structured extraction with optional LLM-compatible processing plus fallback heuristics.
---

# Hearing Memo Generator

## Goal
Turn a hearing transcript or hearing-source text into a house-style congressional hearing memo that matches the approved structure, heading family, and verification requirements before human review.

## Inputs
- `input`
- optional `hearing_title`
- optional `hearing_date`
- optional `hearing_time`
- optional `committee`
- optional `memo_from`
- optional `memo_date`
- optional `subject`
- optional `confidentiality_footer`
- optional `output`
- optional `text_output`
- optional `json_output`
- optional `verbose`

## Prereqs
- Python runtime and local dependencies must be available.
- Transcript or hearing-source text must be available as PDF or text input.
- For best extraction quality, the configured LLM-compatible endpoint credentials should be available.

## Process
1. Read the hearing transcript or source text and detect core metadata.
2. Build a structured hearing record with metadata, leadership statements, witness material, and Q&A exchanges.
3. Compose the memo using the approved heading family and house style.
4. Route Q&A by member rather than by topic cluster.
5. Run verification for metadata completeness, heading compliance, title consistency, and unsupported claims.
6. Export the memo as a draft for human review.

## Output
- memo draft in DOCX format
- rendered memo text
- verification output
- optional structured bundle when requested

## Rules
- Use only the approved top-level sections and preserve their order.
- Keep the hearing overview high level and non-granular.
- Group Q&A under member headings, not topical headings.
- Do not invent names, titles, affiliations, or dates.
- Flag unresolved metadata and factual uncertainty for reviewer follow-up.
