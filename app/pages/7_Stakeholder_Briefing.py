"""
Stakeholder Briefing — Streamlit Page
=======================================
Generate a pre-meeting one-pager for a stakeholder.
"""

import streamlit as st
import sys
import os
import json
import tempfile
from pathlib import Path

# Add tool paths
TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "stakeholder_briefing"
sys.path.insert(0, str(TOOL_ROOT / "execution"))
sys.path.insert(0, str(TOOLKIT_ROOT / "app"))

st.set_page_config(page_title="Stakeholder Briefing", page_icon="🤝", layout="wide")

from shared import page_header, demo_banner
page_header(
    title="Stakeholder Briefing",
    icon="🤝",
    version="0.1.0",
    risk="yellow",
    digiacomo="#2 Stakeholder Analysis, #3 Government Relations",
    description="Generates a pre-meeting one-pager for a stakeholder — compiling "
                "bio, policy positions, disclosure data, recent news, and suggested "
                "talking points into a concise briefing document.",
)


# ─── Inputs ──────────────────────────────────────────────────────────────────

col1, col2 = st.columns(2)
with col1:
    stakeholder_name = st.text_input(
        "Stakeholder name",
        placeholder="e.g., Sen. Maria Cantwell",
        help="Full name of the person or organization you're meeting with.",
    )
with col2:
    organization = st.text_input(
        "Organization (optional)",
        placeholder="e.g., Senate Commerce Committee",
        help="Stakeholder's organization, if not obvious from the name.",
    )

meeting_purpose = st.text_area(
    "Meeting purpose",
    placeholder="e.g., Discuss support for the AI Safety Act and potential co-sponsorship",
    height=80,
    help="Why are you meeting? This shapes the talking points and what info is emphasized.",
)

with st.expander("Additional options", expanded=False):
    your_org = st.text_input(
        "Your organization (optional)",
        placeholder="e.g., TechForward Alliance",
        help="Used to frame talking points from your perspective.",
    )

    context = st.text_area(
        "Additional context (optional)",
        placeholder="Paste any relevant material: bill text, prior correspondence, "
                    "internal notes, background research...",
        height=120,
    )

    uploaded_file = st.file_uploader(
        "Or upload a context document",
        type=["pdf", "docx", "txt"],
        help="Bill summaries, prior correspondence, background memos.",
    )

    opt_col1, opt_col2 = st.columns(2)
    with opt_col1:
        include_disclosures = st.checkbox("Search disclosure records (LDA/FARA)", value=True)
    with opt_col2:
        include_news = st.checkbox("Fetch recent news mentions", value=True)


# Build context from uploads + paste
context_parts = []
if uploaded_file:
    try:
        # Try to use context_reader from messaging matrix
        mm_exec = TOOLKIT_ROOT / "tools" / "messaging_matrix" / "execution"
        sys.path.insert(0, str(mm_exec))
        from context_reader import read_uploaded_file
        text = read_uploaded_file(uploaded_file)
        if text.strip():
            context_parts.append(f"--- {uploaded_file.name} ---\n{text}")
    except Exception as e:
        st.warning(f"Could not read {uploaded_file.name}: {e}")
if context:
    context_parts.append(context)
full_context = "\n\n".join(context_parts)


# ─── Generate ────────────────────────────────────────────────────────────────

demo = demo_banner()

if stakeholder_name and meeting_purpose and st.button(
    "Generate Briefing", type="primary", disabled=demo
):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY not set. Please configure your API key.")
    else:
        with st.spinner("Researching stakeholder and generating briefing..."):
            try:
                from generator import generate_briefing, render_markdown
                from export import export_docx

                result = generate_briefing(
                    stakeholder_name=stakeholder_name,
                    meeting_purpose=meeting_purpose,
                    organization=organization,
                    your_organization=your_org,
                    context=full_context,
                    include_disclosures=include_disclosures,
                    include_news=include_news,
                )

                st.session_state["sb_result"] = result
                st.session_state["sb_markdown"] = render_markdown(result)

                # Export DOCX
                tmpdir = tempfile.mkdtemp()
                docx_path = Path(tmpdir) / "stakeholder_briefing.docx"
                export_docx(result, str(docx_path))
                st.session_state["sb_docx_path"] = str(docx_path)

            except Exception as e:
                st.error(f"Error generating briefing: {e}")
                import traceback
                st.code(traceback.format_exc())


# ─── Display Results ─────────────────────────────────────────────────────────

