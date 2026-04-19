"""
Stakeholder Briefing Generator
================================
Three-step pipeline:
  Step 1 — Gather data: topic-relevant news (GNews) + disclosure records (LDA, FARA, IRS 990)
  Step 2 — gpt-4.1 synthesizes profile, positions, and talking points from all gathered data
  Step 3 — Assemble the final briefing document
"""

import os
import json
import sys
import tempfile
import re
from datetime import datetime, timedelta
from pathlib import Path
from openai import OpenAI

# Optional: news fetching
try:
    from gnews import GNews
    HAS_GNEWS = True
except ImportError:
    HAS_GNEWS = False


MODEL = "ChangeAgent"

def _active_model(default: str) -> str:
    import os
    return os.environ.get("LLM_MODEL_OVERRIDE") or default

def _response_format_kwarg() -> dict:
    import os
    if os.environ.get("LLM_MODEL_OVERRIDE"):
        return {}
    return {"response_format": {"type": "json_object"}}

def _max_tokens_kwarg(default: int) -> dict:
    import os
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
# Step 1: Data gathering
# ---------------------------------------------------------------------------

def fetch_news(stakeholder_name: str, meeting_purpose: str = "",
               max_results: int = 10) -> list[dict]:
    """Fetch recent news mentions via Google News.

    Runs two queries — one for the stakeholder name alone, one combining name
    and the meeting topic — then deduplicates, so results are both broad and
    topically relevant.
    """
    if not HAS_GNEWS:
        print("  gnews not installed, skipping news fetch", file=sys.stderr)
        return []

    try:
        gn = GNews(language="en", country="US", period="90d", max_results=max_results)

        # Query 1: stakeholder name (broad)
        articles_broad = gn.get_news(stakeholder_name) or []

        # Query 2: stakeholder + topic keywords (relevant)
        articles_topic = []
        if meeting_purpose:
            # Extract first few meaningful words from the purpose
            topic_words = " ".join(meeting_purpose.split()[:6])
            topic_query = f"{stakeholder_name} {topic_words}"
            articles_topic = gn.get_news(topic_query) or []

        # Merge and deduplicate by title
        seen_titles = set()
        results = []
        # Prioritize topic-relevant articles first
        for a in articles_topic + articles_broad:
            title = a.get("title", "")
            title_key = title.lower().strip()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            results.append({
                "title": title,
                "source": a.get("publisher", {}).get("title", "Unknown"),
                "date": a.get("published date", ""),
                "url": a.get("url", ""),
                "description": a.get("description", ""),
            })

        return results
    except Exception as e:
        print(f"  News fetch error: {e}", file=sys.stderr)
        return []


