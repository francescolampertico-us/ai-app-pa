"""
extractor.py — Stage 2: Extract structured hearing record from normalized text.

Two-pass LLM architecture:
  Pass 1 (ChangeAgent): extraction — pulls structured data from the transcript
    in one or more chunk calls, then merges results.
  Pass 2 (ChangeAgent): polish — rewrites the prose fields (overview, opening
    statement paragraphs, witness summaries, Q&A summaries) into final
    memo-ready language without altering structure or metadata.

Produces a HearingRecord conforming to schema/hearing_record.schema.json.
"""

import os
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional

try:
    from openai import OpenAI
    _api_key = os.environ.get("OPENAI_API_KEY")
    _base_url = os.environ.get("OPENAI_BASE_URL") or None  # None → use default OpenAI URL
    _openai_client = OpenAI(api_key=_api_key, base_url=_base_url, timeout=180) if _api_key else None
    print(f"[extractor] OpenAI client: api_key={'set' if _api_key else 'MISSING'}, base_url={_base_url or '(default OpenAI)'}", file=sys.stderr)
except ImportError:
    _openai_client = None
    print("[extractor] openai package not installed", file=sys.stderr)

from .config import (
    HEADING_OPENING_STATEMENTS,
    HEADING_OPENING_COCHAIRS,
    HEADING_WITNESS_SECTION,
)


# ---------------------------------------------------------------------------
# Data classes matching the schema
# ---------------------------------------------------------------------------

@dataclass
class SpeakerInfo:
    name: str
    role_display: str


@dataclass
class OpeningStatement:
    speaker: str
    summary_points: List[str]


@dataclass
class WitnessRecord:
    name: str
    affiliation: Optional[str]
    summary_points: List[str]
    recommendations: List[str] = field(default_factory=list)
    panel: Optional[str] = None


@dataclass
class QACluster:
    member: str
    topic: str
    summary: str
    commitments_or_requests: List[str] = field(default_factory=list)


@dataclass
class HearingRecord:
    metadata: dict
    structure: dict
    participants: dict
    overview_points: List[str]
    opening_statements: List[OpeningStatement]
    witnesses: List[WitnessRecord]
    qa_clusters: List[QACluster]
    uncertainties: List[str]

    def to_dict(self) -> dict:
        d = {
            "metadata": self.metadata,
            "structure": self.structure,
            "participants": self.participants,
            "overview_points": self.overview_points,
            "opening_statements": [asdict(s) for s in self.opening_statements],
            "witnesses": [asdict(w) for w in self.witnesses],
            "qa_clusters": [asdict(q) for q in self.qa_clusters],
            "uncertainties": self.uncertainties,
        }
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ---------------------------------------------------------------------------
# State abbreviation map (full names and common short forms)
# ---------------------------------------------------------------------------

STATE_ABBREV_MAP = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
    # Common short forms from transcripts
    "ala": "AL", "ariz": "AZ", "ark": "AR", "calif": "CA", "colo": "CO",
    "conn": "CT", "del": "DE", "fla": "FL", "ill": "IL", "ind": "IN",
    "kan": "KS", "mass": "MA", "mich": "MI", "minn": "MN", "miss": "MS",
    "neb": "NE", "nev": "NV", "okla": "OK", "ore": "OR", "penn": "PA",
    "tenn": "TN", "tex": "TX", "wash": "WA", "wis": "WI", "wyo": "WY",
    # Two-letter codes (already correct, but normalize case)
    "al": "AL", "ak": "AK", "az": "AZ", "ar": "AR", "ca": "CA", "co": "CO",
    "ct": "CT", "de": "DE", "fl": "FL", "ga": "GA", "hi": "HI", "id": "ID",
    "il": "IL", "in": "IN", "ia": "IA", "ks": "KS", "ky": "KY", "la": "LA",
    "me": "ME", "md": "MD", "ma": "MA", "mi": "MI", "mn": "MN", "ms": "MS",
    "mo": "MO", "mt": "MT", "ne": "NE", "nv": "NV", "nh": "NH", "nj": "NJ",
    "nm": "NM", "ny": "NY", "nc": "NC", "nd": "ND", "oh": "OH", "ok": "OK",
    "or": "OR", "pa": "PA", "ri": "RI", "sc": "SC", "sd": "SD", "tn": "TN",
    "tx": "TX", "ut": "UT", "vt": "VT", "va": "VA", "wa": "WA", "wv": "WV",
    "wi": "WI", "wy": "WY",
}


def _normalize_state(raw: str) -> str:
    """Normalize a state abbreviation like 'Fla.' or 'Conn.' to 'FL' or 'CT'."""
    cleaned = raw.strip().rstrip(".").lower()
    return STATE_ABBREV_MAP.get(cleaned, raw.upper()[:2])


# ---------------------------------------------------------------------------
# Single-pass LLM extraction
# ---------------------------------------------------------------------------

