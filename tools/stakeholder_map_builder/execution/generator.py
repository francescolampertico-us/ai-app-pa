"""
Stakeholder Map Builder — Generator
=====================================
Four-step pipeline:
  Step 1 — Discover actors: LDA topic search + LegiScan bill sponsors + GNews context
  Step 2 — Classify actors: gpt-4o infers stance, type, and influence from discovered data
  Step 3 — Extract relationships: lobbies-for (LDA) + co-sponsors (LegiScan)
  Step 4 — Assemble and sort the final result
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from gnews import GNews
    HAS_GNEWS = True
except ImportError:
    HAS_GNEWS = False

try:
    from dotenv import load_dotenv
    _toolkit_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_toolkit_root / ".env")
except ImportError:
    pass


MODEL = "gpt-4o"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_id(name: str, prefix: str = "") -> str:
    """Create a stable, URL-safe ID from a name."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:40]
    return f"{prefix}_{slug}" if prefix else slug


def _lda_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


# ---------------------------------------------------------------------------
# Step 1: Actor discovery
# ---------------------------------------------------------------------------

def _extract_topic_keywords(policy_issue: str) -> str:
    """Extract 2-3 core policy keywords from the issue string."""
    skip_words = {
        "the", "and", "for", "of", "on", "in", "to", "a", "an", "with", "about",
        "policy", "regulation", "legislation", "bill", "act", "federal", "state",
        "reform", "law", "rules", "issue", "topic",
    }
    words = [
        w.strip(".,;:()")
        for w in policy_issue.split()
        if w.lower().strip(".,;:()") not in skip_words and len(w.strip(".,;:()")) > 1
    ]
    return " ".join(words[:3])


