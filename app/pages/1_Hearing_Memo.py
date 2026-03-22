"""
Hearing Memo Generator — Streamlit Page
========================================
Upload a congressional hearing transcript, get a professional hearing memo.
"""

import streamlit as st
import sys
import os
import tempfile
import json
from pathlib import Path

# Add tool paths
TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "hearing_memo_generator"
sys.path.insert(0, str(TOOL_ROOT))

st.set_page_config(page_title="Hearing Memo Generator", page_icon="📝", layout="wide")

st.title("📝 Congressional Hearing Memo Generator")
st.caption("v1.0.0  |  Risk: 🟡 Yellow  |  DiGiacomo: #3 Briefing Creation")
st.markdown(
    "Converts congressional hearing transcripts into professional hearing memos "
    "with structured extraction, house-style composition, and automated verification."
)

st.divider()

# --- Inputs ---
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload hearing transcript",
        type=["pdf", "txt"],
        help="PDF or plain text transcript of a congressional hearing",
    )

with col2:
    memo_from = st.text_input("FROM field", placeholder="e.g., Your Organization")
    memo_date = st.text_input("Memo date", placeholder="e.g., Thursday, March 13, 2026")
    subject_override = st.text_input("Subject line override", placeholder="Auto-detected if blank")

with st.expander("Advanced options"):
    adv_col1, adv_col2 = st.columns(2)
    with adv_col1:
        hearing_title = st.text_input("Override hearing title", placeholder="Auto-detected")
        hearing_date = st.text_input("Override hearing date", placeholder="Auto-detected")
    with adv_col2:
        committee = st.text_input("Override committee name", placeholder="Auto-detected")
        hearing_time = st.text_input("Override hearing time", placeholder="Auto-detected")
    confidentiality = st.text_input(
        "Confidentiality footer",
        placeholder="Default: Confidential - Not for Public Consumption or Distribution",
    )

# --- Run pipeline ---
if uploaded_file and st.button("Generate Memo", type="primary"):
    with st.spinner("Running 4-stage pipeline..."):
        try:
            from src.normalizer import normalize
            from src.extractor import extract
            from src.composer import compose, render_memo_text
            from src.verifier import verify
            from src.exporter import export_docx

            # Save uploaded file to temp
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
            ) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            # Stage 1: Normalize
            status = st.status("Processing transcript...", expanded=True)
            status.write("**[1/4]** Normalizing source text...")
            norm_result = normalize(tmp_path)
            status.write(
                f"  Cleaned {len(norm_result.cleaned_text)} chars, "
                f"profile: {norm_result.source_profile}"
            )

            # Apply overrides
            if hearing_title:
                norm_result.metadata_candidates["hearing_title"] = hearing_title
            if hearing_date:
                norm_result.metadata_candidates["hearing_date_long"] = hearing_date
            if hearing_time:
                norm_result.metadata_candidates["hearing_time"] = hearing_time
            if committee:
                norm_result.metadata_candidates["committee_name"] = committee

            # Stage 2: Extract
            status.write("**[2/4]** Extracting structured hearing record...")
            hearing_record = extract(
                norm_result.cleaned_text,
                norm_result.metadata_candidates,
                norm_result.source_profile,
            )
            record_dict = hearing_record.to_dict()
            status.write(
                f"  {len(hearing_record.opening_statements)} openers, "
                f"{len(hearing_record.witnesses)} witnesses, "
                f"{len(hearing_record.qa_clusters)} Q&A members"
            )

            # Stage 3: Compose
            status.write("**[3/4]** Composing house-style memo...")
            memo_output = compose(
                record_dict,
                memo_from=memo_from or "",
                memo_date=memo_date or None,
                subject_line=subject_override or None,
                confidentiality_footer=confidentiality or None,
            )
            memo_text = render_memo_text(memo_output)

            # Stage 4: Verify
            status.write("**[4/4]** Running verification pass...")
            verification = verify(memo_output, record_dict)
            verdict = verification["verdict"]

            status.update(
                label=f"Pipeline complete — Verdict: {verdict.upper()}",
                state="complete",
            )

            # --- Display results ---
            st.divider()
            st.header("Generated Memo")

            # Verification summary
            if verdict == "pass":
                st.success("Verification: PASS — No flags or human checks required")
            else:
                st.warning(f"Verification: NEEDS REVIEW")
                if verification.get("flags"):
                    st.markdown("**Flags:**")
                    for flag in verification["flags"]:
                        st.markdown(f"- ⚠️ {flag}")
                if verification.get("human_checks"):
                    st.markdown("**Human checks needed:**")
                    for check in verification["human_checks"]:
                        st.markdown(f"- 👁️ {check}")

            # Memo text
            with st.expander("Memo preview (markdown)", expanded=True):
                st.markdown(memo_text)

            # Downloads
            st.subheader("Downloads")
            dl_col1, dl_col2, dl_col3 = st.columns(3)

            # DOCX export
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as docx_tmp:
                export_docx(memo_output, docx_tmp.name)
                with open(docx_tmp.name, "rb") as f:
                    dl_col1.download_button(
                        "Download .docx",
                        data=f.read(),
                        file_name="hearing_memo.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )

            # Text export
            dl_col2.download_button(
                "Download .txt",
                data=memo_text,
                file_name="hearing_memo.txt",
                mime="text/plain",
            )

            # Verification JSON
            dl_col3.download_button(
                "Download verification.json",
                data=json.dumps(verification, indent=2),
                file_name="hearing_memo_verification.json",
                mime="application/json",
            )

            # Cleanup
            os.unlink(tmp_path)

        except Exception as e:
            st.error(f"Pipeline error: {e}")
            import traceback
            st.code(traceback.format_exc())

elif not uploaded_file:
    st.info("Upload a hearing transcript (PDF or text) to get started.")
