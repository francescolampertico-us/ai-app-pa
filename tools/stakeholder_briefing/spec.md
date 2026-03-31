# Stakeholder Briefing

## Purpose
Generate a pre-meeting one-pager that gives a PA professional everything they need to know before meeting a stakeholder. Maps to DiGiacomo Process #2 (Stakeholder Analysis) and #3 (Government Relations) — the preparation step between identifying a stakeholder and engaging them.

Grounded in professional practice: PA teams routinely compile briefing memos before Hill meetings, coalition calls, or stakeholder engagements. This tool automates the research and synthesis, producing a structured document ready for review.

## When to use
- Preparing for a meeting with a legislator, lobbyist, NGO leader, or executive.
- Onboarding a new client and need to understand key stakeholders quickly.
- Building a stakeholder map and need individual profiles.
- Before a Hill fly-in or lobby day — generate briefings for each meeting.
- Prepping for a coalition call where you need background on participants.

## Inputs (Directive)
### Required
- `stakeholder_name` — Full name of the person or organization (e.g., "Sen. Maria Cantwell" or "Heritage Foundation").
- `meeting_purpose` — Why you're meeting. Shapes the talking points and what information is emphasized.

### Optional
- `organization` — Stakeholder's org if not obvious from name (e.g., "Senate Commerce Committee").
- `your_organization` — Your org, used to frame talking points from your perspective.
- `context` — Additional material: bill text, prior correspondence, internal notes.
- `include_disclosures` — Search LDA/FARA/IRS 990 for the stakeholder (default: true).
- `include_news` — Fetch recent Google News mentions (default: true).

## Output Contract

### Briefing Header
- Stakeholder name and title/role
- Organization and affiliation
- Meeting purpose
- Date prepared
- Prepared by (your organization, if provided)

### Section 1: Profile
- Background summary (2-3 sentences)
- Current role and responsibilities
- Key policy areas / committee assignments (if legislator)
- Notable positions or public statements

### Section 2: Policy Positions
- 3-5 bullet points on their known positions relevant to the meeting topic
- Any recent votes, statements, or actions

### Section 3: Disclosure Data (if enabled)
- LDA lobbying activity summary (if any)
- FARA foreign agent registrations (if any)
- IRS 990 nonprofit activity (if applicable)
- Presented as brief highlights, not raw data dumps

### Section 4: Recent News
- 3-5 recent news mentions with source, date, and one-line summary
- Focused on items relevant to the meeting topic

### Section 5: Talking Points
- 3-5 suggested talking points for the meeting
- Framed from your organization's perspective (if provided)
- Each with a brief rationale

### Section 6: Key Questions
- 2-3 questions to ask during the meeting
- Based on gaps in public information or strategic opportunities

## Limitations / Failure Modes
- **Profile accuracy**: Bio and positions are LLM-generated from training data — may be outdated or contain errors. Always verify against official sources.
- **Disclosure gaps**: LDA/FARA data may not cover the most recent quarter. IRS 990 data lags by 1-2 years.
- **News recency**: Google News results depend on indexing and may miss breaking news.
- **Talking point relevance**: Points are strategically reasonable but may not align with your specific negotiation strategy.
- **Lesser-known stakeholders**: For non-public figures, the profile will be thin. Provide context to compensate.

## Human Review Checklist (Risk: Yellow)
- Verify stakeholder's current title, role, and organizational affiliation.
- Cross-check policy positions against official statements or voting records.
- Confirm disclosure data highlights are accurate (spot-check against LDA/FARA sources).
- Review talking points for strategic fit with your actual meeting objectives.
- Remove or flag any information that could be outdated.
- Ensure no confidential internal information appears in the document.
