# Media Clips

## Purpose
Generate a daily media monitoring report for a given **topic** by running a set of **Boolean Google News queries**, then producing:
1) a formatted **.docx** report (index + full clips), and  
2) a draft **email in Mail.app** with the report attached (macOS).

## When to use
- Daily / weekly monitoring for a country, company, policy theme, or stakeholder issue.
- When you want a consistent “clips” format ready to send internally.

## Inputs (Directive)
### Required
- `topic` — label used in the document and email subject (e.g., “India Media Clips”).
- `queries` — comma-separated Boolean queries.

### Optional
- `period` — e.g., `12h`, `24h`, `72h`, `7d`.  
  If not provided: defaults to **72h on Mondays**, otherwise **24h**.
- `since` — ignore articles published before a timestamp (`YYYY-MM-DD HH:MM`).
- `target_date` — override report date (`YYYY-MM-DD`).
- `suffix` — filename suffix (e.g., `Partial`).
- `output_dir` — base folder where a `/topic/` subfolder is created.
- `email_sender` — sender account for the Mail.app draft.
- `email_recipient` — recipients for the Mail.app draft.

## What the tool produces (Execution Output)
### Report (.docx)
The report includes:
- **Title page** (topic + date)
- **Index** (numbered list; each entry links to the source URL)
- **Clips section**, with for each article:
  - source name
  - title (as hyperlink)
  - author (if available)
  - date
  - subtitle/lede (if available)
  - full article body (when extraction succeeds)

If extraction fails (often due to paywalls), the body contains:
- `[PASTE FULL TEXT HERE]`

### Email draft (Mail.app, macOS)
- Creates a draft email in **Mail.app** with the `.docx` attached.
- Subject format: `{topic} - {Month DD, YYYY}`

If you are not on macOS or do not want the draft step, the `.docx` generation is still the primary artifact.

## Orchestration (where data comes from)
- Google News results from the provided Boolean queries.
- Source filtering: trusted sources allowed; blocked sources removed (configured in the execution script).
- Deduplication: repeated links are removed.

## Review requirements (Risk: Yellow)
This tool is intended for distribution, so human review is required before sending externally.

Checklist:
- Confirm each clip is relevant to the queries.
- Check for duplicates or missing high-salience stories.
- Replace any `[PASTE FULL TEXT HERE]` sections for paywalled articles.
- Verify names/titles/dates on any sensitive clip.
- Confirm recipients before sending the Mail draft.

## Known limitations / failure modes
- Paywalls often prevent full extraction.
- Google News can miss outlets or surface duplicates.
- Some pages return “cluttered” text extraction depending on the site structure.
- Author/date fields can be missing or inconsistent.

## Future extensions
- Parameterize geography beyond India (topic + query sets).
- Allow multiple output formats (short digest vs full clips).
- Add alternative email export (Gmail API / Outlook / plain .eml) for non-macOS.
