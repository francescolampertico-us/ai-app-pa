"""
Stakeholder Map Builder — Generator
=====================================
Four-step pipeline:
  Step 1 — Discover actors: LDA topic search + LegiScan bill sponsors + GNews context
  Step 2 — Classify actors: gpt-4.1 infers stance, type, and influence from discovered data
  Step 3 — Extract relationships: lobbies-for (LDA) + co-sponsors (LegiScan)
  Step 4 — Assemble and sort the final result
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
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
    _toolkit_root = Path(__file__).resolve().parent.parent.parent.parent
    load_dotenv(_toolkit_root / ".env")
except ImportError:
    pass


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


SOURCE_LABELS = {
    "LDA": "Structured source",
    "LegiScan": "Structured source",
    "brave": "Web source",
    "seeded": "Seeded",
    "inferred": "Inferred",
}


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _merge_source_metadata(actor: dict, source_name: str, source_type: Optional[str] = None) -> None:
    source_type = source_type or SOURCE_LABELS.get(source_name, "Structured source")
    names = list(actor.get("source_names") or [])
    if source_name and source_name not in names:
        names.append(source_name)
    actor["source_names"] = names

    types = list(actor.get("source_types") or [])
    if source_type and source_type not in types:
        types.append(source_type)
    actor["source_types"] = types
    actor["source_labels"] = list(types)
    actor["source"] = ", ".join(names) if names else source_name or actor.get("source", "")
    actor["source_summary"] = " + ".join(types) if types else actor.get("source_summary", "—")


def _allowed_actor_types(include_types: list[str] = None) -> set[str]:
    type_map = {
        "legislators": "legislator",
        "lobbyists": "lobbyist",
        "corporations": "corporation",
        "nonprofits": "nonprofit",
    }
    if not include_types:
        return set()
    return {type_map[t] for t in include_types if t in type_map}


def _filter_actors_by_allowed_types(actors: list[dict], allowed_types: set[str]) -> list[dict]:
    if not allowed_types:
        return actors
    filtered = []
    for actor in actors:
        actor_type = actor.get("type") or actor.get("stakeholder_type") or ""
        if actor_type in allowed_types:
            filtered.append(actor)
    return filtered


# ---------------------------------------------------------------------------
# Step 1: Actor discovery
# ---------------------------------------------------------------------------

def generate_lda_queries(client: OpenAI, policy_issue: str) -> list[str]:
    """
    Use the LLM to generate 2-3 targeted LDA search phrases for the policy issue.
    Falls back to naive keyword extraction if the LLM call fails.
    """
    prompt = (
        f"Policy issue: {policy_issue}\n\n"
        "Generate 2-3 short search phrases (3-5 words each) that would find relevant "
        "lobbying filings in the LDA database for this issue. The LDA database indexes "
        "the free-text lobbying issue description field — so use the specific policy "
        "terminology lobbyists actually use (e.g., 'drug price negotiation', "
        "'Medicare Part D', 'Inflation Reduction Act'). Return ONLY a JSON object:\n"
        '{"queries": ["phrase one", "phrase two", "phrase three"]}'
    )
    try:
        response = client.chat.completions.create(
            model=_active_model(MODEL),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            **_response_format_kwarg(),
        )
        data = _parse_json_content(response.choices[0].message.content)
        queries = [q.strip() for q in data.get("queries", []) if q.strip()]
        if queries:
            return queries[:3]
    except Exception as e:
        print(f"  LDA query generation failed, using fallback: {e}", file=sys.stderr)
    # Fallback: simple keyword extraction
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
    return [" ".join(words[:3])] if words else [policy_issue[:40]]


def discover_lda_actors(
    queries: list[str], year: int = None, max_results: int = 30
) -> tuple[list[dict], list[dict]]:
    """
    Search LDA filings using a list of targeted search phrases. Merges results
    across all queries, deduplicating by actor ID.

    Returns:
        actors: [{id, name, organization, type, lda_amount, issue_areas, source}]
        relationships: [{from_id, to_id, type, label, source}]
    """
    if not queries:
        return [], []

    session = _lda_session()
    all_actors: dict[str, dict] = {}
    all_relationships: list[dict] = []
    seen_rel_keys: set = set()

    for topic_query in queries:
        print(f"  LDA search: '{topic_query}'", file=sys.stderr)

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
            print(f"  LDA search error for '{topic_query}': {e}", file=sys.stderr)
            continue

        for filing in data.get("results", []):
            reg_name = filing.get("registrant", {}).get("name", "") or ""
            client_name = filing.get("client", {}).get("name", "") or ""
            if not reg_name or not client_name:
                continue

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

            reg_id = _make_id(reg_name, "lobbyist")
            if reg_id not in all_actors:
                all_actors[reg_id] = {
                    "id": reg_id,
                    "name": reg_name,
                    "organization": reg_name,
                    "type": "lobbyist",
                    "lda_amount": None,
                    "issue_areas": [],
                    "source": "LDA",
                    "source_names": ["LDA"],
                    "source_types": ["Structured source"],
                    "source_labels": ["Structured source"],
                    "source_summary": "Structured source",
                }
            else:
                _merge_source_metadata(all_actors[reg_id], "LDA", "Structured source")
            for issue in issues:
                if issue and issue not in all_actors[reg_id]["issue_areas"]:
                    all_actors[reg_id]["issue_areas"].append(issue)

            client_id = _make_id(client_name, "client")
            if client_id not in all_actors:
                all_actors[client_id] = {
                    "id": client_id,
                    "name": client_name,
                    "organization": client_name,
                    "type": "corporation",
                    "lda_amount": 0.0,
                    "issue_areas": [],
                    "source": "LDA",
                    "source_names": ["LDA"],
                    "source_types": ["Structured source"],
                    "source_labels": ["Structured source"],
                    "source_summary": "Structured source",
                }
            else:
                _merge_source_metadata(all_actors[client_id], "LDA", "Structured source")
            if amount:
                all_actors[client_id]["lda_amount"] = (all_actors[client_id]["lda_amount"] or 0.0) + amount
            for issue in issues:
                if issue and issue not in all_actors[client_id]["issue_areas"]:
                    all_actors[client_id]["issue_areas"].append(issue)

            rel_key = (reg_id, client_id)
            if rel_key not in seen_rel_keys:
                seen_rel_keys.add(rel_key)
                label = "lobbies for"
                if filing_year:
                    label += f" ({filing_year}"
                    if filing_period:
                        label += f" {filing_period}"
                    label += ")"
                all_relationships.append({
                    "from_id": reg_id,
                    "to_id": client_id,
                    "type": "lobbies_for",
                    "label": label,
                    "source": "data",
                })

        print(f"  LDA: {len(all_actors)} actors so far", file=sys.stderr)

    print(f"  LDA total: {len(all_actors)} actors, {len(all_relationships)} lobbies-for edges", file=sys.stderr)
    return list(all_actors.values()), all_relationships


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
                        "source_names": ["LegiScan"],
                        "source_types": ["Structured source"],
                        "source_labels": ["Structured source"],
                        "source_summary": "Structured source",
                    }
                else:
                    _merge_source_metadata(actors[actor_id], "LegiScan", "Structured source")
                    if bill_title and bill_title not in actors[actor_id]["issue_areas"]:
                        actors[actor_id]["issue_areas"].append(bill_title)

                if bill_number and bill_number not in actors[actor_id]["bill_numbers"]:
                    actors[actor_id]["bill_numbers"].append(bill_number)

                sponsor_ids_this_bill.append(actor_id)
                if "primary" in role.lower():
                    primary_ids.append(actor_id)

            # Co-sponsor edges: primary → cosponsors.
            # If no primary is labeled (LegiScan often returns role="Rep"/"Sen"),
            # fall back to connecting all sponsors on the same bill to each other.
            non_primary_ids = [sid for sid in sponsor_ids_this_bill if sid not in primary_ids]
            if primary_ids:
                for p_id in primary_ids:
                    for co_id in non_primary_ids:
                        if p_id != co_id:
                            relationships.append({
                                "from_id": p_id,
                                "to_id": co_id,
                                "type": "co_sponsors",
                                "label": f"co-sponsors {bill_number}",
                            })
            else:
                # No primary label — connect all sponsors as mutual co-sponsors
                for i, sid_a in enumerate(sponsor_ids_this_bill):
                    for sid_b in sponsor_ids_this_bill[i + 1:]:
                        relationships.append({
                            "from_id": sid_a,
                            "to_id": sid_b,
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


def discover_brave_context(policy_issue: str, max_results: int = 8) -> list[str]:
    """
    Supplemental Brave web search for public issue pages, testimony, statements,
    coalition pages, and reports. Used as corroborating context, not backbone data.
    """
    api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if not api_key:
        print("  Brave search not configured, skipping supplemental web discovery", file=sys.stderr)
        return []

    queries = [
        f"\"{policy_issue}\" testimony coalition report statement",
        f"\"{policy_issue}\" comment letter advocacy organization",
    ]
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    snippets: list[str] = []
    seen_urls: set[str] = set()
    for query in queries:
        try:
            resp = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params={"q": query, "count": max_results, "search_lang": "en", "country": "us"},
                timeout=12,
            )
            resp.raise_for_status()
            payload = resp.json() or {}
            for item in payload.get("web", {}).get("results", []) or []:
                url = item.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                title = item.get("title", "")
                desc = item.get("description", "")
                source = item.get("profile", {}).get("name", "")
                parts = [part for part in [title, desc[:180] if desc else "", f"({source})" if source else "", url] if part]
                snippets.append(" — ".join(parts))
        except Exception as exc:
            print(f"  Brave supplemental context search error for '{query}': {exc}", file=sys.stderr)
    print(f"  Brave: {len(snippets)} supplemental web context items", file=sys.stderr)
    return snippets[:12]


BRAVE_ACTOR_SYSTEM = """You are helping expand a stakeholder map with supplemental web discovery.

