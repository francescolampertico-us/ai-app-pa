"""
Influence Disclosure Tracker — Streamlit Page
================================================
Query LDA and FARA disclosure records for entities.
"""

import streamlit as st
import sys
import subprocess
import tempfile
import csv as csv_mod
import io
from datetime import datetime
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "influence_disclosure_tracker"
sys.path.insert(0, str(TOOLKIT_ROOT / "app"))

st.set_page_config(page_title="Disclosure Tracker", page_icon="🔍", layout="wide")

from shared import page_header, demo_banner
page_header(
    title="Influence Disclosure Tracker",
    icon="🔍",
    version="0.1.0",
    risk="yellow",
    digiacomo="#2 Stakeholder Analysis",
    description="Retrieves and normalizes lobbying (LDA) and foreign principal (FARA) disclosure "
                "records, producing CSV tables and a markdown summary report.",
)

# --- Inputs ---
entities = st.text_input(
    "Entities to search",
    placeholder="e.g., Microsoft, OpenAI",
    help="Comma-separated list of organization names",
)

search_scope = st.radio(
    "Search scope",
    options=["Client", "Lobbying firm (registrant)", "Both"],
    horizontal=True,
    help="**Client:** the entity being represented (e.g., OpenAI). "
         "**Lobbying firm:** the firm filing on behalf of a client (e.g., Akin Gump). "
         "**Both:** search across both fields.",
)
search_field_map = {"Client": "client", "Lobbying firm (registrant)": "registrant", "Both": "both"}
search_field = search_field_map[search_scope]

col1, col2, col3 = st.columns(3)
with col1:
    current_year = datetime.now().year
    all_years = st.checkbox("All available years", value=False)
    if all_years:
        filing_years = list(range(current_year, 1999, -1))
        st.caption(f"Will search {current_year}–2000")
    else:
        available_years = list(range(current_year, 1999, -1))
        filing_years = st.multiselect(
            "Filing year(s)",
            options=available_years,
            default=[current_year - 1],
            help="Select one or more years",
        )
with col2:
    quarters = st.multiselect(
        "Quarters",
        options=["Q1", "Q2", "Q3", "Q4"],
        default=["Q1", "Q2", "Q3", "Q4"],
        help="Select which quarters to include",
    )
with col3:
    sources = st.multiselect("Data sources", ["lda", "fara"], default=["lda"])

with st.expander("Advanced options"):
    adv_col1, adv_col2 = st.columns(2)
    with adv_col1:
        max_results = st.number_input("Max results per entity", value=500, min_value=10, max_value=5000)
    with adv_col2:
        fuzzy_threshold = st.slider("Fuzzy match threshold", 50, 100, 85)
    dry_run = st.checkbox("Dry run (skip API calls)")


def _rows_to_csv(rows: list[dict], headers: list[str]) -> str:
    """Convert list of dicts to CSV string."""
    buf = io.StringIO()
    writer = csv_mod.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


# --- Run ---
demo = demo_banner()

