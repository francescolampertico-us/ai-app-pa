---
name: media-clips
description: Search recent news, generate fast cleaned article previews, review and edit clips inline, optionally run deeper cleaning with a configured LLM-compatible endpoint, and build the final media clips report and email artifacts.
---

# Media Clips

## Goal
Find relevant recent coverage, present a fast review queue with light-cleaned previews, let the user edit or paste article text manually when needed, optionally run deeper article cleanup, and then build the final clips report.

## Inputs
- `topic`
- `queries`
- optional `period`
- optional `since`
- optional `target_date`
- optional `source_filter`
- optional `custom_sources`
- optional `max_clips`
- optional `suffix`
- optional `output_dir`
- optional `email_sender`
- optional `email_recipient`
- optional `llm_model`

## Prereqs
- Internet access is required.
- Python dependencies in `tool.yaml` must be installed.
- macOS Mail.app is optional and only needed for draft-email creation.
- If deeper clip cleaning is used, the configured LLM-compatible endpoint credentials must be available.

## Process
1. Query Google News for the requested time window.
2. Filter blocked, duplicate, non-matching, and out-of-window results.
3. Extract article text and author where possible.
4. Apply a light automatic cleanup to produce usable preview text quickly.
5. Present the clips for review so the user can:
   - remove an article
   - edit article text inline
   - paste missing article text manually
   - edit author manually
   - run deeper cleanup only on selected articles
6. Build the final report and email artifacts from the reviewed `clips_data`, not from a fresh hidden re-run.

## Output
- `media_clips_<mon><dd>.docx`
- `media_clips_<mon><dd>_email.txt`
- `media_clips_<mon><dd>_email.html`
- `clips_data.json`
- generator-side `media_clips_<mon><dd>_data.json` when run directly from the script

## Rules
- Preserve article selection quality; do not loosen relevance rules just to make the run faster.
- Use light cleanup in the initial pass and reserve deeper cleanup for selected articles.
- Treat inline user edits and pasted text as the source of truth for final report generation.
- Never assume missing extraction means irrelevant coverage; keep manual paste/edit available.
- Human review is required before circulation outside the team.