Use the provided Brave search snippets to identify 0-6 additional actors that appear relevant to the issue and are not already in the structured-source actor list.

Rules:
- Treat Brave results as supplemental discovery and corroboration only.
- Prefer actors tied to testimony, coalition membership, public statements, comment letters, reports, or issue pages.
- Do not repeat actors already discovered from structured sources.
- Do not invent organizations not grounded in the snippets.
- Return only actors that look materially relevant to the issue.

Return ONLY JSON:
{
  "actors": [
    {
      "name": "Actor name",
      "type": "legislator|lobbyist|corporation|nonprofit|coalition|other",
      "evidence": "Short snippet-backed reason this actor appears relevant"
    }
  ]
}"""


def discover_brave_actors(
    client: OpenAI,
    policy_issue: str,
    existing_names: set[str],
    brave_snippets: list[str],
) -> list[dict]:
    if not brave_snippets:
        return []

    prompt = (
        f"Policy issue: {policy_issue}\n\n"
        f"Existing actors to avoid duplicating:\n{', '.join(sorted(existing_names)[:80])}\n\n"
        "Brave search snippets:\n"
        + "\n".join(f"- {snippet}" for snippet in brave_snippets[:12])
    )
    try:
        response = client.chat.completions.create(
            model=_active_model(MODEL),
            messages=[
                {"role": "system", "content": BRAVE_ACTOR_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            **_response_format_kwarg(),
        )
        data = _parse_json_content(response.choices[0].message.content)
        nominees = data.get("actors", [])
    except Exception as exc:
        print(f"  Brave actor extraction failed: {exc}", file=sys.stderr)
        return []

    discovered = []
    norm_existing = {_normalize_name(name) for name in existing_names}
    for actor in nominees:
        name = str(actor.get("name", "")).strip()
        if not name:
            continue
        norm = _normalize_name(name)
        if norm in norm_existing:
            continue
        discovered.append({
            "id": _make_id(name, "web"),
            "name": name,
            "organization": name,
            "type": actor.get("type", "other"),
            "stakeholder_type": actor.get("type", "other"),
            "lda_amount": None,
            "issue_areas": [],
            "source": "brave",
            "source_names": ["brave"],
            "source_types": ["Web source"],
            "source_labels": ["Web source"],
            "source_summary": "Web source",
            "observed_evidence": actor.get("evidence", ""),
            "evidence": actor.get("evidence", ""),
        })
        norm_existing.add(norm)

    print(f"  Brave: discovered {len(discovered)} supplemental actors", file=sys.stderr)
    return discovered[:6]


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
      "confidence_label": "confirmed|likely|possible|unknown",
      "observed_evidence": "str",
      "inferred_rationale": "str",
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
    Single gpt-4.1 call. Classifies all actors by stance, type, and influence tier.
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
            "observed_evidence": a.get("observed_evidence", ""),
        })
    actors_json = json.dumps(trimmed_actors, indent=2)
    news_text = "\n".join(news_snippets[:10]) if news_snippets else "(none available)"
    brave_text = "\n".join(
        f"- {a.get('name', '')}: {a.get('observed_evidence', '')}"
        for a in raw_actors
        if "Web source" in (a.get("source_types") or []) and a.get("observed_evidence")
    ) or "(none available)"

    prompt = f"""Policy issue: {policy_issue}

