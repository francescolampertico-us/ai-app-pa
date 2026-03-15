import os
import json
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io_utils import IOUtils
from matching import match_entity

DEFAULT_INDEX_PATH = os.path.join(os.path.dirname(__file__), ".cache", "fara_fp_index.jsonl")
DEFAULT_REG_INDEX_PATH = os.path.join(os.path.dirname(__file__), ".cache", "fara_reg_index.jsonl")


class FARAClient:
    BASE_URL = "https://efile.fara.gov/api/v1/"

    def __init__(self, io_utils: IOUtils, fuzzy_threshold: float = 85.0,
                 fp_index_path: str = DEFAULT_INDEX_PATH,
                 reg_index_path: str = DEFAULT_REG_INDEX_PATH,
                 max_results: int = 500):
        self.io = io_utils
        self.fuzzy_threshold = fuzzy_threshold
        self.max_results = max_results
        self.fp_index_path = fp_index_path
        self.reg_index_path = reg_index_path

        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        os.makedirs(os.path.dirname(self.fp_index_path), exist_ok=True)

    # -------------------------------------------------------------------------
    # LOW-LEVEL HELPERS
    # -------------------------------------------------------------------------

    def fetch_raw(self, endpoint: str) -> dict:
        """Throttled + cached GET. Returns the raw API dict, or {} on failure."""
        url = f"{self.BASE_URL}{endpoint}"
        cached = self.io.read_cache(url)
        if cached is not None and isinstance(cached, dict):
            self.io.log(f"FARA Cache Hit: {url}", "DEBUG")
            return cached
        # Either cache miss or bad cache entry — do a live fetch
        self.io.fara_throttle()
        self.io.log(f"Fetching FARA: {url}", "INFO")
        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict):
                self.io.write_cache(url, None, data)
                return data
            return {}
        except Exception as e:
            self.io.log(f"FARA fetch error {url}: {e}", "ERROR")
            return {}

    def _extract_registrant_rows(self, data: dict, top_key: str) -> list:
        """
        Registrant list structure:
        {top_key: {"ROW": [...] or {...}}}
        """
        if not isinstance(data, dict):
            return []
        inner = data.get(top_key, {})
        if not isinstance(inner, dict):
            return []
        rows = inner.get("ROW", [])
        if isinstance(rows, dict):
            return [rows]
        return rows if isinstance(rows, list) else []

    def _extract_fp_rows(self, data: dict) -> list:
        """
        FP structure:
        {"ROWSET": {"ROW": [...] or {...}}}
        Always returns list of fp dicts.
        """
        if not isinstance(data, dict):
            return []
        rowset = data.get("ROWSET", {})
        if not isinstance(rowset, dict):
            return []
        rows = rowset.get("ROW", [])
        if isinstance(rows, dict):
            return [rows]
        return rows if isinstance(rows, list) else []

    # -------------------------------------------------------------------------
    # INDEX BUILDING (run once, slow ~5-20 min first time)
    # -------------------------------------------------------------------------

    def build_index(self):
        """
        One-time bulk download of all FARA active registrant FP data.
        Saves two JSONL index files. After this, all queries are <1s.
        """
        self.io.log("=== BUILDING FARA INDEX ===", "INFO")
        self.io.log("First-time build may take ~5-20 min. Future queries will be instant.", "INFO")

        active_regs = self._extract_registrant_rows(
            self.fetch_raw("Registrants/json/Active"), "REGISTRANTS_ACTIVE"
        )
        term_regs = self._extract_registrant_rows(
            self.fetch_raw("Registrants/json/Terminated"), "REGISTRANTS_TERMINATED"
        )
        all_regs = active_regs + term_regs
        self.io.log(f"Total registrants: {len(all_regs)} ({len(active_regs)} active, {len(term_regs)} terminated)", "INFO")

        with open(self.reg_index_path, "w", encoding="utf-8") as rf:
            for reg in all_regs:
                rf.write(json.dumps(reg) + "\n")
        self.io.log(f"Registrant index: {self.reg_index_path} ({len(all_regs)} records)", "INFO")

        # FP scan — active registrants only (practical scope)
        active_regnums = [
            str(r.get("Registration_Number", ""))
            for r in active_regs if r.get("Registration_Number")
        ]
        self.io.log(f"Scanning {len(active_regnums)} active registrants for FP data...", "INFO")

        total_fps = 0
        with open(self.fp_index_path, "w", encoding="utf-8") as ff:
            for i, r_num in enumerate(active_regnums):
                fp_data = self.fetch_raw(f"ForeignPrincipals/json/Active/{r_num}")
                fps = self._extract_fp_rows(fp_data)
                for fp in fps:
                    if not isinstance(fp, dict):
                        continue
                    fp["_registration_number"] = r_num
                    ff.write(json.dumps(fp) + "\n")
                    total_fps += 1
                if (i + 1) % 50 == 0:
                    self.io.log(f"  {i+1}/{len(active_regnums)} registrants | {total_fps} FPs indexed", "INFO")

        self.io.log(f"FP index: {self.fp_index_path} ({total_fps} records)", "INFO")
        self.io.log("=== FARA INDEX BUILD COMPLETE ===", "INFO")

    def index_exists(self) -> bool:
        return os.path.exists(self.fp_index_path) and os.path.exists(self.reg_index_path)

    # -------------------------------------------------------------------------
    # FAST QUERY (milliseconds — reads local index files)
    # -------------------------------------------------------------------------

    def search_entity(self, entity_query: str, date_from: str, date_to: str):
        if self.index_exists():
            self._search_index_mode(entity_query, date_from, date_to)
        else:
            self._search_ondemand_mode(entity_query, date_from, date_to)

    def _is_within_date_range(self, doc_date_raw: str, date_from: str, date_to: str) -> bool:
        if not doc_date_raw:
            return True
        if "T" in doc_date_raw:
            date_part = doc_date_raw.split("T")[0]
        elif "/" in doc_date_raw:
            parts = doc_date_raw.split("/")
            if len(parts) == 3:
                date_part = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
            else:
                return True
        else:
            date_part = doc_date_raw[:10]
        return date_from <= date_part <= date_to

    def _search_ondemand_mode(self, entity_query: str, date_from: str, date_to: str):
        self.io.log(f"FARA index not found. Using fast On-Demand Mode for '{entity_query}'...", "INFO")
        
        active_regs = self._extract_registrant_rows(self.fetch_raw("Registrants/json/Active"), "REGISTRANTS_ACTIVE")
        term_regs = self._extract_registrant_rows(self.fetch_raw("Registrants/json/Terminated"), "REGISTRANTS_TERMINATED")
        all_regs = active_regs + term_regs
        
        matched_count = 0
        for reg in all_regs:
            if matched_count >= self.max_results:
                break
                
            r_name = reg.get("Name", "")
            r_num = str(reg.get("Registration_Number", ""))
            
            m = match_entity(entity_query, r_name, self.fuzzy_threshold)
            if m["match"]:
                self.io.log(f"Registrant match: '{r_name}' #{r_num} ({m})", "INFO")
                self.io.append_raw_jsonl("fara", reg)
                
                # Fetch details precisely for this matched registrant
                self._emit_registrant_ondemand(entity_query, r_num, reg, m, date_from, date_to)
                matched_count += 1
                
        self.io.log(f"FARA On-Demand search complete: {matched_count} matches found.", "INFO")

    def _search_index_mode(self, entity_query: str, date_from: str, date_to: str):
        self.io.log(f"Searching FARA index for: '{entity_query}'", "INFO")
        matched = 0

        # 1. Match as Registrant
        with open(self.reg_index_path, encoding="utf-8") as f:
            for line in f:
                if matched >= self.max_results: break
                reg = json.loads(line)
                r_name = reg.get("Name", "")
                r_num = str(reg.get("Registration_Number", ""))
                m = match_entity(entity_query, r_name, self.fuzzy_threshold)
                if m["match"]:
                    self.io.log(f"Registrant match: '{r_name}' #{r_num} ({m})", "INFO")
                    self.io.append_raw_jsonl("fara", reg)
                    self._emit_registrant(entity_query, r_num, reg, m, date_from, date_to)
                    matched += 1

        # 2. Match as Foreign Principal
        with open(self.fp_index_path, encoding="utf-8") as f:
            for line in f:
                if matched >= self.max_results: break
                fp = json.loads(line)
                fp_name = fp.get("FP_NAME", "")
                r_num = str(fp.get("_registration_number", fp.get("REG_NUMBER", "")))
                m = match_entity(entity_query, fp_name, self.fuzzy_threshold)
                if m["match"]:
                    self.io.log(f"FP match: '{fp_name}' under #{r_num} ({m})", "INFO")
                    self.io.append_raw_jsonl("fara", fp)
                    self._emit_fp(entity_query, r_num, fp, m, date_from, date_to)
                    matched += 1

        self.io.log(f"FARA search complete for '{entity_query}': {matched} matches found.", "INFO")

    # -------------------------------------------------------------------------
    # OUTPUT EMITTERS
    # -------------------------------------------------------------------------

    def _emit_registrant(self, query, r_num, reg, match_info, date_from, date_to):
        r_name = reg.get("Name", "")
        terminated = bool(reg.get("Termination_Date"))
        self.io.append_row("master_results", {
            "entity_query": query, "source": "FARA", "record_type": "fara_registrant",
            "match_type": match_info["match_type"], "match_confidence": match_info["confidence"],
            "name_primary": r_name, "id_primary": r_num,
            "date_start": reg.get("Registration_Date", ""), "date_end": reg.get("Termination_Date", ""),
            "amount": "", "description": "Terminated Registrant" if terminated else "Active Registrant",
            "url": reg.get("Url", ""), "raw_ref": f"fara_reg_{r_num}"
        })
        self.io.append_row("fara_registrants", {
            "registration_number": r_num, "registrant_name": r_name,
            "address": reg.get("Address_1", ""),
            "registration_date": reg.get("Registration_Date", ""),
            "termination_date": reg.get("Termination_Date", "")
        })
        # Pull FP rows for this registrant from index
        with open(self.fp_index_path, encoding="utf-8") as f:
            for line in f:
                fp = json.loads(line)
                if str(fp.get("_registration_number", "")) == str(r_num):
                    self.io.append_row("fara_foreign_principals", {
                        "registration_number": r_num,
                        "foreign_principal_name": fp.get("FP_NAME", ""),
                        "foreign_principal_date": fp.get("FP_REG_DATE", ""),
                        "foreign_principal_term_date": "",
                        "state_or_country": fp.get("COUNTRY_NAME", fp.get("STATE", ""))
                    })
        # Fetch docs from API
        doc_data = self.fetch_raw(f"RegDocs/json/{r_num}")
        docs_fetched = len(doc_data)
        docs_kept = 0
        docs_rejected = 0
        for doc in self._extract_fp_rows(doc_data):
            doc_date = doc.get("DATE_STAMPED", "")
            if not self._is_within_date_range(doc_date, date_from, date_to):
                docs_rejected += 1
                continue
            docs_kept += 1
            self.io.append_raw_jsonl("fara", doc)
            self.io.append_row("fara_documents", {
                "registration_number": r_num,
                "document_url": doc.get("URL", ""),
                "document_type": doc.get("DOCUMENT_TYPE", ""),
                "document_date": doc_date
            })
        if docs_fetched > 0:
            self.io.log(f"FARA Docs for #{r_num}: Fetched {docs_fetched}, Kept {docs_kept}, Rejected Out-Of-Timeframe {docs_rejected}", "INFO")
        # Fetch short forms from API
        sf_data = self.fetch_raw(f"ShortFormRegistrants/json/Active/{r_num}")
        for sf in self._extract_fp_rows(sf_data):
            self.io.append_raw_jsonl("fara", sf)
            sf_name = f"{sf.get('SF_FIRST_NAME', '')} {sf.get('SF_LAST_NAME', '')}".strip()
            self.io.append_row("fara_short_forms", {
                "registration_number": r_num,
                "short_form_name": sf_name
            })

    def _emit_registrant_ondemand(self, query, r_num, reg, match_info, date_from, date_to):
        r_name = reg.get("Name", "")
        terminated = bool(reg.get("Termination_Date"))
        self.io.append_row("master_results", {
            "entity_query": query, "source": "FARA", "record_type": "fara_registrant",
            "match_type": match_info["match_type"], "match_confidence": match_info["confidence"],
            "name_primary": r_name, "id_primary": r_num,
            "date_start": reg.get("Registration_Date", ""), "date_end": reg.get("Termination_Date", ""),
            "amount": "", "description": "Terminated Registrant" if terminated else "Active Registrant",
            "url": reg.get("Url", ""), "raw_ref": f"fara_reg_{r_num}"
        })
        self.io.append_row("fara_registrants", {
            "registration_number": r_num, "registrant_name": r_name,
            "address": reg.get("Address_1", ""),
            "registration_date": reg.get("Registration_Date", ""),
            "termination_date": reg.get("Termination_Date", "")
        })
        # Fetch FPs from API directly
        fp_data = self.fetch_raw(f"ForeignPrincipals/json/Active/{r_num}")
        for fp in self._extract_fp_rows(fp_data):
            self.io.append_raw_jsonl("fara", fp)
            self.io.append_row("fara_foreign_principals", {
                "registration_number": r_num,
                "foreign_principal_name": fp.get("FP_NAME", ""),
                "foreign_principal_date": fp.get("FP_REG_DATE", ""),
                "foreign_principal_term_date": "",
                "state_or_country": fp.get("COUNTRY_NAME", fp.get("STATE", ""))
            })
        # Fetch docs from API
        doc_data = self.fetch_raw(f"RegDocs/json/{r_num}")
        docs_fetched = len(doc_data)
        docs_kept = 0
        docs_rejected = 0
        for doc in self._extract_fp_rows(doc_data):
            doc_date = doc.get("DATE_STAMPED", "")
            if not self._is_within_date_range(doc_date, date_from, date_to):
                docs_rejected += 1
                continue
            docs_kept += 1
            self.io.append_raw_jsonl("fara", doc)
            self.io.append_row("fara_documents", {
                "registration_number": r_num,
                "document_url": doc.get("URL", ""),
                "document_type": doc.get("DOCUMENT_TYPE", ""),
                "document_date": doc_date
            })
        if docs_fetched > 0:
            self.io.log(f"FARA Docs for #{r_num}: Fetched {docs_fetched}, Kept {docs_kept}, Rejected Out-Of-Timeframe {docs_rejected}", "INFO")
        # Fetch short forms from API
        sf_data = self.fetch_raw(f"ShortFormRegistrants/json/Active/{r_num}")
        for sf in self._extract_fp_rows(sf_data):
            self.io.append_raw_jsonl("fara", sf)
            sf_name = f"{sf.get('SF_FIRST_NAME', '')} {sf.get('SF_LAST_NAME', '')}".strip()
            self.io.append_row("fara_short_forms", {
                "registration_number": r_num,
                "short_form_name": sf_name
            })

    def _emit_fp(self, query, r_num, fp, match_info, date_from, date_to):
        fp_name = fp.get("FP_NAME", "")
        self.io.append_row("master_results", {
            "entity_query": query, "source": "FARA", "record_type": "fara_foreign_principal",
            "match_type": match_info["match_type"], "match_confidence": match_info["confidence"],
            "name_primary": fp_name, "id_primary": r_num,
            "date_start": fp.get("FP_REG_DATE", ""), "date_end": "",
            "amount": "", "description": f"Foreign Principal under registrant #{r_num} ({fp.get('REGISTRANT_NAME','')})",
            "url": "", "raw_ref": f"fara_fp_{r_num}"
        })
        self.io.append_row("fara_foreign_principals", {
            "registration_number": r_num,
            "foreign_principal_name": fp_name,
            "foreign_principal_date": fp.get("FP_REG_DATE", ""),
            "foreign_principal_term_date": "",
            "state_or_country": fp.get("COUNTRY_NAME", fp.get("STATE", ""))
        })
