#!/usr/bin/env python3
"""Media Clip Cleaner execution script.

Transforms messy pasted news text into cleaned markdown suitable for clips.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

CHANGE_AGENT_BASE_URL = "https://runpod-proxy-956966668285.us-central1.run.app/v1/"


NOISE_PATTERNS = [
    r"^#+\s+",
    r"^example\s+\d+",
    r"\bsubscribe\b",
    r"\bnewsletter\b",
    r"\brecommended\b",
    r"\bread more\b",
    r"\bcookie\b",
    r"\bsign up\b",
    r"\bfollow us\b",
    r"\badvertisement\b",
    r"\bphoto credit\b",
    r"\bcredit\s*[\.\:]",
    r"credit\s+for\s+the\s+new\s+york\s+times",
    r"^\s*photo\s*:",
    r"^\s*image\s*:",
    r"^\s*share\s*$",
    r"^\s*share\s+full\s+article",
    r"^\s*live\s+video\s*$",
    r"^\s*article\s+body\s+starts\.{0,3}\s*$",
    r"^\s*skip\s+to\s+(content|navigation|main)",
    r"^\s*listen\s*[·•:]\s*\d+",
    r"^\s*\d+:\d+\s*min\b",
    r"^\s*supported\s+by\s*$",
    r"^\s*send\s+any\s+friend\b",
    r"^\s*gift\s+this\s+article\b",
    r"^\s*save\s*$",
    r"^\s*comments\s*$",
    r"^\s*log\s*in\b",
    r"^\s*open\s+in\s+app\b",
    r"^\s*get\s+the\s+app\b",
    r"^\s*liveupdates?\s*$",
    r"^\s*\d+[mh]\s+ago\s*$",
    r"^\s*list of \d+ items",
    r"^\s*-\s*list \d+ of \d+",
    r"^\s*see\s+more\s+on\s*:",
    r"\bterms\s+of\s+(service|sale)\b",
    r"\bprivacy\s+policy\b",
    r"\bcookie\s+policy\b",
    r"\baccessibility\b",
    r"\badvertise\b",
    r"\bsite\s*map\b",
    r"\byour\s+privacy\s+choices\b",
    r"\bcontact\s+us\b",
    r"\bwork\s+with\s+us\b",
    r"\bt\s+brand\s+studio\b",
    r"^exclusive news, data and analytics for financial market professionals$",
    r"^our standards:",
    r"^reuters, the news and media division of thomson reuters",
    r"^access unmatched financial data",
    r"^browse an unrivalled portfolio",
    r"^screen for heightened risk",
    r"^all quotes delayed a minimum of 15 minutes",
    r"^©\s*\d{4}\s+reuters",
    r"^copyright\s+©?\s*\d{4}",
    r"\ball rights reserved\b",
    r"\bappeared in the .* print edition\b",
    r"^[a-f0-9]{24,}$",
    r"^d\.c\.,\s*md\.,\s*&\s*va\.",
    r"washingtonpost\.com",
    r"^\s*loading\.\.\.\s*$",
    r"^\s*in\s+[\"“][^\"”]{1,40}[\"”]\s*$",
    r"^\s*s\s+m\s+t\s+w\s+t\s+f\s+s\s*$",
    r"^\s*(?:\d{1,2}\s+){6}\d{1,2}\s*$",
    r"\ball right reserved\b",
    r"\bfoi portal\b",
    r"\bstaff mail\b",
    r"\brate card\b",
    r"\babout us\b",
    r"\bfederal radio corporation of nigeria\b",
    r"\blargest radio network\b",
]

METADATA_PATTERNS = [
    r"^\s*by\s+[A-Z]",                          # "By Adam Rasgon..."
    r"^\s*reporting\s+by\b",
    r"\bwriting\s+by\b",
    r"\bediting\s+by\b",
    r"\breported\s+from\s+",                       # "Adam Rasgon reported from Jerusalem."
    r"^\s*reporting\s+was\s+contributed\s+by\b",  # "Reporting was contributed by..."
    r"^\s*updated\s+\w+\s+\d+",                  # "Updated March 21..."
    r"^\s*published\s+\w+\s+\d+",                # "Published March 21..."
    r"is\s+a\s+(reporter|correspondent|columnist|editor|writer)\s+(for|at|with)\s+the\b",
]

# Patterns that signal "everything after this is not the article"
END_OF_ARTICLE_PATTERNS = [
    r"^\s*see\s+more\s+on\s*:",
    r"^\s*more\s+on\s+(the\s+)?\w",
    r"^\s*more\s+in\s+\w",
    r"^\s*trending\s+in\b",
    r"^\s*what\s+to\s+read\s+next\b",
    r"^\s*read\s+next\s*$",
    r"^\s*suggested\s+topics:?\s*$",
    r"^\s*related\s+(articles?|stories|coverage)\b",
    r"^\s*you\s+might\s+(also\s+)?like\b",
    r"^\s*popular\s+(in|on|stories)\b",
    r"^\s*editors['']?\s+picks?\b",
    r"^\s*site\s+index\s*$",
    r"^\s*transcript\s*:",
    r"^\s*disclaimer\s*:",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_for_match(text: str) -> str:
    return re.sub(r"[^\w\s]", "", _normalize(text).lower()).strip()


def _is_changeagent_model(model: str) -> bool:
    active_model = (os.environ.get("LLM_MODEL_OVERRIDE") or model or "").strip()
    return active_model == "ChangeAgent"


def _llm_api_key(model: str) -> str:
    if _is_changeagent_model(model):
        api_key = (os.environ.get("CHANGE_AGENT_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("CHANGE_AGENT_API_KEY is not set.")
        return api_key
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("LLM API key is not set for the configured endpoint.")
    return api_key


def _responses_api_url(model: str) -> str:
    if _is_changeagent_model(model):
        base_url = (
            os.environ.get("CHANGE_AGENT_BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or CHANGE_AGENT_BASE_URL
        ).strip()
    else:
        base_url = (os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip()
    return f"{base_url.rstrip('/')}/responses"


def _looks_like_social_cluster(line: str) -> bool:
    platforms = ("facebook", "twitter", "x", "instagram", "linkedin", "bluesky", "pinterest", "tumblr")
    hits = sum(1 for platform in platforms if platform in line)
    return hits >= 2


def _is_noise(line: str) -> bool:
    low = line.lower().strip()
    if not low:
        return True
    if low in {"-", "•", "|"}:
        return True
    if _looks_like_social_cluster(low):
        return True
    return any(re.search(pattern, low) for pattern in NOISE_PATTERNS)


def _is_metadata(line: str) -> bool:
    stripped = line.strip()
    low = stripped.lower()
    if re.match(r"^\s*by\s+(?:[—-]\s*)?[A-Z]", stripped):
        return True
    if re.match(r"^\s*(byline|author)\s*:", low):
        return True
    if " • " in low and re.search(r"\bby\b", low):
        return True
    # Standalone timestamps: "March 21, 2026, 9:03 a.m. ET" or "March 20, 2026"
    if re.match(r"^\s*\w+\.?\s+\d{1,2},?\s+\d{4}", low):
        # It's a date-like line — only treat as metadata if it's short (not a real paragraph)
        if len(stripped.split()) <= 10:
            return True
    # Short lines that look like bylines or datelines (not full paragraphs)
    if len(stripped.split()) <= 15:
        if any(re.search(pattern, stripped, re.IGNORECASE) for pattern in METADATA_PATTERNS):
            return True
    return False


def _is_headline(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    low = stripped.lower()
    if low.startswith(("headline:", "big headline:")):
        return True
    letters = re.sub(r"[^A-Za-z]", "", stripped)
    is_shouty = bool(letters) and stripped.upper() == stripped and len(letters) >= 12
    words = stripped.split()
    if is_shouty:
        return True
    # Short lines in mostly-title case (allow small words like "an", "in", "to", "the", "of")
    if len(words) <= 18 and not stripped.endswith("."):
        small_words = {"a", "an", "and", "as", "at", "but", "by", "for", "if", "in",
                       "is", "it", "no", "nor", "not", "of", "on", "or", "so", "the",
                       "to", "up", "vs", "yet", "from", "into", "with"}
        capitalized = sum(1 for w in words if w[0].isupper() or w.lower() in small_words)
        if capitalized == len(words) and len(words) >= 4:
            return True
    return False


def _extract_subtitle(line: str) -> Optional[str]:
    m = re.match(r"^\s*(subtitle|lede|deck)\s*:\s*(.+)$", line, flags=re.IGNORECASE)
    if m:
        return _normalize(m.group(2))
    return None


def _is_image_caption(line: str, next_line: str = "") -> bool:
    """Detect image captions — descriptive lines near Credit lines."""
    low = line.lower().strip()
    next_low = next_line.lower().strip() if next_line else ""
    if re.search(r"\((image|photo)\)\s*$", low):
        return True
    if "purchase licensing rights" in low or "file photo" in low:
        return True
    if any(token in low for token in (
        "getty images",
        "agence france-presse",
        "attila kisbenedek/",
        "jonathan ernst/",
        "reuters/",
        "marton monus",
        "photo:",
    )):
        return True
    # Lines containing "Credit" references
    if re.search(r"credit\s*[\.\:\…]", low):
        return True
    if "for the new york times" in low or "for the washington post" in low:
        return True
    # If the next line is a credit line, this is likely a caption
    if next_low and re.search(r"(credit|for the new york times|for the washington post)", next_low):
        return True
    return False


def _is_author_bio(line: str) -> bool:
    """Detect author bio lines like 'David Sanger covers the Trump administration...'"""
    low = line.lower().strip()
    # "X is a reporter/correspondent/columnist for..."
    if re.search(r"is\s+a\s+(reporter|correspondent|columnist|editor|writer|journalist)\s+(for|at|with|covering)\b", low):
        return True
    if re.search(r"\b(correspondent|reporter|editor|writer)\s+covering\b", low):
        return True
    # "X covers ... for The Times / The Post / etc."
    if re.search(r"\bcovers?\s+.{5,}\s+for\s+the\s+\w+", low):
        return True
    if re.search(r"\bcovers?\s+(breaking|politics|policy|business|climate|courts|international|world|national)\b", low):
        return True
    # "X has covered ... presidents / administrations"
    if re.search(r"\bhas\s+(covered|reported|written|been\s+a\s+\w*\s*journalist)", low):
        return True
    # "X writes often on..." / "X has written X books"
    if re.search(r"\bwrites?\s+(often|regularly|frequently|about|on)\b", low):
        return True
    if re.search(r"\bis\s+based\s+in\b", low):
        return True
    if re.search(r"\b(distinguished\s+fellow|senior\s+fellow|professor\s+of|board\s+member|member\s+of)\b", low):
        return True
    if re.search(r"\b(authored|written)\s+numerous\s+books\b", low):
        return True
    if re.search(r"\bmost\s+recent\s+book\b", low):
        return True
    if re.search(r"\bbefore\s+joining\s+\w+", low):
        return True
    if re.search(r"\bthe\s+column\s+appears\s+on\b", low):
        return True
    # "X has been a Times/Post journalist"
    if re.search(r"has\s+been\s+a\s+\w+\s+journalist", low):
        return True
    return False


def _is_end_of_article(line: str) -> bool:
    """Detect lines that signal end of article / start of related content."""
    low = line.lower().strip()
    return any(re.search(pattern, low) for pattern in END_OF_ARTICLE_PATTERNS)


def _is_tail_section_start(line: str) -> bool:
    stripped = line.strip()
    low = stripped.lower()
    if not stripped:
        return False
    if re.match(r"^(q|a)\s*:\s+", stripped, flags=re.IGNORECASE):
        return True
    if re.match(r"^(?:-+\s*)?on\s+\w+\s+\d{1,2},\s+\d{4}\b", stripped, flags=re.IGNORECASE):
        return True
    if re.match(r"^(?:-+\s*)?in\s+\w+\s+\d{4}\b", stripped, flags=re.IGNORECASE):
        return True
    if "footage from the hearing is available here" in low:
        return True
    if "for professional and dedicated immigration legal services" in low:
        return True
    if "the column appears on" in low or "global view" in low:
        return True
    if "all rights reserved" in low or ("appeared in the" in low and "print edition" in low):
        return True
    return _is_end_of_article(stripped)


def _is_nav_fragment(line: str) -> bool:
    """Detect short navigation-like fragments that aren't real paragraphs."""
    stripped = line.strip()
    words = stripped.split()
    # Very short lines (1-5 words) that don't end with a period are likely nav
    if len(words) <= 5 and not stripped.endswith((".","!","?",'"',"'")):
        return True
    return False