VIDEO_TRANSCRIPT_ADDENDUM = """

IMPORTANT — THIS IS A YOUTUBE AUTO-CAPTION TRANSCRIPT:
YouTube auto-captions are generated by automatic speech recognition (ASR). They commonly have:
- No consistent speaker labels; everything runs together
- Repeated consecutive words from ASR stutter (e.g., "the the committee")
- Missing punctuation and poor sentence boundaries
- No formatted committee headers or official hearing titles
- Partial or garbled witness introductions and affiliations

RULES FOR VIDEO TRANSCRIPT EXTRACTION:
1. SPEAKER IDENTITY: Only label a speaker if they are addressed by name in the text, introduce themselves, or their state/party is explicitly mentioned. If a speaker cannot be confidently identified, use "[SPEAKER UNCERTAIN]" as the speaker_heading. Do NOT guess from your general knowledge.
2. HEARING METADATA: If the committee name or hearing title is not explicitly stated in the text, return null for those fields and add a note in uncertainties. Do NOT infer or guess from context alone.
3. WITNESS AFFILIATIONS: Extract affiliations only if clearly stated during an introduction. If not stated, return null.
4. UNCERTAINTY: Add every uncertain identification to the "uncertainties" list. Be explicit: "Speaker around Q&A timestamp unclear — labeled SPEAKER UNCERTAIN."
5. ASR ARTIFACTS: Treat repeated consecutive words as a single word. Reconstruct meaning from context where words are clearly garbled.
"""

SYSTEM_PROMPT = """You are an expert congressional hearing analyst producing detailed professional memos. You will receive the full text of a congressional hearing transcript. Your job is to extract a complete structured record with SUBSTANTIAL DETAIL — the final memo should be 6 to 10 pages.

CRITICAL RULES:
1. Be SPECIFIC and SUBSTANTIVE in all summaries. Never write vague filler like "inquired about a specific topic" or "discussed the issue." Always name the actual policy, person, event, or proposal being discussed. Include specific facts, figures, and commitments mentioned.
2. Use correct senator/representative states — look them up from context or your knowledge. Example: Blumenthal is D-CT, not D-CO. Ernst is R-IA.
3. Identify Chairman/Ranking Member roles from how they are addressed in the transcript.
4. Distinguish between witnesses/nominees and members who introduce them.
5. If a member asks questions in multiple rounds, create SEPARATE entries for each round.
6. WITNESS AFFILIATIONS: Extract the affiliation EXACTLY as stated in the transcript introduction. Do NOT use your training knowledge to fill in or correct affiliations — if the transcript says "Center for Critical Mineral Strategy," write that exactly, even if you think they work somewhere else.
7. HEARING DATE: Extract the date string exactly as it appears in the document header or transcript (e.g., "03/25/2026" or "March 25, 2026"). Do NOT derive or guess the day of week — leave it as-is from the source.
8. PROCEDURAL ACTIONS: If the transcript includes motions, votes, subpoena requests, or other procedural actions at the end of the hearing, capture them in the "procedural_actions" field. Do NOT omit them.

LENGTH TARGETS (these are critical — write substantially, not telegraphically):
- Opening statements: 2-4 paragraphs per speaker, 150-300 words each. Cover the speaker's framing, specific concerns, proposals, and any cited facts or events.
- Witness testimony: 2-4 paragraphs per witness, 150-350 words each. Cover their main argument, key evidence, specific policy prescriptions and recommendations.
- Q&A exchanges: 1-4 paragraphs per member per round, 150-400 words each. Capture EACH question and its specific answer. If a senator asks 3 questions, write about all 3.
- Overview: 5-8 sentences, 150-200 words. DO NOT start with the committee/title/date — that is added separately. Write about TOPICS and THEMES only — no speaker attributions at all. Do NOT mention individual committee members or witnesses by name. Do NOT use generic role references either (e.g., "the chairman said", "witnesses testified", "senators pressed"). Instead write purely about what was discussed.
  GOOD example: "Discussion centered on AI safety regulation and workforce displacement. Key areas of inquiry included federal oversight frameworks, the adequacy of voluntary industry commitments, and projected job losses in manufacturing sectors."
  BAD example: "The chairman discussed AI safety. Witnesses testified about workforce displacement. Senators pressed for details on federal oversight."
  Weave the themes into flowing prose — do NOT write a literal list like "Key themes included X, Y, Z."

STYLE:
- ALWAYS write in professional third person. NEVER use first person ("I", "we", "my").
  WRONG: "I entered the Senate the same year that..."
  CORRECT: "Chairman Paul opened by reflecting on his personal experiences with..."
  WRONG: "Before starting my opening statement, I must address..."
  CORRECT: "Sen. Mullin addressed the Chairman's remarks directly, asserting that..."
- Each paragraph should carry one clear unit of meaning (2-4 sentences).
- Paraphrase by default. Use direct quotes only for especially distinctive or politically significant phrases.
- Be descriptive, not argumentative. Do not add your own policy implications or predictions.

Return a JSON object with this exact structure:
{
  "metadata": {
    "hearing_title": "Full official title of the hearing",
    "hearing_date": "Day of week, Month DD, YYYY",
    "hearing_time": "HH:MM AM/PM" or null,
    "committee_name": "Full committee name",
    "subcommittee_name": null or "subcommittee name"
  },
  "leadership_model": "chair_ranking_member" or "co_chairs" or "chair_only",
  "opening_statements": [
    {
      "speaker_heading": "Chairman FirstName LastName (R-XX)" or "Ranking Member FirstName LastName (D-XX)",
      "paragraphs": ["Paragraph 1 text...", "Paragraph 2 text...", "Paragraph 3 text..."]
    }
  ],
  "witnesses": [
    {
      "name": "Full name with title (e.g., Honorable Markwayne Mullin)",
      "role": "introducer" or "nominee" or "witness" or "expert",
      "affiliation": "Organization or position",
      "paragraphs": ["Paragraph 1...", "Paragraph 2...", "Paragraph 3..."]
    }
  ],
  "qa_exchanges": [
    {
      "member_heading": "Senator/Chairman/Ranking Member FirstName LastName (R/D-XX)",
      "round": 1,
      "paragraphs": ["Paragraph 1 about first question and answer...", "Paragraph 2 about second question and answer..."]
    }
  ],
  "procedural_actions": [
    {
      "action_type": "motion" or "vote" or "subpoena_request" or "unanimous_consent" or "other",
      "description": "Full description of the procedural action, who moved it, the outcome, and any vote tally."
    }
  ],
  "overview": {
    "themes": ["theme 1", "theme 2"],
    "summary": "A 5-8 sentence overview paragraph naming the committee, title, date, time, and major themes."
  }
}

IMPORTANT for qa_exchanges:
- Each paragraph should start with the senator's short form (e.g., "Sen. Blumenthal asked..." or "Chairman Paul challenged...").
- If a senator asks multiple separate questions in one round, write one paragraph per question-answer pair.
- If a senator returns for a second round, create a new entry with round: 2.
- Always capture what the witness/nominee actually said in response — include their specific answer, not just "the witness responded."
- Use the witness's name (e.g., "Hon. Mullin replied that..." or "Ms. Madan said that...") instead of generic "the witness."
- Include specific policy details, names, figures, and commitments in every exchange.
"""


