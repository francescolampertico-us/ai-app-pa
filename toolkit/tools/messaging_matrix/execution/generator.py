"""
Messaging Matrix Generator
============================
Three-step LLM pipeline:
  Step 1 — Message House: builds the strategic foundation + per-channel angles
  Step 0 — Fact Verification: classifies every supporting fact before copy is drafted
  Step 2 — Platform Variants: generates each deliverable from its channel-specific angle

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

from formats import VARIANT_IDS, VARIANT_LABELS, VARIANT_PROMPTS, VARIANT_STYLE_MAP, VARIANT_SAMPLES_MAP
from context_reader import read_directory


STRATEGY_MODEL = "ChangeAgent"
VARIANT_MODEL = "ChangeAgent"

def _active_model(default: str) -> str:
    return os.environ.get("LLM_MODEL_OVERRIDE") or default

def _response_format_kwarg() -> dict:
    if os.environ.get("LLM_MODEL_OVERRIDE"):
        return {}
    return {"response_format": {"type": "json_object"}}

def _max_tokens_kwarg(default: int) -> dict:
    if os.environ.get("LLM_MODEL_OVERRIDE"):
        return {}
    return {"max_tokens": default}

def _parse_json_content(content: "str | None") -> dict:
    import re
    if not content:
        return {}
    text = content.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    last = text.rfind("}")
    if last != -1:
        try:
            return json.loads(text[: last + 1])
        except json.JSONDecodeError:
            pass
    return {}


# ---------------------------------------------------------------------------
# Style guide + example loading (unchanged)
# ---------------------------------------------------------------------------

def _load_variant_examples(variant_id: str, style_samples_root: str = "") -> str:
    if not style_samples_root:
        return ""
    folder = VARIANT_SAMPLES_MAP.get(variant_id)
    if not folder:
        return ""
    root = Path(style_samples_root).parent
    samples_dir = root / folder / "my_samples"
    if not samples_dir.exists():
        return ""
    files = read_directory(str(samples_dir))
    if not files:
        return ""
    parts = [f"--- {f['name']} ---\n{f['text'][:4000]}" for f in files[:3]]
    return "\n\n".join(parts)


def _load_matrix_instructions(style_samples_root: str = "") -> tuple[str, str]:
    if not style_samples_root:
        return "", ""
    root = Path(style_samples_root).parent
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


def _load_style_guide(variant_id: str, style_guides_dir: str = "") -> str:
    if not style_guides_dir:
        return ""
    parts = []
    general_path = Path(style_guides_dir) / "general_style_guide.md"
    if general_path.exists():
        parts.append(general_path.read_text(encoding="utf-8", errors="ignore").strip())
    filename = VARIANT_STYLE_MAP.get(variant_id, "")
    if filename:
        guide_path = Path(style_guides_dir) / filename
        if guide_path.exists():
            parts.append(guide_path.read_text(encoding="utf-8", errors="ignore").strip())
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Step 1: Message House (with channel_angles)
# ---------------------------------------------------------------------------

MESSAGE_HOUSE_SYSTEM = """You are a senior public affairs strategist at a top-tier PA firm.
Your job is to build a Message Map — a strategic messaging architecture that will drive all campaign deliverables.

A Message Map has:
- OVERARCHING MESSAGE: One clear, compelling sentence that ties everything together
- 3 KEY MESSAGES: Each a short, declarative statement covering a DIFFERENT argument dimension (not three ways of saying the same thing)
- 3 SUPPORTING FACTS per key message: Specific, data-driven evidence. If context provides it, use it. If not, use plausible common knowledge and mark uncertain claims with [VERIFY].
- KEY TERMS: Specific phrases to use consistently across all communications
- TARGET AUDIENCES: Who the messaging is designed to reach
- CHANNEL ANGLES: Per-deliverable emphasis so each output has a distinct entry point and purpose

Rules:
- Key messages must cover genuinely DIFFERENT argument dimensions (e.g., legislative gap vs. public health impact vs. economic cost)
- Supporting facts must use concrete numbers, not vague gestures
- Channel angles must give each deliverable a UNIQUE lead — different from the others

