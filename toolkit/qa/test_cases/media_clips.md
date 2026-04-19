# Media Clips — Canonical Manual Cases

Use the web page at `/media-clips`.

## MC-SMK-01

- Tool: Media Clips
- Goal: Validate a standard daily clips run from search to downloadable report.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Report Topic / Title:
  `India Media Clips`
- Query Mode:
  `Advanced (Boolean)`
- Search Queries:
  `"India" AND ("elections" OR "BJP" OR "Modi")`
- Exclude Words / Phrases:
  `cricket, Bollywood`
- Search Period:
  `24h`
- Target Date:
  `2026-04-13`
- Source Filter:
  `Mainstream media only`
- Since Date:
  leave blank
- Email To:
  leave blank on first pass
- Email Sender:
  leave blank on first pass

### Optional setup / preconditions

- This case depends on current Google News availability.
- If no clips are returned, rerun once with `All sources` before logging a bug.

### What to verify

- Effective queries display correctly.
- Search returns clips or a sensible empty state.
- Final report build works.
- DOCX download works.
- No duplicate URLs appear in the index.
- Missing extraction text is clearly flagged for manual cleanup.

### Pass / fail rules

- Pass: clips list is usable, report builds, and download works.
- Fail: query handling is wrong, report build fails, or output is structurally broken.

### Known risks this case covers

- Boolean query handling
- dedupe
- report build path

### If it fails, log bug as

`Media Clips smoke run fails to build a usable report`

### Regression candidate

yes

## MC-EDGE-01

- Tool: Media Clips
- Goal: Validate extraction-failure cleanup and manual clip repair flow.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Reuse `MC-SMK-01` until a clip with missing full text appears.
- Select a clip that lacks full text.
- In the cleaner input, paste this sample article body:

```text
Subscription required

India trade negotiators said Monday they expect talks with U.S. counterparts to continue this month.

By Staff Reporter
Updated April 13, 2026 7:12 am ET

The discussions focus on tariff alignment, digital trade, and investment screening. Officials said both sides want to show progress before the next ministerial meeting.
```

- Cleaner mode:
  `llm`

### Optional setup / preconditions

- This case only applies if at least one clip needs cleanup.

### What to verify

- Cleaner output removes clutter and preserves the readable body.
- Rebuilt report uses the cleaned text.
- The clip is no longer marked as missing full text.
- The page does not corrupt other clips when one clip is cleaned.

### Pass / fail rules

- Pass: cleaned text is inserted into the chosen clip and rebuild succeeds.
- Fail: cleaner output is unusable, wrong clip updates, or rebuild fails after cleanup.

### Known risks this case covers

- clip cleaner integration
- clip state updates
- rebuild after manual repair

### If it fails, log bug as

`Media Clips cleaner flow corrupts or fails to repair missing clip text`

### Regression candidate

yes

## Regression placeholder

- Add the first confirmed media clips bug here after it is fixed.
