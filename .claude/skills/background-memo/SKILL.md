---
name: background-memo
description: Generate a structured background memo on any client, organization, policy issue, or individual. Produces a DOCX and markdown with Overview, Fast Facts, and user-defined sections.
allowed-tools: Read, Bash, Glob
---

# Background Memo Generator Skill

## Goal
Run the background memo generator for a given subject and set of section headings.
Produce a DOCX and markdown output. Always show the review warning before sharing output.

## Steps

1. **Gather inputs** — Confirm with the user:
   - `subject`: name of the client, organization, issue, or person
   - `sections`: list of section headings (one per line or comma-separated)
   - `context` (optional): background notes or angles to emphasize
   - `date` (optional): memo date string (default: today)
   - `out` (optional): output DOCX path

2. **Run the generator**
   ```bash
   cd toolkit
   python3 tools/background_memo_generator/execution/run.py \
     --subject "<subject>" \
     --sections "<Section 1>" "<Section 2>" "<Section 3>" \
     --context "<context>" \
     --out "output/<slug>_background_memo.docx"
   ```
   Replace `<slug>` with a snake_case version of the subject name.

3. **Review output** — Read the generated markdown and check:
   - All requested section headings are present
   - Fast Facts contain 4-6 bolded sentences
   - No obvious hallucinations in names, dates, or figures
   - Links point to plausible domains

4. **Present results** — Show the user:
   - The overview paragraph
   - Fast Facts list
   - Section headings with first sentence of each section
   - Path to the DOCX file

5. **Review warning** — Always include:
   > ⚠️ **Review required.** All facts are LLM-generated — verify against primary sources before distribution. Links should be checked individually.

## Output format rules
- Overview: single prose paragraph, ~100 words
- Fast Facts: 4-6 bullet sentences, each bold
- Sections: one heading per user-specified section, 1-3 paragraphs each
- Relevant Links: 4-6 entries as `label — URL`

## Error recovery
- If the LLM returns malformed JSON, re-run with a more specific `--context` that constrains scope
- If a section is empty, add context about what that section should cover and re-run
- If links are clearly fabricated (.org/.gov domains that don't exist), note them in the review checklist but do not re-run automatically — let the user verify

## Spec reference
`toolkit/tools/background_memo_generator/spec.md`
