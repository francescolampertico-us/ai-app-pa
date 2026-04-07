# Skill — Media Clips (DOE-aligned)

This skill defines how to run the **Media Clips** tool using the Directive → Orchestration → Execution pattern.

—

## Directive (what you must decide before running)

### Required
- **Topic**: the label for the report (e.g., `India`, `India Media Clips`, `EU AI Act`).
- **Boolean queries**: a comma-separated list of Google News searches.

### Optional (but common)
- **Time window**: `—period` (e.g., `24h`, `72h`, `7d`)
- **Cutoff**: `—since “YYYY-MM-DD HH:MM”` (ignore older stories)
- **Output location**: `—output-dir <path>`
- **Email draft**:
  - `—email-sender you@domain.com`
  - `—email-recipient a@domain.com,b@domain.com`
- **Report date override**: `—target-date YYYY-MM-DD`
- **Filename suffix**: `—suffix Partial`

—

## Orchestration (how the tool gathers and prepares information)

1) Run each Boolean query against Google News.  
2) Filter results:
   - remove blocked sources
   - keep only trusted sources (lists are currently configured in the execution script)
3) Deduplicate articles (avoid repeated links).  
4) Extract article content where possible:
   - if extraction fails (often paywalls), insert `[PASTE FULL TEXT HERE]`.

—

## Execution (how to run)

### 1) Run the script
From the repository root:

```bash
python tools/media_clips/execution/generate_clips.py \
  python tools/media_clips/execution/generate_clips.py \
  --topic "India" \
  --queries '"India" AND ("elections" OR "BJP" OR "Modi"), ("New Delhi" AND "trade")' \
  --period 24h \
  --output-dir "/path/to/output" \
  --email-sender "you@domain.com" \
  --email-recipient "team@domain.com"

```

Notes:
- `--queries` is a comma-separated list. Wrap it in quotes to avoid shell parsing issues.
- If you omit `--period`, the script defaults to **72h on Mondays**, otherwise **24h**.
- If you omit email flags, the `.docx` is still generated; the Mail draft step may be skipped depending on implementation.

### 2) Output artifacts
- A topic folder is created under `output-dir`.
- The report is saved as `.docx` inside that folder.
- A draft email is created in Mail.app (macOS) with the `.docx` attached.

### 3) Human review (required)
Before sending/distributing:
- Replace any `[PASTE FULL TEXT HERE]` blocks for paywalled articles.
- Confirm relevance: each clip actually matches the intended queries.
- Remove duplicates or low-salience items.
- Verify names/titles/dates for sensitive clips.

---

## Paywall workflow (manual step)
If an article is paywalled:
1) Open it in browser (logged in if needed).
2) Copy the article text.
3) Clean it using the auxiliary tool **Media Clip Cleaner** (Gem / tool).
4) Paste the cleaned text into the report where `[PASTE FULL TEXT HERE]` appears.

---

## Output contract (format expectations)
Every report should contain:
- Title page (topic + date)
- Index (numbered list of articles with links)
- Full clips section with: source, linked title, author (if available), date, subtitle/lede, body
- A clear placeholder when full text is not available (`[PASTE FULL TEXT HERE]`)

