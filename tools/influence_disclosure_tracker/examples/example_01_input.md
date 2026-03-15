# Example 01 - Combined LDA + FARA Query

## Directive
- **Entities:** Microsoft, OpenAI
- **From:** 2024-01-01
- **To:** 2024-12-31
- **Sources:** lda,fara
- **Out:** ./output
- **Max results:** 500

## Command
```bash
python3 tools/influence_disclosure_tracker/execution/run.py \
  --entities "Microsoft, OpenAI" \
  --from 2024-01-01 \
  --to 2024-12-31 \
  --sources "lda,fara" \
  --out "./output" \
  --max-results 500
```
