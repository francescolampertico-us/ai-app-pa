# Eval Case 01 — AI Regulation (Federal)

## Input
```
policy_issue: "artificial intelligence regulation"
scope: federal
```

## Pass criteria

- [ ] Returns at least 10 actors total
- [ ] At least 1 legislator discovered (LegiScan)
- [ ] At least 5 actors from LDA
- [ ] Issue summary is factual and coherent (2-3 sentences)
- [ ] All actors have: id, name, stakeholder_type, stance, influence_tier, evidence
- [ ] Stance distribution includes at least 2 of: proponent, opponent, neutral, unknown
- [ ] At least 1 lobbies-for relationship extracted
- [ ] DOCX exports without error and has all sections
- [ ] Excel has 2 sheets: Actors (≥10 rows) and Relationships
- [ ] HTML graph renders without error (nodes visible, edges present)

## Fail criteria

- Returns fewer than 5 actors
- Any actor missing required fields (id, name, stance, influence_tier)
- LLM fabricates evidence not present in source data
- All actors assigned same stance (indicates classification failure)
- JSON output is not valid JSON
