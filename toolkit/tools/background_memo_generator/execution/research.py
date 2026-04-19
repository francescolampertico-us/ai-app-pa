"""
Background Memo — Web Research Step
=====================================
Finds recent articles about the subject via GNews, decodes redirect URLs,
and extracts article text to ground the LLM in real, current information.

This is what makes the memo specific rather than generic: the LLM cannot
know niche details about a Czech think tank or an Italian industrial group
from training data alone, but it can synthesize them from real articles.
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


MAX_ARTICLES = 15         # candidates to fetch per query
MAX_EXTRACTED = 10        # articles to include in the final package
CHARS_PER_ARTICLE = 2500  # text truncation per article
MAX_PER_DOMAIN = 2        # max articles from any single publisher domain


def _domain_of(url: str) -> str:
    """Extract the registered domain from a URL (for source deduplication)."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        parts = host.lstrip("www.").split(".")
        return ".".join(parts[-2:]) if len(parts) >= 2 else host
    except Exception:
        return url


def _decode_url(url: str) -> str:
    """Decode a Google News redirect URL to the real article URL."""
    if not url.startswith("https://news.google.com"):
        return url
    if not HAS_DECODER:
        return url
    try:
        decoded = new_decoderv1(url, interval=2)
        if decoded and decoded.get("status"):
            return decoded["decoded_url"]
    except Exception:
        pass
    return url


def _extract_text(url: str) -> str:
    """Fetch a URL and extract clean article text using trafilatura."""
    if not HAS_TRAFILATURA or not HAS_REQUESTS:
        return ""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        text = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        return text or ""
    except Exception:
        return ""


def _fetch_article(item: dict) -> dict:
    """Decode URL and extract text for a single GNews result."""
    raw_url = item.get("url", "")
    real_url = _decode_url(raw_url)
    if not real_url or real_url == raw_url and real_url.startswith("https://news.google.com"):
        return {}
    text = _extract_text(real_url)
    if not text or len(text) < 200:
        return {}
    return {
        "title": item.get("title", ""),
        "source": item.get("publisher", {}).get("title", ""),
        "url": real_url,
        "text": text[:CHARS_PER_ARTICLE],
    }


def research_subject(subject: str, context: str = "") -> str:
    """
    Search for articles about the subject and return a research package as a
    markdown string for injection into the LLM prompt.

    Strategy:
    - Runs two queries (precise + broad) to widen coverage and reduce
      single-cluster bias.
    - Deduplicates candidates by URL across both queries.
    - Fetches all candidates in parallel, then selects the most substantive
      articles by preferring longer text and capping per-domain representation.

    Returns empty string if GNews or extraction is unavailable.
    """
    if not HAS_GNEWS:
        print("GNews not available — skipping web research.", file=sys.stderr)
        return ""

    # Query A: precise — subject + first line of context (if any)
    query_precise = f'"{subject}"'
    if context:
        first_line = context.strip().splitlines()[0][:60].strip()
        if first_line:
            query_precise = f'{query_precise} {first_line}'

    # Query B: broad — subject only (different result cluster from A)
    query_broad = f'"{subject}"'

    queries = [query_precise]
    if query_broad != query_precise:
        queries.append(query_broad)

    gn = GNews(language="en", max_results=MAX_ARTICLES, period="2y")

    # Collect candidates from all queries, deduplicating by URL
    candidates = []
    seen_urls: set = set()
    for query in queries:
        print(f"Researching: {query}", file=sys.stderr)
        try:
            results = gn.get_news(query)
        except Exception as e:
            print(f"GNews query failed ({query!r}): {e}", file=sys.stderr)
            results = []
        for item in (results or []):
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                candidates.append(item)

    # Fallback: unquoted subject search
    if not candidates:
        try:
            candidates = gn.get_news(subject) or []
        except Exception:
            return ""

    if not candidates:
        return ""

    # Fetch article texts in parallel across all candidates
    extracted = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_fetch_article, a): a for a in candidates}
        for future in as_completed(futures):
            result = future.result()
            if result:
                extracted.append(result)

    if not extracted:
        return ""

    # Sort by text length descending — longer articles are generally more substantive
    extracted.sort(key=lambda a: len(a["text"]), reverse=True)

    # Domain cap: at most MAX_PER_DOMAIN articles per publisher domain so one
    # news outlet or news cluster cannot dominate the research pool.
    domain_counts: dict = {}
    diverse = []
    for art in extracted:
        domain = _domain_of(art["url"])
        if domain_counts.get(domain, 0) < MAX_PER_DOMAIN:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            diverse.append(art)
        if len(diverse) >= MAX_EXTRACTED:
            break

    # If the domain cap was too strict, fill remaining slots from leftovers
    if len(diverse) < MAX_EXTRACTED:
        in_diverse = {a["url"] for a in diverse}
        for art in extracted:
            if art["url"] not in in_diverse:
                diverse.append(art)
            if len(diverse) >= MAX_EXTRACTED:
                break

    n_domains = len({_domain_of(a["url"]) for a in diverse})
    print(
        f"Research complete: {len(diverse)} articles from {n_domains} sources.",
        file=sys.stderr,
    )

    # Format as research package
    lines = [
        f"RESEARCH MATERIAL — {len(diverse)} articles about '{subject}' "
        f"from {n_domains} sources:",
        "",
        "These are raw sources. Synthesize across ALL of them — do not recap "
        "any single article or event. "
        "Prioritize: mission/purpose, structure, key figures, scale, policy relevance, "
        "funding, U.S./international angle, and controversy. "
        "Exclude: logistics, operational disruptions, scheduling details, and event minutiae. "
        "If multiple articles cover the same event, treat it as one data point.",
        "",
    ]
    for i, art in enumerate(diverse, 1):
        lines.append(f"--- Article {i}: {art['title']} ({art['source']}) ---")
        lines.append(art["text"])
        lines.append(f"[Source: {art['url']}]")
        lines.append("")

    return "\n".join(lines)
