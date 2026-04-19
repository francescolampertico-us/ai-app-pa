# Media Clip Cleaner

## Purpose
Clean messy pasted article text into clip-ready body text for media monitoring workflows.

This tool is used when:
- copied article text includes page chrome, captions, bios, promos, related-story blocks, or footer junk
- extraction quality is weak and the user wants to paste text manually
- a selected article in the media clips workflow needs deeper cleanup before final report build

## When to use
- A clip preview still contains obvious clutter after the light automatic cleanup.
- A paywalled or badly extracted article needs manual paste and cleanup.
- The reviewer wants to run deeper cleanup on one article without rerunning the whole search.

## Inputs

### Required
- `raw_text` — pasted article text or a file/stdin source that resolves to pasted article text

### Optional
- `title` — known article headline to help remove title echoes
- `mode` — `local` or `llm`
- `llm_model` — model identifier for deeper cleanup mode
- `fallback_local` — fallback to local rules if deeper cleanup fails
- `input_file`
- `output_file`
- `--paste` interactive mode

## Modes

### Local mode
- deterministic
- fast
- best for obvious clutter removal
- used safely in larger review workflows

### LLM mode
- slower
- stronger on broad structural judgment across outlets
- uses a configured LLM-compatible endpoint
- followed by validation and post-processing

## Cleaning contract
The output should:
- remove the main headline/title
- remove bylines, bios, datelines, timestamps, image captions, photo credits, promos, navigation, related stories, widgets, footer text, and legal/corporate page chrome
- preserve real article paragraphs verbatim
- preserve real in-article section headers
- keep paragraph separation
- avoid commentary such as “Here is the cleaned text”

The output should not rely on outlet-specific string matching alone; it should favor article coherence:
- if a line would not belong if the publisher website disappeared and only the article remained, remove it

## Outputs
- cleaned clip text returned to the caller
- optional output file when requested

## Review requirements
Human review is still recommended when:
- the pasted source text is incomplete
- the article is paywalled or copied in a structurally broken way
- the cleaned output looks too short or too aggressive

Checklist:
- confirm article body is intact
- confirm title and metadata are removed
- confirm no obvious page chrome remains
- confirm author/title/date can still be set manually in the media clips review workflow if needed

## Known limitations
- The cleaner cannot recover article text that was never copied in the first place.
- Severely collapsed one-block pastes may still require manual touch-up.
- Some ambiguous lines may need reviewer judgment, especially on opinion pages and unusual layouts.
