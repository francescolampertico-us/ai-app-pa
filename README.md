# AI-Powered Public Affairs Toolkit

A capstone project exploring how generative AI can be systematically integrated into public affairs workflows. Grounded in the DiGiacomo (2025) framework for PA management, validated through practitioner interviews, and backed by a 41-source literature review.

**Author:** Francesco Lampertico — M.A. Political Communication, American University (May 2026)

---

## Project Structure

| Folder | Contents |
|--------|----------|
| `toolkit/` | AI tool packages, governance docs, workflows, evaluation fixtures. Primary deliverable. [GitHub repo](https://github.com/francescolampertico/ai-app-pa) |
| `literature_review/` | Completed web literature review (markdown + evidence matrix) and interactive React presentation app |
| `knowledge/` | Research papers (47), industry reports (6), practitioner interviews (3), blog posts, YT transcripts, university documents |

---

## Tool Catalog

| # | Tool | Version | DiGiacomo Workflow | Status |
|---|------|---------|-------------------|--------|
| 1 | Congressional Hearing Memo Generator | 1.0.0 | #3 Briefing Creation | Gold standard, locked |
| 2 | Media Clips | 0.1.0 | #1 Legislative Monitoring | Functional |
| 3 | Media Clip Cleaner | 0.3.0 | #1 Legislative Monitoring | Functional |
| 4 | Influence Disclosure Tracker | 0.1.0 | #2 Stakeholder Analysis | Functional |
| 5 | Bill/Regulation Summary | — | #1 Legislative Monitoring | Planned |
| 6 | Stakeholder Map Builder | — | #2 Stakeholder Analysis, #4 Advocacy Campaign | Planned |
| 7 | Stakeholder Briefing | — | #3 Briefing Creation | Planned |
| 8 | Messaging Matrix | — | #4 Advocacy Campaign, #5 Digital PA | Planned |
| 9 | Crisis Response Brief | — | #6 Crisis Communication | Planned |
| 10 | Meeting Prep Brief | — | #7 Institutional Relationship Mgmt | Planned |
| 11 | PA Performance Tracker | — | #8 Performance Measurement | Planned |
| 12 | Grant Proposal Drafter | — | #4 Advocacy Campaign | Planned |
| 13 | Multilingual Content Adapter | — | #5 Digital PA | Planned |

### Planned Tool Descriptions

**5. Bill/Regulation Summary** — Pulls bill text via LegiScan API or Congress.gov and produces a plain-language summary: key provisions, potential impact analysis, and talking points for/against. Complements Hearing Memo (which covers hearings) by covering the legislation itself. Feeds into Messaging Matrix and Stakeholder Briefing.

**6. Stakeholder Map Builder** — Takes a policy issue or legislative topic and builds a structured map of relevant actors: legislators, lobbyists, advocacy orgs, industry groups. Pulls from Disclosure Tracker outputs (LDA/FARA data) and public directories. Outputs a visual map or structured table with positions, influence level, and relationship to the issue.

**7. Stakeholder Briefing** — Generates a pre-meeting or pre-event briefing on a specific stakeholder or organization. Auto-populates with relevant disclosure context from the Disclosure Tracker (lobbying activity, foreign agent registrations), recent media mentions from Media Clips, and any active legislation from Bill/Regulation Summary. One-pager output.

**8. Messaging Matrix** — Takes a core policy position and produces platform-specific communication variants: press release draft, social media posts (by platform), email alert, and internal talking points. Each variant is adapted for audience, tone, and format constraints. Supports rapid response workflows when paired with Media Clips for monitoring.

**9. Crisis Response Brief** — Given a crisis trigger (news event, leaked document, viral social post), generates a structured response package: situation assessment, key facts and unknowns, holding statement, Q&A for spokespeople, internal escalation checklist, and social media response. Time-sensitive by design — optimized for speed over polish.

**10. Meeting Prep Brief** — Takes a meeting subject + attendee names and compiles a one-pager: attendee disclosure records (from Disclosure Tracker), recent media coverage (from Media Clips), relevant bill activity (from Bill/Regulation Summary), and suggested talking points. Chains three existing tools into a single pre-meeting deliverable.

**11. PA Performance Tracker** — Takes a set of PA objectives (legislative outcomes, media coverage targets, stakeholder engagement goals) and tracks progress over time. Ingests outputs from other toolkit tools (clips count, briefings produced, stakeholder meetings logged) to generate a periodic performance dashboard with trend indicators.

**12. Grant Proposal Drafter** — Takes a grant opportunity description + organization profile (mission, past grants, program descriptions) and produces a structured first draft: need statement, objectives, methodology, budget narrative, and evaluation plan. Inspired by practitioner evidence showing 60%+ time reduction on first drafts (Great Plains Action Society via Change Agent AI).

**13. Multilingual Content Adapter** — Takes any toolkit output (memo, briefing, messaging matrix, press release) and produces culturally-adapted translations. Not literal translation — adjusts idiom, formality level, and cultural references for target audiences. Supports PA teams reaching diverse constituencies, a key gap in current workflow tooling.

---

## DiGiacomo Framework Coverage

The toolkit maps to the 8 core PA workflows identified in DiGiacomo (2025):

1. **Legislative/Regulatory Monitoring** — Media Clips, Bill/Regulation Summary
2. **Stakeholder Mapping & Analysis** — Influence Disclosure Tracker, Stakeholder Map Builder
3. **Position Paper & Briefing Creation** — Hearing Memo Generator, Stakeholder Briefing
4. **Advocacy Campaign Planning** — Messaging Matrix, Stakeholder Map Builder, Grant Proposal Drafter
5. **Digital Public Affairs** — Messaging Matrix, Multilingual Content Adapter
6. **Crisis Communication** — Crisis Response Brief
7. **Institutional Relationship Management** — Meeting Prep Brief
8. **Performance Measurement** — PA Performance Tracker

### Tool Pipeline

Tools are designed to chain together, demonstrating systematic AI integration rather than isolated utilities:

- **Media Clips** → **Messaging Matrix** (monitoring feeds response)
- **Media Clips** → **Crisis Response Brief** (breaking news triggers crisis workflow)
- **Influence Disclosure Tracker** → **Stakeholder Map Builder** → **Stakeholder Briefing** (disclosure data builds maps, maps feed briefings)
- **Influence Disclosure Tracker** → **Meeting Prep Brief** (disclosure context for attendees)
- **Bill/Regulation Summary** → **Hearing Memo Generator** (legislation context for hearing analysis)
- **Bill/Regulation Summary** → **Meeting Prep Brief** (active bills relevant to meeting)
- **Any output** → **Multilingual Content Adapter** (translation as a universal downstream step)

---

## Architecture

Every tool follows the **DOE pattern** (Directive-Orchestration-Execution):
- **Directive:** Task specification with explicit constraints and output contract
- **Orchestration:** Data gathering, routing, context management, checkpoint logic
- **Execution:** Deliverable production, verification, human review gate

Each tool package contains: `tool.yaml` (contract), `spec.md` (tool card), `skill.md` (instruction core), `execution/` (Python code), `examples/`, `eval/`.

---

## Key Deadlines

- **March 26, 2026** — Working prototype: 4 tools in Streamlit app shell
- **April 26, 2026** — Complete final product: 13 tools, polished app, documentation

---

## Literature Review

The interactive literature review is available at the deployed URL and in `literature_review/interactive/`. It covers:
- AI adoption landscape in public affairs
- GenAI performance evidence from adjacent fields
- Task allocation and governance frameworks (Mollick 2024)
- Practical integration methods (prompt design, context engineering, skills)
- Tool-building approaches (DOE framework)
