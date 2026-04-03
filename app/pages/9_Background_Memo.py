"""
Background Memo Generator — Streamlit Page
============================================
Generate a structured background memo on any client, organization,
policy issue, or individual.
"""

import streamlit as st
import sys
import os
import json
import tempfile
from datetime import date
from pathlib import Path

# Add tool paths
TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "background_memo_generator"
sys.path.insert(0, str(TOOLKIT_ROOT / "app"))

st.set_page_config(page_title="Background Memo Generator", page_icon="📄", layout="wide")

from shared import page_header, demo_banner
page_header(
    title="Background Memo Generator",
    icon="📄",
    version="0.1.0",
    risk="yellow",
    digiacomo="#2 Stakeholder Analysis, #3 Government Relations",
    description="Generates a structured background memo on any client, organization, "
                "policy issue, or individual. Provide a subject name and the section "
                "headings you need — the tool fills all content and exports a formatted DOCX.",
)


# ─── Inputs ──────────────────────────────────────────────────────────────────

col1, col2 = st.columns([1, 1])

with col1:
    subject = st.text_input(
        "Subject",
        placeholder="e.g., Jagello 2000, Giordano Riello Group, AI Safety Act",
        help="Name of the client, organization, policy issue, or person.",
    )

with col2:
    memo_date = st.text_input(
        "Memo date",
        value=date.today().strftime("%B %d, %Y"),
        help="Date that will appear on the memo.",
    )

st.markdown("**Sections** — enter one section heading per line")
sections_input = st.text_area(
    "Sections",
    placeholder=(
        "Corporate Overview\n"
        "Key Leadership\n"
        "U.S. Presence\n"
        "Policy Positions\n"
        "Relevant Links"
    ),
    height=160,
    label_visibility="collapsed",
    help="Each line becomes a section heading. The tool also adds Overview and Fast Facts automatically.",
)

context = st.text_area(
    "Additional context (optional)",
    placeholder="Key angles, background notes, or specific aspects to emphasize...",
    height=80,
    help="Anything that helps the LLM understand what matters for this memo.",
)

# ─── Generate ────────────────────────────────────────────────────────────────

demo = demo_banner()

sections = [s.strip() for s in sections_input.strip().splitlines() if s.strip()]

if subject and sections and st.button("Generate Memo", type="primary", disabled=demo):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY not set.")
    else:
        with st.spinner("Generating background memo..."):
            try:
                import importlib.util as _ilu

                _gen_spec = _ilu.spec_from_file_location(
                    "bmg_generator", TOOL_ROOT / "execution" / "generator.py"
                )
                _gen = _ilu.module_from_spec(_gen_spec)
                _gen_spec.loader.exec_module(_gen)

                _exp_spec = _ilu.spec_from_file_location(
                    "bmg_export", TOOL_ROOT / "execution" / "export.py"
                )
                _exp = _ilu.module_from_spec(_exp_spec)
                _exp_spec.loader.exec_module(_exp)

                result = _gen.generate_memo(
                    subject=subject,
                    sections=sections,
                    context=context,
                )

                # Export DOCX
                tmpdir = tempfile.mkdtemp()
                docx_path = Path(tmpdir) / "background_memo.docx"
                _exp.export_docx(result, str(docx_path), memo_date=memo_date)

                # Render markdown
                md_text = _gen.render_markdown(result, memo_date=memo_date)

                st.session_state["bmg_result"] = result
                st.session_state["bmg_markdown"] = md_text
                st.session_state["bmg_docx_path"] = str(docx_path)
                st.session_state["bmg_subject"] = subject

            except Exception as e:
                st.error(f"Error generating memo: {e}")
                import traceback
                st.code(traceback.format_exc())


# ─── Display Results ─────────────────────────────────────────────────────────

if "bmg_result" in st.session_state:
    result = st.session_state["bmg_result"]
    subject_disp = st.session_state.get("bmg_subject", result["subject"])

    st.warning(
        "**Review required.** All facts are LLM-generated — verify against primary sources "
        "before distribution. Links should be checked individually.",
        icon="⚠️",
    )

    st.markdown("---")

    # Overview
    st.markdown("### Overview")
    st.markdown(result["overview"])

    # Fast Facts
    st.markdown("### Fast Facts")
    for fact in result["fast_facts"]:
        st.markdown(f"- **{fact}**")

    # Sections
    for section in result["sections"]:
        st.markdown(f"### {section['heading']}")
        for sub in section.get("subsections", []):
            if sub.get("heading"):
                st.markdown(f"**{sub['heading']}**")
            for para in sub.get("paragraphs", []):
                st.markdown(para)

    # Links
    st.markdown("### Relevant Links")
    for link in result["links"]:
        url = link.get("url", "")
        label = link.get("label", url)
        if url:
            st.markdown(f"- [{label}]({url})")

    # Downloads
    st.divider()
    dl1, dl2, dl3 = st.columns(3)

    with dl1:
        docx_path = st.session_state.get("bmg_docx_path")
        if docx_path and Path(docx_path).exists():
            safe = subject_disp.lower().replace(" ", "_")[:30]
            st.download_button(
                "Download DOCX",
                data=Path(docx_path).read_bytes(),
                file_name=f"{safe}_background_memo.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    with dl2:
        st.download_button(
            "Download Markdown",
            data=st.session_state.get("bmg_markdown", ""),
            file_name="background_memo.md",
            mime="text/markdown",
        )

    with dl3:
        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2, default=str),
            file_name="background_memo.json",
            mime="application/json",
        )