Discovered actors ({len(raw_actors)} total):
{actors_json}

Recent news headlines for context:
{news_text}

Supplemental Brave web evidence:
{brave_text}

Classify all {len(raw_actors)} actors. Preserve every actor's id field exactly."""

    try:
        response = client.chat.completions.create(
            model=_active_model(MODEL),
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            **_max_tokens_kwarg(8000),
            **_response_format_kwarg(),
        )
        result = _parse_json_content(response.choices[0].message.content)
    except json.JSONDecodeError:
        # Retry with explicit JSON reminder
        print("  LLM returned invalid JSON, retrying...", file=sys.stderr)
        response = client.chat.completions.create(
            model=_active_model(MODEL),
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM + "\n\nCRITICAL: Return ONLY valid JSON, no markdown, no code blocks."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            **_max_tokens_kwarg(8000),
            **_response_format_kwarg(),
        )
        result = _parse_json_content(response.choices[0].message.content)

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
                "confidence_label": "unknown",
                "observed_evidence": "",
                "inferred_rationale": "",
                "evidence": "Not classified — insufficient data.",
                "issue_areas": actor.get("issue_areas", []),
                "lda_amount": actor.get("lda_amount"),
                "notes": "",
                "source": actor.get("source", ""),
                "source_names": actor.get("source_names", []),
                "source_types": actor.get("source_types", []),
                "source_labels": actor.get("source_labels", []),
                "source_summary": actor.get("source_summary", ""),
            })

    for actor in result.get("actors", []):
        observed = str(actor.get("observed_evidence", "") or "").strip()
        inferred = str(actor.get("inferred_rationale", "") or "").strip()
        confidence = str(actor.get("confidence_label", "") or "").strip().lower()
        if confidence not in {"confirmed", "likely", "possible", "unknown"}:
            confidence = "unknown"
        actor["confidence_label"] = confidence

        evidence_parts = []
        if observed:
            evidence_parts.append(f"Observed: {observed}")
        if inferred:
            evidence_parts.append(f"Inferred: {inferred}")
        if not evidence_parts and actor.get("evidence"):
            evidence_parts.append(str(actor.get("evidence")))
        actor["evidence"] = " ".join(evidence_parts).strip() or "Not classified — insufficient data."

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
    Tags all returned edges as source="data". Caps at max_edges total.
    """
    actor_ids = {a["id"] for a in actors}
    all_rels = lda_rels + leg_rels
    valid_rels = []
    for r in all_rels:
        if r["from_id"] in actor_ids and r["to_id"] in actor_ids:
            r2 = dict(r)
            r2["source"] = "data"
            valid_rels.append(r2)
    return valid_rels[:max_edges]


# ---------------------------------------------------------------------------
# Step 3b: LLM-inferred relationships
# ---------------------------------------------------------------------------
# Step 2b: Known-actor seeding
# ---------------------------------------------------------------------------

SEED_SYSTEM = """You are a political intelligence analyst.

Given a policy issue and an existing actor list, identify the 5-8 most influential stakeholders that are widely known to be active on this issue but are MISSING from the current map. These often include actors that use different filing names, operate through coalitions, or are primarily active through advocacy rather than formal lobbying.

BALANCE REQUIREMENT: If the existing map is skewed toward one side (e.g., mostly opponents), prioritise nominating actors from the underrepresented side to create a balanced picture.

Focus on: major trade associations, well-known advocacy groups, large corporations with documented positions, prominent legislators, patient/consumer groups — whichever are most relevant.

