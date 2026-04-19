# Eval Case 02 - Noisy transcript cleanup

## Input
Note: input files live in eval/inputs and are not committed to git.

```bash
python3 toolkit/tools/hearing_memo_generator/execution/run.py \
  --input toolkit/tools/hearing_memo_generator/eval/inputs/case_02_transcript_noisy.txt \
  --output toolkit/tools/hearing_memo_generator/eval/runs/case_02/memo.docx \
  --json-output toolkit/tools/hearing_memo_generator/eval/runs/case_02/bundle.json \
  --text-output toolkit/tools/hearing_memo_generator/eval/runs/case_02/memo.md
```

## Acceptance Criteria
- No inline timestamps (e.g., "(00:21)") remain in memo prose.
- Speaker labels are normalized (no "SENATOR X:" transcript-style labels in body).
- Output still follows the approved heading family.
