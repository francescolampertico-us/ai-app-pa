import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io_utils import IOUtils
from matching import match_entity
from xml_parser import IRS990XMLParser
from llm_enricher import IRS990LLMEnricher

class IRS990Client:
    SEARCH_URL = "https://projects.propublica.org/nonprofits/api/v2/search.json"
    ORG_URL_TEMPLATE = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
    
    def __init__(self, io_utils: IOUtils, fuzzy_threshold: float = 85.0,
                 max_results: int = 500, mode: str = "basic",
                 filing_years: list = None):
        self.io = io_utils
        self.fuzzy_threshold = fuzzy_threshold
        self.max_results = max_results
        self.mode = mode
        self.filing_years = filing_years or []
        self.deep_narratives = {}

        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def _throttle(self):
        """Be polite to ProPublica\'s free API."""
        time.sleep(0.5)

    def _fetch_url(self, url: str, params: dict = None) -> dict:
        """Fetch URL with caching."""
        cached = self.io.read_cache(url, params)
        if cached:
            self.io.log(f"IRS 990 Cache Hit: {url}", "DEBUG")
            return cached
            
        self._throttle()
        self.io.log(f"Fetching IRS 990: {url}", "INFO")
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.io.write_cache(url, params, data)
            return data
        except Exception as e:
            self.io.log(f"IRS 990 Fetch Error for {url}: {e}", "ERROR")
            return {}

    def search_entity(self, entity_query: str, date_from: str, date_to: str):
        self.io.log(f"Starting IRS 990 search for entity: {entity_query}", "INFO")
        
        # 1. Search for organizations matching the query
        params = {"q": entity_query}
        search_results = self._fetch_url(self.SEARCH_URL, params)
        organizations = search_results.get("organizations", [])
        
        matched_count = 0
        seen_eins_in_query = set()
        
        for org in organizations:
            if matched_count >= self.max_results:
                break
                
            ein = org.get("ein")
            org_name = org.get("name", "")
            if not ein or not org_name or ein in seen_eins_in_query:
                continue
                
            # We evaluate exact/contains/fuzzy against org name
            match_info = match_entity(entity_query, org_name, self.fuzzy_threshold)
            
            # Optionally check sub_name
            sub_name = org.get("sub_name", "")
            if sub_name and not match_info["match"]:
                match_info_sub = match_entity(entity_query, sub_name, self.fuzzy_threshold)
                if match_info_sub["match"]:
                    match_info = match_info_sub
                    
            if match_info["match"]:
                seen_eins_in_query.add(ein)
                self.io.log(f"IRS 990 matched '{org_name}' (EIN: {ein}) with confidence {match_info['confidence']}%", "INFO")
                
                # 2. Fetch specific filings for this organization
                org_url = self.ORG_URL_TEMPLATE.format(ein=ein)
                org_details = self._fetch_url(org_url)
                
                if org_details:
                    self._normalize_and_save(entity_query, org_details, match_info, date_from, date_to)
                    matched_count += 1

        self.io.log(f"IRS 990 search complete for '{entity_query}': {matched_count} organizations matched.", "INFO")

    def _normalize_and_save(self, query: str, org_details: dict, match_info: dict, date_from: str, date_to: str):
        org = org_details.get("organization", {})
        ein = org.get("ein")
        org_name = org.get("name")
        
        # Save Organization Level Data
        self.io.append_row("irs990_organizations", {
            "ein": ein,
            "organization_name": org_name,
            "ntee_code": org.get("ntee_code", ""),
            "address": org.get("address", ""),
            "city": org.get("city", ""),
            "state": org.get("state", ""),
            "zipcode": org.get("zipcode", "")
        })
        
        self.io.append_raw_jsonl("irs990", org_details)

        # Always add a master record for the matched organization
        self.io.append_row("master_results", {
            "entity_query": query,
            "source": "IRS990",
            "record_type": "IRS 990 Organization",
            "match_type": match_info["match_type"],
            "match_confidence": match_info["confidence"],
            "registrant": org_name,
            "client": "",
            "filing_year": "",
            "filing_period": "",
            "amount": "",
            "url": "",
        })

        # Process Filings
        filings = org_details.get("filings_with_data", [])
        for filing in filings:
            tax_year = filing.get("tax_prd_yr")
            if not tax_year:
                continue
                
            # Date filtering by year
            if self.filing_years:
                if int(tax_year) not in self.filing_years:
                    continue
            elif date_from and str(tax_year) < date_from[:4]:
                continue
            elif date_to and str(tax_year) > date_to[:4]:
                continue
                
            form_type_num = filing.get("formtype")
            form_lookup = {0: "Form 990", 1: "Form 990-EZ", 2: "Form 990-PF"}
            form_type = form_lookup.get(form_type_num, f"Unknown ({form_type_num})")
            
            # Different IRS extracts might label these differently, ProPublica passes them through
            tot_rev = filing.get("totrevenue", filing.get("totrcptperbks", "0"))
            tot_exp = filing.get("totfuncexpns", filing.get("totexpns", "0"))
            net_assets = filing.get("totassetsend", "0")
            pdf_url = filing.get("pdf_url", "")
            xml_url = filing.get("xml_url", "") # ProPublica does not natively serve this, but AWS S3 link could be tracked later in Deep mode
            
            # Save filing data
            self.io.append_row("irs990_filings", {
                "ein": ein,
                "organization_name": org_name,
                "tax_year": tax_year,
                "form_type": form_type,
                "total_revenue": tot_rev,
                "total_functional_expenses": tot_exp,
                "net_assets": net_assets,
                "pdf_url": pdf_url,
                "xml_url": xml_url
            })
            
            # Record hit in Master Results List
            self.io.append_row("master_results", {
                "entity_query": query,
                "source": "IRS990",
                "record_type": f"IRS {form_type}",
                "match_type": match_info["match_type"],
                "match_confidence": match_info["confidence"],
                "registrant": org_name,
                "client": "",
                "filing_year": tax_year,
                "filing_period": "Annual",
                "amount": tot_rev,
                "url": pdf_url,
            })
            
        # Phase 2: XML Deep Extraction (Run on latest available XML if in deep mode)
        latest_object_id = org.get("latest_object_id")
        if self.mode == "deep" and latest_object_id:
            self.io.log(f"IRS 990 Deep mode: Parsing XML for Object ID {latest_object_id}", "INFO")
            parser = IRS990XMLParser(latest_object_id)
            if parser.fetch_and_parse():

                # Extract all data structures
                profile = parser.extract_org_profile()
                financials = parser.extract_financials()
                officers = parser.extract_officers()
                compensation = parser.extract_schedule_j_compensation()
                lobbying = parser.extract_schedule_c_lobbying()
                grants = parser.extract_schedule_i_grants()
                foreign = parser.extract_schedule_f_foreign()
                relateds = parser.extract_schedule_r_related_orgs()
                narrative = parser.extract_narrative_blocks()

                # Save narrative for potential future use
                self.deep_narratives[ein] = narrative

                # Org profile + financials
                self.io.append_row("irs990_deep_profile", {
                    "ein": ein,
                    "organization_name": org_name,
                    "object_id": latest_object_id,
                    "website": profile.get("website", ""),
                    "formation_year": profile.get("formation_year", ""),
                    "state_of_domicile": profile.get("state_of_domicile", ""),
                    "total_employees": profile.get("total_employees", "0"),
                    "total_volunteers": profile.get("total_volunteers", "0"),
                    "flag_lobbying": profile.get("flag_lobbying", "0"),
                    "flag_political_campaign": profile.get("flag_political_campaign", "0"),
                    "flag_grants_to_orgs": profile.get("flag_grants_to_orgs", "0"),
                    "voting_board_members": profile.get("voting_board_members", "0"),
                    "independent_board_members": profile.get("independent_board_members", "0"),
                    "total_revenue": financials.get("total_revenue", "0"),
                    "contributions_and_grants": financials.get("contributions_and_grants", "0"),
                    "program_service_revenue": financials.get("program_service_revenue", "0"),
                    "investment_income": financials.get("investment_income", "0"),
                    "government_grants": financials.get("government_grants", "0"),
                    "total_expenses": financials.get("total_expenses", "0"),
                    "program_service_expenses": financials.get("program_service_expenses", "0"),
                    "management_expenses": financials.get("management_expenses", "0"),
                    "fundraising_expenses": financials.get("fundraising_expenses", "0"),
                    "net_assets": financials.get("net_assets", "0"),
                    "foreign_spending": foreign.get("total_foreign_spending", "0") if foreign.get("present") == "True" else "0",
                })

                # Lobbying (Schedule C)
                self.io.append_row("irs990_deep_lobbying", {
                    "ein": ein,
                    "organization_name": org_name,
                    "object_id": latest_object_id,
                    "total_lobbying": lobbying.get("total_lobbying_expenditures", "0"),
                    "grassroots_lobbying": lobbying.get("grassroots_lobbying_expenditures", "0"),
                    "direct_lobbying": lobbying.get("direct_lobbying", "0"),
                    "sect_162e_lobbying": lobbying.get("sect_162e_lobbying", "0"),
                    "total_sect_162e": lobbying.get("total_sect_162e_lobbying", "0"),
                    "schedule_c_present": lobbying.get("present", "False"),
                })

                # Officers (Part VII)
                for off in officers:
                    self.io.append_row("irs990_deep_officers", {
                        "ein": ein, "object_id": latest_object_id,
                        "name": off["name"], "title": off["title"], "compensation": off["compensation"],
                    })

                # Top compensation (Schedule J)
                for c in compensation:
                    self.io.append_row("irs990_deep_compensation", {
                        "ein": ein, "object_id": latest_object_id,
                        "name": c["name"],
                        "total_compensation_org": c["total_compensation_org"],
                        "compensation_related_orgs": c["compensation_related_orgs"],
                        "other_compensation": c["other_compensation"],
                    })

                # Grants (Schedule I)
                for grant in grants:
                    self.io.append_row("irs990_deep_grants", {
                        "ein": ein, "object_id": latest_object_id,
                        "recipient": grant["recipient"],
                        "recipient_ein": grant.get("recipient_ein", ""),
                        "amount": grant["amount"],
                        "purpose": grant["purpose"],
                        "city": grant.get("city", ""),
                        "state": grant.get("state", ""),
                    })

                # Related orgs (Schedule R)
                for rel in relateds:
                    self.io.append_row("irs990_deep_related", {
                        "ein": ein, "object_id": latest_object_id,
                        "related_name": rel["name"], "related_type": rel["type"],
                    })

                self.io.log(
                    f"Deep extraction complete for {org_name}: "
                    f"{len(officers)} officers, {len(compensation)} Schedule J entries, "
                    f"{len(grants)} grants, {len(relateds)} related orgs",
                    "INFO"
                )

                # Phase 3: Selective LLM Enrichment
                try:
                    self.io.log(f"IRS 990 Deep mode: Running LLM Enrichment for Object ID {latest_object_id}", "INFO")
                    enricher = IRS990LLMEnricher()
                    structured = {
                        "profile": profile,
                        "financials": financials,
                        "lobbying": lobbying,
                        "officers": officers[:15],
                        "grants": grants[:10],
                        "foreign": foreign,
                    }
                    insights = enricher.extract_insights(org_name, narrative, structured)
                    
                    if insights:
                        self.io.append_row("irs990_deep_enrichments", {
                            "ein": ein,
                            "object_id": latest_object_id,
                            "pa_relevance_score": insights.get("pa_relevance_score", ""),
                            "one_sentence_org_profile": insights.get("one_sentence_org_profile", ""),
                            "issue_area_tags": insights.get("issue_area_tags", ""),
                            "top_influence_signals": insights.get("top_influence_signals", ""),
                            "top_risk_flags": insights.get("top_risk_flags", ""),
                            "likely_advocacy_tactics_named": insights.get("likely_advocacy_tactics_named", ""),
                            "likely_target_institutions_named": insights.get("likely_target_institutions_named", "")
                        })
                        self.io.log(f"LLM Enrichment Phase 3 complete for {org_name}.", "INFO")
                except Exception as e:
                    self.io.log(f"Skipping LLM Enrichment (Phase 3) due to error/missing key: {e}", "WARNING")
