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
from pathlib import Path
from openai import OpenAI

# Schema is in the same directory; add it to path for importability both via CLI and FastAPI.
sys.path.insert(0, str(Path(__file__).parent))
from schema import BackgroundMemoResult  # noqa: E402

MODEL = "ChangeAgent"

def _active_model(default: str) -> str:
    import os
    return os.environ.get("LLM_MODEL_OVERRIDE") or default

def _response_format_kwarg() -> dict:
    import os
    if os.environ.get("LLM_MODEL_OVERRIDE"):
        return {}
    return {"response_format": {"type": "json_object"}}

def _max_tokens_kwarg(default: int) -> dict:
    import os
    if os.environ.get("LLM_MODEL_OVERRIDE"):
        return {}
    return {"max_tokens": default}

def _parse_json_content(content: "str | None") -> dict:
    import re
    if not content:
        return {}
    text = content.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if m:
        text = m.group(1).strip()
    # Try full parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Repair truncated JSON: trim to last complete closing brace
    last = text.rfind("}")
    if last != -1:
        try:
            return json.loads(text[: last + 1])
        except json.JSONDecodeError:
            pass
    return {}

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
- Distinguish hard facts from interpretation. If a sentence goes beyond a directly sourced fact, signal it with phrasing like "This suggests..." or "This may indicate..."
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

RESEARCH SYNTHESIS RULES (apply when research articles are provided):
- Research articles are raw material — not a script. The memo is not a recap of them.
- Synthesize across the full article set to build a complete picture of the subject.
- Priority order for what to surface: mission/purpose → structure and scale → key figures
  → policy relevance → U.S./international angle → funding → controversies → recent news.
- Recent news should fill in current status, not define the entire framing of a section.
- If the same event appears in multiple articles, treat it as a single data point — one
  supporting sentence at most.
- Never include operational minutiae: logistical disruptions, scheduling notes, venue
  changes, and event-management details have no place in a strategic background memo.
- If articles are thin or repetitive, rely on the subject's documented background,
  structure, and policy footprint, and flag currency limits with "as of [date]" language.

DISCLOSURE DATA RULES (apply only when disclosure data is provided):
- Use disclosure data (LDA, FARA, IRS 990) solely to enrich the content of the user-specified sections.
- Do NOT add any new top-level section that the user did not request, regardless of what filings are present.
- Weave disclosure facts naturally into whichever user-requested section is most relevant
  (e.g., lobbying spend into "Funding and Membership", foreign agent relationships into
  "U.S. and NATO Relations", revenue/assets into "Overview of Activities").
- Use attribution language: "Official disclosures report...", "According to LDA filings...",
  "FARA registration documents indicate..."
- Report exact figures: dollar amounts, registration dates, named firms, government targets, issue areas.
- If sources conflict or the record is incomplete, preserve that nuance rather than smoothing it over.
- The overview must list only the sections the user requested — never mention disclosure-derived sections.

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
    suppress_disclosures: bool = False,
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
        raise ValueError("OPENAI_API_KEY is required. Check that toolkit/.env is set and loaded.")

    client = OpenAI(api_key=api_key, timeout=120)

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
            f"\n---\n{research_context[:24000]}\n---\n"
        )

    if disclosure_context:
        user_prompt += (
            f"\n---\nDISCLOSURE DATA (LDA/FARA/IRS 990 filings from official U.S. databases):\n"
            f"{disclosure_context[:8000]}\n"
            "Use this data to enrich the content of the user-specified sections only. "
            "Do NOT add any new top-level section. The memo must contain exactly the sections listed above.\n---\n"
        )
    elif suppress_disclosures:
        user_prompt += (
            "\nDo not mention lobbying disclosures, LDA filings, FARA registrations, or IRS 990 filings "
            "in any form. Do not note their absence or presence.\n"
        )

    user_prompt += (
        "\nReturn a JSON object following the structure in the system prompt exactly. "
        "Use the section headings exactly as provided above."
    )

    print(f"Generating background memo for: {subject}", file=sys.stderr)
    response = client.chat.completions.create(
        model=_active_model(MODEL),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        **_max_tokens_kwarg(5000),
        **_response_format_kwarg(),
    )

    raw = _parse_json_content(response.choices[0].message.content)

    # Validate through the typed contract — catches malformed LLM output early.
    validated = BackgroundMemoResult(
        subject=subject,
        sections_requested=sections,
        overview=raw.get("overview", ""),
        fast_facts=raw.get("fast_facts", []),
        sections=raw.get("sections", []),
        links=raw.get("links", []),
    )
    return validated.model_dump()


def render_markdown(result: "BackgroundMemoResult | dict", memo_date: str = "") -> str:
    """Render the memo as plain markdown.

    Accepts either a BackgroundMemoResult model or a plain dict (e.g. from model_dump()).
    Normalizes to BackgroundMemoResult so internal access is always typed.
    """
    if isinstance(result, dict):
        result = BackgroundMemoResult(**result)

    lines = []
    d = memo_date or date.today().strftime("%B %d, %Y")

    lines.append(f"**DATE:** {d}")
    lines.append(f"**SUBJECT:** {result.subject} Background Memo")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(result.overview)
    lines.append("")
    lines.append("## Fast Facts")
    lines.append("")
    for fact in result.fast_facts:
        lines.append(f"- **{fact}**")
    lines.append("")

    for section in result.sections:
        lines.append(f"## {section.heading}")
        lines.append("")
        for sub in section.subsections:
            if sub.heading:
                lines.append(f"**{sub.heading}**")
                lines.append("")
            for para in sub.paragraphs:
                lines.append(para)
                lines.append("")

    lines.append("## Links")
    lines.append("")
    for link in result.links:
        lines.append(f"- [{link.label}]({link.url})")
    lines.append("")
    lines.append("---")
    lines.append("*FOR INTERNAL USE ONLY — Verify all facts before distribution.*")

    return "\n".join(lines)
