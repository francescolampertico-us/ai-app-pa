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
            else:
                lines.append("| FARA records | None |")
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
