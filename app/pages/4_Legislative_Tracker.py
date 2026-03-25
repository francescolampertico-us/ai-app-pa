"""
Legislative Tracker — Streamlit Page
======================================
Search, track, and summarize legislation via the LegiScan API.
Click any row in the results table to select a bill, then track or summarize it.
"""

import streamlit as st
import sys
import subprocess
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "legislative_tracker"
CACHE_DIR = TOOL_ROOT / "execution" / ".cache"
sys.path.insert(0, str(TOOLKIT_ROOT / "app"))

st.set_page_config(page_title="Legislative Tracker", page_icon="📜", layout="wide")

from shared import page_header
page_header(
    title="Legislative Tracker",
    icon="📜",
    version="0.1.0",
    risk="yellow",
    digiacomo="#1 Legislative Monitoring",
    description="Search, track, and summarize legislation across federal and state jurisdictions. "
                "Powered by the LegiScan API.",
)


# =============================================================
# Helpers
# =============================================================

def _run_cli(extra_args: list, timeout: int = 120) -> tuple:
    """Run the legislative tracker CLI and return (stdout, stderr, returncode)."""
    cmd = [sys.executable, str(TOOL_ROOT / "execution" / "run.py"), "--json"] + extra_args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(TOOL_ROOT / "execution"),
    )
    return result.stdout, result.stderr, result.returncode


def _load_watchlist() -> list[dict]:
    """Load the watchlist directly from the cache file."""
    wl_path = CACHE_DIR / "watchlist.json"
    if wl_path.exists():
        try:
            data = json.loads(wl_path.read_text())
            return list(data.get("bills", {}).values())
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def _build_results_df(bills: list[dict]) -> pd.DataFrame:
    """Build a display DataFrame from a list of bill dicts."""
    rows = []
    for b in bills:
        title = b.get("title", "")
        if len(title) > 80:
            title = title[:77] + "..."
        last_action = b.get("last_action", "")
        if len(last_action) > 50:
            last_action = last_action[:47] + "..."
        rows.append({
            "Bill": b.get("number", ""),
            "Title": title,
            "State": b.get("state", ""),
            "Status": b.get("status", ""),
            "Last Action": last_action,
            "Date": b.get("last_action_date", ""),
        })
    return pd.DataFrame(rows)


def _show_bill_detail(bill: dict):
    """Show bill metadata in a compact panel."""
    st.markdown(f"#### {bill.get('number', '')} — {bill.get('title', '')}")

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(f"**State:** {bill.get('state', 'N/A')}")
    with mc2:
        st.markdown(f"**Status:** {bill.get('status', 'N/A')}")
    with mc3:
        st.markdown(f"**Date:** {bill.get('last_action_date', 'N/A')}")
    with mc4:
        url = bill.get("url", "")
        if url:
            st.markdown(f"[View on LegiScan]({url})")

    last_action = bill.get("last_action", "")
    if last_action:
        st.markdown(f"> {last_action}")


def _generate_summary(bill_id: int):
    """Generate and cache AI summary for a bill."""
    with st.spinner(f"Fetching bill text and generating AI analysis... (may take 1-3 minutes for long bills)"):
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                stdout, stderr, rc = _run_cli([
                    "--bill-id", str(bill_id),
                    "--summarize",
                    "--out", tmpdir,
                ], timeout=300)

                if rc != 0:
                    st.error(f"Summary failed: {stderr}")
                    return

                # Try JSON output first, fall back to markdown file
                summary_md = ""
                try:
                    data = json.loads(stdout)
                    st.session_state["lt_bill_detail_json"] = data.get("bill", {})
                    summary_md = data.get("summary", "")
                except json.JSONDecodeError:
                    pass

                if not summary_md:
                    summaries = list(Path(tmpdir).rglob("bill_summary.md"))
                    if summaries:
                        summary_md = summaries[0].read_text()

                st.session_state["lt_summary_md"] = summary_md
                st.session_state["lt_summary_bill_id"] = bill_id

        except subprocess.TimeoutExpired:
            st.error("Summary timed out. The bill may be very long.")
        except Exception as e:
            st.error(f"Error: {e}")


