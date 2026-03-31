---
name: hearing-memo
description: Generate a congressional hearing memo from a transcript PDF or text file. Use when user asks to create a hearing memo, summarize a hearing, or process a congressional transcript.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Congressional Hearing Memo Generator

## Goal
Produce a house-style congressional hearing memo (DOCX + markdown + verification JSON) from a hearing transcript. V1 locked — output structure is fixed.

## Inputs
- **transcript**: Path to hearing transcript (PDF or text file) — REQUIRED
- **memo_from**: FROM field value (optional)
- **memo_date**: e.g. "Thursday, March 12, 2026" (optional, defaults to today)
- **subject**: Override SUBJECT line (optional)
- **hearing_title**: Override if auto-detection fails (optional)
- **hearing_date**: Override hearing date (optional)
- **committee**: Override committee name (optional)
- **output**: Output DOCX path (optional, defaults to output/memo.docx)

## Scripts
- `tools/hearing_memo_generator/execution/run.py` — Full pipeline: normalize → extract → compose → verify → export

## Process

### Step 1: Run the generator
```bash
python3 tools/hearing_memo_generator/execution/run.py \
  --input "TRANSCRIPT_PATH" \
  --output "OUTPUT_PATH" \
  --from "MEMO_FROM" \
  --memo-date "MEMO_DATE" \
  --subject "SUBJECT_LINE"
```

Add optional overrides as needed:
- `--hearing-title "TITLE"` if auto-detection is uncertain
- `--hearing-date "DATE"` if transcript metadata is unclear
- `--committee "COMMITTEE_NAME"`
- `--json-output "path/verification.json"` for verification data
- `--text-output "path/memo.txt"` for plain text version

### Step 2: Review verification output
- Read the verification JSON if generated
- Check for any flags: missing metadata, heading mismatches, day-of-week errors
- **All flags must be resolved before distribution**

### Step 3: Human review reminder
Notify user that the following must be verified before distribution:
- Title, committee, and dates against the source
- Witness names and affiliations
- Overview abstraction level (should be high-level, non-granular)
- Q&A grouping (must be by member, not by topic)

## Output
**Deliverables:**
- DOCX memo at the specified output path
- Optional: plain text version and verification JSON

## Edge Cases
- **PDF extraction fails**: Try converting PDF to text first, then re-run with text input
- **Co-chair format**: May need `--hearing-title` and `--committee` overrides
- **Noisy OCR transcript**: Speaker segmentation may degrade; flag for manual review
- **Missing OPENAI_API_KEY**: Falls back to heuristic extraction (lower fidelity)

## Environment
Optional in environment:
```
OPENAI_API_KEY=your_key  # improves extraction quality
```
