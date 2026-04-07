import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List, Any


class IRS990XMLParser:
    """
    Deterministic parser for IRS 990 XML filings.
    Extracts structured schedules and data bypassing an LLM.
    """
    def __init__(self, object_id: str):
        self.object_id = object_id
        self.xml_url = f"https://projects.propublica.org/nonprofits/download-xml?object_id={object_id}"
        self.namespace = {"irs": "http://www.irs.gov/efile"}
        self.root = None
        self._form = None  # Cached IRS990 form element

    def fetch_and_parse(self) -> bool:
        """Downloads and parses the XML. Returns True if successful."""
        try:
            req = urllib.request.Request(self.xml_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                xml_data = response.read()
            self.root = ET.fromstring(xml_data)
            return_data = self.root.find("irs:ReturnData", self.namespace)
            if return_data is not None:
                self._form = return_data.find("irs:IRS990", self.namespace)
            return True
        except Exception as e:
            print(f"[WARNING] Failed to fetch/parse XML {self.xml_url}: {e}")
            return False

    def _get_text(self, parent: ET.Element, xpath: str, default: str = "") -> str:
        if parent is None:
            return default
        el = parent.find(f"irs:{xpath}", self.namespace)
        return el.text.strip() if el is not None and el.text else default

    # ------------------------------------------------------------------
    # Organization profile (Part I + Part IV + Part VI)
    # ------------------------------------------------------------------

    def extract_org_profile(self) -> Dict[str, str]:
        """Extracts org-level fields: website, formation, employees, activity flags, governance."""
        if self._form is None:
            return {}

        f = self._form
        g = self._get_text

        profile = {
            "website": g(f, "WebsiteAddressTxt"),
            "formation_year": g(f, "FormationYr"),
            "state_of_domicile": g(f, "LegalDomicileStateCd"),
            "total_employees": g(f, "TotalEmployeeCnt", "0"),
            "total_volunteers": g(f, "TotalVolunteersCnt", "0"),
            # Part IV activity flags (1 = yes, 0 = no)
            "flag_political_campaign": g(f, "PoliticalCampaignActyInd", "0"),
            "flag_lobbying": g(f, "LobbyingActivitiesInd", "0"),
            "flag_grants_to_orgs": g(f, "GrantsToOrganizationsInd", "0"),
            "flag_grants_to_individuals": g(f, "GrantsToIndividualsInd", "0"),
            # Part VI governance
            "voting_board_members": g(f, "VotingMembersGoverningBodyCnt", "0"),
            "independent_board_members": g(f, "VotingMembersIndependentCnt", "0"),
            "conflict_of_interest_policy": g(f, "ConflictOfInterestPolicyInd", "0"),
            "whistleblower_policy": g(f, "WhistleblowerPolicyInd", "0"),
            "document_retention_policy": g(f, "DocumentRetentionPolicyInd", "0"),
        }
        return profile

    # ------------------------------------------------------------------
    # Financial breakdown (revenue + expenses)
    # ------------------------------------------------------------------

    def extract_financials(self) -> Dict[str, str]:
        """Extracts revenue breakdown, expense breakdown, and assets."""
        if self._form is None:
            return {}

        f = self._form
        g = self._get_text

        return {
            # Revenue breakdown
            "total_revenue": g(f, "CYTotalRevenueAmt", "0"),
            "contributions_and_grants": g(f, "CYContributionsGrantsAmt", "0"),
            "program_service_revenue": g(f, "CYProgramServiceRevenueAmt", "0"),
            "investment_income": g(f, "CYInvestmentIncomeAmt", "0"),
            "other_revenue": g(f, "CYOtherRevenueAmt", "0"),
            "government_grants": g(f, "CYGrantsAndSimilarPaidAmt", "0"),
            # Expense breakdown
            "total_expenses": g(f, "CYTotalExpenseAmt", "0"),
            "program_service_expenses": g(f, "TotalProgramServiceExpensesAmt", "0"),
            "management_expenses": g(f, "TotalMgmtAndGeneralExpnssAmt", "0"),
            "fundraising_expenses": g(f, "TotalFundrsngExpensesAmt", "0"),
            # Balance sheet
            "total_assets": g(f, "TotalAssetsEOYAmt", "0"),
            "total_liabilities": g(f, "TotalLiabilitiesEOYAmt", "0"),
            "net_assets": g(f, "NetAssetsOrFundBalancesEOYAmt", "0"),
        }

    # ------------------------------------------------------------------
    # Part VII — Officers, directors, trustees
    # ------------------------------------------------------------------

    def extract_officers(self) -> List[Dict[str, str]]:
        """Extracts Part VII officers, directors, trustees."""
        officers = []
        if self._form is None:
            return officers

        for person in self._form.findall("irs:Form990PartVIISectionAGrp", self.namespace):
            name = self._get_text(person, "PersonNm")
            if not name:
                name = self._get_text(person, "BusinessName/BusinessNameLine1Txt")

            officers.append({
                "name": name,
                "title": self._get_text(person, "TitleTxt", "Officer/Director"),
                "compensation": self._get_text(person, "ReportableCompFromOrgAmt", "0"),
            })
        return officers

    # ------------------------------------------------------------------
    # Schedule C — Lobbying activities
    # ------------------------------------------------------------------

    def extract_schedule_c_lobbying(self) -> Dict[str, str]:
        """Extracts lobbying values from Schedule C."""
        sched_c = self.root.find(".//irs:IRS990ScheduleC", self.namespace)
        if sched_c is None:
            return {"present": "False"}

        lobbying = {"present": "True"}

        # 501(h) election metrics
        lobbying["total_lobbying_expenditures"] = self._get_text(sched_c, "TotalLobbyingExpendituresAmt", "0")
        lobbying["grassroots_lobbying_expenditures"] = self._get_text(sched_c, "GrassrootsLobbyingExpendituresAmt", "0")
        lobbying["direct_lobbying"] = self._get_text(sched_c, "LobbyingNontaxableAmount", "0")

        # Section 162(e) lobbying (non-501(h) orgs)
        lobbying["sect_162e_lobbying"] = self._get_text(sched_c, "Sect162eLobbyingAmt", "0")
        lobbying["other_lobbying_expenditures"] = self._get_text(sched_c, "OtherLobbyingExpendituresAmt", "0")
        lobbying["total_sect_162e_lobbying"] = self._get_text(sched_c, "TotalSection162eLobbyingAmt", "0")
        lobbying["dues_assessment"] = self._get_text(sched_c, "DuesAssessmentAmt", "0")

        return lobbying

    # ------------------------------------------------------------------
    # Schedule I — Domestic grants
    # ------------------------------------------------------------------

    def extract_schedule_i_grants(self) -> List[Dict[str, str]]:
        """Extracts domestic grants from Schedule I."""
        grants = []
        sched_i = self.root.find(".//irs:IRS990ScheduleI", self.namespace)
        if sched_i is None:
            return grants

        # Try multiple tag names used across filing years
        grant_tags = ["RecipientTable", "GrantOrContributionPdDurYrGrp"]
        for tag in grant_tags:
            for g in sched_i.findall(f"irs:{tag}", self.namespace):
                name = self._get_text(g, "RecipientBusinessName/BusinessNameLine1Txt")
                if not name:
                    name = self._get_text(g, "RecipientPersonNm", "(Individual)")
                amount = self._get_text(g, "CashGrantAmt", "0")
                purpose = self._get_text(g, "PurposeOfGrantTxt", "")
                ein = self._get_text(g, "RecipientEIN", "")

                # Try multiple address paths
                city = self._get_text(g, "USAddress/CityNm")
                if not city:
                    city = self._get_text(g, "RecipientUSAddress/CityNm")
                state = self._get_text(g, "USAddress/StateAbbreviationCd")
                if not state:
                    state = self._get_text(g, "RecipientUSAddress/StateAbbreviationCd")

                if name:
                    grants.append({
                        "recipient": name,
                        "recipient_ein": ein,
                        "amount": amount,
                        "purpose": purpose,
                        "city": city,
                        "state": state,
                    })
        return grants

    # ------------------------------------------------------------------
    # Schedule J — Top compensation details
    # ------------------------------------------------------------------

    def extract_schedule_j_compensation(self) -> List[Dict[str, str]]:
        """Extracts Schedule J detailed compensation for key employees."""
        comp = []
        sched_j = self.root.find(".//irs:IRS990ScheduleJ", self.namespace)
        if sched_j is None:
            return comp

        for grp in sched_j.findall("irs:RltdOrgOfficerTrstKeyEmplGrp", self.namespace):
            name = self._get_text(grp, "PersonNm")
            if not name:
                name = self._get_text(grp, "BusinessName/BusinessNameLine1Txt")
            comp.append({
                "name": name,
                "total_compensation_org": self._get_text(grp, "TotalCompensationFilingOrgAmt", "0"),
                "compensation_related_orgs": self._get_text(grp, "CompensationFromRelatedOrgsAmt", "0"),
                "other_compensation": self._get_text(grp, "OtherCompensationAmt", "0"),
            })
        return comp

    # ------------------------------------------------------------------
    # Schedule F — Foreign activities summary
    # ------------------------------------------------------------------

    def extract_schedule_f_foreign(self) -> Dict[str, str]:
        """Extracts foreign activity summary from Schedule F."""
        sched_f = self.root.find(".//irs:IRS990ScheduleF", self.namespace)
        if sched_f is None:
            return {"present": "False"}

        return {
            "present": "True",
            "total_foreign_spending": self._get_text(sched_f, "TotalSpentAmt", "0"),
            "foreign_employees": self._get_text(sched_f, "TotalEmployeeCnt", "0"),
            "foreign_offices": self._get_text(sched_f, "TotalOfficeCnt", "0"),
            "transfers_to_foreign_corp": self._get_text(sched_f, "TransferToForeignCorpInd", "0"),
        }

    # ------------------------------------------------------------------
    # Schedule R — Related organizations
    # ------------------------------------------------------------------

    def extract_schedule_r_related_orgs(self) -> List[Dict[str, str]]:
        """Extracts related organizations from Schedule R."""
        orgs = []
        sched_r = self.root.find(".//irs:IRS990ScheduleR", self.namespace)
        if sched_r is None:
            return orgs

        for part in ["IdDisregardedEntitiesGrp", "IdentificationOfDisregardedEntGrp",
                     "IdRelatedTaxExemptOrgGrp", "IdentificationRelatedTaxExemptOrgGrp",
                     "IdRelatedOrgTxblCorpTrGrp", "IdentificationRelatedTaxableCorpGrp",
                     "IdRelatedOrgTxblPartnershipGrp", "IdentificationRelatedPartnershipGrp"]:
            for o in sched_r.findall(f"irs:{part}", self.namespace):
                name = self._get_text(o, "BusinessName/BusinessNameLine1Txt")
                org_type = self._get_text(o, "ExemptCodeSectionTxt", "Taxable/Disregarded")
                if name:
                    orgs.append({"name": name, "type": org_type})
        return orgs

    # ------------------------------------------------------------------
    # Narrative blocks (for LLM enrichment context)
    # ------------------------------------------------------------------

    def extract_narrative_blocks(self) -> str:
        """Extracts mission and program narrative descriptions for LLM context."""
        blocks = []
        if self._form is not None:
            mission = self._get_text(self._form, "MissionDesc")
            if mission:
                blocks.append(f"MISSION: {mission}")

            for prog in self._form.findall("irs:ProgramServiceAccomplishmentGrp", self.namespace):
                desc = self._get_text(prog, "Desc")
                exp = self._get_text(prog, "ExpenseAmt")
                if desc:
                    blocks.append(f"PROGRAM (Exp: {exp}): {desc}")

        sched_o = self.root.find(".//irs:IRS990ScheduleO", self.namespace)
        if sched_o is not None:
            for exp in sched_o.findall("irs:SupplementalInformationDetail", self.namespace):
                text = self._get_text(exp, "ExplanationTxt")
                if text:
                    blocks.append(f"SCHEDULE O: {text}")

        return "\n\n".join(blocks)

    # ------------------------------------------------------------------
    # Full extraction
    # ------------------------------------------------------------------

    def extract_all(self) -> Dict[str, Any]:
        """Extracts all PA-relevant fields from the XML."""
        if self.root is None:
            return {}

        return {
            "object_id": self.object_id,
            "xml_url": self.xml_url,
            "org_profile": self.extract_org_profile(),
            "financials": self.extract_financials(),
            "officers": self.extract_officers(),
            "lobbying_schedule_c": self.extract_schedule_c_lobbying(),
            "domestic_grants_schedule_i": self.extract_schedule_i_grants(),
            "compensation_schedule_j": self.extract_schedule_j_compensation(),
            "foreign_activity_schedule_f": self.extract_schedule_f_foreign(),
            "related_orgs_schedule_r": self.extract_schedule_r_related_orgs(),
            "narrative_blocks": self.extract_narrative_blocks(),
        }
