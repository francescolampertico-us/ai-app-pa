#!/usr/bin/env python3
"""
Brand demo — generates a sample branded document showing all components.

Run from anywhere:
    python3 toolkit/tools/shared/brand/demo.py
    python3 toolkit/tools/shared/brand/demo.py --out /path/to/output.docx
"""
import sys
import argparse
from pathlib import Path
from datetime import date

# Allow running from any directory
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))          # brand/
    sys.path.insert(0, str(_HERE.parent))   # shared/

from docx_brand import (
    new_branded_doc, apply_cover, section_heading,
    body_para, bullet_item, callout, meta_table, data_table, add_footer,
)


def build_demo(out_path: str) -> None:
    doc = new_branded_doc()

    # ── Cover ──────────────────────────────────────────────────────────────
    apply_cover(
        doc,
        title="Hearing Memo",
        subtitle="Senate Foreign Relations Committee — AI and National Security",
        date_str=date.today().strftime("%B %d, %Y"),
    )

    # ── Metadata block ─────────────────────────────────────────────────────
    section_heading(doc, "Document Details", level=3)
    meta_table(doc, [
        ("Committee",     "Senate Foreign Relations Committee"),
        ("Hearing Date",  "April 10, 2026"),
        ("Prepared By",   "PA AI Toolkit — Background Memo"),
        ("Classification", "Confidential — Internal Use Only"),
        ("Risk Level",    "Yellow — Review before external distribution"),
    ])

    # ── Executive Summary ──────────────────────────────────────────────────
    section_heading(doc, "Executive Summary", level=1)
    body_para(doc,
        "The Senate Foreign Relations Committee will hold a hearing on April 10 examining "
        "the implications of AI systems in national security contexts, with particular focus "
        "on autonomous decision-making, allied coordination, and oversight frameworks. "
        "Three administration officials are expected to testify.")

    callout(doc,
        "Key watch item: Senator Chen is expected to press witnesses on the gap between "
        "DoD's stated AI ethics principles and procurement decisions made in fiscal 2025.",
        kind="info")

    # ── Witnesses ──────────────────────────────────────────────────────────
    section_heading(doc, "Witnesses", level=1)
    body_para(doc, "The following witnesses are scheduled to appear:", size_pt=10)

    data_table(doc,
        headers=["Name", "Title", "Agency", "Prior Testimony"],
        rows=[
            ["Dr. Sarah Okonkwo", "Deputy Secretary", "Department of Defense", "3 appearances"],
            ["James Whitfield",   "Director",         "National Security Agency", "1 appearance"],
            ["Amara Singh",       "Senior Advisor",   "NSC",                     "None on record"],
        ]
    )

    # ── Key Issues ─────────────────────────────────────────────────────────
    section_heading(doc, "Anticipated Lines of Questioning", level=1)

    section_heading(doc, "Autonomous Weapons Systems", level=2)
    body_para(doc,
        "Committee members have publicly raised concerns about the adequacy of the "
        "Directive 3000.09 review cycle given the pace of AI deployment across INDOPACOM.")
    bullet_item(doc, "DoD has approved 47 programs with autonomous features since 2023")
    bullet_item(doc, "GAO found 12 programs lacked sufficient human-on-the-loop documentation")
    bullet_item(doc, "Allied partners (UK, Australia) have pushed for NATO-level standards")

    callout(doc,
        "Warning: Dr. Okonkwo's prepared remarks, obtained informally, do not address "
        "the GAO findings directly. Expect pressure from Ranking Member Torres.",
        kind="warning")

    section_heading(doc, "Budget and Oversight", level=2)
    body_para(doc,
        "The committee is expected to probe the $2.3B AI modernization line in the "
        "FY2026 NDAA, specifically the classification of certain programs that "
        "bypassed standard acquisition review.")
    bullet_item(doc, "HASC subcommittee requested declassification of 4 program elements")
    bullet_item(doc, "NSA's PATHFINDER initiative has not had a public hearing since 2022")

    # ── Background on Client Position ──────────────────────────────────────
    section_heading(doc, "Relevance to Client", level=1)
    body_para(doc,
        "Your client, [Client Name], has a direct interest in two provisions being "
        "considered as potential amendments: the mandatory AI audit requirement (§ 847) "
        "and the export control expansion for frontier model weights (§ 912).")

    callout(doc,
        "Positive signal: § 847 language was drafted in consultation with industry working "
        "groups in which client participated. Client's position aligns with the current text.",
        kind="positive")

    # ── Review Checklist ───────────────────────────────────────────────────
    section_heading(doc, "Pre-Distribution Review Checklist", level=1)
    for item in [
        "Verify witness names and titles against official committee notice",
        "Confirm client position on § 847 with account lead",
        "Remove [Client Name] placeholder before distribution",
        "PA supervisor sign-off required (yellow risk level)",
    ]:
        bullet_item(doc, item)

    # ── Footer ─────────────────────────────────────────────────────────────
    add_footer(doc)

    doc.save(out_path)
    print(f"Demo saved → {out_path}")


