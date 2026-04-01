"""
Stakeholder Map Builder — Streamlit Page
==========================================
Discover and classify policy actors around a given issue.
"""

import streamlit as st
import sys
import os
import json
import tempfile
from pathlib import Path

# Add tool + app paths
TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT    = TOOLKIT_ROOT / "tools" / "stakeholder_map_builder"
sys.path.insert(0, str(TOOL_ROOT / "execution"))
sys.path.insert(0, str(TOOLKIT_ROOT / "app"))

st.set_page_config(page_title="Stakeholder Map Builder", page_icon="🗺️", layout="wide")

from shared import page_header, demo_banner
page_header(
    title="Stakeholder Map Builder",
    icon="🗺️",
    version="0.1.0",
    risk="yellow",
    digiacomo="#2 Stakeholder Analysis",
    description=(
        "Discovers and classifies all relevant actors on a policy issue — "
        "pulling from LDA lobbying filings, LegiScan bill sponsorships, and news. "
        "Classifies each actor by stance, type, and influence, then renders an "
        "interactive network graph."
    ),
)


# ─── Inputs ──────────────────────────────────────────────────────────────────

policy_issue = st.text_input(
    "Policy issue",
    placeholder="e.g., artificial intelligence regulation",
    help="Use 2-4 word phrases for best results. Avoid specific bill names.",
)

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    scope = st.selectbox("Scope", ["Federal", "State"], index=0)
with col2:
    state_input = st.text_input(
        "State (2-letter code)",
        placeholder="e.g., TX",
        disabled=(scope == "Federal"),
        help="Required when Scope = State.",
    )
with col3:
    year_input = st.number_input(
        "Year filter (optional)",
        min_value=2015,
        max_value=2026,
        value=None,
        step=1,
        format="%d",
        help="Filter LDA and LegiScan results to a specific year.",
    )

include_types = st.multiselect(
    "Actor types to include",
    options=["Legislators", "Lobbyists", "Corporations", "Nonprofits"],
    default=["Legislators", "Lobbyists", "Corporations", "Nonprofits"],
    help="Uncheck types to exclude them from discovery.",
)

# ─── Generate ────────────────────────────────────────────────────────────────

demo = demo_banner()

run_disabled = demo or not policy_issue.strip()

if st.button("Build Stakeholder Map", type="primary", disabled=run_disabled):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY not set. Please configure your API key.")
    else:
        # Normalise inputs
        scope_val        = scope.lower()
        state_val        = state_input.strip().upper() if scope == "State" and state_input.strip() else "US"
        year_val         = int(year_input) if year_input else None
        include_types_lc = [t.lower() for t in include_types] if include_types else None

        with st.spinner("Discovering actors and building map… this takes 30-60 seconds."):
            try:
                from generator import build_map, render_markdown
                from export import export_xlsx, export_docx

                result = build_map(
                    policy_issue=policy_issue,
                    scope=scope_val,
                    state=state_val,
                    year=year_val,
                    include_types=include_types_lc,
                )

                st.session_state["smb_result"]   = result
                st.session_state["smb_markdown"]  = render_markdown(result)

                # Build graph
                try:
                    from graph import build_network_graph
                    fig = build_network_graph(
                        actors=result.get("actors", []),
                        relationships=result.get("relationships", []),
                        title=f"Stakeholder Map: {policy_issue}",
                    )
                    st.session_state["smb_fig"] = fig
                except ImportError as e:
                    st.session_state["smb_fig"] = None
                    st.warning(f"Network graph unavailable: {e}. Install networkx and plotly.")

                # Export files
                tmpdir    = tempfile.mkdtemp()
                xlsx_path = Path(tmpdir) / "stakeholder_map.xlsx"
                docx_path = Path(tmpdir) / "stakeholder_map.docx"

                try:
                    export_xlsx(result, str(xlsx_path))
                    st.session_state["smb_xlsx_path"] = str(xlsx_path)
                except Exception as e:
                    st.session_state["smb_xlsx_path"] = None
                    st.warning(f"Excel export failed: {e}")

                try:
                    export_docx(result, str(docx_path))
                    st.session_state["smb_docx_path"] = str(docx_path)
                except Exception as e:
                    st.session_state["smb_docx_path"] = None
                    st.warning(f"DOCX export failed: {e}")

            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Error building map: {e}")
                import traceback
                st.code(traceback.format_exc())


# ─── Display Results ─────────────────────────────────────────────────────────

