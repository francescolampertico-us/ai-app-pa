"""
Media Clips — Streamlit Page
==============================
Search Google News with Boolean queries, generate filtered clips report.
"""

import streamlit as st
import sys
import os
import tempfile
import datetime
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "media_clips"
sys.path.insert(0, str(TOOL_ROOT / "execution"))

st.set_page_config(page_title="Media Clips", page_icon="📰", layout="wide")

st.title("📰 Media Clips Generator")
st.caption("v0.1.0  |  Risk: 🟡 Yellow  |  DiGiacomo: #1 Legislative Monitoring")
st.markdown(
    "Daily media monitoring tool. Searches Google News with Boolean queries, "
    "filters to trusted sources, deduplicates, and generates a formatted .docx report."
)

st.divider()

# --- Inputs ---
topic = st.text_input("Report topic / title", placeholder="e.g., India Media Clips")
queries = st.text_area(
    "Search queries (one per line, Boolean syntax supported)",
    placeholder='"India" AND ("elections" OR "Modi")\n"New Delhi" AND "trade"',
    height=100,
)

col1, col2, col3 = st.columns(3)
with col1:
    period = st.selectbox("Search period", ["24h", "12h", "72h", "7d"], index=0)
with col2:
    target_date = st.date_input("Target date", value=datetime.date.today())
with col3:
    since_date = st.text_input("Filter since (optional)", placeholder="YYYY-MM-DD HH:MM")

with st.expander("Email options (macOS only)"):
    email_sender = st.text_input("Sender email", placeholder="you@domain.com")
    email_recipient = st.text_input("Recipient email", placeholder="team@domain.com")

# --- Run ---
if topic and queries and st.button("Generate Clips Report", type="primary"):
    with st.spinner("Searching and generating clips..."):
        try:
            # We need to call generate_clips.py's main logic
            # Import the key functions from generate_clips
            import generate_clips as gc

            query_list = [q.strip() for q in queries.strip().split("\n") if q.strip()]

            with tempfile.TemporaryDirectory() as tmpdir:
                # Build argparse-style args
                class Args:
                    pass

                args = Args()
                args.topic = topic
                args.queries = ",".join(query_list)
                args.period = period
                args.suffix = ""
                args.since = since_date or None
                args.target_date = str(target_date)
                args.output_dir = tmpdir
                args.email_sender = email_sender or None
                args.email_recipient = email_recipient or None

                # Call as subprocess since the script has tightly coupled argparse
                import subprocess

                cmd = [
                    sys.executable,
                    str(TOOL_ROOT / "execution" / "generate_clips.py"),
                    "--topic", topic,
                    "--queries", ",".join(query_list),
                    "--period", period,
                    "--target-date", str(target_date),
                    "--output-dir", tmpdir,
                ]
                if since_date:
                    cmd.extend(["--since", since_date])

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=str(TOOL_ROOT / "execution"),
                )

                # Show output log
                if result.stdout:
                    with st.expander("Pipeline log", expanded=False):
                        st.code(result.stdout)
                if result.stderr:
                    with st.expander("Errors/warnings", expanded=False):
                        st.code(result.stderr)

                # Find generated .docx
                docx_files = list(Path(tmpdir).rglob("*.docx"))
                if docx_files:
                    docx_path = docx_files[0]
                    st.success(f"Report generated: {docx_path.name}")

                    with open(docx_path, "rb") as f:
                        st.download_button(
                            "Download .docx report",
                            data=f.read(),
                            file_name=docx_path.name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                else:
                    st.warning(
                        "No .docx was generated. Check the pipeline log for details. "
                        "This may happen if no articles matched your queries."
                    )

        except subprocess.TimeoutExpired:
            st.error("Search timed out after 2 minutes. Try narrower queries or a shorter period.")
        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())

elif not topic or not queries:
    st.info("Enter a topic and search queries to generate a media clips report.")
