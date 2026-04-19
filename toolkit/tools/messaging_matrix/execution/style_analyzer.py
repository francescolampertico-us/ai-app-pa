"""
Style Analyzer
===============
One-time analysis of writing samples to generate personalized style guides.
Reads from style_samples/<type>/my_samples/ and style_samples/<type>/references/,
produces a combined style guide saved to style_samples/style_guides/.
"""

import os
import sys
from pathlib import Path
from openai import OpenAI

from context_reader import read_directory


MODEL = "ChangeAgent"

# Document types and their folder names
DOC_TYPES = {
    "social_media": "Social Media Posts",
    "press_releases": "Press Releases / News Releases",
    "talking_points": "Talking Points",
    "op_eds": "Op-Eds / Opinion Pieces",
    "speeches": "Speeches",
    "media_talking_points": "Media Talking Points",
}


ANALYZE_PROMPT = """You are a professional writing style analyst. Your job is to analyze
writing samples and produce a detailed, actionable style guide that an AI writer can follow
to reproduce this style.

{samples_section}

Produce a DETAILED STYLE GUIDE covering:

1. **Voice & Tone** — Formal vs. conversational, authoritative vs. approachable, active vs. passive voice preferences
2. **Sentence Structure** — Average sentence length, simple vs. complex structures, use of fragments, cadence patterns
3. **Paragraph Structure** — Length preferences, topic sentence patterns, transition styles
4. **Vocabulary** — Register level (plain vs. technical), favored phrases or constructions, jargon usage
5. **Opening Patterns** — How documents typically begin (hook types, lead styles)
6. **Closing Patterns** — How documents typically end (CTA styles, summary approaches, memorable endings)
7. **Use of Evidence** — How data, stats, quotes, and examples are integrated
8. **Rhetorical Devices** — Repetition, triads, questions, metaphors, analogies
9. **Formatting Conventions** — Headers, bullets, bold text, numbering patterns
10. **Distinctive Characteristics** — Anything unique about this writing voice that should be preserved

Be SPECIFIC and ACTIONABLE. Instead of "uses professional language," say "favors short,
declarative sentences (8-15 words) with active verbs; avoids hedging phrases like
'it could be argued that.'"

Include direct examples from the samples where possible.

Document type: {doc_type}
"""


def _build_samples_section(my_samples: list[dict], references: list[dict]) -> str:
    """Build the samples section of the prompt."""
    parts = []

    if my_samples:
        parts.append("## AUTHOR'S OWN WRITING SAMPLES")
        parts.append("(Learn the author's personal voice, tone, and style from these)\n")
        for i, s in enumerate(my_samples, 1):
            text = s["text"][:5000]  # Cap per sample to manage tokens
            parts.append(f"### Sample {i}: {s['name']}\n{text}\n")

    if references:
        parts.append("\n## REFERENCE MATERIALS & BEST PRACTICES")
        parts.append("(Learn professional standards and quality markers from these)\n")
        for i, r in enumerate(references, 1):
            text = r["text"][:5000]
            parts.append(f"### Reference {i}: {r['name']}\n{text}\n")

    return "\n".join(parts)


def analyze_type(doc_type: str, samples_dir: str, output_dir: str,
                 client: OpenAI = None) -> str:
    """Analyze samples for a single document type and generate a style guide.

    Args:
        doc_type: Key from DOC_TYPES (e.g., "press_releases")
        samples_dir: Path to style_samples/<doc_type>/
        output_dir: Path to style_samples/style_guides/
        client: OpenAI client (created if not provided)

    Returns:
        The generated style guide text, or empty string if no samples found.
    """
    samples_path = Path(samples_dir)
    my_samples = read_directory(str(samples_path / "my_samples"))
    references = read_directory(str(samples_path / "references"))

    if not my_samples and not references:
        return ""

    if client is None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required.")
        client = OpenAI(api_key=api_key)

    doc_label = DOC_TYPES.get(doc_type, doc_type)
    samples_section = _build_samples_section(my_samples, references)

    prompt = ANALYZE_PROMPT.format(
        samples_section=samples_section,
        doc_type=doc_label,
    )

    print(f"  Analyzing {doc_label} ({len(my_samples)} samples, {len(references)} references)...",
          file=sys.stderr)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=3000,
    )

    guide_text = response.choices[0].message.content

    # Save to output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    guide_file = out_path / f"{doc_type}_style_guide.md"
    guide_file.write_text(guide_text, encoding="utf-8")
    print(f"  Saved: {guide_file}", file=sys.stderr)

    return guide_text


def analyze_all(style_samples_root: str) -> dict[str, str]:
    """Analyze all document types that have samples.

    Args:
        style_samples_root: Path to style_samples/ directory

    Returns:
        Dict of doc_type → style guide text for types that had samples.
    """
    root = Path(style_samples_root)
    output_dir = str(root / "style_guides")

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required.")
    client = OpenAI(api_key=api_key)

    results = {}
    for doc_type in DOC_TYPES:
        type_dir = root / doc_type
        if type_dir.exists():
            guide = analyze_type(doc_type, str(type_dir), output_dir, client)
            if guide:
                results[doc_type] = guide

    return results


def get_style_status(style_samples_root: str) -> dict[str, dict]:
    """Check which document types have samples and/or style guides.

    Returns dict of doc_type → {
        "label": str,
        "has_samples": bool,
        "has_references": bool,
        "has_guide": bool,
        "sample_count": int,
        "reference_count": int,
    }
    """
    root = Path(style_samples_root)
    status = {}

    for doc_type, label in DOC_TYPES.items():
        type_dir = root / doc_type
        my_dir = type_dir / "my_samples"
        ref_dir = type_dir / "references"
        guide_file = root / "style_guides" / f"{doc_type}_style_guide.md"

        sample_count = len(list(my_dir.glob("*"))) if my_dir.exists() else 0
        ref_count = len(list(ref_dir.glob("*"))) if ref_dir.exists() else 0

        status[doc_type] = {
            "label": label,
            "has_samples": sample_count > 0,
            "has_references": ref_count > 0,
            "has_guide": guide_file.exists(),
            "sample_count": sample_count,
            "reference_count": ref_count,
        }

    return status


if __name__ == "__main__":
    # CLI usage: python3 style_analyzer.py [path_to_style_samples]
    import argparse
    parser = argparse.ArgumentParser(description="Analyze writing samples and generate style guides.")
    parser.add_argument("--samples-dir", default=None,
                        help="Path to style_samples/ directory")
    args = parser.parse_args()

    samples_dir = args.samples_dir
    if not samples_dir:
        # Default: relative to this script
        samples_dir = str(Path(__file__).resolve().parent.parent / "style_samples")

    print(f"Analyzing samples in: {samples_dir}", file=sys.stderr)
    results = analyze_all(samples_dir)
    if results:
        print(f"\nGenerated style guides for: {', '.join(results.keys())}", file=sys.stderr)
    else:
        print("\nNo samples found. Add files to style_samples/<type>/my_samples/ or references/",
              file=sys.stderr)
