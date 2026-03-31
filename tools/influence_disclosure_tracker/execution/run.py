#!/usr/bin/env python3
import os
import argparse
from io_utils import IOUtils
from lda_client import LDAClient
from fara_client import FARAClient
from irs990_client import IRS990Client
from report import ReportGenerator

def parse_args():
    parser = argparse.ArgumentParser(description="Influence Disclosure Tracker Prototype")
    
    parser.add_argument("--entities", required=True, help="Comma-separated list of entities")
    parser.add_argument("--from", dest="from_date", default=None, help="Start date YYYY-MM-DD (optional)")
    parser.add_argument("--to", dest="to_date", default=None, help="End date YYYY-MM-DD (optional)")
    parser.add_argument("--filing-years", default=None, help="Comma-separated filing years (e.g. 2024,2025)")
    parser.add_argument("--filing-periods", default=None, help="Comma-separated quarters: Q1,Q2,Q3,Q4")
    parser.add_argument("--out", default="./output", help="Output base folder")
    parser.add_argument("--sources", default="lda,fara,irs990", help="Sources to scrape (comma-sep)")
    parser.add_argument("--mode", default="basic", choices=["basic", "deep"], help="Execution mode")
    parser.add_argument("--format", default="csv,md", help="Output formats")
    parser.add_argument("--lda-api-key", default=os.getenv("LDA_API_KEY"), help="LDA API Key")
    parser.add_argument("--fuzzy-threshold", type=float, default=85.0, help="Fuzzy match threshold")
    parser.add_argument("--max-results", type=int, default=500, help="Max results")
    parser.add_argument("--cache-dir", default=".cache/influence_disclosure_tracker", help="Cache dir")
    # --build-fara-index removed: FARA now uses bulk CSV downloads automatically
    parser.add_argument("--search-field", default="client", choices=["client", "registrant", "both"],
                        help="Search by client name, registrant (lobbying firm) name, or both")
    parser.add_argument("--debug", action="store_true", help="Debug logging")
    parser.add_argument("--dry-run", action="store_true", help="Print configs, create folders, do not execute API")
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    entities = [e.strip() for e in args.entities.split(",") if e.strip()]
    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    
    io = IOUtils(args.out, args.cache_dir, entities=entities)
    log_level = "DEBUG" if args.debug else "INFO"
    io.log(f"Starting Influence Disclosure Tracker (Log Level: {log_level})", log_level)

    formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]

    filing_years = [int(y.strip()) for y in args.filing_years.split(",") if y.strip()] if args.filing_years else None
    filing_periods = [p.strip() for p in args.filing_periods.split(",") if p.strip()] if args.filing_periods else None

    config = {
        "entities": entities,
        "from_date": args.from_date or "",
        "to_date": args.to_date or "",
        "filing_years": filing_years,
        "filing_periods": filing_periods,
        "sources": sources,
        "mode": args.mode,
        "search_field": args.search_field,
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
        lda_client = LDAClient(io, api_key=args.lda_api_key, fuzzy_threshold=args.fuzzy_threshold,
                               max_results=args.max_results, search_field=args.search_field)
        years_to_search = filing_years or [None]
        for ent in entities:
            for year in years_to_search:
                lda_client.search_entity(
                    ent,
                    args.from_date or "",
                    args.to_date or "",
                    filing_year=year,
                    filing_periods=filing_periods,
                )
            
    # 2. FARA
    if "fara" in sources:
        fara_client = FARAClient(io, fuzzy_threshold=args.fuzzy_threshold, max_results=args.max_results)
        for ent in entities:
            fara_client.search_entity(ent, args.from_date or "", args.to_date or "")
            
    # 3. IRS 990
    if "irs990" in sources:
        irs990_client = IRS990Client(io, fuzzy_threshold=args.fuzzy_threshold,
                                     max_results=args.max_results, mode=args.mode,
                                     filing_years=filing_years)
        for ent in entities:
            irs990_client.search_entity(ent, args.from_date or "", args.to_date or "")
            
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
