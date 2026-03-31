"""
Stakeholder Briefing — CLI Entry Point
========================================
Usage:
  python3 run.py --name "Sen. Maria Cantwell" --purpose "Discuss AI Safety Act" [options]

Options:
  --name TEXT              Stakeholder name (required)
  --purpose TEXT           Meeting purpose (required)
  --organization TEXT      Stakeholder's organization
  --your-org TEXT          Your organization
  --context TEXT           Additional context text
  --context-file PATH     Read context from a file
  --no-disclosures        Skip disclosure search
  --no-news               Skip news fetch
  --out DIR               Output directory (default: ./output)
  --json                  Print result as JSON to stdout
"""

import argparse
import json
import sys
from pathlib import Path

from generator import generate_briefing, render_markdown
from export import export_docx


def main():
    parser = argparse.ArgumentParser(
        description="Generate a pre-meeting stakeholder briefing."
    )
    parser.add_argument("--name", required=True, help="Stakeholder name")
    parser.add_argument("--purpose", required=True, help="Meeting purpose")
    parser.add_argument("--organization", default="", help="Stakeholder's organization")
    parser.add_argument("--your-org", default="", dest="your_org", help="Your organization")
    parser.add_argument("--context", default="", help="Additional context text")
    parser.add_argument("--context-file", default=None, dest="context_file",
                        help="Read context from file")
    parser.add_argument("--no-disclosures", action="store_true", dest="no_disclosures",
                        help="Skip disclosure search")
    parser.add_argument("--no-news", action="store_true", dest="no_news",
                        help="Skip news fetch")
    parser.add_argument("--out", default="./output", help="Output directory")
    parser.add_argument("--json", action="store_true", dest="json_out",
                        help="Print JSON result to stdout")

    args = parser.parse_args()

    # Load context from file if specified
    context = args.context
    if args.context_file:
        context = Path(args.context_file).read_text(encoding="utf-8")

    # Run pipeline
    result = generate_briefing(
        stakeholder_name=args.name,
        meeting_purpose=args.purpose,
        organization=args.organization,
        your_organization=args.your_org,
        context=context,
        include_disclosures=not args.no_disclosures,
        include_news=not args.no_news,
    )

    # Output
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Markdown
    md_text = render_markdown(result)
    md_path = out_dir / "stakeholder_briefing.md"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"Markdown report: {md_path}", file=sys.stderr)

    # DOCX
    docx_path = out_dir / "stakeholder_briefing.docx"
    export_docx(result, str(docx_path))
    print(f"DOCX report: {docx_path}", file=sys.stderr)

    # JSON output
    if args.json_out:
        json.dump(result, sys.stdout, indent=2)
    else:
        print(md_text)


if __name__ == "__main__":
    main()