def _display_summary():
    """Display the cached summary if it matches the current bill."""
    summary_md = st.session_state.get("lt_summary_md", "")
    if not summary_md:
        return

    st.divider()
    st.markdown(summary_md)

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            "Download Summary (Markdown)",
            data=summary_md,
            file_name="bill_summary.md",
            mime="text/markdown",
            key="dl_summary",
        )
    with dl_col2:
        detail = st.session_state.get("lt_bill_detail_json", {})
        if detail:
            st.download_button(
                "Download Bill Detail (JSON)",
                data=json.dumps(detail, indent=2),
                file_name="bill_detail.json",
                mime="application/json",
                key="dl_detail",
            )


# =============================================================
# Tab layout
# =============================================================
tab_search, tab_watchlist = st.tabs(["🔎 Search & Discover", "📋 Watchlist"])


# =============================================================
# Tab 1: Search & Discover
# =============================================================
with tab_search:
    col_query, col_state, col_year = st.columns([3, 1, 1])
    with col_query:
        query = st.text_input(
            "Search keywords",
            placeholder="e.g., artificial intelligence, data privacy",
            help="Enter keywords to search across bill titles and descriptions",
        )
    with col_state:
        states = ["US (Federal)"] + [
            s for s in [
                "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
                "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
                "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
                "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
            ]
        ]
        state_sel = st.selectbox("Jurisdiction", states, index=0)
        state_code = state_sel.split(" ")[0] if " " in state_sel else state_sel
    with col_year:
        current_year = datetime.now().year
        year = st.number_input("Year", min_value=2010, max_value=current_year + 1,
                               value=current_year, step=1)

    if query and st.button("Search Bills", type="primary", key="btn_search"):
        # Clear previous state
        for k in ["lt_search_results", "lt_summary_md", "lt_summary_bill_id",
                   "lt_bill_detail_json"]:
            st.session_state.pop(k, None)

        with st.spinner(f"Searching for '{query}' in {state_code}..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    stdout, stderr, rc = _run_cli([
                        "--query", query,
                        "--state", state_code,
                        "--year", str(year),
                        "--out", tmpdir,
                    ], timeout=60)

                    if rc != 0:
                        st.error(f"Search failed: {stderr}")
                    else:
                        try:
                            results = json.loads(stdout)
                        except json.JSONDecodeError:
                            results_path = Path(tmpdir) / "search_results.json"
                            results = json.loads(results_path.read_text()) if results_path.exists() else []

                        st.session_state["lt_search_results"] = results
                        st.session_state["lt_search_query"] = query

            except subprocess.TimeoutExpired:
                st.error("Search timed out. Try more specific keywords.")
            except Exception as e:
                st.error(f"Error: {e}")

    # --- Display search results with clickable rows ---
    results = st.session_state.get("lt_search_results", [])
    if results:
        st.subheader(f"Found {len(results)} bills — click a row to select it")

        df = _build_results_df(results)
        event = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="search_df",
        )

        # Get selected row
        selected_rows = event.selection.rows if event.selection else []

        if selected_rows:
            idx = selected_rows[0]
            selected_bill = results[idx]

            st.divider()
            _show_bill_detail(selected_bill)

            bill_id = selected_bill.get("bill_id")

            # Action buttons
            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button("📋 Add to Watchlist", key="s_track", use_container_width=True):
                    with st.spinner("Adding..."):
                        stdout, stderr, rc = _run_cli([
                            "--watchlist", "add", "--bill-id", str(bill_id),
                        ])
                        if rc == 0:
                            st.success("Added to watchlist!")
                        else:
                            st.info(stdout.strip() or stderr.strip() or "Already tracked")
            with btn2:
                if st.button("📄 Generate AI Summary", key="s_summarize", use_container_width=True):
                    _generate_summary(bill_id)

            # Show summary if we have one for this bill
            if st.session_state.get("lt_summary_bill_id") == bill_id:
                _display_summary()

        # Download full results
        st.download_button(
            "Download Full Results (JSON)",
            data=json.dumps(results, indent=2),
            file_name="search_results.json",
            mime="application/json",
            key="dl_search",
        )

    elif not query:
        st.info("Enter keywords to search for legislation across federal and state jurisdictions.")


