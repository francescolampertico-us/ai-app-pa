"""
Background Memo Generator
==========================
Single LLM call (gpt-4o) that produces a fully structured background memo.

Output structure:
  - Overview paragraph (1-2 sentences)
  - Fast Facts (4-6 bolded bullet sentences)
  - One content section per user-defined heading
  - Relevant Links (4-6 URLs)
"""

import os
import json
import sys
from datetime import date
from openai import OpenAI

MODEL = "gpt-4o"

SYSTEM_PROMPT = """You are a senior public affairs research analyst producing professional background memos.

Your memos are used by PA professionals before client meetings, congressional briefings,
and strategy sessions. Every sentence must be factual, specific, and verifiable.

STYLE RULES:
- Professional, neutral, third-person prose
- Short paragraphs (3-6 sentences). No walls of text.
- No marketing language, no opinions, no predictions
- Numbers and dates are specific: "$2.3 billion" not "billions"; "established in 1994" not "founded decades ago"
- Section content covers what a PA professional needs to know: history, structure, key people,
  policy positions, controversies, U.S. presence, financial scale — whatever is relevant to that section heading
- Never mention any consulting firm, PA firm, or intermediary preparing this memo

FAST FACTS RULES:
- Exactly 4-6 bullet points
- Each bullet is one complete, bolded sentence stating the single most important fact about that aspect
- Facts should be diverse: cover founding/origin, scale/size, key figures, policy relevance, U.S. angle
- Example format: "Jagello 2000 is a Czech non-governmental think tank founded in 2000 to promote
  Czech integration into NATO and transatlantic security structures."

SECTION RULES:
- Write 1-3 paragraphs per section (3-6 sentences each)
- If a section covers a person, include: role, background, key positions, relevance
- If a section covers a topic/program, include: what it is, how it works, key stakeholders, current status
- Sub-sections are allowed when the heading warrants it (e.g., "U.S. Presence" → "Operations" + "Partnerships")
  but only add them if they genuinely add structure — do not force them

LINKS RULES:
- 4-6 links maximum
- Only suggest URLs you are confident exist (official websites, Wikipedia, major news sources,
  government databases). If uncertain, omit rather than fabricate.
- Format: descriptive label + URL

Return a JSON object with this exact structure:
{
  "overview": "One to two sentence summary of what this memo covers and why it is relevant.",
  "fast_facts": [
    "Complete bolded sentence stating fact 1.",
    "Complete bolded sentence stating fact 2.",
    "Complete bolded sentence stating fact 3.",
    "Complete bolded sentence stating fact 4."
  ],
  "sections": [
    {
      "heading": "Section Heading",
      "subsections": [
        {
          "heading": null,
          "paragraphs": ["Paragraph 1 text.", "Paragraph 2 text."]
        }
      ]
    }
  ],
  "links": [
    {"label": "Official website", "url": "https://example.com"},
    {"label": "Wikipedia entry", "url": "https://en.wikipedia.org/wiki/..."}
  ]
}

For sections with no sub-division needed, use a single subsection with heading: null.
For sections that benefit from sub-headings, use multiple subsections each with a heading string.
"""


def generate_memo(
    subject: str,
    sections: list[str],
    context: str = "",
) -> dict:
    """
    Generate a full background memo via gpt-4o.

    Args:
        subject:  The name of the client, organization, issue, or person.
        sections: List of section heading strings (user-defined).
        context:  Optional additional context to guide the LLM.

    Returns:
        dict with keys: subject, sections_requested, overview, fast_facts,
                        sections, links
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
        temperature=0.3,
        max_tokens=4000,
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
    """Render the memo as markdown."""
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
                lines.append(f"### {sub['heading']}")
                lines.append("")
            for para in sub.get("paragraphs", []):
                lines.append(para)
                lines.append("")

    lines.append("## Relevant Links")
    lines.append("")
    for link in result["links"]:
        lines.append(f"- [{link['label']}]({link['url']})")
    lines.append("")
    lines.append("---")
    lines.append("*CONFIDENTIAL — FOR INTERNAL USE ONLY*")

    return "\n".join(lines)