def _matches_title(line: str, title: Optional[str]) -> bool:
    if not title:
        return False
    title_norm = _normalize_for_match(title)
    line_norm = _normalize_for_match(line)
    if not title_norm or not line_norm:
        return False
    if title_norm == line_norm or title_norm in line_norm or line_norm in title_norm:
        return True
    return SequenceMatcher(None, title_norm, line_norm).ratio() >= 0.82


def _strip_title_prefix(line: str, title: Optional[str]) -> str:
    if not title:
        return line.strip()
    title_parts = [re.escape(part) for part in title.split() if part.strip()]
    if not title_parts:
        return line.strip()
    title_pattern = r"\s+".join(title_parts)
    match = re.match(rf"^\s*{title_pattern}(?:\s*[:\-–—|]\s*)?(.*)$", line, flags=re.IGNORECASE)
    if not match:
        return line.strip()
    remainder = match.group(1).strip()
    return remainder or ""


def _strip_category_prefix(line: str) -> str:
    cleaned = re.sub(
        r"^\s*(?:[A-Z](?:\.[A-Z])+\.?|[A-Z][a-z]{1,15}(?:\s+[A-Z][a-z]{1,15}){0,2})"
        r"\s*(?:[:|]|[—-])\s*",
        "",
        line,
    ).strip()
    cleaned = re.sub(
        r"^\s*(?:[A-Z](?:\.[A-Z])+\.?)\s+(?=[A-Z])",
        "",
        cleaned,
    ).strip()
    return cleaned or line.strip()


