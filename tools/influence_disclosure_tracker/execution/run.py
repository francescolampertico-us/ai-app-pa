#!/usr/bin/env python3
import os
import argparse
from datetime import datetime

from io_utils import IOUtils
from lda_client import LDAClient
from fara_client import FARAClient
from report import ReportGenerator

def parse_args():
    parser = argparse.ArgumentParser(description="Influence Disclosure Tracker Prototype")
    
    parser.add_argument("--entities", required=True, help="Comma-separated list of entities")
    parser.add_argument("--from", dest="from_date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--out", default="./output", help="Output base folder")
    parser.add_argument("--sources", default="lda,fara", help="Sources to scrape (comma-sep)")
    parser.add_argument("--format", default="csv,md", help="Output formats")
    parser.add_argument("--lda-api-key", default=os.getenv("LDA_API_KEY"), help="LDA API Key")
    parser.add_argument("--fuzzy-threshold", type=float, default=85.0, help="Fuzzy match threshold")
    parser.add_argument("--max-results", type=int, default=500, help="Max results")
    parser.add_argument("--cache-dir", default=".cache/influence_disclosure_tracker", help="Cache dir")
    parser.add_argument("--build-fara-index", action="store_true",
                        help="One-time build of local FARA FP index (slow, ~20min). Required before FARA queries.")
    parser.add_argument("--debug", action="store_true", help="Debug logging")
    parser.add_argument("--dry-run", action="store_true", help="Print configs, create folders, do not execute API")
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    entities = [e.strip() for e in args.entities.split(",") if e.strip()]
    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    io = IOUtils(args.out, args.cache_dir, entities=entities)
    log_level = "DEBUG" if args.debug else "INFO"
    io.log(f"Starting Influence Disclosure Tracker (Log Level: {log_level})", log_level)
    
    formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
    
    config = {
        "entities": entities,
        "from_date": args.from_date,
        "to_date": args.to_date,
        "sources": sources,
        "fuzzy_threshold": args.fuzzy_threshold,
        "max_results": args.max_results,
        "formats": formats,
        "dry_run": args.dry_run
    }
    io.save_config(config)

    if args.dry_run:
        io.log("DRY RUN: generating empty datasets (if CSV format active) and bypassing API calls.", log_level)
        if "csv" in formats:
            io.write_csvs(dry_run=True)
        if "md" in formats:
            ReportGenerator(io, config).generate()
        return

    # 1. LDA
    if "lda" in sources:
        lda_client = LDAClient(io, api_key=args.lda_api_key, fuzzy_threshold=args.fuzzy_threshold, max_results=args.max_results)
        for ent in entities:
            lda_client.search_entity(ent, args.from_date, args.to_date)
            
    # 2. FARA
    if "fara" in sources:
        fara_client = FARAClient(io, fuzzy_threshold=args.fuzzy_threshold, max_results=args.max_results)
        if args.build_fara_index:
            fara_client.build_index()
        elif not fara_client.index_exists():
            io.log(
                "FARA index not found. Run once with --build-fara-index to enable FARA searches. Skipping FARA.",
                "WARNING"
            )
        else:
            for ent in entities:
                fara_client.search_entity(ent, args.from_date, args.to_date)
            
    # Write flat files
    if "csv" in formats:
        io.write_csvs(dry_run=False)
    
    # Generate report
    if "md" in formats:
        report_gen = ReportGenerator(io, config)
        report_gen.generate()
    
    io.log("Run completed successfully.", "INFO")

if __name__ == "__main__":
    main()
