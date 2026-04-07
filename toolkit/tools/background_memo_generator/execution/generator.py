"""
Background Memo Generator
==========================
Two-stage pipeline:
  1. Optional: pull LDA/FARA/IRS 990 disclosure data for the subject
  2. LLM call (gpt-4.1) to produce a fully structured background memo

Output structure:
  - Header (DATE, SUBJECT)
  - Overview paragraph (memo scope description)
  - Fast Facts (4-6 bolded bullet sentences)
  - One content section per user-defined heading
  - Relevant Links (4-6 verified reference URLs)
"""

import os
import json
import sys
from datetime import date
from openai import OpenAI

MODEL = "gpt-4.1"

SYSTEM_PROMPT = """You are a senior public affairs research analyst writing professional background memos
for pre-meeting preparation, congressional briefings, and strategy sessions.

OVERVIEW RULES:
- The Overview is a meta-description of the memo, not a subject summary.
- Use this exact formula:
  "This memorandum provides background information on [Subject]. It begins with fast facts,
   followed by detailed sections on [list the section headings in plain English, lowercase, comma-separated]."
- If context restricts scope (e.g., "and its U.S. operations"), acknowledge that in the first sentence.
- Keep it to 2-3 sentences max.

WRITING STYLE:
- Dense, precise, professional. Never vague.
- Use full job titles on first reference: "Chief Executive Officer, Chairman, and Co-Founder"
- Specific numbers: "$2.23 billion" not "multi-billion"; "14,000 employees" not "thousands"
- Specific dates: "founded in 1995" not "founded decades ago"; "as of Q1 2026" where currency matters
- Attribute claims: "CSG reports..." / "According to the company's 2025 results..."
- Short paragraphs: 3-6 sentences. No walls of text.
- No marketing language, no adjectives that aren't backed by facts ("leading", "innovative", "premier")
- No opinions, predictions, or recommendations
- Third-person throughout
- Never mention any consulting firm, PA firm, or intermediary preparing this memo

FAST FACTS RULES:
- 4-6 bullet points
- Each bullet is one complete sentence stating the most important fact for that dimension
- Cover diverse dimensions: founding/origin, scale/size, key figures, policy relevance, U.S. angle,
  financial scale, or controversy — whichever are most relevant
- If the subject is a person, focus on: current role, prior roles, policy positions, affiliations
- Example format: "CSG is a Czech industrial-technological holding company that manages over 100
  companies and employs more than 14,000 people worldwide."

SECTION RULES:
- Write 2-4 paragraphs per section (3-6 sentences each)
- Use sub-sections (with headings) when a section has genuinely distinct components —
  e.g., "Corporate Overview" might have "Corporate Structure" and "Financial Scale" sub-headings
- Do NOT force sub-sections; use them only when they clarify structure
- If a section covers a person: role, background, career trajectory, key positions, affiliations, relevance
- If a section covers a company or org: structure, scale, activities, key stakeholders, current status
- If a section covers a policy issue: what it is, regulatory actors, current legislative status,
  industry/stakeholder positions

DISCLOSURE SECTION RULES (apply only when disclosure data is provided):
- If the disclosure data contains filings (LDA, FARA, or IRS 990), append one additional section
  AFTER the user-specified sections. Title it based on content:
    • "U.S. Lobbying Activity" — if only LDA filings with U.S. lobbying spend
    • "FARA Registration" — if only foreign agent activity
    • "U.S. Lobbying and Advisory Work" — if both LDA + FARA are present
    • "Lobbying and Disclosure Activity" — if mixed or unclear
- Write 1-3 paragraphs in the same memo prose style:
    • Named the lobbying firm hired and its registration date
    • Report exact dollar amounts ("$90,000 in lobbying expenditures")
    • Name specific government targets (agencies, committees, chambers)
    • Name the issues lobbied (use the filing's issue area descriptions)
    • If FARA: note the foreign principal relationship and registration date
    • If IRS 990: note revenue, assets, and mission description if relevant
- Use attribution language: "Official disclosures report...", "According to LDA filings...",
  "FARA registration documents indicate..."
- If the disclosure data contains NO filings, do NOT add this section.

LINKS RULES:
- 4-6 links only
- Only include URLs you are highly confident exist:
  • Official organization/company websites (e.g., company.com/about)
  • Wikipedia articles (en.wikipedia.org/wiki/...)
  • Government databases: lda.gov, efts.fara.gov, SEC EDGAR (sec.gov/cgi-bin/...)
  • Major reference profiles: LinkedIn company pages, GLOBSEC, Atlantic Council, think-tank bios
  • Major news sources for specific documented articles (FT, Reuters, WSJ, NYT, Politico)
- If you are not confident the exact URL exists, use the domain only (e.g., https://company.com)
  rather than fabricating a path
- Labels should describe the content: "CSG 2024 Annual Report" not "Annual Report"

Return a JSON object with this exact structure:
{
  "overview": "This memorandum provides background information on [Subject]. It begins with fast facts, followed by detailed sections on [section names].",
  "fast_facts": [
    "Complete sentence stating fact 1.",
    "Complete sentence stating fact 2.",
    "Complete sentence stating fact 3.",
    "Complete sentence stating fact 4."
  ],
  "sections": [
    {
      "heading": "Section Heading",
      "subsections": [
        {
          "heading": null,
          "paragraphs": ["Paragraph 1.", "Paragraph 2."]
        }
      ]
    }
  ],
  "links": [
    {"label": "Official website", "url": "https://example.com"},
    {"label": "Wikipedia — Example Organization", "url": "https://en.wikipedia.org/wiki/Example_Organization"}
  ]
}

For sections with no sub-division needed, use a single subsection with heading: null.
For sections that benefit from sub-headings, use multiple subsections each with a heading string.
"""