# =============================================================
# Tab 2: Watchlist
# =============================================================
with tab_watchlist:
    wl_header_col, wl_btn_col = st.columns([3, 1])
    with wl_header_col:
        st.subheader("Tracked Bills")
    with wl_btn_col:
        refresh_clicked = st.button("🔄 Refresh All", key="btn_refresh_wl")

    if refresh_clicked:
        with st.spinner("Checking for status changes..."):
            stdout, stderr, rc = _run_cli(["--watchlist", "refresh"])
            if rc == 0:
                try:
                    data = json.loads(stdout)
                    refresh_results = data.get("refresh_results", [])
                    changed = [r for r in refresh_results if r.get("changed")]
                    if changed:
                        st.warning(f"⚠️ {len(changed)} bill(s) have status changes!")
                        for r in changed:
                            st.markdown(
                                f"- **{r['number']}** ({r['state']}): "
                                f"{r.get('old_status', '?')} → **{r.get('new_status', '?')}**"
                            )
                    else:
                        st.success("All bills up to date — no changes detected.")
                except json.JSONDecodeError:
                    st.info("Watchlist refreshed.")
            else:
                st.error(f"Refresh failed: {stderr}")

    # Load watchlist
    watchlist = _load_watchlist()

    if watchlist:
        wl_df_data = []
        for b in watchlist:
            title = b.get("title", "")
            if len(title) > 60:
                title = title[:57] + "..."
            last_action = b.get("last_action", "")
            if len(last_action) > 50:
                last_action = last_action[:47] + "..."
            wl_df_data.append({
                "Bill": b.get("number", ""),
                "Title": title,
                "State": b.get("state", ""),
                "Status": b.get("status", ""),
                "Last Action": last_action,
                "Tracked Since": b.get("added_at", "")[:10],
            })

        wl_df = pd.DataFrame(wl_df_data)
        wl_event = st.dataframe(
            wl_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="wl_df",
        )

        # Get selected row
        wl_selected_rows = wl_event.selection.rows if wl_event.selection else []

        if wl_selected_rows:
            wl_idx = wl_selected_rows[0]
            wl_bill = watchlist[wl_idx]

            st.divider()
            _show_bill_detail(wl_bill)

            wl_bill_id = wl_bill.get("bill_id")

            wc1, wc2 = st.columns(2)
            with wc1:
                if st.button("📄 Generate AI Summary", key="wl_summarize", use_container_width=True):
                    _generate_summary(wl_bill_id)
            with wc2:
                if st.button("🗑️ Remove from Watchlist", key="wl_remove", use_container_width=True):
                    stdout, stderr, rc = _run_cli([
                        "--watchlist", "remove", "--bill-id", str(wl_bill_id),
                    ])
                    if rc == 0:
                        st.success("Removed.")
                        st.rerun()
                    else:
                        st.error(f"Failed: {stderr}")

            # Show summary if we have one for this bill
            if st.session_state.get("lt_summary_bill_id") == wl_bill_id:
                _display_summary()

    else:
        st.info("No bills in your watchlist. Search for bills and click **Add to Watchlist** to start tracking.")

    st.divider()
    st.caption(
        "⚠️ **Risk: Yellow** — AI-generated summaries require human review before external distribution. "
        "Verify bill provisions, sponsor information, and talking points against official sources."
    )