def _is_category_label(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    words = stripped.split()
    if len(words) > 4:
        return False
    if re.search(r"[:;!?]$", stripped):
        return False
    if re.fullmatch(r"[A-Za-z0-9.&/'-]+(?:\s+[A-Za-z0-9.&/'-]+){0,3}\.?", stripped):
        return True
    return False


def _is_location_dateline_fragment(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if re.match(
        r"^(?:[A-Z][A-Za-z.\-']+(?:,\s*[A-Z][A-Za-z.\-']+)*)\s*(?:\([A-Za-z. ]+\))?\s*[—-]\s*$",
        stripped,
    ):
        return True
    if re.match(r"^(?:[A-Z]{2,}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})\s*[—-]\s*$", stripped):
        return True
    return False


def _is_ui_or_promo_line(line: str) -> bool:
    low = line.lower().strip()
    if not low:
        return False
    if re.fullmatch(r"in\s+[\"“][^\"”]{1,40}[\"”]", low):
        return True
    if re.fullmatch(r"s\s+m\s+t\s+w\s+t\s+f\s+s", low):
        return True
    if re.fullmatch(r"(?:\d{1,2}\s+){6}\d{1,2}", low):
        return True
    promo_patterns = [
        r"\bsee more of our coverage\b",
        r"\bsearch results\b",
        r"\badd .* on google\b",
        r"\bget the full .* experience\b",
        r"\bupgrade to enjoy\b",
        r"\byou['’]re currently subscribed\b",
        r"\bcancel anytime\b",
        r"\bview all posts\b",
        r"\bleave your feedback\b",
        r"\bcopy url\b",
        r"\bpurchase licensing rights\b",
        r"\bget connected\b",
        r"\bstay informed\b",
        r"\bour ratings\b",
        r"\bcharity watchdog\b",
        r"\befficient use of donor contributions\b",
        r"\bmost pressing crises\b",
        r"\bany questions\??\b",
        r"\bfill the form\b",
        r"\bcall you soon\b",
        r"\bshare on\b",
        r"\bshare\b",
        r"\bread more:\b",
        r"\bsupport trusted journalism\b",
        r"\ba free press is a cornerstone\b",
        r"\bcivil dialogue\b",
        r"\bdonate now\b",
        r"\bfollow the .* on\b",
        r"\bdownload the app\b",
        r"\bcreate account\b",
        r"\bsubscribe\b",
        r"\bappeared in the .* print edition\b",
        r"\ball rights reserved\b",
        r"\bglobal view\b",
        r"\bjournal editorial report\b",
        r"\bwashingtonpost\.com\b",
        r"\ball right reserved\b",
        r"\bradio nigeria\b",
        r"\bradionigeria\.gov\.ng\b",
        r"\bfoi portal\b",
        r"\bstaff mail\b",
        r"\brate card\b",
        r"\bclick naija radio\b",
        r"\bcorporate fm stations\b",
    ]
    if any(re.search(pattern, low) for pattern in promo_patterns):
        return True
    if re.search(r"https?://|www\.", low):
        return True
    if _looks_like_social_cluster(low):
        return True
    return False


def _strip_dateline_prefix(line: str) -> str:
    cleaned = re.sub(
        r"^\s*(?:(?:[A-Z][A-Za-z.\-']*(?:\s+[A-Z][A-Za-z.\-']*)*),\s+)?"
        r"(?:\w+\.?\s+\d{1,2})\s*\([^)]+\)\s*[-–—]\s*",
        "",
        line,
    ).strip()
    cleaned = re.sub(
        r"^\s*\w+\.?\s+\d{1,2},\s+\d{4}\s*(?=[A-Z\"'])",
        "",
        cleaned,
    ).strip()
    if not re.match(r"^\s*By\s+[—-]", cleaned, flags=re.IGNORECASE):
        cleaned = re.sub(
            r"^\s*(?:[A-Z][A-Z.\-']+(?:[-\s][A-Z.\-']+)*|[A-Z][A-Za-z.\-']+(?:\s+[A-Z][A-Za-z.\-']+){0,5})"
            r"(?:,\s*[A-Z][A-Za-z.\-']+(?:\s+[A-Z][A-Za-z.\-']+)*)*"
            r"\s*(?:\([^)]+\))?\s*[-–—]\s*",
            "",
            cleaned,
        ).strip()
    if cleaned:
        return cleaned
    return line.strip()


def _slice_from_dateline_if_prefixed(line: str, title: Optional[str] = None) -> str:
    dateline_patterns = [
        r"(?:[A-Z][A-Za-z.\-']+(?:,\s*[A-Z][A-Za-z.\-']+)*)\s*(?:\([^)]+\))?\s*[—–-]\s+",
        r"(?:\w+\.?\s+\d{1,2}\s*\([^)]+\)\s*[-–—]\s+)",
    ]
    for pattern in dateline_patterns:
        for match in re.finditer(pattern, line):
            if match.start() == 0:
                continue
            matched_text = line[match.start():match.end()].strip().lower()
            if matched_text.startswith("by "):
                continue
            prefix = line[:match.start()].strip()
            if (
                _is_ui_or_promo_line(prefix)
                or _is_metadata(prefix)
                or _matches_title(prefix, title)
                or _is_category_label(prefix)
                or "share" in prefix.lower()
                or "feedback" in prefix.lower()
            ):
                return line[match.start():].strip()
    return line


def _scrub_inline_noise(line: str) -> str:
    cleaned = line
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", cleaned)
    cleaned = re.sub(r"\bREAD MORE:\s*[^.?!]+(?:[.?!]|$)", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\bA free press is a cornerstone of a healthy democracy\.[^.?!]*Donate now\.?",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\bSupport trusted journalism(?: and civil dialogue)?\.?\s*Donate now\.?",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"(?:^|\s)By\s+[—-]\s*[^.?!]{0,250}$",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+copyright\s+©?\s*\d{4}.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+appeared in the .* print edition.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+the column appears on .*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+global view\b.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+journal editorial report:.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+photo:\s+.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+reuters/\S+.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\s+(?:-\s+)?On\s+\w+\s+\d{1,2},\s+\d{4}\b.*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+Q:\s+.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+Disclaimer:\s+.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+Transcript:\s+.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def _strip_leading_article_chrome(
    line: str,
    title: Optional[str] = None,
    *,
    strip_category: bool = False,
) -> str:
    cleaned = line.strip()
    prior = None
    while cleaned and cleaned != prior:
        prior = cleaned
        if strip_category:
            cleaned = _strip_category_prefix(cleaned)
        cleaned = _strip_title_prefix(cleaned, title)
        cleaned = _strip_dateline_prefix(cleaned)
    return cleaned.strip()


def clean_clip(raw_text: str, title: Optional[str] = None) -> str:
    lines = raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized_lines = [_normalize(raw) for raw in lines]
    cleaned_lines: list[str] = []
    seen = set()
    for i, line in enumerate(normalized_lines):
        if not line:
            continue

        line = _slice_from_dateline_if_prefixed(line, title=title)

        # Once we hit an end-of-article marker, stop collecting
        if _is_end_of_article(line):
            break

        # Look ahead for image caption detection
        next_line = normalized_lines[i + 1] if i + 1 < len(normalized_lines) else ""
        next_nonempty_line = ""
        for candidate in normalized_lines[i + 1:]:
            if candidate:
                next_nonempty_line = candidate
                break

        if not cleaned_lines and _matches_title(line, title):
            continue

        if (
            next_nonempty_line
            and re.fullmatch(r'in\s+[\"“][^\"”]{1,40}[\"”]', next_nonempty_line.strip(), flags=re.IGNORECASE)
            and (_is_headline(line) or not re.search(r"[.?!]$", line))
        ):
            continue

        # Only strip headlines/titles BEFORE the first body paragraph.
        # Once we have body content, short uppercase/title-case lines are
        # in-article section headers and must be kept.
        if not cleaned_lines and _is_headline(line):
            continue

        # Skip short nav-like fragments before the first real paragraph
        if not cleaned_lines and _is_nav_fragment(line):
            continue

        # Strip common bracket wrappers left by copied snippets.
        line = re.sub(r"^\[(.*?)\]$", r"\1", line).strip()
        if not line:
            continue
        line = _slice_from_dateline_if_prefixed(line, title=title)
        line = _strip_leading_article_chrome(
            line,
            title=title,
            strip_category=not cleaned_lines,
        )
        pre_scrub_line = line
        line = _scrub_inline_noise(line)
        if not line:
            continue
        if cleaned_lines and _is_tail_section_start(line):
            break
        if _is_noise(line) or _is_metadata(line) or _is_image_caption(pre_scrub_line, next_line) or _is_author_bio(line):
            continue
        if _is_noise(line):
            continue

        # Skip nav fragments that appear between article paragraphs
        if _is_nav_fragment(line):
            continue

        key = re.sub(r"\W+", "", line.lower())
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned_lines.append(line)

    output = "\n\n".join(cleaned_lines).strip()
    if not output:
        return output
    return _post_process_llm(output, title=title)


def validate_output(cleaned_text: str, title: Optional[str] = None) -> tuple[bool, list[str]]:
    issues = []
    stripped = cleaned_text.strip()
    if not stripped:
        issues.append("Output is empty.")
        return False, issues

    forbidden_snippets = [
        "skip to content",
        "section navigation",
        "subscribe",
        "recommended",
        "cookie policy",
        "terms of service",
        "read comments",
        "here is the cleaned text",
        "read next",
        "suggested topics",
        "our standards:",
        "all quotes delayed",
        "purchase licensing rights",
        "leave your feedback",
        "copy url",
    ]
    low = stripped.lower()
    for snippet in forbidden_snippets:
        if snippet in low:
            issues.append(f"Forbidden clutter found: '{snippet}'.")
            break

    if re.search(r"https?://|www\.", low):
        issues.append("URL-like text remains in output.")

    if title:
        title_norm = _normalize_for_match(title)
        body_norm = _normalize_for_match(stripped)
        if title_norm and title_norm in body_norm:
            issues.append("Headline/title still appears in cleaned output.")

    if re.search(r"^\s*(headline|big headline)\s*:", stripped, flags=re.IGNORECASE | re.MULTILINE):
        issues.append("Headline marker remains in output.")

    return len(issues) == 0, issues


def _llm_prompt(raw_text: str, title: Optional[str] = None) -> str:
    title_instruction = ""
    if title:
        title_instruction = (
            f'\nKNOWN HEADLINE: "{title}"\n'
            "Never output this headline or any close variation of it anywhere in the response, "
            "even if it appears multiple times or is separated by punctuation/case changes.\n"
        )
    return (
        "You clean messy pasted news text into clip-ready format.\n"
        "Your job is to keep only the article deck/subtitle (if present) and the article body.\n"
        "Everything else is disposable page chrome.\n\n"
        f"{title_instruction}"
        "CORE TEST:\n"
        "- Keep a line only if it clearly reads as part of the article itself.\n"
        "- If the publisher website disappeared and only the article remained, would this line still belong? If no, remove it.\n"
        "- Prefer false negatives over false positives: when in doubt, drop the line rather than keep possible page chrome.\n"
        "- A line must contribute reported content, a real deck/subtitle, or a genuine in-article section header. Otherwise remove it.\n\n"
        "ALWAYS PROTECT REAL ARTICLE TEXT:\n"
        "- Never remove a full sentence or paragraph that clearly conveys the article's reported facts, analysis, quotations, or narrative.\n"
        "- Never remove a real in-article section header that organizes the article itself.\n"
        "- Do not rewrite, summarize, or shorten valid article prose.\n"
        "- If something is clearly a real article sentence, keep it even if it mentions a place, a person, a publication, or an organization.\n\n"
        "REMOVE GENERIC NON-ARTICLE TEXT ACROSS ALL OUTLETS:\n"
        "- The main headline/title and any close variation of it\n"
        "- Section/category labels at the top such as desk names, countries, or beats (for example lines like 'U.S.' or 'Politics')\n"
        "- Bylines, reporter/editor credits, author bios, correspondent bios, 'based in' lines\n"
        "- Datelines and location-only openers, including wire-style prefixes like 'PORT-AU-PRINCE, Haiti (AP) —', 'WASHINGTON —', or 'April 17 (Reuters) -'\n"
        "- Image markers, image alt text, photo captions, gallery text, photographer credits, file-photo notes, licensing-rights text\n"
        "- Timestamps, publication dates, update times, standalone dates\n"
        "- Share widgets, social buttons, URLs, 'copy url', feedback prompts, forms, email/social platform lists\n"
        "- Subscription, account, upgrade, donation, fundraising, app-download, and newsletter prompts\n"
        "- Related stories, 'read next', 'see more coverage', search-result promos, recommendations, footer/legal text\n"
        "- Any marketing or institutional boilerplate that is not part of the reported article\n\n"
        "BROAD CLASSES TO REMOVE:\n"
        "- Titles, near-duplicate titles, subtitles that are actually promo text, and top-of-page category or section labels\n"
        "- Standalone words, short fragments, isolated labels, menu items, tabs, buttons, widget text, and other text that does not read like article prose\n"
        "- Outlet names, publication names, section names, edition labels, desk labels, newsletter labels, app labels, and brand labels when they appear alone or as page furniture\n"
        "- Byline material of any kind: authors, editors, correspondents, contributors, columnist labels, bios, affiliations, credentials, prior positions, books, awards, and profile blurbs\n"
        "- Image-related material of any kind: captions, alt text, photo descriptions, photographer names, agency names, file-photo notes, licensing notes, and credit lines\n"
        "- Navigation and discovery material: related stories, teaser headlines, recommendation lists, search-result snippets, homepage fragments, article indexes, read-next blocks, and carousel text\n"
        "- Utility/interface material: share prompts, copy-link text, feedback prompts, forms, login/subscription prompts, donation asks, app-download prompts, and account or settings text\n"
        "- Structural website junk: calendars, date pickers, day-of-week rows, number grids, loading states, pagination, filters, and generic widgets\n"
        "- Footer/legal/corporate material: copyright, rights reserved, site descriptions, company descriptions, radio/network/about text, legal notices, edition notes, and footer menus\n"
        "- Any list of unrelated headlines or standalone headline-like lines that are not part of the same article\n"
        "- Summary bullet lists that appear before the article body\n"
        "- Stray one-line fragments that are clearly UI labels rather than article prose\n\n"
        "KEEP all of the following:\n"
        "- All factual body paragraphs of the article\n"
        "- In-article section headers and subheadings (e.g. 'WORRY AMONG SOME JOURNALISTS', "
        "'THE BOTTOM LINE', 'WHAT HAPPENS NEXT', 'A New Approach'). "
        "These break the article into sections and MUST stay as standalone lines "
        "with blank lines around them. Do NOT remove or merge them.\n"
        "- A real subtitle/deck/lede that appears right after the main title and summarizes the story in sentence form\n"
        "- The article body's paragraph breaks\n\n"
        "RULES:\n"
        "- Preserve the original text VERBATIM — do not paraphrase, summarize, or rewrite.\n"
        "- Output only the cleaned article text. No labels, bullets, or commentary.\n"
        "- Use one blank line between paragraphs.\n"
        "- Preserve paragraph separation. Do NOT collapse the article into one large block.\n"
        "- If a line is ambiguous, remove it unless it clearly contributes factual article content.\n"
        "- Do not keep standalone lines that are just category labels, city labels, sharing prompts, bios, or promos.\n"
        "- Never keep text just because it is fluent English. Fluency does not make it article body.\n"
        "- A real article sentence usually works as part of a coherent article paragraph; page chrome usually looks isolated, repetitive, list-like, promotional, navigational, or metadata-like.\n"
        "- Before finalizing, mentally scan every kept line and remove any line that reads like a widget, recommendation, footer, caption, bio, or site furniture.\n"
        "- Do NOT add any commentary like 'Here is the cleaned text.'\n\n"
        "Raw article text:\n"
        f"{raw_text}"
    )


def _post_process_llm(text: str, title: Optional[str] = None) -> str:
    """Clean up common LLM output issues — title removal, metadata stripping, paragraph cleanup."""
    lines = text.split("\n")
    cleaned = []
    seen = set()
    body_started = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # Preserve blank lines for paragraph separation
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue

        line_clean = _slice_from_dateline_if_prefixed(stripped, title=title)
        line_clean = _strip_leading_article_chrome(
            line_clean,
            title=title,
            strip_category=not body_started,
        )
        pre_scrub_line = line_clean
        line_clean = _scrub_inline_noise(line_clean)
        if not line_clean:
            continue

        if not body_started and (_matches_title(line_clean, title) or _is_headline(line_clean)):
            continue

        # Remove title if it appears as a standalone line anywhere near the start
        if title and not body_started and _matches_title(line_clean, title):
            continue

        if _is_location_dateline_fragment(line_clean):
            continue

        if not body_started and (_is_category_label(line_clean) or _is_nav_fragment(line_clean)):
            continue

        # Skip photo credits, author bios, first published lines, and UI/promotional blocks
        low = line_clean.lower()
        if "photo credit" in low or "first published:" in low:
            continue
        if re.match(r"^(credit|photo)\s*[:\.]", low):
            continue
        if _is_ui_or_promo_line(line_clean):
            continue
        if _is_metadata(line_clean) or _is_author_bio(line_clean) or _is_image_caption(pre_scrub_line):
            continue
        # Skip standalone timestamps like "March 20, 2026, 3:55 p.m. ET"
        if re.match(r"^\w+\.?\s+\d{1,2},?\s+\d{4}", low) and len(line_clean.split()) <= 10:
            continue
        if re.fullmatch(r"[A-Za-z]+\s+\d{1,2},\s+\d{4}", line_clean):
            continue
        # Skip "Here is the cleaned" preamble
        if low.startswith("here is the cleaned"):
            continue
        if body_started and _is_tail_section_start(line_clean):
            break

        # Paragraph dedup
        para_norm = re.sub(r"\s+", "", low)
        if para_norm in seen:
            continue
        seen.add(para_norm)

        cleaned.append(line_clean)
        body_started = True

    output = "\n".join(cleaned).strip()
    if output and "\n\n" not in output and output.count("\n") >= 1:
        output = output.replace("\n", "\n\n")
    return output


def clean_clip_llm_openai(raw_text: str, model: str, title: Optional[str] = None) -> str:
    api_key = _llm_api_key(model)

    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": _llm_prompt(raw_text, title=title)},
                ],
            }
        ],
    }
    req = urllib.request.Request(
        _responses_api_url(model),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LLM API HTTP {exc.code}: {detail}") from exc
    except Exception as exc:
        raise RuntimeError(f"LLM API request failed: {exc}") from exc

    data = json.loads(body)
    text = data.get("output_text", "").strip()
    if not text:
        parts = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    parts.append(content["text"])
        text = "\n".join(parts).strip()
    if not text:
        raise RuntimeError("LLM API returned no text content.")
    return _post_process_llm(text, title=title)


def _read_input(raw_text: Optional[str], input_file: Optional[str]) -> str:
    if raw_text:
        return raw_text
    if input_file:
        return Path(input_file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("Provide input using --raw-text, --input-file, or stdin.")


def _read_paste_until_token(done_token: str) -> str:
    print(
        f"Paste article text below. When finished, type '{done_token}' on a new line and press Enter:"
    )
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == done_token:
            break
        lines.append(line)
    text = "\n".join(lines).strip()
    if not text:
        raise ValueError("No pasted text received.")
    return text


def _read_clipboard() -> str:
    try:
        out = subprocess.check_output(["pbpaste"], text=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to read clipboard via pbpaste: {exc}") from exc
    text = out.strip()
    if not text:
        raise ValueError("Clipboard is empty. Copy article text first.")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean raw article text into clip-ready markdown.")
    parser.add_argument("--raw-text", type=str, default=None, help="Raw article text to clean.")
    parser.add_argument("--input-file", type=str, default=None, help="Path to raw text file.")
    parser.add_argument("--output-file", type=str, default=None, help="Write cleaned markdown to file.")
    parser.add_argument("--title", type=str, default=None, help="Article headline used for safer title removal.")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["local", "llm"],
        default="local",
        help="Cleaning mode: 'local' (rule-based) or 'llm' (configured LLM-compatible endpoint).",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="ChangeAgent",
        help="Model used in --mode llm (default: ChangeAgent).",
    )
    parser.add_argument(
        "--fallback-local",
        action="store_true",
        help="If the LLM API call fails, fallback to the local cleaner.",
    )
    parser.add_argument(
        "--paste",
        action="store_true",
        help="Interactive paste mode: paste text, then type done token on a new line.",
    )
    parser.add_argument(
        "--done-token",
        type=str,
        default="::end",
        help="Line token used to finish --paste mode (default: ::end).",
    )
    parser.add_argument(
        "--clipboard",
        action="store_true",
        help="Read article text directly from macOS clipboard (pbpaste).",
    )
    args = parser.parse_args()

    if args.paste and args.clipboard:
        raise ValueError("Use only one of --paste or --clipboard.")

    if args.clipboard:
        raw = _read_clipboard()
    elif args.paste:
        raw = _read_paste_until_token(args.done_token)
    else:
        raw = _read_input(args.raw_text, args.input_file)

    cleaned: str
    if args.mode == "local":
        cleaned = clean_clip(raw, title=args.title)
    else:
        try:
            cleaned = clean_clip_llm_openai(raw, args.llm_model, title=args.title)
        except Exception as exc:
            if not args.fallback_local:
                raise
            print(f"[warn] LLM mode failed ({exc}); falling back to local mode.", file=sys.stderr)
            cleaned = clean_clip(raw, title=args.title)

    ok, issues = validate_output(cleaned, title=args.title)
    if not ok:
        print("[warn] Output failed strict validation:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)

    if args.output_file:
        Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_file).write_text(cleaned + "\n", encoding="utf-8")
        print(args.output_file)
        return

    print(cleaned)


if __name__ == "__main__":
    main()
