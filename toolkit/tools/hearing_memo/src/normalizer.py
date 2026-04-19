"""
normalizer.py — Stage 1: Ingest and normalize hearing source text.

Implements NORMALIZATION_RULES.md and INPUT_SOURCE_PROFILES.md.
Removes format noise without changing meaning.
"""

import re
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from pypdf import PdfReader

from .config import TIMESTAMP_PATTERNS, VENDOR_NOISE_PATTERNS, SOURCE_PROFILE_SIGNALS


@dataclass
class NormalizationResult:
    """Output of the normalization stage."""
    cleaned_text: str
    source_profile: str  # licensed_transcript | article_style | video_transcript | cleaned_notes | generic_text
    metadata_candidates: dict = field(default_factory=dict)
    cleanup_notes: List[str] = field(default_factory=list)


def ingest_pdf(filepath: str) -> str:
    """Extract raw text from a PDF file using pypdf."""
    reader = PdfReader(filepath)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def ingest_text(filepath: str) -> str:
    """Read plaintext file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def ingest(filepath: str) -> str:
    """Auto-detect format and ingest."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return ingest_pdf(filepath)
    else:
        return ingest_text(filepath)


# ---------------------------------------------------------------------------
# Source profile detection (INPUT_SOURCE_PROFILES §Decision rule)
# ---------------------------------------------------------------------------

def detect_source_profile(raw_text: str) -> str:
    """Classify the source into a known profile family."""
    lower = raw_text[:5000].lower()  # check first ~5000 chars
    first_lines = raw_text[:500].strip().split("\n")

    # Article-style transcript (e.g., POLITICO PRO)
    # Pattern: starts with "Transcript" header, then title, then datetime
    if any(kw in lower for kw in SOURCE_PROFILE_SIGNALS["article_style"]):
        return "article_style"
    # Also detect by structure: "Transcript" on first line + date pattern
    if first_lines and first_lines[0].strip().lower() == "transcript":
        return "article_style"
    # Date-time pattern like "03/11/2026 03:30 PM EDT" early in text
    if re.search(r"\d{2}/\d{2}/\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)\s*\w+", raw_text[:500]):
        return "article_style"

    # Licensed transcript PDF
    if any(kw in lower for kw in SOURCE_PROFILE_SIGNALS["licensed_transcript"]):
        if "©" in raw_text[:2000] or "all rights reserved" in lower:
            return "licensed_transcript"

    # Video transcript
    if any(kw in lower for kw in SOURCE_PROFILE_SIGNALS["video_transcript"]):
        return "video_transcript"

    # Check for cleaned notes (relatively clean, no strong noise markers)
    noise_count = sum(1 for line in raw_text[:2000].split("\n")
                      if re.match(r"^\s*$", line))
    if noise_count < 5:
        return "cleaned_notes"

    return "generic_text"


# ---------------------------------------------------------------------------
# Cleanup pipeline
# ---------------------------------------------------------------------------

def strip_vendor_noise(text: str, notes: List[str]) -> str:
    """Remove vendor headers, footers, copyright, page numbers (NORMALIZATION_RULES §1)."""
    lines = text.split("\n")
    cleaned = []
    removed_count = 0
    for line in lines:
        stripped = line.strip()
        should_remove = False
        for pattern in VENDOR_NOISE_PATTERNS:
            if re.match(pattern, stripped, re.IGNORECASE):
                should_remove = True
                break
        if should_remove:
            removed_count += 1
        else:
            cleaned.append(line)
    if removed_count:
        notes.append(f"Removed {removed_count} vendor/noise lines")
    return "\n".join(cleaned)


def strip_timestamps(text: str, notes: List[str]) -> str:
    """Remove inline timestamps like (00:21) (NORMALIZATION_RULES §3)."""
    count = 0
    for pattern in TIMESTAMP_PATTERNS:
        matches = re.findall(pattern, text)
        count += len(matches)
        text = re.sub(pattern, "", text)
    if count:
        notes.append(f"Stripped {count} inline timestamps")
    return text


def normalize_speaker_labels(text: str, notes: List[str]) -> str:
    """Normalize speaker tags to a consistent format (NORMALIZATION_RULES §4).

    Handles patterns like:
    - 'Sen. Rick Scott (R-Fla.)' -> preserved as-is (most informative)
    - '>> Thank you, Commissioner Brands.' -> strip >> prefix
    - 'SMITH:' -> keep but note it as all-caps label
    """
    # Strip >> prefixes often seen in video transcripts
    cleaned, n = re.subn(r"^>>\s*", "", text, flags=re.MULTILINE)
    if n:
        notes.append(f"Stripped {n} '>>' speaker prefixes")

    return cleaned


