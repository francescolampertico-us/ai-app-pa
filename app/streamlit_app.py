"""
Public Affairs AI Toolkit — Streamlit App
==========================================
Main entry point. Home dashboard with tool catalog and framework coverage.
"""

import sys
import streamlit as st
import yaml
from pathlib import Path

# --- Page config ---
st.set_page_config(
    page_title="PA AI Toolkit",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Load shared components ---
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared import inject_custom_css, sidebar_nav, page_footer, demo_banner

inject_custom_css()
sidebar_nav()
demo_banner()

# --- Load tool registry ---
TOOLKIT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = TOOLKIT_ROOT / "tool-registry.yaml"


@st.cache_data
def load_registry():
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


registry = load_registry()

# =====================================================================
# Hero section
# =====================================================================
st.markdown("""
# Public Affairs AI Toolkit

A suite of AI-powered tools for public affairs professionals — from legislative
monitoring to hearing analysis to disclosure tracking. Built on the
**DiGiacomo (2026)** framework for PA management.
""")

# --- Key metrics ---
tools = registry.get("tools", [])
m1, m2, m3, m4 = st.columns(4)
m1.metric("Tools Built", len(tools))
m2.metric("DiGiacomo Processes", "3 of 5")
m3.metric("Architecture", "DOE")
m4.metric("Risk Governance", "3-Tier")

st.divider()

# =====================================================================
# Tool Catalog
# =====================================================================
st.markdown("## Tool Catalog")
st.markdown("Each tool follows the **DOE pattern** — Directive (task specification), "
            "Orchestration (data gathering & processing), Execution (verified output).")
st.markdown("")

RISK_BADGES = {"green": "🟢 Low", "yellow": "🟡 Medium", "red": "🔴 High"}
TOOL_ICONS = {
    "hearing_memo_generator": "📝",
    "media_clips": "📰",
    "media_clip_cleaner": "✂️",
    "influence_disclosure_tracker": "🔍",
    "legislative_tracker": "📜",
}
DIGIACOMO_MAP = {
    "hearing_memo_generator": "#3 Briefing & Position Papers",
    "media_clips": "#1 Monitoring & Analysis",
    "media_clip_cleaner": "#1 Monitoring & Analysis",
    "influence_disclosure_tracker": "#2 Stakeholder Intelligence",
    "legislative_tracker": "#1 Monitoring & Analysis",
}
TOOL_PAGES = {
    "hearing_memo_generator": "pages/1_Hearing_Memo.py",
    "media_clips": "pages/2_Media_Clips.py",
    "influence_disclosure_tracker": "pages/3_Disclosure_Tracker.py",
    "legislative_tracker": "pages/4_Legislative_Tracker.py",
}

# Display tools in a 2-column grid
col_left, col_right = st.columns(2)
for i, tool in enumerate(tools):
    col = col_left if i % 2 == 0 else col_right
    tid = tool["id"]
    icon = TOOL_ICONS.get(tid, "🔧")
    risk = RISK_BADGES.get(tool.get("risk_level", ""), tool.get("risk_level", ""))
    digiacomo = DIGIACOMO_MAP.get(tid, "")
    page = TOOL_PAGES.get(tid)

    with col:
        with st.container(border=True):
            st.markdown(f"### {icon} {tool['name']}")
            st.caption(f"v{tool['version']}  |  Risk: {risk}  |  {digiacomo}")
            st.markdown(tool.get("description", ""))

            c1, c2 = st.columns(2)
            with c1:
                inputs_req = tool.get("inputs", {}).get("required", [])
                st.markdown(f"**Inputs:** `{', '.join(inputs_req)}`")
            with c2:
                artifacts = tool.get("outputs", {}).get("artifacts", [])
                st.markdown(f"**Outputs:** `{', '.join(artifacts)}`")

            if page:
                st.page_link(page, label=f"Open {tool['name']}", icon="➡️")

st.divider()

# =====================================================================
# DiGiacomo Framework Coverage
# =====================================================================
st.markdown("## DiGiacomo Framework Coverage")
st.markdown("The toolkit maps to the 5 basic PA processes identified in "
            "DiGiacomo (2026). Green = built, gray = planned for final delivery.")

framework = [
    {"Process": "1. Monitoring & Analysis",
     "Tools": "Media Clips, Legislative Tracker",
     "Status": "🟢 Built"},
    {"Process": "2. Stakeholder Intelligence",
     "Tools": "Influence Disclosure Tracker",
     "Status": "🟢 Built"},
    {"Process": "3. Briefing & Position Papers",
     "Tools": "Hearing Memo Generator",
     "Status": "🟢 Built"},
    {"Process": "4. Strategy Design",
     "Tools": "Messaging Matrix, Meeting Prep Brief",
     "Status": "⬜ Planned"},
    {"Process": "5. Assessment & Reporting",
     "Tools": "PA Performance Tracker",
     "Status": "⬜ Planned"},
]

st.dataframe(
    framework,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Process": st.column_config.TextColumn(width="large"),
        "Tools": st.column_config.TextColumn(width="large"),
        "Status": st.column_config.TextColumn(width="small"),
    },
)

st.divider()

# =====================================================================
# Architecture & Governance
# =====================================================================
col_arch, col_gov = st.columns(2)

with col_arch:
    st.markdown("### Architecture: DOE Pattern")
    st.markdown("""
Every tool follows a three-stage pipeline:

1. **Directive** — Task specification with explicit constraints and output contract
2. **Orchestration** — Data gathering, API calls, filtering, LLM processing
3. **Execution** — Deliverable production with verification and human review gate

This separates *what to do* from *how to do it* from *quality control*,
keeping each stage testable and auditable.
""")

with col_gov:
    st.markdown("### Governance: Risk Tiers")
    st.markdown("""
Each tool declares a risk level that determines review requirements:

- **🟢 Low** — Output can be used directly (e.g., text cleaning)
- **🟡 Medium** — Requires human review before external use (e.g., AI summaries, memos)
- **🔴 High** — Requires expert review and approval (e.g., legal/compliance content)

All AI-generated content carries a provenance notice and review checklist.
""")

# --- Footer ---
page_footer()