VIDEO_PREPROCESS_SYSTEM = """You are analyzing a raw YouTube auto-caption transcript of a congressional hearing.
These transcripts lack speaker labels, structured headers, and may have ASR errors.

Extract only what is explicitly and reliably present in the text. Do not infer or guess.

Return JSON:
{
  "committee_name": "full committee name or null",
  "hearing_title": "hearing title or null",
  "hearing_date": "date as mentioned in the text or null",
  "hearing_time": "time as mentioned or null",
  "identified_speakers": [
    {
      "name": "Full Name",
      "role": "chairman|ranking_member|member|witness|unknown",
      "confidence": "high|medium|low",
      "evidence": "brief note on how this person was identified in the text"
    }
  ],
  "witnesses": [
    {
      "name": "Witness Name",
      "affiliation": "Organization name or null if not stated",
      "confidence": "high|medium|low"
    }
  ],
  "uncertainty_notes": ["specific things that are unclear or uncertain"]
}

Critical rules:
- Only name speakers explicitly addressed by name or who introduce themselves in the text
- Set confidence "low" if you are inferring from context rather than direct statement
- Return null for any metadata field not clearly stated in the text
- Add a note to uncertainty_notes for every uncertain identification"""


def _build_hints(metadata_candidates: dict) -> str:
    """Build metadata hints string from normalizer candidates.

    For YouTube sources, high-confidence pre-processing results are marked
    CONFIRMED (the LLM must use them verbatim). Medium/low-confidence results
    are marked HINT ONLY (advisory; the LLM must verify against the full text
    and must NOT use them if the transcript contradicts them).
    """
    if not metadata_candidates:
        return ""

    confirmed_lines: list[str] = []   # high-confidence — instruct LLM to treat as locked
    hint_lines: list[str] = []        # medium/low or rule-extracted — advisory only

    # Rule-extracted metadata from normalizer (treated as hints, not confirmed)
    for key in ("committee_name", "hearing_title", "hearing_date_long",
                 "date_mention", "publication_datetime"):
        val = metadata_candidates.get(key)
        if val:
            hint_lines.append(f"- {key}: {val}")

    # YouTube pre-processing results — split by confidence level
    yt_speakers = metadata_candidates.get("yt_identified_speakers", [])
    high_speakers = [s for s in yt_speakers if s.get("confidence") == "high"]
    weak_speakers = [s for s in yt_speakers if s.get("confidence") in ("medium", "low")]

    if high_speakers:
        lines = [
            f"  - {s['name']} ({s.get('role', 'unknown')}): {s.get('evidence', '')}"
            for s in high_speakers
        ]
        confirmed_lines.append(
            "CONFIRMED speakers (use these names and roles exactly):\n" + "\n".join(lines)
        )

    if weak_speakers:
        lines = [
            f"  - {s['name']} ({s.get('role', 'unknown')}, {s.get('confidence')} confidence): {s.get('evidence', '')}"
            for s in weak_speakers
        ]
        hint_lines.append(
            "HINT ONLY — unverified speakers (do NOT use if the transcript contradicts; "
            "label [SPEAKER UNCERTAIN] instead):\n" + "\n".join(lines)
        )

    # YouTube witnesses — split by confidence
    yt_witnesses = metadata_candidates.get("yt_witnesses", [])
    high_witnesses = [w for w in yt_witnesses if w.get("confidence") == "high"]
    weak_witnesses = [w for w in yt_witnesses if w.get("confidence") in ("medium", "low")]

    if high_witnesses:
        lines = [
            f"  - {w['name']} ({w.get('affiliation') or 'affiliation not stated'})"
            for w in high_witnesses
        ]
        confirmed_lines.append(
            "CONFIRMED witnesses (use these names and affiliations exactly):\n" + "\n".join(lines)
        )

    if weak_witnesses:
        lines = [
            f"  - {w['name']} ({w.get('affiliation') or 'affiliation unclear'}, {w.get('confidence')} confidence)"
            for w in weak_witnesses
        ]
        hint_lines.append(
            "HINT ONLY — unverified witnesses (do NOT use affiliation if not stated in transcript):\n"
            + "\n".join(lines)
        )

    if metadata_candidates.get("yt_uncertainty_notes"):
        hint_lines.append(
            "UNCERTAINTY NOTES: " + "; ".join(metadata_candidates["yt_uncertainty_notes"])
        )

    parts: list[str] = []
    if confirmed_lines:
        parts.append(
            "CONFIRMED METADATA (treat as locked — do not alter these values):\n"
            + "\n".join(confirmed_lines)
        )
    if hint_lines:
        parts.append(
            "ADVISORY HINTS (verify against the full transcript; do not override "
            "what the transcript actually says):\n"
            + "\n".join(hint_lines)
        )

    if parts:
        return "\n\nMetadata extracted from the document:\n" + "\n\n".join(parts)
    return ""


