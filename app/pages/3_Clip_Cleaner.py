"""
Clip Cleaner — Streamlit Page
===============================
Paste raw article text, get cleaned markdown output.
"""

import streamlit as st
import sys
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "media_clip_cleaner"
sys.path.insert(0, str(TOOL_ROOT / "execution"))

st.set_page_config(page_title="Clip Cleaner", page_icon="✂️", layout="wide")

st.title("✂️ Media Clip Cleaner")
st.caption("v0.3.0  |  Risk: 🟢 Green  |  DiGiacomo: #1 Legislative Monitoring")
st.markdown(
    "Cleans pasted news article text — removes ads, metadata, navigation clutter — "
    "and produces clean markdown with italicized subtitle and body paragraphs."
)

st.divider()

# --- Input ---
raw_text = st.text_area(
    "Paste raw article text",
    height=300,
    placeholder="Paste the full article text here, including any clutter from the website...",
)

col1, col2 = st.columns(2)
with col1:
    mode = st.radio("Cleaning mode", ["Local (rule-based)", "LLM (OpenAI)"], horizontal=True)
with col2:
    if mode == "LLM (OpenAI)":
        llm_model = st.text_input("Model", value="gpt-4o-mini")
        fallback = st.checkbox("Fallback to local on LLM failure", value=True)

# --- Run ---
if raw_text and st.button("Clean Article", type="primary"):
    with st.spinner("Cleaning..."):
        try:
            from clean_clip import clean_clip, validate_output

            if mode == "Local (rule-based)":
                cleaned = clean_clip(raw_text)
            else:
                try:
                    from clean_clip import clean_clip_llm_openai
                    cleaned = clean_clip_llm_openai(raw_text, llm_model)
                except Exception as llm_err:
                    if fallback:
                        st.warning(f"LLM failed ({llm_err}), falling back to local mode")
                        cleaned = clean_clip(raw_text)
                    else:
                        raise llm_err

            # Validate
            is_valid, issues = validate_output(cleaned)

            if is_valid:
                st.success("Output validated successfully")
            else:
                st.warning("Validation issues detected:")
                for issue in issues:
                    st.markdown(f"- {issue}")

            # Display result
            st.divider()

            result_col1, result_col2 = st.columns(2)
            with result_col1:
                st.subheader("Cleaned output (raw)")
                st.code(cleaned, language="markdown")
            with result_col2:
                st.subheader("Rendered preview")
                st.markdown(cleaned)

            # Download
            st.download_button(
                "Download cleaned text",
                data=cleaned,
                file_name="cleaned_clip.md",
                mime="text/markdown",
            )

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())

elif not raw_text:
    st.info("Paste article text above to clean it.")
