# Eval Case 02 — Drug Pricing Reform (Federal)

## Input
```
policy_issue: "drug pricing reform"
scope: federal
include_types: ["lobbyists", "corporations", "nonprofits"]
```

## Pass criteria

- [ ] Returns at least 8 actors (no legislators — filtered by include_types)
- [ ] No legislators in output (correctly filtered)
- [ ] Pharmaceutical companies and patient advocacy groups present
- [ ] LDA lobbies-for edges present (pharma clients + their lobbying firms)
- [ ] Strategic notes mention the industry/patient coalition dynamic
- [ ] Actors limited to lobbyists, corporations, and nonprofits only

## Fail criteria

- Legislators appear in output (filter not applied)
- Fewer than 5 actors returned
- LDA amount reported as null for all actors with filing data present
- Evidence text is generic placeholder, not issue-specific
