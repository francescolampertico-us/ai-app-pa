---
name: background-memo
description: Generate a structured background memo on a client, organization, policy issue, government program, or individual using a standardized memo format, configurable section headings, research support, and a verification-minded draft workflow.
---

# Background Memo

## Goal
Produce a house-style background memo that gives a fast, usable briefing on a subject while preserving the exact user-requested section structure.

## Inputs
- `subject`
- `sections`
- optional `date`
- optional `context`

## Prereqs
- Python runtime and local dependencies must be available.
- For strongest output quality, the configured LLM-compatible endpoint credentials should be available.
- User-provided context should be included when the topic is obscure, niche, or highly current.

## Process
1. Gather lightweight research and normalize the most relevant findings.
2. Build the memo around the fixed top structure: header, overview, fast facts, requested sections, and relevant links.
3. Preserve the user’s requested section list exactly rather than inventing extra top-level sections.
4. Draft the memo in professional briefing prose with concise, decision-useful paragraphs.
5. Export the memo as a draft for human verification.

## Output
- DOCX memo
- markdown/plain-text rendering

## Rules
- Keep the overview high level and useful.
- Keep fast facts concrete and easy to verify.
- Do not invent facts, statistics, citations, URLs, or top-level sections.
- Use the exact requested section headings unless the user explicitly changes them.
- Treat the memo as a draft that requires human fact-checking before external use.
