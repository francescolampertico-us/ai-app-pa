# Media Clip Cleaner — Canonical Manual Cases

Use the standalone cleaner inside `/media-clips`.

## MCC-SMK-01

- Tool: Media Clip Cleaner
- Goal: Validate the standalone cleaner on a normal pasted article.
- Priority: P0
- Scenario type: smoke

### Exact app inputs

- Cleaning Mode:
  `LLM (recommended)`
- Paste Raw Article Text:

```text
Subscription required

India trade negotiators said Monday they expect talks with U.S. counterparts to continue this month.

By Staff Reporter
Updated April 13, 2026 7:12 am ET

The discussions focus on tariff alignment, digital trade, and investment screening. Officials said both sides want to show progress before the next ministerial meeting.
```

### What to verify

- Cleaner output removes clutter and metadata.
- The readable body remains intact.
- Copy-to-clipboard action appears after success.

### Pass / fail rules

- Pass: cleaned text is concise, readable, and keeps the article body.
- Fail: the cleaner leaves obvious boilerplate or strips out the main content.

### Regression candidate

yes

## MCC-EDGE-01

- Tool: Media Clip Cleaner
- Goal: Check local rule-based cleaning and empty-input guard behavior.
- Priority: P1
- Scenario type: edge

### Exact app inputs

- Cleaning Mode:
  `Local (rule-based)`
- Paste Raw Article Text:
  first leave blank, then reuse the smoke input

### What to verify

- The run button stays disabled on empty input.
- Local mode still produces readable text on the same article.
- The standalone and embedded cleaner modes behave consistently enough to be usable.

### Pass / fail rules

- Pass: empty-input guard works and local mode remains usable.
- Fail: blank input still runs, or local mode returns unusable output.

### Regression candidate

yes
