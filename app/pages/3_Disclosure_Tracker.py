"""
Influence Disclosure Tracker — Streamlit Page
================================================
Query LDA and FARA disclosure records for entities.
"""

import streamlit as st
import sys
import os
import subprocess
import tempfile
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "influence_disclosure_tracker"

st.set_page_config(page_title="Disclosure Tracker", page_icon="🔍", layout="wide")

st.title("🔍 Influence Disclosure Tracker")
st.caption("v0.1.0  |  Risk: 🟡 Yellow  |  DiGiacomo: #2 Stakeholder Analysis")
st.markdown(
    "Retrieves and normalizes lobbying (LDA) and foreign principal (FARA) disclosure "
    "records, producing CSV tables and a markdown summary report."
)

st.divider()

# --- Inputs ---
entities = st.text_input(
    "Entities to search",
    placeholder="e.g., Microsoft, OpenAI",
    help="Comma-separated list of organization names",
)

col1, col2, col3 = st.columns(3)
with col1:
    from_date = st.date_input("From date")
with col2:
    to_date = st.date_input("To date")
with col3:
    sources = st.multiselect("Data sources", ["lda", "fara"], default=["lda", "fara"])

with st.expander("Advanced options"):
    adv_col1, adv_col2 = st.columns(2)
    with adv_col1:
        max_results = st.number_input("Max results", value=500, min_value=10, max_value=5000)
        fuzzy_threshold = st.slider("Fuzzy match threshold", 50, 100, 85)
    with adv_col2:
        lda_api_key = st.text_input("LDA API key (optional)", type="password")
        dry_run = st.checkbox("Dry run (skip API calls)")

# --- Run ---
if entities and st.button("Search Disclosures", type="primary"):
    with st.spinner("Querying disclosure databases..."):
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cmd = [
                    sys.executable,
                    str(TOOL_ROOT / "execution" / "run.py"),
                    "--entities", entities,
                    "--from", str(from_date),
                    "--to", str(to_date),
                    "--sources", ",".join(sources),
                    "--out", tmpdir,
                    "--max-results", str(max_results),
                    "--fuzzy-threshold", str(fuzzy_threshold),
                ]
                if dry_run:
                    cmd.append("--dry-run")

                env = os.environ.copy()
                if lda_api_key:
                    env["LDA_API_KEY"] = lda_api_key

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env=env,
                    cwd=str(TOOL_ROOT / "execution"),
                )

                # Show log
                if result.stdout:
                    with st.expander("Pipeline log", expanded=False):
                        st.code(result.stdout)
                if result.stderr:
                    with st.expander("Errors/warnings", expanded=False):
                        st.code(result.stderr)

                # Find outputs
                output_path = Path(tmpdir)

                # Report
                report_files = list(output_path.rglob("report.md"))
                if report_files:
                    st.divider()
                    st.header("Summary Report")
                    report_text = report_files[0].read_text()
                    st.markdown(report_text)

                # CSV downloads
                csv_files = list(output_path.rglob("*.csv"))
                if csv_files:
                    st.divider()
                    st.header("Data Downloads")
                    for csv_file in sorted(csv_files):
                        col_dl, col_preview = st.columns([1, 3])
                        with col_dl:
                            with open(csv_file, "rb") as f:
                                st.download_button(
                                    f"Download {csv_file.name}",
                                    data=f.read(),
                                    file_name=csv_file.name,
                                    mime="text/csv",
                                )
                        with col_preview:
                            try:
                                import csv as csv_mod
                                import io

                                csv_text = csv_file.read_text()
                                reader = csv_mod.reader(io.StringIO(csv_text))
                                rows = list(reader)
                                if len(rows) > 1:
                                    st.caption(f"{csv_file.name} — {len(rows)-1} rows")
                                    # Show header + first 5 rows as table
                                    header = rows[0]
                                    data_rows = rows[1:6]
                                    st.table(
                                        [{h: r[i] if i < len(r) else "" for i, h in enumerate(header)} for r in data_rows]
                                    )
                                else:
                                    st.caption(f"{csv_file.name} — empty")
                            except Exception:
                                st.caption(f"{csv_file.name}")

                if not report_files and not csv_files:
                    st.warning(
                        "No results found. This may happen if no disclosures match "
                        "the entities and date range. Check the pipeline log."
                    )

        except subprocess.TimeoutExpired:
            st.error("Search timed out after 5 minutes. Try fewer entities or a narrower date range.")
        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())

elif not entities:
    st.info("Enter entity names to search for lobbying and foreign agent disclosures.")
