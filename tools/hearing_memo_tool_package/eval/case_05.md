# Eval Case 05 - Memo date vs hearing date warning

## Input
```bash
python3 tools/hearing_memo_tool_package/execution/run.py \
  --input tools/hearing_memo_tool_package/eval/inputs/case_01_transcript_full.txt \
  --memo-date "Wednesday, March 11, 2026" \
  --output tools/hearing_memo_tool_package/eval/runs/case_05/memo.docx \
  --json-output tools/hearing_memo_tool_package/eval/runs/case_05/bundle.json \
  --text-output tools/hearing_memo_tool_package/eval/runs/case_05/memo.md
```

## Acceptance Criteria
- Verification JSON contains a DATE_WARNING or DAY_DATE_MISMATCH flag.
- Memo still contains required heading family and footer.
