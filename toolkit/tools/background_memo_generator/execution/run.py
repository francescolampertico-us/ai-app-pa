"""
Background Memo Generator — CLI entry point

Usage:
  python run.py --subject "Jagello 2000" \
                --sections "Jagello 2000" "Zbyněk Pavlačík" "Tomáš Pojar" \
                --out output/jagello_memo.docx

  python run.py --subject "Czechoslovak Group" \
                --sections "Corporate Profile" "Defense Sectors" "U.S. Operations" \
                --context "Focus on U.S. acquisitions and defense contracts."
"""

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from generator import generate_memo, render_markdown
from export import export_docx
from schema import BackgroundMemoResult


def main():
    parser = argparse.ArgumentParser(description="Generate a background memo as DOCX and markdown.")
    parser.add_argument("--subject", required=True,
                        help="Name of the client, organization, issue, or person.")
    parser.add_argument("--sections", nargs="+", required=True,
                        help="Section headings (space-separated). Enclose multi-word headings in quotes.")
    parser.add_argument("--context", default="",
                        help="Optional additional context to guide content generation.")
    parser.add_argument("--date", default="",
                        help="Memo date string (default: today). Example: 'April 1, 2026'")
    parser.add_argument("--out", default="",
                        help="Output DOCX path (default: output/<subject>_background_memo.docx)")
    parser.add_argument("--md-out", default="",
                        help="Output markdown path (optional)")

    args = parser.parse_args()

    # Determine output path
    if args.out:
        out_path = Path(args.out)
    else:
        safe_name = args.subject.lower().replace(" ", "_").replace("/", "_")[:40]
        out_path = Path("output") / f"{safe_name}_background_memo.docx"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    memo_date = args.date or date.today().strftime("%B %d, %Y")

    # Generate → validate → render/export
    raw = generate_memo(
        subject=args.subject,
        sections=args.sections,
        context=args.context,
    )
    memo = BackgroundMemoResult(**raw)  # explicit schema construction before render/export

    # Export DOCX
    export_docx(memo, str(out_path), memo_date=memo_date)
    print(f"DOCX saved: {out_path}")

    # Export markdown
    md_text = render_markdown(memo, memo_date=memo_date)
    if args.md_out:
        md_path = Path(args.md_out)
    else:
        md_path = out_path.with_suffix(".md")
    md_path.write_text(md_text, encoding="utf-8")
    print(f"Markdown saved: {md_path}")


if __name__ == "__main__":
    main()
