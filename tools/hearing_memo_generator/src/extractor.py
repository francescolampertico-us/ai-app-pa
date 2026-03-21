"""
extractor.py — Stage 2: Extract structured hearing record from normalized text.

Produces a HearingRecord conforming to schema/hearing_record.schema.json.
"""

import os
import re
import json
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple

try:
    from openai import OpenAI
    # Use a global client so we don't re-init on every call
    import os
    _openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) if os.environ.get("OPENAI_API_KEY") else None
except ImportError:
    _openai_client = None

from .config import (
    HEADING_OPENING_STATEMENTS,
    HEADING_OPENING_COCHAIRS,
    HEADING_WITNESS_SECTION,
    HEADING_QA,
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
# Speaker / section detection helpers
# ---------------------------------------------------------------------------

# Regex for speaker label lines (on their own line)
SPEAKER_LINE_RE = re.compile(
    r"^((?:Sen\.|Senator|Rep\.|Representative|Chairman|Chairwoman|"
    r"Ranking Member|Full Committee Ranking Member|Commissioner|"
    r"Mr\.|Ms\.|Dr\.|Hon\.|Honorable)\s+"
    r"[A-Z][a-zA-Z.']+(?:\s+[A-Z][a-zA-Z.']+)*"
    r"(?:\s+\([RD]-[A-Za-z.]+\))?)\s*$",
    re.MULTILINE
)

# Bare name on its own line (witnesses without a title prefix)
BARE_NAME_RE = re.compile(
    r"^([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?(?:\s+[A-Z][a-z]+)+)\s*$",
    re.MULTILINE
)


def _detect_leadership_model(text: str) -> str:
    """Detect whether the hearing uses co-chairs or chair/ranking member."""
    text_lower = text[:10000].lower()
    if "co-chair" in text_lower:
        return "co_chairs"
    # Check for commissioner-led hearings
    commissioner_lines = len(re.findall(r"^Commissioner\s+", text[:10000], re.MULTILINE))
    chairman_count = text_lower.count("chairman") + text_lower.count("chairwoman")
    if commissioner_lines > chairman_count and commissioner_lines > 3:
        return "co_chairs"
    if "ranking member" in text_lower:
        return "chair_ranking_member"
    if "chairman" in text_lower or "chairwoman" in text_lower:
        return "chair_only"
    return "other"


def _detect_leadership_from_context(text: str) -> Dict[str, str]:
    """Detect which speakers hold leadership roles from body text context.

    Scans for patterns like "Chairman Scott", "Ranking Member Gillibrand"
    and maps last names back to full speaker labels.

    Returns: dict mapping lowercase last name -> role string
    """
    roles = {}

    # Chairman/Chairwoman — match "Chairman [LastName]"
    for match in re.finditer(
        r"(?:Chairman|Chairwoman)\s+([A-Z][a-z]+)(?:\s|,|\.|$)", text[:15000]
    ):
        roles[match.group(1).lower()] = "Chairman"

    # Ranking Member — match "Ranking Member [FirstName LastName]" or "Ranking Member [LastName]"
    for match in re.finditer(
        r"Ranking Member\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text[:15000]
    ):
        # Use the LAST word as the key
        name_parts = match.group(1).split()
        last_name = name_parts[-1].lower()
        # Skip if this is clearly a first name match only  
        if len(name_parts) == 1:
            roles[last_name] = "Ranking Member"
        else:
            # Use the real last name
            roles[name_parts[-1].lower()] = "Ranking Member"

    # Commissioner (for co-chair hearings)
    for match in re.finditer(
        r"Commissioner\s+([A-Z][a-z]+)", text[:15000]
    ):
        roles[match.group(1).lower()] = "Commissioner"

    return roles


def _split_by_speakers(text: str) -> List[Dict[str, str]]:
    """Split text into segments by speaker labels.

    Returns list of {speaker: ..., text: ...} dicts.
    """
    segments = []
    lines = text.split("\n")
    current_speaker = None
    current_text = []

    for line in lines:
        stripped = line.strip()

        # Check for titled speaker label line
        is_titled = bool(SPEAKER_LINE_RE.match(stripped))

        # Check for bare name (2-4 capitalized words, standing alone)
        is_bare = False
        if not is_titled and stripped:
            is_bare = bool(BARE_NAME_RE.match(stripped))
            # Exclude lines that are too long to be speaker labels
            if is_bare and len(stripped) > 60:
                is_bare = False
            # Exclude common false positives (section headings, etc.)
            if is_bare:
                words = stripped.split()
                # If all words are capitalized normal words (not function words), treat as name
                if len(words) < 2 or len(words) > 4:
                    is_bare = False

        if is_titled or is_bare:
            # Save previous segment
            if current_speaker:
                segments.append({
                    "speaker": current_speaker,
                    "text": "\n".join(current_text).strip()
                })
            current_speaker = stripped
            current_text = []
        else:
            current_text.append(line)

    # Save last segment
    if current_speaker:
        segments.append({
            "speaker": current_speaker,
            "text": "\n".join(current_text).strip()
        })

    return segments

def _llm_summarize(text: str, speaker_name: str, context: str = "opening") -> str:
    """Use an LLM (OpenAI) to generate a third-person narrative summary matching the reference style."""
    
    # Strip (R-Fla.) style suffixes before getting the last name
    clean_name = re.sub(r'\s*\([RD]-[A-Za-z.]+\)\s*$', '', speaker_name).strip()
    last_name = clean_name.split()[-1]
    
    # Determine the role prefix
    if "Rep." in speaker_name or "Represent" in speaker_name:
        prefix = f"Rep. {last_name}"
    elif "Sen." in speaker_name or "Senator" in speaker_name:
        prefix = f"Sen. {last_name}"
    elif "Chairman" in speaker_name or "Chairwoman" in speaker_name:
        prefix = f"Chairman {last_name}"
    elif "Ranking Member" in speaker_name:
        prefix = f"Ranking Member {last_name}"
    else:
        # For witnesses, use Mr./Ms./Dr. based on basic heuristic
        prefix = f"Mr./Ms. {last_name}"
        if "Dr." in clean_name:
            prefix = f"Dr. {last_name}"

    if not _openai_client:
        # Fallback if no API key or openai library is missing
        words = text.split()
        snippet = " ".join(words[:15]) + "..." if len(words) > 15 else text
        snippet = snippet.replace('\n', ' ')
        if context == "qa_question":
            return f"{prefix} asked about the issues, noting: \"{snippet}\""
        elif context == "qa_response":
            return f"{prefix} replied: \"{snippet}\""
        return f"{prefix} discussed the issue, noting: \"{snippet}\""

    # Prepare prompt based on context
    system_prompt = (
        "You are an expert congressional hearing note-taker writing a formal Mercury-style memo. "
        "Your task is to summarize the provided transcript segment objectively in the third-person. "
        "Write exactly ONE strict, concise paragraph. Do not use bullets. Do not use direct quotes. "
        "Remove conversational pleasantries. Focus entirely on the substantive arguments and questions. "
        "Maintain a neutral, professional, objective tone."
    )

    if context == "opening":
        user_prompt = f"Summarize this opening statement by {prefix}. Emphasize their key arguments, concerns, or legislative priorities regarding the topic:\\n\\n{text}\\n\\nRule: Start your response with '{prefix} emphasized...' or '{prefix} outlined...'"
    elif context == "witness":
        user_prompt = f"Summarize this witness testimony by {prefix}. Highlight their core arguments, specific risks identified, and any explicit policy recommendations they made to Congress:\\n\\n{text}\\n\\nRule: Start your response with '{prefix} testified that...' or '{prefix} argued...'"
    elif context == "qa_exchange":
        # Text is the combined interaction. Pass instructions to write it cohesively
        user_prompt = f"Summarize this Q&A exchange. The member ({prefix}) asks a question or makes a point, and the witness responds. Summarize the interaction in 1 or 2 concise sentences (e.g., '{prefix} asked [Witness] about [Topic]. [Witness] replied/suggested [Answer].'):\\n\\n{text}"
    else:
        user_prompt = f"Summarize what {prefix} said:\\n\\n{text}"

    try:
        response = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        summary = response.choices[0].message.content.strip()
        
        # Enforce the prefix for non-QA exchange contexts if the LLM hallucinates
        if context != "qa_exchange" and not summary.startswith(prefix):
            words = summary.split()
            if words[0].lower() in ("he", "she", "they", "the"):
                summary = f"{prefix} {' '.join(words[1:])}"
            else:
                summary = f"{prefix} {summary}"
                
        return summary
    except Exception as e:
        print(f"LLM Error: {e}", file=sys.stderr)
        return f"{prefix} exchanged views on the issue."

def _extract_witness_info(name: str, text: str) -> WitnessRecord:
    """Extract witness information from a text segment."""
    affiliation = None

    # Check for comma-separated affiliation
    if "," in name:
        parts = name.split(",", 1)
        name = parts[0].strip()
        affiliation = parts[1].strip()

    # Generate the LLM witness summary
    summary_paragraph = _llm_summarize(text, name, context="witness")
    points = [summary_paragraph]

    # Extract recommendations
    recommendations = []
    rec_patterns = [
        r"(?:recommend|urge|propose|advocate|call for|suggest)\w*\s+(?:that\s+)?(.+?)(?:\.|$)",
    ]
    for pattern in rec_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            rec = match.group(1).strip()
            if len(rec) > 20:
                recommendations.append(rec)

    return WitnessRecord(
        name=name,
        affiliation=affiliation,
        summary_points=points if points else [text[:200]],
        recommendations=recommendations[:5],
    )


def _extract_overview_points(text: str, metadata: dict) -> List[str]:
    """Generate high-level overview points from the hearing text."""
    points = []

    committee = metadata.get("committee_name", "The committee")
    title = metadata.get("hearing_title", "the hearing")
    date = metadata.get("hearing_date", "")
    time = metadata.get("hearing_time", "")

    context = f'{committee} held a hearing titled "{title}"'
    if date:
        context += f" on {date}"
    if time:
        context += f" at {time}"
    points.append(context)

    # Scan for major themes
    theme_signals = [
        (r"(?:national security|security risk)", "national security implications"),
        (r"(?:supply chain|manufacturing|domestic production)", "supply chain vulnerabilities and domestic manufacturing"),
        (r"(?:China|Chinese|CCP|Communist China|Beijing)", "China's role in the pharmaceutical supply chain"),
        (r"(?:FDA|pharmaceutical|drug|medicine|generic)", "pharmaceutical oversight and drug safety"),
        (r"(?:legislation|act|bill|reform)", "legislative and policy reform proposals"),
        (r"(?:oversight|transparency|accountability)", "oversight and transparency measures"),
        (r"(?:innovation|biotechnology|biotech)", "biotechnology innovation"),
    ]

    detected_themes = []
    text_lower = text[:15000].lower()
    for pattern, theme in theme_signals:
        if re.search(pattern, text_lower):
            detected_themes.append(theme)

    if detected_themes:
        points.append(f"Key themes included {', '.join(detected_themes[:5])}")

    return points


# ---------------------------------------------------------------------------
# Main extraction entry point
# ---------------------------------------------------------------------------

def extract(cleaned_text: str, metadata_candidates: dict,
            source_profile: str) -> HearingRecord:
    """Build a structured HearingRecord from normalized text."""
    uncertainties: List[str] = []

    # --- Metadata ---
    hearing_title = metadata_candidates.get("hearing_title", None)
    hearing_date = None
    hearing_time = None
    memo_date = None

    pub_datetime = metadata_candidates.get("publication_datetime")
    date_long = metadata_candidates.get("hearing_date_long")
    date_mention = metadata_candidates.get("date_mention")

    if date_long:
        hearing_date = date_long if isinstance(date_long, str) else date_long[0]
    elif date_mention:
        hearing_date = date_mention if isinstance(date_mention, str) else date_mention[0]

    if pub_datetime:
        pub_str = pub_datetime if isinstance(pub_datetime, str) else pub_datetime[0]
        time_match = re.search(r"(\d{1,2}:\d{2}\s*(?:AM|PM))", pub_str)
        if time_match:
            hearing_time = time_match.group(1)
            uncertainties.append(
                "Publication timestamp used for hearing time; "
                "verify this is the actual hearing time, not just the article publication time"
            )

    if not hearing_date and pub_datetime:
        pub_str = pub_datetime if isinstance(pub_datetime, str) else pub_datetime[0]
        date_match = re.search(r"(\d{2}/\d{2}/\d{4})", pub_str)
        if date_match:
            raw = date_match.group(1)
            from datetime import datetime
            try:
                dt = datetime.strptime(raw, "%m/%d/%Y")
                hearing_date = dt.strftime("%B %d, %Y")
            except ValueError:
                hearing_date = raw

    # Fallback: publication_date_only (when time portion was garbled)
    if not hearing_date:
        pub_date_only = metadata_candidates.get("publication_date_only")
        if pub_date_only:
            raw = pub_date_only if isinstance(pub_date_only, str) else pub_date_only[0]
            from datetime import datetime
            try:
                dt = datetime.strptime(raw, "%m/%d/%Y")
                hearing_date = dt.strftime("%B %d, %Y")
                uncertainties.append(
                    "Date extracted from publication header; verify this is the hearing date"
                )
            except ValueError:
                hearing_date = raw

    committee_name = metadata_candidates.get("committee_name")

    # Attempt to extract hearing title from text if not found
    if not hearing_title:
        lines = cleaned_text[:3000].split("\n")
        for line in lines:
            stripped = line.strip()
            if (len(stripped) > 20 and len(stripped) < 200
                    and not stripped.startswith("Sen.")
                    and not stripped.startswith("Rep.")
                    and not re.match(r"\d", stripped)):
                words = stripped.split()
                if len(words) >= 4 and words[0][0].isupper():
                    hearing_title = stripped
                    break
        if not hearing_title:
            uncertainties.append("Could not detect hearing title from source text")

    source_quality = "mostly_clean"
    if source_profile in ("video_transcript",):
        source_quality = "noisy"
    elif source_profile == "cleaned_notes":
        source_quality = "clean"

    metadata = {
        "hearing_title": hearing_title,
        "hearing_date": hearing_date,
        "hearing_time": hearing_time,
        "memo_date": memo_date,
        "committee_name": committee_name,
        "subcommittee_name": None,
        "subject_line": None,
        "source_quality": source_quality,
    }

    # --- Structure ---
    leadership_model = _detect_leadership_model(cleaned_text)

    if leadership_model == "co_chairs":
        opening_heading = HEADING_OPENING_COCHAIRS
    else:
        opening_heading = HEADING_OPENING_STATEMENTS

    structure = {
        "opening_heading": opening_heading,
        "witness_heading": HEADING_WITNESS_SECTION,
        "hearing_format": "committee_hearing",
        "leadership_model": leadership_model,
        "panel_count": len(metadata_candidates.get("panels_detected", [])) or 1,
        "has_qa_section": True,
    }

    # --- Detect leadership roles from context ---
    leadership_roles = _detect_leadership_from_context(cleaned_text)
    # leadership_roles: {last_name_lower: "Chairman" | "Ranking Member" | "Commissioner"}

    # --- Split text by speakers ---
    segments = _split_by_speakers(cleaned_text)

    # --- Build speaker roster ---
    # Collect all unique speakers and classify them
    all_speaker_labels = [seg["speaker"] for seg in segments]
    unique_labels = list(dict.fromkeys(all_speaker_labels))

    leadership_speakers = []
    member_speakers = []
    leadership_label_set = set()  # lowercase labels of leadership speakers
    member_label_set = set()      # lowercase labels of member speakers
    witness_label_set = set()     # lowercase labels of witness speakers

    for label in unique_labels:
        label_stripped = label.strip()
        has_party = bool(re.search(r"\([RD]-", label_stripped))

        # Extract the actual last name (before any party/state paren)
        if has_party:
            name_part = re.sub(r"\s*\([RD]-[A-Za-z.]+\)\s*$", "", label_stripped).strip()
            last_name = name_part.split()[-1]
        else:
            last_name = label_stripped.split()[-1]

        # Check if this person has a leadership role from context
        if last_name.lower() in leadership_roles:
            role = leadership_roles[last_name.lower()]
            # Build the proper heading label
            if has_party:
                # Already has party/state, reformat with role
                name_part = re.sub(r"\s*\([RD]-[A-Za-z.]+\)\s*$", "", label_stripped).strip()
                party_match = re.search(r"\(([RD]-[A-Za-z.]+)\)", label_stripped)
                state_code = party_match.group(1) if party_match else ""
                # Remove "Sen." prefix and use role
                name_core = re.sub(r"^(?:Sen\.|Senator|Rep\.|Representative)\s+", "", name_part).strip()
                heading_label = f"{role} {name_core} ({state_code})"
            else:
                heading_label = f"{role} {label_stripped}"

            leadership_speakers.append(
                SpeakerInfo(name=label_stripped, role_display=heading_label)
            )
            leadership_label_set.add(label_stripped.lower())
        elif has_party:
            # Member with party/state but not leadership
            # Normalize label format for heading
            heading_label = label_stripped
            # Convert "Sen." -> "Senator" for headings
            heading_label = re.sub(r"^Sen\.\s+", "Senator ", heading_label)
            heading_label = re.sub(r"^Rep\.\s+", "Representative ", heading_label)

            member_speakers.append(
                SpeakerInfo(name=label_stripped, role_display=heading_label)
            )
            member_label_set.add(label_stripped.lower())
        else:
            # Bare name — likely a witness
            witness_label_set.add(label_stripped.lower())

    # --- Process segments into opening/witness/Q&A ---
    opening_statements: List[OpeningStatement] = []
    witness_records: List[WitnessRecord] = []
    qa_by_member: Dict[str, List[Dict]] = {}

    # Phase detection: opening -> witness testimony -> Q&A
    # Rules:
    # 1. "opening" phase lasts until the FIRST WITNESS speaks
    # 2. "witness" phase: witness segments are testimony; congress segments are introductions
    # 3. "qa" phase: starts when a non-leadership member speaks after witnesses have testified,
    #    or when leadership speaks with Q&A signals after all witnesses
    phase = "opening"  # "opening", "witness", "qa"
    witness_count = 0
    seen_leadership_opening = set()
    expected_witness_count = len(witness_label_set)

    for i, seg in enumerate(segments):
        speaker = seg["speaker"]
        text = seg["text"]
        speaker_lower = speaker.lower()

        is_leadership = speaker_lower in leadership_label_set
        is_member = speaker_lower in member_label_set
        is_witness = speaker_lower in witness_label_set
        is_congress = is_leadership or is_member

        # --- Phase transitions ---
        # Opening -> Witness: when the first witness speaks
        if phase == "opening" and is_witness:
            phase = "witness"

        # Witness -> Q&A:
        # 1. A non-leadership member speaks (Senators who aren't chair/ranking)
        # 2. After all witnesses, leadership speaks with Q&A-style content (questions)
        if phase == "witness":
            if is_member and not is_leadership:
                phase = "qa"
            elif is_congress and witness_count >= expected_witness_count:
                phase = "qa"
            elif is_congress and witness_count >= expected_witness_count - 1:
                # Only transition if text explicitly signals Q&A start
                text_lower = text.lower()[:300]
                if any(kw in text_lower for kw in [
                    "let's go to questions", "five minutes",
                    "begin questions", "we'll start with questions",
                    "go to questions",
                ]):
                    phase = "qa"

        # --- Assign segment based on phase ---
        if phase == "opening":
            if is_leadership and speaker_lower not in seen_leadership_opening:
                seen_leadership_opening.add(speaker_lower)
                opening_summary = _llm_summarize(text, speaker, context="opening")
                opening_statements.append(
                    OpeningStatement(
                        speaker=speaker,
                        summary_points=[opening_summary]
                    )
                )
            elif is_congress and speaker_lower in seen_leadership_opening:
                # Leadership speaking again — likely introducing witnesses
                # Don't count as an opening statement, just skip
                pass

        elif phase == "witness":
            if is_witness:
                witness = _extract_witness_info(speaker, text)
                witness_records.append(witness)
                witness_count += 1
            elif is_congress:
                # Congress member speaking during witness phase = introductions
                # Don't classify as Q&A yet unless it's clearly Q&A
                pass

        elif phase == "qa":
            if is_congress:
                if speaker_lower not in qa_by_member:
                    qa_by_member[speaker_lower] = {"speaker": speaker, "exchanges": []}
                qa_by_member[speaker_lower]["exchanges"].append({
                    "text": text, "responders": []
                })
            elif is_witness and qa_by_member:
                # Witness responding to a member's question
                last_member = list(qa_by_member.keys())[-1]
                if qa_by_member[last_member]["exchanges"]:
                    qa_by_member[last_member]["exchanges"][-1]["responders"].append({
                        "witness": speaker, "text": text
                    })




    # --- Build Q&A clusters ---
    qa_clusters: List[QACluster] = []
    for member_key, data in qa_by_member.items():
        member_label = data["speaker"]
        exchanges = data["exchanges"]

        combined_text = []
        for ex in exchanges:
            combined_text.append(ex["text"])
            for resp in ex.get("responders", []):
                combined_text.append(f"{resp['witness']} responded: {resp['text']}")

        full_text = " ".join(combined_text)

        # Detect topic
        topic = "General inquiry"
        topic_keywords = {
            "supply chain": "supply chain security",
            "manufactur": "domestic manufacturing",
            "China": "China dependencies",
            "FDA": "FDA oversight",
            "API": "active pharmaceutical ingredients",
            "national security": "national security",
            "generic drug": "generic drug market",
            "biotech": "biotechnology",
            "innovation": "pharmaceutical innovation",
            "transparency": "supply chain transparency",
        }
        for kw, topic_name in topic_keywords.items():
            if kw.lower() in full_text.lower():
                topic = topic_name
                break

        # Commitments or requests
        commitments = []
        for match in re.finditer(
            r"(?:commit|pledge|promise|request|will follow up|agreed to)\w*\s+(.+?)(?:\.|$)",
            full_text, re.IGNORECASE
        ):
            c = match.group(1).strip()
            if len(c) > 15:
                commitments.append(c)

        # Build objective summary of the exchange mimicking the example reports
        exchange_paragraphs = []
        for ex in exchanges[:4]:
            if ex.get("responders"):
                resp = ex["responders"][0]
                combined_text = f"MEMBER QUESTION/STATEMENT:\\n{ex['text']}\\n\\nWITNESS ({resp['witness']}) RESPONSE:\\n{resp['text']}"
                summary = _llm_summarize(combined_text, member_label, context="qa_exchange")
                exchange_paragraphs.append(summary)
            else:
                combined_text = f"MEMBER STATEMENT:\\n{ex['text']}"
                summary = _llm_summarize(combined_text, member_label, context="qa_exchange")
                exchange_paragraphs.append(summary)
                    
        # Join the exchange paragraphs with double newlines
        summary_text = "\n\n".join(exchange_paragraphs)

        qa_clusters.append(QACluster(
            member=member_label,
            topic=topic,
            summary=summary_text if summary_text else "General discussion on the topic.",
            commitments_or_requests=commitments[:3],
        ))

    # --- Overview points ---
    overview_points = _extract_overview_points(cleaned_text, metadata)

    # --- Participants ---
    participants = {
        "leadership": [{"name": s.name, "role_display": s.role_display} for s in leadership_speakers],
        "members": [{"name": s.name, "role_display": s.role_display} for s in member_speakers],
    }

    # --- Validation and uncertainties ---
    if not opening_statements:
        uncertainties.append("No opening statements detected — may need manual review")
    if not witness_records:
        uncertainties.append("No witness testimonies detected — may need manual review")
    if not qa_clusters:
        uncertainties.append("No Q&A exchanges detected — may need manual review")
    if not hearing_title:
        uncertainties.append("Hearing title not detected")
    if not hearing_date:
        uncertainties.append("Hearing date not detected")
    if not committee_name:
        uncertainties.append("Committee name not detected")

    for w in witness_records:
        if not w.affiliation:
            uncertainties.append(f"Affiliation not detected for witness: {w.name}")

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
