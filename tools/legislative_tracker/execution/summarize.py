"""
Bill Summarizer
================
LLM-powered bill analysis using OpenAI.
Produces structured plain-language summaries with impact analysis and talking points.

Two-pass approach for long bills:
  Pass 1 — gpt-4o-mini extracts concrete facts from each chunk (cheap, reliable for extraction)
  Pass 2 — gpt-4o synthesizes extracted facts into the final structured summary (accurate, grounded)

Short bills (≤50K chars) go directly to gpt-4o in a single pass.
"""

import os
import json
from openai import OpenAI


DEFAULT_MODEL = "gpt-4o"
EXTRACTION_MODEL = "gpt-4o-mini"
# Bills under this threshold get single-pass summarization with gpt-4o.
# Above this, we use two-pass: gpt-4o-mini extraction → gpt-4o synthesis.
SINGLE_PASS_CHAR_LIMIT = 50_000
# Chunk size for pass-1 extraction (~12K tokens fits comfortably in mini's context)
EXTRACTION_CHUNK_CHARS = 50_000


SYSTEM_PROMPT = """You are a nonpartisan legislative analyst producing plain-language bill summaries for public affairs professionals. Your analysis must be:

- Accurate: only state what the bill text explicitly supports. Do NOT generalize or invent provisions.
- Specific: name the actual programs, agencies, dollar amounts, dates, and mechanisms in the bill.
- Balanced: present both sides fairly in talking points.
- Clear: avoid legal jargon; explain in plain English.
- Honest: explicitly flag what you cannot determine from the text provided.

CRITICAL RULES:
- Do NOT describe provisions that are not in the bill text. If the text is truncated, say so.
- Do NOT use generic phrases like "establishes a regulatory framework" or "promotes transparency" unless the bill specifically creates named regulations or transparency requirements.
- Anchor every claim to specific language, sections, or provisions in the bill.
- If the bill text is a pre-summary (marked with [Section X/Y]), synthesize those summaries faithfully — do not add information not present in them.

Output ONLY the markdown sections below. Do not add any other sections or commentary."""


SUMMARY_PROMPT_TEMPLATE = """Analyze the following bill and produce a structured summary.

## Bill Metadata
- **Number:** {number}
- **Title:** {title}
- **Description:** {description}
- **State:** {state}
- **Session:** {session}
- **Status:** {status}
- **Sponsors:** {sponsors}
- **Subjects:** {subjects}
- **Last Action:** {last_action} ({last_action_date})

## Bill Text
{bill_text}

---

Produce your analysis using EXACTLY these markdown sections:

### Plain-Language Summary
2-3 paragraphs explaining what this bill does in plain English. Be SPECIFIC — name the actual mechanisms, agencies, programs, or changes the bill creates. Who introduced it, what it changes, and why it matters. If the bill text was truncated, acknowledge this.

### Key Provisions
Bulleted list of the major provisions. Each bullet should reference a specific section or requirement from the bill. Do NOT invent provisions — only list what appears in the text.

### Potential Impact
Who is affected and how? Be specific about which industries, agencies, populations, or jurisdictions are named in the bill.

### Talking Points FOR
3-5 arguments that supporters would make. Ground these in the bill's actual provisions.

### Talking Points AGAINST
3-5 arguments that opponents would make. Ground these in the bill's actual provisions.

### Status & Next Steps
Where the bill stands in the legislative process and what is likely to happen next based on its current status and history.

### Assumptions & Unknowns
What this summary cannot determine: political dynamics, likelihood of passage, implementation details, fiscal impact if not stated in the bill. If the bill text was truncated or unavailable, note that here."""


EXTRACTION_PROMPT = """You are a legislative text analyst. Extract ALL concrete facts from this bill text section.

For each provision you find, extract:
- Section number/letter
- What it requires, creates, prohibits, or changes
- Named agencies, programs, offices, or entities
- Dollar amounts, percentages, or numerical thresholds
- Dates, deadlines, or timelines
- Definitions of key terms
- Penalties or enforcement mechanisms

Rules:
- ONLY extract what is explicitly stated in the text. Do NOT interpret or generalize.
- Use direct quotes for key phrases when possible.
- If a section is procedural (amendments to existing law by striking/inserting), note what is being changed.
- Be exhaustive — capture every substantive provision, no matter how minor.

Bill: {number} — {title}
This is section {chunk_num} of {total_chunks} of the bill text.

---
{chunk_text}
---

Output a structured extraction as markdown bullet points, grouped by section/title when possible."""


