# Media Clip Cleaner

## Purpose
Clean messy text copied from news websites into a **professional clip** suitable for pasting into a media monitoring report.

This tool is designed for the “paywall/manual extraction” step: when full-text extraction fails and you must copy/paste the article yourself.

## When to use
- A clip contains `[PASTE FULL TEXT HERE]` because extraction failed (often paywalls).
- Copy/pasted text includes ads, cookie banners, UI elements, “recommended” blocks, or duplicated fragments.

## Input
- Raw pasted text from the article page.

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