"""
Background Memo — Streamlit Page
============================================
Generate a structured background memo on any client, organization,
policy issue, or individual. Automatically searches LDA/FARA disclosure
records for all available years and adds a dedicated section to the memo.
"""

import streamlit as st
import sys
import os
import json
import subprocess
import tempfile
from datetime import date
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "background_memo"
DISCLOSURE_TOOL_ROOT = TOOLKIT_ROOT / "tools" / "influence_disclosure_tracker"
sys.path.insert(0, str(TOOLKIT_ROOT / "app"))

st.set_page_config(page_title="Background Memo", page_icon="📄", layout="wide")

from shared import page_header, demo_banner
page_header(
    title="Background Memo",
    icon="📄",
    version="0.2.0",
    risk="yellow",
    digiacomo="#2 Stakeholder Analysis, #3 Government Relations",
    description="Generates a structured background memo on any client, organization, "
                "policy issue, or individual. Automatically searches LDA/FARA disclosure "
                "records (all years) and adds a lobbying/advisory section in memo style.",
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
        "Policy Positions"
    ),
    height=160,
    label_visibility="collapsed",
    help="Each line becomes a section heading. Overview, Fast Facts, and (if found) a "
         "Lobbying & Disclosure section are added automatically.",
)

context = st.text_area(
    "Additional context (optional)",
    placeholder="Key angles, background notes, specific aspects to emphasize, or facts to anchor the memo...",
    height=80,
    help="Anything that helps the LLM understand what matters for this memo.",
)

st.markdown("**Source files (optional)** — upload PDFs, DOCX, or text files to ground the memo")
uploaded_files = st.file_uploader(
    "Source files",
    type=["pdf", "docx", "txt", "md"],
    accept_multiple_files=True,
    label_visibility="collapsed",
    help="Annual reports, website exports, policy documents, press releases — any file with relevant facts.",
)

with st.expander("Disclosure search options"):
    st.caption(
        "LDA/FARA records are searched automatically for all available years. "
        "Adjust the entity name below if it differs from the subject name as it appears in filings."
    )
    dc1, dc2 = st.columns(2)
    with dc1:
        disclosure_entity_override = st.text_input(
            "Entity name in filings (optional override)",
            value="",
            placeholder="Leave blank to use subject name",
            help="Use this if the filing name differs — e.g., 'Institut Macaya' vs 'Institute Macaya'.",
        )
    with dc2:
        disclosure_sources = st.multiselect(
            "Sources",
            options=["lda", "fara", "irs990"],
            default=["lda", "fara"],
        )


# ─── Generate ────────────────────────────────────────────────────────────────

demo = demo_banner()

sections = [s.strip() for s in sections_input.strip().splitlines() if s.strip()]


def _extract_file_text(uploaded_file) -> str:
    """Extract plain text from an uploaded PDF, DOCX, or text file."""
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()

    if name.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(__import__("io").BytesIO(raw))
            return "\n\n".join(
                page.extract_text() or "" for page in reader.pages
            ).strip()
        except Exception as e:
            return f"[Could not extract PDF: {e}]"

    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(__import__("io").BytesIO(raw))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            return f"[Could not extract DOCX: {e}]"

    # txt / md
    try:
        return raw.decode("utf-8", errors="replace").strip()
    except Exception as e:
        return f"[Could not decode file: {e}]"


