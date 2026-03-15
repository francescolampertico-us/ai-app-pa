import os
from datetime import datetime
from io_utils import IOUtils

class ReportGenerator:
    def __init__(self, io_utils: IOUtils, config: dict):
        self.io = io_utils
        self.config = config

    def generate(self):
        self.io.log("Generating Markdown Report...", "INFO")
        
        lines = []
        lines.append("# Influence Disclosure Tracker Report")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Entities Queried:** `{', '.join(self.config['entities'])}`")
        lines.append(f"**Timeframe:** {self.config['from_date']} to {self.config['to_date']}")
        lines.append("")
        
        master = self.io.datasets.get("master_results", [])
        
        # 1. Executive Summary
        lines.append("## 1. Executive Summary")
        for ent in self.config['entities']:
            ent_records = [r for r in master if r['entity_query'].lower() == ent.lower()]
            lda_count = len([r for r in ent_records if r['source'] == 'LDA'])
            fara_count = len([r for r in ent_records if r['source'] == 'FARA'])
            
            lines.append(f"### Entity: **{ent}**")
            lines.append(f"- **LDA Hits:** {lda_count}")
            lines.append(f"- **FARA Hits:** {fara_count}")
            lines.append("")
        
        # 2. LDA Details
        lines.append("## 2. LDA Filings Summary")
        lda_filings = self.io.datasets.get("lda_filings", [])
        if lda_filings:
            lines.append("| Registrant | Client | Year | Period | Amount | URL |")
            lines.append("|---|---|---|---|---|---|")
            for f in lda_filings:
                amt = f.get('amount_reported') or "N/A"
                url_cell = f"[Link]({f['filing_url']})" if f.get('filing_url') else "N/A"
                lines.append(f"| {f.get('registrant_name')} | {f.get('client_name')} | {f.get('filing_year')} | {f.get('filing_period')} | {amt} | {url_cell} |")
        else:
            lines.append("*No LDA filings found for the specified entities and timeframe.*")
        lines.append("")

        # 3. FARA Details
        lines.append("## 3. FARA Highlights Summary")
        fara_master = [r for r in master if r['source'] == 'FARA']
        
        if fara_master:
            for fm in fara_master:
                name = fm.get('name_primary', '')
                rnum = fm.get('id_primary', '')
                rtype = fm.get('record_type', '').replace('fara_', '').replace('_', ' ').title()
                desc = fm.get('description', '')
                
                lines.append(f"### {rtype}: {name} (#{rnum})")
                lines.append(f"- **Role / Status:** {desc}")
                
                # Associated Principals (if this was a registrant hit)
                fps = [fp for fp in self.io.datasets.get("fara_foreign_principals", []) if fp.get('registration_number') == rnum]
                if "Registrant" in rtype and fps:
                    lines.append("- **Foreign Principals Represented:**")
                    seen_fps = set()
                    for fp in fps:
                        fp_name = fp.get('foreign_principal_name')
                        if fp_name not in seen_fps:
                            seen_fps.add(fp_name)
                            lines.append(f"  - {fp_name} ({fp.get('state_or_country')})")
                
                # Associated Docs
                docs = [d for d in self.io.datasets.get("fara_documents", []) if str(d.get('registration_number')) == str(rnum)]
                if docs:
                    lines.append(f"- **Recent Documents (Up to 5):**")
                    for d in docs[:5]:
                        lines.append(f"  - {d.get('document_date')} - [{d.get('document_type')}]({d.get('document_url')})")
                lines.append("")
        else:
            lines.append("*No FARA records matched the specified entities.*")
        lines.append("")

        # 4. Matching Notes
        lines.append("## 4. Matching Confidence Notes")
        lines.append("The tool uses Exact, Contains, and Fuzzy string matching algorithms. Matches with <100% confidence should be manually verified.")
        lines.append("| Source | Query | Matched Name | Match Type | Confidence |")
        lines.append("|---|---|---|---|---|")
        
        # deduplicate matches for summary
        seen_matches = set()
        for r in master:
            match_key = (r['source'], r['entity_query'], r['name_primary'], r['match_type'], r['match_confidence'])
            if match_key not in seen_matches:
                seen_matches.add(match_key)
                lines.append(f"| {r['source']} | {r['entity_query']} | {r['name_primary']} | {r['match_type']} | {r['match_confidence']}% |")
        lines.append("")
        
        # Write to file
        with open(self.io.report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        self.io.log(f"Report saved to {self.io.report_path}", "INFO")