def _call_llm(user_prompt: str, model: str = None, system_prompt: str = None) -> dict:
    """Make a single LLM call and return parsed JSON."""
    model = model or os.environ.get("MEMO_MODEL", "ChangeAgent")
    system = system_prompt or SYSTEM_PROMPT

    # ChangeAgent does not support response_format or large max_tokens — skip them.
    use_change_agent = bool(os.environ.get("LLM_MODEL_OVERRIDE"))
    extra = {} if use_change_agent else {
        "max_tokens": int(os.environ.get("MEMO_MAX_TOKENS", 16000)),
        "response_format": {"type": "json_object"},
    }

    try:
        response = _openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            **extra,
        )
    except Exception as e:
        error_msg = str(e)
        if ("rate_limit" in error_msg or "429" in error_msg) and model != "ChangeAgent":
            print(f"Rate limited on {model}, falling back to ChangeAgent...", file=sys.stderr)
            response = _openai_client.chat.completions.create(
                model="ChangeAgent",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        else:
            raise

    raw = (response.choices[0].message.content or "").strip()
    # Strip markdown code fences if model didn't use response_format mode
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if m:
        raw = m.group(1).strip()
    # Fallback: extract the outermost JSON object if raw still has surrounding text
    if not raw.startswith("{"):
        m2 = re.search(r"\{[\s\S]+\}", raw)
        if m2:
            raw = m2.group(0)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"  JSON parse error in _call_llm: {exc}", file=sys.stderr)
        print(f"  Raw response (first 500 chars): {raw[:500]!r}", file=sys.stderr)
        raise


def _sample_video_excerpt(transcript: str, max_chars: int = 30_000) -> str:
    """Sample strategic sections of a video transcript for metadata pre-processing.

    YouTube hearings follow a predictable structure:
      - Opening (~0–10 min): committee name, hearing title, chairman introduction
      - Witness intros (~10–25 min): affiliations read into the record
      - Q&A: where speaker uncertainty is highest but identities less critical for metadata

    For long transcripts, we take the first 20K chars (opening + first witness intro)
    plus a 10K window centered at ~25% of the transcript (catches second-panel intros).
    For short transcripts we use the full text.
    """
    total = len(transcript)
    if total <= max_chars:
        return transcript

    head = transcript[:20_000]
    # 25% into the transcript typically captures witness introductions for the second panel
    mid_center = total // 4
    mid_start = max(20_000, mid_center - 5_000)
    mid_end = min(total, mid_start + 10_000)
    mid = transcript[mid_start:mid_end]

    divider = "\n\n[...transcript section omitted for pre-processing...]\n\n"
    return head + divider + mid


