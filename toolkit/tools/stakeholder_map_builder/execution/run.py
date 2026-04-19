"""
Stakeholder Map — CLI Entry Point
=================================
Usage:
  python3 execution/run.py --policy_issue "artificial intelligence regulation"
  python3 execution/run.py --policy_issue "clean energy tax credits" --scope state --state TX
  python3 execution/run.py --help
"""

import argparse
import json
import sys
from pathlib import Path

# Load .env from toolkit root
try:
    from dotenv import load_dotenv
    _toolkit_root = Path(__file__).resolve().parent.parent.parent.parent
    load_dotenv(_toolkit_root / ".env")
except ImportError:
    pass


def main():
    parser = argparse.ArgumentParser(
        description="Build a stakeholder map for a policy issue.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 execution/run.py --policy_issue "AI regulation"
  python3 execution/run.py --policy_issue "clean energy" --scope state --state TX
  python3 execution/run.py --policy_issue "drug pricing" --out ./output
        """,
    )
    parser.add_argument(
        "--policy_issue", required=True,
        help="The policy issue to map (e.g., 'artificial intelligence regulation')",
    )
    parser.add_argument(
        "--scope", default="federal", choices=["federal", "state"],
        help="Federal or state scope (default: federal)",
    )
    parser.add_argument(
        "--state", default="US",
        help="Two-letter state code (only used when --scope state, e.g., TX, CA)",
    )
    parser.add_argument(
        "--include_types", nargs="+",
        choices=["legislators", "lobbyists", "corporations", "nonprofits"],
        default=None,
        help="Actor types to include (default: all types)",
    )
    parser.add_argument(
        "--out", default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--no_graph", action="store_true",
        help="Skip HTML graph export (faster, no plotly/networkx required)",
    )
    args = parser.parse_args()

    # Set up output directory
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Validate state scope
    if args.scope == "state" and args.state == "US":
        print("Warning: --scope state requires --state <2-letter code>. Defaulting to TX.", file=sys.stderr)
        args.state = "TX"

    print(f"\nBuilding stakeholder map for: '{args.policy_issue}'", file=sys.stderr)
    print(f"Scope: {args.scope.title()}{' (' + args.state + ')' if args.scope == 'state' else ''}", file=sys.stderr)
    print("", file=sys.stderr)

    # Add execution dir to path
    exec_dir = Path(__file__).resolve().parent
    if str(exec_dir) not in sys.path:
        sys.path.insert(0, str(exec_dir))

    from generator import build_map, render_markdown
    from export import export_xlsx, export_docx

    try:
        result = build_map(
            policy_issue=args.policy_issue,
            scope=args.scope,
            state=args.state,
            include_types=args.include_types,
        )
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    actors = result.get("actors", [])
    rels   = result.get("relationships", [])
    stances = {s: sum(1 for a in actors if a.get("stance") == s)
               for s in ("proponent", "opponent", "neutral", "unknown")}

    print(f"\nResults: {len(actors)} actors, {len(rels)} relationships", file=sys.stderr)
    print(f"  Proponents: {stances['proponent']}", file=sys.stderr)
    print(f"  Opponents:  {stances['opponent']}", file=sys.stderr)
    print(f"  Neutral:    {stances['neutral']}", file=sys.stderr)
    print(f"  Unknown:    {stances['unknown']}", file=sys.stderr)
    print("", file=sys.stderr)

    # Export Markdown
    md_path = out_dir / "stakeholder_map.md"
    md_path.write_text(render_markdown(result), encoding="utf-8")
    print(f"Markdown → {md_path}", file=sys.stderr)

    # Export JSON
    json_path = out_dir / "stakeholder_map.json"
    json_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"JSON     → {json_path}", file=sys.stderr)

    # Export Excel
    try:
        xlsx_path = out_dir / "stakeholder_map.xlsx"
        export_xlsx(result, str(xlsx_path))
        print(f"Excel    → {xlsx_path}", file=sys.stderr)
    except ImportError:
        print("Excel export skipped (openpyxl not installed: pip install openpyxl)", file=sys.stderr)

    # Export DOCX
    try:
        docx_path = out_dir / "stakeholder_map.docx"
        export_docx(result, str(docx_path))
        print(f"DOCX     → {docx_path}", file=sys.stderr)
    except ImportError:
        print("DOCX export skipped (python-docx not installed: pip install python-docx)", file=sys.stderr)

    # Export HTML graph
    if not args.no_graph:
        try:
            from graph import build_network_graph, save_graph_html
            fig = build_network_graph(
                actors=actors,
                relationships=rels,
                title=f"Stakeholder Map: {args.policy_issue}",
            )
            html_path = out_dir / "stakeholder_map.html"
            save_graph_html(fig, str(html_path))
            print(f"Graph    → {html_path}", file=sys.stderr)
        except ImportError as e:
            print(f"Graph export skipped ({e}). Install: pip install networkx plotly", file=sys.stderr)

    print("\nDone.", file=sys.stderr)
    return result


if __name__ == "__main__":
    main()
