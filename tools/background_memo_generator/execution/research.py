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


MAX_ARTICLES = 8          # search results to attempt
MAX_EXTRACTED = 5         # articles to actually include
CHARS_PER_ARTICLE = 3000  # text truncation per article


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
    Search for recent articles about the subject and return a research
    package as a markdown string for injection into the LLM prompt.

    Returns empty string if GNews or extraction is unavailable.
    """
    if not HAS_GNEWS:
        print("GNews not available — skipping web research.", file=sys.stderr)
        return ""

    # Build search query — quoted for precision, context adds scope
    query = f'"{subject}"'
    if context:
        # Extract first meaningful phrase from context as an extra keyword
        first_line = context.strip().splitlines()[0][:60].strip()
        if first_line:
            query = f'{query} {first_line}'

    print(f"Researching: {query}", file=sys.stderr)

    gn = GNews(language="en", max_results=MAX_ARTICLES, period="2y")
    try:
        articles = gn.get_news(query)
    except Exception as e:
        print(f"GNews search failed: {e}", file=sys.stderr)
        return ""

    if not articles:
        # Fallback: try without quotes
        try:
            articles = gn.get_news(subject)
        except Exception:
            return ""

    if not articles:
        return ""

    # Fetch article texts in parallel
    extracted = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_fetch_article, a): a for a in articles[:MAX_ARTICLES]}
        for future in as_completed(futures):
            result = future.result()
            if result:
                extracted.append(result)
            if len(extracted) >= MAX_EXTRACTED:
                break

    if not extracted:
        return ""

    # Format as research package
    lines = [
        f"RESEARCH MATERIAL — {len(extracted)} articles found about '{subject}':",
        "",
        "Use these articles to write specific, accurate content. "
        "Cite figures, names, and facts that appear in the articles. "
        "Do not repeat generic information that does not come from this research.",
        "",
    ]
    for i, art in enumerate(extracted, 1):
        lines.append(f"--- Article {i}: {art['title']} ({art['source']}) ---")
        lines.append(art["text"])
        lines.append(f"[Source: {art['url']}]")
        lines.append("")

    print(f"Research complete: {len(extracted)} articles extracted.", file=sys.stderr)
    return "\n".join(lines)