Return ONLY a JSON object (no markdown):
{
  "known_actors": [
    {
      "name": "Official organization name",
      "type": "legislator|lobbyist|corporation|nonprofit|coalition|other",
      "stance": "proponent|opponent|neutral|unknown",
      "influence_tier": "high|medium|low",
      "evidence": "1 sentence explaining why this actor matters for this issue"
    }
  ]
}"""


def seed_known_actors(
    client: OpenAI,
    policy_issue: str,
    existing_names: set[str],
    stance_counts: dict = None,
) -> list[dict]:
    """
    Ask the LLM to nominate well-known stakeholders not caught by LDA/LegiScan.
    Skips any actor whose normalized name already appears in existing_names.
    stance_counts — e.g. {"proponent": 5, "opponent": 20} — guides the LLM toward
    the underrepresented side.
    Returns actors tagged with source='seeded'.
    """
    balance_note = ""
    if stance_counts:
        n_pro = stance_counts.get("proponent", 0)
        n_opp = stance_counts.get("opponent", 0)
        if n_opp > n_pro * 1.5:
            balance_note = (
                f"\nNOTE: The current map has {n_opp} opponents but only {n_pro} proponents. "
                "Please prioritise proponent actors (supporters, beneficiary groups, allied legislators) "
                "to balance the picture."
            )
        elif n_pro > n_opp * 1.5:
            balance_note = (
                f"\nNOTE: The current map has {n_pro} proponents but only {n_opp} opponents. "
                "Please prioritise opponent actors (industry, trade associations opposing this policy) "
                "to balance the picture."
            )

    prompt = (
        f"Policy issue: {policy_issue}\n"
        f"{balance_note}\n"
        f"Already discovered actors (skip these): {', '.join(sorted(existing_names)[:40])}\n\n"
        "Which major stakeholders are missing? List the 5-8 most influential actors "
        "known to be active on this issue that are not in the above list."
    )
    try:
        response = client.chat.completions.create(
            model=_active_model(MODEL),
            messages=[
                {"role": "system", "content": SEED_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            **_response_format_kwarg(),
        )
        data = _parse_json_content(response.choices[0].message.content)
        nominees = data.get("known_actors", [])
    except Exception as e:
        print(f"  Seeding failed: {e}", file=sys.stderr)
        return []

    def _norm(n: str) -> str:
        return re.sub(r"[^a-z0-9]", "", n.lower())

    norm_existing = {_norm(n) for n in existing_names}
    seeded = []
    for actor in nominees:
        name = actor.get("name", "").strip()
        if not name or _norm(name) in norm_existing:
            continue
        actor_id = _make_id(name, "known")
        seeded.append({
            "id": actor_id,
            "name": name,
            "organization": name,
            "type": actor.get("type", "other"),
            "stakeholder_type": actor.get("type", "other"),
            "stance": actor.get("stance", "unknown"),
            "influence_tier": actor.get("influence_tier", "medium"),
            "confidence_label": actor.get("confidence_label", "possible"),
            "observed_evidence": "",
            "inferred_rationale": actor.get("evidence", ""),
            "evidence": actor.get("evidence", ""),
            "lda_amount": None,
            "issue_areas": [],
            "bill_numbers": None,
            "source": "seeded",
            "source_names": ["seeded"],
            "source_types": ["Seeded"],
            "source_labels": ["Seeded"],
            "source_summary": "Seeded",
        })
        norm_existing.add(_norm(name))

    print(f"  Seeded {len(seeded)} known actors not in LDA/LegiScan", file=sys.stderr)
    return seeded


# ---------------------------------------------------------------------------

RELATIONSHIP_SYSTEM = """You are a political intelligence analyst building a stakeholder network map.

You will receive a list of classified policy actors (with their stances and types) for a specific policy issue.
Your task is to infer the most significant RELATIONSHIPS between these actors based on your knowledge of their real-world connections, coalitions, and interactions.

RELATIONSHIP TYPES — use exactly one:
- "allied":          Two actors who actively coordinate or share the same policy goal (same or compatible stances)
- "opposed":         Two actors in direct conflict over this issue (opposing stances with active friction)
- "lobbies_for":     A lobbyist/firm hired by or representing another actor
- "funds":           A foundation, PAC, or donor that funds or grants to another actor
- "coalition_with":  An actor that is a formal or informal member of the same coalition as another
- "targets":         An advocacy actor that is running campaigns directed at a specific government actor

RULES:
- Only assert relationships you are reasonably confident exist based on known public information
- Do NOT fabricate relationships — if you are not confident, omit the pair
- Prefer well-known, verifiable connections over speculative ones
- Aim for 10-25 edges total — enough to form a real network but not noise
- Each actor's "id" field is provided — use it exactly in from_id / to_id
- Focus on edges that cross stance lines (allied within a coalition, opposed across coalitions) — these are most analytically valuable
- Include at least a few cross-stance edges if they exist
- Trade association membership is a strong, reliable signal — always connect member organizations to their trade associations: e.g., pharma companies → PhRMA or BIO; health insurers → AHIP; banks → ABA; tech companies → ITAA or TechNet. If a trade association is in the actor list, connect all of its member companies that are also in the list.
- Do NOT leave actors isolated if you can reasonably infer a coalition_with or allied relationship

