# Eval Harness (V1)

Note: `eval/inputs/` and `eval/reference_memos/` are local-only and ignored by git.

## Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r tools/hearing_memo_tool_package/requirements.txt
```

## Running a case
```bash
python3 tools/hearing_memo_tool_package/execution/run.py \
  --input tools/hearing_memo_tool_package/eval/inputs/case_01_transcript_full.txt \
  --output tools/hearing_memo_tool_package/eval/runs/case_01/memo.docx \
  --json-output tools/hearing_memo_tool_package/eval/runs/case_01/bundle.json \
  --text-output tools/hearing_memo_tool_package/eval/runs/case_01/memo.md
```

## Evaluate
- Compare output against the gold references in `eval/reference_memos/`.
- Log deltas using the templates in `eval/deltas/`.
- Classify issues by layer and update only the weak layer (prompts, schemas, verifier, exporter).
