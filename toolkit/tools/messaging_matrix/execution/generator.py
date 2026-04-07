"""
Messaging Matrix Generator
============================
Two-step LLM pipeline:
  Step 1 — gpt-4.1 builds the Message House (strategic foundation)
  Step 2 — gpt-4.1-mini generates each platform variant (format adaptation)

Optional inputs:
  - core_messages: User-provided core messages (skip LLM generation for these)
  - facts: User-provided proof points to seed the pillars
  - style_guides_dir: Path to style_samples/style_guides/ for style injection
"""

import os
import json
import sys
from pathlib import Path
from openai import OpenAI

from formats import VARIANT_IDS, VARIANT_LABELS, VARIANT_PROMPTS
from context_reader import read_directory


STRATEGY_MODEL = "gpt-4.1"
VARIANT_MODEL = "gpt-4.1-mini"

# Map variant IDs to style guide filenames
VARIANT_STYLE_MAP = {
    "talking_points": "talking_points_style_guide.md",
    "media_talking_points": "media_talking_points_style_guide.md",
    "news_release": "press_releases_style_guide.md",
    "social_media": "social_media_style_guide.md",
    "grassroots_email": "grassroots_email_style_guide.md",
    "op_ed": "op_eds_style_guide.md",
    "speech_draft": "speeches_style_guide.md",
}

# Map variant IDs to their samples folder (under style_samples/)
VARIANT_SAMPLES_MAP = {
    "social_media": "social_media",
    "media_talking_points": "media_talking_points",
    "talking_points": "talking_points",
    "news_release": "press_releases",
    "op_ed": "op_eds",
    "grassroots_email": "emails",
    "speech_draft": "speeches",
}


# ---------------------------------------------------------------------------
# Message Matrix instructions/examples loading
# ---------------------------------------------------------------------------

def _load_variant_examples(variant_id: str, style_samples_root: str = "") -> str:
    """Load platform-specific example outputs for a given variant.

    Looks in style_samples/<folder>/my_samples/ for user-provided examples.
    Returns example text to inject into the variant prompt, or empty string.
    """
    if not style_samples_root:
        return ""

    folder = VARIANT_SAMPLES_MAP.get(variant_id)
    if not folder:
        return ""

    root = Path(style_samples_root).parent  # style_guides/ -> style_samples/
    samples_dir = root / folder / "my_samples"
    if not samples_dir.exists():
        return ""

    files = read_directory(str(samples_dir))
    if not files:
        return ""

    parts = [f"--- {f['name']} ---\n{f['text'][:4000]}" for f in files[:3]]
    return "\n\n".join(parts)


def _load_matrix_instructions(style_samples_root: str = "") -> tuple[str, str]:
    """Load user instructions and examples from message_matrix/ folder.

    Returns:
        (instructions_text, examples_text) — either or both may be empty.
    """
    if not style_samples_root:
        return "", ""

    root = Path(style_samples_root).parent  # style_guides -> style_samples
    mm_dir = root / "message_matrix"
    if not mm_dir.exists():
        return "", ""

    instructions = ""
    instr_files = read_directory(str(mm_dir / "instructions"))
    if instr_files:
        parts = [f"--- {f['name']} ---\n{f['text'][:5000]}" for f in instr_files]
        instructions = "\n\n".join(parts)

    examples = ""
    ex_files = read_directory(str(mm_dir / "examples"))
    if ex_files:
        parts = [f"--- {f['name']} ---\n{f['text'][:8000]}" for f in ex_files]
        examples = "\n\n".join(parts)

    return instructions, examples


# ---------------------------------------------------------------------------
# Step 1: Message House
# ---------------------------------------------------------------------------

MESSAGE_HOUSE_SYSTEM = """You are a senior public affairs strategist at a top-tier PA firm.
Your job is to build a Message Map — a strategic messaging grid that will be
used to generate all campaign deliverables (talking points, press releases, social posts, etc.).

A Message Map has:
- OVERARCHING MESSAGE: One clear, compelling sentence that ties everything together
- 3 KEY MESSAGES: Each a short, declarative statement covering a different argument dimension
- 3 SUPPORTING FACTS per key message: Specific, data-driven evidence for each key message
- KEY TERMS: Specific phrases to use consistently across all communications
- TARGET AUDIENCES: Who the messaging is designed to reach

Rules:
- Be SPECIFIC. Use concrete policy language, not vague platitudes.
- Supporting facts must come from the provided context when available. If no context is provided,
  use plausible facts but mark uncertain ones with [VERIFY].
- The overarching message should be quotable and memorable — one sentence max.
- Key messages should cover DIFFERENT argument dimensions (e.g., public health crisis, policy effectiveness, public opinion)
  rather than restating the same point three ways.
- Each supporting fact should be a specific number, statistic, case study, or concrete evidence.
- Key terms should be specific phrases to use consistently (e.g., "responsible AI" not just "AI").

Return ONLY a JSON object with this exact structure:
{
  "overarching_message": "One sentence umbrella statement",
  "key_messages": [
    {
      "title": "Short declarative statement (one sentence)",
      "supporting_facts": [
        "Specific fact or statistic with source",
        "Second specific fact or statistic with source",
        "Third specific fact or statistic with source"
      ]
    }
  ],
  "target_audiences": ["Audience 1", "Audience 2", "Audience 3"],
  "key_terms": ["term or phrase to use consistently", "another key term"]
}"""