if entities and st.button("Search Disclosures", type="primary", disabled=demo):
    if not quarters:
        st.warning("Select at least one quarter.")
    elif not filing_years and not all_years:
        st.warning("Select at least one year.")
    else:
        spinner_msg = "Querying disclosure databases..."
        if "fara" in sources:
            spinner_msg = "Querying disclosure databases (FARA searches may take longer)..."
        with st.spinner(spinner_msg):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    cmd = [
                        sys.executable,
                        str(TOOL_ROOT / "execution" / "run.py"),
                        "--entities", entities,
                        "--search-field", search_field,
                    ]
                    if not all_years:
                        cmd += ["--filing-years", ",".join(str(y) for y in filing_years)]
                    cmd += [
                        "--filing-periods", ",".join(quarters),
                        "--sources", ",".join(sources),
                        "--out", tmpdir,
                        "--max-results", str(max_results),
                        "--fuzzy-threshold", str(fuzzy_threshold),
                    ]
                    if dry_run:
                        cmd.append("--dry-run")

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300,
                        cwd=str(TOOL_ROOT / "execution"),
                    )

                    # Store in session state so data persists after tmpdir cleanup
                    st.session_state["dt_stdout"] = result.stdout or ""
                    st.session_state["dt_stderr"] = result.stderr or ""

                    output_path = Path(tmpdir)

                    # Read report
                    report_files = list(output_path.rglob("report.md"))
                    st.session_state["dt_report"] = report_files[0].read_text() if report_files else ""

                    # Read CSVs into session state
                    csv_data = {}
                    for csv_file in output_path.rglob("*.csv"):
                        try:
                            reader = csv_mod.DictReader(io.StringIO(csv_file.read_text()))
                            csv_data[csv_file.stem] = list(reader)
                        except Exception:
                            pass
                    st.session_state["dt_csv_data"] = csv_data
                    st.session_state["dt_has_results"] = True

            except subprocess.TimeoutExpired:
                st.error("Search timed out after 5 minutes. Try fewer entities or narrower filters.")
                st.session_state["dt_has_results"] = False
            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())
                st.session_state["dt_has_results"] = False

def _extract_matched_names(csv_data: dict) -> tuple[list[str], list[str]]:
    """Extract unique client and registrant names separately from CSV data."""
    clients = set()
    registrants = set()
    for r in csv_data.get("lda_filings", []):
        registrants.add(r.get("registrant_name", ""))
        clients.add(r.get("client_name", ""))
    for r in csv_data.get("lda_issues", []):
        registrants.add(r.get("registrant", ""))
        clients.add(r.get("client", ""))
    for r in csv_data.get("lda_lobbyists", []):
        registrants.add(r.get("registrant", ""))
        clients.add(r.get("client", ""))
    # FARA
    for r in csv_data.get("fara_foreign_principals", []):
        registrants.add(r.get("registrant_name", ""))
        clients.add(r.get("foreign_principal_name", ""))
    clients.discard("")
    registrants.discard("")
    return sorted(clients), sorted(registrants)


def _filter_csv_data(csv_data: dict, allowed_names: set) -> dict:
    """Filter all CSV datasets to only include rows matching allowed names."""
    filtered = {}
    filtered["lda_filings"] = [
        r for r in csv_data.get("lda_filings", [])
        if r.get("registrant_name", "") in allowed_names
        or r.get("client_name", "") in allowed_names
    ]
    filtered["lda_issues"] = [
        r for r in csv_data.get("lda_issues", [])
        if r.get("registrant", "") in allowed_names
        or r.get("client", "") in allowed_names
    ]
    filtered["lda_lobbyists"] = [
        r for r in csv_data.get("lda_lobbyists", [])
        if r.get("registrant", "") in allowed_names
        or r.get("client", "") in allowed_names
    ]
    # FARA
    filtered["fara_foreign_principals"] = [
        r for r in csv_data.get("fara_foreign_principals", [])
        if r.get("registrant_name", "") in allowed_names
        or r.get("foreign_principal_name", "") in allowed_names
    ]
    filtered["fara_registrants"] = [
        r for r in csv_data.get("fara_registrants", [])
        if r.get("registrant_name", "") in allowed_names
    ]
    filtered["fara_documents"] = [
        r for r in csv_data.get("fara_documents", [])
        if r.get("registrant_name", "") in allowed_names
        or r.get("foreign_principal_name", "") in allowed_names
    ]
    filtered["fara_short_forms"] = csv_data.get("fara_short_forms", [])
    return filtered