def _preprocess_video_transcript(transcript: str) -> dict:
    """Pre-pass to stabilize metadata from a raw YouTube caption transcript.

    Uses ChangeAgent (same model as main extraction) for consistency.
    Samples the opening + a mid-point window to capture both opening metadata
    and witness introductions that appear after chairman remarks.
    Returns enriched metadata dict or empty dict on failure.
    """
    if not _openai_client:
        return {}
    excerpt = _sample_video_excerpt(transcript)
    model = os.environ.get("MEMO_MODEL", "ChangeAgent")
    try:
        print(f"  YouTube pre-processing pass ({model}, {len(excerpt)} chars)...", file=sys.stderr)
        preprocess_extra = {} if os.environ.get("LLM_MODEL_OVERRIDE") else {
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
        }
        response = _openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": VIDEO_PREPROCESS_SYSTEM},
                {"role": "user", "content": (
                    "Extract metadata and speaker identifications from this "
                    "YouTube auto-caption transcript excerpt:\n\n" + excerpt
                )},
            ],
            temperature=0.1,
            **preprocess_extra,
        )
        raw_pre = (response.choices[0].message.content or "").strip()
        m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw_pre)
        if m:
            raw_pre = m.group(1).strip()
        if not raw_pre.startswith("{"):
            m2 = re.search(r"\{[\s\S]+\}", raw_pre)
            if m2:
                raw_pre = m2.group(0)
        result = json.loads(raw_pre)
        print(
            f"  YouTube pre-processing: {len(result.get('identified_speakers', []))} speakers, "
            f"{len(result.get('witnesses', []))} witnesses, "
            f"{len(result.get('uncertainty_notes', []))} uncertainty notes",
            file=sys.stderr,
        )
        return result
    except Exception as e:
        print(f"  YouTube pre-processing failed ({e}), proceeding without.", file=sys.stderr)
        return {}


def _merge_results(part1: dict, part2: dict) -> dict:
    """Merge two partial extraction results into one complete record."""
    # Use part1 as the base (it has metadata, opening statements, witnesses, early Q&A)
    merged = {
        "metadata": part1.get("metadata", {}),
        "leadership_model": part1.get("leadership_model", "chair_ranking_member"),
        "opening_statements": part1.get("opening_statements", []),
        "witnesses": part1.get("witnesses", []),
        "qa_exchanges": list(part1.get("qa_exchanges", [])),
        "overview": part1.get("overview", {}),
    }

    # Merge opening statements from part2 (dedup by speaker_heading)
    existing_speakers = {s.get("speaker_heading", "").lower() for s in merged["opening_statements"]}
    for stmt in part2.get("opening_statements", []):
        if stmt.get("speaker_heading", "").lower() not in existing_speakers:
            merged["opening_statements"].append(stmt)
            existing_speakers.add(stmt.get("speaker_heading", "").lower())

    # Add Q&A exchanges from part2 that aren't duplicates
    existing_members = set()
    for ex in merged["qa_exchanges"]:
        key = (ex.get("member_heading", ""), ex.get("round", 1))
        existing_members.add(key)

    for ex in part2.get("qa_exchanges", []):
        key = (ex.get("member_heading", ""), ex.get("round", 1))
        if key not in existing_members:
            merged["qa_exchanges"].append(ex)
            existing_members.add(key)

    # Add any witnesses from part2 not already present
    existing_witnesses = {w.get("name", "").lower() for w in merged["witnesses"]}
    for w in part2.get("witnesses", []):
        if w.get("name", "").lower() not in existing_witnesses:
            merged["witnesses"].append(w)

    # Merge overview themes
    themes1 = set(merged.get("overview", {}).get("themes", []))
    themes2 = set(part2.get("overview", {}).get("themes", []))
    merged["overview"]["themes"] = list(themes1 | themes2)

    return merged


def _find_split_point(text: str, target_pos: int, search_radius: int = 2000) -> int:
    """Find a paragraph break near the target position."""
    start = max(target_pos - search_radius, 0)
    end = min(target_pos + search_radius, len(text))
    region = text[start:end]
    split_pos = region.rfind("\n\n")
    if split_pos == -1:
        split_pos = region.rfind("\n")
    if split_pos == -1:
        split_pos = len(region) // 2
    return start + split_pos


