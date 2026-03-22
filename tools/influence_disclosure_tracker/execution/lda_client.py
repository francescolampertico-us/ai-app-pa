import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io_utils import IOUtils
from matching import match_entity

class LDAClient:
    BASE_URL = "https://lda.gov/api/v1/" # Using lda.gov as requested
    
    def __init__(self, io_utils: IOUtils, api_key: str = None, fuzzy_threshold: float = 85.0,
                 max_results: int = 500, search_field: str = "client"):
        self.io = io_utils
        self.api_key = api_key
        self.fuzzy_threshold = fuzzy_threshold
        self.max_results = max_results
        self.search_field = search_field
        
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

    def _generate_query_variations(self, query: str) -> list:
        """Generate search variations for an entity name to catch different spellings."""
        variations = {query}
        # Without spaces: "Open AI" → "OpenAI"
        no_space = query.replace(" ", "")
        variations.add(no_space)
        # With spaces before uppercase: "OpenAI" → "Open AI"
        import re
        spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', query)
        variations.add(spaced)
        # All uppercase
        variations.add(query.upper())
        return list(variations)

    def search_entity(self, entity_query: str, date_from: str, date_to: str,
                      filing_year: int = None, filing_periods: list = None):
        self.io.log(f"Starting LDA search for entity: {entity_query}" +
                    (f" (year={filing_year})" if filing_year else ""))

        query_variations = self._generate_query_variations(entity_query)
        self.io.log(f"Query variations: {query_variations}", "DEBUG")

        # Build date filter params
        date_filters = {}
        if filing_year:
            date_filters["filing_year"] = str(filing_year)
        elif date_from and date_to and date_from[:4] == date_to[:4]:
            date_filters["filing_year"] = date_from[:4]

        period_map = {
            "Q1": "first_quarter", "Q2": "second_quarter",
            "Q3": "third_quarter", "Q4": "fourth_quarter",
        }
        allowed_periods = None
        if filing_periods and len(filing_periods) < 4:
            # Only filter by period if not all 4 are selected
            allowed_periods = {period_map.get(p, p) for p in filing_periods}

        # Determine which API fields to search based on search_field setting
        if self.search_field == "client":
            search_fields = ["client_name"]
        elif self.search_field == "registrant":
            search_fields = ["registrant_name"]
        else:
            search_fields = ["client_name", "registrant_name"]

        # Build search params: variation × field
        all_search_params = []
        for variation in query_variations:
            for field in search_fields:
                params = {field: variation, "ordering": "-dt_posted"}
                params.update(date_filters)
                all_search_params.append(params)

        seen_filings = set()
        matched_count = 0

        for params in all_search_params:
            if matched_count >= self.max_results:
                break

            filings = self.fetch_filings(params, max_fetch=self.max_results * 2)

            for f in filings:
                if matched_count >= self.max_results:
                    break

                uuid = f.get("url")
                if uuid in seen_filings:
                    continue
                seen_filings.add(uuid)

                # Filter by quarter if needed
                if allowed_periods and f.get("filing_period") not in allowed_periods:
                    continue

                # Check match confidence against the original query
                client_name = f.get("client", {}).get("name", "")
                reg_name = f.get("registrant", {}).get("name", "")

                if self.search_field == "client":
                    best_match = match_entity(entity_query, client_name, self.fuzzy_threshold)
                elif self.search_field == "registrant":
                    best_match = match_entity(entity_query, reg_name, self.fuzzy_threshold)
                else:
                    match_c = match_entity(entity_query, client_name, self.fuzzy_threshold)
                    match_r = match_entity(entity_query, reg_name, self.fuzzy_threshold)
                    best_match = match_c if match_c["confidence"] > match_r["confidence"] else match_r

                if best_match["match"]:
                    self.normalize_and_save(entity_query, f, best_match)
                    matched_count += 1

        self.io.log(f"LDA search complete for '{entity_query}': {matched_count} matched filings.", "INFO")

    def normalize_and_save(self, query: str, filing: dict, match_info: dict):
        f_uuid = filing.get("url")
        client = filing.get("client", {})
        registrant = filing.get("registrant", {})
        c_id = client.get("id")
        c_name = client.get("name")
        r_id = registrant.get("id")
        r_name = registrant.get("name")

        amount = filing.get("expenses") or filing.get("income")

        # 1. Master Record
        self.io.append_row("master_results", {
            "entity_query": query,
            "source": "LDA",
            "record_type": filing.get("filing_type_display", "lda_filing"),
            "match_type": match_info["match_type"],
            "match_confidence": match_info["confidence"],
            "registrant": r_name,
            "client": c_name,
            "client_description": client.get("general_description") or "",
            "filing_year": filing.get("filing_year"),
            "filing_period": filing.get("filing_period_display", filing.get("filing_period", "")),
            "amount": amount,
            "url": filing.get("filing_document_url", ""),
        })

        # 2. LDA Filing
        self.io.append_row("lda_filings", {
            "filing_uuid": f_uuid,
            "registrant_name": r_name,
            "client_name": c_name,
            "client_description": client.get("general_description") or "",
            "self_filer": client.get("client_self_select", False),
            "filing_year": filing.get("filing_year"),
            "filing_period": filing.get("filing_period"),
            "filing_type": filing.get("filing_type_display", filing.get("filing_type", "")),
            "amount": amount,
            "filing_url": filing.get("filing_document_url")
        })

        # 3. Lobbying Activities — issues, lobbyists, government entities
        seen_lobbyists = set()
        for activity in filing.get("lobbying_activities", []):
            issue_code = activity.get("general_issue_code", "")
            issue_name = activity.get("general_issue_code_display", issue_code)
            description = activity.get("description", "")
            gov_entities = [g.get("name", "") for g in activity.get("government_entities", [])]

            self.io.append_row("lda_issues", {
                "filing_uuid": f_uuid,
                "registrant": r_name,
                "client": c_name,
                "issue_code": issue_code,
                "issue_area": issue_name,
                "description": description,
                "government_entities": "; ".join(gov_entities),
            })

            for lob_entry in activity.get("lobbyists", []):
                lob = lob_entry.get("lobbyist", {})
                first = lob.get("first_name", "")
                last = lob.get("last_name", "")
                name = f"{first} {last}".strip()
                covered = lob_entry.get("covered_position", "")
                lob_key = (f_uuid, name)
                if lob_key not in seen_lobbyists:
                    seen_lobbyists.add(lob_key)
                    self.io.append_row("lda_lobbyists", {
                        "filing_uuid": f_uuid,
                        "registrant": r_name,
                        "client": c_name,
                        "lobbyist_name": name,
                        "covered_position": covered or "",
                    })
