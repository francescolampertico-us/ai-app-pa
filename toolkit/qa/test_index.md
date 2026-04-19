# QA Test Index

This is the master board for canonical manual coverage. `Status` refers to overall readiness of the test pack, not product health.

| Tool | Test Pack | Smoke | Edge | Regression Placeholder | Last Run | Status |
|---|---|---:|---:|---:|---|---|
| Hearing Memo | [hearing_memo.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/hearing_memo.md) | Yes | Yes | Yes | Not run | Ready |
| Disclosure Tracker | [influence_disclosure_tracker.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/influence_disclosure_tracker.md) | Yes | Yes | Yes | Not run | Ready |
| Media Clips | [media_clips.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/media_clips.md) | Yes | Yes | Yes | Not run | Ready |
| Media List Builder | [media_list_builder.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/media_list_builder.md) | Yes | Yes | Yes | Not run | Ready |
| Legislative Tracker | [legislative_tracker.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/legislative_tracker.md) | Yes | Yes | Yes | Not run | Ready |
| Messaging Matrix | [messaging_matrix.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/messaging_matrix.md) | Yes | Yes | Yes | Not run | Ready |
| Stakeholder Briefing | [stakeholder_briefing.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/stakeholder_briefing.md) | Yes | Yes | Yes | Not run | Ready |
| Background Memo | [background_memo.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/background_memo.md) | Yes | Yes | Yes | Not run | Ready |
| Stakeholder Map | [stakeholder_map_builder.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/stakeholder_map_builder.md) | Yes | Yes | Yes | Not run | Ready |
| Media Clip Cleaner | [media_clip_cleaner.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/media_clip_cleaner.md) | Yes | Yes | Yes | Not run | Ready |
| Remy | [remy.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/remy.md) | Yes | Yes | Yes | Not run | Ready |
| API / Jobs | [api_jobs.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/api_jobs.md) | Yes | Yes | Yes | Not run | Ready |
| Helper Flows | [helper_flows.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/test_cases/helper_flows.md) | Yes | Yes | Yes | Not run | Ready |

## Default cadence

- Run the smoke case before major demos, handoffs, or fix validation.
- Run the edge case when changing prompts, backend orchestration, or UI input handling.
- Run relevant regressions after each bug fix.

## Case selection rule

- If a tool has not been tested recently, run smoke first.
- If a tool just changed, run smoke plus relevant regressions.
- If quality feels unstable, run edge after smoke before sending anything to Claude.
