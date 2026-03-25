#!/usr/bin/env python3
"""
Legislative Tracker — CLI Entry Point
=======================================
Search, track, and summarize legislation via the LegiScan API.

Usage:
    # Search for bills
    python3 run.py --query "artificial intelligence" --state US --year 2026

    # Get bill detail + AI summary
    python3 run.py --bill-id 1234567 --summarize

    # Manage watchlist
    python3 run.py --watchlist add --bill-id 1234567
    python3 run.py --watchlist list
    python3 run.py --watchlist refresh
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

from legiscan_client import LegiScanClient
from watchlist import WatchlistManager
from summarize import summarize_bill, format_bill_header
from report import ReportGenerator


def parse_args():
    parser = argparse.ArgumentParser(
        description="Legislative Tracker — Search, track, and summarize legislation"
    )

    # Search mode
    parser.add_argument("--query", help="Search keywords (e.g., 'artificial intelligence')")
    parser.add_argument("--state", default="US",
                        help="Two-letter state code, 'US' for federal, 'ALL' for all (default: US)")
    parser.add_argument("--year", type=int, default=None, help="Legislative session year")

    # Bill detail mode
    parser.add_argument("--bill-id", type=int, default=None, help="LegiScan bill ID for detail/summary")
    parser.add_argument("--summarize", action="store_true", help="Generate AI summary for the bill")

    # Watchlist mode
    parser.add_argument("--watchlist", choices=["add", "remove", "list", "refresh"],
                        help="Watchlist action: add, remove, list, or refresh")

    # Output
    parser.add_argument("--out", default="./output", help="Output directory (default: ./output)")
    parser.add_argument("--cache-dir", default=".cache", help="Cache directory (default: .cache)")

    # Options
    parser.add_argument("--model", default=None, help="OpenAI model for summarization (default: gpt-4o-mini)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON to stdout")

    return parser.parse_args()


def log(msg: str):
    """Print a timestamped log message to stderr."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr)


def cmd_search(client: LegiScanClient, args):
    """Search for bills and output results."""
    log(f"Searching for '{args.query}' in {args.state}...")
    results = client.search_bills(args.query, state=args.state, year=args.year)
    log(f"Found {len(results)} bills.")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = out_dir / "search_results.json"
    json_path.write_text(json.dumps(results, indent=2))
    log(f"Results saved to {json_path}")

    # Save report
    report = ReportGenerator.search_report(args.query, args.state, args.year, results)
    report_path = out_dir / "report.md"
    report_path.write_text(report)
    log(f"Report saved to {report_path}")

    if args.json_output:
        print(json.dumps(results, indent=2))
    else:
        # Print summary table to stdout
        print(f"\nFound {len(results)} bills for '{args.query}' ({args.state}):\n")
        for i, bill in enumerate(results[:20], 1):
            title = bill["title"][:60] + "..." if len(bill["title"]) > 60 else bill["title"]
            print(f"  {i:2d}. [{bill['state']}] {bill['number']} — {title}")
            print(f"      Status: {bill['status']} | Last: {bill['last_action_date']}")
            print(f"      ID: {bill['bill_id']} | {bill['url']}")
            print()
        if len(results) > 20:
            print(f"  ... and {len(results) - 20} more (see {json_path})")

    return results