def rebuild_paragraphs(text: str, notes: List[str]) -> str:
    """Rebuild paragraphs broken by PDF line wrapping (NORMALIZATION_RULES §5).

    Rules:
    - Join lines that are clearly mid-sentence (end without period, ?, !, :)
    - Do NOT join across speaker changes or section boundaries
    - Do NOT join across blank lines (paragraph boundaries)
    """
    lines = text.split("\n")
    rebuilt = []
    buffer = ""

    # Patterns indicating a new speaker or section boundary
    speaker_pattern = re.compile(
        r"^(?:Sen\.|Rep\.|Chairman|Chairwoman|Ranking Member|Commissioner|"
        r"Mr\.|Ms\.|Dr\.|Hon\.|Honorable|"
        r"Senator|Representative)\s+[A-Z]",
        re.IGNORECASE
    )
    # Pattern for all-caps speaker labels like "SCOTT:"
    allcaps_speaker = re.compile(r"^[A-Z][A-Z\s]+:")

    join_count = 0
    for line in lines:
        stripped = line.strip()

        # Blank line = paragraph boundary
        if not stripped:
            if buffer:
                rebuilt.append(buffer)
                buffer = ""
            rebuilt.append("")
            continue

        # Section/speaker boundary - don't join
        if speaker_pattern.match(stripped) or allcaps_speaker.match(stripped):
            if buffer:
                rebuilt.append(buffer)
                buffer = ""
            buffer = stripped
            continue

        # If buffer exists and the previous line looks like it was broken mid-sentence
        if buffer:
            # Check if previous buffer ends in a way that suggests continuation
            if (not buffer.rstrip().endswith((".", "?", "!", ":", '"', "'"))
                    and not stripped[0].isupper()):
                # Likely a broken line — join
                buffer = buffer.rstrip() + " " + stripped
                join_count += 1
                continue
            elif buffer.rstrip().endswith("-"):
                # Hyphenated word break
                buffer = buffer.rstrip()[:-1] + stripped
                join_count += 1
                continue

        # Start new buffer or append normally
        if buffer:
            rebuilt.append(buffer)
        buffer = stripped

    if buffer:
        rebuilt.append(buffer)

    if join_count:
        notes.append(f"Rebuilt {join_count} broken paragraph lines")

    return "\n".join(rebuilt)


def extract_metadata_candidates(text: str, notes: List[str]) -> dict:
    """Extract metadata candidates from text (NORMALIZATION_RULES §2, §7).

    Separates publication metadata from hearing metadata.
    """
    candidates = {}

    # Look for date patterns
    date_patterns = [
        # "03/11/2026 03:30 PM EDT"
        (r"(\d{2}/\d{2}/\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)\s*\w+)", "publication_datetime"),
        # Just "03/11/2026" (fallback when time is garbled by PDF extraction)
        (r"(\d{2}/\d{2}/\d{4})", "publication_date_only"),
        # "Wednesday, March 11, 2026"
        (r"((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+"
         r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
         r"\s+\d{1,2},?\s+\d{4})", "hearing_date_long"),
        # "March 11, 2026"
        (r"((?:January|February|March|April|May|June|July|August|September|October|November|December)"
         r"\s+\d{1,2},?\s+\d{4})", "date_mention"),
    ]

    for pattern, key in date_patterns:
        matches = re.findall(pattern, text[:5000])
        if matches:
            candidates[key] = matches[0] if len(matches) == 1 else matches

    # Look for committee name — also handle "Senate Aging" / "Special Committee on Aging"
    committee_patterns = [
        r"((?:Senate|House)\s+(?:Special\s+)?(?:Committee|Subcommittee)\s+on\s+[A-Z][a-zA-Z\s,]+?)(?:\.|,|\s+held|\s+will)",
        r"(U\.S\.\s+(?:Senate|House)\s+(?:Special\s+)?(?:Committee|Subcommittee)\s+on\s+[A-Z][a-zA-Z\s,]+?)(?:\.|,|\s+held|\s+will)",
        r"(U\.S\.-China\s+Economic\s+and\s+Security\s+Review\s+Commission)",
        r"(Senate\s+Aging)\b",
        r"(Special\s+Committee\s+on\s+Aging)",
    ]
    for pattern in committee_patterns:
        match = re.search(pattern, text[:5000], re.IGNORECASE)
        if match:
            raw_name = match.group(1).strip()
            # Normalize known short names
            if raw_name.lower() == "senate aging":
                raw_name = "U.S. Senate Special Committee on Aging"
            candidates["committee_name"] = raw_name
            break

    # For article-style: extract hearing title from early lines
    # Pattern: lines near the top before the first speaker label
    lines = text[:2000].split("\n")
    for i, line in enumerate(lines[:10]):
        stripped = line.strip()
        # Skip blank, date, and very short lines
        if not stripped or len(stripped) < 15:
            continue
        # Skip date/time lines
        if re.match(r"\d{2}/\d{2}/\d{4}", stripped):
            continue
        # Skip speaker lines
        if re.match(r"^(?:Sen\.|Rep\.|Chairman|Ranking)", stripped):
            break
        # This could be the title
        if (20 < len(stripped) < 200 and
                not stripped.startswith("The ") and
                stripped[0].isupper()):
            candidates.setdefault("hearing_title_from_header", stripped)
            break

    # Look for hearing title (often in quotes or after "hearing titled")
    title_patterns = [
        r'(?:hearing\s+titled|hearing\s+on)\s+["\u201c]([^"\u201d]+)["\u201d]',
        r'(?:hearing\s+titled|hearing\s+on)\s+(.+?)(?:\.|,\s+on\s)',
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text[:10000], re.IGNORECASE)
        if match:
            candidates["hearing_title"] = match.group(1).strip()
            break

    # Fallback: use the header-derived title
    if "hearing_title" not in candidates and "hearing_title_from_header" in candidates:
        candidates["hearing_title"] = candidates["hearing_title_from_header"]

    # Detect senators/representatives mentioned — handle (R-Fla.) style state abbrevs
    speaker_mentions = re.findall(
        r"(?:Sen\.|Senator|Rep\.|Representative|Chairman|Chairwoman|Ranking Member|Commissioner)"
        r"\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        r"(?:\s+\(([RD])-([A-Za-z.]+\.?)\))?",
        text[:15000]
    )
    if speaker_mentions:
        unique_speakers = list(dict.fromkeys(
            (name, party, state)
            for name, party, state in speaker_mentions
        ))
        candidates["speaker_mentions"] = [
            {"name": n, "party": p, "state": s}
            for n, p, s in unique_speakers[:20]
        ]

    return candidates


