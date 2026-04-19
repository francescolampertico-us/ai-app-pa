# Example 01 — Input: AI Regulation (Federal)

```
policy_issue: "artificial intelligence regulation"
scope: federal
include_types: null
```

## Expected behavior

- LDA topic search returns lobbying firms and tech companies filing on AI regulation issues
- LegiScan returns AI-related bills (e.g., AI transparency acts, AI safety bills) and their sponsors
- gpt-4o classifies large tech companies (Microsoft, Google) as likely proponents of certain frameworks
- Advocacy groups (e.g., Center for AI Safety) classified as proponents of regulation
- Industry coalitions lobbying against specific mandates classified as opponents
- Network graph shows lobbies-for edges between lobbying firms and tech clients
