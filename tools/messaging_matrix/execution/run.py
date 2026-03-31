"""
Messaging Matrix — CLI Entry Point
=====================================
Usage:
  python3 run.py --position "Support the AI Safety Act" [options]

Options:
  --position TEXT         Core policy position (required)
  --context TEXT          Supporting context (bill summary, hearing excerpt, etc.)
  --context-file PATH    Read context from a file instead
  --organization TEXT     Organization name for attribution
  --audience TEXT         Primary target audience
  --core-messages TEXT    Pre-defined core messages (optional, skips LLM generation)
  --facts TEXT            Supporting facts / proof points (optional)
  --variants LIST        Comma-separated variant IDs (default: all)
  --style-guides-dir DIR Path to style_guides/ directory for style injection
  --out DIR              Output directory (default: ./output)
  --json                 Print result as JSON to stdout
"""

import argparse
import json
import sys
from pathlib import Path

from generator import generate_matrix, render_markdown
from export import export_docx


def main():
    parser = argparse.ArgumentParser(
        description="Generate a messaging matrix from a policy position."
    )
    parser.add_argument("--position", required=True, help="Core policy position")
    parser.add_argument("--context", default="", help="Supporting context text")
    parser.add_argument("--context-file", default=None, help="Read context from file")
    parser.add_argument("--organization", default="", help="Organization name")
    parser.add_argument("--audience", default="", help="Primary target audience")
    parser.add_argument("--core-messages", default="", dest="core_messages",
                        help="Pre-defined core messages (optional)")
    parser.add_argument("--facts", default="", help="Supporting facts / proof points (optional)")
    parser.add_argument("--variants", default=None,
                        help="Comma-separated variant IDs (talking_points,media_talking_points,news_release,social_media,grassroots_email,op_ed,speech_draft)")
    parser.add_argument("--style-guides-dir", default="", dest="style_guides_dir",
                        help="Path to style_guides/ directory for style injection")
    parser.add_argument("--out", default="./output", help="Output directory")
    parser.add_argument("--json", action="store_true", dest="json_out",
                        help="Print JSON result to stdout")

    args = parser.parse_args()

    # Load context from file if specified
    context = args.context
    if args.context_file:
        context = Path(args.context_file).read_text(encoding="utf-8")

    # Parse variants
    variants = None
    if args.variants:
        variants = [v.strip() for v in args.variants.split(",") if v.strip()]

    # Run pipeline
    result = generate_matrix(
        position=args.position,
        context=context,
        organization=args.organization,
        target_audience=args.audience,
        core_messages=args.core_messages,
        facts=args.facts,
        variants=variants,
        style_guides_dir=args.style_guides_dir,
    )

    # Output
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Markdown
    md_text = render_markdown(result)
    md_path = out_dir / "messaging_matrix.md"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"Markdown report: {md_path}", file=sys.stderr)

    # DOCX
    docx_path = out_dir / "messaging_matrix.docx"
    export_docx(result, str(docx_path))
    print(f"DOCX report: {docx_path}", file=sys.stderr)

    # JSON output
    if args.json_out:
        json.dump(result, sys.stdout, indent=2)
    else:
        print(md_text)


if __name__ == "__main__":
    main()
