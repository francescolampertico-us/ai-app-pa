"""
config.py — Shared constants and style definitions for the hearing memo tool.
All values are derived from the repo package documents (STYLE_GUIDE.md, CHANGELOG_V2.md, etc.).
"""

import os

# ---------- Paths ----------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(REPO_ROOT, "schema")
PROMPTS_DIR = os.path.join(REPO_ROOT, "prompts")
EXAMPLES_DIR = os.path.join(REPO_ROOT, "examples", "final_outputs")

HEARING_RECORD_SCHEMA = os.path.join(SCHEMA_DIR, "hearing_record.schema.json")
MEMO_OUTPUT_SCHEMA = os.path.join(SCHEMA_DIR, "memo_output.schema.json")

# ---------- Approved section headings (STYLE_GUIDE §7) ----------
HEADING_HEARING_OVERVIEW = "Hearing Overview"
HEADING_OPENING_STATEMENTS = "Committee Leadership Opening Statements"
HEADING_OPENING_COCHAIRS = "Co-Chairs' Opening Remarks"
HEADING_WITNESS_SECTION = "Witnesses Introductions and Testimonies"
# Variation seen in some examples (singular):
HEADING_WITNESS_SECTION_ALT = "Witnesses Introduction and Testimonies"
HEADING_QA = "Q&A"

DEFAULT_SECTION_ORDER = [
    HEADING_HEARING_OVERVIEW,
    HEADING_OPENING_STATEMENTS,
    HEADING_WITNESS_SECTION,
    HEADING_QA,
]

APPROVED_HEADINGS = {
    HEADING_HEARING_OVERVIEW,
    HEADING_OPENING_STATEMENTS,
    HEADING_OPENING_COCHAIRS,
    HEADING_WITNESS_SECTION,
    HEADING_WITNESS_SECTION_ALT,
    HEADING_QA,
}

# ---------- Confidentiality footer (STYLE_GUIDE §18, CHANGELOG_V2) ----------
DEFAULT_CONFIDENTIALITY_FOOTER = (
    "Confidential - Not for Public Consumption or Distribution"
)

# ---------- Word-count targets (STYLE_GUIDE §16) ----------
WORD_TARGETS = {
    "hearing_overview": (110, 170),
    "opening_speaker": (90, 180),
    "witness": (90, 180),
    "qa_member": (70, 180),
}

# ---------- Speaker-label patterns (STYLE_GUIDE §§10-12, skill.md) ----------
# In subsection headings: full role style
# In prose: short forms such as "Chairman Scott", "Sen. Tuberville"
HEADING_ROLE_PREFIXES = [
    "Chairman",
    "Chairwoman",
    "Ranking Member",
    "Full Committee Ranking Member",
    "Senator",
    "Commissioner",
    "Representative",
    "Rep.",
]

PROSE_SHORT_PREFIXES = [
    "Chairman",
    "Chairwoman",
    "Ranking Member",
    "Sen.",
    "Rep.",
    "Commissioner",
    "Hon.",
    "Mr.",
    "Ms.",
    "Dr.",
]

# ---------- DOCX formatting (inferred from example memos) ----------
DOCX_FONT_NAME = "Lato Light"
DOCX_FONT_FALLBACK = "Times New Roman"
DOCX_BODY_FONT_SIZE_PT = 11
DOCX_SECTION_HEADING_SIZE_PT = 14
DOCX_ALIGNMENT = "JUSTIFY"

# ---------- Timestamp patterns to strip (NORMALIZATION_RULES §3) ----------
TIMESTAMP_PATTERNS = [
    r"\(\d{1,2}:\d{2}(?::\d{2})?\)",   # (00:21) or (1:23:45)
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b",   # 00:21 standalone
]

# ---------- Vendor / noise patterns (NORMALIZATION_RULES §1) ----------
VENDOR_NOISE_PATTERNS = [
    r"^Transcript\s*$",
    r"©\s*\d{4}.*",
    r"^\d+\s*$",                       # standalone page numbers
    r"All rights reserved",
    r"POLITICO.*PRO",
]

# ---------- Source profile keywords (INPUT_SOURCE_PROFILES) ----------
SOURCE_PROFILE_SIGNALS = {
    "licensed_transcript": ["transcript", "©", "all rights reserved"],
    "article_style": ["politico", "reuters", "ap news"],
    "video_transcript": ["youtube", "video", "00:00"],
    "cleaned_notes": [],
}