Return ONLY a JSON object (no markdown):
{
  "relationships": [
    {
      "from_id": "exact_id_from_input",
      "to_id": "exact_id_from_input",
      "type": "allied|opposed|lobbies_for|funds|coalition_with|targets",
      "label": "short human-readable description (max 8 words)"
    }
  ]
}"""


def infer_relationships(
    client: OpenAI,
    policy_issue: str,
    classified_actors: list[dict],
) -> list[dict]:
    """
    Ask the LLM to infer real-world relationships between the classified actors.
    Returns a list of relationship dicts with from_id, to_id, type, label.
    Falls back to empty list on any failure.
    """
    if not classified_actors:
        return []

    # Build a compact actor list for the prompt
    actor_lines = []
    for a in classified_actors:
        actor_lines.append(
            f'  id="{a["id"]}" name="{a["name"]}" type="{a.get("stakeholder_type","")}" '
            f'stance="{a.get("stance","")}" influence="{a.get("influence_tier","")}"'
        )

    prompt = (
        f"Policy issue: {policy_issue}\n\n"
        f"Classified actors ({len(classified_actors)} total):\n"
        + "\n".join(actor_lines)
        + "\n\nInfer the real relationships between these actors. Use the id values exactly as shown."
    )

    try:
        response = client.chat.completions.create(
            model=_active_model(MODEL),
            messages=[
                {"role": "system", "content": RELATIONSHIP_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            **_max_tokens_kwarg(3000),
            **_response_format_kwarg(),
        )
        data = _parse_json_content(response.choices[0].message.content)
        rels = data.get("relationships", [])

        # Validate: drop any edge referencing an unknown actor ID; tag all as inferred
        known_ids = {a["id"] for a in classified_actors}
        valid = []
        for r in rels:
            if (r.get("from_id") in known_ids
                    and r.get("to_id") in known_ids
                    and r.get("from_id") != r.get("to_id")):
                r2 = dict(r)
                r2["source"] = "inferred"
                valid.append(r2)
        print(f"  LLM inferred {len(valid)} relationships ({len(rels) - len(valid)} dropped — unknown IDs)", file=sys.stderr)
        return valid

    except Exception as e:
        print(f"  Relationship inference failed: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Step 4a: LLM strategic analysis (powered by SNA results)
# ---------------------------------------------------------------------------

STRATEGIC_ANALYSIS_SYSTEM = """You are a senior public affairs strategist. You have been given a stakeholder network map for a policy issue, enriched with Social Network Analysis (SNA) metrics.

Your task is to produce a concise, decision-ready strategic analysis that a public affairs team can act on immediately.
Use confirmed and likely evidence preferentially. If an action depends on a possible or unknown classification, say so directly instead of overstating certainty.

The analysis must be grounded in the provided data — do NOT fabricate actors, relationships, or events not in the input.

Return ONLY a JSON object (no markdown):
{
  "landscape": "2-3 sentences: what is the overall power balance? Who dominates the network? Is there a structural advantage for one side?",
  "dynamics": "2-3 sentences: what is the key tension or pivot point right now? What structural feature of this network creates opportunity or risk?",
  "coalition_opportunities": [
    {
      "opportunity": "1 concrete coalition-building action",
      "support": ["Observed evidence, named actor, or network fact that supports this"],
      "metrics": ["Metric or structural cue if relevant"],
      "confidence": "confirmed|likely|possible|unknown"
    }
  ],
  "risks": [
    {
      "risk": "1 specific risk derived from the network structure or actor positions",
      "support": ["Observed evidence, named actor, or network fact that supports this"],
      "metrics": ["Metric or structural cue if relevant"],
      "confidence": "confirmed|likely|possible|unknown"
    }
  ],
  "immediate_actions": [
    {
      "actor": "named actor or coalition",
      "action": "specific tactic",
      "why": "why this action follows from the evidence",
      "support": ["Observed evidence, named actor fact, or relationship"],
      "metrics": ["Metric or structural cue if relevant"],
      "confidence": "confirmed|likely|possible|unknown"
    }
  ],
  "swing_actor_strategy": {
    "summary": "1-2 sentences on how to approach the highest-value persuadable actor identified in the map, if any",
    "support": ["Observed evidence, named actor fact, or network fact"],
    "metrics": ["Metric or structural cue if relevant"],
    "confidence": "confirmed|likely|possible|unknown"
  }
}

