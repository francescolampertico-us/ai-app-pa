"""
Messaging Matrix — Streamlit Page
===================================
Generate a Message House and platform-specific communication variants
from a core policy position.
"""

import streamlit as st
import sys
import os
import json
import tempfile
from pathlib import Path

# Add tool paths
TOOLKIT_ROOT = Path(__file__).resolve().parent.parent.parent
TOOL_ROOT = TOOLKIT_ROOT / "tools" / "messaging_matrix"
STYLE_SAMPLES_DIR = TOOL_ROOT / "style_samples"
STYLE_GUIDES_DIR = STYLE_SAMPLES_DIR / "style_guides"
sys.path.insert(0, str(TOOL_ROOT / "execution"))
sys.path.insert(0, str(TOOLKIT_ROOT / "app"))

st.set_page_config(page_title="Messaging Matrix", page_icon="📣", layout="wide")

from shared import page_header, demo_banner
page_header(
    title="Messaging Matrix",
    icon="📣",
    version="0.2.0",
    risk="yellow",
    digiacomo="#4 Advocacy Campaign Planning",
    description="Takes a core policy position and generates a Message House "
                "(core message, pillars, proof points) plus platform-specific "
                "deliverables: talking points, press statement, social posts, "
                "grassroots email, op-ed, media talking points, and speech draft.",
)


# ─── Inputs ──────────────────────────────────────────────────────────────────

position = st.text_area(
    "Core policy position",
    placeholder="e.g., Support the AI Safety Act — mandatory pre-deployment testing "
                "protects consumers without stifling innovation.",
    height=100,
    help="What is the message you want to communicate? Can be a sentence or a paragraph.",
)

with st.expander("Optional: Core messages & supporting facts", expanded=False):
    core_messages = st.text_area(
        "Core messages (optional)",
        placeholder="If you already have core messages, enter them here.\n"
                    "Otherwise the tool will generate them from your position.",
        height=80,
        help="Pre-defined messages to use as the Message House foundation. "
             "If provided, the LLM will build around these rather than generating new ones.",
    )
    facts = st.text_area(
        "Supporting facts / proof points (optional)",
        placeholder="Key facts, statistics, or evidence to anchor the messaging.\n"
                    "e.g., '67% of consumers support AI safety regulation (Pew, 2026)'",
        height=80,
        help="Specific evidence the tool should use as proof points in the pillars.",
    )

st.markdown("**Supporting context**")
st.caption("Upload documents and/or paste text to ground the messaging in specific facts.")

ctx_col1, ctx_col2 = st.columns(2)
with ctx_col1:
    uploaded_files = st.file_uploader(
        "Upload context documents",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Bill summaries, hearing memos, news clips, background research.",
    )
with ctx_col2:
    context_paste = st.text_area(
        "Or paste context text",
        placeholder="Paste a bill summary, hearing memo excerpt, news clips, "
                    "or any background material...",
        height=120,
    )

# Build combined context from uploads + paste
context_parts = []
if uploaded_files:
    from context_reader import read_uploaded_file
    for uf in uploaded_files:
        try:
            text = read_uploaded_file(uf)
            if text.strip():
                context_parts.append(f"--- {uf.name} ---\n{text}")
        except Exception as e:
            st.warning(f"Could not read {uf.name}: {e}")
if context_paste:
    context_parts.append(context_paste)
context = "\n\n".join(context_parts)

col1, col2 = st.columns(2)
with col1:
    organization = st.text_input(
        "Organization name (optional)",
        placeholder="e.g., TechForward Alliance",
        help="Used for attribution in press statement, op-ed, and speech.",
    )
with col2:
    target_audience = st.text_input(
        "Primary target audience (optional)",
        placeholder="e.g., Senate Commerce Committee members",
        help="Shifts emphasis across all variants toward this audience.",
    )

st.markdown("**Select deliverables to generate:**")
vc1, vc2, vc3, vc4 = st.columns(4)
with vc1:
    v_tp = st.checkbox("Hill Talking Points", value=True)
    v_mtp = st.checkbox("Media Talking Points", value=True)
