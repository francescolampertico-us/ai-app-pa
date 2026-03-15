import os
import json
import time
import hashlib
import urllib.parse
from datetime import datetime
import pandas as pd
import threading

OUTPUT_SCHEMAS = {
    "master_results": [
        "entity_query", "source", "record_type", "match_type", "match_confidence",
        "name_primary", "id_primary", "date_start", "date_end", "amount",
        "description", "url", "raw_ref"
    ],
    "lda_filings": [
        "filing_uuid", "registrant_id", "registrant_name", "client_id", "client_name",
        "filing_year", "filing_period", "filing_type", "amount_reported", "filing_url"
    ],
    "lda_issues": ["filing_uuid", "issue_code", "specific_issue"],
    "lda_lobbyists": ["filing_uuid", "lobbyist_name"],
    "fara_registrants": [
        "registration_number", "registrant_name", "address",
        "registration_date", "termination_date"
    ],
    "fara_foreign_principals": [
        "registration_number", "foreign_principal_name", "foreign_principal_date",
        "foreign_principal_term_date", "state_or_country"
    ],
    "fara_documents": [
        "registration_number", "document_url", "document_type", "document_date"
    ],
    "fara_short_forms": [
        "registration_number", "short_form_name"
    ]
}

class IOUtils:
    def __init__(self, out_dir: str, cache_dir: str, entities: list = None):
        # Generate clean folder name based on entity
        if not entities:
            folder_name = "Query_Results"
        elif len(entities) == 1:
            # Clean entity name for folder usage
            folder_name = "".join(c for c in entities[0] if c.isalnum() or c in (" ", "_", "-")).strip()
        else:
            folder_name = "Multiple_Entities"
            
        self.out_dir = os.path.join(out_dir, folder_name)
        self.cache_dir = cache_dir
        self.last_fara_call = 0.0
        self.fara_lock = threading.Lock()
        
        # Ensure directories exist
        os.makedirs(self.out_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Setup file paths
        self.raw_lda_path = os.path.join(self.out_dir, "lda_raw.jsonl")
        self.raw_fara_path = os.path.join(self.out_dir, "fara_raw.jsonl")
        self.logs_path = os.path.join(self.out_dir, "logs.txt")
        self.report_path = os.path.join(self.out_dir, "report.md")
        self.config_path = os.path.join(self.out_dir, "run_config.json")
        
        # In-memory datasets for CSV writing
        self.datasets = {
            "master_results": [],
            "lda_filings": [],
            "lda_entities": [],
            "lda_issues": [],
            "lda_lobbyists": [],
            "fara_registrants": [],
            "fara_foreign_principals": [],
            "fara_short_forms": [],
            "fara_documents": []
        }

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        with open(self.logs_path, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

    def get_cache_key(self, url: str, params: dict = None) -> str:
        """Create a unique cache filename based on URL and params."""
        key_dict = {"url": url}
        if params:
            key_dict["params"] = {k: str(v) for k, v in sorted(params.items())}
        key_str = json.dumps(key_dict, sort_keys=True)
        hashed = hashlib.md5(key_str.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed}.json")

    def read_cache(self, url: str, params: dict = None) -> dict:
        """Return cached JSON response if it exists."""
        cache_path = self.get_cache_key(url, params)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"Cache read error for {url}: {e}", "WARNING")
        return None

    def write_cache(self, url: str, params: dict, data: dict):
        """Save JSON response to cache."""
        cache_path = self.get_cache_key(url, params)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            self.log(f"Cache write error for {url}: {e}", "WARNING")

    def fara_throttle(self):
        """Enforce FARA API limit (5 requests / 10 seconds -> 2 seconds/req)."""
        with self.fara_lock:
            now = time.time()
            elapsed = now - self.last_fara_call
            if elapsed < 2.1:
                sleep_time = 2.1 - elapsed
                self.log(f"Throttling FARA: sleeping for {sleep_time:.2f}s", "DEBUG")
                time.sleep(sleep_time)
            self.last_fara_call = time.time()

    def lda_throttle(self, has_api_key: bool):
        """Enforce LDA API limit. (Anonymous is very low, authenticated is higher)"""
        # simplified throttle; could be improved based on response headers
        delay = 0.5 if has_api_key else 1.2
        time.sleep(delay)

    def append_raw_jsonl(self, source: str, data: dict):
        path = self.raw_lda_path if source.lower() == "lda" else self.raw_fara_path
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def append_row(self, table_name: str, row: dict):
        if table_name in self.datasets:
            self.datasets[table_name].append(row)
        else:
            self.log(f"Attempted to append to unknown table: {table_name}", "WARNING")

    def save_config(self, config: dict):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def write_csvs(self, dry_run: bool = False):
        """Flush all in-memory datasets to CSVs in the output directory. Skips empty tables unless dry_run=True."""
        self.log("Flushing datasets to CSV...")
        for table_name, rows in self.datasets.items():
            if not rows and not dry_run:
                continue # Do not write empty CSV files (unless dry-run)
                
            csv_path = os.path.join(self.out_dir, f"{table_name}.csv")
            
            if dry_run and not rows:
                cols = OUTPUT_SCHEMAS.get(table_name, [])
                df = pd.DataFrame(columns=cols)
            else:
                df = pd.DataFrame(rows)
                if table_name in OUTPUT_SCHEMAS:
                    cols = [c for c in OUTPUT_SCHEMAS[table_name] if c in df.columns]
                    extra_cols = [c for c in df.columns if c not in OUTPUT_SCHEMAS[table_name]]
                    df = df[cols + extra_cols]
                    
            df.to_csv(csv_path, index=False)
            self.log(f"Wrote {len(rows)} rows to {table_name}.csv", "INFO")
