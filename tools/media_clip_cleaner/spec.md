# Media Clip Cleaner

## Purpose
Clean messy text copied from news websites into a **professional clip** suitable for pasting into a media monitoring report.

This tool is designed for the “paywall/manual extraction” step: when full-text extraction fails and you must copy/paste the article yourself.

## When to use
- A clip contains `[PASTE FULL TEXT HERE]` because extraction failed (often paywalls).
- Copy/pasted text includes ads, cookie banners, UI elements, “recommended” blocks, or duplicated fragments.

## Input
- Raw pasted text from the article page.
- Optional: file-based input/output for repeatable runs.

## Execution
From repository root:

```bash
python3 tools/media_clip_cleaner/execution/clean_clip.py \
  --input-file /path/to/raw_article.txt \
  --output-file /path/to/cleaned_clip.md
```

Alternative modes:
- `--raw-text "..."` for short snippets
- stdin piping (no flags), e.g. `cat raw.txt | python3 tools/media_clip_cleaner/execution/clean_clip.py`
- interactive paste mode: `--paste`

### LLM mode (recommended for cross-outlet reliability)
Set your API key:

```bash
export OPENAI_API_KEY="<your_key>"
```

Run:

```bash
python3 tools/media_clip_cleaner/execution/clean_clip.py \
  --mode llm \
  --llm-model gpt-5-mini \
  --input-file /path/to/raw_article.txt \
  --output-file /path/to/cleaned_clip.md \
  --fallback-local
```

Notes:
- `--mode llm` calls OpenAI API and then validates output against the contract.
- `--fallback-local` keeps the run resilient if API/validation fails.

## Output contract (what you should get)
1) **Start directly with the subtitle/lede in italics**  
2) **Do not include the main headline/title**  
3) Remove:
   - ads, UI clutter, “read more”, “recommended”, newsletter prompts
   - timestamps/publication dates
   - photo captions/credits
4) Provide the **clean full article body** in normal paragraphs  
5) Do not add any prefacing commentary (no “Here is…”)

## Risk level
**Green** — it’s a text-cleaning tool. Still, do a quick human scan to ensure the body is complete and nothing important was removed.

## Known limitations
- If the pasted input is incomplete (e.g., only part of the article), the output will also be incomplete.
- Some sites interleave unrelated “cards” mid-article; those must be removed manually if they slip through.
- Subtitle detection is conservative: the script italicizes only explicit subtitle/lede/deck markers.
- Local mode may under-clean or over-clean on some outlet-specific templates; prefer LLM mode for highest reliability.