def strip_youtube_artifacts(text: str, notes: List[str]) -> str:
    """Remove YouTube auto-caption noise patterns (NORMALIZATION_RULES §video).

    Handles:
    - Bracketed audio cues: [Music], [Applause], [Laughter], [Inaudible], etc.
    - ASR stutter: consecutive duplicate words ("the the committee" → "the committee")
    - YouTube chapter markers that survived timestamp stripping
    """
    original_len = len(text)

    # Strip bracketed sound descriptors
    text = re.sub(r"\[(?:Music|Applause|Laughter|Inaudible|Indistinct|Crosstalk|Silence|"
                  r"Speaking foreign language|Background noise|Noise|Static|Beep)[^\]]*\]",
                  "", text, flags=re.IGNORECASE)

    # Strip chapter headings inserted by YouTube (e.g., "0:00 Opening Remarks")
    text = re.sub(r"^\d{1,2}:\d{2}(?::\d{2})?\s+.+$", "", text, flags=re.MULTILINE)

    # Remove ASR stutter: 2-4 consecutive occurrences of the same word
    def _dedup_words(m: re.Match) -> str:
        return m.group(1)
    text = re.sub(r"\b(\w+)(?:\s+\1){1,3}\b", _dedup_words, text, flags=re.IGNORECASE)

    # Collapse resulting blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    removed = original_len - len(text)
    if removed > 0:
        notes.append(f"Stripped ~{removed} chars of YouTube artifacts (sound cues, stutter)")
    return text


def detect_panels(text: str, notes: List[str]) -> List[str]:
    """Detect panel boundaries (NORMALIZATION_RULES §6)."""
    panel_signals = [
        r"Panel\s+(?:I{1,3}|[123])\b",
        r"(?:First|Second|Third)\s+[Pp]anel",
    ]
    panels_found = []
    for pattern in panel_signals:
        matches = re.findall(pattern, text)
        panels_found.extend(matches)
    if panels_found:
        notes.append(f"Detected panel markers: {panels_found}")
    return panels_found


# ---------------------------------------------------------------------------
# Main normalization entry point
# ---------------------------------------------------------------------------

def normalize(filepath: str) -> NormalizationResult:
    """Run the full normalization pipeline on a source file.

    Pipeline order:
    1. Ingest raw text
    2. Detect source profile
    3. Strip vendor noise
    4. Strip timestamps
    5. Normalize speaker labels
    6. Rebuild paragraphs
    7. Extract metadata candidates
    8. Detect panels
    """
    notes: List[str] = []

    # 1. Ingest
    raw_text = ingest(filepath)
    notes.append(f"Ingested {len(raw_text)} characters from {os.path.basename(filepath)}")

    # 2. Detect source profile
    profile = detect_source_profile(raw_text)
    notes.append(f"Detected source profile: {profile}")

    # 3-6. Cleanup pipeline
    # 3a. YouTube-specific artifacts (before general cleanup)
    if profile == "video_transcript":
        raw_text = strip_youtube_artifacts(raw_text, notes)
    text = strip_vendor_noise(raw_text, notes)
    text = strip_timestamps(text, notes)
    text = normalize_speaker_labels(text, notes)
    text = rebuild_paragraphs(text, notes)

    # 7. Extract metadata
    metadata = extract_metadata_candidates(text, notes)

    # 8. Panel detection
    panels = detect_panels(text, notes)
    if panels:
        metadata["panels_detected"] = panels

    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return NormalizationResult(
        cleaned_text=text,
        source_profile=profile,
        metadata_candidates=metadata,
        cleanup_notes=notes,
    )
