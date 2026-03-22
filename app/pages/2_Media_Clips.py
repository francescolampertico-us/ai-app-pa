"""
Media Clips — Streamlit Page
==============================
Search Google News with Boolean queries, generate filtered clips report.
Includes embedded Clip Cleaner utility for paywalled articles.
"""

import streamlit as st
import sys
import os
import tempfile
import datetime
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "media_clips"
CLEANER_ROOT = TOOLKIT_ROOT / "tools" / "media_clip_cleaner"
sys.path.insert(0, str(TOOL_ROOT / "execution"))
sys.path.insert(0, str(CLEANER_ROOT / "execution"))

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
    source_filter = st.selectbox(
        "Source filter",
        ["Mainstream media only", "All sources", "Custom"],
        index=0,
    )

# Custom sources input
custom_sources = None
if source_filter == "Custom":
    custom_sources = st.text_area(
        "Custom trusted domains (one per line)",
        placeholder="nytimes.com\npolitico.com\nyourcustomsource.com",
        height=80,
    )

since_date = st.text_input("Filter since (optional)", placeholder="YYYY-MM-DD HH:MM")

with st.expander("Email options (optional — macOS Mail.app)"):
    email_sender = st.text_input("Sender email", placeholder="you@domain.com")
    email_recipient = st.text_input("Recipient email", placeholder="team@domain.com")

# --- Run ---
if topic and queries and st.button("Generate Clips Report", type="primary"):
    with st.spinner("Searching and generating clips..."):
        try:
            import subprocess

            with tempfile.TemporaryDirectory() as tmpdir:
                cmd = [
                    sys.executable,
                    str(TOOL_ROOT / "execution" / "generate_clips.py"),
                    "--topic", topic,
                    "--queries", ",".join(q.strip() for q in queries.strip().split("\n") if q.strip()),
                    "--period", period,
                    "--target-date", str(target_date),
                    "--output-dir", tmpdir,
                ]
                if since_date:
                    cmd.extend(["--since", since_date])

                # Source filter: pass --all-sources or --custom-sources
                if source_filter == "All sources":
                    cmd.append("--all-sources")
                elif source_filter == "Custom" and custom_sources:
                    domains = ",".join(d.strip() for d in custom_sources.strip().split("\n") if d.strip())
                    cmd.extend(["--custom-sources", domains])

                # Email args (only if both provided)
                if email_sender and email_recipient:
                    cmd.extend(["--email-sender", email_sender])
                    cmd.extend(["--email-recipient", email_recipient])
                elif not email_sender and not email_recipient:
                    cmd.append("--no-email")

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

# --- Clip Cleaner Utility ---
st.divider()
st.subheader("🧹 Clip Cleaner")
st.markdown(
    "For paywalled or problematic articles: paste the raw article text below "
    "to clean it into clip-ready format."
)

raw_paste = st.text_area(
    "Paste raw article text",
    placeholder="Copy the full article text from the webpage and paste it here...",
    height=200,
    key="clip_cleaner_input",
)

cleaner_mode = st.radio(
    "Cleaning mode",
    ["LLM (recommended)", "Local (rule-based)"],
    index=0,
    horizontal=True,
    key="cleaner_mode",
)

if raw_paste and st.button("Clean Article", key="clean_btn"):
    try:
        # Load directly from file to avoid caching issues
        import importlib.util
        _spec = importlib.util.spec_from_file_location(
            "clean_clip",
            str(CLEANER_ROOT / "execution" / "clean_clip.py"),
        )
        _cc = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_cc)

        if cleaner_mode.startswith("LLM"):
            with st.spinner("Cleaning with LLM..."):
                try:
                    # Ensure API key is available
                    if not os.environ.get("OPENAI_API_KEY"):
                        st.error("OPENAI_API_KEY not set. Using local cleaner.")
                        raise RuntimeError("No API key")
                    cleaned = _cc.clean_clip_llm_openai(raw_paste, "gpt-4o-mini")
                    st.success("Cleaned with LLM.")
                except Exception as llm_err:
                    st.warning(f"LLM failed ({llm_err}), falling back to local cleaner.")
                    cleaned = _cc.clean_clip(raw_paste)
        else:
            cleaned = _cc.clean_clip(raw_paste)

        ok, issues = _cc.validate_output(cleaned)

        if not ok:
            st.warning("Cleaned text has minor issues:")
            for issue in issues:
                st.markdown(f"- {issue}")

        st.text_area("Cleaned output", value=cleaned, height=300, key="clip_cleaner_output")

        st.download_button(
            "Download cleaned text",
            data=cleaned,
            file_name="cleaned_clip.txt",
            mime="text/plain",
        )
    except Exception as e:
        st.error(f"Cleaning error: {e}")
        import traceback
        st.code(traceback.format_exc())
