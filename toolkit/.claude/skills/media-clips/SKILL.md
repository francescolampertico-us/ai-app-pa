---
name: media-clips
description: Generate a daily media monitoring report with formatted DOCX and optional email draft. Use when user asks to create media clips, run media monitoring, find news articles on a topic, or generate a clips report.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Media Clips Generator

## Goal
Produce a formatted DOCX media clips report from Boolean Google News queries, with optional Mail.app email draft.

## Inputs
- **topic**: Label for the report (e.g. "India Media Clips") — REQUIRED
- **queries**: Comma-separated Boolean search queries — REQUIRED
- **period**: Time window: `12h`, `24h`, `72h`, `7d` (optional, defaults to 72h on Mondays, 24h otherwise)
- **since**: Ignore articles before timestamp `YYYY-MM-DD HH:MM` (optional)
- **target_date**: Override report date `YYYY-MM-DD` (optional)
- **output_dir**: Base output folder (optional)
- **no_email**: Skip email draft creation (optional flag)
- **all_sources**: Include all sources, not just trusted mainstream (optional flag)
- **custom_sources**: Comma-separated trusted domains (optional)

## Scripts
- `tools/media_clips/execution/generate_clips.py` — Full pipeline: query → fetch → deduplicate → extract → build DOCX → email draft

## Process

### Step 1: Run the clips generator
```bash
python3 tools/media_clips/execution/generate_clips.py \
  --topic "TOPIC" \
  --queries "QUERY1,QUERY2" \
  --period "24h" \
  --no-email \
  --output-dir "OUTPUT_DIR"
```

Add optional flags:
- `--all-sources` to include non-mainstream outlets
- `--custom-sources "domain1.com,domain2.com"` for specific outlets
- `--since "2026-03-20 00:00"` to filter by date
- `--email-sender "sender@example.com" --email-recipient "recipient@example.com"` for email draft

### Step 2: Review the output
- Check the generated DOCX in the output directory
- Look for `[PASTE FULL TEXT HERE]` placeholders (paywalled articles)
- If placeholders found, use the **clip-cleaner** skill to clean pasted article text

### Step 3: Handle paywalled articles
For each `[PASTE FULL TEXT HERE]` placeholder:
1. Copy the article text from the source
2. Run the clip cleaner skill to clean it
3. Replace the placeholder in the DOCX

### Step 4: Human review reminder
Notify user to check:
- Relevance of each clip to the queries
- Duplicates or missing high-salience stories
- Names, titles, and dates on sensitive clips
- Recipients before sending email draft

## Output
**Deliverables:**
- DOCX report at `OUTPUT_DIR/TOPIC/` with title page, index, and clips
- Optional: Mail.app email draft with DOCX attached

## Edge Cases
- **No results**: Broaden queries or extend period
- **Paywall-heavy results**: Many `[PASTE FULL TEXT HERE]` — use clip-cleaner
- **Cluttered extraction**: Some sites return noisy text; manual cleanup may be needed
