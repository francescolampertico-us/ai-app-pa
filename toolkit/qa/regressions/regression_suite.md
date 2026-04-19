# Regression Suite

This file stays intentionally small. Only add tests that guard an actual bug or a high-risk behavior.

## Open regression slots

### REG-0001
- Source Bug ID: TBD
- Tool: Hearing Memo
- Exact rerun input: use the first confirmed hearing memo bug case
- Must-stay-true assertions:
  - The original failure no longer appears.
  - Required memo structure still matches the spec.
- Adjacent risks to recheck:
  - verification flags
  - download artifacts
- Last passed date: not run
- Status: open

### REG-0002
- Source Bug ID: TBD
- Tool: Stakeholder Map
- Exact rerun input: use the first confirmed stakeholder map bug case
- Must-stay-true assertions:
  - The original failure no longer appears.
  - Actor table and network output still render.
- Adjacent risks to recheck:
  - HTML export
  - confidence labels
- Last passed date: not run
- Status: open

### REG-0003
- Source Bug ID: BUG-0001
- Tool: Background Memo
- Exact rerun input: rerun `BM-SMK-01` from `toolkit/qa/test_cases/background_memo.md`
- Must-stay-true assertions:
  - Output includes only the user-requested section headings.
  - No extra disclosure section is injected into the main memo body unless explicitly requested.
- Adjacent risks to recheck:
  - overview should not announce sections the user did not request
  - section naming should preserve readable capitalization
- Last passed date: 2026-04-13
- Status: passed

### REG-0004
- Source Bug ID: BUG-0002
- Tool: Legislative Tracker
- Exact rerun input: rerun `LT-SMK-01` from `toolkit/qa/test_cases/legislative_tracker.md`, including the summarize step after selecting or tracking a bill
- Must-stay-true assertions:
  - A completed summarize job always produces visible summary output in the UI.
  - The user can download the rendered summary after it appears.
- Adjacent risks to recheck:
  - summarize from watchlist vs summarize from selected search result
  - selected bill context and bill detail download
- Last passed date: not run
- Status: open

### REG-0005
- Source Bug ID: BUG-0003
- Tool: Background Memo
- Exact rerun input: rerun `BM-SMK-01` from `toolkit/qa/test_cases/background_memo.md`
- Must-stay-true assertions:
  - `Overview of Activities` covers the organization's real activity mix, not just one event or one recent article cluster.
  - Low-value operational details do not crowd out higher-level, decision-relevant facts.
  - The memo reads as a broad backgrounder, not a synthesis of only a few recent news items.
- Adjacent risks to recheck:
  - link diversity
  - fast facts prioritization
  - section-level clarity and paragraph organization
- Last passed date: 2026-04-13
- Status: passed

### REG-0006
- Source Bug ID: BUG-0005
- Tool: Media List Builder
- Exact rerun input: rerun `MLB-SMK-01` from `toolkit/qa/test_cases/media_list_builder.md`, then switch scope between National, State, and City / Metro
- Must-stay-true assertions:
  - Geographic scope behavior is clear and consistent in the UI.
  - National scope does not trap the user in a misleading disabled location flow.
- Adjacent risks to recheck:
  - state value entry
  - city / metro entry
  - payload sent to backend
- Last passed date: not run
- Status: open

### REG-0007
- Source Bug ID: BUG-0006
- Tool: Media List Builder
- Exact rerun input: rerun `MLB-SMK-01` from `toolkit/qa/test_cases/media_list_builder.md`
- Must-stay-true assertions:
  - A completed generation job shows visible contacts in the UI.
  - Result counts and download controls appear when the backend returns contacts.
- Adjacent risks to recheck:
  - empty-state handling
  - media type filters
  - pitch modal launch from a rendered contact
- Last passed date: not run
- Status: open

### REG-0008
- Source Bug ID: BUG-0007
- Tool: Stakeholder Briefing
- Exact rerun input: rerun `SB-SMK-01` from `toolkit/qa/test_cases/stakeholder_briefing.md`
- Must-stay-true assertions:
  - Disclosure content is directly relevant to briefing the named stakeholder.
  - Topic-adjacent lobbying noise is filtered or summarized more selectively.
  - The strategic strength of the profile, talking points, and key questions is preserved.
- Adjacent risks to recheck:
  - news relevance
  - policy position grounding
  - tab rendering when disclosure content becomes thinner
- Last passed date: not run
- Status: open

## Add rule

Add a new regression only when:

- a bug was fixed and could realistically return, or
- the workflow is business-critical enough to justify permanent reruns
