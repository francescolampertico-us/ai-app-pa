"""
Media List Builder — Streamlit Page
=====================================
Generate a targeted media pitch list for a policy issue.
"""

import streamlit as st
import sys
import os
import json
import tempfile
from pathlib import Path

# Add tool paths
TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "media_list_builder"
sys.path.insert(0, str(TOOL_ROOT / "execution"))
sys.path.insert(0, str(TOOLKIT_ROOT / "app"))

st.set_page_config(page_title="Media List Builder", page_icon="📋", layout="wide")

from shared import page_header, demo_banner
page_header(
    title="Media List Builder",
    icon="📋",
    version="0.1.0",
    risk="yellow",
    digiacomo="#5 Media Relations",
    description="Generates a targeted media pitch list based on a policy issue, "
                "geographic scope, and media type filter. Outputs a downloadable "
                "Excel table with journalist contacts, pitch angles, and previous coverage.",
)


# ─── Inputs ──────────────────────────────────────────────────────────────────

issue = st.text_area(
    "Policy issue to pitch",
    placeholder="e.g., AI safety regulation and mandatory pre-deployment testing requirements",
    height=80,
    help="What's the issue or topic you want to pitch to media?",
)

col1, col2, col3 = st.columns(3)

with col1:
    location_type = st.selectbox(
        "Geographic scope",
        ["National (US)", "State", "City / Metro"],
    )

with col2:
    location = "US"
    if location_type == "State":
        location = st.text_input(
            "State",
            placeholder="e.g., California",
        )
    elif location_type == "City / Metro":
        location = st.text_input(
            "City or metro area",
            placeholder="e.g., Washington DC",
        )

with col3:
    num_contacts = st.slider(
        "Number of contacts",
        min_value=5, max_value=40, value=20, step=5,
        help="Target number of media contacts to generate.",
    )

st.markdown("**Media types to include:**")
mt_col1, mt_col2, mt_col3 = st.columns(3)
with mt_col1:
    mt_mainstream = st.checkbox("Mainstream", value=True)
    mt_print = st.checkbox("Print", value=True)
with mt_col2:
    mt_broadcast = st.checkbox("Broadcast (TV/Radio)", value=True)
    mt_digital = st.checkbox("Digital / Online", value=True)
with mt_col3:
    mt_trade = st.checkbox("Trade / Policy", value=True)
    mt_podcast = st.checkbox("Podcast", value=False)

selected_types = []
if mt_mainstream: selected_types.append("mainstream")
if mt_print: selected_types.append("print")
if mt_broadcast: selected_types.append("broadcast")
if mt_digital: selected_types.append("digital")
if mt_trade: selected_types.append("trade")
if mt_podcast: selected_types.append("podcast")


# ─── Generate ────────────────────────────────────────────────────────────────

demo = demo_banner()

if issue and selected_types and st.button("Build Media List", type="primary", disabled=demo):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY not set. Please configure your API key.")
    else:
        with st.spinner("Researching journalists and building pitch list..."):
            try:
                import importlib.util as _ilu
                _gen_spec = _ilu.spec_from_file_location("mlb_generator", TOOL_ROOT / "execution" / "generator.py")
                _gen = _ilu.module_from_spec(_gen_spec); _gen_spec.loader.exec_module(_gen)
                generate_media_list = _gen.generate_media_list
                render_markdown = _gen.render_markdown
                MEDIA_TYPE_LABELS = _gen.MEDIA_TYPE_LABELS

                _exp_spec = _ilu.spec_from_file_location("mlb_export", TOOL_ROOT / "execution" / "export.py")
                _exp = _ilu.module_from_spec(_exp_spec); _exp_spec.loader.exec_module(_exp)
                export_xlsx = _exp.export_xlsx

                result = generate_media_list(
                    issue=issue,
                    location=location,
                    media_types=selected_types,
                    num_contacts=num_contacts,
                )

                st.session_state["ml_result"] = result
                st.session_state["ml_markdown"] = render_markdown(result)
                st.session_state["ml_MEDIA_TYPE_LABELS"] = MEDIA_TYPE_LABELS

                # Export Excel
                tmpdir = tempfile.mkdtemp()
                xlsx_path = Path(tmpdir) / "media_list.xlsx"
                export_xlsx(result, str(xlsx_path))
                st.session_state["ml_xlsx_path"] = str(xlsx_path)

            except Exception as e:
                st.error(f"Error building media list: {e}")
                import traceback
                st.code(traceback.format_exc())