Rules:
- Separate observed support from inference where possible.
- Every coalition opportunity, risk, and immediate action must cite visible support.
- Use plain-English metric names in the analysis: "Bridge Role", "Connection Reach", "Strategic Relevance", and "Estimated Influence Tier".
- Metrics should be short phrases like "Bridge Role 0.24" or "Strategic Relevance 52", not full prose.
- Do not imply certainty that the input does not support.
}"""


def _normalize_confidence_label(value: str) -> str:
    value = str(value or "").strip().lower()
    return value if value in {"confirmed", "likely", "possible", "unknown"} else "unknown"


def _normalize_support_block(items, text_key: str) -> list[dict]:
    normalized = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, str):
                normalized.append({
                    text_key: item,
                    "support": [],
                    "metrics": [],
                    "confidence": "unknown",
                })
                continue
            if not isinstance(item, dict):
                continue
            normalized.append({
                text_key: item.get(text_key, "") or item.get("summary", "") or item.get("risk", "") or item.get("opportunity", ""),
                "support": [s for s in item.get("support", []) if s],
                "metrics": [m for m in item.get("metrics", []) if m],
                "confidence": _normalize_confidence_label(item.get("confidence", "unknown")),
            })
    return [item for item in normalized if item.get(text_key)]


def _normalize_strategic_analysis(data: dict) -> dict:
    swing = data.get("swing_actor_strategy", {})
    if isinstance(swing, str):
        swing = {"summary": swing, "support": [], "metrics": [], "confidence": "unknown"}
    elif not isinstance(swing, dict):
        swing = {"summary": "", "support": [], "metrics": [], "confidence": "unknown"}
    return {
        "landscape": data.get("landscape", ""),
        "dynamics": data.get("dynamics", ""),
        "coalition_opportunities": _normalize_support_block(data.get("coalition_opportunities", []), "opportunity"),
        "risks": _normalize_support_block(data.get("risks", []), "risk"),
        "immediate_actions": [
            {
                "actor": item.get("actor", ""),
                "action": item.get("action", ""),
                "why": item.get("why", ""),
                "support": [s for s in item.get("support", []) if s],
                "metrics": [m for m in item.get("metrics", []) if m],
                "confidence": _normalize_confidence_label(item.get("confidence", "unknown")),
            }
            for item in data.get("immediate_actions", [])
            if isinstance(item, dict) and (item.get("actor") or item.get("action") or item.get("why"))
        ] if isinstance(data.get("immediate_actions"), list) and any(isinstance(item, dict) for item in data.get("immediate_actions", [])) else [
            {
                "actor": "",
                "action": entry,
                "why": "",
                "support": [],
                "metrics": [],
                "confidence": "unknown",
            }
            for entry in data.get("immediate_actions", [])
            if isinstance(entry, str) and entry
        ],
        "swing_actor_strategy": {
            "summary": swing.get("summary", ""),
            "support": [s for s in swing.get("support", []) if s],
            "metrics": [m for m in swing.get("metrics", []) if m],
            "confidence": _normalize_confidence_label(swing.get("confidence", "unknown")),
        },
    }


def generate_strategic_analysis(
    client: OpenAI,
    policy_issue: str,
    result: dict,
    analytics: dict,
) -> dict:
    """
    LLM call that synthesises the stakeholder map + SNA analytics into a
    decision-ready strategic brief. Returns a dict with the structured analysis.
    Falls back to a minimal dict on any failure.
    """
    actors = result.get("actors", [])
    relationships = result.get("relationships", [])
    id_to_name = {a["id"]: a["name"] for a in actors}

    # Build compact actor summary
    actor_lines = []
    for a in actors[:40]:  # cap to avoid token overflow
        score = a.get("composite_score", 0)
        bw = a.get("betweenness_centrality", 0.0)
        deg = a.get("degree_centrality", 0.0)
        line = (
            f'  {a["name"]} | {a.get("stakeholder_type","?")} | '
            f'stance={a.get("stance","?")} | Estimated Influence Tier={a.get("influence_tier","?")} | '
            f'confidence={a.get("confidence_label","unknown")} | Strategic Relevance={score} | Bridge Role={bw:.3f} | Connection Reach={deg:.3f} | '
            f'observed={a.get("observed_evidence","")[:120]} | inferred={a.get("inferred_rationale","")[:120]}'
        )
        actor_lines.append(line)

    # Key SNA figures
    brokers = analytics.get("brokers", [])
    broker_names = ", ".join(b["name"] for b in brokers[:3]) if brokers else "none identified"
    persuadables = analytics.get("top_persuadables", [])
    persuadable_names = ", ".join(a["name"] for a in persuadables[:3]) if persuadables else "none"
    density = analytics.get("network_density", 0.0)
    communities = analytics.get("communities", 0)
    cohesion = analytics.get("coalition_cohesion", {})
    top_opponents = analytics.get("top_opponents", [])
    top_proponents = analytics.get("top_proponents", [])
    strategic_summary = analytics.get("strategic_summary", "")

    prompt = f"""Policy issue: {policy_issue}

ACTOR MAP ({len(actors)} actors):
{chr(10).join(actor_lines)}

NETWORK METRICS:
- Density: {density:.3f} | Communities: {communities}
- Proponent coalition: {cohesion.get('proponent_cohesion_label','?')} (cohesion={cohesion.get('proponent_cohesion',0):.2f})
- Opponent coalition: {cohesion.get('opponent_cohesion_label','?')} (cohesion={cohesion.get('opponent_cohesion',0):.2f})
- Bridge actors: {broker_names}
- Top swing actors: {persuadable_names}
- Network summary: {strategic_summary}

    TOP OPPONENTS (by Strategic Relevance): {', '.join(a['name'] for a in top_opponents[:3])}
    TOP PROPONENTS (by Strategic Relevance): {', '.join(a['name'] for a in top_proponents[:3])}

KEY RELATIONSHIPS (sample of {min(len(relationships), 12)}):
{chr(10).join(f'  {id_to_name.get(r["from_id"], r["from_id"])} --[{r["type"]}]--> {id_to_name.get(r["to_id"], r["to_id"])}' for r in relationships[:12])}

