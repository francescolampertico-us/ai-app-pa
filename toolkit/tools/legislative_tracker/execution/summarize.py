"""
Bill Summarizer
================
ChangeAgent-powered legislative summarization that only emits a verified source
summary when every displayed line is traceable to the official bill text.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any

from openai import OpenAI


DEFAULT_MODEL = "ChangeAgent"
EXTRACTION_MODEL = "ChangeAgent"
CHANGE_AGENT_BASE_URL = "https://runpod-proxy-956966668285.us-central1.run.app/v1/"
MAX_CHUNK_CHARS = 8_500
MAX_SECTIONS_PER_CHUNK = 3
MAX_LARGE_BILL_CHUNK_CHARS = 30_000
MAX_LARGE_BILL_SECTIONS_PER_CHUNK = 12
LARGE_BILL_CHAR_THRESHOLD = 120_000
CHANGEAGENT_TIMEOUT_SECONDS = 45
MAX_SUMMARIZE_SECONDS = 420
MAX_EXTRACTION_CHUNKS = 8
MAX_AGGRESSIVE_CHUNK_CHARS = 60_000

VERIFIED_SECTIONS = [
    "### Bill Overview",
    "### Plain-Language Summary",
    "### Key Provisions",
    "### Definitions, Thresholds, and Deadlines",
    "### Exemptions and Exceptions",
    "### Enforcement, Reporting, and Certification",
    "### Legislative Status",
]

FACT_CATEGORIES = {
    "scope",
    "prohibition",
    "authorization",
    "exemption",
    "deadline",
    "funding_threshold",
    "enforcement",
    "reporting_certification",
    "definition",
}

EXTRACTION_SYSTEM_PROMPT = """You are a legislative text extraction engine.

Rules:
- Extract only facts directly supported by the bill text.
- Do not infer impact, intent, politics, market effects, or business consequences.
- Preserve the legal mechanics as written: requires, prohibits, creates, exempts,
  authorizes, defines, certifies, reports, enforces.
- Include a short exact support snippet copied from the bill text for every fact.
- If the chunk is mostly amendment mechanics, say that explicitly and be conservative.
- Return JSON only if possible."""

EXTRACTION_USER_PROMPT = """Extract directly supported legislative facts from the bill chunk below.

Bill metadata:
- Number: {number}
- Title: {title}
- Chunk: {chunk_num} of {total_chunks}

Return a JSON object with:
- "chunk_notes": short string
- "facts": array of objects with:
  - "section_ref"
  - "heading"
  - "category" (one of: scope, prohibition, authorization, exemption, deadline, funding_threshold, enforcement, reporting_certification, definition)
  - "fact_text" (normalized factual meaning in plain language, but still text-supported)
  - "support_snippet" (short exact quote from the text)
  - "defined_terms" (array)
  - "dates_deadlines" (array)
  - "money_thresholds" (array)
  - "agencies_entities" (array)
  - "amendment_mechanics" (boolean)
  - "confidence" ("high" | "medium" | "low")

If there are no usable directly supported facts, return an empty "facts" array and explain why in "chunk_notes".

Bill chunk:
---
{chunk_text}
---"""

EXTRACTION_REPAIR_PROMPT = """Repair the previous response into valid JSON with this exact shape:
{
  "chunk_notes": "string",
  "facts": [
    {
      "section_ref": "string",
      "heading": "string",
      "category": "scope",
      "fact_text": "string",
      "support_snippet": "string",
      "defined_terms": ["string"],
      "dates_deadlines": ["string"],
      "money_thresholds": ["string"],
      "agencies_entities": ["string"],
      "amendment_mechanics": false,
      "confidence": "high"
    }
  ]
}
Return JSON only."""

COMPOSITION_SYSTEM_PROMPT = """You are a legislative translator for policy and public-affairs audiences.

Rules:
- Write in clear plain English for a non-lawyer reader.
- Paraphrase the bill's mechanics so the reader can understand what the bill actually does.
- Use only the evidence records provided. Do not add implications, market effects, strategy, politics, or speculation.
- Keep each bullet to one or two short sentences.
- Every fact-derived bullet must end with an evidence tag in this exact format:
  [[evidence:fact_id_1,fact_id_2]]
- If a section has no usable evidence, output exactly:
  - No directly supported provision is available for this section. [[evidence:none]]
- Preserve the exact markdown headings requested."""

COMPOSITION_USER_PROMPT = """Using only the evidence below, write the fact-derived sections of a verified legislative summary.

Audience:
- intelligent non-lawyer reader
- wants to understand what the bill actually does in normal language

Required headings and order:
### Plain-Language Summary
### Key Provisions
### Definitions, Thresholds, and Deadlines
### Exemptions and Exceptions
### Enforcement, Reporting, and Certification

Requirements:
- Under each heading, write short bullet points in plain English.
- You may combine closely related evidence records into one bullet if all referenced ids are included in the evidence tag.
- Do not use quotation marks unless absolutely necessary.
- Do not mention information that is not present in the evidence.
- Do not include legislative status, sponsors, political analysis, next steps, or stakeholder impact.

Bill metadata:
- Number: {number}
- Title: {title}