def _extract_via_llm(transcript: str, metadata_candidates: dict,
                     source_profile: str = "generic_text") -> dict:
    """Extract structured hearing record via LLM.

    For transcripts that exceed rate limits (~30K TPM on Tier 1),
    splits into multiple sequential calls and merges results.
    """
    if not _openai_client:
        raise RuntimeError(
            "OpenAI API key not set. Set OPENAI_API_KEY environment variable."
        )

    hints = _build_hints(metadata_candidates)
    model = os.environ.get("MEMO_MODEL", "ChangeAgent")

    # Build system prompt — append video addendum for YouTube sources
    system = SYSTEM_PROMPT
    if source_profile == "video_transcript":
        system = SYSTEM_PROMPT + VIDEO_TRANSCRIPT_ADDENDUM

    # Safe input budget per call: ~15K tokens input = ~60K chars.
    # This leaves room for system prompt (~3K tokens) + output (16K tokens)
    # while staying within Tier 1 30K TPM limit per call.
    max_chunk_chars = int(os.environ.get("MEMO_MAX_CHARS", 60_000))

    if len(transcript) <= max_chunk_chars:
        # Single call — transcript fits within limits
        user_prompt = (
            f"Extract the structured hearing record from this transcript.{hints}"
            f"\n\n---TRANSCRIPT START---\n{transcript}\n---TRANSCRIPT END---"
        )
        return _call_llm(user_prompt, model, system_prompt=system)

    # --- Determine number of chunks needed ---
    num_chunks = (len(transcript) // max_chunk_chars) + 1
    num_chunks = max(num_chunks, 2)
    print(f"Transcript is {len(transcript)} chars — splitting into {num_chunks} calls...", file=sys.stderr)

    # Find split points at paragraph breaks
    chunk_size = len(transcript) // num_chunks
    split_points = [0]
    for i in range(1, num_chunks):
        target = chunk_size * i
        split_points.append(_find_split_point(transcript, target))
    split_points.append(len(transcript))

    OVERLAP_CHARS = 2000
    chunks = []
    for i in range(num_chunks):
        start = split_points[i]
        if i > 0:
            start = max(split_points[i] - OVERLAP_CHARS, split_points[i - 1])
        chunks.append(transcript[start:split_points[i + 1]])

    # --- Call 1: First chunk (opening statements, witnesses, early Q&A) ---
    prompt1 = (
        f"Extract the structured hearing record from this transcript (PART 1 of {num_chunks} — "
        f"this is the beginning of the hearing, including opening statements, witness testimony, and early Q&A).{hints}"
        f"\n\n---TRANSCRIPT PART 1 START---\n{chunks[0]}\n---TRANSCRIPT PART 1 END---"
    )
    print("  Extracting Part 1...", file=sys.stderr)
    merged = _call_llm(prompt1, model, system_prompt=system)

    # --- Subsequent chunks: Q&A continuation ---
    for chunk_idx in range(1, num_chunks):
        # Build context from all previous results
        covered_members = []
        for ex in merged.get("qa_exchanges", []):
            h = ex.get("member_heading", "")
            if h:
                covered_members.append(h)

        witness_names = ", ".join(w.get("name", "") for w in merged.get("witnesses", []))
        hearing_title = merged.get("metadata", {}).get("hearing_title", "the topic")

        context = (
            f"\n\nContext from previous parts: The hearing is about {hearing_title}. "
            f"The nominee/witness is {witness_names}. "
            f"Senators already covered (DO NOT repeat unless they return for a new round): "
            f"{', '.join(covered_members)}."
        )

        prompt_n = (
            f"Extract the structured hearing record from this transcript (PART {chunk_idx + 1} of {num_chunks} — "
            f"this is a continuation of the hearing). "
            f"Extract ALL content you find in this part: opening statements, witness testimony, AND Q&A exchanges. "
            f"For Q&A, the senators listed below are already covered — avoid duplicating their exchanges "
            f"unless they return for a new round of questioning.{context}{hints}"
            f"\n\n---TRANSCRIPT PART {chunk_idx + 1} START---\n{chunks[chunk_idx]}\n---TRANSCRIPT PART {chunk_idx + 1} END---"
        )
        print(f"  Extracting Part {chunk_idx + 1}...", file=sys.stderr)
        result_n = _call_llm(prompt_n, model, system_prompt=system)
        merged = _merge_results(merged, result_n)

    print(f"  Merged: {len(merged['qa_exchanges'])} total Q&A entries", file=sys.stderr)
    return merged


# ---------------------------------------------------------------------------
# Fallback: rule-based extraction (no LLM)
# ---------------------------------------------------------------------------

def _extract_fallback(transcript: str, metadata_candidates: dict) -> dict:
    """Minimal rule-based extraction when no LLM is available."""
    return {
        "metadata": {
            "hearing_title": metadata_candidates.get("hearing_title"),
            "hearing_date": metadata_candidates.get("hearing_date_long")
                            or metadata_candidates.get("date_mention"),
            "hearing_time": None,
            "committee_name": metadata_candidates.get("committee_name"),
            "subcommittee_name": None,
        },
        "leadership_model": "chair_ranking_member",
        "opening_statements": [],
        "witnesses": [],
        "qa_exchanges": [],
        "overview": {
            "themes": [],
            "summary": "LLM extraction unavailable. Please set OPENAI_API_KEY.",
        },
    }


# ---------------------------------------------------------------------------
# Pass 2: prose polish via ChangeAgent
# ---------------------------------------------------------------------------

POLISH_MODEL = "ChangeAgent"

POLISH_PROMPT = """You are a senior congressional staff writer reviewing a hearing memo draft.
You will receive a JSON record extracted from a congressional hearing transcript.
Your task is to polish ONLY the prose text fields — making them clear, authoritative, and memo-ready — while preserving ALL structure, metadata, and speaker names exactly as given.

Polish these fields only:
- overview.summary — rewrite as a tight, authoritative paragraph (5–7 sentences)
- opening_statements[*].paragraphs — each entry should be a substantive, professional bullet-point summary
- witnesses[*].paragraphs — same standard
- qa_exchanges[*].paragraphs — each entry should be a concise, professional summary of the exchange

Rules:
- Do NOT change any names, dates, committee titles, or metadata fields
- Do NOT add or remove entries from any list
- Do NOT change JSON structure or field names
- Return valid JSON only, identical structure to the input"""


def _polish_extracted(llm_output: dict) -> dict:
    """Pass 2: refine prose sections with gpt-4.1. Falls back silently on any error."""
    if not _openai_client:
        return llm_output
    try:
        print("  Polish pass (ChangeAgent)...", file=sys.stderr)
        polish_extra = {} if os.environ.get("LLM_MODEL_OVERRIDE") else {
            "max_tokens": 16000,
            "response_format": {"type": "json_object"},
        }
        response = _openai_client.chat.completions.create(
            model=POLISH_MODEL,
            messages=[
                {"role": "system", "content": POLISH_PROMPT},
                {"role": "user", "content": json.dumps(llm_output, indent=2)},
            ],
            temperature=0.3,
            **polish_extra,
        )
        raw_pol = (response.choices[0].message.content or "").strip()
        m = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw_pol)
        if m:
            raw_pol = m.group(1).strip()
        if not raw_pol.startswith("{"):
            m2 = re.search(r"\{[\s\S]+\}", raw_pol)
            if m2:
                raw_pol = m2.group(0)
        polished = json.loads(raw_pol)
        # Safety net: restore any top-level keys lost in the polish pass
        for key in ("metadata", "leadership_model", "opening_statements",
                    "witnesses", "qa_exchanges", "overview"):
            if key in llm_output and key not in polished:
                polished[key] = llm_output[key]
        return polished
    except Exception as e:
        print(f"  Polish pass failed ({e}), using draft extraction.", file=sys.stderr)
        return llm_output