# ─── Display Results ─────────────────────────────────────────────────────────

if "ml_result" in st.session_state:
    result = st.session_state["ml_result"]
    contacts = result.get("contacts", [])

    st.warning(
        "**Review required.** This list was generated by an AI. Journalist names, roles, "
        "and story links may be inaccurate or outdated. Verify all contacts before pitching. "
        "Contacts marked [VERIFY] in Notes need extra scrutiny.",
        icon="⚠️",
    )

    # Summary metrics
    type_counts = {}
    for c in contacts:
        mt = c.get("media_type", "other")
        type_counts[mt] = type_counts.get(mt, 0) + 1

    metric_cols = st.columns(min(len(type_counts) + 1, 6))
    with metric_cols[0]:
        st.metric("Total Contacts", len(contacts))
    _MEDIA_TYPE_LABELS = st.session_state.get("ml_MEDIA_TYPE_LABELS", {})
    for i, (mt, count) in enumerate(sorted(type_counts.items(), key=lambda x: -x[1])):
        if i + 1 < len(metric_cols):
            with metric_cols[i + 1]:
                st.metric(_MEDIA_TYPE_LABELS.get(mt, mt), count)

    # Pitch timing
    if result.get("pitch_timing"):
        st.info(f"**Pitch Timing:** {result['pitch_timing']}")

    st.markdown("")

    # Interactive table
    import pandas as pd

    def _fix_url(url: str) -> str:
        """Ensure URL has https:// prefix; return empty string if blank or obviously fake."""
        if not url or url.strip() in ("", "[RESEARCH NEEDED]", "N/A", "n/a"):
            return ""
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    for c in contacts:
        c["outlet_website"] = _fix_url(c.get("outlet_website", ""))
        c["previous_story_url"] = _fix_url(c.get("previous_story_url", ""))

    df = pd.DataFrame(contacts)
    display_cols = [
        "first_name", "last_name", "outlet", "outlet_website", "role", "media_type",
        "location", "pitch_angle", "previous_story_title", "previous_story_url",
        "email", "notes"
    ]
    display_cols = [c for c in display_cols if c in df.columns]

    # Rename columns for display
    col_rename = {
        "first_name": "First Name",
        "last_name": "Last Name",
        "outlet": "Outlet",
        "outlet_website": "Website",
        "role": "Role",
        "media_type": "Media Type",
        "location": "Location",
        "pitch_angle": "Pitch Angle",
        "previous_story_title": "Previous Story",
        "previous_story_url": "Story URL",
        "email": "Email",
        "notes": "Notes",
    }
    display_df = df[display_cols].rename(columns=col_rename)

    # Filter by media type
    type_filter = st.multiselect(
        "Filter by media type",
        options=sorted(type_counts.keys()),
        default=sorted(type_counts.keys()),
        format_func=lambda x: _MEDIA_TYPE_LABELS.get(x, x),
    )
    if type_filter:
        mask = df["media_type"].isin(type_filter)
        display_df = display_df[mask.values]

    # Build column config — make URL fields clickable
    col_config = {}
    if "Story URL" in display_df.columns:
        col_config["Story URL"] = st.column_config.LinkColumn("Story URL", display_text="View story")
    if "Website" in display_df.columns:
        col_config["Website"] = st.column_config.LinkColumn("Website", display_text="Visit")

    st.dataframe(display_df, use_container_width=True, height=500, column_config=col_config)

    # Downloads
    st.divider()
    dl_col1, dl_col2, dl_col3 = st.columns(3)

    with dl_col1:
        xlsx_path = st.session_state.get("ml_xlsx_path")
        if xlsx_path and Path(xlsx_path).exists():
            st.download_button(
                "Download Excel",
                data=Path(xlsx_path).read_bytes(),
                file_name="media_list.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with dl_col2:
        st.download_button(
            "Download Markdown",
            data=st.session_state.get("ml_markdown", ""),
            file_name="media_list.md",
            mime="text/markdown",
        )

    with dl_col3:
        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2, default=str),
            file_name="media_list.json",
            mime="application/json",
        )
