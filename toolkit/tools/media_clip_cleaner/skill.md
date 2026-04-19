---
name: media-clip-cleaner
description: Clean messy pasted article text into clip-ready body text by removing headlines, metadata, captions, widgets, promos, related-story blocks, and other page chrome. Supports a fast local mode and an optional deeper LLM-compatible cleanup mode.
---

# Media Clip Cleaner

## Goal
Turn raw pasted webpage text into clean clip-ready article text that can be inserted into the media clips workflow or edited manually before final report build.

## Inputs
- `raw_text`
- optional `title`
- optional `mode`
- optional `llm_model`
- optional `fallback_local`
- optional `input_file`
- optional `output_file`

## Prereqs
- Python runtime and local dependencies must be available.
- For deeper cleanup mode, the configured LLM-compatible endpoint credentials must be available.

## Process
1. Read raw article text from direct input, file input, stdin, or paste mode.
2. In local mode, strip obvious page chrome and article-adjacent clutter using deterministic rules.
3. In LLM mode, apply the article-coherence prompt, then validate and post-process the output.
4. Preserve only article body text, real deck/subtitle text when present, and real in-article section headers.
5. Return clean text suitable for media clip review or direct insertion into a report.

## Output
- cleaned article text as markdown/plain text
- optional output file when `output_file` is provided

## Rules
- Remove the main article headline and close headline echoes.
- Remove bylines, bios, datelines, timestamps, image captions, credits, share prompts, recommendations, widgets, calendars, footer text, and other page chrome.
- Keep real article paragraphs verbatim; do not summarize or rewrite them.
- Prefer dropping ambiguous clutter over preserving likely non-article text.
- Use manual review if the pasted input is incomplete or structurally corrupted.
