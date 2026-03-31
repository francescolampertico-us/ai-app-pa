"""
extractor.py — Stage 2: Extract structured hearing record from normalized text.

Single-pass LLM architecture: sends the full transcript to GPT-4o and receives
a complete structured hearing record in one call. This gives the model full
context across all speakers, exchanges, and themes — producing far more accurate
and substantive summaries than per-exchange calls.

Produces a HearingRecord conforming to schema/hearing_record.schema.json.
"""

import os
import json
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional

try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) if os.environ.get("OPENAI_API_KEY") else None
except ImportError:
    _openai_client = None

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

SYSTEM_PROMPT = """You are an expert congressional hearing analyst producing detailed professional memos. You will receive the full text of a congressional hearing transcript. Your job is to extract a complete structured record with SUBSTANTIAL DETAIL — the final memo should be 6 to 10 pages.

CRITICAL RULES:
1. Be SPECIFIC and SUBSTANTIVE in all summaries. Never write vague filler like "inquired about a specific topic" or "discussed the issue." Always name the actual policy, person, event, or proposal being discussed. Include specific facts, figures, and commitments mentioned.
2. Use correct senator states — look them up from context or your knowledge. Example: Blumenthal is D-CT, not D-CO. Ernst is R-IA.
3. Identify Chairman/Ranking Member roles from how they are addressed in the transcript.
4. Distinguish between witnesses/nominees and senators who introduce them.
5. If a senator asks questions in multiple rounds, create SEPARATE entries for each round.

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


def _build_hints(metadata_candidates: dict) -> str:
    """Build metadata hints string from normalizer candidates."""
    if not metadata_candidates:
        return ""
    hint_parts = []
    for key in ("committee_name", "hearing_title", "hearing_date_long",
                 "date_mention", "publication_datetime"):
        val = metadata_candidates.get(key)
        if val:
            hint_parts.append(f"- {key}: {val}")
    if hint_parts:
        return "\n\nMetadata hints extracted from the document:\n" + "\n".join(hint_parts)
    return ""


def _call_llm(user_prompt: str, model: str = None) -> dict:
    """Make a single LLM call and return parsed JSON."""
    model = model or os.environ.get("MEMO_MODEL", "gpt-4o-mini")

    try:
        response = _openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=int(os.environ.get("MEMO_MAX_TOKENS", 16000)),
            response_format={"type": "json_object"},
        )
    except Exception as e:
        error_msg = str(e)
        if ("rate_limit" in error_msg or "429" in error_msg) and model != "gpt-4o-mini":
            print(f"Rate limited on {model}, falling back to gpt-4o-mini...", file=sys.stderr)
            response = _openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=int(os.environ.get("MEMO_MAX_TOKENS", 16000)),
                response_format={"type": "json_object"},
            )
        else:
            raise

    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


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


def _extract_via_llm(transcript: str, metadata_candidates: dict) -> dict:
    """Extract structured hearing record via LLM.

    For transcripts that exceed rate limits (~30K TPM on Tier 1),
    splits into multiple sequential calls and merges results.
    """
    if not _openai_client:
        raise RuntimeError(
            "OpenAI API key not set. Set OPENAI_API_KEY environment variable."
        )

    hints = _build_hints(metadata_candidates)
    model = os.environ.get("MEMO_MODEL", "gpt-4o-mini")

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
        return _call_llm(user_prompt, model)

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
    merged = _call_llm(prompt1, model)

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
        result_n = _call_llm(prompt_n, model)
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

    Uses single-pass GPT-4o extraction for maximum accuracy.
    Falls back to rule-based extraction if no API key is set.
    """
    try:
        llm_output = _extract_via_llm(cleaned_text, metadata_candidates)
    except RuntimeError as e:
        print(f"LLM unavailable: {e}", file=sys.stderr)
        llm_output = _extract_fallback(cleaned_text, metadata_candidates)
    except Exception as e:
        print(f"LLM extraction error: {e}", file=sys.stderr)
        llm_output = _extract_fallback(cleaned_text, metadata_candidates)

    return _build_hearing_record(llm_output, metadata_candidates, source_profile)
