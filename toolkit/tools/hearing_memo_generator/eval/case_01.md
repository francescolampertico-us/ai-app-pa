# Eval Case 01 - Standard hearing (full transcript)

## Input
Note: input files live in eval/inputs and are not committed to git.

```bash
python3 toolkit/tools/hearing_memo_generator/execution/run.py \
  --input toolkit/tools/hearing_memo_generator/eval/inputs/case_01_transcript_full.txt \
  --output toolkit/tools/hearing_memo_generator/eval/runs/case_01/memo.docx \
  --json-output toolkit/tools/hearing_memo_generator/eval/runs/case_01/bundle.json \
  --text-output toolkit/tools/hearing_memo_generator/eval/runs/case_01/memo.md
```

## Acceptance Criteria
- Output includes the required heading family in the correct order.
- Overview is a single paragraph and does not mention individual speakers.
- Q&A section is organized by member (no topic headings).
- Confidentiality footer appears exactly once in the memo body.
- Verification JSON exists and verdict is not missing.
