"""
composer.py — Stage 3: Compose Mercury-style memo from a structured HearingRecord.

Follows STYLE_GUIDE.md and prompts/compose_memo.md exactly.
Output conforms to schema/memo_output.schema.json.
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Any

from .config import (
    HEADING_HEARING_OVERVIEW,
    HEADING_OPENING_STATEMENTS,
    HEADING_OPENING_COCHAIRS,
    HEADING_WITNESS_SECTION,
    HEADING_QA,
    DEFAULT_CONFIDENTIALITY_FOOTER,
    WORD_TARGETS,
    PROSE_SHORT_PREFIXES,
)


# ---------------------------------------------------------------------------
# Speaker label helpers (STYLE_GUIDE §§10-12)
# ---------------------------------------------------------------------------

def _short_form(full_label: str) -> str:
    """Convert a full speaker label to short prose form.

    Examples:
        "Chairman Rick Scott (R-FL)" -> "Chairman Scott"
        "Ranking Member Kirsten Gillibrand (D-NY)" -> "Ranking Member Gillibrand"
        "Senator Tommy Tuberville (R-AL)" -> "Sen. Tuberville"
        "Honorable Ted Yoho" -> "Hon. Yoho"
        "Mr. Gordon G. Chang" -> "Mr. Chang"
    """
    # Strip party/state
    clean = re.sub(r"\s*\([RD]-[A-Za-z.]+\)\s*$", "", full_label).strip()

    # Map common title patterns
    mappings = [
        (r"^Chairman\s+(.+)", lambda m: f"Chairman {m.group(1).split()[-1]}"),
        (r"^Chairwoman\s+(.+)", lambda m: f"Chairwoman {m.group(1).split()[-1]}"),
        (r"^Ranking Member\s+(.+)", lambda m: f"Ranking Member {m.group(1).split()[-1]}"),
        (r"^Full Committee Ranking Member\s+(.+)", lambda m: f"Ranking Member {m.group(1).split()[-1]}"),
        (r"^Senator\s+(.+)", lambda m: f"Sen. {m.group(1).split()[-1]}"),
        (r"^Sen\.\s+(.+)", lambda m: f"Sen. {m.group(1).split()[-1]}"),
        (r"^Representative\s+(.+)", lambda m: f"Rep. {m.group(1).split()[-1]}"),
        (r"^Rep\.\s+(.+)", lambda m: f"Rep. {m.group(1).split()[-1]}"),
        (r"^Commissioner\s+(.+)", lambda m: f"Commissioner {m.group(1).split()[-1]}"),
        (r"^Honorable\s+(.+)", lambda m: f"Hon. {m.group(1).split()[-1]}"),
        (r"^Hon\.\s+(.+)", lambda m: f"Hon. {m.group(1).split()[-1]}"),
        (r"^Mr\.\s+(.+)", lambda m: f"Mr. {m.group(1).split()[-1]}"),
        (r"^Ms\.\s+(.+)", lambda m: f"Ms. {m.group(1).split()[-1]}"),
        (r"^Dr\.\s+(.+)", lambda m: f"Dr. {m.group(1).split()[-1]}"),
    ]

    for pattern, formatter in mappings:
        match = re.match(pattern, clean)
        if match:
            return formatter(match)

    # Fallback: use last name
    parts = clean.split()
    return parts[-1] if parts else clean


def _format_heading(full_label: str) -> str:
    """Format a speaker heading per STYLE_GUIDE exact preferences.
    
    Examples:
        "Sen. Tommy Tuberville (R-Ala.)" -> "Senator Tommy Tuberville (R-AL)"
        "Rep. Rich McCormick (R-Ga.)" -> "Representative Rich McCormick (R-GA)"
    """
    heading = full_label

    # Expand common titles
    heading = re.sub(r"^Sen\.\s+", "Senator ", heading)
    heading = re.sub(r"^Rep\.\s+", "Representative ", heading)
    
    # Capitalize the state abbreviations and remove periods (e.g., "(R-Fla.)" to "(R-FL)")
    def state_fix(match):
        party = match.group(1)
        state_abbr = match.group(2).replace('.', '').upper()
        # Map common shortened states to 2 letters if needed, but just upper() + take first 2 usually works for Florida (FL), Alabama (AL), NY (NY)
        if state_abbr == "FLA": state_abbr = "FL"
        if state_abbr == "ALA": state_abbr = "AL"
        if state_abbr == "GA": state_abbr = "GA"
        # Most states match first 2 letters if we strip to 2, but let's just do a basic map for the most common weird ones
        state_map = {"FLA": "FL", "ALA": "AL", "MICH": "MI", "TENN": "TN", "WASH": "WA", "WIS": "WI", "PENN": "PA"}
        state_abbr = state_map.get(state_abbr, state_abbr[:2])
        return f"({party}-{state_abbr})"

    heading = re.sub(r"\(([RD])-([A-Za-z.]+)\)", state_fix, heading)
    
    return heading


def _compose_prose_paragraph(points: List[str], speaker_short: str,
                              max_sentences: int = 4) -> str:
    """Compose a memo paragraph from summary points.

    Rules (STYLE_GUIDE §§8, 13):
    - 2 to 4 sentences per paragraph
    - Use preferred sentence-level moves
    - Professional, neutral tone
    - Third person
    """
    if not points:
        return ""

    sentences = []
    for pt in points[:max_sentences]:
        # Clean up the point
        pt = pt.strip()
        if not pt:
            continue
        # Ensure it ends with punctuation
        if not pt.endswith((".", "!", "?")):
            pt += "."
        sentences.append(pt)

    return " ".join(sentences)


def _word_count(text: str) -> int:
    """Count words in a text string."""
    return len(text.split())


# ---------------------------------------------------------------------------
# Section composers
# ---------------------------------------------------------------------------

def _compose_overview(record: dict) -> dict:
    """Compose the Hearing Overview section.

    Rules (STYLE_GUIDE §9):
    - One paragraph only
    - 4 to 5 sentences, 110–170 words
    - Name committee, hearing title, date, time
    - Summarize issues at high level
    - Do NOT mention individual speakers
    """
    meta = record["metadata"]
    overview_points = record.get("overview_points", [])

    # Build the overview paragraph
    parts = []

    # Opening sentence: committee + hearing context
    committee = meta.get("committee_name", "The committee")
    title = meta.get("hearing_title", "the hearing")
    date = meta.get("hearing_date", "")
    time = meta.get("hearing_time", "")

    opening = f'The {committee} held a hearing titled "{title}"'
    if date:
        opening += f" on {date}"
    if time:
        opening += f" at {time}"
    opening += "."
    parts.append(opening)

    # Add thematic points from the overview_points
    for pt in overview_points[1:]:  # Skip first (already covered by opening)
        pt = pt.strip()
        if not pt.endswith("."):
            pt += "."
        parts.append(pt)

    # Add generic thematic sentences if needed
    witnesses = record.get("witnesses", [])
    if witnesses:
        witness_count = len(witnesses)
        parts.append(
            f"The committee heard testimony from {witness_count} witness{'es' if witness_count > 1 else ''} "
            f"offering perspectives on the issues under examination."
        )

    qa = record.get("qa_clusters", [])
    if qa:
        parts.append(
            "Members engaged witnesses on policy implications, legislative responses, "
            "and areas requiring further oversight."
        )

    paragraph = " ".join(parts)

    return {
        "heading": HEADING_HEARING_OVERVIEW,
        "body": paragraph,
        "subsections": [],
    }


def _compose_opening_statements(record: dict) -> dict:
    """Compose the Committee Leadership Opening Statements section.

    Rules (STYLE_GUIDE §10):
    - One subheading per leadership speaker
    - Full role/title style in headings
    - Short forms in body text
    - 90–180 words per speaker
    """
    opening_heading = record["structure"]["opening_heading"]
    statements = record.get("opening_statements", [])

    subsections = []
    for stmt in statements:
        speaker_heading = stmt["speaker"]
        speaker_short = _short_form(speaker_heading)
        points = stmt["summary_points"]

        # Build 1-2 paragraphs
        if len(points) <= 3:
            body = _compose_prose_paragraph(points, speaker_short)
        else:
            # Split into two paragraphs for readability
            mid = len(points) // 2
            para1 = _compose_prose_paragraph(points[:mid], speaker_short)
            para2 = _compose_prose_paragraph(points[mid:], speaker_short)
            body = f"{para1}\n\n{para2}"

        subsections.append({
            "heading": _format_heading(speaker_heading),
            "body": body,
            "speaker_type": "leadership_member",
        })

    return {
        "heading": opening_heading,
        "body": "",
        "subsections": subsections,
    }


def _compose_witnesses(record: dict) -> dict:
    """Compose the Witnesses Introductions and Testimonies section.

    Rules (STYLE_GUIDE §11):
    - One subsection per witness
    - Heading: Honorific + Name, Affiliation
    - 90–180 words per witness
    """
    witnesses = record.get("witnesses", [])

    subsections = []
    for w in witnesses:
        # Build heading: Name, Affiliation
        heading = w["name"]
        if w.get("affiliation"):
            heading = f"{w['name']}, {w['affiliation']}"

        points = w["summary_points"]

        # Build 1-2 paragraphs
        speaker_short = _short_form(w["name"])
        if len(points) <= 3:
            body = _compose_prose_paragraph(points, speaker_short)
        else:
            mid = len(points) // 2
            para1 = _compose_prose_paragraph(points[:mid], speaker_short)
            para2 = _compose_prose_paragraph(points[mid:], speaker_short)
            body = f"{para1}\n\n{para2}"

        subsections.append({
            "heading": heading,
            "body": body,
            "speaker_type": "witness",
        })

    return {
        "heading": HEADING_WITNESS_SECTION,
        "body": "",
        "subsections": subsections,
    }


def _compose_qa(record: dict) -> dict:
    """Compose the Q&A section.

    Rules (STYLE_GUIDE §12):
    - Organized by member, not by issue cluster
    - One subsection per member
    - 70–180 words per member
    - Chair closing folded into chair's subsection
    """
    qa_clusters = record.get("qa_clusters", [])
    chair_closing = record.get("chair_closing_summary", "")

    subsections = []
    for qa in qa_clusters:
        member_heading = qa["member"]
        speaker_short = _short_form(member_heading)
        summary = qa["summary"]

        # Clean up the summary text into memo prose
        body = summary.strip()
        if not body.endswith("."):
            body += "."

        subsections.append({
            "heading": _format_heading(member_heading),
            "body": body,
            "speaker_type": "qa_member",
        })

    # Fold chair closing into the chair's subsection if present
    if chair_closing:
        # Find the chair's subsection
        for sub in subsections:
            if "chairman" in sub["heading"].lower() or "chairwoman" in sub["heading"].lower():
                sub["body"] += f"\n\n{chair_closing}"
                break
        else:
            # If no chair subsection found, add as last
            if subsections:
                subsections[-1]["body"] += f"\n\n{chair_closing}"

    return {
        "heading": HEADING_QA,
        "body": "",
        "subsections": subsections,
    }


# ---------------------------------------------------------------------------
# Metadata block composer
# ---------------------------------------------------------------------------

def _compose_metadata_block(record: dict, overrides: dict) -> dict:
    """Compose the FROM / DATE / SUBJECT block.

    Rules (STYLE_GUIDE §5):
    - Exactly three metadata lines
    - Labels are all caps followed by colon
    - Long-form SUBJECT line
    """
    meta = record["metadata"]

    memo_from = overrides.get("memo_from") or "Mercury"
    memo_date = overrides.get("memo_date") or meta.get("memo_date")
    if not memo_date:
        # Default to today
        memo_date = datetime.now().strftime("%A, %B %d, %Y")

    # Build long-form subject line
    committee = meta.get("committee_name", "Committee")
    title = meta.get("hearing_title", "Hearing")
    subject = overrides.get("subject_line")
    if not subject:
        subject = f'{committee} Hearing, "{title}"'

    return {
        "from": memo_from,
        "date": memo_date,
        "subject": subject,
    }


def _compose_display_title(record: dict) -> str:
    """Return the official hearing title for centered display.

    Rules (STYLE_GUIDE §6):
    - Use official hearing title when known
    - Do not embellish
    """
    return record["metadata"].get("hearing_title", "")


# ---------------------------------------------------------------------------
# Main composition entry point
# ---------------------------------------------------------------------------

def compose(record_dict: dict,
            memo_from: str = "Mercury",
            memo_date: str = None,
            subject_line: str = None,
            confidentiality_footer: str = None) -> dict:
    """Compose a Mercury-style memo from a structured hearing record.

    Args:
        record_dict: HearingRecord as a dict (from extractor)
        memo_from: FROM field value
        memo_date: DATE field value (defaults to today)
        subject_line: SUBJECT field override
        confidentiality_footer: Override default footer text

    Returns:
        MemoOutput dict conforming to memo_output.schema.json
    """
    overrides = {
        "memo_from": memo_from,
        "memo_date": memo_date,
        "subject_line": subject_line,
    }

    # Compose each section
    metadata_block = _compose_metadata_block(record_dict, overrides)
    display_title = _compose_display_title(record_dict)

    sections = [
        _compose_overview(record_dict),
        _compose_opening_statements(record_dict),
        _compose_witnesses(record_dict),
        _compose_qa(record_dict),
    ]

    footer_text = confidentiality_footer or DEFAULT_CONFIDENTIALITY_FOOTER

    memo_output = {
        "metadata_block": metadata_block,
        "display_title": display_title,
        "sections": sections,
        "footer": {
            "text": footer_text,
            "placement": "inline_once",
        },
        "verification_flags": [],
        "reviewer_notes": record_dict.get("uncertainties", []),
    }

    return memo_output


def render_memo_text(memo_output: dict) -> str:
    """Render the memo output as formatted plain text / markdown.

    This is the human-readable version of the memo.
    """
    lines = []

    # Metadata block
    mb = memo_output["metadata_block"]
    lines.append(f"FROM:\t\t{mb['from']}")
    lines.append(f"DATE:\t\t{mb['date']}")
    lines.append(f"SUBJECT:\t{mb['subject']}")
    lines.append("")
    lines.append("")

    # Display title (centered)
    lines.append(memo_output["display_title"])
    lines.append("")

    # Sections
    for section in memo_output["sections"]:
        lines.append(section["heading"])
        if section["body"]:
            lines.append(section["body"])
            lines.append("")

        for sub in section.get("subsections", []):
            lines.append(sub["heading"])
            lines.append(sub["body"])
            lines.append("")

    # Footer
    lines.append("")
    lines.append(memo_output["footer"]["text"])

    return "\n".join(lines)
