# Example 01 — Output (expected characteristics)

- Produces a reviewable clips set and a final .docx report under: `/path/to/output/India/`
- Report filename follows the current artifact convention: `media_clips_<mon><dd>.docx`
- Reviewed clip data is saved as JSON for downstream editing
- Report contains:
  - Title page (India + date)
  - Index with numbered items linking to source URLs
  - Full clips with source, linked title, author, date, optional subtitle/lede, and body text
- In the app workflow, article text and author can be edited manually before the final report build
- Creates plain-text and HTML email artifacts; Mail.app draft creation remains optional on macOS