def _run_disclosure_search(entity: str, sources: list) -> str:
    """Run the disclosure tracker for all years and return the markdown report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            sys.executable,
            str(DISCLOSURE_TOOL_ROOT / "execution" / "run.py"),
            "--entities", entity,
            "--search-field", "both",
            "--filing-periods", "Q1,Q2,Q3,Q4",
            "--sources", ",".join(sources),
            "--out", tmpdir,
            "--max-results", "500",
            "--format", "md",
        ]
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(DISCLOSURE_TOOL_ROOT / "execution"),
        )
        # Tracker creates {tmpdir}/{entity_name}/report.md
        matches = list(Path(tmpdir).rglob("report.md"))
        if matches:
            return matches[0].read_text(encoding="utf-8")
    return ""


if subject and sections and st.button("Generate Memo", type="primary", disabled=demo):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY not set.")
    else:
        import importlib.util as _ilu

        _res_spec = _ilu.spec_from_file_location(
            "bmg_research", TOOL_ROOT / "execution" / "research.py"
        )
        _res = _ilu.module_from_spec(_res_spec)
        _res_spec.loader.exec_module(_res)

        disclosure_md = ""
        research_md = ""
        entity_for_search = disclosure_entity_override.strip() or subject

        # Step 0: Extract uploaded files
        file_context = ""
        if uploaded_files:
            parts = []
            for f in uploaded_files:
                text = _extract_file_text(f)
                if text and not text.startswith("[Could not"):
                    parts.append(f"=== {f.name} ===\n{text[:6000]}")
            if parts:
                file_context = (
                    "UPLOADED SOURCE DOCUMENTS — treat these as primary research material. "
                    "Use specific facts, figures, names, and dates from these files in the memo:\n\n"
                    + "\n\n".join(parts)
                )
                st.success(f"{len(parts)} file(s) extracted and will be used as source material.")

        # Step 1a: Web research
        with st.spinner(f"Searching recent articles about '{subject}'..."):
            try:
                research_md = _res.research_subject(subject, context)
                if research_md:
                    n = research_md.count("--- Article")
                    st.success(f"Web research: {n} article(s) extracted.")
                else:
                    st.info("No web articles found. Memo will rely on LLM knowledge + context provided.")
            except Exception as e:
                st.warning(f"Web research failed ({e}). Proceeding without article data.")

        # Step 1b: Disclosure search
        with st.spinner(f"Searching LDA/FARA records for '{entity_for_search}' (all years)..."):
            try:
                disclosure_md = _run_disclosure_search(entity_for_search, disclosure_sources)
                if disclosure_md:
                    line_count = len(disclosure_md.splitlines())
                    st.success(f"Disclosure data: {line_count} lines of LDA/FARA filing data found.")
                else:
                    st.info("No disclosure records found. No lobbying section will be added.")
            except subprocess.TimeoutExpired:
                st.warning("Disclosure search timed out. Proceeding without disclosure section.")
            except Exception as e:
                st.warning(f"Disclosure search failed ({e}). Proceeding without disclosure section.")

        # Step 2: Generate memo
        with st.spinner("Generating background memo..."):
            try:
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

                combined_research = "\n\n".join(
                    x for x in [file_context, research_md] if x
                )
                result = _gen.generate_memo(
                    subject=subject,
                    sections=sections,
                    context=context,
                    disclosure_context=disclosure_md,
                    research_context=combined_research,
                )

                tmpdir_docx = tempfile.mkdtemp()
                docx_path = Path(tmpdir_docx) / "background_memo.docx"
                _exp.export_docx(result, str(docx_path), memo_date=memo_date)

                md_text = _gen.render_markdown(result, memo_date=memo_date)

                st.session_state["bmg_result"] = result
                st.session_state["bmg_markdown"] = md_text
                st.session_state["bmg_docx_path"] = str(docx_path)
                st.session_state["bmg_subject"] = subject
                st.session_state["bmg_disclosure_md"] = disclosure_md
                st.session_state["bmg_research_md"] = research_md

            except Exception as e:
                st.error(f"Error generating memo: {e}")
                import traceback
                st.code(traceback.format_exc())


# ─── Display Results ─────────────────────────────────────────────────────────

if "bmg_result" in st.session_state:
    result = st.session_state["bmg_result"]
    subject_disp = st.session_state.get("bmg_subject", result["subject"])
    disclosure_md = st.session_state.get("bmg_disclosure_md", "")

    st.warning(
        "**Review required.** All facts are LLM-generated — verify against primary sources "
        "before distribution. Disclosure figures sourced from official LDA/FARA databases.",
        icon="⚠️",
    )

    st.markdown("---")

    st.markdown("### Overview")
    st.markdown(result["overview"])

    st.markdown("### Fast Facts")
    for fact in result["fast_facts"]:
        st.markdown(f"- **{fact}**")

    for section in result["sections"]:
        st.markdown(f"### {section['heading']}")
        for sub in section.get("subsections", []):
            if sub.get("heading"):
                st.markdown(f"**{sub['heading']}**")
            for para in sub.get("paragraphs", []):
                st.markdown(para)

    st.markdown("### Links")
    for link in result["links"]:
        url = link.get("url", "")
        label = link.get("label", url)
        if url:
            st.markdown(f"- [{label}]({url})")

    research_md = st.session_state.get("bmg_research_md", "")
    if research_md:
        with st.expander("View articles used for research"):
            st.text(research_md[:6000])

    if disclosure_md:
        with st.expander("View raw disclosure data used"):
            st.markdown(disclosure_md[:8000])

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
