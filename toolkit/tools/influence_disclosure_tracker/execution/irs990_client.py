import copy
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import parse_qs, urlparse
from io_utils import IOUtils
from matching import match_entity
from xml_parser import IRS990XMLParser
from pdf_parser import IRS990PDFParser
from llm_enricher import IRS990LLMEnricher

class IRS990Client:
    SEARCH_URL = "https://projects.propublica.org/nonprofits/api/v2/search.json"
    ORG_URL_TEMPLATE = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
    
    def __init__(self, io_utils: IOUtils, fuzzy_threshold: float = 85.0,
                 max_results: int = 500, mode: str = "basic",
                 filing_years: list = None, max_deep: int = 2):
        self.io = io_utils
        self.fuzzy_threshold = fuzzy_threshold
        self.max_results = max_results
        self.mode = mode
        self.filing_years = filing_years or []
        self.deep_narratives = {}
        self.max_deep = max_deep   # max orgs to run deep XML + LLM enrichment on
        self._deep_count = 0       # tracks how many orgs have already had deep treatment

        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def _extract_object_id(self, filing: dict) -> str:
        for key in ("object_id", "objectId", "latest_object_id", "objectid"):
            value = filing.get(key)
            if value:
                return str(value)

        xml_url = filing.get("xml_url", "") or ""
        if xml_url:
            parsed = urlparse(xml_url)
            object_id = parse_qs(parsed.query).get("object_id", [""])[0]
            if object_id:
                return object_id
        return ""

    def _build_xml_url(self, filing: dict, object_id: str) -> str:
        existing = (filing.get("xml_url") or "").strip()
        if existing:
            return existing
        if object_id:
            return f"https://projects.propublica.org/nonprofits/download-xml?object_id={object_id}"
        return ""

    def _eligible_filing(self, filing: dict, date_from: str, date_to: str) -> bool:
        tax_year = filing.get("tax_prd_yr")
        if not tax_year:
            return False

        try:
            year_int = int(tax_year)
        except (TypeError, ValueError):
            return False

        if self.filing_years:
            return year_int in self.filing_years
        if date_from and str(year_int) < date_from[:4]:
            return False
        if date_to and str(year_int) > date_to[:4]:
            return False
        return True

    def _select_deep_filing(self, org: dict, filings: list[dict], date_from: str, date_to: str) -> dict:
        strict_candidates = []
        older_backfill_candidates = []
        for filing in filings:
            tax_year = filing.get("tax_prd_yr")
            try:
                year_int = int(tax_year)
            except (TypeError, ValueError):
                continue

            object_id = self._extract_object_id(filing)
            xml_url = self._build_xml_url(filing, object_id)
            candidate = {
                "tax_year": str(tax_year or ""),
                "tax_year_int": year_int,
                "object_id": object_id,
                "xml_url": xml_url,
                "pdf_url": filing.get("pdf_url", "") or "",
                "has_actionable_source": bool(xml_url or filing.get("pdf_url")),
                "total_revenue": filing.get("totrevenue", filing.get("totrcptperbks", "0")),
                "total_expenses": filing.get("totfuncexpns", filing.get("totexpns", "0")),
                "net_assets": filing.get("totassetsend", "0"),
            }

            if self._eligible_filing(filing, date_from, date_to):
                strict_candidates.append(candidate)
            elif self._is_older_backfill_candidate(year_int, date_from):
                older_backfill_candidates.append(candidate)

        strict_candidates.sort(key=lambda item: item["tax_year_int"], reverse=True)
        older_backfill_candidates.sort(key=lambda item: item["tax_year_int"], reverse=True)

        skipped_years = [item["tax_year"] for item in strict_candidates if not item["has_actionable_source"]]
        fallback_pdf = next(
            (pdf_item for pdf_item in strict_candidates if pdf_item.get("pdf_url")),
            next((pdf_item for pdf_item in older_backfill_candidates if pdf_item.get("pdf_url")), None),
        )

        for item in strict_candidates:
            if item.get("xml_url"):
                item = copy.deepcopy(item)
                item["selection_note"] = self._selection_note(skipped_years, item["tax_year"], "XML")
                item["selection_source_type"] = "xml"
                item["fallback_pdf_url"] = fallback_pdf.get("pdf_url", "") if fallback_pdf else ""
                item["fallback_pdf_tax_year"] = fallback_pdf.get("tax_year", "") if fallback_pdf else ""
                item["fallback_total_revenue"] = fallback_pdf.get("total_revenue", "0") if fallback_pdf else "0"
                item["fallback_total_expenses"] = fallback_pdf.get("total_expenses", "0") if fallback_pdf else "0"
                item["fallback_net_assets"] = fallback_pdf.get("net_assets", "0") if fallback_pdf else "0"
                return item

        for item in strict_candidates:
            if item.get("pdf_url"):
                item = copy.deepcopy(item)
                item["selection_note"] = self._selection_note(skipped_years, item["tax_year"], "PDF")
                item["selection_source_type"] = "pdf"
                item["fallback_pdf_url"] = item.get("pdf_url", "")
                item["fallback_pdf_tax_year"] = item.get("tax_year", "")
                item["fallback_total_revenue"] = item.get("total_revenue", "0")
                item["fallback_total_expenses"] = item.get("total_expenses", "0")
                item["fallback_net_assets"] = item.get("net_assets", "0")
                return item

        for item in older_backfill_candidates:
            if item.get("xml_url"):
                item = copy.deepcopy(item)
                item["selection_note"] = (
                    f"No in-window deep source was available; selected older XML filing from {item['tax_year']} for deep detail."
                )
                item["selection_source_type"] = "xml"
                item["fallback_pdf_url"] = fallback_pdf.get("pdf_url", "") if fallback_pdf else ""
                item["fallback_pdf_tax_year"] = fallback_pdf.get("tax_year", "") if fallback_pdf else ""
                item["fallback_total_revenue"] = fallback_pdf.get("total_revenue", "0") if fallback_pdf else "0"
                item["fallback_total_expenses"] = fallback_pdf.get("total_expenses", "0") if fallback_pdf else "0"
                item["fallback_net_assets"] = fallback_pdf.get("net_assets", "0") if fallback_pdf else "0"
                return item

        for item in older_backfill_candidates:
            if item.get("pdf_url"):
                item = copy.deepcopy(item)
                item["selection_note"] = (
                    f"No in-window deep source was available; selected older PDF filing from {item['tax_year']} for deep detail."
                )
                item["selection_source_type"] = "pdf"
                item["fallback_pdf_url"] = item.get("pdf_url", "")
                item["fallback_pdf_tax_year"] = item.get("tax_year", "")
                item["fallback_total_revenue"] = item.get("total_revenue", "0")
                item["fallback_total_expenses"] = item.get("total_expenses", "0")
                item["fallback_net_assets"] = item.get("net_assets", "0")
                return item

        fallback_object_id = str(org.get("latest_object_id") or org.get("object_id") or "")
        fallback_xml = self._build_xml_url({}, fallback_object_id)
        if fallback_xml:
            return {
                "tax_year": "",
                "object_id": fallback_object_id,
                "xml_url": fallback_xml,
                "pdf_url": "",
                "selection_note": "",
                "selection_source_type": "xml",
                "fallback_pdf_url": "",
                "fallback_pdf_tax_year": "",
                "fallback_total_revenue": "0",
                "fallback_total_expenses": "0",
                "fallback_net_assets": "0",
            }
        return {
            "tax_year": "",
            "object_id": "",
            "xml_url": "",
            "pdf_url": "",
            "selection_note": self._selection_note(skipped_years, "", ""),
            "selection_source_type": "none",
            "fallback_pdf_url": "",
            "fallback_pdf_tax_year": "",
            "fallback_total_revenue": "0",
            "fallback_total_expenses": "0",
            "fallback_net_assets": "0",
        }

    def _is_older_backfill_candidate(self, year_int: int, date_from: str) -> bool:
        if self.filing_years:
            return year_int < min(self.filing_years)
        if date_from:
            return year_int < int(date_from[:4])
        return False

    @staticmethod
    def _selection_note(skipped_years: list[str], selected_year: str, selected_source: str) -> str:
        relevant = [year for year in skipped_years if year and year != selected_year]
        if not relevant:
            return ""
        return (
            f"Skipped newer eligible filing year(s) with no XML or PDF document link: {', '.join(relevant)}; "
            f"selected {selected_source} source for {selected_year or 'latest available filing'}."
        )

    def _append_deep_source(
        self,
        ein: str,
        org_name: str,
        tax_year: str,
        source_type: str,
        source_url: str,
        object_id: str,
        parse_status: str,
        parse_reason: str,
    ) -> None:
        self.io.append_row("irs990_deep_sources", {
            "ein": ein,
            "organization_name": org_name,
            "tax_year": tax_year,
            "source_type": source_type,
            "source_url": source_url,
            "object_id": object_id,
            "parse_status": parse_status,
            "parse_reason": parse_reason,
        })

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

        # Phase 1: scan search results and collect all matches with their confidence scores.
        # We do NOT fetch org details yet — we want to rank by quality first so that
        # the deep XML+LLM cap (max_deep) is applied to the highest-confidence matches,
        # not whichever orgs happened to come first in ProPublica's result order.
        params = {"q": entity_query}
        search_results = self._fetch_url(self.SEARCH_URL, params)
        organizations = search_results.get("organizations", [])

        matches: list[tuple[dict, dict]] = []   # (org dict, match_info dict)
        seen_eins = set()

        for org in organizations:
            ein = org.get("ein")
            org_name = org.get("name", "")
            if not ein or not org_name or ein in seen_eins:
                continue

            match_info = match_entity(entity_query, org_name, self.fuzzy_threshold)

            sub_name = org.get("sub_name", "")
            if sub_name and not match_info["match"]:
                match_info_sub = match_entity(entity_query, sub_name, self.fuzzy_threshold)
                if match_info_sub["match"]:
                    match_info = match_info_sub

            if match_info["match"]:
                seen_eins.add(ein)
                matches.append((org, match_info))

        if not matches:
            self.io.log(f"IRS 990 search complete for '{entity_query}': 0 organizations matched.", "INFO")
            return

        # Phase 2: sort by match confidence (descending) so the best matches get deep treatment.
        matches.sort(key=lambda x: x[1]["confidence"], reverse=True)
        matches = matches[:self.max_results]

        deep_count_before = self._deep_count
        processed = 0
        for org, match_info in matches:
            ein = org.get("ein")
            org_name = org.get("name", "")
            will_get_deep = (self.mode == "deep" and self._deep_count < self.max_deep)
            self.io.log(
                f"IRS 990 matched '{org_name}' (EIN: {ein}) with confidence {match_info['confidence']}% "
                f"— {'deep' if will_get_deep else 'basic'} enrichment",
                "INFO",
            )

            # Phase 3: fetch org details and process
            org_url = self.ORG_URL_TEMPLATE.format(ein=ein)
            org_details = self._fetch_url(org_url)
            if org_details:
                self._normalize_and_save(entity_query, org_details, match_info, date_from, date_to)
                processed += 1

        deep_done = self._deep_count - deep_count_before
        basic_only = processed - deep_done
        self.io.log(
            f"IRS 990 search complete for '{entity_query}': {processed} organizations matched "
            f"({deep_done} deep enrichment, {basic_only} basic filing data only).",
            "INFO",
        )

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

        # Determine whether this org will receive deep enrichment
        will_get_deep = (self.mode == "deep" and self._deep_count < self.max_deep)
        enrichment_tier = "deep" if will_get_deep else "basic"

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
            "enrichment_tier": enrichment_tier,
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
            object_id = self._extract_object_id(filing)
            xml_url = self._build_xml_url(filing, object_id)
            
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
                "xml_url": xml_url,
                "object_id": object_id,
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
        deep_candidate = self._select_deep_filing(org, filings, date_from, date_to)
        deep_tax_year = deep_candidate.get("tax_year", "")
        deep_object_id = deep_candidate.get("object_id", "")
        deep_xml_url = deep_candidate.get("xml_url", "")
        deep_pdf_url = deep_candidate.get("pdf_url", "")
        fallback_pdf_url = deep_candidate.get("fallback_pdf_url", "") or deep_pdf_url
        fallback_pdf_tax_year = deep_candidate.get("fallback_pdf_tax_year", "") or deep_tax_year
        fallback_total_revenue = deep_candidate.get("fallback_total_revenue", "0")
        fallback_total_expenses = deep_candidate.get("fallback_total_expenses", "0")
        fallback_net_assets = deep_candidate.get("fallback_net_assets", "0")
        selection_note = deep_candidate.get("selection_note", "")

        if selection_note:
            self.io.log(f"IRS 990 Deep mode: {selection_note}", "INFO")

        if self.mode == "deep" and self._deep_count >= self.max_deep:
            self.io.log(
                f"IRS 990 Deep mode: Skipping deep extraction for {org_name} "
                f"(max_deep={self.max_deep} already reached; basic filing data saved).",
                "INFO",
            )
        elif self.mode == "deep" and deep_xml_url:
            year_note = f" ({deep_tax_year})" if deep_tax_year else ""
            self.io.log(
                f"IRS 990 Deep mode: Parsing XML for Object ID {deep_object_id or 'n/a'}{year_note}",
                "INFO",
            )
            parser = IRS990XMLParser(deep_object_id, xml_url=deep_xml_url)
            if parser.fetch_and_parse():
                self._append_deep_source(
                    ein,
                    org_name,
                    deep_tax_year,
                    "xml",
                    deep_xml_url,
                    deep_object_id,
                    "parsed",
                    selection_note,
                )

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
                    "object_id": deep_object_id,
                    "source_type": "xml",
                    "source_url": deep_xml_url,
                    "parse_status": "parsed",
                    "parse_reason": "",
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
                    "mission_excerpt": "",
                    "program_excerpt": "",
                    "schedule_mentions": "",
                })

                # Lobbying (Schedule C)
                self.io.append_row("irs990_deep_lobbying", {
                    "ein": ein,
                    "organization_name": org_name,
                    "object_id": deep_object_id,
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
                        "ein": ein, "object_id": deep_object_id,
                        "name": off["name"], "title": off["title"], "compensation": off["compensation"],
                    })

                # Top compensation (Schedule J)
                for c in compensation:
                    self.io.append_row("irs990_deep_compensation", {
                        "ein": ein, "object_id": deep_object_id,
                        "name": c["name"],
                        "total_compensation_org": c["total_compensation_org"],
                        "compensation_related_orgs": c["compensation_related_orgs"],
                        "other_compensation": c["other_compensation"],
                    })

                # Grants (Schedule I)
                for grant in grants:
                    self.io.append_row("irs990_deep_grants", {
                        "ein": ein, "object_id": deep_object_id,
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
                        "ein": ein, "object_id": deep_object_id,
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
                    self.io.log(f"IRS 990 Deep mode: Running LLM Enrichment for Object ID {deep_object_id or 'n/a'}", "INFO")
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
                            "object_id": deep_object_id,
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
                self._deep_count += 1
            elif fallback_pdf_url:
                self.io.log(
                    f"IRS 990 XML parse failed for {org_name}; using PDF fallback for {fallback_pdf_tax_year or 'latest eligible filing'}.",
                    "WARNING",
                )
                reason = "XML parse failed; PDF fallback used."
                if selection_note:
                    reason = f"{reason} {selection_note}"
                self._parse_pdf_fallback(
                    ein,
                    org_name,
                    fallback_pdf_tax_year,
                    deep_object_id,
                    fallback_pdf_url,
                    reason,
                    fallback_total_revenue,
                    fallback_total_expenses,
                    fallback_net_assets,
                )
                self._deep_count += 1
            else:
                self._append_deep_source(
                    ein,
                    org_name,
                    deep_tax_year,
                    "xml",
                    deep_xml_url,
                    deep_object_id,
                    "failed",
                    f"XML URL existed but parsing failed, and no PDF fallback URL was available. {selection_note}".strip(),
                )
        elif self.mode == "deep":
            if deep_pdf_url:
                self.io.log(
                    f"IRS 990 Deep mode: XML unavailable for {org_name}; using PDF fallback for {deep_tax_year or 'latest eligible filing'}.",
                    "INFO",
                )
                self._parse_pdf_fallback(
                    ein,
                    org_name,
                    deep_tax_year,
                    deep_object_id,
                    deep_pdf_url,
                    f"XML/object_id unavailable; PDF fallback used. {selection_note}".strip(),
                    fallback_total_revenue,
                    fallback_total_expenses,
                    fallback_net_assets,
                )
                self._deep_count += 1
            else:
                self.io.log(
                    f"IRS 990 Deep mode skipped for {org_name}: no eligible XML or PDF filing document was available.",
                    "WARNING",
                )
                self._append_deep_source(
                    ein,
                    org_name,
                    deep_tax_year,
                    "none",
                    "",
                    deep_object_id,
                    "unavailable",
                    f"No eligible XML/object_id or PDF filing URL was available for the selected filing window. {selection_note}".strip(),
                )

    def _parse_pdf_fallback(
        self,
        ein: str,
        org_name: str,
        tax_year: str,
        object_id: str,
        pdf_url: str,
        parse_reason: str,
        fallback_total_revenue: str = "0",
        fallback_total_expenses: str = "0",
        fallback_net_assets: str = "0",
    ) -> None:
        parser = IRS990PDFParser(pdf_url)
        if not parser.fetch_and_parse():
            self._append_deep_source(
                ein,
                org_name,
                tax_year,
                "pdf",
                parser.source_url or pdf_url,
                object_id,
                parser.parse_status or "fetch_failed",
                f"{parse_reason} PDF parsing failed: {parser.error}",
            )
            return

        profile = parser.extract_profile()
        total_revenue = self._prefer_filing_total(profile.get("total_revenue", "0"), fallback_total_revenue)
        total_expenses = self._prefer_filing_total(profile.get("total_expenses", "0"), fallback_total_expenses)
        net_assets = self._prefer_filing_total(profile.get("net_assets", "0"), fallback_net_assets)
        self._append_deep_source(
            ein,
            org_name,
            tax_year,
            "pdf",
            parser.source_url or pdf_url,
            object_id,
            "parsed",
            f"{parse_reason} Extraction method: {parser.extraction_method or 'unknown'}.",
        )
        self.io.append_row("irs990_deep_profile", {
            "ein": ein,
            "organization_name": org_name,
            "object_id": object_id,
            "source_type": "pdf",
            "source_url": parser.source_url or pdf_url,
            "parse_status": "parsed",
            "parse_reason": f"{parse_reason} Extraction method: {parser.extraction_method or 'unknown'}.",
            "website": profile.get("website", ""),
            "formation_year": profile.get("formation_year", ""),
            "state_of_domicile": profile.get("state_of_domicile", ""),
            "total_employees": profile.get("total_employees", "0"),
            "total_volunteers": profile.get("total_volunteers", "0"),
            "flag_lobbying": "1" if "Schedule C" in profile.get("schedule_mentions", "") else "0",
            "flag_political_campaign": "0",
            "flag_grants_to_orgs": "1" if "Schedule I" in profile.get("schedule_mentions", "") else "0",
            "voting_board_members": "0",
            "independent_board_members": "0",
            "total_revenue": total_revenue,
            "contributions_and_grants": "0",
            "program_service_revenue": "0",
            "investment_income": "0",
            "government_grants": "0",
            "total_expenses": total_expenses,
            "program_service_expenses": "0",
            "management_expenses": "0",
            "fundraising_expenses": "0",
            "net_assets": net_assets,
            "foreign_spending": "0",
            "mission_excerpt": profile.get("mission_excerpt", ""),
            "program_excerpt": profile.get("program_excerpt", ""),
            "schedule_mentions": profile.get("schedule_mentions", ""),
        })

        try:
            self.io.log(f"IRS 990 Deep mode: Running LLM Enrichment from PDF fallback for {org_name}", "INFO")
            enricher = IRS990LLMEnricher()
            insights = enricher.extract_insights(
                org_name,
                parser.narrative_blocks(),
                {
                    "profile": profile,
                    "financials": {
                        "total_revenue": total_revenue,
                        "total_expenses": total_expenses,
                        "net_assets": net_assets,
                    },
                    "lobbying": {"present": "True" if "Schedule C" in profile.get("schedule_mentions", "") else "False"},
                    "officers": [],
                    "grants": [],
                    "foreign": {"present": "True" if "Schedule F" in profile.get("schedule_mentions", "") else "False"},
                },
            )
            if insights:
                self.io.append_row("irs990_deep_enrichments", {
                    "ein": ein,
                    "object_id": object_id,
                    "pa_relevance_score": insights.get("pa_relevance_score", ""),
                    "one_sentence_org_profile": insights.get("one_sentence_org_profile", ""),
                    "issue_area_tags": insights.get("issue_area_tags", ""),
                    "top_influence_signals": insights.get("top_influence_signals", ""),
                    "top_risk_flags": insights.get("top_risk_flags", ""),
                    "likely_advocacy_tactics_named": insights.get("likely_advocacy_tactics_named", ""),
                    "likely_target_institutions_named": insights.get("likely_target_institutions_named", ""),
                })
        except Exception as exc:
            self.io.log(f"Skipping PDF fallback enrichment for {org_name}: {exc}", "WARNING")

    @staticmethod
    def _prefer_filing_total(parsed_value: str, filing_value: str) -> str:
        filing_digits = len("".join(ch for ch in str(filing_value or "") if ch.isdigit()))
        if filing_digits:
            return str(filing_value or "0")
        return str(parsed_value or "0")
