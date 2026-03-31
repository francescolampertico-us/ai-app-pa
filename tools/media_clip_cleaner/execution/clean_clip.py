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
from pathlib import Path
from typing import Optional


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
]

METADATA_PATTERNS = [
    r"^\s*by\s+[A-Z]",                          # "By Adam Rasgon..."
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
    r"^\s*related\s+(articles?|stories|coverage)\b",
    r"^\s*you\s+might\s+(also\s+)?like\b",
    r"^\s*popular\s+(in|on|stories)\b",
    r"^\s*editors['']?\s+picks?\b",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _is_noise(line: str) -> bool:
    low = line.lower().strip()
    if not low:
        return True
    if low in {"-", "•", "|"}:
        return True
    return any(re.search(pattern, low) for pattern in NOISE_PATTERNS)


def _is_metadata(line: str) -> bool:
    stripped = line.strip()
    low = stripped.lower()
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
    # "X covers ... for The Times / The Post / etc."
    if re.search(r"\bcovers?\s+.{5,}\s+for\s+the\s+\w+", low):
        return True
    # "X has covered ... presidents / administrations"
    if re.search(r"\bhas\s+(covered|reported|written|been\s+a\s+\w*\s*journalist)", low):
        return True
    # "X writes often on..." / "X has written X books"
    if re.search(r"\bwrites?\s+(often|regularly|frequently|about|on)\b", low):
        return True
    # "X has been a Times/Post journalist"
    if re.search(r"has\s+been\s+a\s+\w+\s+journalist", low):
        return True
    return False


def _is_end_of_article(line: str) -> bool:
    """Detect lines that signal end of article / start of related content."""
    low = line.lower().strip()
    return any(re.search(pattern, low) for pattern in END_OF_ARTICLE_PATTERNS)


def _is_nav_fragment(line: str) -> bool:
    """Detect short navigation-like fragments that aren't real paragraphs."""
    stripped = line.strip()
    words = stripped.split()
    # Very short lines (1-5 words) that don't end with a period are likely nav
    if len(words) <= 5 and not stripped.endswith((".","!","?",'"',"'")):
        return True
    return False


def clean_clip(raw_text: str) -> str:
    lines = raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized_lines = [_normalize(raw) for raw in lines]
    cleaned_lines: list[str] = []
    seen = set()
    for i, line in enumerate(normalized_lines):
        if not line:
            continue

        # Once we hit an end-of-article marker, stop collecting
        if _is_end_of_article(line):
            break

        # Look ahead for image caption detection
        next_line = normalized_lines[i + 1] if i + 1 < len(normalized_lines) else ""

        if _is_noise(line) or _is_metadata(line) or _is_image_caption(line, next_line) or _is_author_bio(line):
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

    return "\n\n".join(cleaned_lines).strip()


def validate_output(cleaned_text: str) -> tuple[bool, list[str]]:
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
    ]
    low = stripped.lower()
    for snippet in forbidden_snippets:
        if snippet in low:
            issues.append(f"Forbidden clutter found: '{snippet}'.")
            break

    if re.search(r"^\s*(headline|big headline)\s*:", stripped, flags=re.IGNORECASE | re.MULTILINE):
        issues.append("Headline marker remains in output.")

    return len(issues) == 0, issues


def _llm_prompt(raw_text: str, title: Optional[str] = None) -> str:
    title_instruction = ""
    if title:
        title_instruction = (
            f'\nIMPORTANT: The article headline is: "{title}". '
            "Remove this headline and any close variation of it from the output.\n"
        )
    return (
        "You clean messy pasted news text into clip-ready format.\n\n"
        f"{title_instruction}"
        "REMOVE all of the following:\n"
        "- The main article headline/title (the big title at the top)\n"
        "- Bylines, author names, author bios\n"
        "- Datelines (e.g. 'NEW DELHI, March 20 (Reuters) -')\n"
        "- Timestamps, publication dates\n"
        "- Image captions, photographer credits, photo credits\n"
        "- Advertisements, 'Read More' links, 'Recommended for you' blocks\n"
        "- Newsletter sign-ups, social media buttons, navigation elements\n"
        "- Related articles, trending sections, 'What to read next'\n"
        "- Summary bullet lists that appear before the article body\n\n"
        "KEEP all of the following:\n"
        "- All body paragraphs of the article\n"
        "- In-article section headers and subheadings (e.g. 'WORRY AMONG SOME JOURNALISTS', "
        "'THE BOTTOM LINE', 'WHAT HAPPENS NEXT', 'A New Approach'). "
        "These break the article into sections and MUST stay as standalone lines "
        "with blank lines around them. Do NOT remove or merge them.\n"
        "- Subtitles or ledes that appear right after the main title — keep them as the first line\n\n"
        "RULES:\n"
        "- Preserve the original text VERBATIM — do not paraphrase, summarize, or rewrite.\n"
        "- Output clean paragraphs separated by blank lines.\n"
        "- Only remove the main headline at the very top, nothing else that looks like a header.\n"
        "- Do NOT add any commentary like 'Here is the cleaned text.'\n\n"
        "Raw article text:\n"
        f"{raw_text}"
    )