def generate_memo(
    subject: str,
    sections: list,
    context: str = "",
    disclosure_context: str = "",
    research_context: str = "",
) -> dict:
    """
    Generate a full background memo via gpt-4.1.

    Args:
        subject:            The name of the client, organization, issue, or person.
        sections:           List of section heading strings (user-defined).
        context:            Optional additional context to guide the LLM.
        disclosure_context: Pre-fetched LDA/FARA/IRS 990 markdown from the disclosure tracker.
        research_context:   Pre-fetched article text from web research step.

    Returns:
        dict with keys: subject, sections_requested, overview, fast_facts, sections, links
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required.")

    client = OpenAI(api_key=api_key)

    sections_list = "\n".join(f"- {s}" for s in sections)

    user_prompt = (
        f"Subject: {subject}\n\n"
        f"Generate a background memo with the following sections (in this order):\n"
        f"{sections_list}\n"
    )
    if context:
        user_prompt += f"\nAdditional context:\n{context}\n"

    if research_context:
        user_prompt += (
            f"\n---\n{research_context[:10000]}\n---\n"
        )

    if disclosure_context:
        user_prompt += (
            f"\n---\nDISCLOSURE DATA (LDA/FARA/IRS 990 filings from official U.S. databases):\n"
            f"{disclosure_context[:8000]}\n"
            "Follow the DISCLOSURE SECTION RULES in the system prompt: if filings are present, "
            "append a dedicated prose section after the user-specified sections. "
            "If no filings are found in the data, do not add the section.\n---\n"
        )

    user_prompt += (
        "\nReturn a JSON object following the structure in the system prompt exactly. "
        "Use the section headings exactly as provided above."
    )

    print(f"Generating background memo for: {subject}", file=sys.stderr)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=5000,
        response_format={"type": "json_object"},
    )

    raw = json.loads(response.choices[0].message.content)

    return {
        "subject": subject,
        "sections_requested": sections,
        "overview": raw.get("overview", ""),
        "fast_facts": raw.get("fast_facts", []),
        "sections": raw.get("sections", []),
        "links": raw.get("links", []),
    }


def render_markdown(result: dict, memo_date: str = "") -> str:
    """Render the memo as plain markdown."""
    lines = []
    d = memo_date or date.today().strftime("%B %d, %Y")

    lines.append(f"**DATE:** {d}")
    lines.append(f"**SUBJECT:** {result['subject']} Background Memo")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(result["overview"])
    lines.append("")
    lines.append("## Fast Facts")
    lines.append("")
    for fact in result["fast_facts"]:
        lines.append(f"- **{fact}**")
    lines.append("")

    for section in result["sections"]:
        lines.append(f"## {section['heading']}")
        lines.append("")
        for sub in section.get("subsections", []):
            if sub.get("heading"):
                lines.append(f"**{sub['heading']}**")
                lines.append("")
            for para in sub.get("paragraphs", []):
                lines.append(para)
                lines.append("")

    lines.append("## Links")
    lines.append("")
    for link in result["links"]:
        lines.append(f"- [{link['label']}]({link['url']})")
    lines.append("")
    lines.append("---")
    lines.append("*FOR INTERNAL USE ONLY — Verify all facts before distribution.*")

    return "\n".join(lines)
