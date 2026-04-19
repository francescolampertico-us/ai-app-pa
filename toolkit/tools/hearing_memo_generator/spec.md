# Hearing Memo Generator

## Purpose
Generate a house-style congressional hearing memo from transcript or hearing-source text with strict structure, controlled headings, and a verification pass. Output is always a draft and requires human review before distribution.

## Inputs

### Required
- `input`: Path to hearing transcript (PDF or text).

### Optional
- `hearing_title`, `hearing_date`, `hearing_time`, `committee`: Overrides when auto-detection is uncertain.
- `memo_from`, `memo_date`, `subject`, `confidentiality_footer`: Metadata overrides for the memo header/footer.
- `output`, `text_output`, `json_output`: Output locations.

## Workflow
1. Detect metadata and hearing structure from transcript or source text.
2. Build a structured hearing record for leadership remarks, witness testimony, and Q&A exchanges.
3. Compose the memo using the approved heading family and house style.
4. Verify metadata completeness, title consistency, heading compliance, and unsupported claims.
5. Export the memo as a draft for reviewer approval.

## Output Contract
The memo must include exactly these top-level sections in order:
1. FROM / DATE / SUBJECT block
2. Display title (official hearing title)
3. Hearing Overview
4. Committee Leadership Opening Statements (or `Co-Chairs Opening Remarks` when applicable)
5. Witnesses Introductions and Testimonies
6. Q&A
7. Confidentiality footer (single inline line; repeated page footer handled by export)

Quality requirements:
- Overview is high level and non-granular.
- Q&A is organized by member, not by topic cluster.
- Witness headings preserve honorific + affiliation when verified.
- No invented names, titles, affiliations, or dates.

## Extraction Modes
- Structured extraction with a configured LLM-compatible endpoint when available.
- Heuristic fallback when configured LLM processing is unavailable.

## V1 Freeze (Locked)
**Version locked:** 1.0.0 (2026-03-16)

Accepted input types:
- PDF transcripts (licensed transcript or article-style formats)
- Plain-text transcripts or cleaned notes

Fixed output structure:
- Heading family limited to the approved set in `STYLE_GUIDE.md`.
- Single confidentiality line in the content layer; repeated footers handled by export.

Known limitations (V1):
- Co-chair/commission formats may require manual metadata overrides.
- Highly noisy OCR may reduce speaker segmentation quality.
- Extraction quality is strongest with configured LLM-compatible processing; heuristic fallback is acceptable but lower fidelity.

Fixed style rules:
- Use the exact headings in `STYLE_GUIDE.md`.
- Use third-person, professional, descriptive tone.
- Prefer 2–4 sentence paragraphs; avoid transcript-like narration.
- Use short-form speaker references in prose.

Fixed verification rules:
- Metadata completeness (FROM/DATE/SUBJECT).
- Memo date vs hearing date checks, including day-of-week validation.
- Title consistency between SUBJECT and display title.
- Approved headings only; required sections present.
- Q&A organized by member headings only.
- Confidentiality footer present and unmodified unless explicitly overridden.

## Failure Modes
- Missing or incorrect witness affiliations.
- Over-detailed overview (mentions individual speakers).
- Q&A grouped by issue instead of member.
- Fabricated or overstated claims not grounded in the transcript.
- Footer omitted or modified without authorization.

## Human Review Checklist
- Verify title, committee, and dates against the source.
- Confirm witness names and affiliations.
- Confirm overview abstraction level and tone.
- Validate Q&A grouping by member.
- Resolve all verification flags before distribution.