def _filter_report(report_text: str, allowed_names: set) -> str:
    """Filter the markdown report to only include sections for allowed entities."""
    if not report_text:
        return ""

    import re

    # Build case-insensitive lookup (report may title-case names via _title_case_name)
    allowed_lower = {n.lower() for n in allowed_names}

    # Split into sections by ## and ### headers, preserving preamble
    lines = report_text.split("\n")
    preamble = []  # lines before the first ## header
    sections = []  # list of (header_line, body_lines)
    current_header = None
    current_body = []

    for line in lines:
        if line.startswith("### ") or line.startswith("## "):
            if current_header is not None:
                sections.append((current_header, current_body))
            elif current_body:
                preamble = current_body
            current_header = line
            current_body = []
        else:
            current_body.append(line)
    if current_header is not None:
        sections.append((current_header, current_body))

    output_lines = list(preamble)
    in_filterable = False
    in_fara = False

    for header, body in sections:
        if header.startswith("## "):
            if "Lobbying Activity" in header:
                in_filterable = True
                in_fara = False
            elif "FARA Foreign Agent" in header:
                in_filterable = True
                in_fara = True
            else:
                in_filterable = False
                in_fara = False
            output_lines.append(header)
            output_lines.extend(body)
            continue

        # ### subsections inside filterable areas
        if header.startswith("### ") and in_filterable:
            section_name = header[4:].strip()
            section_text = "\n".join(body)
            bold_names = re.findall(r'\*\*([^*]+)\*\*', section_text)
            label_words = {"registration #", "registered", "terminated", "location",
                           "status", "total", "client:"}
            entity_bold = [n for n in bold_names if n.lower().rstrip(":") not in
                           {lw.rstrip(":") for lw in label_words}]

            if in_fara:
                # FARA: check if any FP entity in the body is in allowed
                relevant = any(n.lower() in allowed_lower for n in entity_bold)
                if not entity_bold:
                    relevant = section_name.lower() in allowed_lower
            else:
                # LDA: check header name or bold entity names
                relevant = section_name.lower() in allowed_lower
                if not relevant:
                    relevant = any(n.lower() in allowed_lower for n in entity_bold)
            if relevant:
                output_lines.append(header)
                output_lines.extend(body)
        elif header.startswith("### "):
            output_lines.append(header)
            output_lines.extend(body)

    return "\n".join(output_lines)


