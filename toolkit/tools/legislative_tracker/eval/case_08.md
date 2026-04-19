# Eval Case 08: Missing source text refusal

## Scenario
- Use a valid bill where LegiScan returns no usable bill text, or simulate missing usable text in a controlled run

## Acceptance Criteria
- [ ] Tool does not return a verified summary body
- [ ] `summary_status` is `blocked_missing_source`
- [ ] Refusal diagnostics explain why verified summary generation is unavailable
- [ ] Bill detail remains downloadable
