import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io_utils import IOUtils
from matching import match_entity

class LDAClient:
    BASE_URL = "https://lda.gov/api/v1/" # Using lda.gov as requested
    
    def __init__(self, io_utils: IOUtils, api_key: str = None, fuzzy_threshold: float = 85.0, max_results: int = 500):
        self.io = io_utils
        self.api_key = api_key
        self.fuzzy_threshold = fuzzy_threshold
        self.max_results = max_results
        
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        if self.api_key:
            self.session.headers.update({"Authorization": f"Token {self.api_key}"})

    def _is_within_date_range(self, filing: dict, date_from: str, date_to: str) -> bool:
        dt_posted = filing.get("dt_posted")
        if dt_posted:
            date_part = dt_posted.split("T")[0]
            return date_from <= date_part <= date_to
            
        filing_year = str(filing.get("filing_year", ""))
        if filing_year:
            return date_from[:4] <= filing_year <= date_to[:4]
            
        return True

    def fetch_filings(self, params: dict, max_fetch: int):
        url = f"{self.BASE_URL}filings/"
        results = []
        
        while url and len(results) < max_fetch:
            req_url = url
            if params:
                req = requests.Request('GET', url, params=params).prepare()
                req_url = req.url
                
            # Check cache
            cached_data = self.io.read_cache(url, params)
            if cached_data:
                data = cached_data
                self.io.log(f"LDA Cache Hit: {req_url}", "DEBUG")
            else:
                self.io.lda_throttle(bool(self.api_key))
                self.io.log(f"Fetching LDA: {req_url}", "INFO")
                try:
                    response = self.session.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    self.io.write_cache(url, params, data)
                except Exception as e:
                    self.io.log(f"LDA Error fetching {req_url}: {e}", "ERROR")
                    break
            
            # Save raw
            for r in data.get("results", []):
                self.io.append_raw_jsonl("lda", r)
                results.append(r)
                if len(results) >= max_fetch:
                    break
                
            url = data.get("next")
            params = None # only needed for first page
            
        return results

    def _fetch_filing_detail(self, detail_url: str) -> dict:
        """Fetch individual filing to get full nested lobbyists/issues."""
        cached_data = self.io.read_cache(detail_url)
        if cached_data:
            return cached_data
            
        self.io.lda_throttle(bool(self.api_key))
        try:
            response = self.session.get(detail_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.io.write_cache(detail_url, None, data)
            return data
        except Exception as e:
            self.io.log(f"LDA detail fetch error {detail_url}: {e}", "WARNING")
            return {}

    def search_entity(self, entity_query: str, date_from: str, date_to: str):
        self.io.log(f"Starting LDA search for entity: {entity_query}")
        
        # We search by client name and registrant name
        search_params = [
            {"client_name": entity_query, "filing_period_start__gte": date_from, "filing_period_end__lte": date_to, "ordering": "-dt_posted"},
            {"registrant_name": entity_query, "filing_period_start__gte": date_from, "filing_period_end__lte": date_to, "ordering": "-dt_posted"}
        ]
        
        if date_from[:4] == date_to[:4]:
            for p in search_params:
                p["filing_year"] = date_from[:4]
        
        seen_filings = set()
        matched_count = 0
        rejected_count = 0
        
        for params in search_params:
            if matched_count >= self.max_results:
                break
                
            # fetch generously but constrained
            filings = self.fetch_filings(params, max_fetch=self.max_results * 2)
            
            for f in filings:
                if matched_count >= self.max_results:
                    break
                    
                uuid = f.get("url") # Use URL as unique identifier
                if uuid in seen_filings:
                    continue
                seen_filings.add(uuid)
                
                if not self._is_within_date_range(f, date_from, date_to):
                    rejected_count += 1
                    continue

                
                # Check match confidence
                client_name = f.get("client", {}).get("name", "")
                reg_name = f.get("registrant", {}).get("name", "")
                
                match_c = match_entity(entity_query, client_name, self.fuzzy_threshold)
                match_r = match_entity(entity_query, reg_name, self.fuzzy_threshold)
                
                best_match = match_c if match_c["confidence"] > match_r["confidence"] else match_r
                
                if best_match["match"]:
                    # Fetch complete detail payload for maximum data accuracy
                    detail_url = f.get("url")
                    if detail_url:
                        detail_filing = self._fetch_filing_detail(detail_url)
                        if detail_filing:
                            f = detail_filing  # override with detail variant
                            
                    self.normalize_and_save(entity_query, f, best_match)
                    matched_count += 1
                    
        if rejected_count > 0:
            self.io.log(f"Rejected {rejected_count} LDA filings outside the requested date range ({date_from} to {date_to}).", "INFO")

    def normalize_and_save(self, query: str, filing: dict, match_info: dict):
        f_uuid = filing.get("url")
        c_id = filing.get("client", {}).get("id")
        c_name = filing.get("client", {}).get("name")
        r_id = filing.get("registrant", {}).get("id")
        r_name = filing.get("registrant", {}).get("name")
        
        # 1. Master Record
        self.io.append_row("master_results", {
            "entity_query": query,
            "source": "LDA",
            "record_type": filing.get("filing_type_display", "lda_filing"),
            "match_type": match_info["match_type"],
            "match_confidence": match_info["confidence"],
            "name_primary": c_name or r_name,
            "id_primary": c_id or r_id,
            "date_start": filing.get("dt_posted"),
            "date_end": filing.get("dt_posted"),
            "amount": filing.get("income") or filing.get("expenses"),
            "description": filing.get("filing_period_display", ""),
            "url": filing.get("filing_document_url", ""),
            "raw_ref": f_uuid
        })
        
        # 2. LDA Filing
        self.io.append_row("lda_filings", {
            "filing_uuid": f_uuid,
            "registrant_id": r_id,
            "registrant_name": r_name,
            "client_id": c_id,
            "client_name": c_name,
            "filing_year": filing.get("filing_year"),
            "filing_period": filing.get("filing_period"),
            "filing_type": filing.get("filing_type"),
            "amount_reported": filing.get("income") or filing.get("expenses"),
            "filing_url": filing.get("filing_document_url")
        })
        
        # 3. LDA Issues & Lobbyists
        for issue in filing.get("lobbying_activities", []):
            self.io.append_row("lda_issues", {
                "filing_uuid": f_uuid,
                "issue_code": issue.get("general_issue_code"),
                "specific_issue": issue.get("description", "")
            })
            for lobbyist in issue.get("lobbyists", []):
                self.io.append_row("lda_lobbyists", {
                    "filing_uuid": f_uuid,
                    "lobbyist_name": lobbyist.get("lobbyist", {}).get("name")
                })
