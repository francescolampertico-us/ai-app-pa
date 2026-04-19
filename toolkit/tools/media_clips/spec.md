# Media Clips

## Purpose
Generate a review-first media monitoring workflow for a topic or issue:
1. search and collect relevant news,
2. produce fast light-cleaned previews,
3. let the user review, edit, paste, remove, and optionally deep-clean articles,
4. build the final report and email artifacts from the reviewed set.

## When to use
- Daily or ad hoc media monitoring on a country, company, stakeholder, crisis, or policy theme.
- When a team needs a sendable clips packet but still wants manual control before output.
- When light automatic cleanup is helpful but full trust in automatic extraction is not appropriate.

## Inputs

### Required
- `topic` — label used in the report and UI.
- `queries` — one or more search queries sent to Google News.

### Optional
- `period` — `12h`, `24h`, `72h`, `7d`; defaults to `72h` on Mondays and `24h` otherwise.
- `since` — timestamp cutoff in `YYYY-MM-DD HH:MM`.
- `target_date` — date used for report labeling and artifact names.
- `source_filter` / `--all-sources` / `custom_sources` — source filtering mode.
- `max_clips` — cap on accepted articles.
- `suffix` — optional filename suffix when running the script directly.
- `output_dir` — output folder.
- `email_sender`, `email_recipient` — optional Mail.app draft inputs.
- `llm_model` — model selection for deep clip cleaning.

## Workflow

### 1. Discovery
- Search Google News for the requested query set.
- Filter duplicates, blocked sources, international mismatches, and out-of-window results.
- Resolve article URLs.

### 2. Fast extraction
- Extract article text and author when possible.
- Apply light automatic cleanup only:
  - strip obvious metadata and page chrome
  - preserve article body candidates
  - keep the run fast enough for review-first use

### 3. Review
The reviewed article list is the working source of truth. For each article, the user can:
- open the source
- remove the article
- edit author manually
- edit article text manually
- paste article text if extraction failed or was partial
- run deeper cleanup on that one article only

### 4. Final build
- Build report and email artifacts from the reviewed `clips_data`.
- Do not silently discard user edits by rerunning hidden extraction at report time.

## Outputs

### Backend report build
- `media_clips_<mon><dd>.docx`
- `media_clips_<mon><dd>_email.txt`
- `media_clips_<mon><dd>_email.html`
- `clips_data.json`

### Direct script execution
- `media_clips_<mon><dd>[_<suffix>].docx`
- `media_clips_<mon><dd>[_<suffix>]_data.json`
- optional Mail.app draft

## Review requirements
Human review is required before distribution.

Checklist:
- Confirm every clip is relevant.
- Remove duplicates and weak results.
- Fix author names where needed.
- Paste missing article text where extraction failed.
- Use deeper cleanup only when the light preview is not good enough.
- Check dates, names, and links for sensitive outputs.

## Known limitations
- Google News query fetches can be intermittently slow upstream.
- Some sites are slow or poor at text extraction.
- Paywalled sources may still require manual paste.
- Automatic cleanup improves previews but is not perfect; manual editing remains essential.

## Implementation notes
- Speed improvements should preserve article selection behavior as much as possible.
- The tool uses a configured LLM-compatible endpoint for optional deep cleanup, but manual editing is always available as the fallback.
