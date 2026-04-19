---
name: stakeholder-map
description: Build stakeholder maps for policy issues using LegiScan and LDA as the structured backbone, with news and Brave Search as supplemental context. Use when the user asks to map stakeholders, identify proponents and opponents, analyze coalitions, or generate a stakeholder network around an issue.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Stakeholder Map

## Goal
Build a structured stakeholder map for a policy issue. The tool discovers actors, classifies their stance and type, extracts relationships, computes network metrics, and produces exportable outputs for analyst review.

## Inputs
- **Policy Issue**: Short issue phrase such as `AI regulation` or `drug pricing reform`
- **Scope** (optional): `federal` or `state`
- **State** (optional): Two-letter code when scope is `state`
- **Include Types** (optional): `legislators`, `lobbyists`, `corporations`, `nonprofits`

## Data Sources
- **LegiScan**: Primary structured source for legislators, sponsors, and co-sponsors
- **LDA**: Secondary structured source for lobbying firms, clients, and lobbies-for relationships
- **GNews**: Supplemental news context for classification
- **Brave Search**: Supplemental public web evidence and surrounding issue context

Structured sources should remain the backbone. Web/news sources help complete the picture but should not replace LegiScan or LDA as the main discovery layer.

## Scripts
All execution logic is in `./execution/`:
- `run.py` - CLI entry point
- `generator.py` - actor discovery, classification, relationship building, strategic analysis
- `analytics.py` - network metrics and priority logic
- `graph.py` - interactive network graph
- `export.py` - Excel and DOCX exports

## Process

### 1. Run the Tool
```bash
python3 ./execution/run.py \
  --policy_issue "artificial intelligence regulation" \
  --scope federal \
  --out ./output
```

Optional filters:
- `--scope state --state TX`
- `--include_types legislators corporations`
- `--no_graph`

### 2. Review Core Outputs
Generated artifacts:
- `stakeholder_map.json`
- `stakeholder_map.md`
- `stakeholder_map.xlsx`
- `stakeholder_map.docx`
- `stakeholder_map.html`

Check:
- actor list is plausible
- major expected actors are present
- stance and evidence look defensible
- relationships are coherent
- network summary uses the latest terminology

### 3. Validate Source Backbone
- Confirm legislators mainly come from LegiScan
- Confirm lobbying relationships mainly come from LDA
- Confirm web/news context is supplemental rather than the main source of actors
- If type filters are used, verify the final actor list includes only the requested types

### 4. Review Strategic Output
Pay special attention to:
- `Bridge Role`
- `Connection Reach`
- `Strategic Relevance`
- `Estimated Influence Tier`

These outputs are directional and should support prioritization, not replace analyst judgment.

## Output
Primary deliverables:
- stakeholder map JSON
- analyst-readable markdown
- Excel actor/relationship export
- DOCX narrative export
- HTML network graph

## Notes
- Use short issue phrases for better retrieval quality
- Treat stance and influence as analyst-facing estimates
- Prefer updating terminology and evidence quality over changing the scoring formula unless necessary
- Keep structured records in priority over web discovery when making future changes
