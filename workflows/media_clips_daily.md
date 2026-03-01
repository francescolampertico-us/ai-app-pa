# Workflow — Daily Media Clips (Automated + Paywall Cleanup)

## Goal
Produce a daily media monitoring package:
1) a formatted `.docx` report of relevant articles (with index + full clips), and  
2) a ready-to-send email draft (optional),  
with a manual process to fill paywalled articles using **Media Clip Cleaner**.

## Tools used
- **media_clips** (`tools/media_clips/`) — automated discovery + extraction + `.docx` generation (+ optional Mail.app draft)
- **media_clip_cleaner** (`tools/media_clip_cleaner/`) — manual LLM cleaner for paywalled / messy pasted text

---

## Step 0 — Prepare the Directive
Decide:
- `topic` (e.g., “India”, “EU Tech”, “Italy Energy”)
- `queries` (comma-separated Boolean searches)
- time window:
  - `period` (e.g., `24h`, `72h`, `7d`) and/or
  - `since` (e.g., `YYYY-MM-DD HH:MM`)
- output folder (`output_dir`)
- email settings (optional): `email_sender`, `email_recipient`

Tip: Start conservative (1–3 queries, 12h–24h) to reduce noise.

---

## Step 1 — Run Media Clips (Execution)
From repo root:

```bash
python3 tools/media_clips/execution/generate_clips.py \
  --topic "<TOPIC>" \
  --queries '<QUERY_1>, <QUERY_2>, <QUERY_3>' \
  --period 24h \
  --output-dir "<OUTPUT_DIR>" \
  --email-sender "<SENDER_EMAIL>" \
  --email-recipient "<RECIPIENTS_COMMA_SEPARATED>"
```


Outputs:
- `.docx` report in: `<OUTPUT_DIR>/<topic>/`
- optional Mail.app draft email (macOS) with `.docx` attached

---

## Step 2 — First review pass (Quality + relevance)
Open the `.docx` and check:
- relevance: each clip matches the intent of the queries
- duplicates: repeated stories/URLs removed
- obvious misses: any critical outlet/story missing due to query design

If needed, adjust queries and re-run.

---

## Step 3 — Paywall/manual fill loop (Media Clip Cleaner)
In the `.docx`, locate any clip body that contains:
- `[PASTE FULL TEXT HERE]`

For each placeholder:
1) Open the article in browser (log in if needed).
2) Copy the article text (it may include clutter).
3) Paste into **Media Clip Cleaner** (Gem or ChatGPT).
4) Copy the cleaned output:
   - starts with *italic subtitle/lede*
   - no headline
   - no dates/credits/ads
   - clean full body paragraphs
5) Paste the cleaned text into the `.docx` replacing `[PASTE FULL TEXT HERE]`.

---

## Step 4 — Final review checklist (required before sending)
- no placeholders remain (`[PASTE FULL TEXT HERE]`)
- titles and sources look correct
- dates/authors are reasonable where included
- tone is consistent and professional
- confirm recipients (if sending)

---

## Step 5 — Send
- If Mail.app draft exists: open Mail → review → send  
- Otherwise: attach the `.docx` to your email client and send with your standard subject format:
  - `{topic} - {Month DD, YYYY}`

---

## Notes / iteration
- If the output is too long: tighten queries, shorten `period`, or later add a “digest mode” format.
- If you repeatedly see paywalls from certain outlets, consider maintaining an “expected manual fill list”.