def summarize_bill(bill_detail: dict, bill_text: str, model: str = None) -> str:
    """
    Generate an AI summary of a bill.

    Short bills (≤50K chars): single-pass with gpt-4o.
    Long bills: two-pass — gpt-4o-mini extracts facts from chunks, gpt-4o synthesizes.

    Args:
        bill_detail: Normalized bill detail dict from LegiScanClient.get_bill().
        bill_text: Decoded full text of the bill.
        model: OpenAI model to use for synthesis (default: gpt-4o).

    Returns:
        Markdown string with the structured summary.
    """
    model = model or DEFAULT_MODEL
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for bill summarization.")

    client = OpenAI(api_key=api_key)

    # Format metadata
    sponsors_str = ", ".join(
        f"{s['name']} ({s['party']})" for s in bill_detail.get("sponsors", [])
    ) or "Not available"
    subjects_str = ", ".join(bill_detail.get("subjects", [])) or "Not specified"
    description = bill_detail.get("description", "") or "Not available"

    # Decide single-pass vs two-pass
    if len(bill_text) <= SINGLE_PASS_CHAR_LIMIT:
        synthesis_input = bill_text
    else:
        synthesis_input = _two_pass_extract(client, bill_detail, bill_text)

    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        number=bill_detail.get("number", "N/A"),
        title=bill_detail.get("title", "N/A"),
        description=description,
        state=bill_detail.get("state", "N/A"),
        session=bill_detail.get("session", "N/A"),
        status=bill_detail.get("status", "N/A"),
        sponsors=sponsors_str,
        subjects=subjects_str,
        last_action=bill_detail.get("last_action", "N/A"),
        last_action_date=bill_detail.get("last_action_date", "N/A"),
        bill_text=synthesis_input,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=4000,
    )

    return response.choices[0].message.content


def _chunk_bill_text(text: str, chunk_size: int) -> list[str]:
    """Split bill text into chunks, breaking at section boundaries when possible."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break

        # Try to break at a section boundary within the last 20% of the chunk
        search_start = start + int(chunk_size * 0.8)
        segment = text[search_start:end]
        for marker in ["\nSEC.", "\nSection", "\nTITLE", "\n\n"]:
            pos = segment.rfind(marker)
            if pos >= 0:
                end = search_start + pos
                break

        chunks.append(text[start:end])
        start = end

    return chunks


def _two_pass_extract(client: OpenAI, bill_detail: dict, bill_text: str) -> str:
    """
    Two-pass summarization for long bills.

    Pass 1: gpt-4o-mini extracts concrete facts from each chunk.
    Pass 2: Concatenated extractions become the input for the final gpt-4o synthesis.
    """
    chunks = _chunk_bill_text(bill_text, EXTRACTION_CHUNK_CHARS)
    total = len(chunks)
    number = bill_detail.get("number", "N/A")
    title = bill_detail.get("title", "N/A")

    extractions = []
    for i, chunk in enumerate(chunks, 1):
        prompt = EXTRACTION_PROMPT.format(
            number=number,
            title=title,
            chunk_num=i,
            total_chunks=total,
            chunk_text=chunk,
        )

        response = client.chat.completions.create(
            model=EXTRACTION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=3000,
        )

        extraction = response.choices[0].message.content
        extractions.append(f"[Section {i}/{total}]\n{extraction}")

    combined = "\n\n---\n\n".join(extractions)

    return (
        f"[NOTE: This bill is {len(bill_text):,} characters long. "
        f"The text below is a factual extraction from all {total} sections of the bill, "
        f"produced by a first-pass analysis. Synthesize these extractions into your summary. "
        f"Do NOT add information beyond what is stated in the extractions.]\n\n"
        f"{combined}"
    )


def format_bill_header(bill_detail: dict) -> str:
    """Generate the bill overview header for the report."""
    sponsors = bill_detail.get("sponsors", [])
    sponsor_lines = []
    for s in sponsors[:10]:
        line = f"  - {s['name']} ({s['party']})"
        if s.get("role"):
            line += f" — {s['role']}"
        sponsor_lines.append(line)
    if len(sponsors) > 10:
        sponsor_lines.append(f"  - ... and {len(sponsors) - 10} more")

    header = f"""## Bill Overview

- **Number:** {bill_detail.get('number', 'N/A')}
- **Title:** {bill_detail.get('title', 'N/A')}
- **State:** {bill_detail.get('state', 'N/A')}
- **Session:** {bill_detail.get('session', 'N/A')}
- **Status:** {bill_detail.get('status', 'N/A')} (as of {bill_detail.get('status_date', 'N/A')})
- **Last Action:** {bill_detail.get('last_action', 'N/A')} ({bill_detail.get('last_action_date', 'N/A')})
- **Official URL:** {bill_detail.get('state_url', bill_detail.get('url', 'N/A'))}
- **Sponsors:**
{chr(10).join(sponsor_lines) if sponsor_lines else '  - Not available'}
- **Subjects:** {', '.join(bill_detail.get('subjects', [])) or 'Not specified'}"""

    return header
