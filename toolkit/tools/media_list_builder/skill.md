---
name: media-list-builder
description: Build a targeted media list for a policy issue, campaign, or narrative angle using recent coverage, outlet filters, geography, and media-type constraints, then draft personalized journalist pitches from the returned contacts.
---

# Media List Builder

## Goal
Produce a usable outreach list anchored to recent relevant coverage, with enough contact and pitch context for a human operator to verify and start pitching quickly.

## Inputs
- `issue` — the primary issue, narrative, or pitch topic (required)
- `location` — geography or outlet scope constraint such as `US`, state, or city/metro (required)
- `media_types` — one or more of mainstream, print, digital, trade, broadcast, or podcast (required)
- `num_contacts` — requested list size (required)
- optional `broad_topic`
- optional `coverage_desk`
- optional pitch-drafting context from a selected contact row

## Prereqs
- Python runtime and local dependencies must be available.
- Search providers and the configured LLM-compatible endpoint should be available for best results.
- Output must be treated as a draft list for human review before outreach.

## Process
1. Interpret the issue as the primary search subject, then use any broad topic or coverage desk only to expand the search space.
2. Retrieve recent relevant coverage, filter by geography and media type, and keep story-backed evidence whenever possible.
3. Rank contacts by coverage fit, recency, and pitchability, then assemble the requested list and export downloads.
4. If drafting a pitch from a selected row, use the instruction stack below and personalize the email to that contact's actual coverage.

## Output
- `media_list.md` — readable contact table with coverage context and pitch angles
- `media_list.xlsx` — spreadsheet export for sorting and outreach workflow
- `media_list.json` — structured result data for the app
- personalized pitch email draft when the user triggers pitch generation from a contact

## Pitch Drafting Stack
Use these materials in order when generating a one-to-one journalist pitch:
1. `pitch_instructions/pitch_best_practices.txt`
2. `PITCH_STYLE_GUIDE.md`
3. `pitch_agent_instructions.md`
4. `pitch_examples/` for calibration only

The best-practices file is authoritative. The examples are not templates.

## Rules
- Keep the user's issue literal and primary; do not let broad-topic expansion replace it.
- Do not invent journalists, hosts, emails, story links, quotes, interviews, exclusives, or access.
- Prefer specific story evidence over desk pages, author indexes, or generic site sections.
- Personalized pitches must stay under 200 words and read like direct one-to-one outreach, not a press release.
- Mark results as draft research that requires human verification before external use.
