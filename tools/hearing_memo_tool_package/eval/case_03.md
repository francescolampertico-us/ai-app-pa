# Eval Case 03 - Opening + witness excerpt

## Input
```bash
python3 tools/hearing_memo_tool_package/execution/run.py \
  --input tools/hearing_memo_tool_package/eval/inputs/case_03_transcript_excerpt.txt \
  --output tools/hearing_memo_tool_package/eval/runs/case_03/memo.docx \
  --json-output tools/hearing_memo_tool_package/eval/runs/case_03/bundle.json \
  --text-output tools/hearing_memo_tool_package/eval/runs/case_03/memo.md
```

## Acceptance Criteria
- Witness headings include honorifics when present in source.
- Overview remains high level even with limited source text.
- No invented affiliations appear in witness headings.