if "smb_result" in st.session_state:
    result  = st.session_state["smb_result"]
    actors  = result.get("actors", [])
    rels    = result.get("relationships", [])

    proponents = [a for a in actors if a.get("stance") == "proponent"]
    opponents  = [a for a in actors if a.get("stance") == "opponent"]
    neutral    = [a for a in actors if a.get("stance") in ("neutral", "unknown")]

    # Summary metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Actors",   len(actors))
    m2.metric("Proponents",     len(proponents))
    m3.metric("Opponents",      len(opponents))
    m4.metric("Neutral/Unknown", len(neutral))
    m5.metric("Relationships",  len(rels))

    st.markdown("")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_network, tab_proponents, tab_opponents, tab_all, tab_summary = st.tabs(
        ["🕸️ Network Graph", "✅ Proponents", "❌ Opponents", "📋 All Actors", "📄 Summary"]
    )

    # Network Graph tab
    with tab_network:
        fig = st.session_state.get("smb_fig")
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
            # HTML download
            html_str = fig.to_html(include_plotlyjs="cdn")
            st.download_button(
                "⬇ Download Interactive Graph (.html)",
                data=html_str,
                file_name="stakeholder_map.html",
                mime="text/html",
            )
        else:
            st.info("Network graph unavailable. Install networkx and plotly to enable visualization.")
            if actors:
                st.caption("Actor list (graph not available):")
                for a in actors[:10]:
                    st.markdown(f"- **{a['name']}** ({a.get('stance', 'unknown').title()})")

    # Proponents tab
    with tab_proponents:
        if result.get("proponent_summary"):
            st.info(result["proponent_summary"])
        if proponents:
            import pandas as pd
            df = pd.DataFrame([{
                "Name":           a.get("name", ""),
                "Type":           a.get("stakeholder_type", "").title(),
                "Organization":   a.get("organization", ""),
                "Influence":      a.get("influence_tier", "").title(),
                "Evidence":       a.get("evidence", ""),
                "LDA Amount ($)": (
                    f"${float(a['lda_amount']):,.0f}"
                    if a.get("lda_amount") else ""
                ),
            } for a in proponents])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No proponents identified for this issue.")

    # Opponents tab
    with tab_opponents:
        if result.get("opponent_summary"):
            st.info(result["opponent_summary"])
        if opponents:
            import pandas as pd
            df = pd.DataFrame([{
                "Name":           a.get("name", ""),
                "Type":           a.get("stakeholder_type", "").title(),
                "Organization":   a.get("organization", ""),
                "Influence":      a.get("influence_tier", "").title(),
                "Evidence":       a.get("evidence", ""),
                "LDA Amount ($)": (
                    f"${float(a['lda_amount']):,.0f}"
                    if a.get("lda_amount") else ""
                ),
            } for a in opponents])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No opponents identified for this issue.")

    # All Actors tab
    with tab_all:
        import pandas as pd
        df_all = pd.DataFrame([{
            "Name":           a.get("name", ""),
            "Type":           a.get("stakeholder_type", "").title(),
            "Stance":         a.get("stance", "").title(),
            "Influence":      a.get("influence_tier", "").title(),
            "Organization":   a.get("organization", ""),
            "Evidence":       a.get("evidence", ""),
            "LDA Amount ($)": (
                f"${float(a['lda_amount']):,.0f}"
                if a.get("lda_amount") else ""
            ),
            "Source":         a.get("source", ""),
        } for a in actors])
        st.dataframe(df_all, use_container_width=True, hide_index=True)

        if rels:
            st.markdown("#### Relationships")
            id_to_name = {a["id"]: a["name"] for a in actors}
            rels_df = pd.DataFrame([{
                "From":              id_to_name.get(r["from_id"], r["from_id"]),
                "To":                id_to_name.get(r["to_id"],   r["to_id"]),
                "Relationship":      r.get("type", "").replace("_", " ").title(),
                "Label":             r.get("label", ""),
            } for r in rels])
            st.dataframe(rels_df, use_container_width=True, hide_index=True)

    # Summary tab
    with tab_summary:
        if result.get("issue_summary"):
            st.markdown("### Issue Overview")
            st.markdown(result["issue_summary"])

        coalitions = result.get("key_coalitions", [])
        if coalitions:
            st.markdown("### Key Coalitions")
            for c in coalitions:
                st.markdown(f"- {c}")

        if result.get("strategic_notes"):
            st.markdown("### Strategic Notes")
            st.markdown(result["strategic_notes"])

        st.caption(
            "Stance classifications are LLM-inferred from public data (LDA, LegiScan, news) — "
            "verify before strategic use."
        )

    # ── Downloads ─────────────────────────────────────────────────────────────
    st.divider()
    dl1, dl2, dl3 = st.columns(3)

    with dl1:
        xlsx_path = st.session_state.get("smb_xlsx_path")
        if xlsx_path and Path(xlsx_path).exists():
            st.download_button(
                "⬇ Download Excel (.xlsx)",
                data=Path(xlsx_path).read_bytes(),
                file_name="stakeholder_map.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with dl2:
        docx_path = st.session_state.get("smb_docx_path")
        if docx_path and Path(docx_path).exists():
            st.download_button(
                "⬇ Download DOCX",
                data=Path(docx_path).read_bytes(),
                file_name="stakeholder_map.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    with dl3:
        st.download_button(
            "⬇ Download JSON",
            data=json.dumps(result, indent=2, default=str),
            file_name="stakeholder_map.json",
            mime="application/json",
        )
