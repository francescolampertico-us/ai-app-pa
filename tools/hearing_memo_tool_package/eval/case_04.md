# Eval Case 04 - Q&A excerpt

## Input
```bash
python3 tools/hearing_memo_tool_package/execution/run.py \
  --input tools/hearing_memo_tool_package/eval/inputs/case_04_transcript_qa_excerpt.txt \
  --output tools/hearing_memo_tool_package/eval/runs/case_04/memo.docx \
  --json-output tools/hearing_memo_tool_package/eval/runs/case_04/bundle.json \
  --text-output tools/hearing_memo_tool_package/eval/runs/case_04/memo.md
```

## Acceptance Criteria
- Q&A headings are member names, not issue headings.
- Chair closing remarks (if present) are folded into the chair subsection.
- No extra top-level sections like "Closing Remarks" appear.
