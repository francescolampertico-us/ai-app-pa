# Background Memo Generator — Spec

## When to use
Use this tool to quickly produce a professional background memo on any subject:
a client, organization, policy issue, government program, or individual. The user
provides the subject name and the section headings they want; the tool fills all
content via LLM.

## Output structure (fixed)
Every memo follows this exact structure:

1. **Header** — DATE and SUBJECT lines
2. **Overview** — one prose paragraph summarizing the memo scope
3. **Fast Facts** — 4-6 bolded bullet sentences with the most important facts
4. **User-defined sections** — one section per heading provided, with optional sub-sections
5. **Relevant Links** — 4-6 suggested reference URLs

## Failure modes
- LLM may hallucinate facts, figures, or URLs — always verify before distribution
- For obscure subjects the LLM has little training data on, output quality drops sharply;
  use the `context` input to supply background notes
- Links section should be treated as starting points for research, not verified sources

## Review checklist
- [ ] All facts in Fast Facts verified against primary sources
- [ ] No confidential client information in the document (check Overview and sections)
- [ ] Links open and point to relevant content
- [ ] Section headings match the user's intent
- [ ] Date is correct