Return ONLY a JSON object with this exact structure:
{
  "overarching_message": "One sentence umbrella statement",
  "key_messages": [
    {
      "title": "Short declarative statement (one sentence)",
      "supporting_facts": [
        "Specific fact or statistic with source or [VERIFY]",
        "Second specific fact or statistic",
        "Third specific fact or statistic"
      ]
    }
  ],
  "target_audiences": ["Audience 1", "Audience 2", "Audience 3"],
  "key_terms": ["term or phrase to use consistently", "another key term"],
  "channel_angles": {
    "talking_points": "Which key message to lead with for Hill staff. What specific legislative mechanism or jurisdictional hook to open with. What the concrete ask is (bill, markup, vote, hearing).",
    "media_talking_points": "The most newsworthy or conflict-driven angle. The best soundbite sentence. The tough question to anticipate.",
    "news_release": "The news hook — what specifically happened or was released today that makes this a story. Lead with this, not the organization.",
    "social_media": "The most shareable or counterintuitive fact. The personal stakes frame for a general audience.",
    "grassroots_email": "How this affects the reader personally. The specific ask — what one action to take and why now.",
    "op_ed": "The intellectual hook or reframing argument. The contrarian or surprising angle that earns placement. The one-arc thesis.",
    "speech_draft": "The emotional and rhetorical core. The through-line image or phrase. The opening hook that sets the tone."
  }
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
            f"\n\nThe user has provided these key facts. USE THEM as supporting facts:\n{facts}"
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
    """Step 1: Generate the Message House including channel_angles."""
    prompt = _build_message_house_prompt(
        position, context, target_audience, core_messages, facts, matrix_instructions
    )
    response = client.chat.completions.create(
        model=_active_model(STRATEGY_MODEL),
        messages=[
            {"role": "system", "content": MESSAGE_HOUSE_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        **_max_tokens_kwarg(2500),
        **_response_format_kwarg(),
    )
    return _parse_json_content(response.choices[0].message.content)


# ---------------------------------------------------------------------------
# Step 0: Fact Verification
# ---------------------------------------------------------------------------

FACT_VERIFICATION_SYSTEM = """You are a fact-checking editor reviewing claims before they appear in published public affairs materials.

For each claim, classify it as one of:
- CONFIDENT: Well-established, commonly cited, attributable to a recognizable source with high confidence. Include verbatim.
- QUALIFIED: Plausible but source is uncertain or the number is approximate. Include with hedging language (e.g., "According to estimates," "Approximately").
- UNVERIFIED: Cannot be confidently attributed to a real source; risks being demonstrably false or is clearly invented. Exclude from deliverables.

Critical rules:
- Do not invent sources. If you cannot name or strongly infer a real source, classify as UNVERIFIED.
- [VERIFY] tags in the input = claims that need classification — do not pass them through as-is.
- Err toward QUALIFIED over UNVERIFIED when a claim is broadly plausible but the specific number is uncertain.

Return ONLY this JSON structure:
{
  "verified": [
    {"claim": "exact claim text", "source_note": "[Organization or Source, Year]"}
  ],
  "qualified": [
    {"claim": "exact claim text", "qualifier": "According to [source type], approximately..."}
  ],
  "unverified": [
    {"claim": "exact claim text", "reason": "brief reason for exclusion"}
  ]
}"""


def verify_facts(client: OpenAI, house: dict, context: str = "") -> dict:
    """
    Step 0: Classify every supporting fact in the message house before generating deliverables.
    Returns {"verified": [...], "qualified": [...], "unverified": [...]}.
    """
    all_facts = []
    for km in house.get("key_messages", house.get("pillars", [])):
        for fact in km.get("supporting_facts", km.get("proof_points", [])):
            all_facts.append(fact)

    if not all_facts:
        return {"verified": [], "qualified": [], "unverified": []}

    claims_text = "\n".join(f"- {fact}" for fact in all_facts)
    context_note = f"\n\nContext (use to assess plausibility):\n{context[:2000]}" if context else ""
    prompt = f"Review each claim for inclusion in public affairs communications materials:\n\n{claims_text}{context_note}"

    try:
        response = client.chat.completions.create(
            model=_active_model(STRATEGY_MODEL),
            messages=[
                {"role": "system", "content": FACT_VERIFICATION_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            **_max_tokens_kwarg(1500),
            **_response_format_kwarg(),
        )
        result = _parse_json_content(response.choices[0].message.content)
        # Ensure all keys present
        result.setdefault("verified", [])
        result.setdefault("qualified", [])
        result.setdefault("unverified", [])
        return result
    except Exception as e:
        print(f"  Fact verification failed ({e}); treating all facts as qualified.", file=sys.stderr)
        return {
            "verified": [],
            "qualified": [{"claim": f, "qualifier": ""} for f in all_facts],
            "unverified": [],
        }


# ---------------------------------------------------------------------------
# Fact formatting helpers
# ---------------------------------------------------------------------------

def _format_verified_facts_text(fact_check: dict) -> str:
    """Format verified + qualified facts for injection into variant prompts."""
    lines = []
    for item in fact_check.get("verified", []):
        if isinstance(item, dict):
            claim = item.get("claim", "")
            source = item.get("source_note", "")
            lines.append(f"- {claim} {source}".strip())
        else:
            lines.append(f"- {item}")

    for item in fact_check.get("qualified", []):
        if isinstance(item, dict):
            claim = item.get("claim", "")
            qualifier = item.get("qualifier", "")
            if qualifier:
                lines.append(f"- {qualifier}")
            elif claim:
                lines.append(f"- {claim} [use with appropriate hedging]")
        else:
            lines.append(f"- {item} [use with appropriate hedging]")

    if not lines:
        return "(No pre-verified facts available — draw only from the context provided above.)"
    return "\n".join(lines)


def _format_unverified_note(fact_check: dict) -> str:
    """Format a note listing claims to exclude, for transparency in the prompt."""
    unverified = fact_check.get("unverified", [])
    if not unverified:
        return ""
    lines = ["EXCLUDED CLAIMS — do not use these in the deliverable (needs verification):"]
    for item in unverified:
        if isinstance(item, dict):
            claim = item.get("claim", "")
            reason = item.get("reason", "")
            lines.append(f"- {claim}" + (f" ({reason})" if reason else ""))
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Step 2: Platform Variants
# ---------------------------------------------------------------------------

def _format_message_house_text(house: dict) -> str:
    """Fallback: convert Message Map JSON to readable text (used if channel_angle not available)."""
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
                     matrix_examples: str = "",
                     fact_check: dict = None,
                     target_audience: str = "",
                     position: str = "") -> str:
    """Step 2: Generate a single platform variant."""
    template = VARIANT_PROMPTS[variant_id]
    org = organization or "[ORGANIZATION]"
    fact_check = fact_check or {}

    # Channel angle from message house (per-deliverable emphasis)
    channel_angles = house.get("channel_angles", {})
    channel_angle = channel_angles.get(variant_id, "")
    # Fallback: use full message map text if no channel angle
    if not channel_angle:
        channel_angle = _format_message_house_text(house)

    overarching_message = house.get("overarching_message", house.get("core_message", ""))
    key_terms = ", ".join(house.get("key_terms", []))
    audience = target_audience or ", ".join(house.get("target_audiences", []))

    verified_facts_text = _format_verified_facts_text(fact_check)
    unverified_note = _format_unverified_note(fact_check)

    context_section = f"Additional context:\n{context[:3000]}" if context else ""

    if isinstance(template, dict):
        # New format: separate system + user messages
        system_msg = template["system"]
        user_msg = template["user"].format(
            position=position or overarching_message,
            audience=audience,
            channel_angle=channel_angle,
            overarching_message=overarching_message,
            key_terms=key_terms,
            verified_facts_text=verified_facts_text,
            unverified_note=unverified_note,
            context_section=context_section,
            org_name=org,
        )
        # Append style guide and examples to user message
        if style_guide:
            user_msg += f"\n\nWRITING STYLE GUIDE — Follow this style closely:\n{style_guide}\n"
        if matrix_examples:
            user_msg += f"\n\nEXAMPLE OUTPUTS — Use as reference for format and quality:\n{matrix_examples}\n"
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
    else:
        # Legacy string format (backward compat)
        house_text = _format_message_house_text(house)
        prompt = template.format(
            message_house=house_text,
            context_section=context_section,
            org_name=org,
        )
        if style_guide:
            prompt += f"\n\nWRITING STYLE GUIDE — Follow this style closely:\n{style_guide}\n"
        if matrix_examples:
            prompt += f"\n\nEXAMPLE OUTPUTS — Use as reference:\n{matrix_examples}\n"
        messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model=_active_model(VARIANT_MODEL),
        messages=messages,
        temperature=0.4,
        **_max_tokens_kwarg(2500),
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
            "variants": { "talking_points": "...", "news_release": "...", ... },
            "fact_check": { "verified": [...], "qualified": [...], "unverified": [...] }
        }
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required. Check that toolkit/.env is set and loaded.")

    client = OpenAI(api_key=api_key, timeout=120)
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
    print(f"  Overarching: {house.get('overarching_message', 'N/A')[:80]}", file=sys.stderr)

    # Step 0: Fact Verification
    print("Step 0: Verifying supporting facts...", file=sys.stderr)
    fact_check = verify_facts(client, house, context)
    n_verified = len(fact_check.get("verified", []))
    n_qualified = len(fact_check.get("qualified", []))
    n_unverified = len(fact_check.get("unverified", []))
    print(f"  Facts — verified: {n_verified}, qualified: {n_qualified}, excluded: {n_unverified}", file=sys.stderr)
    if n_unverified > 0:
        print(f"  Excluded claims will NOT appear in deliverables.", file=sys.stderr)

    # Step 2: Variants
    generated = {}
    for vid in variants:
        if vid not in VARIANT_PROMPTS:
            print(f"  Skipping unknown variant: {vid}", file=sys.stderr)
            continue
        label = VARIANT_LABELS.get(vid, vid)
        print(f"Step 2: Generating {label}...", file=sys.stderr)

        style_guide = _load_style_guide(vid, style_guides_dir)
        if style_guide:
            print(f"  Using style guide for {label}", file=sys.stderr)

        variant_examples = _load_variant_examples(vid, style_guides_dir)
        examples_to_use = variant_examples or matrix_examples
        if variant_examples:
            print(f"  Using {label} examples", file=sys.stderr)

        generated[vid] = generate_variant(
            client, vid, house, context, organization,
            style_guide, examples_to_use,
            fact_check=fact_check,
            target_audience=target_audience,
            position=position,
        )

    return {
        "message_house": house,
        "variants": generated,
        "fact_check": fact_check,
    }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def render_markdown(result: dict) -> str:
    """Render the full messaging matrix as a markdown document."""
    house = result["message_house"]
    fact_check = result.get("fact_check", {})
    sections = []

    sections.append("# Messaging Matrix\n")
    sections.append("## Message Map\n")

    overarching = house.get("overarching_message", house.get("core_message", ""))
    key_messages = house.get("key_messages", house.get("pillars", []))

    if house.get("target_audiences"):
        sections.append(f"**Target Audiences:** {', '.join(house['target_audiences'])}\n")

    sections.append(f"**Overarching Message:** {overarching}\n")

    if key_messages:
        headers = [""]
        for i, km in enumerate(key_messages, 1):
            headers.append(f"**Key Message {i}**")
        sections.append("| " + " | ".join(headers) + " |")
        sections.append("| " + " | ".join(["---"] * len(headers)) + " |")

        titles = ["**Key Message**"]
        for km in key_messages:
            title = km.get("title", km.get("name", ""))
            titles.append(title)
        sections.append("| " + " | ".join(titles) + " |")

        max_facts = max(len(km.get("supporting_facts", km.get("proof_points", []))) for km in key_messages)
        for fi in range(max_facts):
            row = [f"**Supporting Fact {fi + 1}**"]
            for km in key_messages:
                facts_list = km.get("supporting_facts", km.get("proof_points", []))
                row.append(facts_list[fi] if fi < len(facts_list) else "")
            sections.append("| " + " | ".join(row) + " |")

        sections.append("")

    if house.get("key_terms"):
        sections.append(f"**Key Terms:** {', '.join(house['key_terms'])}\n")

    # Fact check summary
    unverified = fact_check.get("unverified", [])
    if unverified:
        sections.append("---\n")
        sections.append("## Unverified Claims — Needs Confirmation Before Use\n")
        sections.append(
            "_The following claims were excluded from all deliverables. "
            "Verify with a primary source before adding to any final copy._\n"
        )
        for item in unverified:
            if isinstance(item, dict):
                claim = item.get("claim", "")
                reason = item.get("reason", "")
                sections.append(f"- **{claim}**" + (f" — {reason}" if reason else ""))
            else:
                sections.append(f"- {item}")
        sections.append("")

    sections.append("---\n")

    for vid, content in result.get("variants", {}).items():
        label = VARIANT_LABELS.get(vid, vid)
        sections.append(f"## {label}\n")
        sections.append(content)
        sections.append("\n---\n")

    return "\n".join(sections)
