# Stakeholder Map — Specification

## Purpose

Maps the full actor landscape around a policy issue by discovering and classifying stakeholders from public data sources. Answers: **"Who are all the players on this issue, and where do they stand?"**

Implements DiGiacomo (2025) **#2 Stakeholder Analysis** — the systematic identification and classification of actors by interest, influence, and stance, enabling strategic positioning and coalition planning.

**Distinction from Stakeholder Briefing:** The Briefing tool profiles one *known* stakeholder in depth. This tool *discovers* all relevant actors for a *policy issue* and produces a comparative map.

---

## When to Use

- **Issue entry:** Mapping the landscape before engaging on a new policy topic
- **Coalition strategy:** Identifying potential allies and opponents to engage or neutralize
- **Opposition research:** Understanding who funds and advocates for opposing positions
- **Regulatory landscape:** Mapping corporate and nonprofit actors in a regulatory proceeding
- **Client onboarding:** Briefing a new client on who the key players are in their issue space

---

## Inputs (Directive)

| Input | Required | Description |
|-------|----------|-------------|
| `policy_issue` | Yes | The issue to map. Use 2-4 word phrases for best results: "AI regulation", "drug pricing reform", "clean energy tax credits". Avoid proper bill names (LegiScan searches by keyword, not bill number). |
| `scope` | No | `federal` (default) or `state`. If `state`, also provide `state`. |
| `state` | No | Two-letter state code (e.g., `TX`, `CA`). Only used when `scope=state`. |
| `include_types` | No | Filter to actor types: `legislators`, `lobbyists`, `corporations`, `nonprofits`. Default: all types included. |

---

## Output Contract

### stakeholder_map.xlsx
**Sheet 1: Actors** (10 columns)
- Name, Organization, Type, Stance (color-coded), Influence Tier, Evidence, Issue Areas, LDA Amount ($), Source, Notes

**Sheet 2: Relationships**
- From, To, Relationship Type (lobbies-for / co-sponsors), Label

### stakeholder_map.docx
Narrative summary with sections:
1. Issue Overview (LLM-generated 2-3 sentence landscape summary)
2. Proponents (N) — with proponent coalition summary
3. Opponents (N) — with opponent coalition summary
4. Neutral / Unknown (N)
5. Key Relationships (up to 15, bullet list)
6. Key Coalitions (known alliances)
7. Strategic Notes (swing actors, dynamics, patterns)
8. Footer: disclaimer on LLM inference

### stakeholder_map.html
Interactive Plotly network graph:
- Nodes: color = stance, size = influence tier, shape = actor type
- Edges: dashed = lobbies-for, solid = co-sponsors
- Hover: name, org, type, stance, influence, evidence

### stakeholder_map.json
Full structured result including all actor dicts and relationship dicts.

---

## Data Sources and Actor Discovery Logic

| Source | What it finds | Relationship extracted |
|--------|--------------|----------------------|
| **LegiScan** (`getSearch`) | Bill primary sponsors and co-sponsors | co-sponsors (legislator ↔ legislator) |
| **LDA** (`filing_specific_lobbying_issues`) | Lobbying firms + their clients actively lobbying on the issue | lobbies-for (registrant → client) |
| **GNews** | News headlines — used as context for LLM classification only | None |
| **Brave Search** | Supplemental public issue pages, testimony, coalition, report, and statement evidence | None |

Actor cap: 50 total (up to 20 legislators + up to 30 non-legislative actors).

---

## Limitations and Failure Modes

| Limitation | Notes |
|-----------|-------|
| **LDA keyword sensitivity** | LDA searches the `filing_specific_lobbying_issues` field — results depend on how lobbyists describe the issue. Narrow queries may miss relevant actors; broad queries may include unrelated actors. |
| **No actor profiles** | Actors are classified from LDA/LegiScan data only — no individual deep profiles. For a profile, run Stakeholder Briefing. |
| **Stance is inferred** | The LLM classifies stance based on indirect evidence (what issues they lobby, which bills they sponsor). "Unknown" is the honest answer when evidence is thin. |
| **LegiScan requires API key** | Without `LEGISCAN_API_KEY`, legislators will not appear in the map. Get a free key at legiscan.com. |
| **News/web context only** | GNews and Brave Search are used as supplemental classification context and evidence support, not as the actor-discovery backbone. |
| **Max 50 actors** | For performance and LLM context window reasons. Very large issues (e.g., "healthcare") may be under-represented. |
| **FARA not included** | Foreign agent disclosures are not searched in this tool (use Influence Disclosure Tracker for FARA). |

---

## Human Review Checklist (Yellow Risk)

Before using this map for strategic decisions:

- [ ] Verify the stance of at least the top 5 high-influence actors against primary sources (news, official statements, voting records)
- [ ] Check that the issue summary accurately reflects the landscape you know
- [ ] Confirm that key actors you expect are present — if major players are missing, try a broader or alternative keyword
- [ ] Treat "unknown" stances as genuinely unknown — do not interpret as neutral
- [ ] Do not share the map externally without removing the disclaimer footer