def discover_lda_actors(
    policy_issue: str, year: int = None, max_results: int = 30
) -> tuple[list[dict], list[dict]]:
    """
    Search LDA filings by lobbying issue topic. Extracts unique actors (lobbyists
    and their clients) plus lobbies-for edges.

    Returns:
        actors: [{id, name, organization, type, lda_amount, issue_areas, source}]
        relationships: [{from_id, to_id, type, label}]
    """
    topic_query = _extract_topic_keywords(policy_issue)
    if not topic_query:
        return [], []

    print(f"  LDA topic search: '{topic_query}'", file=sys.stderr)
    session = _lda_session()

    params = {
        "filing_specific_lobbying_issues": topic_query,
        "ordering": "-dt_posted",
        "page_size": min(max_results, 25),
    }
    if year:
        params["filing_year"] = year

    try:
        resp = session.get(
            "https://lda.gov/api/v1/filings/",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  LDA topic search error: {e}", file=sys.stderr)
        return [], []

    actors: dict[str, dict] = {}
    relationships: list[dict] = []
    seen_rel_keys: set = set()

    for filing in data.get("results", []):
        reg_name = filing.get("registrant", {}).get("name", "") or ""
        client_name = filing.get("client", {}).get("name", "") or ""
        if not reg_name or not client_name:
            continue

        # Extract issue descriptions from this filing
        issues = []
        for activity in filing.get("lobbying_activities", []):
            desc = activity.get("description", "")
            if desc:
                issues.append(desc[:150])

        amount_raw = filing.get("income") or filing.get("expenses") or None
        try:
            amount = float(amount_raw) if amount_raw else None
        except (ValueError, TypeError):
            amount = None

        filing_year = filing.get("filing_year", "")
        filing_period = filing.get("filing_period_display", "")

        # Registrant (lobbying firm)
        reg_id = _make_id(reg_name, "lobbyist")
        if reg_id not in actors:
            actors[reg_id] = {
                "id": reg_id,
                "name": reg_name,
                "organization": reg_name,
                "type": "lobbyist",
                "lda_amount": None,
                "issue_areas": [],
                "source": "LDA",
            }
        for issue in issues:
            if issue and issue not in actors[reg_id]["issue_areas"]:
                actors[reg_id]["issue_areas"].append(issue)

        # Client (the entity lobbied for — type refined by LLM)
        client_id = _make_id(client_name, "client")
        if client_id not in actors:
            actors[client_id] = {
                "id": client_id,
                "name": client_name,
                "organization": client_name,
                "type": "corporation",  # LLM will refine
                "lda_amount": 0.0,
                "issue_areas": [],
                "source": "LDA",
            }
        if amount:
            actors[client_id]["lda_amount"] = (actors[client_id]["lda_amount"] or 0.0) + amount
        for issue in issues:
            if issue and issue not in actors[client_id]["issue_areas"]:
                actors[client_id]["issue_areas"].append(issue)

        # Lobbies-for edge (deduplicated by registrant+client pair)
        rel_key = (reg_id, client_id)
        if rel_key not in seen_rel_keys:
            seen_rel_keys.add(rel_key)
            label = f"lobbies for"
            if filing_year:
                label += f" ({filing_year}"
                if filing_period:
                    label += f" {filing_period}"
                label += ")"
            relationships.append({
                "from_id": reg_id,
                "to_id": client_id,
                "type": "lobbies_for",
                "label": label,
            })

        if len(actors) // 2 >= max_results:
            break

    print(f"  LDA: {len(actors)} actors, {len(relationships)} lobbies-for edges", file=sys.stderr)
    return list(actors.values()), relationships


def discover_legislative_actors(
    policy_issue: str, state: str = "US", year: int = None, max_bills: int = 5
) -> tuple[list[dict], list[dict]]:
    """
    Search LegiScan for bills related to the policy issue. Extracts bill sponsors
    and co-sponsorship edges.

    Returns:
        actors: [{id, name, organization, type, party, role, bill_numbers, source}]
        relationships: [{from_id, to_id, type, label}]
    """
    toolkit_root = Path(__file__).resolve().parent.parent.parent
    legiscan_exec = toolkit_root / "legislative_tracker" / "execution"
    sys.path.insert(0, str(legiscan_exec))

    actors: dict[str, dict] = {}
    relationships: list[dict] = []

    try:
        from legiscan_client import LegiScanClient
        lc = LegiScanClient()

        bills = lc.search_bills(policy_issue, state=state, year=year)
        print(f"  LegiScan: {len(bills)} bills found", file=sys.stderr)

        for bill_summary in bills[:max_bills]:
            bill_id = bill_summary.get("bill_id")
            bill_number = bill_summary.get("number", "")
            bill_title = bill_summary.get("title", "")[:80]

            try:
                bill_detail = lc.get_bill(bill_id)
                sponsors = bill_detail.get("sponsors", [])
            except Exception as e:
                print(f"  Could not get bill {bill_id}: {e}", file=sys.stderr)
                continue

            bill_state = bill_summary.get("state", state)

            sponsor_ids_this_bill: list[str] = []
            primary_ids: list[str] = []

            for sponsor in sponsors:
                name = sponsor.get("name", "").strip()
                if not name:
                    continue
                actor_id = _make_id(name, "leg")
                role = sponsor.get("role", "cosponsor")

                if actor_id not in actors:
                    actors[actor_id] = {
                        "id": actor_id,
                        "name": name,
                        "organization": bill_state,
                        "type": "legislator",
                        "party": sponsor.get("party", ""),
                        "role": role,
                        "bill_numbers": [],
                        "lda_amount": None,
                        "issue_areas": [bill_title] if bill_title else [],
                        "source": "LegiScan",
                    }
                else:
                    if bill_title and bill_title not in actors[actor_id]["issue_areas"]:
                        actors[actor_id]["issue_areas"].append(bill_title)

                if bill_number and bill_number not in actors[actor_id]["bill_numbers"]:
                    actors[actor_id]["bill_numbers"].append(bill_number)

                sponsor_ids_this_bill.append(actor_id)
                if "primary" in role.lower():
                    primary_ids.append(actor_id)

            # Co-sponsor edges: primary → cosponsors
            non_primary_ids = [sid for sid in sponsor_ids_this_bill if sid not in primary_ids]
            for p_id in primary_ids:
                for co_id in non_primary_ids:
                    if p_id != co_id:
                        relationships.append({
                            "from_id": p_id,
                            "to_id": co_id,
                            "type": "co_sponsors",
                            "label": f"co-sponsors {bill_number}",
                        })

    except ValueError as e:
        # Missing API key — skip silently
        print(f"  LegiScan skipped: {e}", file=sys.stderr)
    except Exception as e:
        print(f"  LegiScan error: {e}", file=sys.stderr)

    # Deduplicate co-sponsor edges (treat A→B same as B→A)
    seen_pairs: set = set()
    deduped_rels: list[dict] = []
    for rel in relationships:
        pair_key = (frozenset([rel["from_id"], rel["to_id"]]), rel["type"])
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            deduped_rels.append(rel)

    print(f"  LegiScan: {len(actors)} legislators, {len(deduped_rels)} co-sponsor edges", file=sys.stderr)
    return list(actors.values()), deduped_rels


def discover_news_snippets(policy_issue: str, max_results: int = 20) -> list[str]:
    """
    Fetch recent news about the policy issue. Returns title+description strings
    used as context for the classification LLM call.
    """
    if not HAS_GNEWS:
        print("  gnews not installed, skipping news context", file=sys.stderr)
        return []

    try:
        gn = GNews(language="en", country="US", period="90d", max_results=max_results)
        articles = gn.get_news(policy_issue) or []

        snippets = []
        for a in articles:
            title = a.get("title", "")
            desc = a.get("description", "")
            source = a.get("publisher", {}).get("title", "")
            date = a.get("published date", "")
            snippet = f"[{date}] {title}"
            if desc:
                snippet += f" — {desc[:150]}"
            if source:
                snippet += f" ({source})"
            snippets.append(snippet)

        print(f"  News: {len(snippets)} articles for context", file=sys.stderr)
        return snippets
    except Exception as e:
        print(f"  News search error: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Step 2: LLM classification
# ---------------------------------------------------------------------------

CLASSIFICATION_SYSTEM = """You are a political intelligence analyst mapping the stakeholder landscape for a policy issue.

You receive a JSON list of policy actors discovered from public lobbying filings (LDA), legislative records (LegiScan), and news sources. Your task is to classify each actor by stance, type, and influence.

CLASSIFICATION RULES:
1. Use the actor data and news context as primary evidence for classification.
2. For well-known organizations (major corporations, large trade associations, established nonprofits, advocacy groups), you SHOULD use your knowledge of their established policy positions — cite this as "Known policy position:" in the evidence field. Actively reduce "unknown" classifications by drawing on what you know.
3. For lobbying firms (registrants), classify as "unknown" — their stance reflects their clients', not their own. Focus stance classification on the clients they represent.
4. Use "unknown" ONLY when you have no data evidence AND genuinely no knowledge of the organization's position on this type of legislation.
5. Use "neutral" when you have evidence of a balanced, bipartisan, or deliberately uncommitted position.
6. PRESERVE each actor's "id" field exactly as given — it is used for graph rendering.
7. Include ALL actors from the input in your output — do not drop any.
8. Refine stakeholder_type based on your knowledge: e.g., "Microsoft Corporation" → corporation, "Heritage Foundation" → nonprofit, "AARP" → coalition, "Akin Gump" → lobbyist, "U.S. Chamber of Commerce" → coalition.

INFLUENCE TIER:
- high: Major institution (Fortune 500, large nonprofit >$100M revenue), large LDA spending (>$500k), primary bill sponsor, committee chair
- medium: Mid-size organization, moderate LDA activity, cosponsor
- low: Small organization, minimal LDA data, limited public profile

EVIDENCE format: 1-2 sentences. Lead with specific data from the input (LDA filing, bill number, news headline) if available. If using known policy position, write "Known policy position: [reason]." Do not fabricate specific dollar amounts or events not in the data.

Return ONLY a JSON object with this exact structure (no markdown, pure JSON):
{
  "issue_summary": "2-3 sentence factual overview of the policy landscape and key actors",
  "actors": [
    {
      "id": "PRESERVE EXACTLY as given",
      "name": "str",
      "organization": "str",
      "stakeholder_type": "legislator|lobbyist|corporation|nonprofit|coalition|other",
      "stance": "proponent|opponent|neutral|unknown",
      "influence_tier": "high|medium|low",
      "evidence": "str",
      "issue_areas": ["str"],
      "lda_amount": null,
      "notes": "str"
    }
  ],
  "proponent_summary": "1-2 sentences on the proponent coalition",
  "opponent_summary": "1-2 sentences on the opponent coalition",
  "key_coalitions": ["Known coalition or alliance name"],
  "strategic_notes": "2-3 sentences on strategic dynamics, swing actors, or notable patterns"
}"""


def classify_actors(
    client: OpenAI,
    policy_issue: str,
    raw_actors: list[dict],
    news_snippets: list[str],
) -> dict:
    """
    Single gpt-4o call. Classifies all actors by stance, type, and influence tier.
    Returns the full classification dict including top-level narrative fields.
    """
    # Trim actor data before sending to reduce prompt size and avoid truncation
    trimmed_actors = []
    for a in raw_actors:
        trimmed_actors.append({
            "id": a["id"],
            "name": a["name"],
            "organization": a.get("organization", ""),
            "type": a.get("type", "other"),
            "lda_amount": a.get("lda_amount"),
            "issue_areas": a.get("issue_areas", [])[:2],  # up to 2 issue areas for context
            "source": a.get("source", ""),
        })
    actors_json = json.dumps(trimmed_actors, indent=2)
    news_text = "\n".join(news_snippets[:10]) if news_snippets else "(none available)"

    prompt = f"""Policy issue: {policy_issue}

Discovered actors ({len(raw_actors)} total):
{actors_json}

Recent news headlines for context:
{news_text}

Classify all {len(raw_actors)} actors. Preserve every actor's id field exactly."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=8000,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        # Retry with explicit JSON reminder
        print("  LLM returned invalid JSON, retrying...", file=sys.stderr)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM + "\n\nCRITICAL: Return ONLY valid JSON, no markdown, no code blocks."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=8000,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)

    # Reconcile: ensure all input actors appear in output (re-add any the LLM dropped)
    classified_ids = {a["id"] for a in result.get("actors", [])}
    for actor in raw_actors:
        if actor["id"] not in classified_ids:
            result.setdefault("actors", []).append({
                "id": actor["id"],
                "name": actor["name"],
                "organization": actor.get("organization", ""),
                "stakeholder_type": actor.get("type", "other"),
                "stance": "unknown",
                "influence_tier": "low",
                "evidence": "Not classified — insufficient data.",
                "issue_areas": actor.get("issue_areas", []),
                "lda_amount": actor.get("lda_amount"),
                "notes": "",
            })

    return result


# ---------------------------------------------------------------------------
# Step 3: Relationship extraction
# ---------------------------------------------------------------------------

def extract_relationships(
    lda_rels: list[dict],
    leg_rels: list[dict],
    actors: list[dict],
    max_edges: int = 30,
) -> list[dict]:
    """
    Filter relationships to only include actors that exist in the classified list.
    Caps at max_edges total.
    """
    actor_ids = {a["id"] for a in actors}
    all_rels = lda_rels + leg_rels
    valid_rels = [
        r for r in all_rels
        if r["from_id"] in actor_ids and r["to_id"] in actor_ids
    ]
    return valid_rels[:max_edges]


# ---------------------------------------------------------------------------
# Step 4: Full pipeline + rendering
# ---------------------------------------------------------------------------

def build_map(
    policy_issue: str,
    scope: str = "federal",
    state: str = "US",
    year: int = None,
    include_types: list[str] = None,
) -> dict:
    """
    Run the full stakeholder map pipeline.

    Returns:
        {
            policy_issue, generated_at, issue_summary,
            actors: [classified actor dicts],
            relationships: [relationship dicts],
            proponent_summary, opponent_summary,
            key_coalitions, strategic_notes
        }
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required.")

    client = OpenAI(api_key=api_key)

    # Step 1: Discover actors from all sources
    print("Step 1a: Discovering LDA actors...", file=sys.stderr)
    lda_actors, lda_rels = discover_lda_actors(policy_issue, year=year)

    print("Step 1b: Discovering legislative actors...", file=sys.stderr)
    leg_state = state if scope == "state" else "US"
    leg_actors, leg_rels = discover_legislative_actors(policy_issue, state=leg_state, year=year)

    print("Step 1c: Fetching news context...", file=sys.stderr)
    news_snippets = discover_news_snippets(policy_issue)

    # Merge actors, deduplicate by ID first
    all_actors_dict: dict[str, dict] = {}
    for actor in lda_actors + leg_actors:
        aid = actor["id"]
        if aid not in all_actors_dict:
            all_actors_dict[aid] = actor
        else:
            # Accumulate LDA amounts and issue areas across duplicate filings
            if actor.get("lda_amount"):
                existing = all_actors_dict[aid].get("lda_amount") or 0.0
                all_actors_dict[aid]["lda_amount"] = existing + actor["lda_amount"]
            for ia in actor.get("issue_areas", []):
                if ia not in all_actors_dict[aid]["issue_areas"]:
                    all_actors_dict[aid]["issue_areas"].append(ia)

    # Secondary deduplication: merge actors with the same normalized name but different prefixes
    # (e.g. "client_national_assoc" and "lobbyist_national_assoc" are the same org)
    def _normalize_name(n: str) -> str:
        return re.sub(r"[^a-z0-9]", "", n.lower())

    norm_to_canonical: dict[str, str] = {}
    id_remap: dict[str, str] = {}  # old_id → canonical_id
    for aid, actor in list(all_actors_dict.items()):
        norm = _normalize_name(actor["name"])
        if norm in norm_to_canonical:
            canonical_id = norm_to_canonical[norm]
            canonical = all_actors_dict[canonical_id]
            # Merge: keep higher lda_amount, accumulate issue_areas
            if actor.get("lda_amount"):
                canonical["lda_amount"] = (canonical.get("lda_amount") or 0) + actor["lda_amount"]
            for ia in actor.get("issue_areas", []):
                if ia not in canonical["issue_areas"]:
                    canonical["issue_areas"].append(ia)
            # Prefer the non-lobbyist type as canonical type
            if canonical.get("type") == "lobbyist" and actor.get("type") != "lobbyist":
                canonical["type"] = actor["type"]
            id_remap[aid] = canonical_id
            del all_actors_dict[aid]
        else:
            norm_to_canonical[norm] = aid

    # Remap relationship IDs to canonical IDs
    def _remap_rels(rels: list[dict]) -> list[dict]:
        remapped = []
        for r in rels:
            r2 = dict(r)
            r2["from_id"] = id_remap.get(r["from_id"], r["from_id"])
            r2["to_id"] = id_remap.get(r["to_id"], r["to_id"])
            if r2["from_id"] != r2["to_id"]:  # drop self-loops created by merging
                remapped.append(r2)
        return remapped

    lda_rels = _remap_rels(lda_rels)
    leg_rels = _remap_rels(leg_rels)

    raw_actors = list(all_actors_dict.values())

    # Apply type filter if specified
    if include_types:
        type_map = {
            "legislators": "legislator",
            "lobbyists": "lobbyist",
            "corporations": "corporation",
            "nonprofits": "nonprofit",
        }
        allowed = {type_map[t] for t in include_types if t in type_map}
        if allowed:
            raw_actors = [a for a in raw_actors if a.get("type") in allowed]

    # Cap at 50 actors: prioritize legislators, then by LDA amount
    legislators = [a for a in raw_actors if a.get("type") == "legislator"]
    others = sorted(
        [a for a in raw_actors if a.get("type") != "legislator"],
        key=lambda a: a.get("lda_amount") or 0,
        reverse=True,
    )
    raw_actors = legislators + others
    if len(raw_actors) > 50:
        raw_actors = raw_actors[:50]
        print("  Capped at 50 actors", file=sys.stderr)

    if not raw_actors:
        raise ValueError(
            f"No actors found for '{policy_issue}'. "
            "Try broader keywords (e.g., 'AI regulation' instead of a specific bill name)."
        )

    print(f"  Total actors for classification: {len(raw_actors)}", file=sys.stderr)

    # Step 2: Classify actors
    print("Step 2: Classifying actors with gpt-4o...", file=sys.stderr)
    classification = classify_actors(client, policy_issue, raw_actors, news_snippets)
    classified_actors = classification.get("actors", [])
    print(f"  Classified {len(classified_actors)} actors", file=sys.stderr)

    # Step 3: Extract and filter relationships
    # Use raw_actors (canonical IDs, pre-LLM) — not classified_actors — so that
    # LLM ID drift doesn't silently drop all edges.
    print("Step 3: Extracting relationships...", file=sys.stderr)
    relationships = extract_relationships(lda_rels, leg_rels, raw_actors)
    print(f"  {len(relationships)} relationships retained", file=sys.stderr)

    # Sort actors: proponents → opponents → neutral → unknown, then high → low influence
    stance_order = {"proponent": 0, "opponent": 1, "neutral": 2, "unknown": 3}
    tier_order = {"high": 0, "medium": 1, "low": 2}
    classified_actors.sort(key=lambda a: (
        stance_order.get(a.get("stance", "unknown"), 3),
        tier_order.get(a.get("influence_tier", "low"), 2),
    ))

    return {
        "policy_issue": policy_issue,
        "generated_at": datetime.now().strftime("%B %d, %Y"),
        "issue_summary": classification.get("issue_summary", ""),
        "actors": classified_actors,
        "relationships": relationships,
        "proponent_summary": classification.get("proponent_summary", ""),
        "opponent_summary": classification.get("opponent_summary", ""),
        "key_coalitions": classification.get("key_coalitions", []),
        "strategic_notes": classification.get("strategic_notes", ""),
    }


def render_markdown(result: dict) -> str:
    """Render the stakeholder map as a formatted markdown document."""
    sections = []
    issue = result["policy_issue"]
    date = result.get("generated_at", "")

    sections.append(f"# Stakeholder Map: {issue}")
    sections.append(f"**Generated:** {date}\n")
    sections.append("---\n")

    if result.get("issue_summary"):
        sections.append("## Issue Overview")
        sections.append(result["issue_summary"])
        sections.append("")

    actors = result.get("actors", [])
    proponents = [a for a in actors if a.get("stance") == "proponent"]
    opponents = [a for a in actors if a.get("stance") == "opponent"]
    neutral = [a for a in actors if a.get("stance") in ("neutral", "unknown")]

    def _actor_line(a):
        parts = [f"**{a['name']}**"]
        if a.get("stakeholder_type"):
            parts.append(f"({a['stakeholder_type'].title()}")
            if a.get("organization") and a["organization"] != a["name"]:
                parts[-1] += f", {a['organization']}"
            parts[-1] += ")"
        if a.get("evidence"):
            parts.append(f"— {a['evidence']}")
        tier = a.get("influence_tier", "")
        if tier:
            parts.append(f"*[{tier} influence]*")
        return " ".join(parts)

    if proponents:
        sections.append(f"## Proponents ({len(proponents)})")
        if result.get("proponent_summary"):
            sections.append(f"*{result['proponent_summary']}*\n")
        for a in proponents:
            sections.append(f"- {_actor_line(a)}")
        sections.append("")

    if opponents:
        sections.append(f"## Opponents ({len(opponents)})")
        if result.get("opponent_summary"):
            sections.append(f"*{result['opponent_summary']}*\n")
        for a in opponents:
            sections.append(f"- {_actor_line(a)}")
        sections.append("")

    if neutral:
        sections.append(f"## Neutral / Unknown ({len(neutral)})")
        for a in neutral:
            line = f"- **{a['name']}**"
            if a.get("notes"):
                line += f" — {a['notes']}"
            sections.append(line)
        sections.append("")

    relationships = result.get("relationships", [])
    if relationships:
        # Build name lookup
        id_to_name = {a["id"]: a["name"] for a in actors}
        sections.append("## Key Relationships")
        for r in relationships[:15]:
            from_name = id_to_name.get(r["from_id"], r["from_id"])
            to_name = id_to_name.get(r["to_id"], r["to_id"])
            sections.append(f"- **{from_name}** {r['label']} **{to_name}**")
        sections.append("")

    coalitions = result.get("key_coalitions", [])
    if coalitions:
        sections.append("## Key Coalitions")
        for c in coalitions:
            sections.append(f"- {c}")
        sections.append("")

    if result.get("strategic_notes"):
        sections.append("## Strategic Notes")
        sections.append(result["strategic_notes"])
        sections.append("")

    sections.append("---")
    sections.append("*Stance classifications are LLM-inferred from public data — verify before strategic use*")

    return "\n".join(sections)
