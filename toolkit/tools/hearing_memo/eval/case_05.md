# Eval Case 05 - Memo date vs hearing date warning

## Input
Note: input files live in eval/inputs and are not committed to git.

```bash
python3 toolkit/tools/hearing_memo/execution/run.py \
  --input toolkit/tools/hearing_memo/eval/inputs/case_01_transcript_full.txt \
  --memo-date "Wednesday, March 11, 2026" \
  --output toolkit/tools/hearing_memo/eval/runs/case_05/memo.docx \
  --json-output toolkit/tools/hearing_memo/eval/runs/case_05/bundle.json \
  --text-output toolkit/tools/hearing_memo/eval/runs/case_05/memo.md
```

## Acceptance Criteria
- Verification JSON contains a DATE_WARNING or DAY_DATE_MISMATCH flag.
- Memo still contains required heading family and footer.
