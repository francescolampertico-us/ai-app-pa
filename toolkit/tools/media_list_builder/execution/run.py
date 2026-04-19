"""
Media List Builder — CLI Entry Point
======================================
Usage:
  python3 run.py --issue "AI safety regulation" [options]
  python3 run.py --broad-topic "health" --coverage-desk "health" --topic-mode broad [options]

Options:
  --issue TEXT           Policy issue to pitch
  --broad-topic TEXT     Broad topic to search across a desk or beat
  --coverage-desk TEXT   Desk or beat to emphasize (e.g. health, technology)
  --topic-mode TEXT      specific or broad (default: specific)
  --location TEXT        Geographic scope: US, state, city (default: US)
  --media-types TEXT     Comma-separated: mainstream,print,broadcast,digital,trade,podcast
  --num-contacts INT     Target number of contacts (default: 20)
  --out DIR              Output directory (default: ./output)
  --json                 Print result as JSON to stdout
"""

import argparse
import json
import sys
from pathlib import Path

from generator import generate_media_list, render_markdown
from export import export_xlsx


def main():
    parser = argparse.ArgumentParser(
        description="Generate a targeted media pitch list for a policy issue."
    )
    parser.add_argument("--issue", default="", help="Policy issue to pitch")
    parser.add_argument("--broad-topic", default="", dest="broad_topic", help="Broad topic to search")
    parser.add_argument("--coverage-desk", default="", dest="coverage_desk", help="Desk or beat to emphasize")
    parser.add_argument("--topic-mode", default="specific", dest="topic_mode", help="specific or broad")
    parser.add_argument("--location", default="US", help="Geographic scope (default: US)")
    parser.add_argument("--media-types", default=None, dest="media_types",
                        help="Comma-separated media types: mainstream,print,broadcast,digital,trade,podcast")
    parser.add_argument("--num-contacts", type=int, default=20, dest="num_contacts",
                        help="Target number of contacts (default: 20)")
    parser.add_argument("--out", default="./output", help="Output directory")
    parser.add_argument("--json", action="store_true", dest="json_out",
                        help="Print JSON result to stdout")

    args = parser.parse_args()

    # Parse media types
    media_types = None
    if args.media_types:
        media_types = [mt.strip().lower() for mt in args.media_types.split(",") if mt.strip()]

    # Run pipeline
    result = generate_media_list(
        issue=args.issue,
        location=args.location,
        media_types=media_types,
        num_contacts=args.num_contacts,
        broad_topic=args.broad_topic,
        coverage_desk=args.coverage_desk,
        topic_mode=args.topic_mode,
    )

    # Output
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Markdown
    md_text = render_markdown(result)
    md_path = out_dir / "media_list.md"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"Markdown report: {md_path}", file=sys.stderr)

    # Excel
    xlsx_path = out_dir / "media_list.xlsx"
    export_xlsx(result, str(xlsx_path))
    print(f"Excel report: {xlsx_path}", file=sys.stderr)

    # JSON output
    if args.json_out:
        json.dump(result, sys.stdout, indent=2)
    else:
        print(md_text)


if __name__ == "__main__":
    main()