def build_pdf_demo(out_path: str) -> None:
    from pdf_brand import (
        build_branded_pdf, heading, body, bullet, callout, meta_block, data_table,
        Spacer,
    )
    from reportlab.lib.units import mm

    story = []

    story += meta_block([
        ("Committee",      "Senate Foreign Relations Committee"),
        ("Hearing Date",   "April 10, 2026"),
        ("Prepared By",    "PA AI Toolkit — Background Memo"),
        ("Classification", "Confidential — Internal Use Only"),
        ("Risk Level",     "Yellow — Review before external distribution"),
    ])

    story += heading("Executive Summary")
    story.append(body(
        "The Senate Foreign Relations Committee will hold a hearing on April 10 examining "
        "the implications of AI systems in national security contexts, with particular focus "
        "on autonomous decision-making, allied coordination, and oversight frameworks. "
        "Three administration officials are expected to testify."
    ))
    story += callout(
        "Key watch item: Senator Chen is expected to press witnesses on the gap between "
        "DoD's stated AI ethics principles and procurement decisions made in fiscal 2025.",
        kind="info",
    )

    story += heading("Witnesses")
    story.append(body("The following witnesses are scheduled to appear:", tight=True))
    story += data_table(
        headers=["Name", "Title", "Agency", "Prior Testimony"],
        rows=[
            ["Dr. Sarah Okonkwo", "Deputy Secretary", "Department of Defense", "3 appearances"],
            ["James Whitfield",   "Director",         "National Security Agency", "1 appearance"],
            ["Amara Singh",       "Senior Advisor",   "NSC",                     "None on record"],
        ],
    )

    story += heading("Anticipated Lines of Questioning")
    story += heading("Autonomous Weapons Systems", level=2)
    story.append(body(
        "Committee members have publicly raised concerns about the adequacy of the "
        "Directive 3000.09 review cycle given the pace of AI deployment across INDOPACOM."
    ))
    for item in [
        "DoD has approved 47 programs with autonomous features since 2023",
        "GAO found 12 programs lacked sufficient human-on-the-loop documentation",
        "Allied partners (UK, Australia) have pushed for NATO-level standards",
    ]:
        story.append(bullet(item))
    story += callout(
        "Warning: Dr. Okonkwo's prepared remarks do not address the GAO findings directly. "
        "Expect pressure from Ranking Member Torres.",
        kind="warning",
    )

    story += heading("Budget and Oversight", level=2)
    story.append(body(
        "The committee is expected to probe the $2.3B AI modernization line in the FY2026 NDAA, "
        "specifically the classification of certain programs that bypassed standard acquisition review."
    ))
    for item in [
        "HASC subcommittee requested declassification of 4 program elements",
        "NSA's PATHFINDER initiative has not had a public hearing since 2022",
    ]:
        story.append(bullet(item))

    story += heading("Relevance to Client")
    story.append(body(
        "Your client has a direct interest in two provisions being considered as potential amendments: "
        "the mandatory AI audit requirement (§ 847) and the export control expansion for frontier "
        "model weights (§ 912)."
    ))
    story += callout(
        "Positive signal: § 847 language was drafted in consultation with industry working groups "
        "in which client participated. Client position aligns with the current text.",
        kind="positive",
    )

    story += heading("Pre-Distribution Review Checklist")
    for item in [
        "Verify witness names and titles against official committee notice",
        "Confirm client position on § 847 with account lead",
        "Remove [Client Name] placeholder before distribution",
        "PA supervisor sign-off required (yellow risk level)",
    ]:
        story.append(bullet(item))

    build_branded_pdf(
        out_path=out_path,
        title="Hearing Memo",
        subtitle="Senate Foreign Relations Committee — AI and National Security",
        date_str=date.today().strftime("%B %d, %Y"),
        story=story,
    )
    print(f"PDF demo saved → {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate branded sample documents.")
    parser.add_argument("--out",     default="brand_demo.docx", help="DOCX output path")
    parser.add_argument("--out-pdf", default="brand_demo.pdf",  help="PDF output path")
    parser.add_argument("--pdf-only", action="store_true")
    parser.add_argument("--docx-only", action="store_true")
    args = parser.parse_args()

    if not args.pdf_only:
        build_demo(args.out)
    if not args.docx_only:
        build_pdf_demo(args.out_pdf)


if __name__ == "__main__":
    main()
