"""
verifier.py — Stage 4: Verification pass for the composed memo.

Checks structure, metadata, and style compliance per verify_memo.md.
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

from .config import (
    APPROVED_HEADINGS,
    DEFAULT_CONFIDENTIALITY_FOOTER,
    WORD_TARGETS,
    HEADING_HEARING_OVERVIEW,
    HEADING_QA,
)


def _parse_date_string(date_str: str):
    """Try to parse a date string into a datetime object."""
    formats = [
        "%A, %B %d, %Y",       # "Wednesday, March 11, 2026"
        "%B %d, %Y",            # "March 11, 2026"
        "%m/%d/%Y",             # "03/11/2026"
        "%Y-%m-%d",             # "2026-03-11"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def verify(memo_output: dict, hearing_record: dict) -> dict:
    """Run verification checks on the composed memo.

    Args:
        memo_output: MemoOutput dict from the composer
        hearing_record: Original HearingRecord dict

    Returns:
        dict with:
        - verdict: "pass" or "needs_review"
        - flags: list of verification flags
        - human_checks: fields requiring human confirmation
    """
    flags: List[str] = []
    human_checks: List[str] = []

    # ===== 1. Metadata block completeness =====
    mb = memo_output.get("metadata_block", {})
    for field in ["from", "date", "subject"]:
        if not mb.get(field):
            flags.append(f"MISSING_METADATA: '{field.upper()}' field is empty")

    # ===== 2. Memo date vs hearing date distinction =====
    memo_date_str = mb.get("date", "")
    hearing_date_str = hearing_record.get("metadata", {}).get("hearing_date", "")

    if memo_date_str and hearing_date_str:
        memo_dt = _parse_date_string(memo_date_str)
        hearing_dt = _parse_date_string(hearing_date_str)

        if memo_dt and hearing_dt:
            if memo_dt == hearing_dt:
                flags.append(
                    "DATE_WARNING: Memo date equals hearing date — verify this is intended "
                    "(memo date is typically the day after the hearing)"
                )
        else:
            human_checks.append("Unable to parse memo date or hearing date for comparison")

    # ===== 3. Day-of-week correctness =====
    if memo_date_str:
        # Check if the day name matches the date
        day_match = re.match(
            r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(.+)",
            memo_date_str
        )
        if day_match:
            stated_day = day_match.group(1)
            rest = day_match.group(2)
            dt = _parse_date_string(rest)
            if dt:
                actual_day = dt.strftime("%A")
                if stated_day != actual_day:
                    flags.append(
                        f"DAY_DATE_MISMATCH: Stated '{stated_day}' but {rest} is actually a {actual_day}"
                    )

    if hearing_date_str:
        day_match = re.match(
            r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(.+)",
            hearing_date_str
        )
        if day_match:
            stated_day = day_match.group(1)
            rest = day_match.group(2)
            dt = _parse_date_string(rest)
            if dt:
                actual_day = dt.strftime("%A")
                if stated_day != actual_day:
                    flags.append(
                        f"DAY_DATE_MISMATCH: Hearing date stated '{stated_day}' "
                        f"but {rest} is actually a {actual_day}"
                    )

    # ===== 4. Title consistency =====
    subject = mb.get("subject", "")
    display_title = memo_output.get("display_title", "")
    if display_title and subject:
        # The display title should appear within the subject line
        if display_title.lower() not in subject.lower():
            flags.append(
                f"TITLE_INCONSISTENCY: Display title '{display_title[:50]}...' "
                f"not found within SUBJECT line"
            )
            human_checks.append("Verify SUBJECT line and display title are consistent")

    # ===== 5. Heading compliance =====
    sections = memo_output.get("sections", [])
    for section in sections:
        heading = section.get("heading", "")
        if heading not in APPROVED_HEADINGS:
            flags.append(f"UNAPPROVED_HEADING: '{heading}' is not in the approved heading set")

    # Check that all required sections are present
    section_headings = {s["heading"] for s in sections}
    required = {HEADING_HEARING_OVERVIEW, HEADING_QA}
    for req in required:
        if req not in section_headings:
            flags.append(f"MISSING_SECTION: Required section '{req}' not found")

    # ===== 6. Speaker heading format =====
    for section in sections:
        for sub in section.get("subsections", []):
            heading = sub.get("heading", "")
            speaker_type = sub.get("speaker_type", "")

            if speaker_type == "leadership_member":
                # Should have format like "Chairman Rick Scott (R-FL)" or (R-Fla.)
                if not re.search(r"\([RD]-[A-Za-z.]+\)", heading):
                    # Commissioners might not have party/state
                    if "commissioner" not in heading.lower():
                        flags.append(
                            f"SPEAKER_FORMAT: Leadership heading '{heading}' "
                            f"may be missing party/state designation"
                        )

    # ===== 7. Overview abstraction level =====
    overview_section = None
    for section in sections:
        if section["heading"] == HEADING_HEARING_OVERVIEW:
            overview_section = section
            break

    if overview_section:
        overview_body = overview_section.get("body", "")
        wc = len(overview_body.split())

        min_wc, max_wc = WORD_TARGETS["hearing_overview"]
        if wc < min_wc:
            flags.append(f"OVERVIEW_SHORT: Overview is {wc} words (target: {min_wc}–{max_wc})")
        elif wc > max_wc + 30:  # Allow some flexibility
            flags.append(f"OVERVIEW_LONG: Overview is {wc} words (target: {min_wc}–{max_wc})")

        # Check for individual speaker names (should be avoided)
        speaker_mentions = re.findall(
            r"(?:Sen\.|Senator|Rep\.|Chairman|Chairwoman|Ranking Member|Commissioner|Mr\.|Ms\.|Dr\.)\s+"
            r"[A-Z][a-z]+",
            overview_body
        )
        if speaker_mentions:
            flags.append(
                f"OVERVIEW_TOO_GRANULAR: Overview mentions specific speakers: "
                f"{', '.join(speaker_mentions[:3])}. Should stay high-level."
            )

    # ===== 8. Q&A organization =====
    qa_section = None
    for section in sections:
        if section["heading"] == HEADING_QA:
            qa_section = section
            break

    if qa_section:
        # Verify subsections are by member
        for sub in qa_section.get("subsections", []):
            if sub.get("speaker_type") != "qa_member":
                flags.append(
                    f"QA_ORGANIZATION: Q&A subsection '{sub.get('heading', '')}' "
                    f"may not be organized by member"
                )

    # ===== 9. Chair closing placement =====
    # Check no separate "Closing Remarks" top-level section exists
    for section in sections:
        heading_lower = section.get("heading", "").lower()
        if "closing" in heading_lower or "conclusion" in heading_lower:
            flags.append(
                f"EXTRA_SECTION: Found '{section['heading']}' — "
                f"closing remarks should be folded into the chair's Q&A subsection"
            )

    # ===== 10. Confidentiality footer =====
    footer = memo_output.get("footer", {})
    footer_text = footer.get("text", "")
    if not footer_text:
        flags.append("MISSING_FOOTER: No confidentiality footer text")
    elif footer_text != DEFAULT_CONFIDENTIALITY_FOOTER:
        flags.append(
            f"FOOTER_MODIFIED: Footer text differs from default: '{footer_text[:50]}...'"
        )
        human_checks.append("Verify custom confidentiality footer is authorized")

    # ===== 11. Word count checks =====
    for section in sections:
        for sub in section.get("subsections", []):
            body = sub.get("body", "")
            wc = len(body.split())
            speaker_type = sub.get("speaker_type", "")

            target_key = {
                "leadership_member": "opening_speaker",
                "witness": "witness",
                "qa_member": "qa_member",
            }.get(speaker_type)

            if target_key and target_key in WORD_TARGETS:
                min_wc, max_wc = WORD_TARGETS[target_key]
                if wc > max_wc + 50:
                    flags.append(
                        f"OVERLONG: '{sub['heading'][:40]}' is {wc} words "
                        f"(target: {min_wc}–{max_wc})"
                    )

    # ===== Determine verdict =====
    critical_prefixes = [
        "MISSING_METADATA", "MISSING_SECTION", "UNAPPROVED_HEADING",
        "EXTRA_SECTION", "DAY_DATE_MISMATCH", "MISSING_FOOTER",
    ]
    has_critical = any(
        any(f.startswith(prefix) for prefix in critical_prefixes)
        for f in flags
    )

    verdict = "needs_review" if (has_critical or len(flags) > 3) else "pass"

    # Add uncertainties from the hearing record as human checks
    for u in hearing_record.get("uncertainties", []):
        human_checks.append(u)

    return {
        "verdict": verdict,
        "flags": flags,
        "human_checks": human_checks,
    }
