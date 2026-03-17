# Baseline Assessment (2026-03-16)

## Snapshot reviewed
- Local eval runs in `eval/runs/` (not committed to git)

## Observed strengths
- Memo structure largely matches the approved heading family.
- Confidentiality footer is present.
- Overview is high level in the objective/LLM variants.

## Observed issues (by layer)
- **Extraction**
  - Witness honorifics are ambiguous ("Mr./Ms.") when gender is unknown; replace with neutral last-name references or omit honorifics.
  - Hearing title is truncated ("Senate Aging on Drug Supply Dependence on") — needs better title parsing/cleanup.
  - Q&A summaries can become generic (e.g., repeated "asked about specific mechanisms") in fallback mode.
- **Structure**
  - Some outputs read transcript-like (long, unbroken paragraphs) rather than memo-style compression.
- **Style**
  - Mixed use of full names vs short forms in prose; should prefer short-form labels.

## Recommended focus for next iteration
- Tighten title extraction and normalization in `src/normalizer.py`.
- Adjust `_llm_summarize` fallback to avoid the "Mr./Ms." placeholder and generic phrasing.
- Enforce paragraph length targets more aggressively in `src/composer.py`.

## Next steps
- Run eval cases 01–05 and log deltas with `eval/deltas/template.md`.
- Fix the single weakest layer per issue category.

## Case 01 sanity run (2026-03-16)
- Verdict: PASS (with flags)
- Flags:
  - OVERVIEW_SHORT (75 words vs target 110–170)
  - OVERLONG Q&A subsection (Sen. Tommy Tuberville)
- Human checks:
  - Hearing date source may be publication header
  - Missing witness affiliations (all four witnesses)

## Eval run summary (2026-03-16)
Case | Verdict | Flags | Human checks
-----|---------|-------|-------------
case_01 | pass | 2 | 5
case_02 | pass | 2 | 5
case_03 | pass | 2 | 5
case_04 | pass | 2 | 8
case_05 | pass | 3 | 5
