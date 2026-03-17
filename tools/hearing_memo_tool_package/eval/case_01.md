# Eval Case 01 - Standard hearing (full transcript)

## Input
```bash
python3 tools/hearing_memo_tool_package/execution/run.py \
  --input tools/hearing_memo_tool_package/eval/inputs/case_01_transcript_full.txt \
  --output tools/hearing_memo_tool_package/eval/runs/case_01/memo.docx \
  --json-output tools/hearing_memo_tool_package/eval/runs/case_01/bundle.json \
  --text-output tools/hearing_memo_tool_package/eval/runs/case_01/memo.md
```

## Acceptance Criteria
- Output includes the required heading family in the correct order.
- Overview is a single paragraph and does not mention individual speakers.
- Q&A section is organized by member (no topic headings).
- Confidentiality footer appears exactly once in the memo body.
- Verification JSON exists and verdict is not missing.
