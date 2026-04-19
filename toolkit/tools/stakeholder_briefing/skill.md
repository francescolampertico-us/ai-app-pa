---
name: stakeholder-briefing
description: Generate a pre-meeting briefing one-pager for any stakeholder — legislator, lobbyist, NGO leader, or executive. Use when the user needs to prepare for a meeting, understand a stakeholder's policy positions, find their disclosure footprint, or build talking points tailored to a specific meeting objective.
---

# Stakeholder Briefing

## Goal
Synthesize publicly available information — news, lobbying disclosures, and LLM world knowledge — into a concise, actionable pre-meeting brief that a PA professional can review in five minutes.

## Inputs
- `stakeholder_name` — full name of the person or organization (required)
- `meeting_purpose` — why you're meeting; shapes talking points and emphasis (required)
- `organization` — stakeholder's organization if not obvious from name (optional)
- `your_organization` — your org, used to frame talking points from your perspective (optional)
- `context` — additional material: bill text, prior correspondence, internal notes (optional)
- `context_file` — path to a context document (PDF, DOCX, TXT) (optional)
- `include_disclosures` — search LDA, FARA, and IRS 990 for the stakeholder (default: true)
- `include_news` — fetch recent news mentions via Google News (default: true)

## Prereqs
- An LLM API key must be set in the environment for profile synthesis and talking point generation.
- `gnews`, `openai`, `python-docx` must be installed.
- LDA, FARA, and IRS 990 use public APIs — no additional keys required.

## Process
1. **News** — if `include_news`, run two Google News queries (stakeholder name alone; name + meeting topic keywords), deduplicate, and filter for relevance to the meeting objective.
2. **Disclosures** — if `include_disclosures`:
   - For non-government stakeholders: search LDA (lobbying), FARA (foreign agents), and IRS 990 by entity name.
   - If the meeting purpose signals lobbying intelligence is needed, also run a topic-based LDA search on the meeting keywords.
   - Government officials (senators, representatives, etc.) skip entity disclosure search — they don't file LDA.
3. **LLM synthesis** — pass all gathered data to the LLM with the full meeting context; produce structured JSON with profile, policy positions, talking points, and key questions.
4. **Assembly** — render markdown and export DOCX one-pager.

## Output
- `stakeholder_briefing.md` — full briefing with profile, policy positions, disclosure highlights, recent news, talking points, and key questions
- `stakeholder_briefing.docx` — formatted one-pager ready for print or distribution
- `stakeholder_briefing.json` — structured data for downstream use

## Rules
- Never fabricate specific quotes, vote counts, dollar amounts, or bill numbers.
- Talking points must be forward-looking and centered on the meeting objective — past events may provide context but must not be the point itself.
- If a stakeholder is a legislator or government official, do not run entity disclosure searches (they do not file LDA/FARA).
- Disclosure data may lag by one to three years; flag absence of recent data as expected, not as a finding.
- News results depend on Google News availability; treat missing coverage as a data gap, not a fact.
- Mark the output as requiring human review before external use.