Generate a concise strategic analysis for a public affairs team advising proponents of this policy."""

    try:
        response = client.chat.completions.create(
            model=_active_model(MODEL),
            messages=[
                {"role": "system", "content": STRATEGIC_ANALYSIS_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            **_max_tokens_kwarg(2000),
            **_response_format_kwarg(),
        )
        data = _parse_json_content(response.choices[0].message.content)
        if data:
            return _normalize_strategic_analysis(data)
    except Exception as e:
        print(f"  Strategic analysis failed: {e}", file=sys.stderr)

    # Fallback: minimal structure so the frontend always has something to render
    return {
        "landscape": result.get("strategic_notes", "Strategic analysis not available."),
        "dynamics": "",
        "coalition_opportunities": [],
        "risks": [],
        "immediate_actions": [],
        "swing_actor_strategy": {"summary": "", "support": [], "metrics": [], "confidence": "unknown"},
    }


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

    client_kwargs: dict = {"api_key": api_key}
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)

    # Step 1: Discover actors from all sources
    print("Step 1a: Generating LDA search queries...", file=sys.stderr)
    lda_queries = generate_lda_queries(client, policy_issue)
    print(f"  Queries: {lda_queries}", file=sys.stderr)

    print("Step 1b: Discovering LDA actors...", file=sys.stderr)
    lda_actors, lda_rels = discover_lda_actors(lda_queries, year=year)

    print("Step 1c: Discovering legislative actors...", file=sys.stderr)
    leg_state = state if scope == "state" else "US"
    leg_actors, leg_rels = discover_legislative_actors(policy_issue, state=leg_state, year=year)

    print("Step 1d: Fetching news context...", file=sys.stderr)
    news_snippets = discover_news_snippets(policy_issue)
    print("Step 1e: Fetching supplemental Brave context...", file=sys.stderr)
    brave_snippets = discover_brave_context(policy_issue)

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
            for source_name, source_type in zip(actor.get("source_names", []), actor.get("source_types", [])):
                _merge_source_metadata(canonical, source_name, source_type)
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

    allowed_types = _allowed_actor_types(include_types)
    raw_actors = _filter_actors_by_allowed_types(raw_actors, allowed_types)

    # Cap at 50 actors: balance legislators and LDA actors so neither crowds the other out.
    # Keep top 20 legislators (by bill count) and top 30 LDA actors (by spend), then merge.
    legislators = sorted(
        [a for a in raw_actors if a.get("type") == "legislator"],
        key=lambda a: len(a.get("bill_numbers") or []),
        reverse=True,
    )
    others = sorted(
        [a for a in raw_actors if a.get("type") != "legislator"],
        key=lambda a: a.get("lda_amount") or 0,
        reverse=True,
    )
    raw_actors = legislators[:20] + others[:30]
    if len(raw_actors) > 50:
        raw_actors = raw_actors[:50]
        print("  Capped at 50 actors", file=sys.stderr)

    if not raw_actors:
        raise ValueError(
            f"No actors found for '{policy_issue}'. "
            "Try broader keywords (e.g., 'AI regulation' instead of a specific bill name)."
        )

    print(f"  Total actors for classification: {len(raw_actors)}", file=sys.stderr)

    print("Step 1f: Using Brave as supplemental context only...", file=sys.stderr)
    print(f"  Total actors after structured discovery: {len(raw_actors)}", file=sys.stderr)

    # Step 2: Classify actors
    print("Step 2: Classifying actors with gpt-4.1...", file=sys.stderr)
    classification = classify_actors(client, policy_issue, raw_actors, news_snippets)
    classified_actors = classification.get("actors", [])
    print(f"  Classified {len(classified_actors)} actors", file=sys.stderr)

    # Merge raw actor fields that the LLM doesn't return (bill_numbers, party, role, source)
    raw_by_id = {a["id"]: a for a in raw_actors}
    for actor in classified_actors:
        raw = raw_by_id.get(actor["id"], {})
        for field in ("bill_numbers", "party", "role", "source", "source_names", "source_types", "source_labels", "source_summary"):
            if field not in actor or actor[field] is None:
                if raw.get(field) is not None:
                    actor[field] = raw[field]
        # Also restore lda_amount from raw if LLM zeroed it out
        if not actor.get("lda_amount") and raw.get("lda_amount"):
            actor["lda_amount"] = raw["lda_amount"]
        if not actor.get("observed_evidence") and raw.get("observed_evidence"):
            actor["observed_evidence"] = raw["observed_evidence"]
        if not actor.get("source_types"):
            source_name = raw.get("source") or actor.get("source") or "inferred"
            source_type = SOURCE_LABELS.get(source_name, "Inferred" if source_name == "inferred" else "Structured source")
            _merge_source_metadata(actor, source_name, source_type)
        actor["source_labels"] = list(actor.get("source_types") or [])
        actor["source_summary"] = " + ".join(actor["source_labels"]) if actor.get("source_labels") else "—"

    # Step 2b: Seed known actors missing from LDA/LegiScan
    print("Step 2b: Seeding known actors...", file=sys.stderr)
    existing_names = {a["name"] for a in classified_actors}
    stance_counts = {
        "proponent": sum(1 for a in classified_actors if a.get("stance") == "proponent"),
        "opponent": sum(1 for a in classified_actors if a.get("stance") == "opponent"),
    }
    seeded_actors = seed_known_actors(client, policy_issue, existing_names, stance_counts)
    seeded_actors = _filter_actors_by_allowed_types(seeded_actors, allowed_types)
    classified_actors.extend(seeded_actors)
    classified_actors = _filter_actors_by_allowed_types(classified_actors, allowed_types)

    # Step 3: Extract and filter relationships
    # Use raw_actors (canonical IDs, pre-LLM) — not classified_actors — so that
    # LLM ID drift doesn't silently drop all edges.
    print("Step 3: Extracting relationships...", file=sys.stderr)
    relationships = extract_relationships(lda_rels, leg_rels, raw_actors)
    print(f"  {len(relationships)} relationships retained", file=sys.stderr)

    # Step 3b: LLM-inferred relationships (guarantees edges for SNA metrics)
    print("Step 3b: Inferring relationships with LLM...", file=sys.stderr)
    inferred_rels = infer_relationships(client, policy_issue, classified_actors)
    # Merge: add inferred edges not already covered by data-sourced edges
    existing_pairs = {(r["from_id"], r["to_id"]) for r in relationships}
    for r in inferred_rels:
        pair = (r["from_id"], r["to_id"])
        reverse = (r["to_id"], r["from_id"])
        if pair not in existing_pairs and reverse not in existing_pairs:
            relationships.append(r)
            existing_pairs.add(pair)
    print(f"  {len(relationships)} total relationships after inference", file=sys.stderr)

    # Step 3c: Anchor isolated actors — deterministic fallback, no extra LLM call.
    # Any actor with zero edges gets a coalition_with edge to the highest-degree
    # same-stance actor (or any actor if no same-stance match exists).
    ids_in_rels = set()
    for r in relationships:
        ids_in_rels.add(r["from_id"])
        ids_in_rels.add(r["to_id"])
    isolated_actors = [a for a in classified_actors if a["id"] not in ids_in_rels]

    if isolated_actors:
        # Build degree lookup
        degree_count: dict[str, int] = {}
        for r in relationships:
            degree_count[r["from_id"]] = degree_count.get(r["from_id"], 0) + 1
            degree_count[r["to_id"]] = degree_count.get(r["to_id"], 0) + 1

        _opposing = {"proponent": "opponent", "opponent": "proponent"}

        for actor in isolated_actors:
            aid = actor["id"]
            stance = actor.get("stance", "unknown")
            # Prefer same-stance candidates for coalition_with
            same_stance = [
                a for a in classified_actors
                if a["id"] in ids_in_rels and a["id"] != aid and a.get("stance") == stance
            ]
            if same_stance:
                anchor = max(same_stance, key=lambda a: degree_count.get(a["id"], 0))
                rel_type, rel_label = "coalition_with", f"coalition with {anchor['name'][:30]}"
            else:
                # Fall back to highest-degree actor with opposite stance → opposed edge
                opp_stance = _opposing.get(stance)
                cross = [
                    a for a in classified_actors
                    if a["id"] in ids_in_rels and a["id"] != aid
                    and (opp_stance is None or a.get("stance") == opp_stance)
                ]
                if not cross:
                    cross = [a for a in classified_actors if a["id"] in ids_in_rels and a["id"] != aid]
                if not cross:
                    continue
                anchor = max(cross, key=lambda a: degree_count.get(a["id"], 0))
                rel_type, rel_label = "opposed", f"opposed to {anchor['name'][:30]}"

            relationships.append({
                "from_id": aid,
                "to_id": anchor["id"],
                "type": rel_type,
                "label": rel_label,
                "source": "inferred",
            })
            ids_in_rels.add(aid)

        newly_connected = sum(1 for a in isolated_actors if a["id"] in ids_in_rels)
        print(f"  Step 3c: anchored {newly_connected} isolated actors", file=sys.stderr)

    # Sort actors: proponents → opponents → neutral → unknown, then high → low influence
    stance_order = {"proponent": 0, "opponent": 1, "neutral": 2, "unknown": 3}
    tier_order = {"high": 0, "medium": 1, "low": 2}
    classified_actors.sort(key=lambda a: (
        stance_order.get(a.get("stance", "unknown"), 3),
        tier_order.get(a.get("influence_tier", "low"), 2),
    ))

    # Step 4a: Network analytics (networkx, no LLM)
    print("Step 4a: Computing network analytics...", file=sys.stderr)
    exec_dir = Path(__file__).resolve().parent
    if str(exec_dir) not in sys.path:
        sys.path.insert(0, str(exec_dir))
    try:
        from analytics import compute_network_analytics
        network_analytics = compute_network_analytics(classified_actors, relationships)
        print(f"  Network density={network_analytics['network_density']}, "
              f"communities={network_analytics['communities']}, "
              f"brokers={len(network_analytics['brokers'])}", file=sys.stderr)
    except Exception as e:
        print(f"  Network analytics failed: {e}", file=sys.stderr)
        network_analytics = {}

    # Step 4b: LLM strategic analysis
    print("Step 4b: Generating strategic analysis...", file=sys.stderr)
    _partial_result = {
        "policy_issue": policy_issue,
        "actors": classified_actors,
        "relationships": relationships,
        "strategic_notes": classification.get("strategic_notes", ""),
    }
    strategic_analysis = generate_strategic_analysis(client, policy_issue, _partial_result, network_analytics)
    print("  Strategic analysis complete", file=sys.stderr)

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
        "network_analytics": network_analytics,
        "strategic_analysis": strategic_analysis,
        "methodology_note": (
            "Actors may come from structured sources, web discovery, or model inference. "
            "Some labels and relationships are inferred. Network indicators are calculated within the generated map. "
            "Scores are directional and require analyst review before strategic use."
        ),
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

    if result.get("methodology_note"):
        sections.append("## Methodology And Limitations")
        sections.append(result["methodology_note"])
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
        confidence = a.get("confidence_label")
        if confidence:
            parts.append(f"[{confidence}]")
        if a.get("source_summary"):
            parts.append(f"[Sources: {a['source_summary']}]")
        if a.get("observed_evidence"):
            parts.append(f"— Observed: {a['observed_evidence']}")
        if a.get("inferred_rationale"):
            parts.append(f"— Inferred: {a['inferred_rationale']}")
        elif a.get("evidence"):
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

    strategic = result.get("strategic_analysis", {})
    if strategic:
        if strategic.get("landscape"):
            sections.append("## Strategic Landscape")
            sections.append(strategic["landscape"])
            sections.append("")
        if strategic.get("dynamics"):
            sections.append("## Strategic Dynamics")
            sections.append(strategic["dynamics"])
            sections.append("")
        if strategic.get("immediate_actions"):
            sections.append("## Immediate Actions")
            for action in strategic["immediate_actions"]:
                parts = [p for p in [action.get("actor"), action.get("action"), action.get("why")] if p]
                sections.append(f"- {' — '.join(parts)}")
                if action.get("support"):
                    sections.append(f"  Support: {'; '.join(action['support'])}")
                if action.get("metrics"):
                    sections.append(f"  Metrics: {'; '.join(action['metrics'])}")
                if action.get("confidence"):
                    sections.append(f"  Confidence: {action['confidence']}")
            sections.append("")

    sections.append("---")
    sections.append("*Stance classifications are LLM-inferred from public data — verify before strategic use*")

    return "\n".join(sections)
