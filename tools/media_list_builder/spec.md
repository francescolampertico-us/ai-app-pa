# Media List Builder

## Purpose
Generate a targeted media list for pitching a policy issue. Maps to DiGiacomo Process #5 (Media Relations) — the step between "we have a message" and "we pitch it to reporters."

PA professionals spend significant time manually researching journalists, checking beats, and building pitch lists. This tool automates the research phase, producing a structured list of contacts with suggested pitch angles tailored to each journalist's coverage history.

## When to use
- Launching a media campaign around a policy issue and need to identify target journalists.
- Pitching a client's position to relevant reporters in a specific market.
- Preparing for a press conference or media event and need a distribution list.
- Expanding media outreach to new markets or beats.
- Building a trade media list for a niche policy area.

## Inputs (Directive)
### Required
- `issue` — The policy issue or topic to pitch. Can be specific ("AI Safety Act pre-deployment testing requirements") or broad ("renewable energy tax credits").

### Optional
- `location` — Geographic scope. Options:
  - `"US"` or `"national"` — national outlets (default)
  - State name (e.g., `"California"`, `"Texas"`) — state + national outlets
  - City/metro (e.g., `"Washington DC"`, `"Chicago"`) — local + state + national
- `media_types` — Comma-separated filter. Options:
  - `mainstream` — Major national newspapers and wire services
  - `print` — Newspapers and magazines
  - `broadcast` — TV and radio
  - `digital` — Online-only outlets and newsletters
  - `trade` — Industry and policy-specific publications
  - `podcast` — Relevant podcasts
  - Default: all types
- `num_contacts` — Target number of contacts (default: 20, max: 40)

## Output Contract

### Excel Table (media_list.xlsx)
Each row represents one media contact with these columns:

| Column | Description |
|--------|-------------|
| First Name | Journalist's first name |
| Last Name | Journalist's last name |
| Outlet | Publication or media organization |
| Role | Title or beat description (e.g., "Tech Policy Reporter") |
| Media Type | Category: mainstream, print, broadcast, digital, trade, podcast |
| Location | Outlet's geographic focus |
| Pitch Angle | Suggested angle tailored to this journalist's interests |
| Previous Coverage | Title + URL of a relevant previous story (if found) |
| Email | Contact email (pattern-guessed, marked [VERIFY]) |
| Notes | Additional context (e.g., "covers AI for Senate hearings") |

### Markdown Summary (media_list.md)
- Total contacts by media type
- Top outlets represented
- Suggested pitch timing notes

## Limitations / Failure Modes
- **Contact accuracy**: Journalist names and beats are based on LLM knowledge and recent news — reporters change beats frequently.
- **Email addresses**: Pattern-guessed from outlet conventions (firstname.lastname@outlet.com) — ALWAYS verify before sending.
- **Coverage gaps**: Google News may not surface all relevant journalists, especially at smaller outlets.
- **Recency**: LLM knowledge has a cutoff — very new hires or beat changes won't be reflected.
- **Trade media**: Niche publications are harder to identify accurately.

## Human Review Checklist (Risk: Yellow)
- Verify each journalist is still at the listed outlet and covering the listed beat.
- Confirm email addresses before sending any pitches.
- Review pitch angles for strategic fit with your actual campaign message.
- Remove any journalists with known adversarial relationships with your client.
- Check that the list doesn't include journalists who have moved to competitors or left journalism.
- Verify previous coverage links are accessible and relevant.
