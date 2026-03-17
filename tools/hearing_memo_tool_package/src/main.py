"""
main.py — CLI orchestrator for the Congressional Hearing Memo Tool.

Runs the 4-stage pipeline:
  normalize → extract → compose → verify
Then exports to DOCX.

Usage:
    python -m src.main --input transcripts/file.pdf --from "Mercury" \
        --memo-date "Thursday, March 12, 2026" --output output/memo.docx
"""

import argparse
import json
import os
import sys

# Add parent directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.normalizer import normalize
from src.extractor import extract
from src.composer import compose, render_memo_text
from src.verifier import verify
from src.exporter import export_docx
from src.config import REPO_ROOT


def main():
    parser = argparse.ArgumentParser(
        description="Congressional Hearing Memo Generator V1.0.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --input transcripts/Senate_Aging.pdf --output output/memo.docx
  python -m src.main --input transcript.txt --from "Mercury" --memo-date "March 12, 2026"
        """,
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to hearing transcript (PDF or text file)",
    )
    parser.add_argument(
        "--output", "-o",
        default="output/memo.docx",
        help="Output DOCX file path (default: output/memo.docx)",
    )
    parser.add_argument(
        "--from", dest="memo_from",
        default="Mercury",
        help="FROM field value (default: Mercury)",
    )
    parser.add_argument(
        "--memo-date",
        default=None,
        help="Memo date (e.g., 'Thursday, March 12, 2026'). Defaults to today.",
    )
    parser.add_argument(
        "--subject",
        default=None,
        help="Override SUBJECT line",
    )
    parser.add_argument(
        "--confidentiality-footer",
        default=None,
        help="Override default confidentiality footer text",
    )
    parser.add_argument(
        "--hearing-title",
        default=None,
        help="Override hearing title if auto-detection fails",
    )
    parser.add_argument(
        "--hearing-date",
        default=None,
        help="Override hearing date if auto-detection fails",
    )
    parser.add_argument(
        "--hearing-time",
        default=None,
        help="Override hearing time",
    )
    parser.add_argument(
        "--committee",
        default=None,
        help="Override committee name",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Path to write structured JSON outputs (hearing record + verification)",
    )
    parser.add_argument(
        "--text-output",
        default=None,
        help="Path to write rendered memo text (markdown format)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed pipeline progress",
    )

    args = parser.parse_args()

    # Resolve paths
    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)

    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("=" * 60)
    print("  Congressional Hearing Memo Generator V1.0.0")
    print("=" * 60)
    print()

    # ===== Stage 1: Normalize =====
    print("[1/4] Normalizing source text...")
    norm_result = normalize(input_path)

    if args.verbose:
        print(f"  Source profile: {norm_result.source_profile}")
        print(f"  Cleaned text: {len(norm_result.cleaned_text)} chars")
        print(f"  Cleanup notes:")
        for note in norm_result.cleanup_notes:
            print(f"    - {note}")
        print(f"  Metadata candidates:")
        for k, v in norm_result.metadata_candidates.items():
            val_str = str(v)[:80]
            print(f"    {k}: {val_str}")
    else:
        print(f"  ✓ {len(norm_result.cleaned_text)} chars cleaned, profile: {norm_result.source_profile}")

    # Apply overrides to metadata candidates
    if args.hearing_title:
        norm_result.metadata_candidates["hearing_title"] = args.hearing_title
    if args.hearing_date:
        norm_result.metadata_candidates["hearing_date_long"] = args.hearing_date
    if args.hearing_time:
        norm_result.metadata_candidates["hearing_time"] = args.hearing_time
    if args.committee:
        norm_result.metadata_candidates["committee_name"] = args.committee

    # ===== Stage 2: Extract =====
    print("[2/4] Extracting structured hearing record...")
    hearing_record = extract(
        norm_result.cleaned_text,
        norm_result.metadata_candidates,
        norm_result.source_profile,
    )
    record_dict = hearing_record.to_dict()

    if args.verbose:
        print(f"  Leadership speakers: {len(hearing_record.opening_statements)}")
        print(f"  Witnesses: {len(hearing_record.witnesses)}")
        print(f"  Q&A members: {len(hearing_record.qa_clusters)}")
        print(f"  Uncertainties: {len(hearing_record.uncertainties)}")
        for u in hearing_record.uncertainties:
            print(f"    ⚠ {u}")
    else:
        print(f"  ✓ {len(hearing_record.opening_statements)} openers, "
              f"{len(hearing_record.witnesses)} witnesses, "
              f"{len(hearing_record.qa_clusters)} Q&A members")

    # ===== Stage 3: Compose =====
    print("[3/4] Composing Mercury-style memo...")
    memo_output = compose(
        record_dict,
        memo_from=args.memo_from,
        memo_date=args.memo_date,
        subject_line=args.subject,
        confidentiality_footer=args.confidentiality_footer,
    )

    # Render text version
    memo_text = render_memo_text(memo_output)

    section_count = len(memo_output["sections"])
    total_subsections = sum(len(s.get("subsections", [])) for s in memo_output["sections"])
    print(f"  ✓ {section_count} sections, {total_subsections} subsections composed")

    # ===== Stage 4: Verify =====
    print("[4/4] Running verification pass...")
    verification = verify(memo_output, record_dict)

    verdict = verification["verdict"]
    flags = verification["flags"]
    human_checks = verification["human_checks"]

    verdict_icon = "✓" if verdict == "pass" else "⚠"
    print(f"  {verdict_icon} Verdict: {verdict.upper()}")
    if flags:
        print(f"  Flags ({len(flags)}):")
        for flag in flags:
            print(f"    ⚠ {flag}")
    if human_checks:
        print(f"  Human checks ({len(human_checks)}):")
        for check in human_checks:
            print(f"    → {check}")

    # Update memo output with verification
    memo_output["verification_flags"] = flags

    # ===== Export =====
    print()
    print("Exporting...")

    # DOCX export
    export_docx(memo_output, output_path)
    print(f"  ✓ DOCX: {output_path}")

    # Text export (optional)
    if args.text_output:
        text_path = os.path.abspath(args.text_output)
        os.makedirs(os.path.dirname(text_path), exist_ok=True)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(memo_text)
        print(f"  ✓ Text: {text_path}")

    # JSON export (optional)
    if args.json_output:
        json_path = os.path.abspath(args.json_output)
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        output_data = {
            "hearing_record": record_dict,
            "memo_output": memo_output,
            "verification": verification,
            "normalization_notes": norm_result.cleanup_notes,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ JSON: {json_path}")

    # Always write a text version next to DOCX
    text_sibling = output_path.rsplit(".", 1)[0] + ".txt"
    with open(text_sibling, "w", encoding="utf-8") as f:
        f.write(memo_text)
    print(f"  ✓ Text: {text_sibling}")

    # Always write verification JSON next to DOCX
    verify_sibling = output_path.rsplit(".", 1)[0] + "_verification.json"
    with open(verify_sibling, "w", encoding="utf-8") as f:
        json.dump(verification, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Verification: {verify_sibling}")

    print()
    print("=" * 60)
    print(f"  Done. Verdict: {verdict.upper()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
