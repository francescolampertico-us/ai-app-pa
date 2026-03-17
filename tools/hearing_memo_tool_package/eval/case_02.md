# Eval Case 02 - Noisy transcript cleanup

## Input
Note: input files live in eval/inputs and are not committed to git.

```bash
python3 tools/hearing_memo_tool_package/execution/run.py \
  --input tools/hearing_memo_tool_package/eval/inputs/case_02_transcript_noisy.txt \
  --output tools/hearing_memo_tool_package/eval/runs/case_02/memo.docx \
  --json-output tools/hearing_memo_tool_package/eval/runs/case_02/bundle.json \
  --text-output tools/hearing_memo_tool_package/eval/runs/case_02/memo.md
```

## Acceptance Criteria
- No inline timestamps (e.g., "(00:21)") remain in memo prose.
- Speaker labels are normalized (no "SENATOR X:" transcript-style labels in body).
- Output still follows the approved heading family.