# ---------------------------------------------------------------------------
# Convert LLM output to HearingRecord
# ---------------------------------------------------------------------------

def _build_hearing_record(llm_output: dict, metadata_candidates: dict,
                           source_profile: str) -> HearingRecord:
    """Convert the LLM JSON output into a HearingRecord object."""
    uncertainties: List[str] = []

    # --- Metadata ---
    llm_meta = llm_output.get("metadata", {})
    hearing_title = llm_meta.get("hearing_title") or metadata_candidates.get("hearing_title")
    hearing_date = llm_meta.get("hearing_date") or metadata_candidates.get("hearing_date_long") or metadata_candidates.get("date_mention")
    hearing_time = llm_meta.get("hearing_time")
    committee_name = llm_meta.get("committee_name") or metadata_candidates.get("committee_name")

    if not hearing_title:
        uncertainties.append("Hearing title not detected")
    if not hearing_date:
        uncertainties.append("Hearing date not detected")
    if not committee_name:
        uncertainties.append("Committee name not detected")

    source_quality = "mostly_clean"
    if source_profile in ("video_transcript",):
        source_quality = "noisy"
    elif source_profile == "cleaned_notes":
        source_quality = "clean"

    metadata = {
        "hearing_title": hearing_title,
        "hearing_date": hearing_date,
        "hearing_time": hearing_time,
        "memo_date": None,
        "committee_name": committee_name,
        "subcommittee_name": llm_meta.get("subcommittee_name"),
        "subject_line": None,
        "source_quality": source_quality,
    }

    # --- Structure ---
    leadership_model = llm_output.get("leadership_model", "chair_ranking_member")
    if leadership_model == "co_chairs":
        opening_heading = HEADING_OPENING_COCHAIRS
    else:
        opening_heading = HEADING_OPENING_STATEMENTS

    structure = {
        "opening_heading": opening_heading,
        "witness_heading": HEADING_WITNESS_SECTION,
        "hearing_format": "committee_hearing",
        "leadership_model": leadership_model,
        "panel_count": 1,
        "has_qa_section": True,
    }

    # --- Opening Statements ---
    opening_statements: List[OpeningStatement] = []
    for stmt in llm_output.get("opening_statements", []):
        heading = stmt.get("speaker_heading", "Unknown")
        paragraphs = stmt.get("paragraphs", [])
        opening_statements.append(
            OpeningStatement(speaker=heading, summary_points=paragraphs)
        )

    # --- Witnesses ---
    witness_records: List[WitnessRecord] = []
    for w in llm_output.get("witnesses", []):
        name = w.get("name", "Unknown")
        affiliation = w.get("affiliation")
        role = w.get("role", "witness")
        paragraphs = w.get("paragraphs", [])

        witness_records.append(WitnessRecord(
            name=name,
            affiliation=affiliation,
            summary_points=paragraphs,
            recommendations=[],
            panel=role,
        ))

    # --- Q&A ---
    qa_clusters: List[QACluster] = []
    for ex in llm_output.get("qa_exchanges", []):
        member_heading = ex.get("member_heading", "Unknown")
        round_num = ex.get("round", 1)
        paragraphs = ex.get("paragraphs", [])

        # Add round indicator if round > 1
        display_heading = member_heading
        if round_num > 1:
            display_heading = f"{member_heading} (Round {round_num})"

        summary_text = "\n\n".join(paragraphs)

        qa_clusters.append(QACluster(
            member=display_heading,
            topic="",
            summary=summary_text,
            commitments_or_requests=[],
        ))

    # --- Overview ---
    overview_data = llm_output.get("overview", {})
    overview_summary = overview_data.get("summary", "")
    themes = overview_data.get("themes", [])
    overview_points = [overview_summary]

    # --- Participants ---
    leadership = []
    members = []
    for stmt in opening_statements:
        leadership.append({"name": stmt.speaker, "role_display": stmt.speaker})
    for qa in qa_clusters:
        members.append({"name": qa.member, "role_display": qa.member})

    participants = {
        "leadership": leadership,
        "members": members,
    }

    return HearingRecord(
        metadata=metadata,
        structure=structure,
        participants=participants,
        overview_points=overview_points,
        opening_statements=opening_statements,
        witnesses=witness_records,
        qa_clusters=qa_clusters,
        uncertainties=uncertainties,
    )


