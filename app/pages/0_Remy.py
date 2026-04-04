"""
Remy — Streamlit assistant page
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
APP_ROOT = TOOLKIT_ROOT / "app"

import sys

sys.path.insert(0, str(APP_ROOT))

from remy_assistant import chat_with_remy, default_greeting
from shared import demo_banner, page_header

st.set_page_config(page_title="Remy", page_icon="🎯", layout="wide")

page_header(
    title="Remy",
    icon="🎯",
    version="0.1.0",
    risk="yellow",
    digiacomo="Cross-tool assistant",
    description="Tool-aware public affairs assistant. Remy can route work to the right toolkit page, "
                "collect missing inputs, and execute supported tools through the app's existing backend scripts.",
)


def _ensure_state() -> None:
    if "remy_messages" not in st.session_state:
        st.session_state["remy_messages"] = [
            {"role": "assistant", "content": default_greeting(), "tool_events": []}
        ]
    if "remy_upload_dir" not in st.session_state:
        st.session_state["remy_upload_dir"] = tempfile.mkdtemp(prefix="remy_uploads_")


def _stash_uploads(uploaded_files) -> list[dict]:
    upload_dir = Path(st.session_state["remy_upload_dir"])
    manifest = []
    for uploaded_file in uploaded_files:
        destination = upload_dir / uploaded_file.name
        destination.write_bytes(uploaded_file.getbuffer())
        manifest.append(
            {
                "name": uploaded_file.name,
                "path": str(destination),
                "size_bytes": destination.stat().st_size,
                "kind": destination.suffix.lower().lstrip(".") or "file",
            }
        )
    return manifest


def _render_tool_events(tool_events: list[dict], message_idx: int) -> None:
    for event_idx, event in enumerate(tool_events):
        label = event.get("tool_id") or "tool"
        status = "completed" if event.get("ok") else "failed"
        with st.expander(f"{label} {status}", expanded=not event.get("ok", False)):
            if event.get("page_path"):
                st.page_link(event["page_path"], label="Open tool page", icon="➡️")

            if event.get("error"):
                st.error(event["error"])
            if event.get("stderr"):
                st.code(event["stderr"], language="text")

            artifacts = event.get("artifacts") or []
            if artifacts:
                st.markdown("**Artifacts**")
            for artifact_idx, artifact in enumerate(artifacts):
                artifact_path = Path(artifact["path"])
                if not artifact_path.exists():
                    continue
                st.caption(artifact["path"])
                with open(artifact_path, "rb") as f:
                    st.download_button(
                        label=f"Download {artifact['name']}",
                        data=f.read(),
                        file_name=artifact["name"],
                        key=f"remy-{message_idx}-{event_idx}-{artifact_idx}",
                    )

            previews = event.get("artifact_previews") or []
            for preview in previews:
                st.markdown(f"**Preview: {preview['name']}**")
                st.code(preview["preview"], language="text")


_ensure_state()

left, right = st.columns([3, 1])

with right:
    st.markdown("### Remy's brief")
    st.caption(
        "Strategic, disciplined, discreet. Built for public affairs work, not generic chit-chat."
    )
    st.markdown(
        "- routes users to the right tool\n"
        "- asks only for missing inputs\n"
        "- runs supported tools when inputs are ready\n"
        "- flags review needs on medium-risk outputs"
    )
    with st.expander("Settings", expanded=False):
        model = st.text_input("OpenAI model", value="gpt-4o-mini")
        clear_chat = st.button("Clear conversation")
        if clear_chat:
            st.session_state["remy_messages"] = [
                {"role": "assistant", "content": default_greeting(), "tool_events": []}
            ]
            st.rerun()

    uploads = st.file_uploader(
        "Working files",
        type=["pdf", "txt", "md", "docx", "json", "csv", "html", "xlsx"],
        accept_multiple_files=True,
        help="Upload transcripts, policy docs, context notes, article text, or other source material Remy may need.",
    )
    uploaded_manifest = _stash_uploads(uploads or [])
    if uploaded_manifest:
        st.markdown("**Available files**")
        for item in uploaded_manifest:
            st.caption(item["name"])
    else:
        st.caption("No working files uploaded.")

with left:
    demo = demo_banner()
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY not set. Remy needs an OpenAI API key to operate.")

    st.info(
        "Try prompts like: 'Which tool should I use to prep for a meeting with Sen. Cantwell?', "
        "'Run a background memo on Jagello 2000 with sections leadership, U.S. presence, and policy positions.', "
        "or 'Clean this pasted article text for clips.'"
    )

    for idx, message in enumerate(st.session_state["remy_messages"]):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                _render_tool_events(message.get("tool_events") or [], idx)

    prompt = st.chat_input(
        "Tell Remy the objective.",
        disabled=demo or not os.environ.get("OPENAI_API_KEY"),
    )

    if prompt:
        st.session_state["remy_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        history = [
            {"role": item["role"], "content": item["content"]}
            for item in st.session_state["remy_messages"]
            if item["role"] in {"user", "assistant"}
        ]

        with st.chat_message("assistant"):
            with st.spinner("Remy is working..."):
                try:
                    response = chat_with_remy(
                        user_message=prompt,
                        history=history[:-1],
                        uploaded_files=uploaded_manifest,
                        model=model,
                    )
                    st.markdown(response["text"])
                    _render_tool_events(response.get("tool_events") or [], len(st.session_state["remy_messages"]))
                    st.session_state["remy_messages"].append(
                        {
                            "role": "assistant",
                            "content": response["text"],
                            "tool_events": response.get("tool_events") or [],
                        }
                    )
                except Exception as exc:
                    error_text = f"Remy hit an error: {exc}"
                    st.error(error_text)
                    st.session_state["remy_messages"].append(
                        {"role": "assistant", "content": error_text, "tool_events": []}
                    )
