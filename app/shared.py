"""
Shared UI components for all toolkit pages.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the toolkit root (one level above app/)
_toolkit_root = Path(__file__).resolve().parent.parent
load_dotenv(_toolkit_root / ".env")

import streamlit as st


def is_demo_mode() -> bool:
    """Check if running in demo mode (deployed without API keys)."""
    return os.environ.get("DEMO_MODE", "").lower() in ("true", "1", "yes")


def demo_banner():
    """Show a banner explaining that tool execution is disabled in demo mode."""
    if is_demo_mode():
        st.warning(
            "**Demo Mode** — This is a read-only preview of the PA AI Toolkit. "
            "Tool execution is disabled because it requires API keys (OpenAI, LegiScan) "
            "and would incur costs. You can explore the interface and see example outputs. "
            "For a live demo, contact Francesco Lampertico.",
            icon="🔒",
        )
        return True
    return False


def inject_custom_css():
    """Inject shared CSS for consistent styling across pages."""
    st.markdown("""
    <style>
        /* Tighter top padding */
        .block-container { padding-top: 2rem; }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background-color: #f8f9fb;
            border: 1px solid #e0e4e8;
            border-radius: 8px;
            padding: 12px 16px;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1.5rem;
        }

        /* Tabs: bolder active tab */
        button[data-baseweb="tab"] {
            font-weight: 500;
        }

        /* Bordered containers (tool cards on home) */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 10px;
        }

        /* Dataframe: subtle header */
        .stDataFrame thead th {
            background-color: #f0f2f6 !important;
        }

        /* Expander headers */
        div[data-testid="stExpander"] summary {
            font-weight: 500;
        }

        /* Download buttons: subtler */
        .stDownloadButton > button {
            border-radius: 6px;
        }

        /* Footer captions */
        .footer-caption {
            text-align: center;
            color: #6c757d;
            font-size: 0.8rem;
            padding: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)


def sidebar_nav():
    """Render the consistent sidebar navigation."""
    st.sidebar.markdown("### PA AI Toolkit")
    st.sidebar.caption("AI-powered tools for public affairs")
    st.sidebar.divider()

    st.sidebar.page_link("streamlit_app.py", label="Home", icon="🏠")
    st.sidebar.page_link("pages/1_Hearing_Memo.py", label="Hearing Memo", icon="📝")
    st.sidebar.page_link("pages/2_Media_Clips.py", label="Media Clips", icon="📰")
    st.sidebar.page_link("pages/3_Disclosure_Tracker.py", label="Disclosure Tracker", icon="🔍")
    st.sidebar.page_link("pages/4_Legislative_Tracker.py", label="Legislative Tracker", icon="📜")
    st.sidebar.page_link("pages/5_Literature_Review.py", label="Literature Review", icon="📚")

    st.sidebar.divider()
    st.sidebar.caption("Francesco Lampertico")
    st.sidebar.caption("M.A. Political Communication")
    st.sidebar.caption("American University, 2026")


def page_header(title: str, icon: str, version: str, risk: str, digiacomo: str, description: str):
    """Render a consistent page header for tool pages."""
    inject_custom_css()
    sidebar_nav()

    st.markdown(f"# {icon} {title}")

    risk_badge = {"green": "🟢 Low", "yellow": "🟡 Medium", "red": "🔴 High"}.get(risk, risk)
    st.caption(f"v{version}  |  Risk: {risk_badge}  |  DiGiacomo: {digiacomo}")
    st.markdown(description)
    st.divider()


def page_footer():
    """Render a consistent footer for tool pages."""
    st.divider()
    st.caption(
        "Public Affairs AI Toolkit — Capstone Project, American University. "
        "Francesco Lampertico, M.A. Political Communication (May 2026)."
    )