# ---------------------------------------------------------------------------
# Main extraction entry point
# ---------------------------------------------------------------------------

def extract(cleaned_text: str, metadata_candidates: dict,
            source_profile: str) -> HearingRecord:
    """Build a structured HearingRecord from normalized text.

    For video_transcript sources: runs a YouTube-specific pre-processing pass
    first to stabilize metadata and speaker identity before main extraction.
    Falls back to rule-based extraction if no API key is set.
    """
    # YouTube pre-processing: stabilize metadata before main extraction
    if source_profile == "video_transcript":
        yt_meta = _preprocess_video_transcript(cleaned_text)
        if yt_meta:
            if yt_meta.get("committee_name") and not metadata_candidates.get("committee_name"):
                metadata_candidates["committee_name"] = yt_meta["committee_name"]
            if yt_meta.get("hearing_title") and not metadata_candidates.get("hearing_title"):
                metadata_candidates["hearing_title"] = yt_meta["hearing_title"]
            if yt_meta.get("hearing_date") and not metadata_candidates.get("date_mention"):
                metadata_candidates["date_mention"] = yt_meta["hearing_date"]
            if yt_meta.get("identified_speakers"):
                metadata_candidates["yt_identified_speakers"] = yt_meta["identified_speakers"]
            if yt_meta.get("witnesses"):
                metadata_candidates["yt_witnesses"] = yt_meta["witnesses"]
            if yt_meta.get("uncertainty_notes"):
                metadata_candidates["yt_uncertainty_notes"] = yt_meta["uncertainty_notes"]

    extraction_error: str | None = None
    try:
        llm_output = _extract_via_llm(cleaned_text, metadata_candidates, source_profile)
        llm_output = _polish_extracted(llm_output)
    except RuntimeError as e:
        extraction_error = str(e)
        print(f"LLM unavailable: {extraction_error}", file=sys.stderr)
        llm_output = _extract_fallback(cleaned_text, metadata_candidates)
    except Exception as e:
        extraction_error = str(e)
        print(f"LLM extraction error: {extraction_error}", file=sys.stderr)
        llm_output = _extract_fallback(cleaned_text, metadata_candidates)

    if extraction_error:
        # Propagate the error into the output so it surfaces in the memo/verification
        llm_output.setdefault("overview", {})
        llm_output["overview"]["summary"] = (
            f"LLM extraction failed: {extraction_error}. "
            "Check that OPENAI_API_KEY / ChangeAgent credentials are set correctly "
            "and that the model can be reached."
        )

    return _build_hearing_record(llm_output, metadata_candidates, source_profile)
