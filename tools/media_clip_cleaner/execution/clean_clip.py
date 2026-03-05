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
    r"^\s*photo\s*:",
    r"^\s*image\s*:",
    r"^\s*share\s*$",
    r"^\s*live\s+video\s*$",
    r"^\s*article\s+body\s+starts\.{0,3}\s*$",
]

METADATA_PATTERNS = [
    r"^\s*by\s+[a-z].*",
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    r"\b\d{4}\b",
    r"\bupdated\b",
    r"\bpublished\b",
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
    low = line.lower().strip()
    if re.match(r"^\s*(byline|author)\s*:", low):
        return True
    if " • " in low and re.search(r"\bby\b", low):
        return True
    return any(re.search(pattern, low) for pattern in METADATA_PATTERNS)


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
    return is_shouty or (len(words) <= 12 and not stripped.endswith(".") and stripped.istitle())


def _extract_subtitle(line: str) -> Optional[str]:
    m = re.match(r"^\s*(subtitle|lede|deck)\s*:\s*(.+)$", line, flags=re.IGNORECASE)
    if m:
        return _normalize(m.group(2))
    return None


def clean_clip(raw_text: str) -> str:
    lines = raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    subtitle = None
    cleaned_lines: list[str] = []
    seen = set()

    for raw in lines:
        line = _normalize(raw)
        if not line:
            continue

        explicit_subtitle = _extract_subtitle(line)
        if explicit_subtitle:
            subtitle = explicit_subtitle
            continue

        if _is_noise(line) or _is_metadata(line) or _is_headline(line):
            continue

        # Strip common bracket wrappers left by copied snippets.
        line = re.sub(r"^\[(.*?)\]$", r"\1", line).strip()
        if not line:
            continue
        if _is_noise(line):
            continue

        key = re.sub(r"\W+", "", line.lower())
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned_lines.append(line)

    if subtitle:
        body = "\n\n".join(cleaned_lines)
        return f"*{subtitle}*\n\n{body}".strip()
    return "\n\n".join(cleaned_lines).strip()


def validate_output(cleaned_text: str) -> tuple[bool, list[str]]:
    issues = []
    stripped = cleaned_text.strip()
    if not stripped:
        issues.append("Output is empty.")
        return False, issues

    first_line = stripped.splitlines()[0].strip()
    if not (first_line.startswith("*") and first_line.endswith("*") and len(first_line) > 2):
        issues.append("Output does not start with an italicized subtitle/lede.")

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


def _llm_prompt(raw_text: str) -> str:
    return (
        "You clean messy pasted news text into clip-ready markdown.\n"
        "Output requirements:\n"
        "1) First line must be ONLY the subtitle/lede in italics using markdown: *...*\n"
        "2) Remove the main headline/title\n"
        "3) Remove navigation/footer/UI clutter, ads, newsletter prompts, social/share blocks, comment counters\n"
        "4) Remove timestamps, publication dates, image/photo credits, bylines\n"
        "5) Keep the full article body in clean paragraphs (non-italic)\n"
        "6) Do not add any prefacing text\n"
        "7) If no clear subtitle exists, use the first meaningful summary sentence as italic first line\n\n"
        "Raw article text:\n"
        f"{raw_text}"
    )


def clean_clip_llm_openai(raw_text: str, model: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": _llm_prompt(raw_text)},
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
    return text


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
