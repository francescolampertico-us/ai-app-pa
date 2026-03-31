"""
Media List Builder Generator
===============================
Two-step pipeline:
  Step 1 — GNews research: find real articles on the issue to extract journalists/outlets
  Step 2 — gpt-4o synthesis: expand the list, add pitch angles, fill gaps
"""

import os
import json
import sys
from pathlib import Path
from openai import OpenAI

try:
    from gnews import GNews
    HAS_GNEWS = True
except ImportError:
    HAS_GNEWS = False


MODEL = "gpt-4o"

MEDIA_TYPE_LABELS = {
    "mainstream": "Mainstream",
    "print": "Print",
    "broadcast": "Broadcast (TV/Radio)",
    "digital": "Digital / Online",
    "trade": "Trade / Policy",
    "podcast": "Podcast",
}


# ---------------------------------------------------------------------------
# Step 1: News research
# ---------------------------------------------------------------------------

def research_journalists(issue: str, location: str = "US",
                         max_results: int = 20) -> list[dict]:
    """Search Google News for recent articles on the issue to find active journalists."""
    if not HAS_GNEWS:
        print("  gnews not installed, skipping news research", file=sys.stderr)
        return []

    try:
        gn = GNews(language="en", country="US", period="180d", max_results=max_results)

        # Build location-aware query
        if location and location.upper() not in ("US", "USA", "NATIONAL"):
            query = f"{issue} {location}"
        else:
            query = issue

        articles = gn.get_news(query) or []

        results = []
        seen_titles = set()
        for a in articles:
            title = a.get("title", "")
            if title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())

            # GNews sometimes includes the source in the title after " - "
            source = a.get("publisher", {}).get("title", "Unknown")

            results.append({
                "title": title,
                "source": source,
                "url": a.get("url", ""),
                "date": a.get("published date", ""),
            })

        return results
    except Exception as e:
        print(f"  News research error: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Step 2: LLM synthesis
# ---------------------------------------------------------------------------

MEDIA_LIST_SYSTEM = """You are a senior public affairs media strategist building a targeted media pitch list.

Your job is to identify journalists, editors, and producers who cover the given policy issue
in the specified geographic area, and suggest a tailored pitch angle for each contact.

RULES:
- Use REAL journalist names you are confident about. For any name you are uncertain of, use
  a plausible name and mark the entire row with [VERIFY] in the Notes column.
- Outlets must be real, currently operating media organizations.
- Pitch angles should be SPECIFIC to the journalist's known interests, not generic.
- For email addresses, use the outlet's known email pattern (e.g., first.last@nytimes.com).
  If you don't know the pattern, use [RESEARCH NEEDED].
- Distribute contacts across the requested media types.
- The media_type field MUST use one of these exact values: "mainstream", "print", "broadcast", "digital", "trade", "podcast"
- Prioritize journalists who have recently covered the topic or related issues.
- For local/state requests, include a mix of local and national reporters who cover that region.

IMPORTANT: Use the provided news articles as evidence of active coverage. If a journalist's
name appears in an article byline, they are confirmed active on this beat.

Return a JSON object with this exact structure:
{
  "contacts": [
    {
      "first_name": "Jane",
      "last_name": "Smith",
      "outlet": "The Washington Post",
      "role": "Technology Policy Reporter",
      "media_type": "mainstream",
      "location": "Washington, DC",
      "pitch_angle": "Specific angle tied to their coverage interests",
      "previous_story_title": "Title of a relevant story they wrote (if known)",
      "previous_story_url": "URL if available, otherwise empty string",
      "email": "jane.smith@washpost.com or [RESEARCH NEEDED]",
      "notes": "Additional context about their coverage"
    }
  ],
  "pitch_timing": "Brief note on optimal timing for this pitch (2-3 sentences)"
}"""


def generate_media_list(issue: str, location: str = "US",
                        media_types: list[str] = None,
                        num_contacts: int = 20) -> dict:
    """
    Run the full media list pipeline.

    Returns:
        {
            "issue": str,
            "location": str,
            "media_types": list,
            "contacts": [{ ... }],
            "pitch_timing": str,
            "news_research": [{ ... }],
        }
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required.")

    client = OpenAI(api_key=api_key)
    media_types = media_types or list(MEDIA_TYPE_LABELS.keys())
    num_contacts = min(num_contacts, 40)

    # Step 1: Research
    print("Step 1: Researching journalists via Google News...", file=sys.stderr)
    articles = research_journalists(issue, location, max_results=20)
    print(f"  Found {len(articles)} relevant articles", file=sys.stderr)

    # Step 2: LLM synthesis
    print(f"Step 2: Generating media list ({num_contacts} contacts)...", file=sys.stderr)

    # Build prompt
    media_type_str = ", ".join(MEDIA_TYPE_LABELS.get(mt, mt) for mt in media_types)

    parts = [
        f"Build a targeted media pitch list for the following issue:",
        f"Issue: {issue}",
        f"Geographic scope: {location}",
        f"Media types to include: {media_type_str}",
        f"Target number of contacts: {num_contacts}",
    ]

    if articles:
        article_text = "\n".join(
            f"- [{a['date']}] \"{a['title']}\" — {a['source']}"
            for a in articles[:15]
        )
        parts.append(
            f"\n--- Recent articles on this issue (use these to identify active journalists) ---\n"
            f"{article_text}"
        )

    parts.append(
        f"\nGenerate exactly {num_contacts} contacts distributed across these media types: {media_type_str}. "
        f"Prioritize journalists who have demonstrated active coverage of this issue."
    )

    prompt = "\n".join(parts)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": MEDIA_LIST_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=6000,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    # Normalize media_type values to our canonical keys
    label_to_key = {}
    for key, label in MEDIA_TYPE_LABELS.items():
        label_to_key[key.lower()] = key
        label_to_key[label.lower()] = key

    contacts = result.get("contacts", [])
    for c in contacts:
        raw_type = c.get("media_type", "").lower().strip()
        c["media_type"] = label_to_key.get(raw_type, raw_type)

    # Filter by requested media types
    if media_types and set(media_types) != set(MEDIA_TYPE_LABELS.keys()):
        contacts = [c for c in contacts if c.get("media_type", "") in media_types]

    return {
        "issue": issue,
        "location": location,
        "media_types": media_types,
        "contacts": contacts,
        "pitch_timing": result.get("pitch_timing", ""),
        "news_research": articles[:10],
    }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def render_markdown(result: dict) -> str:
    """Render the media list as a markdown summary."""
    sections = []

    sections.append(f"# Media Pitch List")
    sections.append(f"**Issue:** {result['issue']}")
    sections.append(f"**Location:** {result['location']}")
    sections.append(f"**Total Contacts:** {len(result['contacts'])}")
    sections.append("")

    # Summary by media type
    type_counts = {}
    for c in result["contacts"]:
        mt = c.get("media_type", "other")
        type_counts[mt] = type_counts.get(mt, 0) + 1

    if type_counts:
        sections.append("## Coverage by Media Type")
        for mt, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            label = MEDIA_TYPE_LABELS.get(mt, mt)
            sections.append(f"- **{label}:** {count} contacts")
        sections.append("")

    # Pitch timing
    if result.get("pitch_timing"):
        sections.append("## Pitch Timing")
        sections.append(result["pitch_timing"])
        sections.append("")

    # Contact table
    sections.append("## Contacts")
    sections.append("")
    sections.append("| Name | Outlet | Role | Media Type | Pitch Angle |")
    sections.append("|------|--------|------|------------|-------------|")
    for c in result["contacts"]:
        name = f"{c.get('first_name', '')} {c.get('last_name', '')}"
        outlet = c.get("outlet", "")
        role = c.get("role", "")
        mt = MEDIA_TYPE_LABELS.get(c.get("media_type", ""), c.get("media_type", ""))
        angle = c.get("pitch_angle", "")[:80]
        sections.append(f"| {name} | {outlet} | {role} | {mt} | {angle} |")

    sections.append("")
    sections.append("---")
    sections.append("*CONFIDENTIAL — FOR INTERNAL USE ONLY*")

    return "\n".join(sections)