Evidence records:
{evidence_records}
"""


def _effective_model(model: str) -> str:
    return os.environ.get("LLM_MODEL_OVERRIDE") or model


def _changeagent_client() -> OpenAI:
    api_key = os.environ.get("CHANGE_AGENT_API_KEY", "").strip()
    base_url = os.environ.get("OPENAI_BASE_URL") or CHANGE_AGENT_BASE_URL
    if _effective_model(DEFAULT_MODEL) != "ChangeAgent":
        raise ValueError("Legislative summarization is ChangeAgent-only.")
    if not api_key:
        raise ValueError("ChangeAgent credentials not configured. Set CHANGE_AGENT_API_KEY.")
    return OpenAI(api_key=api_key, base_url=base_url)


def _call_changeagent(
    client: OpenAI,
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float = 0.0,
) -> str:
    response = client.chat.completions.create(
        model=_effective_model(model),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        timeout=CHANGEAGENT_TIMEOUT_SECONDS,
    )
    return response.choices[0].message.content or ""


def summarize_bill(bill_detail: dict, bill_text: str, model: str = None) -> dict:
    return summarize_bill_detailed(bill_detail, bill_text, model=model)


def summarize_bill_preview(bill_detail: dict) -> dict:
    sponsors = bill_detail.get("sponsors") or []
    primary = [s for s in sponsors if s.get("sponsorship_type_id") == 1 or s.get("type") == 1] or sponsors[:3]
    sponsor_names = ", ".join(s.get("name", "Unknown") for s in primary[:3]) or "Not listed"
    texts = bill_detail.get("texts") or []
    latest_text = None
    if texts:
        latest_text = sorted(texts, key=lambda item: item.get("date") or "", reverse=True)[0]

    state = bill_detail.get("state") or ""
    jurisdiction = "Federal (US)" if state.upper() == "US" else (state or "N/A")
    history = bill_detail.get("history") or []
    last_action = bill_detail.get("last_action") or ""
    last_action_date = bill_detail.get("last_action_date") or ""
    if not last_action and history:
        latest = sorted(history, key=lambda h: h.get("date") or "", reverse=True)
        last_action = latest[0].get("action") or ""
        if not last_action_date:
            last_action_date = latest[0].get("date") or ""

    lines = [
        "### Bill Overview",
        f"- **Number:** {bill_detail.get('number', 'N/A')}",
        f"- **Title:** {bill_detail.get('title', 'N/A')}",
        f"- **Jurisdiction:** {jurisdiction}",
        f"- **Session:** {bill_detail.get('session', 'N/A')}",
        "",
        "### Quick Preview",
        f"- {bill_detail.get('description') or 'No official description was available in the bill record.'}",
        f"- Primary sponsor(s): {sponsor_names}.",
        f"- Current legislative status: {bill_detail.get('status', 'N/A')}.",
        "",
        "### Current Record",
        f"- Last action date: {last_action_date or 'Not recorded'}.",
        f"- Last action: {last_action or 'Not recorded in the summary record.'}",
        f"- Text versions available: {len(texts)}.",
    ]
    if latest_text:
        lines.append(
            f"- Latest text version on record: {latest_text.get('type') or 'Unknown'} dated {latest_text.get('date') or 'Unknown'}."
        )
    if bill_detail.get("url") or bill_detail.get("state_url"):
        lines.extend([
            "",
            "### Source Link",
            f"- Official link: {bill_detail.get('state_url') or bill_detail.get('url')}.",
        ])

    return {
        "summary": "\n".join(lines),
        "caveats": [
            "This is a quick preview generated from bill-record metadata and description only.",
            "Use the detailed summary to scan the full bill text and generate a verified source summary.",
        ],
        "summary_status": "preview_ready",
        "source_text_status": "not_requested",
        "source_status": "metadata_preview",
        "extraction_status": "not_run",
        "verification_status": "preview",
        "coverage_mode": "preview_only",
        "extraction_coverage": {"extracted_sections": 0, "total_sections": 0},
        "evidence_coverage": {"fact_count": 0, "parsed_chunks": 0, "total_chunks": 0},
        "validation_flags": [],
        "unsupported_claims": [],
        "traceability_report": [],
        "model_path": {"extraction": "not_run", "synthesis": "metadata_preview"},
        "evidence_index": [],
        "summary_structured": {
            "render_mode": "preview_summary",
            "detail_level": "preview",
            "sections": ["### Bill Overview", "### Quick Preview", "### Current Record", "### Source Link"],
        },
    }


def summarize_bill_detailed(bill_detail: dict, bill_text: str, model: str = None) -> dict:
    del model
    client = _changeagent_client()

    normalized = _normalize_bill_text(bill_text)
    source_status = _classify_source_status(bill_detail, bill_text, normalized)
    if source_status != "verified_full_text":
        return _blocked_missing_source_result(bill_detail, normalized, bill_text)

    extraction = _extract_and_consolidate_facts(client, bill_detail, normalized["text"], detailed=True)
    summary, traceability_report = _compose_verified_summary(client, bill_detail, extraction["fact_index"])
    verification = verify_summary(
        summary=summary,
        traceability_report=traceability_report,
        fact_index=extraction["fact_index"],
        bill_detail=bill_detail,
        source_status=source_status,
        extraction_status=extraction["extraction_status"],
    )

    if verification["summary_status"] != "verified":
        return _blocked_verification_result(
            bill_detail=bill_detail,
            extraction=extraction,
            verification=verification,
            normalized=normalized,
        )

    return {
        "summary": summary,
        "caveats": [],
        "summary_status": "verified",
        "source_text_status": "full",
        "source_status": source_status,
        "extraction_status": extraction["extraction_status"],
        "verification_status": "verified",
        "coverage_mode": "verified_full_text",
        "extraction_coverage": {
            "extracted_sections": extraction["coverage"]["parsed_chunks"],
            "total_sections": extraction["coverage"]["total_chunks"],
        },
        "evidence_coverage": extraction["coverage"],
        "validation_flags": [],
        "unsupported_claims": [],
        "traceability_report": traceability_report,
        "model_path": {
            "extraction": _effective_model(EXTRACTION_MODEL),
            "synthesis": "deterministic_composer",
        },
        "evidence_index": extraction["fact_index"],
        "summary_structured": {
            "render_mode": "verified_source_summary",
            "detail_level": "detailed",
            "sections": VERIFIED_SECTIONS,
        },
    }


def _normalize_bill_text(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw or raw.startswith("[Full text not available."):
        return {"text": "", "flags": ["missing_text"], "amendment_heavy": False}

    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u00a0", " ").replace("\ufeff", "").replace("\u200b", "")
    normalized = re.sub(r"([A-Za-z])-\n([A-Za-z])", r"\1\2", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = re.sub(r"^\s*Page \d+\s*$", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(r"^\s*\d+\s*$", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(r"_{3,}", "", normalized)

    repeated = _find_repeated_lines(normalized)
    if repeated:
        normalized = "\n".join(
            line for line in normalized.splitlines()
            if line.strip() not in repeated
        )

    amendment_hits = len(re.findall(r"\b(strike|striking|insert|inserting|redesignate|redesignating|amend)\b", normalized, flags=re.I))
    flags: list[str] = []
    if repeated:
        flags.append("header_footer_cleanup")
    if amendment_hits >= 12:
        flags.append("amendment_heavy_text")

    return {
        "text": normalized.strip(),
        "flags": flags,
        "amendment_heavy": "amendment_heavy_text" in flags,
    }


def _find_repeated_lines(text: str) -> set[str]:
    counts: dict[str, int] = {}
    for line in text.splitlines():
        key = line.strip()
        if len(key) < 8:
            continue
        counts[key] = counts.get(key, 0) + 1
    return {line for line, count in counts.items() if count >= 3}


def _classify_source_status(bill_detail: dict, raw_bill_text: str, normalized: dict[str, Any]) -> str:
    if not normalized["text"]:
        return "unusable_text"
    if not bill_detail.get("texts"):
        return "unusable_text"
    if raw_bill_text.startswith("[Full text not available."):
        return "unusable_text"
    return "verified_full_text"


def _extract_and_consolidate_facts(client: OpenAI, bill_detail: dict, text: str, *, detailed: bool = False) -> dict[str, Any]:
    chunks = _chunk_bill_text(text, detailed=detailed)
    extracted_chunks: list[dict[str, Any]] = []
    parsed_chunks = 0
    started_at = time.monotonic()
    budget_exhausted = False

    for idx, chunk in enumerate(chunks, start=1):
        if not detailed and time.monotonic() - started_at > MAX_SUMMARIZE_SECONDS:
            budget_exhausted = True
            break
        extracted = _extract_chunk(client, bill_detail, chunk, idx, len(chunks))
        if extracted["parsed"]:
            parsed_chunks += 1
        extracted_chunks.append(extracted)

    fact_index = _merge_facts(extracted_chunks)
    extraction_status = "verified"
    if parsed_chunks != len(chunks) or not fact_index or budget_exhausted:
        extraction_status = "blocked"

    return {
        "fact_index": fact_index,
        "coverage": {
            "total_chunks": len(chunks),
            "parsed_chunks": parsed_chunks,
            "fact_count": len(fact_index),
            "amendment_fact_count": sum(1 for fact in fact_index if fact["amendment_mechanics"]),
            "budget_exhausted": budget_exhausted,
        },
        "extraction_status": extraction_status,
    }


def _chunk_bill_text(text: str, *, detailed: bool = False) -> list[str]:
    lines = text.splitlines()
    sections: list[str] = []
    current: list[str] = []
    section_pattern = re.compile(r"^\s*(SEC\.|Section|SECTION|TITLE|Title)\b")
    chunk_char_limit = MAX_LARGE_BILL_CHUNK_CHARS if len(text) >= LARGE_BILL_CHAR_THRESHOLD else MAX_CHUNK_CHARS
    section_limit = MAX_LARGE_BILL_SECTIONS_PER_CHUNK if len(text) >= LARGE_BILL_CHAR_THRESHOLD else MAX_SECTIONS_PER_CHUNK

    def flush() -> None:
        if current:
            sections.append("\n".join(current).strip())
            current.clear()

    for line in lines:
        if section_pattern.match(line) and current:
            flush()
        current.append(line)
    flush()

    if not sections:
        sections = [text]

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_chars = 0
    current_sections = 0
    for section in sections:
        if not section.strip():
            continue
        if current_chunk and (current_chars + len(section) > chunk_char_limit or current_sections >= section_limit):
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            current_chars = 0
            current_sections = 0

        if len(section) > chunk_char_limit:
            for piece in _split_large_section(section, chunk_char_limit):
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_chars = 0
                    current_sections = 0
                chunks.append(piece)
            continue

        current_chunk.append(section)
        current_chars += len(section)
        current_sections += 1

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    chunks = chunks or [text[:chunk_char_limit]]
    if not detailed and len(chunks) > MAX_EXTRACTION_CHUNKS:
        chunks = _coalesce_chunks(chunks, MAX_EXTRACTION_CHUNKS, MAX_AGGRESSIVE_CHUNK_CHARS)
    return chunks


def _split_large_section(section: str, chunk_char_limit: int) -> list[str]:
    pieces: list[str] = []
    start = 0
    while start < len(section):
        end = min(len(section), start + chunk_char_limit)
        if end < len(section):
            split_at = section.rfind("\n", start + int(chunk_char_limit * 0.7), end)
            if split_at > start:
                end = split_at
        pieces.append(section[start:end].strip())
        start = end
    return [piece for piece in pieces if piece]


def _coalesce_chunks(chunks: list[str], max_chunks: int, aggressive_char_limit: int) -> list[str]:
    if len(chunks) <= max_chunks:
        return chunks

    target_size = max(2, (len(chunks) + max_chunks - 1) // max_chunks)
    merged: list[str] = []
    current: list[str] = []
    current_len = 0

    for chunk in chunks:
        if current and (len(current) >= target_size or current_len + len(chunk) > aggressive_char_limit):
            merged.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(chunk)
        current_len += len(chunk)

    if current:
        merged.append("\n\n".join(current))

    if len(merged) > max_chunks:
        final: list[str] = []
        group_size = max(2, (len(merged) + max_chunks - 1) // max_chunks)
        for idx in range(0, len(merged), group_size):
            final.append("\n\n".join(merged[idx:idx + group_size]))
        return final

    return merged


def _extract_chunk(client: OpenAI, bill_detail: dict, chunk_text: str, chunk_num: int, total_chunks: int) -> dict[str, Any]:
    prompt = EXTRACTION_USER_PROMPT.format(
        number=bill_detail.get("number", "N/A"),
        title=bill_detail.get("title", "N/A"),
        chunk_num=chunk_num,
        total_chunks=total_chunks,
        chunk_text=chunk_text,
    )
    try:
        raw = _call_changeagent(
            client,
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_prompt=prompt,
            model=EXTRACTION_MODEL,
        )
    except Exception as exc:
        return {
            "parsed": False,
            "payload": {"chunk_notes": f"Extraction call failed: {exc}", "facts": []},
        }
    parsed = _parse_extraction_response(raw)
    if parsed:
        return {"parsed": True, "payload": parsed}

    try:
        repaired = _call_changeagent(
            client,
            system_prompt="Repair legislative extraction output into valid JSON only.",
            user_prompt=f"{EXTRACTION_REPAIR_PROMPT}\n\nOriginal response:\n{raw}",
            model=EXTRACTION_MODEL,
        )
    except Exception as exc:
        return {
            "parsed": False,
            "payload": {"chunk_notes": f"Repair call failed: {exc}", "facts": []},
        }
    repaired_parsed = _parse_extraction_response(repaired)
    if repaired_parsed:
        return {"parsed": True, "payload": repaired_parsed}

    return {"parsed": False, "payload": {"chunk_notes": "Unparseable extraction output.", "facts": []}}


def _parse_extraction_response(raw: str) -> dict[str, Any] | None:
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if fence:
        text = fence.group(1).strip()

    candidates: list[str] = []
    if text.startswith("{"):
        candidates.append(text)
    outer = re.search(r"\{[\s\S]*\}", text)
    if outer:
        candidates.append(outer.group(0))

    for candidate in candidates:
        try:
            obj = json.loads(candidate)
            return _normalize_extraction_payload(obj)
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    return None


def _normalize_extraction_payload(obj: dict[str, Any]) -> dict[str, Any]:
    facts = []
    for item in obj.get("facts", []):
        if not isinstance(item, dict):
            continue
        category = str(item.get("category") or "").strip()
        if category not in FACT_CATEGORIES:
            continue
        support_snippet = str(item.get("support_snippet") or "").strip()
        fact_text = str(item.get("fact_text") or "").strip()
        if not support_snippet or not fact_text:
            continue
        facts.append({
            "section_ref": str(item.get("section_ref") or "Unspecified section").strip(),
            "heading": str(item.get("heading") or "").strip(),
            "category": category,
            "fact_text": fact_text,
            "support_snippet": support_snippet,
            "defined_terms": _ensure_string_list(item.get("defined_terms")),
            "dates_deadlines": _ensure_string_list(item.get("dates_deadlines")),
            "money_thresholds": _ensure_string_list(item.get("money_thresholds")),
            "agencies_entities": _ensure_string_list(item.get("agencies_entities")),
            "amendment_mechanics": bool(item.get("amendment_mechanics")),
            "confidence": str(item.get("confidence") or "medium").lower(),
        })
    return {"chunk_notes": str(obj.get("chunk_notes") or "").strip(), "facts": facts}


def _ensure_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in re.split(r",|\n", text) if part.strip()]


def _merge_facts(extracted_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for chunk in extracted_chunks:
        for fact in chunk.get("payload", {}).get("facts", []):
            key = hashlib.md5(f"{fact['section_ref']}|{fact['category']}|{fact['fact_text'].lower()}".encode("utf-8")).hexdigest()
            existing = merged.get(key)
            if not existing:
                merged[key] = {
                    "id": f"fact_{key[:10]}",
                    "section_ref": fact["section_ref"],
                    "heading": fact["heading"],
                    "category": fact["category"],
                    "fact_text": fact["fact_text"],
                    "support_snippet": fact["support_snippet"],
                    "defined_terms": set(fact["defined_terms"]),
                    "dates_deadlines": set(fact["dates_deadlines"]),
                    "money_thresholds": set(fact["money_thresholds"]),
                    "agencies_entities": set(fact["agencies_entities"]),
                    "amendment_mechanics": fact["amendment_mechanics"],
                    "confidence": fact["confidence"],
                }
                continue

            existing["defined_terms"].update(fact["defined_terms"])
            existing["dates_deadlines"].update(fact["dates_deadlines"])
            existing["money_thresholds"].update(fact["money_thresholds"])
            existing["agencies_entities"].update(fact["agencies_entities"])
            existing["amendment_mechanics"] = existing["amendment_mechanics"] or fact["amendment_mechanics"]
            existing["confidence"] = _merge_confidence(existing["confidence"], fact["confidence"])
            if len(fact["support_snippet"]) > len(existing["support_snippet"]):
                existing["support_snippet"] = fact["support_snippet"]

    fact_index = []
    for fact in merged.values():
        fact_index.append({
            "id": fact["id"],
            "section_ref": fact["section_ref"],
            "heading": fact["heading"],
            "category": fact["category"],
            "fact_text": fact["fact_text"],
            "support_snippet": fact["support_snippet"],
            "defined_terms": sorted(fact["defined_terms"]),
            "dates_deadlines": sorted(fact["dates_deadlines"]),
            "money_thresholds": sorted(fact["money_thresholds"]),
            "agencies_entities": sorted(fact["agencies_entities"]),
            "amendment_mechanics": fact["amendment_mechanics"],
            "confidence": fact["confidence"],
        })
    fact_index.sort(key=lambda item: (item["section_ref"], item["category"], item["fact_text"]))
    return fact_index


def _merge_confidence(left: str, right: str) -> str:
    order = {"high": 3, "medium": 2, "low": 1}
    return left if order.get(left, 2) >= order.get(right, 2) else right


def _compose_verified_summary(client: OpenAI, bill_detail: dict, fact_index: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    fact_body, fact_traceability = _compose_fact_sections_with_changeagent(client, bill_detail, fact_index)
    traceability_report: list[dict[str, Any]] = []
    lines: list[str] = []

    def add_heading(heading: str) -> None:
        lines.append(heading)

    def add_line(text: str, evidence_ids: list[str], section_refs: list[str], support_status: str = "directly_supported") -> None:
        lines.append(text)
        traceability_report.append({
            "line": text,
            "evidence_ids": evidence_ids,
            "section_refs": section_refs,
            "support_status": support_status,
        })

    jurisdiction = "Federal (US)" if (bill_detail.get("state") or "").upper() == "US" else (bill_detail.get("state") or "N/A")
    add_heading("### Bill Overview")
    add_line(f"- **Number:** {bill_detail.get('number', 'N/A')}", [], [], "metadata_supported")
    add_line(f"- **Title:** {bill_detail.get('title', 'N/A')}", [], [], "metadata_supported")
    add_line(f"- **Jurisdiction:** {jurisdiction}", [], [], "metadata_supported")
    add_line(f"- **Session:** {bill_detail.get('session', 'N/A')}", [], [], "metadata_supported")
    add_line(f"- **Status:** {bill_detail.get('status', 'N/A')}", [], [], "metadata_supported")

    add_heading("")
    for line in fact_body:
        lines.append(line["line"])
        if line["support_status"] == "heading":
            continue
        traceability_report.append({
            "line": line["line"],
            "evidence_ids": line["evidence_ids"],
            "section_refs": line["section_refs"],
            "support_status": line["support_status"],
        })

    last_action = bill_detail.get("last_action") or ""
    last_action_date = bill_detail.get("last_action_date") or ""
    if not last_action or not last_action_date:
        history = bill_detail.get("history") or []
        if history:
            latest = sorted(history, key=lambda h: h.get("date") or "", reverse=True)
            if not last_action:
                last_action = latest[0].get("action") or ""
            if not last_action_date:
                last_action_date = latest[0].get("date") or ""
    action_str = last_action or "Not recorded"
    if last_action_date:
        action_str = f"{action_str} ({last_action_date})"

    add_heading("")
    add_heading("### Legislative Status")
    add_line(f"- Current status: {bill_detail.get('status', 'N/A')}.", [], [], "metadata_supported")
    add_line(f"- Last recorded action: {action_str}.", [], [], "metadata_supported")
    if bill_detail.get("url") or bill_detail.get("state_url"):
        add_line(f"- Official link: {bill_detail.get('state_url') or bill_detail.get('url')}.", [], [], "metadata_supported")

    return "\n".join(lines), traceability_report


def _compose_fact_sections_with_changeagent(
    client: OpenAI,
    bill_detail: dict,
    fact_index: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not fact_index:
        fallback = _deterministic_fact_section_lines(fact_index)
        return fallback, fallback

    fact_map = {fact["id"]: fact for fact in fact_index}
    evidence_records = "\n".join(_format_fact_record(fact) for fact in fact_index)
    try:
        raw = _call_changeagent(
            client,
            system_prompt=COMPOSITION_SYSTEM_PROMPT,
            user_prompt=COMPOSITION_USER_PROMPT.format(
                number=bill_detail.get("number", "N/A"),
                title=bill_detail.get("title", "N/A"),
                evidence_records=evidence_records,
            ),
            model=DEFAULT_MODEL,
            temperature=0.1,
        )
    except Exception:
        fallback = _deterministic_fact_section_lines(fact_index)
        return fallback, fallback
    parsed = _parse_composed_fact_sections(raw, fact_map)
    if parsed:
        return parsed, parsed
    fallback = _deterministic_fact_section_lines(fact_index)
    return fallback, fallback


def _format_fact_record(fact: dict[str, Any]) -> str:
    detail_bits: list[str] = []
    defined_terms = fact.get("defined_terms") or []
    dates_deadlines = fact.get("dates_deadlines") or []
    money_thresholds = fact.get("money_thresholds") or []
    agencies_entities = fact.get("agencies_entities") or []
    if defined_terms:
        detail_bits.append(f"defined_terms={', '.join(defined_terms)}")
    if dates_deadlines:
        detail_bits.append(f"dates_deadlines={', '.join(dates_deadlines)}")
    if money_thresholds:
        detail_bits.append(f"money_thresholds={', '.join(money_thresholds)}")
    if agencies_entities:
        detail_bits.append(f"agencies_entities={', '.join(agencies_entities)}")
    if fact.get("amendment_mechanics"):
        detail_bits.append("amendment_mechanics=true")
    detail_suffix = f" | {' ; '.join(detail_bits)}" if detail_bits else ""
    return (
        f"- {fact.get('id', 'unknown_fact')} | section_ref={fact.get('section_ref', 'Unspecified section')} | heading={fact.get('heading', 'Untitled')} | "
        f"category={fact.get('category', 'scope')} | fact_text={fact.get('fact_text', '')} | support_snippet={fact.get('support_snippet', '')}{detail_suffix}"
    )


def _parse_composed_fact_sections(raw: str, fact_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]] | None:
    text = (raw or "").strip()
    if not text:
        return None

    lines: list[dict[str, Any]] = []
    active_heading = None
    expected_headings = {
        "### Plain-Language Summary",
        "### Key Provisions",
        "### Definitions, Thresholds, and Deadlines",
        "### Exemptions and Exceptions",
        "### Enforcement, Reporting, and Certification",
    }
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line in expected_headings:
            active_heading = line
            lines.append({"line": line, "evidence_ids": [], "section_refs": [], "support_status": "heading"})
            continue
        if not active_heading:
            continue
        if not line.startswith("- "):
            continue
        match = re.search(r"\[\[evidence:([^\]]+)\]\]\s*$", line)
        if not match:
            return None
        ids_text = match.group(1).strip()
        clean_line = re.sub(r"\s*\[\[evidence:[^\]]+\]\]\s*$", "", line).strip()
        if ids_text == "none":
            evidence_ids: list[str] = []
            section_refs: list[str] = []
            support_status = "metadata_supported"
        else:
            evidence_ids = [item.strip() for item in ids_text.split(",") if item.strip()]
            if not evidence_ids or any(evidence_id not in fact_map for evidence_id in evidence_ids):
                return None
            section_refs = sorted({fact_map[evidence_id]["section_ref"] for evidence_id in evidence_ids})
            support_status = "directly_supported"
        lines.append({
            "line": clean_line,
            "evidence_ids": evidence_ids,
            "section_refs": section_refs,
            "support_status": support_status,
        })
    headings_present = {item["line"] for item in lines if item["support_status"] == "heading"}
    if headings_present != expected_headings:
        return None
    return lines


def _deterministic_fact_section_lines(fact_index: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []

    def add_heading(heading: str) -> None:
        lines.append({"line": heading, "evidence_ids": [], "section_refs": [], "support_status": "heading"})

    def add_line(text: str, evidence_ids: list[str], section_refs: list[str], support_status: str = "directly_supported") -> None:
        lines.append({"line": text, "evidence_ids": evidence_ids, "section_refs": section_refs, "support_status": support_status})

    add_heading("### Plain-Language Summary")
    scope_facts = _facts_by_category(fact_index, {"scope", "authorization", "prohibition"})
    for fact in scope_facts[:4]:
        add_line(f"- {fact['fact_text']} ({fact['section_ref']})", [fact["id"]], [fact["section_ref"]])
    if not scope_facts:
        add_line("- No directly supported provision is available for this section.", [], [], "metadata_supported")

    add_heading("### Key Provisions")
    for fact in fact_index[:8]:
        add_line(f"- {fact['fact_text']} ({fact['section_ref']})", [fact["id"]], [fact["section_ref"]])

    add_heading("### Definitions, Thresholds, and Deadlines")
    structured = _facts_by_category(fact_index, {"definition", "deadline", "funding_threshold"})
    if structured:
        for fact in structured[:8]:
            detail_bits = []
            if fact["defined_terms"]:
                detail_bits.append(f"terms: {', '.join(fact['defined_terms'])}")
            if fact["money_thresholds"]:
                detail_bits.append(f"thresholds/funding: {', '.join(fact['money_thresholds'])}")
            if fact["dates_deadlines"]:
                detail_bits.append(f"dates/deadlines: {', '.join(fact['dates_deadlines'])}")
            detail = f" [{' ; '.join(detail_bits)}]" if detail_bits else ""
            add_line(f"- {fact['fact_text']} ({fact['section_ref']}){detail}", [fact["id"]], [fact["section_ref"]])
    else:
        add_line("- No directly supported provision is available for this section.", [], [], "metadata_supported")

    add_heading("### Exemptions and Exceptions")
    exemptions = _facts_by_category(fact_index, {"exemption"})
    if exemptions:
        for fact in exemptions[:6]:
            add_line(f"- {fact['fact_text']} ({fact['section_ref']})", [fact["id"]], [fact["section_ref"]])
    else:
        add_line("- No directly supported provision is available for this section.", [], [], "metadata_supported")

    add_heading("### Enforcement, Reporting, and Certification")
    enforcement = _facts_by_category(fact_index, {"enforcement", "reporting_certification"})
    if enforcement:
        for fact in enforcement[:8]:
            add_line(f"- {fact['fact_text']} ({fact['section_ref']})", [fact["id"]], [fact["section_ref"]])
    else:
        add_line("- No directly supported provision is available for this section.", [], [], "metadata_supported")

    return lines


def _facts_by_category(fact_index: list[dict[str, Any]], categories: set[str]) -> list[dict[str, Any]]:
    return [fact for fact in fact_index if fact["category"] in categories]


def verify_summary(
    *,
    summary: str,
    traceability_report: list[dict[str, Any]],
    fact_index: list[dict[str, Any]],
    bill_detail: dict,
    source_status: str,
    extraction_status: str,
) -> dict[str, Any]:
    flags: list[str] = []
    unsupported_claims: list[str] = []
    fact_map = {fact["id"]: fact for fact in fact_index}

    if source_status != "verified_full_text":
        flags.append("SOURCE_NOT_VERIFIED")
    if extraction_status != "verified":
        flags.append("EXTRACTION_NOT_VERIFIED")

    for heading in VERIFIED_SECTIONS:
        if heading not in summary:
            flags.append(f"MISSING_SECTION:{heading}")

    numeric_mismatches = []
    metadata_pool = _build_metadata_verification_pool(bill_detail)
    for item in traceability_report:
        if item["support_status"] not in {"directly_supported", "metadata_supported"}:
            unsupported_claims.append(item["line"])
            continue
        if item["support_status"] == "metadata_supported":
            numeric_tokens = re.findall(r"(?:\$[\d,]+(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\b(?:\s*(?:days?|months?|years?|percent|%))?)", item["line"])
            for token in numeric_tokens:
                if token.lower() not in metadata_pool:
                    numeric_mismatches.append(token)
                    unsupported_claims.append(item["line"])
            continue
        for evidence_id in item["evidence_ids"]:
            if evidence_id not in fact_map:
                unsupported_claims.append(item["line"])
                break
        numeric_tokens = re.findall(r"(?:\$[\d,]+(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\b(?:\s*(?:days?|months?|years?|percent|%))?)", item["line"])
        evidence_pool = " ".join(
            " ".join([
                fact_map[evidence_id]["section_ref"],
                fact_map[evidence_id]["heading"],
                fact_map[evidence_id]["fact_text"],
                fact_map[evidence_id]["support_snippet"],
                " ".join(fact_map[evidence_id]["dates_deadlines"]),
                " ".join(fact_map[evidence_id]["money_thresholds"]),
                " ".join(fact_map[evidence_id]["agencies_entities"]),
                " ".join(fact_map[evidence_id]["defined_terms"]),
            ])
            for evidence_id in item["evidence_ids"]
            if evidence_id in fact_map
        ).lower()
        for token in numeric_tokens:
            if token.lower() not in evidence_pool:
                numeric_mismatches.append(token)
                unsupported_claims.append(item["line"])

    unsupported_claims = list(dict.fromkeys(unsupported_claims))
    numeric_mismatches = list(dict.fromkeys(numeric_mismatches))
    if numeric_mismatches:
        flags.append("UNSUPPORTED_NUMERIC_CLAIMS")
    if unsupported_claims:
        flags.append("UNSUPPORTED_LINES")

    if bill_detail.get("number") and bill_detail["number"] not in summary:
        flags.append("BILL_NUMBER_NOT_REFERENCED")

    if flags:
        return {
            "summary_status": "blocked_verification",
            "verification_status": "blocked_verification",
            "validation_flags": flags,
            "unsupported_claims": unsupported_claims,
            "numeric_mismatches": numeric_mismatches,
        }

    return {
        "summary_status": "verified",
        "verification_status": "verified",
        "validation_flags": [],
        "unsupported_claims": [],
        "numeric_mismatches": [],
    }


def _build_metadata_verification_pool(bill_detail: dict[str, Any]) -> str:
    values = [
        str(bill_detail.get(key) or "")
        for key in ("number", "title", "state", "session", "status", "last_action", "last_action_date", "url", "state_url")
    ]
    if (bill_detail.get("state") or "").upper() == "US":
        values.append("Federal (US)")

    for entry in bill_detail.get("history") or []:
        if not isinstance(entry, dict):
            continue
        values.append(str(entry.get("action") or ""))
        values.append(str(entry.get("date") or ""))

    return " ".join(values).lower()


def _blocked_missing_source_result(bill_detail: dict, normalized: dict[str, Any], bill_text: str) -> dict[str, Any]:
    reason = "No complete usable bill text was available from the official bill record."
    if bill_text.startswith("[Full text not available."):
        reason = "The bill detail record did not provide usable full bill text."
    diagnostics = [
        f"source_status: unusable_text",
        f"reason: {reason}",
        f"bill_text_present: {'yes' if bool((bill_text or '').strip()) else 'no'}",
        f"normalization_flags: {', '.join(normalized['flags']) or 'none'}",
    ]
    return {
        "summary": "",
        "caveats": [reason],
        "summary_status": "blocked_missing_source",
        "source_text_status": "missing",
        "source_status": "unusable_text",
        "extraction_status": "not_run",
        "verification_status": "blocked_missing_source",
        "coverage_mode": "blocked_missing_source",
        "extraction_coverage": {"extracted_sections": 0, "total_sections": 0},
        "evidence_coverage": {"total_chunks": 0, "parsed_chunks": 0, "fact_count": 0, "amendment_fact_count": 0},
        "validation_flags": ["MISSING_USABLE_FULL_TEXT"],
        "unsupported_claims": [],
        "traceability_report": [],
        "model_path": {"extraction": _effective_model(EXTRACTION_MODEL), "synthesis": "not_run"},
        "evidence_index": [],
        "summary_structured": {"render_mode": "blocked_missing_source", "diagnostics": diagnostics},
    }


def _blocked_verification_result(
    *,
    bill_detail: dict,
    extraction: dict[str, Any],
    verification: dict[str, Any],
    normalized: dict[str, Any],
) -> dict[str, Any]:
    diagnostics = [
        f"source_status: verified_full_text",
        f"extraction_status: {extraction['extraction_status']}",
        f"parsed_chunks: {extraction['coverage']['parsed_chunks']}/{extraction['coverage']['total_chunks']}",
        f"fact_count: {extraction['coverage']['fact_count']}",
        f"normalization_flags: {', '.join(normalized['flags']) or 'none'}",
    ]
    return {
        "summary": "",
        "caveats": ["The tool could not produce a fully traceable source summary from the official bill text."],
        "summary_status": "blocked_verification",
        "source_text_status": "full",
        "source_status": "verified_full_text",
        "extraction_status": extraction["extraction_status"],
        "verification_status": verification["verification_status"],
        "coverage_mode": "blocked_verification",
        "extraction_coverage": {
            "extracted_sections": extraction["coverage"]["parsed_chunks"],
            "total_sections": extraction["coverage"]["total_chunks"],
        },
        "evidence_coverage": extraction["coverage"],
        "validation_flags": verification["validation_flags"],
        "unsupported_claims": verification["unsupported_claims"],
        "traceability_report": [],
        "model_path": {"extraction": _effective_model(EXTRACTION_MODEL), "synthesis": "deterministic_composer"},
        "evidence_index": extraction["fact_index"],
        "summary_structured": {"render_mode": "blocked_verification", "diagnostics": diagnostics},
    }


def format_bill_header(bill_detail: dict) -> str:
    sponsors = bill_detail.get("sponsors", [])
    primary = sponsors[:1]
    cosponsors = sponsors[1:]

    def _format_sponsor(sponsor: dict[str, Any]) -> str:
        parts = [sponsor.get("name", "Unknown")]
        if sponsor.get("party") or sponsor.get("role"):
            meta = " — ".join(filter(None, [sponsor.get("party"), sponsor.get("role")]))
            parts.append(f"({meta})")
        return " ".join(parts)

    primary_str = _format_sponsor(primary[0]) if primary else "Not available"
    cosponsor_lines = [f"  - {_format_sponsor(sponsor)}" for sponsor in cosponsors[:20]] or ["  - None"]
    if len(cosponsors) > 20:
        cosponsor_lines.append(f"  - ... and {len(cosponsors) - 20} more")

    state = bill_detail.get("state") or ""
    jurisdiction = "Federal (US)" if state.upper() == "US" else (state or "N/A")
    return f"""## Bill Overview

- **Number:** {bill_detail.get('number', 'N/A')}
- **Title:** {bill_detail.get('title', 'N/A')}
- **Jurisdiction:** {jurisdiction}
- **Session:** {bill_detail.get('session', 'N/A')}
- **Status:** {bill_detail.get('status', 'N/A')} (as of {bill_detail.get('status_date', 'N/A')})
- **Last Action:** {bill_detail.get('last_action', 'N/A')} ({bill_detail.get('last_action_date', 'N/A')})
- **Official URL:** {bill_detail.get('state_url', bill_detail.get('url', 'N/A'))}
- **Subjects:** {', '.join(bill_detail.get('subjects', [])) or 'Not specified'}

## Sponsors

### Primary Sponsor
  - {primary_str}

### Co-Sponsors ({len(cosponsors)})
{chr(10).join(cosponsor_lines)}"""