with vc2:
    v_ps = st.checkbox("News Release", value=True)
    v_sm = st.checkbox("Social Media", value=True)
with vc3:
    v_ge = st.checkbox("Grassroots Email", value=True)
    v_oe = st.checkbox("Op-Ed Draft", value=True)
with vc4:
    v_sd = st.checkbox("Speech Draft", value=True)

selected_variants = []
if v_tp:
    selected_variants.append("talking_points")
if v_mtp:
    selected_variants.append("media_talking_points")
if v_ps:
    selected_variants.append("news_release")
if v_sm:
    selected_variants.append("social_media")
if v_ge:
    selected_variants.append("grassroots_email")
if v_oe:
    selected_variants.append("op_ed")
if v_sd:
    selected_variants.append("speech_draft")


# ─── Generate ────────────────────────────────────────────────────────────────

demo = demo_banner()

if position and selected_variants and st.button("Generate Messaging Matrix", type="primary", disabled=demo):
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY not set. Please configure your API key.")
    else:
        with st.spinner("Generating Message House and deliverables..."):
            try:
                import importlib.util as _ilu
                _gen_spec = _ilu.spec_from_file_location("mm_generator", TOOL_ROOT / "execution" / "generator.py")
                _gen = _ilu.module_from_spec(_gen_spec); _gen_spec.loader.exec_module(_gen)
                generate_matrix = _gen.generate_matrix
                render_markdown = _gen.render_markdown

                _exp_spec = _ilu.spec_from_file_location("mm_export", TOOL_ROOT / "execution" / "export.py")
                _exp = _ilu.module_from_spec(_exp_spec); _exp_spec.loader.exec_module(_exp)
                export_docx = _exp.export_docx

                result = generate_matrix(
                    position=position,
                    context=context,
                    organization=organization,
                    target_audience=target_audience,
                    core_messages=core_messages,
                    facts=facts,
                    variants=selected_variants,
                    style_guides_dir=str(STYLE_GUIDES_DIR),
                )

                st.session_state["mm_result"] = result
                st.session_state["mm_markdown"] = render_markdown(result)

                # Export DOCX to temp file
                tmpdir = tempfile.mkdtemp()
                docx_path = Path(tmpdir) / "messaging_matrix.docx"
                export_docx(result, str(docx_path))
                st.session_state["mm_docx_path"] = str(docx_path)

            except Exception as e:
                st.error(f"Error generating matrix: {e}")
                import traceback
                st.code(traceback.format_exc())


# ─── Display Results ─────────────────────────────────────────────────────────

VARIANT_LABELS = {
    "talking_points": "Hill Talking Points",
    "media_talking_points": "Media Talking Points",
    "news_release": "News Release",
    "social_media": "Social Media Posts",
    "grassroots_email": "Grassroots Email",
    "op_ed": "Op-Ed Draft",
    "speech_draft": "Speech Draft",
}

