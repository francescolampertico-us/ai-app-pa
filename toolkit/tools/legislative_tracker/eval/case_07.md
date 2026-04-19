# Eval Case 07: Malformed ChangeAgent output repair

## Scenario
- Simulate or capture a summarize run where ChangeAgent returns malformed JSON or tagged text during extraction
- Re-run the summarize flow through the same bill

## Acceptance Criteria
- [ ] Parser repair path recovers structured extraction when possible
- [ ] If repair cannot restore full traceability, the tool returns `blocked_verification` instead of fabricating content
- [ ] Validation flags surface the degraded path
- [ ] Tool does not crash on malformed model output