def _post_process_llm(text: str, title: Optional[str] = None) -> str:
    """Clean up common LLM output issues — title removal, datelines, dedup."""
    lines = text.split("\n")
    cleaned = []
    seen = set()
    first_body = True

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # Preserve blank lines for paragraph separation
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue

        # Strip datelines from start of paragraphs
        line_clean = re.sub(
            r"^\s*[A-Z][A-Z\s,]+,\s*\w+\s+\d{1,2}\s*\([^)]+\)\s*-\s*",
            "", stripped
        ).strip()
        if not line_clean:
            continue

        # Remove title if it appears as first line (fuzzy match)
        if title and first_body:
            from difflib import SequenceMatcher
            t_norm = re.sub(r"[^\w\s]", "", title.lower()).strip()
            l_norm = re.sub(r"[^\w\s]", "", line_clean.lower()).strip()
            if t_norm and l_norm:
                ratio = SequenceMatcher(None, t_norm, l_norm).ratio()
                if ratio > 0.6 or t_norm in l_norm or l_norm in t_norm:
                    continue

        # Skip photo credits, author bios, first published lines
        low = line_clean.lower()
        if "photo credit" in low or "first published:" in low:
            continue
        if re.match(r"^(credit|photo)\s*[:\.]", low):
            continue
        # Skip standalone timestamps like "March 20, 2026, 3:55 p.m. ET"
        if re.match(r"^\w+\.?\s+\d{1,2},?\s+\d{4}", low) and len(line_clean.split()) <= 10:
            continue
        # Skip "Here is the cleaned" preamble
        if low.startswith("here is the cleaned"):
            continue

        # Paragraph dedup
        para_norm = re.sub(r"\s+", "", low)
        if para_norm in seen:
            continue
        seen.add(para_norm)

        cleaned.append(line_clean)
        first_body = False

    return "\n".join(cleaned).strip()


def clean_clip_llm_openai(raw_text: str, model: str, title: Optional[str] = None) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

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
        "https://api.openai.com/v1/responses",
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
        raise RuntimeError(f"OpenAI API HTTP {exc.code}: {detail}") from exc
    except Exception as exc:
        raise RuntimeError(f"OpenAI API request failed: {exc}") from exc

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
        raise RuntimeError("OpenAI API returned no text content.")
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
    parser.add_argument(
        "--mode",
        type=str,
        choices=["local", "llm"],
        default="local",
        help="Cleaning mode: 'local' (rule-based) or 'llm' (OpenAI API).",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gpt-5-mini",
        help="Model used in --mode llm (default: gpt-5-mini).",
    )
    parser.add_argument(
        "--fallback-local",
        action="store_true",
        help="If LLM mode fails validation/API call, fallback to local cleaner.",
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
        cleaned = clean_clip(raw)
    else:
        try:
            cleaned = clean_clip_llm_openai(raw, args.llm_model)
            ok, issues = validate_output(cleaned)
            if not ok:
                raise RuntimeError("LLM output validation failed: " + "; ".join(issues))
        except Exception as exc:
            if not args.fallback_local:
                raise
            print(f"[warn] LLM mode failed ({exc}); falling back to local mode.", file=sys.stderr)
            cleaned = clean_clip(raw)

    ok, issues = validate_output(cleaned)
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
