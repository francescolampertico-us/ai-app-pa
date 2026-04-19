# Eval Case 03 - Opening + witness excerpt

## Input
Note: input files live in eval/inputs and are not committed to git.

```bash
python3 toolkit/tools/hearing_memo_generator/execution/run.py \
  --input toolkit/tools/hearing_memo_generator/eval/inputs/case_03_transcript_excerpt.txt \
  --output toolkit/tools/hearing_memo_generator/eval/runs/case_03/memo.docx \
  --json-output toolkit/tools/hearing_memo_generator/eval/runs/case_03/bundle.json \
  --text-output toolkit/tools/hearing_memo_generator/eval/runs/case_03/memo.md
```

## Acceptance Criteria
- Witness headings include honorifics when present in source.
- Overview remains high level even with limited source text.
- No invented affiliations appear in witness headings.