# --- Display results from session state ---
if st.session_state.get("dt_has_results"):
    # Pipeline log
    if st.session_state.get("dt_stdout"):
        with st.expander("Pipeline log", expanded=False):
            st.code(st.session_state["dt_stdout"])
    if st.session_state.get("dt_stderr"):
        with st.expander("Errors/warnings", expanded=False):
            st.code(st.session_state["dt_stderr"])

    csv_data_raw = st.session_state.get("dt_csv_data", {})
    report_text_raw = st.session_state.get("dt_report", "")

    # --- Entity match selection ---
    matched_clients, matched_registrants = _extract_matched_names(csv_data_raw)
    all_matched_names = sorted(set(matched_clients) | set(matched_registrants))
    if all_matched_names:
        st.divider()
        st.subheader("Review Matched Entities")
        st.caption(
            "The search matched the names below. Deselect any you are not interested in "
            "to exclude them from the report and data tables."
        )
        rc1, rc2 = st.columns(2)
        with rc1:
            sel_clients = st.multiselect(
                "Clients (entities represented)",
                options=matched_clients,
                default=matched_clients,
                key="dt_filter_clients",
            )
        with rc2:
            sel_registrants = st.multiselect(
                "Lobbying firms (registrants)",
                options=matched_registrants,
                default=matched_registrants,
                key="dt_filter_registrants",
            )
        allowed = set(sel_clients) | set(sel_registrants)
    else:
        allowed = set()

    # Apply entity filter
    csv_data = _filter_csv_data(csv_data_raw, allowed)
    report_text = _filter_report(report_text_raw, allowed)

    # Report
    if report_text:
        st.divider()
        st.header("Summary Report")
        st.markdown(report_text)

    # Data tables
    if csv_data.get("lda_filings") or csv_data.get("lda_issues") or csv_data.get("lda_lobbyists"):
        st.divider()
        st.header("Data Tables")
        st.markdown("Expand a table to preview, filter, and download.")

        # --- Filings & Spending ---
        filings = csv_data.get("lda_filings", [])
        if filings:
            with st.expander(f"Filings & Spending ({len(filings)} records)"):
                # Filters
                all_firms = sorted(set(r.get("registrant_name", "") for r in filings))
                all_clients = sorted(set(r.get("client_name", "") for r in filings))

                fc1, fc2 = st.columns(2)
                with fc1:
                    sel_firms = st.multiselect("Filter by firm", all_firms, default=all_firms, key="fil_firms")
                with fc2:
                    sel_clients = st.multiselect("Filter by client", all_clients, default=all_clients, key="fil_clients")

                filtered = [r for r in filings
                            if r.get("registrant_name", "") in sel_firms
                            and r.get("client_name", "") in sel_clients]

                # Build display rows
                display_headers = ["Firm", "Client", "Year", "Quarter", "Type", "Amount"]
                col_map = {"Firm": "registrant_name", "Client": "client_name",
                           "Year": "filing_year", "Quarter": "filing_period",
                           "Type": "filing_type", "Amount": "amount"}
                table_rows = []
                for r in filtered:
                    row = {}
                    for h, c in col_map.items():
                        val = r.get(c, "")
                        if h == "Amount" and val:
                            try:
                                val = f"${float(val):,.0f}"
                            except (ValueError, TypeError):
                                pass
                        row[h] = val
                    table_rows.append(row)

                st.caption(f"Showing {len(table_rows)} of {len(filings)} records")
                st.dataframe(table_rows, use_container_width=True)

                st.download_button(
                    f"Download filtered ({len(table_rows)} rows)",
                    data=_rows_to_csv(table_rows, display_headers),
                    file_name="lda_filings.csv",
                    mime="text/csv",
                    key="dl_filings",
                )

        # --- Issues & Government Entities ---
        issues = csv_data.get("lda_issues", [])
        if issues:
            with st.expander(f"Issues & Government Entities ({len(issues)} records)"):
                all_firms_i = sorted(set(r.get("registrant", "") for r in issues))
                all_areas = sorted(set(r.get("issue_area", "") for r in issues))

                fc1, fc2 = st.columns(2)
                with fc1:
                    sel_firms_i = st.multiselect("Filter by firm", all_firms_i, default=all_firms_i, key="iss_firms")
                with fc2:
                    sel_areas = st.multiselect("Filter by issue area", all_areas, default=all_areas, key="iss_areas")

                filtered_i = [r for r in issues
                              if r.get("registrant", "") in sel_firms_i
                              and r.get("issue_area", "") in sel_areas]

                display_headers = ["Firm", "Client", "Issue Area", "Topics", "Government Entities"]
                col_map = {"Firm": "registrant", "Client": "client",
                           "Issue Area": "issue_area", "Topics": "description",
                           "Government Entities": "government_entities"}
                table_rows = [{h: r.get(c, "") for h, c in col_map.items()} for r in filtered_i]

                st.caption(f"Showing {len(table_rows)} of {len(issues)} records")
                st.dataframe(table_rows, use_container_width=True)

                st.download_button(
                    f"Download filtered ({len(table_rows)} rows)",
                    data=_rows_to_csv(table_rows, display_headers),
                    file_name="lda_issues.csv",
                    mime="text/csv",
                    key="dl_issues",
                )

        # --- Lobbyists ---
        lobbyists = csv_data.get("lda_lobbyists", [])
        if lobbyists:
            # Deduplicate
            seen = {}
            for lob in lobbyists:
                name = lob.get("lobbyist_name", "").strip()
                if name and name not in seen:
                    seen[name] = lob
            deduped = sorted(seen.values(), key=lambda x: x.get("lobbyist_name", ""))

            with st.expander(f"Lobbyists ({len(deduped)} unique)"):
                all_firms_l = sorted(set(r.get("registrant", "") for r in deduped))
                sel_firms_l = st.multiselect("Filter by firm", all_firms_l, default=all_firms_l, key="lob_firms")

                filtered_l = [r for r in deduped if r.get("registrant", "") in sel_firms_l]

                display_headers = ["Lobbyist", "Firm", "Client", "Former Gov. Position"]
                col_map = {"Lobbyist": "lobbyist_name", "Firm": "registrant",
                           "Client": "client", "Former Gov. Position": "covered_position"}
                table_rows = []
                for r in filtered_l:
                    row = {h: r.get(c, "") or "—" for h, c in col_map.items()}
                    table_rows.append(row)

                st.caption(f"Showing {len(table_rows)} of {len(deduped)} lobbyists")
                st.dataframe(table_rows, use_container_width=True)

                st.download_button(
                    f"Download filtered ({len(table_rows)} rows)",
                    data=_rows_to_csv(table_rows, display_headers),
                    file_name="lda_lobbyists.csv",
                    mime="text/csv",
                    key="dl_lobbyists",
                )

        # --- FARA Data Tables ---
        fara_fps = csv_data.get("fara_foreign_principals", [])
        fara_docs = csv_data.get("fara_documents", [])
        if fara_fps:
            if not csv_data.get("lda_filings"):
                st.divider()
                st.header("Data Tables")
                st.markdown("Expand a table to preview, filter, and download.")

            with st.expander(f"FARA Foreign Principals ({len(fara_fps)} records)"):
                # Deduplicate
                seen_fp = {}
                for fp in fara_fps:
                    key = (fp.get("registration_number", ""), fp.get("foreign_principal_name", ""))
                    if key not in seen_fp:
                        seen_fp[key] = fp
                unique_fps = sorted(seen_fp.values(), key=lambda x: x.get("foreign_principal_name", ""))

                display_headers = ["Foreign Principal", "Country", "Registrant", "Registered", "Terminated"]
                col_map = {"Foreign Principal": "foreign_principal_name", "Country": "state_or_country",
                           "Registrant": "registrant_name", "Registered": "foreign_principal_date",
                           "Terminated": "foreign_principal_term_date"}
                table_rows = [{h: r.get(c, "") or "—" for h, c in col_map.items()} for r in unique_fps]

                st.caption(f"Showing {len(table_rows)} records")
                st.dataframe(table_rows, use_container_width=True)
                st.download_button(
                    f"Download ({len(table_rows)} rows)",
                    data=_rows_to_csv(table_rows, display_headers),
                    file_name="fara_foreign_principals.csv",
                    mime="text/csv",
                    key="dl_fara_fps",
                )

        if fara_docs:
            with st.expander(f"FARA Documents ({len(fara_docs)} filings)"):
                display_headers = ["Date", "Type", "Registrant", "Foreign Principal", "Link"]
                table_rows = []
                for d in fara_docs:
                    url = d.get("document_url", "")
                    table_rows.append({
                        "Date": d.get("document_date", "") or "—",
                        "Type": d.get("document_type", "") or "—",
                        "Registrant": d.get("registrant_name", "") or "—",
                        "Foreign Principal": d.get("foreign_principal_name", "") or "—",
                        "Link": url or "—",
                    })

                st.caption(f"Showing {len(table_rows)} documents")
                st.dataframe(table_rows, use_container_width=True)
                st.download_button(
                    f"Download ({len(table_rows)} rows)",
                    data=_rows_to_csv(table_rows, display_headers),
                    file_name="fara_documents.csv",
                    mime="text/csv",
                    key="dl_fara_docs",
                )

        # --- Full report download ---
        if report_text:
            st.divider()
            st.download_button(
                "Download Full Report (Markdown)",
                data=report_text,
                file_name="disclosure_report.md",
                mime="text/markdown",
                key="dl_report",
            )

    has_lda = csv_data.get("lda_filings") or csv_data.get("lda_issues")
    has_fara = csv_data.get("fara_foreign_principals")
    if not report_text and not has_lda and not has_fara:
        st.warning(
            "No results found. This may happen if no disclosures match "
            "the entities and quarters selected. Check the pipeline log."
        )

elif not entities:
    st.info("Enter entity names to search for lobbying and foreign agent disclosures.")
