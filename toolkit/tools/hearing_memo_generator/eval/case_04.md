# Eval Case 04 - Q&A excerpt

## Input
Note: input files live in eval/inputs and are not committed to git.

```bash
python3 toolkit/tools/hearing_memo_generator/execution/run.py \
  --input toolkit/tools/hearing_memo_generator/eval/inputs/case_04_transcript_qa_excerpt.txt \
  --output toolkit/tools/hearing_memo_generator/eval/runs/case_04/memo.docx \
  --json-output toolkit/tools/hearing_memo_generator/eval/runs/case_04/bundle.json \
  --text-output toolkit/tools/hearing_memo_generator/eval/runs/case_04/memo.md
```

## Acceptance Criteria
- Q&A headings are member names, not issue headings.
- Chair closing remarks (if present) are folded into the chair subsection.
- No extra top-level sections like "Closing Remarks" appear.