if "sb_result" in st.session_state:
    result = st.session_state["sb_result"]
    header = result["header"]

    # Check which disclosure sources have data
    disclosures = result.get("disclosures", {})
    has_lda_entity = bool(disclosures.get("lda_entity"))
    has_lda_topic = bool(disclosures.get("lda_topic"))
    fara = disclosures.get("fara", {})
    has_fara = bool(fara.get("registrants") if isinstance(fara, dict) else fara)
    irs = disclosures.get("irs990", {})
    has_irs = bool(irs.get("organizations") if isinstance(irs, dict) else irs)
    has_disclosures = has_lda_entity or has_lda_topic or has_fara or has_irs

    # Tabs for each section
    tab_names = ["Profile", "Policy Positions", "Talking Points"]
    if has_disclosures:
        tab_names.append("Disclosures")
    if result.get("news"):
        tab_names.append("News")

    tabs = st.tabs(tab_names)
    tab_idx = 0

    # Profile tab
    with tabs[tab_idx]:
        profile = result.get("profile", {})
        st.markdown(f"### {header['stakeholder_name']}")
        if header.get("organization"):
            st.markdown(f"**{header['organization']}**")

        if profile.get("summary"):
            st.info(profile["summary"])
        if profile.get("current_role"):
            st.markdown(f"**Current Role:** {profile['current_role']}")
        if profile.get("key_areas"):
            st.markdown(f"**Key Policy Areas:** {', '.join(profile['key_areas'])}")
        if profile.get("notable_positions"):
            st.markdown(f"**Notable Positions:** {profile['notable_positions']}")

        # Key questions
        questions = result.get("key_questions", [])
        if questions:
            st.markdown("---")
            st.markdown("#### Key Questions to Ask")
            for q in questions:
                st.markdown(f"- **{q['question']}**")
                if q.get("purpose"):
                    st.caption(f"Purpose: {q['purpose']}")

    tab_idx += 1

    # Policy Positions tab
    with tabs[tab_idx]:
        positions = result.get("policy_positions", [])
        if positions:
            for p in positions:
                st.markdown(f"**{p['position']}**")
                if p.get("evidence"):
                    st.caption(f"Evidence: {p['evidence']}")
                if p.get("relevance"):
                    st.caption(f"Relevance: {p['relevance']}")
                st.markdown("")
        else:
            st.info("No specific policy positions identified.")

    tab_idx += 1

    # Talking Points tab
    with tabs[tab_idx]:
        talking_points = result.get("talking_points", [])
        if talking_points:
            for i, tp in enumerate(talking_points, 1):
                st.markdown(f"**{i}. {tp['point']}**")
                if tp.get("rationale"):
                    st.caption(tp["rationale"])
                st.markdown("")
        else:
            st.info("No talking points generated.")

    tab_idx += 1

    # Disclosures tab
    if "Disclosures" in tab_names:
        with tabs[tab_idx]:
            import pandas as pd

            if has_lda_entity:
                st.markdown("#### LDA Lobbying (Stakeholder Activity)")
                lda_df = pd.DataFrame(disclosures["lda_entity"][:10])
                display_cols = [c for c in ["registrant_name", "client_name", "filing_year", "amount_reported"] if c in lda_df.columns]
                if display_cols:
                    st.dataframe(lda_df[display_cols], use_container_width=True)

            if has_lda_topic:
                st.markdown("#### Lobbying Activity on Meeting Topic")
                st.caption("Organizations actively lobbying on the issue you're meeting about.")
                topic_df = pd.DataFrame(disclosures["lda_topic"][:10])
                display_cols = [c for c in ["client_name", "registrant_name", "filing_year", "filing_period", "amount_reported"] if c in topic_df.columns]
                if display_cols:
                    st.dataframe(topic_df[display_cols], use_container_width=True)

            if has_fara:
                st.markdown("#### FARA Foreign Agent Records")
                regs = fara.get("registrants", []) if isinstance(fara, dict) else []
                fps = fara.get("foreign_principals", []) if isinstance(fara, dict) else []
                if regs:
                    st.markdown("**Registrants:**")
                    st.dataframe(pd.DataFrame(regs[:10]), use_container_width=True)
                if fps:
                    st.markdown("**Foreign Principals:**")
                    st.dataframe(pd.DataFrame(fps[:10]), use_container_width=True)

            if has_irs:
                st.markdown("#### IRS 990 Nonprofit Records")
                orgs = irs.get("organizations", []) if isinstance(irs, dict) else []
                filings = irs.get("filings", []) if isinstance(irs, dict) else []
                if orgs:
                    st.dataframe(pd.DataFrame(orgs[:5]), use_container_width=True)
                if filings:
                    filing_df = pd.DataFrame(filings[:5])
                    display_cols = [c for c in ["organization_name", "tax_year", "total_revenue", "form_type"] if c in filing_df.columns]
                    if display_cols:
                        st.dataframe(filing_df[display_cols], use_container_width=True)
        tab_idx += 1

    # News tab
    if "News" in tab_names:
        with tabs[tab_idx]:
            news = result.get("news", [])
            for n in news:
                st.markdown(f"**{n['title']}**")
                st.caption(f"{n['source']} — {n.get('date', '')}")
                if n.get("url"):
                    st.markdown(f"[Read article]({n['url']})")
                st.markdown("")

    # Downloads
    st.divider()
    dl_col1, dl_col2, dl_col3 = st.columns(3)

    with dl_col1:
        st.download_button(
            "Download Markdown",
            data=st.session_state.get("sb_markdown", ""),
            file_name="stakeholder_briefing.md",
            mime="text/markdown",
        )

    with dl_col2:
        docx_path = st.session_state.get("sb_docx_path")
        if docx_path and Path(docx_path).exists():
            st.download_button(
                "Download DOCX",
                data=Path(docx_path).read_bytes(),
                file_name="stakeholder_briefing.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    with dl_col3:
        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2, default=str),
            file_name="stakeholder_briefing.json",
            mime="application/json",
        )
