---
name: clip-cleaner
description: Clean messy copy-pasted article text into professional clip format. Use when user asks to clean an article, fix pasted text, remove ads from article text, or prepare a clip for a report.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Media Clip Cleaner

## Goal
Clean raw copy-pasted article text into a professional clip: italic subtitle/lede, no headline, no ads/clutter, clean body paragraphs.

## Inputs
- **text**: Raw article text — provide via file, raw string, or clipboard
- **mode**: `llm` (recommended) or `local` (rule-based fallback)
- **title**: Article title for context (optional, helps LLM mode)

## Scripts
- `tools/media_clip_cleaner/execution/clean_clip.py` — Cleans raw text via rules or LLM

## Process

### Step 1: Clean the article
**LLM mode (recommended):**
```bash
python3 tools/media_clip_cleaner/execution/clean_clip.py \
  --mode llm \
  --input-file "RAW_FILE_PATH" \
  --output-file "CLEANED_OUTPUT_PATH" \
  --fallback-local
```

**Local mode (no API key needed):**
```bash
python3 tools/media_clip_cleaner/execution/clean_clip.py \
  --mode local \
  --input-file "RAW_FILE_PATH" \
  --output-file "CLEANED_OUTPUT_PATH"
```

**From clipboard (macOS):**
```bash
python3 tools/media_clip_cleaner/execution/clean_clip.py \
  --clipboard \
  --mode llm \
  --output-file "CLEANED_OUTPUT_PATH" \
  --fallback-local
```

### Step 2: Verify output
- Read the cleaned output
- Check it starts with italic subtitle/lede (not the headline)
- Confirm no ads, UI clutter, or "read more" fragments remain
- Confirm body paragraphs are complete

## Output
**Deliverable:** Cleaned markdown text file ready for insertion into a clips report.

Output contract:
1. Starts with subtitle/lede in italics
2. No main headline
3. No ads, banners, "recommended" blocks, timestamps, photo credits
4. Clean body paragraphs only

## Edge Cases
- **Incomplete paste**: Output will also be incomplete — warn user
- **Interleaved ads**: Some may slip through local mode; prefer LLM mode
- **LLM API failure**: `--fallback-local` ensures a result is still produced
- **No subtitle detected**: Script is conservative; may skip italicization

## Environment
Optional (for LLM mode):
```
OPENAI_API_KEY=your_key
```
