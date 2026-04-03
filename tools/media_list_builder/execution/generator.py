"""
Media List Builder Generator
===============================
Research-first pipeline — discovers real journalists from actual articles.

Step 1 — Query expansion: LLM generates varied search queries from the issue
Step 2 — News search: multi-query GNews to find recent articles (~40)
Step 3 — Byline extraction: fetch each article, extract real author names
Step 4 — Enrichment: LLM adds pitch angles / role / email — only for real journalists
"""

import os
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

try:
    from gnews import GNews
    HAS_GNEWS = True
except ImportError:
    HAS_GNEWS = False

try:
    from googlenewsdecoder import new_decoderv1
    HAS_DECODER = True
except ImportError:
    HAS_DECODER = False

try:
    from newspaper import Article
    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

import requests


MODEL = "gpt-4o"

MEDIA_TYPE_LABELS = {
    "mainstream": "Mainstream",
    "print": "Print",
    "broadcast": "Broadcast (TV/Radio)",
    "digital": "Digital / Online",
    "trade": "Trade / Policy",
    "podcast": "Podcast",
}

FETCH_TIMEOUT = 8       # seconds per article fetch
MAX_WORKERS = 6         # parallel fetches
MAX_ARTICLES = 40       # cap on articles to fetch bylines from


# ---------------------------------------------------------------------------
# Step 1: Story analysis + query expansion
# ---------------------------------------------------------------------------

