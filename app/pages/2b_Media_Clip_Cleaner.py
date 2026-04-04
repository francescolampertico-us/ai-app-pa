"""
Media Clip Cleaner — Streamlit Page
=====================================
Clean pasted article text for clips reports: removes headlines, metadata, ads,
and clutter; keeps clean body text ready for a clips report.
"""

import os
import sys
from pathlib import Path

import streamlit as st

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
CLEANER_ROOT = TOOLKIT_ROOT / "tools" / "media_clip_cleaner"
sys.path.insert(0, str(CLEANER_ROOT / "execution"))
sys.path.insert(0, str(TOOLKIT_ROOT / "app"))

st.set_page_config(page_title="Clip Cleaner", page_icon="✂️", layout="wide")

from shared import page_header, demo_banner

page_header(
    title="Media Clip Cleaner",
    icon="✂️",
    version="0.3.0",
    risk="green",
    digiacomo="#1 Monitoring & Analysis",
    description="Cleans copy-pasted article text for clips reports. Removes headlines, "
                "bylines, ads, navigation clutter, and metadata. Keeps clean body text.",
)

demo_banner()

raw_paste = st.text_area(
    "Paste raw article text",
    placeholder="Copy the full article text from the webpage and paste it here...",
    height=250,
)

col1, col2 = st.columns(2)
with col1:
    mode = st.radio(
        "Cleaning mode",
        ["LLM (recommended)", "Local (rule-based)"],
        index=0,
        horizontal=True,
    )
with col2:
    article_title = st.text_input(
        "Article headline (optional — helps remove title from output)",
        placeholder="e.g., Senate Passes Energy Bill",
    )

if raw_paste and st.button("Clean Article", type="primary"):
    try:
        import importlib.util

        _spec = importlib.util.spec_from_file_location(
            "clean_clip",
            str(CLEANER_ROOT / "execution" / "clean_clip.py"),
        )
        _cc = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_cc)

        if mode.startswith("LLM"):
            with st.spinner("Cleaning with LLM..."):
                try:
                    if not os.environ.get("OPENAI_API_KEY"):
                        st.error("OPENAI_API_KEY not set. Using local cleaner.")
                        raise RuntimeError("No API key")
                    cleaned = _cc.clean_clip_llm_openai(
                        raw_paste, "gpt-4o-mini", title=article_title or None
                    )
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

        st.text_area("Cleaned output", value=cleaned, height=350)
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

elif not raw_paste:
    st.info(
        "Paste article text above and click **Clean Article**. "
        "Use this tool to fix paywalled clips before adding them to a report."
    )