def cmd_bill_detail(client: LegiScanClient, args):
    """Get bill detail and optionally generate AI summary."""
    log(f"Fetching bill detail for ID {args.bill_id}...")
    bill = client.get_bill(args.bill_id)
    log(f"Got: {bill['number']} — {bill['title'][:60]}")

    out_dir = Path(args.out) / bill["number"].replace(" ", "_")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save bill detail
    detail_path = out_dir / "bill_detail.json"
    detail_path.write_text(json.dumps(bill, indent=2))

    if args.summarize:
        # Get bill text
        bill_text = ""
        if bill.get("texts"):
            doc_id = bill["texts"][0]["doc_id"]
            log(f"Fetching bill text (doc_id: {doc_id})...")
            bill_text = client.get_bill_text(doc_id)

        if not bill_text:
            log("WARNING: No bill text available. Summarizing from metadata only.")
            bill_text = f"[Full text not available. Bill description: {bill.get('description', 'N/A')}]"

        log(f"Generating AI summary ({len(bill_text)} chars of bill text)...")
        header = format_bill_header(bill)
        summary = summarize_bill(bill, bill_text, model=args.model)
        report = ReportGenerator.bill_summary_report(bill, header, summary)

        summary_path = out_dir / "bill_summary.md"
        summary_path.write_text(report)
        log(f"Summary saved to {summary_path}")

        if not args.json_output:
            print(report)
        else:
            print(json.dumps({"bill": bill, "summary": summary}, indent=2))
    else:
        if args.json_output:
            print(json.dumps(bill, indent=2))
        else:
            print(f"\n{bill['number']} — {bill['title']}")
            print(f"State: {bill['state']} | Status: {bill['status']}")
            print(f"Last Action: {bill['last_action']} ({bill['last_action_date']})")
            print(f"Sponsors: {', '.join(s['name'] for s in bill.get('sponsors', []))}")
            print(f"\nUse --summarize to generate an AI analysis.")

    return bill


def cmd_watchlist(client: LegiScanClient, wl: WatchlistManager, args):
    """Manage the bill watchlist."""
    if args.watchlist == "add":
        if not args.bill_id:
            print("ERROR: --bill-id required for watchlist add", file=sys.stderr)
            sys.exit(1)
        bill = client.get_bill(args.bill_id)
        added = wl.add(args.bill_id, bill)
        if added:
            log(f"Added {bill['number']} to watchlist.")
            print(f"Added: {bill['number']} — {bill['title']}")
        else:
            print(f"Already tracked: {bill['number']}")

    elif args.watchlist == "remove":
        if not args.bill_id:
            print("ERROR: --bill-id required for watchlist remove", file=sys.stderr)
            sys.exit(1)
        removed = wl.remove(args.bill_id)
        if removed:
            print(f"Removed bill {args.bill_id} from watchlist.")
        else:
            print(f"Bill {args.bill_id} not found in watchlist.")

    elif args.watchlist == "list":
        bills = wl.list_bills()
        if args.json_output:
            print(json.dumps(bills, indent=2))
        else:
            report = ReportGenerator.watchlist_report(bills)
            print(report)

            out_dir = Path(args.out)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "watchlist_report.md").write_text(report)

    elif args.watchlist == "refresh":
        log("Refreshing watchlist status...")
        results = wl.refresh_all(client)
        changed = [r for r in results if r.get("changed")]
        log(f"Checked {len(results)} bills. {len(changed)} changed.")

        bills = wl.list_bills()
        if args.json_output:
            print(json.dumps({"refresh_results": results, "watchlist": bills}, indent=2))
        else:
            report = ReportGenerator.watchlist_report(bills, refresh_results=results)
            print(report)

            out_dir = Path(args.out)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "watchlist_report.md").write_text(report)


def main():
    args = parse_args()

    # Validate: need at least one action
    if not args.query and not args.bill_id and not args.watchlist:
        print("ERROR: Specify --query, --bill-id, or --watchlist. Use --help for usage.",
              file=sys.stderr)
        sys.exit(1)

    cache_dir = Path(args.cache_dir)
    wl = WatchlistManager(watchlist_path=str(cache_dir / "watchlist.json"))

    # Watchlist list/remove don't need the API client
    if args.watchlist in ("list", "remove"):
        # Create a dummy client only if refresh needs it
        cmd_watchlist(None, wl, args)
        return

    client = LegiScanClient(cache_dir=str(cache_dir))

    if args.watchlist:
        cmd_watchlist(client, wl, args)
    elif args.bill_id:
        cmd_bill_detail(client, args)
    elif args.query:
        cmd_search(client, args)


if __name__ == "__main__":
    main()
