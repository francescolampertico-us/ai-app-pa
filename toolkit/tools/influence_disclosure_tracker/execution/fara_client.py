"""
FARA Client — Bulk CSV approach.

Downloads four bulk CSVs from efile.fara.gov (registrants, foreign principals,
short forms, documents), caches them locally, and searches entirely in-memory.
First call downloads ~3 MB of zipped CSVs; subsequent calls use the cached files.
Typical search completes in < 2 seconds.
"""

import os
import csv
import io
import zipfile
import requests
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io_utils import IOUtils
from matching import match_entity

BULK_BASE = "https://efile.fara.gov/bulk/zip/"
BULK_FILES = {
    "registrants": "FARA_All_Registrants.csv",
    "foreign_principals": "FARA_All_ForeignPrincipals.csv",
    "short_forms": "FARA_All_ShortForms.csv",
    "documents": "FARA_All_RegistrantDocs.csv",
}

CACHE_MAX_AGE_HOURS = 24


class FARAClient:
    def __init__(self, io_utils: IOUtils, fuzzy_threshold: float = 85.0,
                 max_results: int = 500, filing_years=None):
        self.io = io_utils
        self.fuzzy_threshold = fuzzy_threshold
        self.max_results = max_results
        self.filing_years = {str(y) for y in filing_years} if filing_years else None

        self.cache_dir = os.path.join(os.path.dirname(__file__), ".cache", "fara_bulk")
        os.makedirs(self.cache_dir, exist_ok=True)

        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        # Lazy-loaded data
        self._registrants = None
        self._foreign_principals = None
        self._short_forms = None
        self._documents = None

    # -------------------------------------------------------------------------
    # BULK CSV DOWNLOAD + CACHE
    # -------------------------------------------------------------------------

    def _csv_cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.csv")

    def _is_cache_fresh(self, key: str) -> bool:
        path = self._csv_cache_path(key)
        if not os.path.exists(path):
            return False
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        return (datetime.now() - mtime) < timedelta(hours=CACHE_MAX_AGE_HOURS)

    def _download_bulk_csv(self, key: str) -> str:
        """Download a bulk CSV zip, extract, cache, and return the CSV text."""
        filename = BULK_FILES[key]
        url = f"{BULK_BASE}{filename}.zip"

        # Check cache first
        if self._is_cache_fresh(key):
            self.io.log(f"FARA bulk cache hit: {key}", "DEBUG")
            with open(self._csv_cache_path(key), "r", encoding="utf-8") as f:
                return f.read()

        self.io.log(f"Downloading FARA bulk data: {filename}...", "INFO")
        try:
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                csv_name = zf.namelist()[0]
                csv_bytes = zf.read(csv_name)
                csv_text = csv_bytes.decode("utf-8", errors="replace")

            # Cache to disk
            with open(self._csv_cache_path(key), "w", encoding="utf-8") as f:
                f.write(csv_text)

            self.io.log(f"FARA bulk {key}: downloaded and cached.", "INFO")
            return csv_text
        except Exception as e:
            self.io.log(f"FARA bulk download error for {key}: {e}", "ERROR")
            # Fall back to stale cache if available
            path = self._csv_cache_path(key)
            if os.path.exists(path):
                self.io.log(f"Using stale cache for {key}.", "WARNING")
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            return ""

    def _parse_csv(self, csv_text: str) -> list[dict]:
        if not csv_text:
            return []
        reader = csv.DictReader(io.StringIO(csv_text))
        return list(reader)

    def _load_registrants(self) -> list[dict]:
        if self._registrants is None:
            self._registrants = self._parse_csv(self._download_bulk_csv("registrants"))
            self.io.log(f"FARA: {len(self._registrants)} registrants loaded.", "INFO")
        return self._registrants

    def _load_foreign_principals(self) -> list[dict]:
        if self._foreign_principals is None:
            self._foreign_principals = self._parse_csv(self._download_bulk_csv("foreign_principals"))
            self.io.log(f"FARA: {len(self._foreign_principals)} foreign principals loaded.", "INFO")
        return self._foreign_principals

    def _load_short_forms(self) -> list[dict]:
        if self._short_forms is None:
            self._short_forms = self._parse_csv(self._download_bulk_csv("short_forms"))
            self.io.log(f"FARA: {len(self._short_forms)} short forms loaded.", "INFO")
        return self._short_forms

    def _load_documents(self) -> list[dict]:
        if self._documents is None:
            self._documents = self._parse_csv(self._download_bulk_csv("documents"))
            self.io.log(f"FARA: {len(self._documents)} documents loaded.", "INFO")
        return self._documents

    # -------------------------------------------------------------------------
    # DATE FILTERING
    # -------------------------------------------------------------------------

    def _parse_date(self, date_str: str) -> str:
        """Normalize MM/DD/YYYY or ISO dates to YYYY-MM-DD for comparison."""
        if not date_str:
            return ""
        date_str = date_str.strip()
        if "T" in date_str:
            return date_str.split("T")[0]
        if "/" in date_str:
            parts = date_str.split("/")
            if len(parts) == 3:
                return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        return date_str[:10]

    def _is_within_date_range(self, date_raw: str, date_from: str, date_to: str) -> bool:
        parsed = self._parse_date(date_raw)
        # When specific filing years were selected, match only those exact years
        if self.filing_years:
            if not parsed:
                return True
            return parsed[:4] in self.filing_years
        if not date_from and not date_to:
            return True
        if not parsed:
            return True
        if date_from and parsed < date_from:
            return False
        if date_to and parsed > date_to:
            return False
        return True

    # -------------------------------------------------------------------------
    # SEARCH
    # -------------------------------------------------------------------------

    def search_entity(self, entity_query: str, date_from: str, date_to: str):
        self.io.log(f"FARA search for: '{entity_query}'", "INFO")
        matched = 0

        registrants = self._load_registrants()
        foreign_principals = self._load_foreign_principals()

        # Build FP lookup by registration number
        fp_by_reg = {}
        for fp in foreign_principals:
            r_num = fp.get("Registration Number", "").strip()
            fp_by_reg.setdefault(r_num, []).append(fp)

        matched_reg_nums = set()

        # 1. Match as Registrant (firm name)
        for reg in registrants:
            if matched >= self.max_results:
                break
            r_name = (reg.get("Name") or "").strip()
            r_num = (reg.get("Registration Number") or "").strip()
            if not r_name:
                continue

            m = match_entity(entity_query, r_name, self.fuzzy_threshold)
            if m["match"]:
                self.io.log(f"FARA Registrant match: '{r_name}' #{r_num} "
                            f"({m['match_type']}, {m['confidence']}%)", "INFO")
                self._emit_registrant(entity_query, r_num, reg, m, fp_by_reg, date_from, date_to)
                matched_reg_nums.add(r_num)
                matched += 1

        # 2. Match as Foreign Principal (client name)
        for fp in foreign_principals:
            if matched >= self.max_results:
                break
            fp_name = (fp.get("Foreign Principal") or "").strip()
            r_num = (fp.get("Registration Number") or "").strip()
            if not fp_name or r_num in matched_reg_nums:
                continue
            if not self._fp_active_in_range(fp, date_from, date_to):
                continue

            m = match_entity(entity_query, fp_name, self.fuzzy_threshold)
            if m["match"]:
                self.io.log(f"FARA FP match: '{fp_name}' under registrant "
                            f"'{fp.get('Registrant Name', '')}' #{r_num} "
                            f"({m['match_type']}, {m['confidence']}%)", "INFO")
                self._emit_fp(entity_query, r_num, fp, m, fp_by_reg, date_from, date_to)
                matched_reg_nums.add(r_num)
                matched += 1

        self.io.log(f"FARA search complete for '{entity_query}': {matched} matches.", "INFO")

    # -------------------------------------------------------------------------
    # OUTPUT EMITTERS
    # -------------------------------------------------------------------------

    def _fp_active_in_range(self, fp: dict, date_from: str, date_to: str) -> bool:
        """Return False if FP's active period has no overlap with [date_from, date_to]."""
        if not date_from and not date_to:
            return True
        fp_reg_date = self._parse_date(fp.get("Foreign Principal Registration Date", ""))
        fp_term_raw = (fp.get("Foreign Principal Termination Date") or "").strip()
        fp_term_date = self._parse_date(fp_term_raw) if fp_term_raw else ""
        # FP registered after the search window ends → no overlap
        if date_to and fp_reg_date and fp_reg_date > date_to:
            return False
        # FP terminated before the search window starts → no overlap
        if date_from and fp_term_date and fp_term_date < date_from:
            return False
        return True

    def _emit_registrant(self, query, r_num, reg, match_info, fp_by_reg, date_from, date_to):
        r_name = (reg.get("Name") or "").strip()
        term_date = (reg.get("Termination Date") or "").strip()
        terminated = bool(term_date)

        self.io.append_row("master_results", {
            "entity_query": query, "source": "FARA", "record_type": "fara_registrant",
            "match_type": match_info["match_type"], "match_confidence": match_info["confidence"],
            "registrant": r_name, "client": "",
            "filing_period": "Terminated" if terminated else "Active",
            "amount": "", "id_primary": r_num,
            "date_start": reg.get("Registration Date", ""),
            "date_end": term_date,
            "url": "",
        })
        self.io.append_row("fara_registrants", {
            "registration_number": r_num,
            "registrant_name": r_name,
            "address": reg.get("Address 1", ""),
            "city": reg.get("City", ""),
            "state": reg.get("State", ""),
            "registration_date": reg.get("Registration Date", ""),
            "termination_date": term_date,
        })

        # Foreign principals for this registrant
        for fp in fp_by_reg.get(r_num, []):
            if not self._fp_active_in_range(fp, date_from, date_to):
                continue
            fp_name = (fp.get("Foreign Principal") or "").strip()
            self.io.append_row("fara_foreign_principals", {
                "registration_number": r_num,
                "registrant_name": r_name,
                "foreign_principal_name": fp_name,
                "foreign_principal_date": fp.get("Foreign Principal Registration Date", ""),
                "foreign_principal_term_date": fp.get("Foreign Principal Termination Date", ""),
                "state_or_country": fp.get("Country/Location Represented", ""),
            })

        # Short forms for this registrant
        short_forms = self._load_short_forms()
        for sf in short_forms:
            if (sf.get("Registration Number") or "").strip() == r_num:
                sf_name = f"{sf.get('Short Form First Name', '')} {sf.get('Short Form Last Name', '')}".strip()
                self.io.append_row("fara_short_forms", {
                    "registration_number": r_num,
                    "short_form_name": sf_name,
                    "short_form_date": sf.get("Short Form Date", ""),
                })

        # Documents for this registrant
        documents = self._load_documents()
        for doc in documents:
            if (doc.get("Registration Number") or "").strip() == r_num:
                doc_date = doc.get("Stamped Date", doc.get("Date", ""))
                if not self._is_within_date_range(doc_date, date_from, date_to):
                    continue
                self.io.append_row("fara_documents", {
                    "registration_number": r_num,
                    "document_url": doc.get("URL", doc.get("Document Link", "")),
                    "document_type": doc.get("Document Type", ""),
                    "document_date": doc_date,
                })

    def _emit_fp(self, query, r_num, fp, match_info, _fp_by_reg, date_from, date_to):
        if not self._fp_active_in_range(fp, date_from, date_to):
            return
        fp_name = (fp.get("Foreign Principal") or "").strip()
        reg_name = (fp.get("Registrant Name") or "").strip()
        fp_term = (fp.get("Foreign Principal Termination Date") or "").strip()
        fp_status = "Terminated" if fp_term else "Active"

        self.io.append_row("master_results", {
            "entity_query": query, "source": "FARA", "record_type": "fara_foreign_principal",
            "match_type": match_info["match_type"], "match_confidence": match_info["confidence"],
            "registrant": reg_name, "client": fp_name,
            "filing_period": fp_status,
            "amount": "", "id_primary": r_num,
            "date_start": fp.get("Foreign Principal Registration Date", ""),
            "date_end": fp_term,
            "url": "",
        })

        # Registrant info
        registrants = self._load_registrants()
        reg_record = next((r for r in registrants
                           if (r.get("Registration Number") or "").strip() == r_num), None)
        if reg_record:
            self.io.append_row("fara_registrants", {
                "registration_number": r_num,
                "registrant_name": reg_name,
                "address": reg_record.get("Address 1", ""),
                "city": reg_record.get("City", ""),
                "state": reg_record.get("State", ""),
                "registration_date": reg_record.get("Registration Date", ""),
                "termination_date": reg_record.get("Termination Date", ""),
            })

        # Only the matched FP (not all FPs under this registrant)
        self.io.append_row("fara_foreign_principals", {
            "registration_number": r_num,
            "registrant_name": reg_name,
            "foreign_principal_name": fp_name,
            "foreign_principal_date": fp.get("Foreign Principal Registration Date", ""),
            "foreign_principal_term_date": (fp.get("Foreign Principal Termination Date") or ""),
            "state_or_country": fp.get("Country/Location Represented", ""),
        })

        # Documents — only those specifically mentioning this FP
        documents = self._load_documents()
        # Normalize for comparison: strip quotes, parens, extra whitespace
        def _normalize(s):
            return s.lower().replace('"', '').replace("'", "").replace("(", "").replace(")", "").strip()
        fp_norm = _normalize(fp_name)
        for doc in documents:
            if (doc.get("Registration Number") or "").strip() != r_num:
                continue
            doc_fp_raw = (doc.get("Foreign Principal Name") or "").strip()
            doc_fp_norm = _normalize(doc_fp_raw)
            if not doc_fp_norm or (fp_norm not in doc_fp_norm and doc_fp_norm not in fp_norm):
                continue
            doc_date = doc.get("Stamped Date", doc.get("Date Stamped", doc.get("Date", "")))
            if not self._is_within_date_range(doc_date, date_from, date_to):
                continue
            self.io.append_row("fara_documents", {
                "registration_number": r_num,
                "registrant_name": reg_name,
                "foreign_principal_name": doc.get("Foreign Principal Name", ""),
                "document_url": doc.get("URL", ""),
                "document_type": doc.get("Document Type", ""),
                "document_date": doc_date,
            })

        # Short forms (people/agents) — most recent per person only
        short_forms = self._load_short_forms()
        seen_agents = {}
        for sf in short_forms:
            if (sf.get("Registration Number") or "").strip() != r_num:
                continue
            sf_name = f"{sf.get('Short Form First Name', '')} {sf.get('Short Form Last Name', '')}".strip()
            if not sf_name:
                continue
            sf_date = sf.get("Short Form Date", "")
            # Keep most recent entry per person
            if sf_name not in seen_agents or sf_date > seen_agents[sf_name]:
                seen_agents[sf_name] = sf_date
        for sf_name, sf_date in seen_agents.items():
            self.io.append_row("fara_short_forms", {
                "registration_number": r_num,
                "short_form_name": sf_name,
                "short_form_date": sf_date,
            })
