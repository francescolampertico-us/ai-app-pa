# Bug Backlog

Only confirmed defects go here.

| Bug ID | Tool | Severity | Status | Owner | Found In | Summary | Linked Brief |
|---|---|---|---|---|---|---|---|
| BUG-0001 | background_memo_generator | medium | closed | Claude | BM-SMK-01 | Tool adds an unrequested `FARA Registration` section to the memo, violating the requested section contract and weakening memo clarity. | [BUG-0001.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/bugs/BUG-0001.md) |
| BUG-0003 | background_memo_generator | high | closed | Claude | BM-SMK-01 | Background Memo over-relies on too few research inputs and overweights low-value article details, producing narrow and poorly prioritized coverage. | [BUG-0003.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/bugs/BUG-0003.md) |
| BUG-0002 | legislative_tracker | high | open | Claude | LT-SMK-01 | Legislative Tracker summary job can complete with no visible summary output in the UI. | [BUG-0002.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/bugs/BUG-0002.md) |
| BUG-0005 | media_list_builder | medium | open | Claude | MLB-SMK-01 | Media List Builder location scope UI behaves inconsistently and makes national vs city/metro selection unclear. | [BUG-0005.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/bugs/BUG-0005.md) |
| BUG-0006 | media_list_builder | high | open | Claude | MLB-SMK-01 | Media List Builder can report successful generation without showing any visible contact list in the UI. | [BUG-0006.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/bugs/BUG-0006.md) |
| BUG-0007 | stakeholder_briefing | medium | open | Claude | SB-SMK-01 | Stakeholder Briefing disclosure section includes noisy topic-adjacent activity that is not clearly useful for briefing the stakeholder. | [BUG-0007.md](/Users/francescolampertico/Desktop/capstone_project/toolkit/qa/bugs/BUG-0007.md) |

## Status definitions

- `open` — confirmed and waiting for a fix
- `in_progress` — actively being fixed
- `fixed_pending_verification` — fix landed, regression still needs rerun
- `closed` — verified fixed
