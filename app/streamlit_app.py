"""
Public Affairs AI Toolkit — Streamlit App
==========================================
Main entry point. Sidebar navigation + home dashboard.
"""

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

# --- Load tool registry ---
TOOLKIT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = TOOLKIT_ROOT / "tool-registry.yaml"


@st.cache_data
def load_registry():
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


registry = load_registry()

# --- Sidebar ---
st.sidebar.title("PA AI Toolkit")
st.sidebar.markdown("AI-powered tools for public affairs professionals")
st.sidebar.divider()
st.sidebar.markdown("**Navigation**")
st.sidebar.page_link("streamlit_app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/1_Hearing_Memo.py", label="Hearing Memo Generator", icon="📝")
st.sidebar.page_link("pages/2_Media_Clips.py", label="Media Clips", icon="📰")
st.sidebar.page_link("pages/3_Clip_Cleaner.py", label="Clip Cleaner", icon="✂️")
st.sidebar.page_link("pages/4_Disclosure_Tracker.py", label="Disclosure Tracker", icon="🔍")
st.sidebar.divider()
st.sidebar.caption("Capstone Project — Francesco Lampertico")
st.sidebar.caption("M.A. Political Communication, American University")

# --- Home page ---
st.title("Public Affairs AI Toolkit")
st.markdown(
    """
    An AI-powered toolkit for public affairs professionals, grounded in the
    **DiGiacomo (2025)** framework for PA management. Each tool follows the
    **DOE pattern** (Directive-Orchestration-Execution) with built-in verification
    and human review gates.
    """
)

# --- Tool catalog ---
st.header("Tool Catalog")

RISK_BADGES = {
    "green": "🟢 Green",
    "yellow": "🟡 Yellow",
    "red": "🔴 Red",
}

DIGIACOMO_MAP = {
    "hearing_memo_generator": "#3 Briefing Creation",
    "media_clips": "#1 Legislative Monitoring",
    "media_clip_cleaner": "#1 Legislative Monitoring",
    "influence_disclosure_tracker": "#2 Stakeholder Analysis",
}

tools = registry.get("tools", [])
cols = st.columns(2)

for i, tool in enumerate(tools):
    with cols[i % 2]:
        risk = RISK_BADGES.get(tool.get("risk_level", ""), tool.get("risk_level", ""))
        digiacomo = DIGIACOMO_MAP.get(tool["id"], "—")

        st.subheader(tool["name"])
        st.caption(f"v{tool['version']}  |  Risk: {risk}  |  DiGiacomo: {digiacomo}")
        st.markdown(tool.get("description", ""))

        inputs_req = tool.get("inputs", {}).get("required", [])
        st.markdown(f"**Inputs:** {', '.join(inputs_req)}")

        artifacts = tool.get("outputs", {}).get("artifacts", [])
        st.markdown(f"**Outputs:** {', '.join(artifacts)}")
        st.divider()

# --- DiGiacomo framework coverage ---
st.header("DiGiacomo Framework Coverage")

framework_data = {
    "Workflow": [
        "1. Legislative/Regulatory Monitoring",
        "2. Stakeholder Mapping & Analysis",
        "3. Position Paper & Briefing Creation",
        "4. Advocacy Campaign Planning",
        "5. Digital Public Affairs",
        "6. Crisis Communication",
        "7. Institutional Relationship Management",
        "8. Performance Measurement",
    ],
    "Tool(s)": [
        "Media Clips, Bill/Regulation Summary (planned)",
        "Influence Disclosure Tracker, Stakeholder Map (planned)",
        "Hearing Memo Generator, Stakeholder Briefing (planned)",
        "Messaging Matrix (planned), Stakeholder Map (planned)",
        "Messaging Matrix (planned)",
        "Crisis Response Brief (planned)",
        "Meeting Prep Brief (planned)",
        "PA Performance Tracker (planned)",
    ],
    "Status": [
        "Partial",
        "Partial",
        "Partial",
        "Planned",
        "Planned",
        "Planned",
        "Planned",
        "Planned",
    ],
}

st.table(framework_data)

# --- Footer ---
st.divider()
st.markdown(
    """
    **Architecture:** Every tool follows the DOE pattern — Directive (task specification),
    Orchestration (data gathering & processing), Execution (verified output with human review gate).

    **Governance:** Tools are classified by risk level (green/yellow/red) with corresponding
    review requirements. See `STYLE_GUIDE.md` and `RISK_POLICY.md` for details.
    """
)