def analyze_story(issue: str, client: OpenAI) -> dict:
    """
    Understand what kind of story this is before generating search queries.
    Returns a brief analysis: beat, themes, adjacent topics.
    """
    prompt = (
        f'A public affairs professional wants to pitch this story:\n"{issue}"\n\n'
        "Analyze this story and return a JSON object with:\n"
        "- beat: the journalism beat this belongs to (e.g. 'history & preservation', "
        "'environmental policy', 'federal budget')\n"
        "- themes: 2-3 core themes journalists on this beat regularly cover\n"
        "- adjacent_topics: 4-5 related topics or story types that journalists "
        "covering this beat would also write about — NOT this specific story, "
        "but the broader landscape of coverage around it\n\n"
        '{"beat": "...", "themes": ["...", "..."], "adjacent_topics": ["...", "...", "...", "...", "..."]}'
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=300,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def expand_queries(issue: str, location: str, client: OpenAI) -> tuple[list[str], dict]:
    """
    Two-stage: first understand the story, then generate beat-aware search queries.
    Returns (queries, story_analysis).
    """
    # Stage 1: understand the story
    analysis = analyze_story(issue, client)
    beat = analysis.get("beat", "")
    adjacent = analysis.get("adjacent_topics", [])

    print(f"  Beat: {beat}", file=sys.stderr)
    print(f"  Adjacent topics: {adjacent}", file=sys.stderr)

    # Stage 2: turn adjacent topics into search queries
    loc_note = f" in {location}" if location and location.upper() not in ("US", "USA", "NATIONAL") else ""
    topics_text = "\n".join(f"- {t}" for t in adjacent)
    prompt = (
        f'Story beat: "{beat}"\n'
        f"Adjacent topics journalists on this beat cover:\n{topics_text}\n\n"
        f"Convert each adjacent topic into a short Google News search query (3-6 words){loc_note}. "
        "Each query should find real news articles about that topic. "
        "Do NOT include the original story — only the adjacent beat coverage.\n\n"
        "Return a JSON object: "
        '{"queries": ["...", "...", "...", "...", "..."]}'
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=200,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content)
    queries = data.get("queries", [issue])
    return queries[:5], analysis


# ---------------------------------------------------------------------------
# Step 2: Multi-query news search
# ---------------------------------------------------------------------------

def search_articles(queries: list[str], location: str,
                    max_per_query: int = 12) -> list[dict]:
    """Run GNews for each query variant, deduplicate by URL."""
    if not HAS_GNEWS:
        print("  gnews not installed", file=sys.stderr)
        return []

    country = "US"
    if location and location.upper() not in ("US", "USA", "NATIONAL"):
        country = "US"  # still search US edition; location is appended to query

    seen_urls = set()
    seen_titles = set()
    all_articles = []

    gn = GNews(language="en", country=country, period="365d", max_results=max_per_query)

    for q in queries:
        query = q
        if location and location.upper() not in ("US", "USA", "NATIONAL"):
            query = f"{q} {location}"
        try:
            articles = gn.get_news(query) or []
            for a in articles:
                url = a.get("url", "")
                title = a.get("title", "").lower()
                if url in seen_urls or title in seen_titles:
                    continue
                seen_urls.add(url)
                if title:
                    seen_titles.add(title)
                all_articles.append({
                    "title": a.get("title", ""),
                    "source": a.get("publisher", {}).get("title", ""),
                    "url": url,
                    "date": a.get("published date", ""),
                })
        except Exception as e:
            print(f"  GNews error for query '{q}': {e}", file=sys.stderr)

    return all_articles


# ---------------------------------------------------------------------------
# Step 3a: Decode Google News redirect URLs → real article URLs
# ---------------------------------------------------------------------------

def decode_urls(articles: list[dict]) -> list[dict]:
    """
    Resolve Google News redirect URLs to real article URLs.
    Decodes sequentially with a small delay to avoid rate limits.
    """
    if not HAS_DECODER:
        return articles

    decoded = []
    for article in articles:
        url = article.get("url", "")
        if "news.google.com" in url:
            try:
                result = new_decoderv1(url)
                if result.get("status") and result.get("decoded_url"):
                    article = {**article, "url": result["decoded_url"]}
                else:
                    # Can't decode — skip
                    continue
                time.sleep(0.2)  # be polite to Google's servers
            except Exception:
                continue
        decoded.append(article)

    print(f"  Decoded {len(decoded)}/{len(articles)} URLs", file=sys.stderr)
    return decoded


# ---------------------------------------------------------------------------
# Step 3b: Byline extraction
# ---------------------------------------------------------------------------

def _extract_authors_newspaper(url: str) -> list[str]:
    """Try newspaper3k to extract author names from article URL."""
    try:
        art = Article(url, request_timeout=FETCH_TIMEOUT)
        art.download()
        art.parse()
        return [a.strip() for a in art.authors if a.strip()]
    except Exception:
        return []


def _extract_authors_trafilatura(url: str) -> list[str]:
    """Try trafilatura to extract author metadata."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MediaResearch/1.0)"}
        resp = requests.get(url, timeout=FETCH_TIMEOUT, headers=headers)
        if resp.status_code != 200:
            return []
        meta = trafilatura.extract_metadata(resp.text, default_url=url)
        if meta and meta.author:
            # trafilatura may return semicolon-separated names
            return [n.strip() for n in meta.author.split(";") if n.strip()]
    except Exception:
        pass
    return []


def _fetch_byline(article: dict):
    """
    Try to extract at least one author name from the article URL.
    Returns enriched article dict with 'authors' list, or None if no author found.
    """
    url = article.get("url", "")
    if not url:
        return None

    authors = []

    # Try newspaper3k first (usually best for author extraction)
    if HAS_NEWSPAPER:
        authors = _extract_authors_newspaper(url)

    # Fallback: trafilatura
    if not authors and HAS_TRAFILATURA:
        authors = _extract_authors_trafilatura(url)

    if not authors:
        return None

    return {**article, "authors": authors}


def extract_bylines(articles: list[dict]) -> list[dict]:
    """
    Parallel byline extraction. Returns articles where at least one author was found.
    """
    candidates = articles[:MAX_ARTICLES]
    results = []

    print(f"  Fetching bylines from {len(candidates)} articles...", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_fetch_byline, a): a for a in candidates}
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception:
                pass

    print(f"  Found bylines in {len(results)} articles", file=sys.stderr)
    return results


# ---------------------------------------------------------------------------
# Group articles by journalist
# ---------------------------------------------------------------------------

_JUNK_WORDS = {
    "staff", "editor", "editors", "contributor", "contributors",
    "reporter", "reporters", "writer", "published", "updated",
    "community", "anonymous", "guest", "admin", "news", "desk",
    "margin", "padding", "bottom", "top", "left", "right",  # CSS artifacts
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
}

_JUNK_FRAGMENTS = (
    "all posts", "published date", "view all", "read more",
    "follow us", "sign up", "newsletter", "trust", "foundation",
    "institute", "association", "coalition", "committee", "council",
    "reuters", "associated press", "wire services",
)


def _is_person_name(name: str) -> bool:
    """Heuristic: a journalist name should look like 'First Last' — 2-4 words, no junk."""
    if len(name) < 5 or len(name) > 60:
        return False
    lower = name.lower()
    if any(frag in lower for frag in _JUNK_FRAGMENTS):
        return False
    words = name.split()
    # Must be 2–4 words
    if len(words) < 2 or len(words) > 4:
        return False
    # No word should be a known junk token
    if any(w.lower().rstrip(".,;") in _JUNK_WORDS for w in words):
        return False
    # Each word should start with a capital letter
    if not all(w[0].isupper() for w in words if w):
        return False
    # No hyphens spanning the full name (CSS class artifacts like "Margin-Bottom")
    if any("-" in w and len(w) > 8 for w in words):
        return False
    return True


def group_by_journalist(articles_with_bylines: list[dict]) -> list[dict]:
    """
    Group articles by author name. Each journalist entry has their outlet
    and a list of articles they wrote, as evidence of their beat.
    """
    journalist_map: dict[str, dict] = {}

    for article in articles_with_bylines:
        for author in article.get("authors", []):
            name = author.strip().title()
            if not _is_person_name(name):
                continue

            if name not in journalist_map:
                journalist_map[name] = {
                    "name": name,
                    "outlet": article.get("source", ""),
                    "articles": [],
                }

            journalist_map[name]["articles"].append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "date": article.get("date", ""),
                "source": article.get("source", ""),
            })

            # Use the outlet from the most-covered source for this journalist
            # (outlet they appear most with wins)
            outlet_counts: dict[str, int] = {}
            for a in journalist_map[name]["articles"]:
                s = a.get("source", "")
                if s:
                    outlet_counts[s] = outlet_counts.get(s, 0) + 1
            if outlet_counts:
                journalist_map[name]["outlet"] = max(outlet_counts, key=outlet_counts.__getitem__)

    # Sort by number of articles (most prolific first)
    journalists = sorted(journalist_map.values(),
                         key=lambda j: len(j["articles"]), reverse=True)
    return journalists


# ---------------------------------------------------------------------------
# Step 4: LLM enrichment
# ---------------------------------------------------------------------------

ENRICH_SYSTEM = """You are a senior public affairs media strategist.

You will receive a list of real journalists discovered via article research.
Each journalist comes with actual articles they have written on the topic.

Your job is to enrich each contact with:
- A pitch angle specific to their documented coverage
- Their role/beat based on what they actually cover
- A media type classification
- A guessed email address using the outlet's known email pattern
- Notes on their relevance

RULES:
- Do NOT invent or add any journalists not in the input list
- Base pitch angles on the actual articles provided
- If you recognise the journalist, include any additional verified context in notes
- For email: use the outlet's known email pattern (e.g. first.last@nytimes.com).
  If unknown, use [RESEARCH NEEDED]
- media_type must be one of: "mainstream", "print", "broadcast", "digital", "trade", "podcast"
- outlet_website: full https:// URL for the outlet's homepage
- previous_story_title: title of the most relevant article from their list
- previous_story_url: URL of that article (use the provided URL — do not fabricate)
- GEOGRAPHIC SCOPE: if the scope is "national", only include journalists from national-audience
  outlets (e.g. NYT, WaPo, Politico, NPR, national magazines). Exclude local TV stations,
  city newspapers, and regional blogs. If the scope is a specific state or city, include
  both local/regional and national journalists who covered that area.

Return JSON:
{
  "contacts": [
    {
      "first_name": "...",
      "last_name": "...",
      "outlet": "...",
      "outlet_website": "https://...",
      "role": "...",
      "media_type": "mainstream",
      "location": "...",
      "pitch_angle": "...",
      "previous_story_title": "...",
      "previous_story_url": "https://...",
      "email": "...",
      "notes": "..."
    }
  ],
  "pitch_timing": "..."
}"""


def enrich_contacts(journalists: list[dict], issue: str, location: str,
                    media_types: list[str], is_national: bool, client: OpenAI) -> dict:
    """LLM enrichment — adds pitch angles and contact details for real discovered journalists."""

    # Build journalist summaries for the prompt
    journalist_lines = []
    for j in journalists:
        articles_text = "; ".join(
            f'"{a["title"]}" ({a["date"]}) [{a["url"]}]'
            for a in j["articles"][:3]
        )
        journalist_lines.append(
            f'- {j["name"]} @ {j["outlet"]}: {articles_text}'
        )

    media_type_str = ", ".join(MEDIA_TYPE_LABELS.get(mt, mt) for mt in media_types)

    scope_instruction = (
        "IMPORTANT: The user wants NATIONAL coverage only. "
        "Exclude journalists from local TV stations, city newspapers, and regional blogs. "
        "Only include journalists from outlets with a national audience."
        if is_national else
        f"The user wants coverage scoped to: {location}. "
        "Include both local/regional outlets and national journalists who cover that area."
    )

    prompt = (
        f"Issue being pitched: {issue}\n"
        f"Geographic scope: {location}\n"
        f"Media types requested: {media_type_str}\n"
        f"{scope_instruction}\n\n"
        f"Journalists discovered through article research:\n"
        + "\n".join(journalist_lines)
        + f"\n\nEnrich all {len(journalists)} journalists above. "
        f"Assign each a media_type from the requested types where appropriate. "
        f"Write pitch angles based on their actual documented coverage."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": ENRICH_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=6000,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_media_list(issue: str, location: str = "US",
                        media_types: list[str] = None,
                        num_contacts: int = 20) -> dict:
    """
    Run the full research-first media list pipeline.

    Returns:
        {
            "issue": str,
            "location": str,
            "media_types": list,
            "contacts": [{ ... }],
            "pitch_timing": str,
            "news_research": [{ ... }],
        }
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required.")

    client = OpenAI(api_key=api_key)
    media_types = media_types or list(MEDIA_TYPE_LABELS.keys())
    num_contacts = min(num_contacts, 40)

    is_national = location.upper() in ("US", "USA", "NATIONAL")

    # Step 1: Analyze story + expand queries
    print("Step 1: Analyzing story and expanding search queries...", file=sys.stderr)
    queries, story_analysis = expand_queries(issue, location, client)
    print(f"  Queries: {queries}", file=sys.stderr)

    # Step 2: Multi-query news search
    print("Step 2: Searching for articles...", file=sys.stderr)
    articles = search_articles(queries, location, max_per_query=12)
    print(f"  Found {len(articles)} unique articles", file=sys.stderr)

    # Step 3: Decode URLs, then extract bylines
    print("Step 3: Decoding article URLs...", file=sys.stderr)
    articles = decode_urls(articles)

    print("Step 3b: Extracting journalist bylines from articles...", file=sys.stderr)
    articles_with_bylines = extract_bylines(articles)

    journalists = group_by_journalist(articles_with_bylines)
    print(f"  Identified {len(journalists)} unique journalists", file=sys.stderr)

    if not journalists:
        # Graceful fallback: return empty list with a message rather than hallucinating
        return {
            "issue": issue,
            "location": location,
            "media_types": media_types,
            "contacts": [],
            "pitch_timing": (
                "No journalist bylines could be extracted from recent articles on this topic. "
                "Try broadening the issue description, or manually search trade publications "
                "for journalists covering this beat."
            ),
            "news_research": articles[:10],
        }

    # Cap to num_contacts (most-covered journalists first)
    journalists = journalists[:num_contacts]

    # Step 4: LLM enrichment
    print(f"Step 4: Enriching {len(journalists)} contacts with pitch angles...", file=sys.stderr)
    enriched = enrich_contacts(journalists, issue, location, media_types, is_national, client)

    # Normalize media_type values
    label_to_key = {}
    for key, label in MEDIA_TYPE_LABELS.items():
        label_to_key[key.lower()] = key
        label_to_key[label.lower()] = key

    contacts = enriched.get("contacts", [])
    for c in contacts:
        raw_type = c.get("media_type", "").lower().strip()
        c["media_type"] = label_to_key.get(raw_type, raw_type)

    # Filter by requested media types
    if media_types and set(media_types) != set(MEDIA_TYPE_LABELS.keys()):
        contacts = [c for c in contacts if c.get("media_type", "") in media_types]

    return {
        "issue": issue,
        "location": location,
        "media_types": media_types,
        "contacts": contacts,
        "pitch_timing": enriched.get("pitch_timing", ""),
        "news_research": articles[:10],
    }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def render_markdown(result: dict) -> str:
    """Render the media list as a markdown summary."""
    sections = []

    sections.append(f"# Media Pitch List")
    sections.append(f"**Issue:** {result['issue']}")
    sections.append(f"**Location:** {result['location']}")
    sections.append(f"**Total Contacts:** {len(result['contacts'])}")
    sections.append("")

    # Summary by media type
    type_counts = {}
    for c in result["contacts"]:
        mt = c.get("media_type", "other")
        type_counts[mt] = type_counts.get(mt, 0) + 1

    if type_counts:
        sections.append("## Coverage by Media Type")
        for mt, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            label = MEDIA_TYPE_LABELS.get(mt, mt)
            sections.append(f"- **{label}:** {count} contacts")
        sections.append("")

    # Pitch timing
    if result.get("pitch_timing"):
        sections.append("## Pitch Timing")
        sections.append(result["pitch_timing"])
        sections.append("")

    # Contact table
    sections.append("## Contacts")
    sections.append("")
    sections.append("| Name | Outlet | Role | Media Type | Pitch Angle |")
    sections.append("|------|--------|------|------------|-------------|")
    for c in result["contacts"]:
        name = f"{c.get('first_name', '')} {c.get('last_name', '')}"
        outlet = c.get("outlet", "")
        role = c.get("role", "")
        mt = MEDIA_TYPE_LABELS.get(c.get("media_type", ""), c.get("media_type", ""))
        angle = c.get("pitch_angle", "")[:80]
        sections.append(f"| {name} | {outlet} | {role} | {mt} | {angle} |")

    sections.append("")
    sections.append("---")
    sections.append("*CONFIDENTIAL — FOR INTERNAL USE ONLY*")

    return "\n".join(sections)
