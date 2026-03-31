from collections import defaultdict
from datetime import datetime
from io_utils import IOUtils


PERIOD_DISPLAY = {
    "first_quarter": "Q1", "second_quarter": "Q2",
    "third_quarter": "Q3", "fourth_quarter": "Q4",
}

SEARCH_FIELD_LABEL = {
    "client": "Client filings",
    "registrant": "Lobbying firm filings",
    "both": "Client and lobbying firm filings",
}


class ReportGenerator:
    def __init__(self, io_utils: IOUtils, config: dict):
        self.io = io_utils
        self.config = config

    def _period_sort_key(self, period: str) -> int:
        order = {"first_quarter": 1, "second_quarter": 2, "third_quarter": 3, "fourth_quarter": 4}
        return order.get(period, 9)

    def _parse_date_for_sort(self, date_str: str) -> str:
        """Normalize MM/DD/YYYY to YYYY-MM-DD for sorting."""
        if not date_str:
            return ""
        date_str = date_str.strip()
        if "/" in date_str:
            parts = date_str.split("/")
            if len(parts) == 3:
                return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        return date_str[:10]

    def _title_case_name(self, name: str) -> str:
        """Convert ALL-CAPS names to Title Case for readability."""
        if name == name.upper() and len(name) > 3:
            # Keep acronyms like LLC, LLP intact
            words = name.split()
            result = []
            for w in words:
                if w in ("LLC", "LLP", "LP", "INC", "PC", "PA", "US", "USA", "DC", "II", "III", "IV"):
                    result.append(w)
                elif w.endswith(","):
                    result.append(w[:-1].title() + ",")
                else:
                    result.append(w.title())
            return " ".join(result)
        return name

    def generate(self):
        self.io.log("Generating Markdown Report...", "INFO")

        lines = []
        master = self.io.datasets.get("master_results", [])
        lda_filings = self.io.datasets.get("lda_filings", [])
        lda_issues = self.io.datasets.get("lda_issues", [])
        lda_lobbyists = self.io.datasets.get("lda_lobbyists", [])
        irs990_filings = self.io.datasets.get("irs990_filings", [])
        irs990_enrichments = self.io.datasets.get("irs990_deep_enrichments", [])

        search_field = self.config.get("search_field", "client")
        scope_label = SEARCH_FIELD_LABEL.get(search_field, "Client filings")

        # =====================================================================
        # HEADER
        # =====================================================================
        lines.append("# Influence Disclosure Tracker")
        lines.append("")
        lines.append("| | |")
        lines.append("|---|---|")
        lines.append(f"| **Report date** | {datetime.now().strftime('%B %d, %Y')} |")
        lines.append(f"| **Entities queried** | {', '.join(self.config['entities'])} |")

        filing_years = self.config.get('filing_years')
        filing_periods = self.config.get('filing_periods')
        if filing_years:
            years_sorted = sorted(filing_years)
            if len(years_sorted) > 3:
                years_str = f"{years_sorted[0]}–{years_sorted[-1]}"
            else:
                years_str = ", ".join(str(y) for y in years_sorted)
            period_str = ", ".join(filing_periods) if filing_periods else "All quarters"
            timeframe = f"{years_str} ({period_str})"
        else:
            timeframe = "All available records"
        lines.append(f"| **Timeframe** | {timeframe} |")
        lines.append(f"| **Search scope** | {scope_label} |")
        lines.append("")

        # =====================================================================
        # EXECUTIVE SUMMARY
        # =====================================================================
        lines.append("---")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append("")

        for ent in self.config['entities']:
            ent_records = [r for r in master if r['entity_query'].lower() == ent.lower()]
            lda_count = len([r for r in ent_records if r['source'] == 'LDA'])
            fara_count = len([r for r in ent_records if r['source'] == 'FARA'])
            irs990_count = len([r for r in ent_records if r['source'] == 'IRS990'])

            total = 0.0
            for r in ent_records:
                try:
                    total += float(r.get('amount') or 0)
                except (ValueError, TypeError):
                    pass

            # Count unique outside firms
            firms = set()
            for f in lda_filings:
                if not f.get('self_filer') or f.get('self_filer') in ('False', 'false', False):
                    firms.add(f.get('registrant_name', ''))

            lines.append(f"### {ent}")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|---|---|")
            lines.append(f"| LDA filings | {lda_count} |")
            if total > 0:
                lines.append(f"| Total lobbying expenditure | ${total:,.0f} |")
            if firms:
                lines.append(f"| Outside lobbying firms retained | {len(firms)} |")
            if fara_count:
                lines.append(f"| FARA records | {fara_count} |")
            if irs990_count:
                lines.append(f"| IRS 990 filings | {irs990_count} |")
            lines.append("")

            # Client description as blockquote
            for r in ent_records:
                desc = (r.get('client_description') or '').strip()
                if desc and len(desc) > 10:
                    lines.append(f"> {desc}")
                    lines.append("")
                    break

        # =====================================================================
        # LOBBYING ACTIVITY BY FIRM
        # =====================================================================
        lines.append("---")
        lines.append("")
        lines.append("## Lobbying Activity by Firm")
        lines.append("")

        # Group data by registrant
        filings_by_reg = defaultdict(list)
        for f in lda_filings:
            filings_by_reg[f.get('registrant_name', 'Unknown')].append(f)

        issues_by_reg = defaultdict(list)
        for iss in lda_issues:
            issues_by_reg[iss.get('registrant', 'Unknown')].append(iss)

        lobs_by_reg = defaultdict(list)
        for lob in lda_lobbyists:
            lobs_by_reg[lob.get('registrant', 'Unknown')].append(lob)

        for reg_name in sorted(filings_by_reg.keys()):
            reg_filings = filings_by_reg[reg_name]
            is_self = any(f.get('self_filer') in (True, 'True', 'true') for f in reg_filings)

            display_name = self._title_case_name(reg_name)
            lines.append(f"### {display_name}")
            lines.append("")

            if is_self:
                lines.append("*In-house lobbying operation*")
            else:
                clients = sorted(set(f.get('client_name', '') for f in reg_filings))
                client_display = ", ".join(self._title_case_name(c) for c in clients)
                lines.append(f"**Client:** {client_display}")
            lines.append("")

            # --- Quarterly Spending Table ---
            lines.append("#### Quarterly Spending")
            lines.append("")
            lines.append("| Year | Quarter | Filing Type | Amount |")
            lines.append("|:---|:---|:---|---:|")

            sorted_filings = sorted(
                reg_filings,
                key=lambda f: (f.get('filing_year', ''), self._period_sort_key(f.get('filing_period', '')))
            )
            reg_total = 0.0
            for f in sorted_filings:
                year = f.get('filing_year', '')
                period = PERIOD_DISPLAY.get(f.get('filing_period', ''), f.get('filing_period', ''))
                ftype = f.get('filing_type', '')
                amt = f.get('amount') or ''
                if amt:
                    try:
                        amt_f = float(amt)
                        reg_total += amt_f
                        amt = f"${amt_f:,.0f}"
                    except (ValueError, TypeError):
                        pass
                else:
                    amt = "—"
                lines.append(f"| {year} | {period} | {ftype} | {amt} |")

            if reg_total > 0:
                lines.append(f"| | | **Total** | **${reg_total:,.0f}** |")
            lines.append("")

            # --- Issues Lobbied ---
            reg_issues = issues_by_reg.get(reg_name, [])
            if reg_issues:
                issue_groups = defaultdict(lambda: {"descriptions": set(), "gov_entities": set()})
                for iss in reg_issues:
                    area = iss.get('issue_area', iss.get('issue_code', 'Other'))
                    desc = (iss.get('description') or '').strip()
                    if desc:
                        issue_groups[area]["descriptions"].add(desc)
                    for ge in (iss.get('government_entities', '') or '').split('; '):
                        if ge.strip():
                            issue_groups[area]["gov_entities"].add(ge.strip())

                lines.append("#### Issues Lobbied")
                lines.append("")
                lines.append("| Issue Area | Description | Government Entities |")
                lines.append("|:---|:---|:---|")
                for area, info in sorted(issue_groups.items()):
                    descs = "; ".join(sorted(info["descriptions"])) if info["descriptions"] else "—"
                    gov = ", ".join(sorted(info["gov_entities"])) if info["gov_entities"] else "—"
                    lines.append(f"| {area} | {descs} | {gov} |")
                lines.append("")

            # --- Lobbyists ---
            reg_lobs = lobs_by_reg.get(reg_name, [])
            if reg_lobs:
                seen = {}
                for lob in reg_lobs:
                    name = (lob.get('lobbyist_name') or '').strip()
                    if name and name not in seen:
                        seen[name] = (lob.get('covered_position') or '').strip()

                lines.append("#### Registered Lobbyists")
                lines.append("")
                lines.append("| Name | Former Government Position |")
                lines.append("|:---|:---|")
                for name in sorted(seen.keys()):
                    position = seen[name]
                    display_name_lob = self._title_case_name(name)
                    if position:
                        lines.append(f"| **{display_name_lob}** | {position} |")
                    else:
                        lines.append(f"| {display_name_lob} | — |")
                lines.append("")

            lines.append("---")
            lines.append("")

        # =====================================================================
        # FARA
        # =====================================================================
        lines.append("## FARA Foreign Agent Filings")
        lines.append("")
        fara_master = [r for r in master if r['source'] == 'FARA']
        fara_registrants = self.io.datasets.get("fara_registrants", [])
        fara_fps = self.io.datasets.get("fara_foreign_principals", [])
        fara_docs = self.io.datasets.get("fara_documents", [])

        if fara_master:
            # Group by registration number
            from collections import OrderedDict
            reg_groups = OrderedDict()
            for fm in fara_master:
                rnum = fm.get('id_primary', '')
                if rnum not in reg_groups:
                    reg_groups[rnum] = fm

            for rnum, fm in reg_groups.items():
                reg_name = self._title_case_name(fm.get('registrant', ''))
                status = fm.get('filing_period', '')

                # Registrant info
                reg_info = next((r for r in fara_registrants
                                 if r.get('registration_number') == rnum), {})

                # Header: use registrant name
                lines.append(f"### {reg_name}")
                lines.append("")

                # Registration details table
                lines.append("| | |")
                lines.append("|---|---|")
                lines.append(f"| **Registration #** | {rnum} |")
                if reg_info.get('registration_date'):
                    lines.append(f"| **Registered** | {reg_info['registration_date']} |")
                if reg_info.get('termination_date'):
                    lines.append(f"| **Terminated** | {reg_info['termination_date']} |")
                elif status:
                    lines.append(f"| **Status** | {status} |")
                if reg_info.get('address'):
                    addr_parts = [reg_info.get('address', '')]
                    if reg_info.get('city'):
                        addr_parts.append(reg_info['city'])
                    if reg_info.get('state'):
                        addr_parts.append(reg_info['state'])
                    lines.append(f"| **Location** | {', '.join(p for p in addr_parts if p)} |")
                lines.append("")

                # Foreign principals table
                reg_fps = [fp for fp in fara_fps if fp.get('registration_number') == rnum]
                if reg_fps:
                    seen_fp_names = set()
                    unique_fps = []
                    for fp in reg_fps:
                        fp_name = fp.get('foreign_principal_name', '')
                        if fp_name and fp_name not in seen_fp_names:
                            seen_fp_names.add(fp_name)
                            unique_fps.append(fp)

                    lines.append("#### Foreign Principals")
                    lines.append("")
                    lines.append("| Foreign Principal | Country | Registered | Terminated |")
                    lines.append("|:---|:---|:---|:---|")
                    for fp in unique_fps:
                        fp_name_display = self._title_case_name(fp.get('foreign_principal_name', ''))
                        country = fp.get('state_or_country', '—')
                        fp_reg = fp.get('foreign_principal_date', '—') or '—'
                        fp_term = fp.get('foreign_principal_term_date', '') or '—'
                        lines.append(f"| **{fp_name_display}** | {country} | {fp_reg} | {fp_term} |")
                    lines.append("")

                # Documents (filings with links)
                reg_docs = [d for d in fara_docs if d.get('registration_number') == rnum]
                if reg_docs:
                    # Sort by date descending
                    reg_docs.sort(key=lambda d: self._parse_date_for_sort(d.get('document_date', '')), reverse=True)

                    lines.append("#### Filed Documents")
                    lines.append("")
                    lines.append("| Date | Type | Foreign Principal | Link |")
                    lines.append("|:---|:---|:---|:---|")
                    for doc in reg_docs:
                        doc_date = doc.get('document_date', '—')
                        doc_type = doc.get('document_type', '—')
                        doc_fp = self._title_case_name(doc.get('foreign_principal_name', '') or '—')
                        doc_url = doc.get('document_url', '')
                        link = f"[View]({doc_url})" if doc_url else "—"
                        lines.append(f"| {doc_date} | {doc_type} | {doc_fp} | {link} |")
                    lines.append("")

                lines.append("---")
                lines.append("")
        else:
            lines.append("No FARA records matched the specified entities.")
        lines.append("")

        # =====================================================================
        # IRS 990
        # =====================================================================
        lines.append("---")
        lines.append("")
        lines.append("## Nonprofit Tax Filings (IRS Form 990)")
        lines.append("")
        irs990_master = [r for r in master if r['source'] == 'IRS990']
        irs990_deep_profile = self.io.datasets.get("irs990_deep_profile", [])
        irs990_deep_grants = self.io.datasets.get("irs990_deep_grants", [])
        irs990_deep_compensation = self.io.datasets.get("irs990_deep_compensation", [])
        irs990_deep_lobbying = self.io.datasets.get("irs990_deep_lobbying", [])
        irs990_deep_officers = self.io.datasets.get("irs990_deep_officers", [])

        if irs990_master:
            from collections import OrderedDict
            org_groups = OrderedDict()
            for row in irs990_master:
                name = row.get("registrant", "")
                if name not in org_groups:
                    org_groups[name] = []
                org_groups[name].append(row)

            def fmt_dollar(val):
                try:
                    v = float(val)
                    if v == 0:
                        return "—"
                    return f"${v:,.0f}"
                except (ValueError, TypeError):
                    return str(val) if val else "—"

            for org_name, org_filings in org_groups.items():
                lines.append(f"### {self._title_case_name(org_name)}")
                lines.append("")

                # Find EIN for this org
                org_ein = None
                for f in irs990_filings:
                    if f.get("organization_name") == org_name:
                        org_ein = f.get("ein")
                        break
                if not org_ein:
                    org_orgs = self.io.datasets.get("irs990_organizations", [])
                    for o in org_orgs:
                        if o.get("organization_name") == org_name:
                            org_ein = o.get("ein")
                            break

                # Check for Deep Enrichment
                enrich = next((e for e in irs990_enrichments if e.get("ein") == org_ein and e.get("one_sentence_org_profile", "").strip()), None)
                if enrich:
                    lines.append(f"> **AI Summary:** {enrich.get('one_sentence_org_profile')}")
                    lines.append("> ")
                    lines.append(f"> **PA Relevance Score:** {enrich.get('pa_relevance_score')}")
                    lines.append(f"> **Issues:** {enrich.get('issue_area_tags')}")
                    lines.append(f"> **Tactics:** {enrich.get('likely_advocacy_tactics_named')}")
                    lines.append("")

                # Deep Profile (org overview from XML)
                profile = next((p for p in irs990_deep_profile if p.get("ein") == org_ein), None)
                if profile:
                    lines.append("#### Organization Profile")
                    lines.append("")
                    lines.append("| | |")
                    lines.append("|---|---|")
                    if profile.get("website"):
                        lines.append(f"| **Website** | {profile['website']} |")
                    if profile.get("formation_year"):
                        lines.append(f"| **Founded** | {profile['formation_year']} |")
                    if profile.get("state_of_domicile"):
                        lines.append(f"| **State** | {profile['state_of_domicile']} |")
                    lines.append(f"| **Employees** | {profile.get('total_employees', '0')} |")
                    lines.append(f"| **Volunteers** | {profile.get('total_volunteers', '0')} |")
                    lines.append(f"| **Board members** | {profile.get('voting_board_members', '0')} (independent: {profile.get('independent_board_members', '0')}) |")
                    # Activity flags
                    flags = []
                    if profile.get("flag_lobbying") not in ("0", "", "false", "False"):
                        flags.append("Lobbying")
                    if profile.get("flag_political_campaign") not in ("0", "", "false", "False"):
                        flags.append("Political Campaign")
                    if profile.get("flag_grants_to_orgs") not in ("0", "", "false", "False"):
                        flags.append("Grants to Organizations")
                    if flags:
                        lines.append(f"| **Activity flags** | {', '.join(flags)} |")
                    lines.append("")

                    # Financial breakdown
                    lines.append("#### Financial Breakdown (Latest XML Filing)")
                    lines.append("")
                    lines.append("| Category | Amount |")
                    lines.append("|:---|---:|")
                    lines.append(f"| **Total Revenue** | {fmt_dollar(profile.get('total_revenue'))} |")
                    lines.append(f"| Contributions & Grants | {fmt_dollar(profile.get('contributions_and_grants'))} |")
                    lines.append(f"| Program Service Revenue | {fmt_dollar(profile.get('program_service_revenue'))} |")
                    lines.append(f"| Investment Income | {fmt_dollar(profile.get('investment_income'))} |")
                    lines.append(f"| Government Grants | {fmt_dollar(profile.get('government_grants'))} |")
                    lines.append(f"| **Total Expenses** | {fmt_dollar(profile.get('total_expenses'))} |")
                    lines.append(f"| Program Services | {fmt_dollar(profile.get('program_service_expenses'))} |")
                    lines.append(f"| Management & General | {fmt_dollar(profile.get('management_expenses'))} |")
                    lines.append(f"| Fundraising | {fmt_dollar(profile.get('fundraising_expenses'))} |")
                    lines.append(f"| **Net Assets** | {fmt_dollar(profile.get('net_assets'))} |")
                    if profile.get("foreign_spending") not in ("0", "", None):
                        lines.append(f"| Foreign Spending | {fmt_dollar(profile.get('foreign_spending'))} |")
                    lines.append("")

                # Filings table
                lines.append("#### Filing History")
                lines.append("")
                lines.append("| Year | Form Type | Revenue | Expenses | Net Assets | Link |")
                lines.append("|:---|:---|---:|---:|---:|:---|")

                org_detail = [f for f in irs990_filings if f.get("organization_name") == org_name]
                org_detail.sort(key=lambda x: str(x.get("tax_year", "")), reverse=True)

                for detail in org_detail:
                    year = detail.get("tax_year", "")
                    ftype = detail.get("form_type", "")
                    pdf = detail.get("pdf_url", "")
                    link = f"[View PDF]({pdf})" if pdf else ""
                    rev = fmt_dollar(detail.get("total_revenue"))
                    exp = fmt_dollar(detail.get("total_functional_expenses"))
                    ast = fmt_dollar(detail.get("net_assets"))
                    lines.append(f"| {year} | {ftype} | {rev} | {exp} | {ast} | {link} |")
                lines.append("")

                # Lobbying (Schedule C)
                lob = next((l for l in irs990_deep_lobbying if l.get("ein") == org_ein and l.get("schedule_c_present") == "True"), None)
                if lob:
                    lines.append("#### Lobbying Activity (Schedule C)")
                    lines.append("")
                    lines.append("| Category | Amount |")
                    lines.append("|:---|---:|")
                    lines.append(f"| Total Lobbying | {fmt_dollar(lob.get('total_lobbying'))} |")
                    lines.append(f"| Grassroots Lobbying | {fmt_dollar(lob.get('grassroots_lobbying'))} |")
                    lines.append(f"| Direct Lobbying | {fmt_dollar(lob.get('direct_lobbying'))} |")
                    if lob.get("total_sect_162e") not in ("0", "", None):
                        lines.append(f"| Section 162(e) Lobbying | {fmt_dollar(lob.get('total_sect_162e'))} |")
                    lines.append("")

                # Top Compensation (Schedule J + Part VII)
                org_comp = [c for c in irs990_deep_compensation if c.get("ein") == org_ein]
                org_officers = [o for o in irs990_deep_officers if o.get("ein") == org_ein]
                if org_comp:
                    lines.append("#### Top Compensation (Schedule J)")
                    lines.append("")
                    lines.append("| Name | From Organization | From Related Orgs | Other |")
                    lines.append("|:---|---:|---:|---:|")
                    for c in org_comp:
                        lines.append(f"| {c.get('name', '')} | {fmt_dollar(c.get('total_compensation_org'))} | {fmt_dollar(c.get('compensation_related_orgs'))} | {fmt_dollar(c.get('other_compensation'))} |")
                    lines.append("")
                elif org_officers:
                    # Fall back to Part VII officers if no Schedule J
                    top_officers = sorted(org_officers, key=lambda o: float(o.get("compensation", "0") or "0"), reverse=True)[:10]
                    paid_officers = [o for o in top_officers if float(o.get("compensation", "0") or "0") > 0]
                    if paid_officers:
                        lines.append("#### Key Officers & Compensation (Part VII)")
                        lines.append("")
                        lines.append("| Name | Title | Compensation |")
                        lines.append("|:---|:---|---:|")
                        for o in paid_officers:
                            lines.append(f"| {o.get('name', '')} | {o.get('title', '')} | {fmt_dollar(o.get('compensation'))} |")
                        lines.append("")

                # Grants (Schedule I)
                org_grants = [g for g in irs990_deep_grants if g.get("ein") == org_ein]
                if org_grants:
                    lines.append("#### Grants Made (Schedule I)")
                    lines.append("")
                    lines.append("| Recipient | Amount | Purpose | Location |")
                    lines.append("|:---|---:|:---|:---|")
                    # Sort by amount descending
                    org_grants.sort(key=lambda g: float(g.get("amount", "0") or "0"), reverse=True)
                    for g in org_grants:
                        loc_parts = [g.get("city", ""), g.get("state", "")]
                        loc = ", ".join(p for p in loc_parts if p) or "—"
                        purpose = g.get("purpose", "—") or "—"
                        lines.append(f"| {g.get('recipient', '')} | {fmt_dollar(g.get('amount'))} | {purpose} | {loc} |")
                    lines.append("")

                lines.append("")
        else:
            lines.append("No IRS 990 records matched the specified entities.")
        lines.append("")

        # =====================================================================
        # MATCHING CONFIDENCE
        # =====================================================================
        lines.append("---")
        lines.append("")
        lines.append("## Appendix: Matching Confidence")
        lines.append("")
        lines.append("| Query | Matched Name | Match Type | Confidence |")
        lines.append("|:---|:---|:---|---:|")

        seen_matches = set()
        for r in master:
            matched_name = r.get('client', r.get('registrant', ''))
            match_key = (r['entity_query'], matched_name, r['match_type'])
            if match_key not in seen_matches:
                seen_matches.add(match_key)
                lines.append(f"| {r['entity_query']} | {matched_name} | {r['match_type']} | {r['match_confidence']}% |")
        lines.append("")

        # Write to file
        with open(self.io.report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        self.io.log(f"Report saved to {self.io.report_path}", "INFO")