def _lda_topic_search(meeting_purpose: str, max_results: int = 15) -> list[dict]:
    """Search LDA filings by lobbying issue topic, derived from the meeting purpose.

    Uses the LDA API's filing_specific_lobbying_issues parameter to find
    who's actively lobbying on the issue — the real intelligence value for
    legislator meetings.
    """
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    # Extract policy topic keywords from the meeting purpose.
    # We use the LLM-free approach: strip procedural and generic policy-process words,
    # keeping only terms specific enough to anchor a targeted LDA search.
    # Generic words like "transparency" or "accountability" are deliberately excluded —
    # they appear across hundreds of unrelated filings (voting rights, civil rights, etc.)
    # and produce noisy, topic-adjacent results that hurt briefing quality.
    skip_words = {
        "discuss", "support", "oppose", "review", "co-sponsorship", "co-sponsor",
        "cosponsorship", "cosponsor", "the", "and", "for", "of", "on", "in", "to",
        "a", "an", "with", "about", "their", "our", "position", "potential",
        "mandatory", "understand", "meet", "meeting", "explore", "regarding",
        "concerning", "related", "engagement", "briefing", "prepare", "pre-deployment",
        "testing", "framework", "legislation", "bill", "act", "federal", "state",
        # Generic policy-process words — too broad for targeted LDA queries:
        "transparency", "accountability", "oversight", "governance", "reform",
        "standards", "policy", "access", "protection", "rights", "equity",
        "safety", "security", "privacy", "innovation", "initiative", "commission",
    }
    topic_words = [
        w.strip(".,;:()")
        for w in meeting_purpose.split()
        if w.lower().strip(".,;:()") not in skip_words and len(w.strip(".,;:()")) > 2
    ]

    # Build search query: use the core policy topic (2-3 words max for LDA API)
    topic_query = " ".join(topic_words[:3])

    if not topic_query:
        return []

    print(f"  LDA topic search: '{topic_query}'", file=sys.stderr)

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        resp = session.get(
            "https://lda.gov/api/v1/filings/",
            params={
                "filing_specific_lobbying_issues": topic_query,
                "ordering": "-dt_posted",
                "page_size": min(max_results, 25),
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        seen_clients = set()
        for f in data.get("results", []):
            client_name = f.get("client", {}).get("name", "Unknown")
            registrant_name = f.get("registrant", {}).get("name", "Unknown")

            # Deduplicate by client — we want unique actors, not repeat filings
            client_key = client_name.upper()
            if client_key in seen_clients:
                continue
            seen_clients.add(client_key)

            # Extract specific issues from this filing
            issues = []
            for activity in f.get("lobbying_activities", []):
                issue_text = activity.get("description", "")
                if issue_text:
                    issues.append(issue_text[:200])

            amount = f.get("income") or f.get("expenses") or ""

            results.append({
                "registrant_name": registrant_name,
                "client_name": client_name,
                "filing_year": f.get("filing_year", ""),
                "filing_period": f.get("filing_period_display", ""),
                "amount_reported": amount,
                "dt_posted": f.get("dt_posted", ""),
                "issues": issues[:3],
            })

            if len(results) >= max_results:
                break

        # Post-filter: only keep filings whose issues text actually contains
        # at least one core topic word. This removes entries that matched the
        # query on a generic term (e.g. "transparency") but are about an
        # unrelated domain (voting rights, civil rights, etc.).
        if topic_words and results:
            core = [w.lower() for w in topic_words]
            filtered = [
                f for f in results
                if any(
                    word in " ".join(str(i) for i in f.get("issues", [])).lower()
                    for word in core
                )
            ]
            # Only apply the filter if it leaves at least some results.
            # If it would wipe everything (query was very generic), keep the originals.
            if filtered:
                results = filtered
            else:
                print(
                    "  LDA topic post-filter removed all results — keeping originals",
                    file=sys.stderr,
                )

        return results

    except Exception as e:
        print(f"  LDA topic search error: {e}", file=sys.stderr)
        return []


def _meeting_terms(meeting_purpose: str) -> list[str]:
    """Extract meeting-topic terms for disclosure relevance scoring."""
    import re

    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "into", "your", "our",
        "their", "about", "support", "oppose", "discuss", "explore", "meeting",
        "framework", "policy", "federal", "state", "bill", "act", "standards",
        "testing", "transparency", "innovation", "practical", "clear",
    }
    raw_terms = re.findall(r"[A-Za-z0-9][A-Za-z0-9&-]+", meeting_purpose.lower())
    terms = []
    for term in raw_terms:
        if term in stop_words:
            continue
        if len(term) <= 2 and term != "ai":
            continue
        terms.append(term)
    return list(dict.fromkeys(terms))


def _score_topic_disclosure(record: dict, meeting_terms: list[str]) -> int:
    """Score how directly an LDA topic filing helps with the actual meeting topic."""
    haystack = " ".join([
        str(record.get("client_name", "")),
        str(record.get("registrant_name", "")),
        " ".join(str(i) for i in record.get("issues", [])),
    ]).lower()

    score = 0
    for term in meeting_terms:
        if term in haystack:
            score += 2 if len(term) > 4 else 1
    if "artificial intelligence" in haystack or " ai " in f" {haystack} ":
        score += 3
    if "machine learning" in haystack or "model" in haystack or "algorithm" in haystack:
        score += 2
    return score


def _filter_topic_disclosures(disclosures: list[dict], meeting_purpose: str, max_items: int = 5) -> list[dict]:
    """Keep the most meeting-relevant LDA topic disclosures without wiping the section entirely."""
    if not disclosures:
        return []
    terms = _meeting_terms(meeting_purpose)
    scored = []
    for item in disclosures:
        enriched = dict(item)
        enriched["_topic_score"] = _score_topic_disclosure(item, terms)
        scored.append(enriched)

    scored.sort(key=lambda item: item.get("_topic_score", 0), reverse=True)
    filtered = [item for item in scored if item.get("_topic_score", 0) >= 1]
    if len(filtered) < min(2, len(scored)):
        filtered = scored[: min(max_items, max(3, len(filtered)))]
    return filtered[:max_items]


def fetch_disclosures(stakeholder_name: str, organization: str = "",
                      meeting_purpose: str = "") -> dict:
    """Search LDA, FARA, and IRS 990 for the stakeholder.

    Runs TWO types of LDA search:
      1. Entity search — by stakeholder name/org (who ARE they in the lobbying world)
      2. Topic search — by meeting purpose keywords (who's lobbying on this issue)

    For legislators, entity search will typically return 0 (they don't file LDA),
    but topic search surfaces the real intelligence: who's lobbying on the issue
    they oversee.
    """
    toolkit_root = Path(__file__).resolve().parent.parent.parent
    tracker_exec = toolkit_root / "influence_disclosure_tracker" / "execution"
    sys.path.insert(0, str(tracker_exec))

    now = datetime.now()
    two_years_ago = now - timedelta(days=730)
    from_date = two_years_ago.strftime("%Y-%m-%d")
    to_date = now.strftime("%Y-%m-%d")

    result = {
        "lda_entity": [],
        "lda_topic": [],
        "fara": {"registrants": [], "foreign_principals": []},
        "irs990": {"organizations": [], "filings": []},
    }

    # --- LDA Entity Search (by name/org) ---
    entity = organization if organization else stakeholder_name

    try:
        from io_utils import IOUtils
        tmp_out = tempfile.mkdtemp(prefix="sb_disclosure_")
        io = IOUtils(tmp_out, os.path.join(tmp_out, ".cache"), entities=[entity])
    except Exception as e:
        print(f"  Could not init IOUtils: {e}", file=sys.stderr)
        # Still try topic search even if entity search fails
        if meeting_purpose:
            result["lda_topic"] = _filter_topic_disclosures(_lda_topic_search(meeting_purpose), meeting_purpose)
            print(f"  LDA topic: {len(result['lda_topic'])} actors found", file=sys.stderr)
        return result

    # LDA by entity name
    try:
        from lda_client import LDAClient
        lda = LDAClient(io, fuzzy_threshold=85.0, max_results=20, search_field="both")
        lda.search_entity(entity, from_date, to_date)

        lda_filings = io.datasets.get("lda_filings", [])
        lda_issues = io.datasets.get("lda_issues", [])

        issues_by_filing = {}
        for issue in lda_issues:
            fid = issue.get("filing_uuid", "")
            if fid not in issues_by_filing:
                issues_by_filing[fid] = []
            issues_by_filing[fid].append(issue.get("specific_issue", ""))

        for f in lda_filings[:15]:
            fid = f.get("filing_uuid", "")
            f["issues"] = issues_by_filing.get(fid, [])

        result["lda_entity"] = lda_filings[:15]
        print(f"  LDA entity: {len(lda_filings)} filings found", file=sys.stderr)
    except Exception as e:
        print(f"  LDA entity search error: {e}", file=sys.stderr)

    # --- LDA Topic Search (by meeting purpose) ---
    if meeting_purpose:
        result["lda_topic"] = _filter_topic_disclosures(_lda_topic_search(meeting_purpose), meeting_purpose)
        print(f"  LDA topic: {len(result['lda_topic'])} actors found", file=sys.stderr)

    # --- FARA ---
    try:
        from fara_client import FARAClient
        fara = FARAClient(io, fuzzy_threshold=85.0, max_results=20)
        fara.search_entity(entity, from_date, to_date)

        fara_registrants = io.datasets.get("fara_registrants", [])
        fara_principals = io.datasets.get("fara_foreign_principals", [])
        result["fara"] = {
            "registrants": fara_registrants[:10],
            "foreign_principals": fara_principals[:10],
        }
        total_fara = len(fara_registrants) + len(fara_principals)
        print(f"  FARA: {total_fara} records found", file=sys.stderr)
    except Exception as e:
        print(f"  FARA search error: {e}", file=sys.stderr)

    # --- IRS 990 ---
    try:
        from irs990_client import IRS990Client
        irs = IRS990Client(io, fuzzy_threshold=85.0, max_results=10, mode="basic")
        irs.search_entity(entity, from_date, to_date)

        irs_orgs = io.datasets.get("irs990_organizations", [])
        irs_filings = io.datasets.get("irs990_filings", [])
        result["irs990"] = {
            "organizations": irs_orgs[:5],
            "filings": irs_filings[:5],
        }
        print(f"  IRS 990: {len(irs_orgs)} orgs, {len(irs_filings)} filings found", file=sys.stderr)
    except Exception as e:
        print(f"  IRS 990 search error: {e}", file=sys.stderr)

    return result


# ---------------------------------------------------------------------------
# Step 2: LLM synthesis
# ---------------------------------------------------------------------------

BRIEFING_SYSTEM = """You are a senior public affairs researcher preparing a pre-meeting stakeholder briefing.
Your job is to synthesize ALL available information into a concise, actionable one-pager
that a PA professional can review in 5 minutes before walking into the meeting.

RULES:
- Be SPECIFIC and FACTUAL. Use concrete details — names, titles, dates, bill numbers, committee names.
- Do NOT place [VERIFY] markers or unresolved uncertainty tokens in the final prose.
- If a fact is too uncertain to state cleanly, omit it rather than hedging inline.
- Do NOT fabricate specific statistics, quotes, or dates.
- Use the news articles and disclosure data provided to ground your analysis.
- Use disclosure material selectively. Topic lobbying activity can be included as directional intelligence when it materially informs the meeting objective, but do not dump a long unrelated filing list.
- If the stakeholder is a legislator, mention committee assignments, caucus memberships, and recent legislative actions.
- If the stakeholder is an organization, mention leadership, budget/revenue, and key programs.
- Do not make speculative local-benefit or constituency inferences unless supported by explicit evidence in the source material.

QUANTITY REQUIREMENTS:
- profile.key_areas: EXACTLY 5 policy areas, ordered by relevance to the meeting
- policy_positions: EXACTLY 4 positions, each with concrete evidence
- talking_points: EXACTLY 4 talking points, each strategically actionable
- key_questions: EXACTLY 3 questions

Return ONLY a JSON object with this exact structure:
{
  "profile": {
    "summary": "3-4 sentence background summary including career trajectory and key achievements",
    "current_role": "Full current title, committee roles, and key responsibilities",
    "key_areas": ["Policy area 1", "Policy area 2", "Policy area 3", "Policy area 4", "Policy area 5"],
    "notable_positions": "2-3 sentences on their most significant public positions relevant to this meeting"
  },
  "policy_positions": [
    {
      "position": "Clear, specific statement of their position (not vague)",
      "evidence": "Specific vote, bill, statement, or action that demonstrates this (with date if known)",
      "relevance": "One sentence on why this matters for YOUR meeting objective"
    }
  ],
  "talking_points": [
    {
      "point": "Specific, actionable thing to say or raise (not generic)",
      "rationale": "Strategic reason — what reaction you expect and why it advances your objective"
    }
  ],
  "key_questions": [
    {
      "question": "Specific question to ask during the meeting",
      "purpose": "What intelligence you gain from the answer and how it shapes next steps"
    }
  ]
}"""


def _format_disclosures_for_prompt(disclosures: dict) -> str:
    """Format disclosure data into readable text for the LLM prompt."""
    parts = []

    # LDA entity results (stakeholder's own lobbying activity)
    lda_entity = disclosures.get("lda_entity", [])
    if lda_entity:
        lda_lines = []
        for f in lda_entity[:8]:
            line = (
                f"- Registrant: {f.get('registrant_name', 'N/A')}, "
                f"Client: {f.get('client_name', 'N/A')}, "
                f"Year: {f.get('filing_year', 'N/A')}, "
                f"Amount: {f.get('amount_reported', 'N/A')}"
            )
            issues = f.get("issues", [])
            if issues:
                line += f", Issues: {'; '.join(issues[:3])}"
            lda_lines.append(line)
        parts.append("LDA Lobbying Filings (stakeholder's activity):\n" + "\n".join(lda_lines))

    # LDA topic results (who's lobbying on the meeting issue)
    lda_topic = disclosures.get("lda_topic", [])
    if lda_topic:
        topic_lines = []
        for f in lda_topic[:10]:
            line = (
                f"- {f.get('client_name', 'N/A')} (via {f.get('registrant_name', 'N/A')}), "
                f"{f.get('filing_year', '')} {f.get('filing_period', '')}"
            )
            amount = f.get("amount_reported", "")
            if amount:
                try:
                    line += f", ${float(amount):,.0f}"
                except (ValueError, TypeError):
                    pass
            issues = f.get("issues", [])
            if issues:
                line += f" — {issues[0][:150]}"
            topic_lines.append(line)
        parts.append(
            "SELECTED DISCLOSURE INTELLIGENCE — organizations most relevant to the meeting topic:\n"
            + "\n".join(topic_lines)
        )

    fara = disclosures.get("fara", {})
    fara_regs = fara.get("registrants", []) if isinstance(fara, dict) else []
    fara_fps = fara.get("foreign_principals", []) if isinstance(fara, dict) else []
    if fara_regs:
        lines = [
            f"- {r.get('registrant_name', 'N/A')} (Reg #{r.get('registration_number', 'N/A')}), "
            f"Registered: {r.get('registration_date', 'N/A')}"
            for r in fara_regs[:5]
        ]
        parts.append("FARA Registrants:\n" + "\n".join(lines))
    if fara_fps:
        lines = [
            f"- {fp.get('foreign_principal_name', 'N/A')} ({fp.get('state_or_country', 'N/A')})"
            for fp in fara_fps[:5]
        ]
        parts.append("FARA Foreign Principals:\n" + "\n".join(lines))

    irs = disclosures.get("irs990", {})
    irs_orgs = irs.get("organizations", []) if isinstance(irs, dict) else []
    irs_filings = irs.get("filings", []) if isinstance(irs, dict) else []
    if irs_orgs:
        lines = [
            f"- {o.get('organization_name', 'N/A')} (EIN: {o.get('ein', 'N/A')}), "
            f"NTEE: {o.get('ntee_code', 'N/A')}, {o.get('city', '')}, {o.get('state', '')}"
            for o in irs_orgs[:5]
        ]
        parts.append("IRS 990 Organizations:\n" + "\n".join(lines))
    if irs_filings:
        lines = [
            f"- {f.get('organization_name', 'N/A')}, Year: {f.get('tax_year', 'N/A')}, "
            f"Revenue: {f.get('total_revenue', 'N/A')}, Expenses: {f.get('total_functional_expenses', 'N/A')}"
            for f in irs_filings[:5]
        ]
        parts.append("IRS 990 Filings:\n" + "\n".join(lines))

    return "\n\n".join(parts)


def _scrub_verify_markers(value):
    if isinstance(value, str):
        cleaned = re.sub(r"\s*\[VERIFY[^\]]*\]", "", value).strip()
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned
    if isinstance(value, list):
        return [_scrub_verify_markers(item) for item in value]
    if isinstance(value, dict):
        return {key: _scrub_verify_markers(val) for key, val in value.items()}
    return value


def _collect_verify_markers(value, flags: list[str], prefix: str = ""):
    if isinstance(value, str):
        for match in re.findall(r"\[VERIFY([^\]]*)\]", value):
            note = match.strip(" :.-")
            label = prefix or "briefing"
            flags.append(f"{label}: {note}" if note else f"{label}: requires verification")
    elif isinstance(value, list):
        for index, item in enumerate(value, 1):
            _collect_verify_markers(item, flags, f"{prefix}[{index}]" if prefix else f"item {index}")
    elif isinstance(value, dict):
        for key, val in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else key
            _collect_verify_markers(val, flags, next_prefix)


def _derive_disclosure_mode(disclosures: dict) -> str:
    if disclosures.get("lda_entity"):
        return "stakeholder_specific"
    if disclosures.get("lda_topic") or disclosures.get("fara", {}).get("registrants") or disclosures.get("fara", {}).get("foreign_principals"):
        return "topic_context"
    return "none"


def _curate_disclosure_brief(disclosures: dict) -> list[dict]:
    curated = []
    for record in disclosures.get("lda_entity", [])[:3]:
        issues = record.get("issues", [])
        curated.append({
            "who": record.get("client_name") or record.get("registrant_name") or "Unknown actor",
            "what": issues[0][:160] if issues else "Direct lobbying activity tied to the stakeholder",
            "why_it_matters": "Directly relevant to the stakeholder's disclosure footprint.",
        })
    if not curated:
        for record in disclosures.get("lda_topic", [])[:3]:
            issues = record.get("issues", [])
            curated.append({
                "who": record.get("client_name") or "Unknown actor",
                "what": issues[0][:160] if issues else "Lobbying activity tied to the meeting topic",
                "why_it_matters": "Shows which outside organizations are actively engaging on the meeting topic.",
            })
    return curated[:3]


def _clean_synthesis_output(synthesis: dict, disclosures: dict) -> dict:
    evidence_flags: list[str] = []
    _collect_verify_markers(synthesis, evidence_flags)
    cleaned = _scrub_verify_markers(synthesis)
    evidence_flags = list(dict.fromkeys(flag for flag in evidence_flags if flag))

    profile = cleaned.get("profile", {}) or {}
    policy_positions = []
    for item in cleaned.get("policy_positions", []) or []:
        if not item.get("position") or not item.get("evidence"):
            evidence_flags.append("policy_positions: dropped item missing evidence or position.")
            continue
        policy_positions.append(item)

    talking_points = [item for item in (cleaned.get("talking_points", []) or []) if item.get("point")]
    key_questions = [item for item in (cleaned.get("key_questions", []) or []) if item.get("question")]

    disclosure_mode = _derive_disclosure_mode(disclosures)
    curated_brief = _curate_disclosure_brief(disclosures)
    briefing_quality = "complete"
    if evidence_flags or not policy_positions or (disclosure_mode != "none" and not curated_brief):
        briefing_quality = "partial"

    return {
        "profile": profile,
        "policy_positions": policy_positions[:4],
        "talking_points": talking_points[:4],
        "key_questions": key_questions[:3],
        "evidence_flags": list(dict.fromkeys(evidence_flags)),
        "briefing_quality": briefing_quality,
        "disclosure_mode": disclosure_mode,
        "curated_disclosures": curated_brief,
    }


def synthesize_briefing(client: OpenAI, stakeholder_name: str,
                        meeting_purpose: str, organization: str = "",
                        your_organization: str = "", context: str = "",
                        news: list[dict] = None,
                        disclosures: dict = None) -> dict:
    """Use gpt-4.1 to synthesize all gathered data into a structured briefing."""

    parts = [
        f"Prepare a pre-meeting briefing for: {stakeholder_name}",
        f"Meeting purpose: {meeting_purpose}",
    ]
    if organization:
        parts.append(f"Their organization: {organization}")
    if your_organization:
        parts.append(
            f"Our organization: {your_organization}\n"
            f"Frame all talking points from {your_organization}'s perspective."
        )

    if context:
        parts.append(f"\n--- Additional Context ---\n{context[:5000]}")

    if news:
        news_text = "\n".join(
            f"- [{n['date']}] {n['title']} ({n['source']})"
            + (f"\n  {n['description'][:200]}" if n.get("description") else "")
            for n in news[:10]
        )
        parts.append(f"\n--- Recent News Mentions ({len(news)} found) ---\n{news_text}")

    if disclosures:
        disclosure_text = _format_disclosures_for_prompt(disclosures)
        if disclosure_text:
            parts.append(f"\n--- Disclosure Data ---\n{disclosure_text}")

    prompt = "\n".join(parts)

    response = client.chat.completions.create(
        model=_active_model(MODEL),
        messages=[
            {"role": "system", "content": BRIEFING_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        **_max_tokens_kwarg(4000),
        **_response_format_kwarg(),
    )

    return _parse_json_content(response.choices[0].message.content)


# ---------------------------------------------------------------------------
# Step 3: Full pipeline
# ---------------------------------------------------------------------------

def generate_briefing(stakeholder_name: str, meeting_purpose: str,
                      organization: str = "", your_organization: str = "",
                      context: str = "",
                      include_disclosures: bool = True,
                      include_news: bool = True) -> dict:
    """
    Run the full stakeholder briefing pipeline.

    Returns:
        {
            "header": { ... },
            "profile": { ... },
            "policy_positions": [ ... ],
            "news": [ ... ],
            "disclosures": { ... },
            "talking_points": [ ... ],
            "key_questions": [ ... ],
        }
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required.")

    client = OpenAI(api_key=api_key)

    # Step 1: Gather data
    news = []
    if include_news:
        print("Step 1a: Fetching news...", file=sys.stderr)
        news = fetch_news(stakeholder_name, meeting_purpose)
        print(f"  Found {len(news)} articles", file=sys.stderr)

    disclosures = {"lda_entity": [], "lda_topic": [],
                   "fara": {"registrants": [], "foreign_principals": []},
                   "irs990": {"organizations": [], "filings": []}}
    if include_disclosures:
        print("Step 1b: Searching disclosures (LDA + FARA + IRS 990)...", file=sys.stderr)
        disclosures = fetch_disclosures(stakeholder_name, organization, meeting_purpose)

    # Step 2: LLM synthesis
    print("Step 2: Synthesizing briefing...", file=sys.stderr)
    raw_synthesis = synthesize_briefing(
        client, stakeholder_name, meeting_purpose,
        organization, your_organization, context,
        news, disclosures,
    )
    synthesis = _clean_synthesis_output(raw_synthesis, disclosures)

    # Step 3: Assemble result
    header = {
        "stakeholder_name": stakeholder_name,
        "organization": organization,
        "meeting_purpose": meeting_purpose,
        "prepared_by": your_organization or "PA AI Toolkit",
        "date_prepared": datetime.now().strftime("%B %d, %Y"),
    }

    return {
        "header": header,
        "profile": synthesis.get("profile", {}),
        "policy_positions": synthesis.get("policy_positions", []),
        "news": news[:5],
        "disclosures": disclosures,
        "curated_disclosures": synthesis.get("curated_disclosures", []),
        "briefing_quality": synthesis.get("briefing_quality", "partial"),
        "evidence_flags": synthesis.get("evidence_flags", []),
        "disclosure_mode": synthesis.get("disclosure_mode", "none"),
        "talking_points": synthesis.get("talking_points", []),
        "key_questions": synthesis.get("key_questions", []),
    }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def render_markdown(result: dict) -> str:
    """Render the briefing as a markdown document."""
    h = result["header"]
    sections = []

    # Header
    sections.append(f"# Stakeholder Briefing: {h['stakeholder_name']}")
    if h.get("organization"):
        sections.append(f"**Organization:** {h['organization']}")
    sections.append(f"**Meeting Purpose:** {h['meeting_purpose']}")
    sections.append(f"**Prepared by:** {h['prepared_by']}  |  **Date:** {h['date_prepared']}")
    sections.append("\n---\n")

    # Profile
    profile = result.get("profile", {})
    if profile:
        sections.append("## Profile")
        if profile.get("summary"):
            sections.append(profile["summary"])
        if profile.get("current_role"):
            sections.append(f"\n**Current Role:** {profile['current_role']}")
        if profile.get("key_areas"):
            sections.append(f"\n**Key Policy Areas:** {', '.join(profile['key_areas'])}")
        if profile.get("notable_positions"):
            sections.append(f"\n**Notable Positions:** {profile['notable_positions']}")
        sections.append("")

    # Policy Positions
    positions = result.get("policy_positions", [])
    if positions:
        sections.append("## Policy Positions")
        for p in positions:
            sections.append(f"- **{p['position']}**")
            if p.get("evidence"):
                sections.append(f"  *Evidence:* {p['evidence']}")
            if p.get("relevance"):
                sections.append(f"  *Relevance:* {p['relevance']}")
        sections.append("")

    # Disclosure Data
    disclosures = result.get("disclosures", {})
    has_lda_entity = bool(disclosures.get("lda_entity"))
    has_lda_topic = bool(disclosures.get("lda_topic"))
    fara = disclosures.get("fara", {})
    has_fara = bool(fara.get("registrants") if isinstance(fara, dict) else fara)
    irs = disclosures.get("irs990", {})
    has_irs = bool(irs.get("organizations") if isinstance(irs, dict) else irs)

    curated_disclosures = result.get("curated_disclosures", [])
    if curated_disclosures or has_lda_entity or has_lda_topic or has_fara or has_irs:
        sections.append("## Disclosure Data")

        if curated_disclosures:
            sections.append("### Curated Disclosure Intelligence")
            for item in curated_disclosures:
                sections.append(
                    f"- **{item.get('who', 'Unknown actor')}** — {item.get('what', '')} "
                    f"*Why it matters:* {item.get('why_it_matters', '')}"
                )

        if has_lda_entity:
            sections.append("### LDA Lobbying (Stakeholder Activity)")
            for r in disclosures["lda_entity"][:5]:
                amount = r.get("amount_reported", "")
                try:
                    amount_str = f" (${float(amount):,.0f})" if amount and amount != "N/A" else ""
                except (ValueError, TypeError):
                    amount_str = ""
                issues = r.get("issues", [])
                issue_str = f" — *{issues[0][:80]}*" if issues else ""
                sections.append(
                    f"- **{r.get('registrant_name', 'N/A')}** for "
                    f"{r.get('client_name', 'N/A')}{amount_str}, "
                    f"Filed {r.get('filing_year', r.get('dt_posted', 'N/A'))}"
                    f"{issue_str}"
                )

        if has_lda_topic:
            sections.append("### Selected Lobbying Activity on Meeting Topic")
            for r in disclosures["lda_topic"][:5]:
                amount = r.get("amount_reported", "")
                try:
                    amount_str = f" (${float(amount):,.0f})" if amount and amount != "N/A" else ""
                except (ValueError, TypeError):
                    amount_str = ""
                issues = r.get("issues", [])
                issue_str = f" — *{issues[0][:80]}*" if issues else ""
                sections.append(
                    f"- **{r.get('client_name', 'N/A')}** via "
                    f"{r.get('registrant_name', 'N/A')}{amount_str}, "
                    f"{r.get('filing_year', '')} {r.get('filing_period', '')}"
                    f"{issue_str}"
                )

        if has_fara:
            sections.append("### FARA Foreign Agent")
            regs = fara.get("registrants", []) if isinstance(fara, dict) else []
            fps = fara.get("foreign_principals", []) if isinstance(fara, dict) else []
            for r in regs[:5]:
                sections.append(
                    f"- **{r.get('registrant_name', 'N/A')}** "
                    f"(Reg #{r.get('registration_number', 'N/A')}), "
                    f"Registered: {r.get('registration_date', 'N/A')}"
                )
            for fp in fps[:5]:
                sections.append(
                    f"- Foreign Principal: **{fp.get('foreign_principal_name', 'N/A')}** "
                    f"({fp.get('state_or_country', 'N/A')})"
                )

        if has_irs:
            sections.append("### IRS 990 Nonprofit")
            orgs = irs.get("organizations", []) if isinstance(irs, dict) else []
            filings = irs.get("filings", []) if isinstance(irs, dict) else []
            for o in orgs[:3]:
                sections.append(
                    f"- **{o.get('organization_name', 'N/A')}** "
                    f"(EIN: {o.get('ein', 'N/A')}), "
                    f"{o.get('city', '')}, {o.get('state', '')}"
                )
            for f in filings[:3]:
                rev = f.get("total_revenue", "")
                rev_str = f"${rev:,.0f}" if rev and rev != "N/A" else "N/A"
                sections.append(
                    f"- Year {f.get('tax_year', 'N/A')}: Revenue {rev_str}, "
                    f"Form {f.get('form_type', 'N/A')}"
                )
        sections.append("")

    # Recent News
    news = result.get("news", [])
    if news:
        sections.append("## Recent News")
        for n in news:
            date = n.get("date", "")
            sections.append(f"- [{n['title']}]({n.get('url', '')}) — *{n['source']}* ({date})")
        sections.append("")

    # Talking Points
    talking_points = result.get("talking_points", [])
    if talking_points:
        sections.append("## Suggested Talking Points")
        for i, tp in enumerate(talking_points, 1):
            sections.append(f"{i}. **{tp['point']}**")
            if tp.get("rationale"):
                sections.append(f"   *{tp['rationale']}*")
        sections.append("")

    # Key Questions
    questions = result.get("key_questions", [])
    if questions:
        sections.append("## Key Questions to Ask")
        for q in questions:
            sections.append(f"- **{q['question']}**")
            if q.get("purpose"):
                sections.append(f"  *Purpose:* {q['purpose']}")
        sections.append("")

    # Footer
    sections.append("---")
    sections.append("*CONFIDENTIAL — FOR INTERNAL USE ONLY*")

    return "\n".join(sections)