if "mm_result" in st.session_state:
    result = st.session_state["mm_result"]
    house = result["message_house"]

    # Build tabs
    tab_names = ["Message Map"] + [
        VARIANT_LABELS.get(vid, vid) for vid in result.get("variants", {})
    ]
    tabs = st.tabs(tab_names)

    # Message Map tab
    with tabs[0]:
        overarching = house.get("overarching_message", house.get("core_message", ""))
        key_messages = house.get("key_messages", house.get("pillars", []))

        if house.get("target_audiences"):
            st.markdown(f"**Target Audiences:** {', '.join(house['target_audiences'])}")

        st.markdown("### Overarching Message")
        st.info(overarching)

        # Build message map as a table using pandas
        if key_messages:
            import pandas as pd
            # Build table data
            headers = [f"Key Message {i+1}" for i in range(len(key_messages))]
            rows = []

            # Key message titles row
            titles = []
            for km in key_messages:
                titles.append(km.get("title", km.get("name", "")))
            rows.append(titles)

            # Supporting facts rows
            max_facts = max(
                len(km.get("supporting_facts", km.get("proof_points", [])))
                for km in key_messages
            )
            for fi in range(max_facts):
                row = []
                for km in key_messages:
                    facts = km.get("supporting_facts", km.get("proof_points", []))
                    row.append(facts[fi] if fi < len(facts) else "")
                rows.append(row)

            # Create DataFrame
            index_labels = ["**Key Message**"] + [f"**Supporting Fact {i+1}**" for i in range(max_facts)]
            df = pd.DataFrame(rows, columns=headers, index=index_labels)
            st.table(df)

        if house.get("key_terms"):
            st.markdown(f"**Key Terms:** {', '.join(house['key_terms'])}")

    # Variant tabs
    for idx, (vid, content) in enumerate(result.get("variants", {}).items(), 1):
        with tabs[idx]:
            st.markdown(content)

    # Downloads
    st.divider()
    dl_col1, dl_col2, dl_col3 = st.columns(3)

    with dl_col1:
        st.download_button(
            "Download Markdown",
            data=st.session_state.get("mm_markdown", ""),
            file_name="messaging_matrix.md",
            mime="text/markdown",
        )

    with dl_col2:
        docx_path = st.session_state.get("mm_docx_path")
        if docx_path and Path(docx_path).exists():
            st.download_button(
                "Download DOCX",
                data=Path(docx_path).read_bytes(),
                file_name="messaging_matrix.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    with dl_col3:
        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2),
            file_name="messaging_matrix.json",
            mime="application/json",
        )


# ─── Writing Style Section ───────────────────────────────────────────────────

st.divider()

with st.expander("Writing Style Personalization", expanded=False):
    st.markdown(
        "Drop your writing samples and reference materials into the "
        f"`style_samples/` folder, then click **Build Style Guides** to analyze them. "
        "Generated guides are automatically applied when generating deliverables."
    )
    st.caption(
        f"Samples folder: `{STYLE_SAMPLES_DIR.relative_to(TOOLKIT_ROOT)}/`"
    )

    # Show status
    from style_analyzer import get_style_status, analyze_all, DOC_TYPES

    status = get_style_status(str(STYLE_SAMPLES_DIR))

    status_cols = st.columns(3)
    for i, (doc_type, info) in enumerate(status.items()):
        with status_cols[i % 3]:
            icon = ""
            if info["has_guide"]:
                icon = "--- "
            parts = []
            if info["sample_count"] > 0:
                parts.append(f"{info['sample_count']} samples")
            if info["reference_count"] > 0:
                parts.append(f"{info['reference_count']} refs")
            if info["has_guide"]:
                parts.append("guide built")

            label = info["label"]
            detail = ", ".join(parts) if parts else "no files yet"
            st.markdown(f"**{label}**: {detail}")

    st.markdown("")

    if st.button("Build Style Guides", type="secondary"):
        if not os.environ.get("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY not set.")
        else:
            has_any = any(
                s["has_samples"] or s["has_references"] for s in status.values()
            )
            if not has_any:
                st.warning("No samples found. Add files to the style_samples/ subfolders first.")
            else:
                with st.spinner("Analyzing writing samples..."):
                    try:
                        results = analyze_all(str(STYLE_SAMPLES_DIR))
                        if results:
                            st.success(
                                f"Style guides generated for: {', '.join(DOC_TYPES[k] for k in results)}"
                            )
                        else:
                            st.warning("No samples found to analyze.")
                    except Exception as e:
                        st.error(f"Error analyzing samples: {e}")

    # Show existing style guides
    if STYLE_GUIDES_DIR.exists():
        guides = list(STYLE_GUIDES_DIR.glob("*.md"))
        if guides:
            st.markdown("---")
            st.markdown("**Generated Style Guides:**")
            guide_tabs = st.tabs([g.stem.replace("_style_guide", "").replace("_", " ").title() for g in guides])
            for tab, guide_file in zip(guide_tabs, guides):
                with tab:
                    st.markdown(guide_file.read_text(encoding="utf-8"))