def _build_message_house_prompt(position: str, context: str = "",
                                 target_audience: str = "",
                                 core_messages: str = "",
                                 facts: str = "",
                                 matrix_instructions: str = "") -> str:
    parts = [f"Build a Message Map for this policy position:\n\n{position}"]

    if core_messages:
        parts.append(
            f"\n\nThe user has provided these core messages. USE THEM as the overarching_message "
            f"and/or key messages — do not replace or override them:\n{core_messages}"
        )

    if facts:
        parts.append(
            f"\n\nThe user has provided these key facts and supporting facts. "
            f"USE THEM as supporting facts under the key messages:\n{facts}"
        )

    if context:
        parts.append(f"\n\nSupporting context (use this to ground proof points):\n{context}")
    if target_audience:
        parts.append(f"\n\nPrimary target audience: {target_audience}")

    if matrix_instructions:
        parts.append(
            f"\n\nADDITIONAL INSTRUCTIONS from the user — follow these closely:\n{matrix_instructions}"
        )

    return "\n".join(parts)


def generate_message_house(client: OpenAI, position: str, context: str = "",
                           target_audience: str = "",
                           core_messages: str = "",
                           facts: str = "",
                           matrix_instructions: str = "") -> dict:
    """Step 1: Generate the Message House via gpt-4.1."""
    prompt = _build_message_house_prompt(
        position, context, target_audience, core_messages, facts,
        matrix_instructions
    )

    response = client.chat.completions.create(
        model=STRATEGY_MODEL,
        messages=[
            {"role": "system", "content": MESSAGE_HOUSE_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content
    return json.loads(text)


# ---------------------------------------------------------------------------
# Style guide loading
# ---------------------------------------------------------------------------

def _load_style_guide(variant_id: str, style_guides_dir: str = "") -> str:
    """Load style guides for a variant: general guide + variant-specific guide.

    The general style guide is always loaded if it exists, providing baseline
    voice and tone rules. The variant-specific guide is layered on top.
    """
    if not style_guides_dir:
        return ""

    parts = []

    # Load general style guide (applies to all variants)
    general_path = Path(style_guides_dir) / "general_style_guide.md"
    if general_path.exists():
        parts.append(general_path.read_text(encoding="utf-8", errors="ignore").strip())

    # Load variant-specific style guide
    filename = VARIANT_STYLE_MAP.get(variant_id, "")
    if filename:
        guide_path = Path(style_guides_dir) / filename
        if guide_path.exists():
            parts.append(guide_path.read_text(encoding="utf-8", errors="ignore").strip())

    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Step 2: Platform Variants
# ---------------------------------------------------------------------------

def _format_message_house_text(house: dict) -> str:
    """Convert Message Map JSON to readable text for variant prompts."""
    lines = [f"OVERARCHING MESSAGE: {house.get('overarching_message', house.get('core_message', ''))}", ""]
    for i, km in enumerate(house.get("key_messages", house.get("pillars", [])), 1):
        title = km.get("title", km.get("name", ""))
        lines.append(f"KEY MESSAGE {i}: {title}")
        if km.get("argument"):
            lines.append(f"  {km['argument']}")
        for sf in km.get("supporting_facts", km.get("proof_points", [])):
            lines.append(f"  - {sf}")
        lines.append("")
    lines.append(f"KEY TERMS: {', '.join(house.get('key_terms', []))}")
    lines.append(f"TARGET AUDIENCES: {', '.join(house.get('target_audiences', []))}")
    return "\n".join(lines)


def generate_variant(client: OpenAI, variant_id: str, house: dict,
                     context: str = "", organization: str = "",
                     style_guide: str = "",
                     matrix_examples: str = "") -> str:
    """Step 2: Generate a single platform variant via gpt-4.1-mini."""
    template = VARIANT_PROMPTS[variant_id]
    house_text = _format_message_house_text(house)
    org = organization or "[ORGANIZATION]"

    context_section = ""
    if context:
        context_section = f"Additional context for reference:\n{context[:3000]}"

    # Inject style guide if available
    style_section = ""
    if style_guide:
        style_section = (
            "\n\nWRITING STYLE GUIDE — Follow this style closely:\n"
            f"{style_guide}\n"
        )

    # Inject matrix examples if available
    examples_section = ""
    if matrix_examples:
        examples_section = (
            "\n\nEXAMPLE OUTPUTS — Use these as reference for format and quality:\n"
            f"{matrix_examples}\n"
        )

    prompt = template.format(
        message_house=house_text,
        context_section=context_section,
        org_name=org,
    )

    # Append style guide and examples after the formatted prompt
    if style_section:
        prompt += style_section
    if examples_section:
        prompt += examples_section

    response = client.chat.completions.create(
        model=VARIANT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=2000,
    )

    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def generate_matrix(position: str, context: str = "", organization: str = "",
                    target_audience: str = "",
                    core_messages: str = "", facts: str = "",
                    variants: list[str] = None,
                    style_guides_dir: str = "") -> dict:
    """
    Run the full messaging matrix pipeline.

    Returns:
        {
            "message_house": { ... },
            "variants": { "talking_points": "...", "news_release": "...", ... }
        }
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required.")

    client = OpenAI(api_key=api_key)
    variants = variants or VARIANT_IDS

    # Load matrix instructions and examples if available
    matrix_instructions, matrix_examples = _load_matrix_instructions(style_guides_dir)
    if matrix_instructions:
        print("  Loaded matrix instructions", file=sys.stderr)
    if matrix_examples:
        print("  Loaded matrix examples", file=sys.stderr)

    # Step 1: Message House
    print("Step 1: Generating Message House...", file=sys.stderr)
    house = generate_message_house(
        client, position, context, target_audience, core_messages, facts,
        matrix_instructions
    )
    print(f"  Core message: {house.get('core_message', 'N/A')}", file=sys.stderr)

    # Step 2: Variants
    generated = {}
    for vid in variants:
        if vid not in VARIANT_PROMPTS:
            print(f"  Skipping unknown variant: {vid}", file=sys.stderr)
            continue
        label = VARIANT_LABELS.get(vid, vid)
        print(f"Step 2: Generating {label}...", file=sys.stderr)

        # Load style guide for this variant type
        style_guide = _load_style_guide(vid, style_guides_dir)
        if style_guide:
            print(f"  Using style guide for {label}", file=sys.stderr)

        # Load platform-specific examples (takes priority over generic matrix examples)
        variant_examples = _load_variant_examples(vid, style_guides_dir)
        examples_to_use = variant_examples or matrix_examples
        if variant_examples:
            print(f"  Using {label} examples", file=sys.stderr)

        generated[vid] = generate_variant(
            client, vid, house, context, organization, style_guide,
            examples_to_use
        )

    return {"message_house": house, "variants": generated}


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def render_markdown(result: dict) -> str:
    """Render the full messaging matrix as a markdown document."""
    house = result["message_house"]
    sections = []

    # Message Map section
    sections.append("# Messaging Matrix\n")
    sections.append("## Message Map\n")

    overarching = house.get("overarching_message", house.get("core_message", ""))
    key_messages = house.get("key_messages", house.get("pillars", []))

    if house.get("target_audiences"):
        sections.append(f"**Target Audiences:** {', '.join(house['target_audiences'])}\n")

    sections.append(f"**Overarching Message:** {overarching}\n")

    # Build message map table
    if key_messages:
        # Header row
        headers = [""]
        for i, km in enumerate(key_messages, 1):
            headers.append(f"**Key Message {i}**")
        sections.append("| " + " | ".join(headers) + " |")
        sections.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Key message titles row
        titles = ["**Key Message**"]
        for km in key_messages:
            title = km.get("title", km.get("name", ""))
            titles.append(title)
        sections.append("| " + " | ".join(titles) + " |")

        # Supporting facts rows
        max_facts = max(len(km.get("supporting_facts", km.get("proof_points", []))) for km in key_messages)
        for fi in range(max_facts):
            row = [f"**Supporting Fact {fi + 1}**"]
            for km in key_messages:
                facts = km.get("supporting_facts", km.get("proof_points", []))
                row.append(facts[fi] if fi < len(facts) else "")
            sections.append("| " + " | ".join(row) + " |")

        sections.append("")

    if house.get("key_terms"):
        sections.append(f"**Key Terms:** {', '.join(house['key_terms'])}\n")

    sections.append("---\n")

    # Variant sections
    for vid, content in result.get("variants", {}).items():
        label = VARIANT_LABELS.get(vid, vid)
        sections.append(f"## {label}\n")
        sections.append(content)
        sections.append("\n---\n")

    return "\n".join(sections)
