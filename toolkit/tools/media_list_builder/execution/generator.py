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
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, urljoin, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple, List, Dict
import xml.etree.ElementTree as ET
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

def _parse_json_content(content: Optional[str]) -> dict:
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

MEDIA_TYPE_LABELS = {
    "mainstream": "Mainstream",
    "print": "Print",
    "broadcast": "Broadcast (TV/Radio)",
    "digital": "Digital / Online",
    "trade": "Trade / Policy",
    "podcast": "Podcast",
}

OUTLET_MEDIA_HINTS = {
    "trade": (
        "law360", "fedscoop", "nextgov", "fcw", "ipwatchdog", "meritalk", "cyberscoop",
        "the information", "protocol", "venturebeat", "cio dive", "healthcare dive",
        "hr dive", "retail dive", "utility dive", "construction dive", "adexchanger",
        "digiday", "ai business", "techeu", "tech policy press", "inside higher ed",
        "government technology", "statescoop", "defense scoop", "cybersecurity dive",
        "fierce healthcare", "fierce pharma", "medcity news", "mlex"
    ),
    "broadcast": ("cnn", "msnbc", "fox news", "abc news", "cbs news", "nbc news", "npr", "pbs"),
    "print": ("new york times", "washington post", "wall street journal", "usa today", "la times", "time"),
    "digital": ("axios", "politico", "semafor", "the verge", "techcrunch", "wired", "404 media", "slate"),
}

MAINSTREAM_OUTLET_HINTS = (
    "new york times", "washington post", "wall street journal", "usa today", "time",
    "reuters", "associated press", "ap news", "bloomberg",
)

MAINSTREAM_OUTLET_DOMAINS = (
    "nytimes.com", "washingtonpost.com", "wsj.com", "usatoday.com", "time.com",
    "reuters.com", "apnews.com", "bloomberg.com",
)

DESK_TERM_MAP = {
    "health": ("health", "healthcare", "medical", "medicine", "hospital", "hospitals", "public health", "medicaid", "medicare"),
    "business": ("business", "economy", "economic", "markets", "corporate", "industry", "deal", "finance"),
    "finance": ("finance", "banking", "banks", "investment", "securities", "wall street", "private equity", "asset management"),
    "politics": ("politics", "political", "campaign", "campaigns", "election", "elections", "congress", "white house"),
    "policy": ("policy", "regulation", "regulatory", "rule", "rules", "oversight", "agency", "federal"),
    "technology": ("technology", "tech", "ai", "artificial intelligence", "software", "platform", "cyber", "data"),
    "climate": ("climate", "carbon", "emissions", "environment", "environmental", "clean energy", "greenhouse gas"),
    "energy": ("energy", "oil", "gas", "utilities", "power", "grid", "renewable", "renewables"),
    "transportation": ("transportation", "transit", "rail", "aviation", "airlines", "shipping", "ports", "highway"),
    "education": ("education", "schools", "school", "students", "college", "universities", "campus"),
    "legal": ("legal", "law", "court", "courts", "litigation", "judge", "judges", "lawsuit"),
    "labor": ("labor", "union", "unions", "workers", "workforce", "employment", "workplace"),
    "housing": ("housing", "rent", "rents", "mortgage", "mortgages", "real estate", "zoning", "homelessness"),
    "agriculture": ("agriculture", "farm", "farms", "farming", "food", "crops", "agricultural"),
    "defense": ("defense", "military", "pentagon", "army", "navy", "air force", "space force", "weapons"),
    "foreign affairs": ("foreign affairs", "international", "diplomacy", "sanctions", "geopolitics", "state department"),
}

NATIONAL_OUTLET_HINTS = (
    "new york times", "washington post", "wall street journal", "usa today", "time magazine",
    "politico", "axios", "the hill", "the atlantic", "the nation",
    "npr", "pbs", "pbs newshour", "cnn", "abc news", "cbs news", "nbc news", "fox news",
    "reuters", "associated press", "ap news",
    "the verge", "wired", "techcrunch", "semafor", "fedscoop", "nextgov", "fcw", "law360",
    "bloomberg", "business insider", "huffpost", "vox", "vice", "slate", "salon",
    "the guardian", "newsweek", "u.s. news", "roll call", "the intercept", "propublica",
)

NATIONAL_OUTLET_DOMAINS = (
    "nytimes.com", "washingtonpost.com", "wsj.com", "usatoday.com", "politico.com",
    "axios.com", "npr.org", "pbs.org", "cnn.com", "abcnews.go.com", "cbsnews.com",
    "nbcnews.com", "foxnews.com", "reuters.com", "apnews.com", "bloomberg.com",
    "thehill.com", "theatlantic.com", "theguardian.com", "newsweek.com", "time.com",
    "vox.com", "slate.com", "salon.com", "huffpost.com", "propublica.org",
    "rollcall.com", "theintercept.com", "semafor.com", "wired.com", "techcrunch.com",
    "theverge.com", "fedscoop.com", "nextgov.com", "law360.com", "businessinsider.com",
)

NATIONAL_SEARCH_DOMAINS = (
    "washingtonpost.com",
    "wired.com",
    "time.com",
    "politico.com",
    "axios.com",
    "theverge.com",
    "reuters.com",
    "apnews.com",
    "bloomberg.com",
    "semafor.com",
    "fedscoop.com",
    "nextgov.com",
)

TRADE_SEARCH_DOMAINS = (
    "venturebeat.com",
    "theinformation.com",
    "cyberscoop.com",
    "statescoop.com",
    "nextgov.com",
    "fedscoop.com",
    "law360.com",
    "digiday.com",
    "adexchanger.com",
    "healthcaredive.com",
    "cio.com",
    "techpolicy.press",
    "aibusiness.com",
    "mlex.com",
)

PODCAST_SEARCH_DOMAINS = (
    "spotify.com",
    "podcasts.apple.com",
    "youtube.com",
    "podbean.com",
    "simplecast.com",
    "buzzsprout.com",
    "captivate.fm",
    "omny.fm",
    "transistor.fm",
    "megaphone.fm",
    "libsyn.com",
    "art19.com",
    "shows.acast.com",
)

PODCAST_PROVIDER_HINTS = {
    "spotify.com": "Spotify",
    "podcasts.apple.com": "Apple Podcasts",
    "youtube.com": "YouTube",
    "podbean.com": "Podbean",
    "simplecast.com": "Simplecast",
    "buzzsprout.com": "Buzzsprout",
    "captivate.fm": "Captivate",
    "omny.fm": "Omny",
    "transistor.fm": "Transistor",
    "megaphone.fm": "Megaphone",
    "libsyn.com": "Libsyn",
    "art19.com": "ART19",
    "acast.com": "Acast",
}

PODCAST_UI_NOISE_TERMS = (
    "free listening on podbean app",
    "listen on spotify",
    "listen on apple podcasts",
    "watch on youtube",
    "podbean app",
    "apple podcasts",
    "spotify podcast",
)

PODCAST_HOST_BLOCKLIST = (
    "podbean development",
    "podbean",
    "spotify",
    "apple podcasts",
    "youtube",
    "official account",
    "development team",
)

FETCH_TIMEOUT = 8       # seconds per article fetch
MAX_WORKERS = 6         # parallel fetches
MAX_ARTICLES = 80       # cap on articles to fetch bylines from
MAX_PER_OUTLET = 3
MAX_STORY_ROWS_PER_OUTLET = 4
MIN_RELEVANCE_SCORE = 10
HIGH_CONFIDENCE_STORY_SCORE = 16
LAYER1_USABLE_MIN_CONTACTS = 6
LAYER1_STRONG_STOP_CONTACTS = 10
LAYER1_STRONG_STOP_OUTLETS = 4
LAYER2_WAIT_TIMEOUT = 8
LAYER3_WAIT_TIMEOUT = 8

# Domains that are definitively NOT media outlets — law firms, think tanks, IGOs, NGOs, academia.
# Articles from these sources will be dropped before byline extraction.
_NON_MEDIA_DOMAINS = {
    # Law firms
    "skadden.com", "gibsondunn.com", "linklaters.com", "sullcrom.com",
    "davispolk.com", "weil.com", "kirkland.com", "latham.com",
    "whitecase.com", "sidley.com", "milbank.com", "steptoe.com",
    "pillsburylaw.com", "jonesday.com", "freshfields.com",
    "wilmerhale.com", "ogletree.com",
    # Think tanks / policy institutes
    "brookings.edu", "csis.org", "cfr.org", "wilsoncenter.org",
    "heritage.org", "cato.org", "aei.org", "rand.org",
    "stimson.org", "usip.org", "atlanticcouncil.org",
    "chathamhouse.org", "iiss.org", "sipri.org",
    # NGOs / advocacy
    "hrw.org", "amnesty.org", "worldvision.org", "oxfam.org",
    "rescue.org", "msf.org", "icrc.org", "unhcr.org",
    "mercycorps.org", "savethechildren.org",
    # Government / IGOs
    "un.org", "state.gov", "whitehouse.gov", "congress.gov", ".gov",
    "europa.eu", "nato.int",
    # Academia
    ".edu",
}

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "into", "is", "it", "of", "on", "or", "that", "the", "their", "this",
    "to", "was", "were", "what", "when", "where", "which", "with",
    "policy", "policies", "issue", "issues", "story", "stories", "news", "update",
}

_SHORT_ANCHOR_TOKENS = {"ai", "uk", "eu", "us", "vr", "xr"}
_AUTHOR_URL_HINTS = ("/author/", "/authors/", "/profile/", "/profiles/", "/staff/", "/by/", "/writer/")
_NEWSROOM_URL_HINTS = ("/newsroom", "/press", "/staff", "/contributors", "/team")
_STORY_URL_HINTS = ("/202", "/article", "/news/", "/story", "/stories/")


def _is_non_media_url(url: str) -> bool:
    """Return True if the URL belongs to a known non-media domain."""
    lower = url.lower()
    for domain in _NON_MEDIA_DOMAINS:
        if domain in lower:
            return True
    return False


def _domain_of(url: str) -> str:
    try:
        return (urlparse(url).netloc or "").lower().removeprefix("www.")
    except Exception:
        return ""


def _platform_from_url(url: str) -> str:
    domain = _domain_of(url)
    for hint, label in PODCAST_PROVIDER_HINTS.items():
        if hint in domain:
            return label
    return ""


def _is_podcast_domain(url: str) -> bool:
    domain = _domain_of(url)
    return any(hint in domain for hint in PODCAST_PROVIDER_HINTS)


def _classify_candidate_type(url: str) -> str:
    lower = (url or "").lower()
    if any(hint in lower for hint in _AUTHOR_URL_HINTS):
        return "author_page"
    if any(hint in lower for hint in _NEWSROOM_URL_HINTS):
        return "newsroom"
    if any(hint in lower for hint in _STORY_URL_HINTS):
        return "story"
    try:
        path_parts = [part for part in urlparse(url).path.split("/") if part]
    except Exception:
        path_parts = []
    section_markers = {"section", "tag", "tags", "topics", "topic", "category", "categories"}
    if path_parts and any(part in section_markers for part in path_parts):
        return "search_result"
    if len(path_parts) >= 3:
        tail = path_parts[-1]
        if re.search(r"\d{4}", "/".join(path_parts)) or "-" in tail:
            return "story"
    return "search_result"


_MAX_ARTICLE_AGE_YEARS = 5


def _is_article_too_old(date_str: str) -> bool:
    """Return True if the article date is older than 5 years. Unknown dates are kept."""
    if not date_str:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=_MAX_ARTICLE_AGE_YEARS * 365)
    # Try RFC 2822 (GNews / RSS format: "Mon, 14 Apr 2025 12:00:00 GMT")
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt < cutoff
    except Exception:
        pass
    # Try ISO-like formats
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str[:len(fmt)], fmt).replace(tzinfo=timezone.utc)
            return dt < cutoff
        except ValueError:
            continue
    return False  # unparseable → keep


class SearchProvider:
    name = "none"

    def available(self) -> bool:
        return False

    def search(self, query: str, location: str, max_results: int = 8, mode: str = "story") -> List[dict]:
        return []


class NoopSearchProvider(SearchProvider):
    name = "noop"


class BraveSearchProvider(SearchProvider):
    name = "brave"

    def __init__(self):
        self.api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()

    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, location: str, max_results: int = 8, mode: str = "story") -> List[dict]:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key,
        }
        params = {
            "q": query,
            "count": max_results,
            "search_lang": "en",
            "country": "us",
        }
        try:
            resp = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params,
                timeout=12,
            )
            resp.raise_for_status()
            payload = resp.json() or {}
            results = []
            for item in payload.get("web", {}).get("results", []) or []:
                url = item.get("url", "")
                candidate_type = _classify_candidate_type(url)
                if mode == "story" and candidate_type not in {"story", "search_result"}:
                    continue
                if mode == "author" and candidate_type not in {"author_page", "newsroom", "search_result"}:
                    continue
                results.append({
                    "title": item.get("title", ""),
                    "source": item.get("profile", {}).get("name", "") or _domain_of(url),
                    "url": url,
                    "date": item.get("page_age", "") or "",
                    "description": item.get("description", ""),
                    "provider": self.name,
                    "candidate_type": candidate_type,
                    "query": query,
                    "query_kind": "provider",
                })
            return results
        except Exception as exc:
            print(f"  Brave search error for query '{query}': {exc}", file=sys.stderr)
            return []


def _search_provider() -> SearchProvider:
    provider = BraveSearchProvider()
    if provider.available():
        return provider
    return NoopSearchProvider()


def filter_media_articles(articles: List[dict]) -> List[dict]:
    """Drop articles from think tanks, law firms, NGOs, and government sources."""
    kept = [a for a in articles if not _is_non_media_url(a.get("url", ""))]
    dropped = len(articles) - len(kept)
    if dropped:
        print(f"  Filtered {dropped} non-media articles (think tanks, law firms, NGOs)", file=sys.stderr)
    return kept


def normalize_candidate(candidate: dict, issue_profile: dict) -> Optional[dict]:
    url = candidate.get("url", "")
    if not url or _is_non_media_url(url):
        return None
    normalized = {
        "title": candidate.get("title", ""),
        "source": candidate.get("source", "") or _domain_of(url),
        "url": url,
        "date": candidate.get("date", ""),
        "description": candidate.get("description", ""),
        "query": candidate.get("query", ""),
        "query_kind": candidate.get("query_kind", "provider"),
        "provider": candidate.get("provider", "unknown"),
        "candidate_type": candidate.get("candidate_type", _classify_candidate_type(url)),
    }
    score, reason = _score_article(normalized, issue_profile)
    if normalized["candidate_type"] == "story":
        score += 4
    elif normalized["candidate_type"] == "author_page":
        score -= 2
    elif normalized["candidate_type"] == "newsroom":
        score -= 4
    normalized["relevance_score"] = max(score, 0)
    normalized["relevance_reason"] = reason
    return normalized


def validate_candidate(candidate: dict, issue_profile: dict, location: str, is_national: bool, media_types: List[str]) -> bool:
    if not candidate:
        return False
    if candidate.get("relevance_score", 0) < MIN_RELEVANCE_SCORE:
        return False
    if _is_non_media_url(candidate.get("url", "")):
        return False
    source = candidate.get("source", "")
    if is_national and source and not _is_national_outlet(source):
        return False
    if not _matches_location_scope(candidate, location, is_national):
        return False
    guessed_type = _guess_media_type(source)
    if not _media_type_matches(source, guessed_type, media_types):
        # Stories can still seed discovery even if the outlet type is hard to classify.
        if candidate.get("candidate_type") != "story":
            return False
    return True


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (text or "").lower())).strip()


def _tokenize(text: str) -> List[str]:
    return [
        token for token in _normalize_text(text).split()
        if ((len(token) > 2) or token in _SHORT_ANCHOR_TOKENS) and token not in _STOPWORDS
    ]


def _desk_terms(coverage_desk: str) -> List[str]:
    normalized = _normalize_text(coverage_desk)
    if not normalized:
        return []
    terms = list(DESK_TERM_MAP.get(normalized, ()))
    if not terms:
        terms = [normalized]
    tokens = []
    for term in terms:
        normalized_term = _normalize_text(term)
        if normalized_term:
            tokens.append(normalized_term)
    return list(dict.fromkeys(tokens))


def _issue_profile(
    issue: str,
    broad_topic: str = "",
    coverage_desk: str = "",
    topic_mode: str = "specific",
) -> dict:
    primary_topic = (broad_topic or issue or coverage_desk).strip()
    tokens = _tokenize(primary_topic)
    if not tokens:
        tokens = _tokenize(primary_topic.replace("/", " "))
    required_width = 2 if topic_mode == "broad" else 3
    required_terms = tokens[: min(required_width, len(tokens))]
    secondary_terms = tokens[min(required_width, len(tokens)) : 8]
    desk_terms = _desk_terms(coverage_desk)
    return {
        "normalized_issue": _normalize_text(primary_topic),
        "topic_mode": topic_mode,
        "tokens": tokens,
        "required_terms": required_terms,
        "secondary_terms": secondary_terms,
        "desk_terms": desk_terms,
        "broad_topic": (broad_topic or "").strip(),
        "coverage_desk": (coverage_desk or "").strip(),
    }


def _make_query_plan(
    issue: str,
    location: str,
    analysis: dict,
    broad_topic: str = "",
    coverage_desk: str = "",
    topic_mode: str = "specific",
) -> List[dict]:
    subject = (broad_topic or issue or coverage_desk).strip()
    profile = _issue_profile(issue, broad_topic, coverage_desk, topic_mode)
    required_terms = profile["required_terms"]
    query_plan = []
    seen = set()

    def add(query: str, kind: str):
        q = query.strip()
        key = q.lower()
        if not q or key in seen:
            return
        seen.add(key)
        query_plan.append({"query": q, "kind": kind})

    is_local = location and location.upper() not in ("US", "USA", "NATIONAL")

    if subject:
        add(subject, "exact")
        add(f'"{subject}"', "exact")

    # Core anchors
    if required_terms:
        add(" ".join(required_terms), "exact")
        if is_local:
            add(f'{" ".join(required_terms)} {location}', "exact")

    # Beat-angle query: helps find reporters who cover the beat, not just the exact phrase
    beat = (analysis or {}).get("beat", "")
    if beat and required_terms and beat.lower() not in " ".join(required_terms).lower():
        add(f'{" ".join(required_terms)} {beat}', "supporting")

    coverage_desk = (coverage_desk or "").strip()
    if coverage_desk:
        if subject and coverage_desk.lower() not in subject.lower():
            add(f"{subject} {coverage_desk}", "supporting")
        add(f'"{coverage_desk}" reporter OR editor OR desk', "supporting")
        if topic_mode == "broad":
            add(f"{coverage_desk} news", "supporting")

    # Adjacent topic queries — anchored to issue terms to avoid drift
    anchor = " ".join(required_terms or profile["tokens"][:2])
    for topic in (analysis or {}).get("adjacent_topics", [])[:3]:
        if not topic:
            continue
        add(f'{anchor} {topic}', "supporting")

    # Wire-service / investigation angle: broadens to breaking and investigative coverage
    if required_terms:
        add(f'{" ".join(required_terms[:2])} investigation OR exclusive OR report', "supporting")

    # Regional variant: explicitly search for local reporters if scoped location
    if is_local and required_terms:
        add(f'{" ".join(required_terms[:2])} {location} reporter OR coverage', "supporting")

    if topic_mode == "broad":
        broad_anchor = " ".join(required_terms or profile["tokens"][:2])
        if broad_anchor:
            add(f'{broad_anchor} coverage', "supporting")
            if coverage_desk and coverage_desk.lower() not in broad_anchor.lower():
                add(f'{broad_anchor} {coverage_desk} coverage', "supporting")

    return query_plan[:12]


def _score_article(article: dict, issue_profile: dict) -> Tuple[int, str]:
    title_norm = _normalize_text(article.get("title", ""))
    if not title_norm:
        return 0, "missing title"

    context_norm = _normalize_text(
        " ".join(
            part for part in [
                article.get("title", ""),
                article.get("description", ""),
                article.get("source", ""),
                article.get("url", ""),
            ] if part
        )
    )

    required_terms = issue_profile["required_terms"]
    secondary_terms = issue_profile["secondary_terms"]
    desk_terms = issue_profile.get("desk_terms", [])
    topic_mode = issue_profile.get("topic_mode", "specific")

    score = 0
    reasons = []

    if issue_profile["normalized_issue"] and issue_profile["normalized_issue"] in title_norm:
        score += 30
        reasons.append("exact issue phrase")
    elif issue_profile["normalized_issue"] and issue_profile["normalized_issue"] in context_norm:
        score += 18
        reasons.append("exact issue context")

    matched_required = [term for term in required_terms if term in context_norm]
    title_required = [term for term in required_terms if term in title_norm]
    missing_required = [term for term in required_terms if term not in context_norm]
    if matched_required:
        score += len(title_required) * 12
        score += max(len(matched_required) - len(title_required), 0) * 6
        reasons.append(f"anchor terms: {', '.join(matched_required)}")
    if not missing_required and required_terms:
        score += 12 if topic_mode == "broad" else 18
        reasons.append("all anchor terms present")
    elif missing_required:
        penalty = 4 if topic_mode == "broad" else 8
        score -= len(missing_required) * penalty
        reasons.append(f"missing anchors: {', '.join(missing_required)}")

    matched_secondary = [term for term in secondary_terms if term in context_norm]
    if matched_secondary:
        score += len(matched_secondary) * 4

    matched_desk = [term for term in desk_terms if term in context_norm]
    if matched_desk:
        score += min(12, len(matched_desk) * 4)
        reasons.append(f"desk context: {', '.join(matched_desk[:3])}")

    query_kind = article.get("query_kind", "exact")
    if query_kind == "exact":
        score += 6
    elif query_kind == "supporting":
        score -= 4

    if score < 0:
        score = 0

    return score, "; ".join(reasons)


def _dedupe_articles_by_story(articles: List[dict]) -> List[dict]:
    deduped = []
    seen_story_keys = set()
    for article in sorted(articles, key=lambda a: a.get("relevance_score", 0), reverse=True):
        title_key = _normalize_text(article.get("title", ""))
        if not title_key:
            continue
        story_key = title_key[:120]
        if story_key in seen_story_keys:
            continue
        seen_story_keys.add(story_key)
        deduped.append(article)
    return deduped


def _guess_media_type(outlet: str, fallback: str = "digital") -> str:
    lower = (outlet or "").lower()
    if _is_mainstream_outlet(outlet):
        return "mainstream"
    for media_type, hints in OUTLET_MEDIA_HINTS.items():
        if any(hint in lower for hint in hints):
            return media_type
    return fallback


def _is_national_outlet(outlet: str) -> bool:
    lower = (outlet or "").lower()
    if any(hint in lower for hint in NATIONAL_OUTLET_HINTS):
        return True
    # Also match by known national domain names
    return any(domain in lower for domain in NATIONAL_OUTLET_DOMAINS)


def _is_mainstream_outlet(outlet: str) -> bool:
    lower = (outlet or "").lower()
    if any(hint in lower for hint in MAINSTREAM_OUTLET_HINTS):
        return True
    return any(domain in lower for domain in MAINSTREAM_OUTLET_DOMAINS)


def _media_type_matches(outlet: str, guessed_type: str, requested_types: Optional[List[str]]) -> bool:
    if not requested_types:
        return True
    if guessed_type in requested_types:
        return True
    if "mainstream" in requested_types and _is_mainstream_outlet(outlet):
        return True
    return False


def _candidate_domain(candidate: dict) -> str:
    return _domain_of(candidate.get("url", "")) or _domain_of(candidate.get("outlet_website", "")) or ""


def _is_story_url(url: str) -> bool:
    return _classify_candidate_type(url) == "story"


def _location_tokens(location: str) -> List[str]:
    normalized = _normalize_text(location)
    if not normalized:
        return []
    return [token for token in normalized.split() if len(token) > 2 and token not in _STOPWORDS]


def _matches_location_scope(article: dict, location: str, is_national: bool) -> bool:
    if is_national:
        return True
    tokens = _location_tokens(location)
    if not tokens:
        return True
    haystack = _normalize_text(
        " ".join(
            part for part in [
                article.get("title", ""),
                article.get("description", ""),
                article.get("source", ""),
                article.get("url", ""),
            ] if part
        )
    )
    return all(token in haystack for token in tokens[:2])


def _matches_contact_location(contact: dict, location: str, is_national: bool) -> bool:
    if is_national:
        return True
    tokens = _location_tokens(location)
    if not tokens:
        return True
    haystack = _normalize_text(
        " ".join(
            part for part in [
                contact.get("location", ""),
                contact.get("outlet", ""),
                contact.get("previous_story_title", ""),
                contact.get("previous_story_url", ""),
            ] if part
        )
    )
    return all(token in haystack for token in tokens[:2])


def _top_story_outlet_domains(
    articles: List[dict],
    media_types: List[str],
    is_national: bool,
    location: str = "",
    limit: int = 6,
) -> List[str]:
    domains: List[str] = []
    seen = set()
    for article in sorted(articles, key=lambda article: article.get("relevance_score", 0), reverse=True):
        if not _article_matches_output_scope(article, media_types, is_national, location):
            continue
        domain = _domain_of(article.get("url", ""))
        if not domain:
            continue
        if domain in seen:
            continue
        seen.add(domain)
        domains.append(domain)
        if len(domains) >= limit:
            break
    return domains


# ---------------------------------------------------------------------------
# Step 1: Story analysis + query expansion
# ---------------------------------------------------------------------------

def analyze_story(issue: str, client: OpenAI, topic_mode: str = "specific", coverage_desk: str = "") -> dict:
    """
    Understand what kind of story this is before generating search queries.
    Returns a brief analysis: beat, themes, adjacent topics.
    """
    scope_hint = ""
    if topic_mode == "broad" and coverage_desk:
        scope_hint = (
            f"\nTreat this as a broad desk/beat search. Prioritize how a {coverage_desk} desk would frame the topic, "
            "and expand toward reporter-relevant subtopics rather than a single exact phrase.\n"
        )
    elif topic_mode == "broad":
        scope_hint = (
            "\nTreat this as a broad beat search and expand toward adjacent newsroom subtopics, not just exact phrase matches.\n"
        )
    prompt = (
        f'A public affairs professional wants to pitch this story to NEWS JOURNALISTS:\n"{issue}"\n'
        f"{scope_hint}\n"
        "Analyze what journalism beat this belongs to and return a JSON object with:\n"
        "- beat: the journalism beat this belongs to (e.g. 'foreign affairs', "
        "'conflict reporting', 'humanitarian aid', 'international diplomacy')\n"
        "- themes: 2-3 core themes that REPORTERS at news outlets regularly cover on this beat\n"
        "- adjacent_topics: 4-5 related NEWS STORY TYPES that journalists covering this beat "
        "would actively report on — focus on story angles covered by newspapers, wire services, "
        "TV/radio, magazines, and digital news outlets. "
        "Do NOT suggest think tank reports, law firm bulletins, or NGO advocacy materials.\n"
        "Preserve the literal core topic and named entity in your understanding of the story.\n\n"
        '{"beat": "...", "themes": ["...", "..."], "adjacent_topics": ["...", "...", "...", "...", "..."]}'
    )
    response = client.chat.completions.create(
        model=_active_model(MODEL),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        **_max_tokens_kwarg(300),
        **_response_format_kwarg(),
    )
    analysis = _parse_json_content(response.choices[0].message.content)
    if coverage_desk and not analysis.get("beat"):
        analysis["beat"] = coverage_desk
    return analysis


def expand_queries(
    issue: str,
    location: str,
    client: OpenAI,
    broad_topic: str = "",
    coverage_desk: str = "",
    topic_mode: str = "specific",
) -> Tuple[List[dict], dict]:
    """
    Two-stage: first understand the story, then generate beat-aware search queries.
    Returns (queries, story_analysis).
    """
    # Stage 1: understand the story
    search_subject = (broad_topic or issue or coverage_desk).strip()
    analysis = analyze_story(search_subject, client, topic_mode=topic_mode, coverage_desk=coverage_desk)
    beat = analysis.get("beat", "")
    adjacent = analysis.get("adjacent_topics", [])

    print(f"  Beat: {beat}", file=sys.stderr)
    print(f"  Adjacent topics: {adjacent}", file=sys.stderr)

    return _make_query_plan(
        issue,
        location,
        analysis,
        broad_topic=broad_topic,
        coverage_desk=coverage_desk,
        topic_mode=topic_mode,
    ), analysis


# ---------------------------------------------------------------------------
# Step 2: Multi-query news search
# ---------------------------------------------------------------------------

def search_articles(query_plan: List[dict], issue: str, location: str,
                    max_per_query: int = 12) -> List[dict]:
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

    issue_profile = _issue_profile(issue)

    for item in query_plan:
        q = item.get("query", "")
        query_kind = item.get("kind", "exact")
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
                date_str = a.get("published date", "")
                if _is_article_too_old(date_str):
                    continue
                article = {
                    "title": a.get("title", ""),
                    "source": a.get("publisher", {}).get("title", ""),
                    "url": url,
                    "date": date_str,
                    "query": q,
                    "query_kind": query_kind,
                }
                score, reason = _score_article(article, issue_profile)
                article["relevance_score"] = score
                article["relevance_reason"] = reason
                all_articles.append(article)
        except Exception as e:
            print(f"  GNews error for query '{q}': {e}", file=sys.stderr)

    ranked = _dedupe_articles_by_story(all_articles)
    strong = [a for a in ranked if a.get("relevance_score", 0) >= MIN_RELEVANCE_SCORE]
    fallback = strong if strong else ranked[: max_per_query * 2]
    return sorted(fallback, key=lambda a: a.get("relevance_score", 0), reverse=True)


def retrieve_layer1_news(query_plan: List[dict], issue: str, location: str) -> List[dict]:
    print("  Layer 1: Google News retrieval", file=sys.stderr)
    return search_articles(query_plan, issue, location, max_per_query=15)


def retrieve_layer2_search(
    query_plan: List[dict],
    issue: str,
    location: str,
    media_types: List[str],
    is_national: bool,
    broad_topic: str = "",
    coverage_desk: str = "",
    topic_mode: str = "specific",
) -> Tuple[List[dict], SearchProvider]:
    provider = _search_provider()
    if not provider.available():
        print("  Layer 2: no search API configured; skipping broad-web search", file=sys.stderr)
        return [], provider

    print(f"  Layer 2: broad-web retrieval via {provider.name}", file=sys.stderr)
    issue_profile = _issue_profile(issue, broad_topic, coverage_desk, topic_mode)
    raw_results = []
    seen = set()
    planned = []
    for item in query_plan[:4]:
        q = item.get("query", "")
        planned.append((q, "story"))
    anchor = " ".join(issue_profile["required_terms"][:2] or issue_profile["tokens"][:2])
    if anchor:
        planned.append((f'"{anchor}" journalist OR reporter OR editor', "author"))
        if is_national:
            preferred_domains = TRADE_SEARCH_DOMAINS if media_types and media_types == ["trade"] else NATIONAL_SEARCH_DOMAINS
            for domain in preferred_domains[:8]:
                planned.append((f'"{anchor}" site:{domain}', "story"))
        if media_types and media_types == ["trade"]:
            planned.append((f'"{anchor}" trade publication OR industry publication OR policy publication', "story"))

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(provider.search, q, location, 8, mode) for q, mode in planned if q]
        for future in as_completed(futures):
            for result in future.result() or []:
                url = result.get("url", "")
                if not url or url in seen:
                    continue
                seen.add(url)
                normalized = normalize_candidate(result, issue_profile)
                if not normalized:
                    continue
                if _is_article_too_old(normalized.get("date", "")):
                    continue
                if not validate_candidate(normalized, issue_profile, location, is_national, media_types):
                    continue
                raw_results.append(normalized)

    ranked = _dedupe_articles_by_story(raw_results)
    return ranked, provider


def expand_from_validated_seeds(
    journalists: List[dict],
    articles: List[dict],
    issue: str,
    location: str,
    media_types: List[str],
    is_national: bool,
    provider: SearchProvider,
    limit: int = 20,
    broad_topic: str = "",
    coverage_desk: str = "",
    topic_mode: str = "specific",
) -> List[dict]:
    if not provider.available() or (not journalists and not articles):
        return []
    issue_profile = _issue_profile(issue, broad_topic, coverage_desk, topic_mode)
    search_subject = (broad_topic or issue or coverage_desk).strip()
    queries = []
    for journalist in journalists[:4]:
        outlet = journalist.get("outlet", "")
        name = journalist.get("name", "")
        if name and outlet:
            queries.append((f'"{name}" "{outlet}" "{search_subject}"', "story"))
            queries.append((f'"{outlet}" "{search_subject}" reporter OR editor', "author"))
    for domain in _top_story_outlet_domains(articles, media_types, is_national, location, limit=6):
        queries.append((f'"{search_subject}" site:{domain}', "story"))
        queries.append((f'site:{domain} "{search_subject}" reporter OR editor OR author', "author"))
    results = []
    seen = set()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(provider.search, q, location, 6, mode) for q, mode in queries]
        for future in as_completed(futures):
            for result in future.result() or []:
                url = result.get("url", "")
                if not url or url in seen:
                    continue
                seen.add(url)
                normalized = normalize_candidate(result, issue_profile)
                if not validate_candidate(normalized, issue_profile, location, is_national, media_types):
                    continue
                results.append(normalized)
                if len(results) >= limit:
                    break
    return _dedupe_articles_by_story(results)


def _classify_podcast_page(url: str, html: str = "") -> str:
    parsed = urlparse(url)
    lower = url.lower()
    if "spotify.com" in parsed.netloc:
        if "/episode/" in parsed.path:
            return "episode"
        if "/show/" in parsed.path:
            return "show"
    if "podcasts.apple.com" in parsed.netloc:
        if parse_qs(parsed.query).get("i"):
            return "episode"
        if "/podcast/" in parsed.path:
            return "show"
    if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
        if "/watch" in parsed.path or "watch?v=" in lower:
            return "episode"
        if "/playlist" in parsed.path or "/channel/" in parsed.path or "/@" in parsed.path:
            return "show"
    if any(token in lower for token in ("/episode", "/episodes/", "/ep/", "/podcast/episode", "episode-")):
        return "episode"
    if any(token in lower for token in ("/show", "/podcast", "/series", "/podcasts/")):
        return "show"
    if html:
        meta_type = _extract_meta_content(html, ["og:type"])
        if meta_type and "music.radio_station" in meta_type.lower():
            return "show"
    return "show" if _is_podcast_domain(url) else "other"


def _topic_score(title: str, description: str, source: str, url: str, issue_profile: dict, query_kind: str = "exact") -> Tuple[int, str]:
    article_like = {
        "title": title,
        "description": description,
        "source": source,
        "url": url,
        "query_kind": query_kind,
    }
    return _score_article(article_like, issue_profile)


def _podcast_host_parts(host_name: str) -> Tuple[str, str]:
    parts = [part for part in (host_name or "").split() if part]
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


def _normalize_podcast_text(value: str) -> str:
    text = re.sub(r"\s+", " ", (value or "")).strip()
    if not text:
        return ""
    text = re.sub(r"\s*[|:]\s*Free Listening on Podbean App.*$", "", text, flags=re.IGNORECASE)
    parts = [part.strip() for part in text.split("|")]
    cleaned_parts = []
    for part in parts:
        lower = part.lower()
        if not part:
            continue
        if any(noise in lower for noise in PODCAST_UI_NOISE_TERMS):
            continue
        cleaned_parts.append(part)
    text = " | ".join(cleaned_parts) if cleaned_parts else text
    return re.sub(r"\s+", " ", text).strip(" -|:")


def _looks_like_person_name(value: str) -> bool:
    name = re.sub(r"\s+", " ", (value or "")).strip()
    if not name:
        return False
    lower = name.lower()
    if lower in PODCAST_HOST_BLOCKLIST:
        return False
    if name.startswith("@"):
        return False
    if "http" in lower or ".com" in lower:
        return False
    if any(noise in lower for noise in PODCAST_UI_NOISE_TERMS):
        return False
    if re.search(r"\b(app|podcast|show|channel|episode|development|team|network|radio)\b", lower) and not re.search(r"\bhost\b", lower):
        return False
    candidate = name
    if " : " in candidate:
        candidate = candidate.split(" : ", 1)[0].strip()
    if " - " in candidate and len(candidate.split()) > 4:
        candidate = candidate.split(" - ", 1)[0].strip()
    candidate = re.sub(r"\s*\([^)]*\)\s*", " ", candidate).strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z .'\-]{1,79}", candidate):
        return False
    words = [word for word in candidate.split() if word]
    if len(words) < 2 or len(words) > 5:
        return False
    if sum(1 for word in words if word[0].isupper()) < 2:
        return False
    return True


def _normalize_host_name(value: str) -> str:
    name = re.sub(r"\s+", " ", (value or "")).strip()
    if not name:
        return ""
    if " : " in name:
        left = name.split(" : ", 1)[0].strip()
        if _looks_like_person_name(left):
            name = left
    if " - " in name:
        left = name.split(" - ", 1)[0].strip()
        if _looks_like_person_name(left):
            name = left
    name = re.sub(r"\s*\([^)]*\)\s*", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" -|:")
    return name if _looks_like_person_name(name) else ""


def _normalize_email_candidate(value: str) -> str:
    email = (value or "").strip().strip(".,;:()[]{}<>")
    if not email:
        return ""
    lower = email.lower()
    if not re.fullmatch(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", email, flags=re.IGNORECASE):
        return ""
    if re.search(r"\.(png|jpg|jpeg|gif|svg|webp|avif)$", lower):
        return ""
    local_part, _, domain = lower.partition("@")
    if not local_part or not domain:
        return ""
    if domain.startswith("2x.") or domain.startswith("3x."):
        return ""
    if any(token in lower for token in ("image@", "img@", "icon@", "asset@", "logo@")):
        return ""
    return email


def _escape_markdown_cell(value: str) -> str:
    text = str(value or "")
    text = text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def _resolve_podcast_candidate(candidate: dict, issue_profile: dict, location: str, is_national: bool) -> Optional[dict]:
    url = candidate.get("url", "")
    if not url:
        return None
    html, resolved_url = _fetch_html_head(url)
    resolved_url = resolved_url or url
    page_type = _classify_podcast_page(resolved_url, html)
    if page_type == "other":
        return None

    title = _normalize_podcast_text(
        _extract_meta_content(html, ["og:title", "twitter:title"])
        or _extract_title_tag(html)
        or candidate.get("title", "")
    )
    description = _normalize_podcast_text(
        _extract_meta_content(html, ["description", "og:description", "twitter:description"])
        or candidate.get("description", "")
    )
    host_candidates = [
        _extract_meta_content(html, ["author"]),
        _extract_meta_content(html, ["og:author"]),
        _extract_meta_content(html, ["twitter:creator"]),
    ]
    rss_url = _discover_rss_url(html, resolved_url)
    rss_data = _parse_rss_feed(rss_url) if rss_url else {}
    show_name = _normalize_podcast_text(rss_data.get("show_title") or title)
    show_description = _normalize_podcast_text(rss_data.get("show_description") or description)
    host_candidates.insert(0, rss_data.get("show_author", ""))
    host_name = ""
    for candidate_name in host_candidates:
        normalized_name = _normalize_host_name(candidate_name)
        if normalized_name:
            host_name = normalized_name
            break
    show_url = rss_data.get("show_link") or resolved_url
    platform = _platform_from_url(resolved_url) or "Podcast"

    email = _normalize_email_candidate(_extract_email_from_html(html))
    if not email:
        contact_url = _extract_same_domain_link(html, resolved_url, ("contact", "about", "team", "host"))
        if contact_url:
            contact_html = _fetch_text_resource(contact_url)
            email = _normalize_email_candidate(_extract_email_from_html(contact_html))

    matched_title = title
    matched_url = resolved_url
    matched_summary = description
    matched_evidence_type = ""
    best_score = 0
    best_reason = ""

    page_score, page_reason = _topic_score(title, description, platform, resolved_url, issue_profile, query_kind="exact")
    if page_type == "episode" and page_score >= MIN_RELEVANCE_SCORE:
        matched_evidence_type = "episode"
        best_score = page_score + 6
        best_reason = page_reason

    if rss_data.get("episodes"):
        for episode in rss_data["episodes"]:
            score, reason = _topic_score(
                episode.get("title", ""),
                episode.get("description", ""),
                show_name,
                episode.get("url", ""),
                issue_profile,
                query_kind="supporting",
            )
            if score > best_score and episode.get("url"):
                matched_evidence_type = "episode"
                matched_title = _normalize_podcast_text(episode.get("title", "")) or matched_title
                matched_url = episode.get("url", "") or matched_url
                matched_summary = _normalize_podcast_text(episode.get("description", "")) or matched_summary
                best_score = score + 4
                best_reason = reason

    if not matched_evidence_type:
        show_score, show_reason = _topic_score(show_name, show_description, platform, show_url, issue_profile, query_kind="supporting")
        if show_score < MIN_RELEVANCE_SCORE:
            return None
        matched_evidence_type = "show_description"
        matched_title = show_name
        matched_url = show_url
        matched_summary = show_description
        best_score = show_score
        best_reason = show_reason

    if not _matches_location_scope(
        {
            "title": matched_title,
            "description": matched_summary,
            "source": show_name,
            "url": matched_url,
        },
        location,
        is_national,
    ):
        return None

    first_name, last_name = _podcast_host_parts(host_name)
    host_contact_status = (
        "identified_with_contact" if host_name and email else
        "identified_no_contact" if host_name else
        "show_only_verify_host"
    )
    notes = (
        "Host identified from show metadata; verify current booking/contact route before outreach."
        if host_name and not email else
        "Host and direct contact were identified from show or network metadata."
        if host_name and email else
        "Relevant show match found, but host identity still needs verification."
    )

    return {
        "first_name": first_name,
        "last_name": last_name,
        "outlet": show_name,
        "outlet_website": show_url,
        "role": "Podcast Host" if host_name else "Podcast / host to verify",
        "media_type": "podcast",
        "location": location if not is_national else "National",
        "pitch_angle": (
            f"{show_name} has a relevant {matched_evidence_type.replace('_', ' ')} on this issue."
            if matched_title else f"{show_name} appears aligned with this topic."
        ),
        "why_now": matched_title or show_description[:140],
        "pitch_offer": "",
        "previous_story_title": matched_title,
        "previous_story_url": matched_url,
        "email": email,
        "notes": notes,
        "contact_status": host_contact_status,
        "topic_fit_score": best_score,
        "supporting_evidence": best_reason,
        "relevance_confidence": "high" if best_score >= 32 else "medium",
        "identity_confidence": "medium" if host_name else "low",
        "show_name": show_name,
        "host_name": host_name,
        "host_contact_status": host_contact_status,
        "platform": platform,
        "show_url": show_url,
        "matched_evidence_type": matched_evidence_type,
        "matched_title": matched_title,
        "matched_url": matched_url,
        "matched_summary": matched_summary,
    }


def retrieve_podcast_candidates(
    query_plan: List[dict],
    issue: str,
    location: str,
    is_national: bool,
    broad_topic: str = "",
    coverage_desk: str = "",
    topic_mode: str = "specific",
) -> List[dict]:
    provider = _search_provider()
    if not provider.available():
        print("  Podcast discovery skipped: no search API configured", file=sys.stderr)
        return []

    issue_profile = _issue_profile(issue, broad_topic, coverage_desk, topic_mode)
    queries: List[str] = []
    seen = set()

    def add(query: str):
        q = query.strip()
        if not q or q.lower() in seen:
            return
        seen.add(q.lower())
        queries.append(q)

    anchor = " ".join(issue_profile["required_terms"][:2] or issue_profile["tokens"][:2])
    for item in query_plan[:4]:
        query = item.get("query", "")
        for domain in PODCAST_SEARCH_DOMAINS[:8]:
            add(f'{query} podcast site:{domain}')
    if anchor:
        add(f'{anchor} podcast host OR podcast show')
        add(f'{anchor} podcast rss')

    raw_results = []
    seen_urls = set()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(provider.search, query, location, 6, "story") for query in queries[:20]]
        for future in as_completed(futures):
            for result in future.result() or []:
                url = result.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                if not (_is_podcast_domain(url) or "podcast" in (result.get("title", "") + " " + result.get("description", "")).lower()):
                    continue
                raw_results.append(result)

    candidates: List[dict] = []
    seen_match_urls = set()
    for result in raw_results:
        resolved = _resolve_podcast_candidate(result, issue_profile, location, is_national)
        if not resolved:
            continue
        matched_url = (resolved.get("matched_url") or resolved.get("show_url") or "").strip()
        if not matched_url or matched_url in seen_match_urls:
            continue
        seen_match_urls.add(matched_url)
        candidates.append(resolved)

    candidates.sort(
        key=lambda item: (
            0 if item.get("host_contact_status") == "identified_with_contact" else
            1 if item.get("host_contact_status") == "identified_no_contact" else 2,
            0 if item.get("matched_evidence_type") == "episode" else 1,
            -(item.get("topic_fit_score", 0) or 0),
        )
    )
    return candidates


# ---------------------------------------------------------------------------
# Step 3a: Decode Google News redirect URLs → real article URLs
# ---------------------------------------------------------------------------

def decode_urls(articles: List[dict]) -> List[dict]:
    """
    Resolve Google News redirect URLs to real article URLs.
    Decodes sequentially with a small delay to avoid rate limits.
    Articles that cannot be decoded are kept with their original URL —
    requests will still follow the Google redirect during byline extraction.
    """
    if not HAS_DECODER:
        return articles

    decoded_count = 0
    decoded = []
    for article in articles:
        url = article.get("url", "")
        if "news.google.com" in url:
            try:
                result = new_decoderv1(url)
                if result.get("status") and result.get("decoded_url"):
                    article = {**article, "url": result["decoded_url"]}
                    decoded_count += 1
                time.sleep(0.2)  # be polite to Google's servers
            except Exception:
                pass  # Keep original URL — requests will follow the redirect
        decoded.append(article)

    print(f"  Decoded {decoded_count}/{len(articles)} URLs (rest kept for redirect-following)", file=sys.stderr)
    return decoded


# ---------------------------------------------------------------------------
# Step 3b: Byline extraction
# ---------------------------------------------------------------------------

_HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MediaResearch/1.0)"}
_AUTHOR_SOURCE_SCORES = {
    "jsonld_person": 3,
    "trafilatura": 2,
    "newspaper": 2,
    "jsonld_string": 1,
    "meta_author": 1,
    "og_author": 1,
}


def _fetch_html_head(url: str) -> Tuple[str, str]:
    """
    Fetch up to 60 KB of a URL's HTML and return (html, resolved_url).
    Uses streaming to avoid downloading full pages. Follows redirects.
    Works even on paywalled articles because meta tags are in <head>.
    Returns ('', url) on failure.
    """
    try:
        resp = requests.get(url, timeout=FETCH_TIMEOUT, headers=_HTTP_HEADERS,
                            stream=True, allow_redirects=True)
        if resp.status_code not in (200, 403):
            resp.close()
            return "", url
        chunks: List[bytes] = []
        total = 0
        for chunk in resp.iter_content(chunk_size=4096):
            chunks.append(chunk)
            total += len(chunk)
            if total >= 60000:
                break
        resp.close()
        return b"".join(chunks).decode("utf-8", errors="replace"), resp.url
    except Exception:
        return "", url


def _visible_text(html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def _extract_meta_content(html: str, names: List[str]) -> str:
    for name in names:
        pattern = (
            rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\'](.*?)["\']'
            rf'|<meta[^>]+content=["\'](.*?)["\'][^>]+(?:name|property)=["\']{re.escape(name)}["\']'
        )
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            value = next((group for group in match.groups() if group), "")
            if value:
                return re.sub(r"\s+", " ", value).strip()
    return ""


def _extract_title_tag(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _discover_rss_url(html: str, base_url: str) -> str:
    patterns = [
        r'<link[^>]+type=["\']application/rss\+xml["\'][^>]+href=["\'](.*?)["\']',
        r'<link[^>]+href=["\'](.*?)["\'][^>]+type=["\']application/rss\+xml["\']',
        r'<a[^>]+href=["\'](.*?)["\'][^>]*>\s*RSS\s*</a>',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return urljoin(base_url, match.group(1).strip())
    return ""


def _extract_same_domain_link(html: str, base_url: str, keywords: Tuple[str, ...]) -> str:
    base_domain = _domain_of(base_url)
    for href in re.findall(r'<a[^>]+href=["\'](.*?)["\']', html, flags=re.IGNORECASE | re.DOTALL):
        candidate = urljoin(base_url, href.strip())
        if base_domain and _domain_of(candidate) != base_domain:
            continue
        lower = candidate.lower()
        if any(keyword in lower for keyword in keywords):
            return candidate
    return ""


def _extract_email_from_html(html: str) -> str:
    mailto = re.search(r'mailto:([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})', html, flags=re.IGNORECASE)
    if mailto:
        return _normalize_email_candidate(mailto.group(1))
    visible = re.search(r'([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})', html, flags=re.IGNORECASE)
    if visible:
        return _normalize_email_candidate(visible.group(1))
    return ""


def _fetch_text_resource(url: str) -> str:
    try:
        resp = requests.get(url, timeout=FETCH_TIMEOUT, headers=_HTTP_HEADERS, allow_redirects=True)
        if resp.status_code != 200:
            return ""
        return resp.text
    except Exception:
        return ""


def _parse_rss_feed(feed_url: str) -> dict:
    xml_text = _fetch_text_resource(feed_url)
    if not xml_text:
        return {}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {}

    def _find_text(node, candidates: List[str]) -> str:
        for candidate in candidates:
            child = node.find(candidate)
            if child is not None and child.text:
                return re.sub(r"\s+", " ", child.text).strip()
        return ""

    channel = root.find("channel")
    if channel is None:
        channel = root.find("{http://www.w3.org/2005/Atom}channel")
    if channel is None:
        return {}

    show_title = _find_text(channel, ["title", "{*}title"])
    show_description = _find_text(channel, ["description", "{*}summary", "{*}subtitle"])
    show_author = _find_text(channel, ["{*}author", "managingEditor", "{*}owner/{*}name"])
    show_link = _find_text(channel, ["link", "{*}link"])

    episodes = []
    for item in channel.findall("item")[:15]:
        title = _find_text(item, ["title", "{*}title"])
        description = _find_text(item, ["description", "{*}summary", "{*}subtitle"])
        link = _find_text(item, ["link", "{*}link"])
        if not link:
            enclosure = item.find("enclosure")
            if enclosure is not None:
                link = enclosure.attrib.get("url", "")
        if title or description or link:
            episodes.append({"title": title, "description": description, "url": link})

    return {
        "show_title": show_title,
        "show_description": show_description,
        "show_author": show_author,
        "show_link": show_link,
        "episodes": episodes,
    }


def _has_byline_marker(name: str, html: str) -> bool:
    if not name or not html:
        return False
    text = _visible_text(html[:120000])
    escaped = re.escape(name)
    patterns = [
        rf"\bBy\s+{escaped}\b",
        rf"\bWritten by\s+{escaped}\b",
        rf"\bStory by\s+{escaped}\b",
    ]
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _dedupe_author_records(records: List[dict]) -> List[dict]:
    deduped: Dict[str, dict] = {}
    for record in records:
        name = (record.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        current = deduped.get(key)
        if current is None or record.get("confidence", 0) > current.get("confidence", 0):
            deduped[key] = record
    return list(deduped.values())


def _parse_authors_from_html(html: str) -> List[dict]:
    """
    Extract author names from HTML meta tags and JSON-LD structured data.
    This works on paywalled articles because authors are in <head> for SEO/social.
    """
    records: List[dict] = []

    # 1. JSON-LD — most reliable on modern news sites
    for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    ):
        try:
            data = json.loads(m.group(1))
            items = data if isinstance(data, list) else [data]
            for item in items:
                author_field = item.get("author")
                if isinstance(author_field, str) and author_field:
                    records.append({"name": author_field, "source": "jsonld_string"})
                elif isinstance(author_field, dict):
                    author_type = str(author_field.get("@type", "")).lower()
                    if author_type and author_type != "person":
                        continue
                    name = author_field.get("name", "").strip()
                    if name:
                        records.append({"name": name, "source": "jsonld_person"})
                elif isinstance(author_field, list):
                    for a in author_field:
                        if isinstance(a, dict):
                            author_type = str(a.get("@type", "")).lower()
                            if author_type and author_type != "person":
                                continue
                            name = a.get("name", "").strip()
                            source = "jsonld_person"
                        else:
                            name = str(a).strip()
                            source = "jsonld_string"
                        if name:
                            records.append({"name": name, "source": source})
        except Exception:
            pass
    if records:
        return _dedupe_author_records(records)

    # 2. <meta name="author">
    for pattern in [
        r'<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']author["\']',
    ]:
        for m in re.finditer(pattern, html, re.IGNORECASE):
            name = m.group(1).strip()
            if name:
                records.append({"name": name, "source": "meta_author"})
    if records:
        return _dedupe_author_records(records)

    # 3. Open Graph article:author (skip if it's a URL, not a name)
    for pattern in [
        r'<meta[^>]+property=["\']article:author["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']article:author["\']',
    ]:
        for m in re.finditer(pattern, html, re.IGNORECASE):
            name = m.group(1).strip()
            if name and not name.startswith("http"):
                records.append({"name": name, "source": "og_author"})

    return _dedupe_author_records(records)


def _extract_authors_newspaper(url: str) -> List[dict]:
    """Try newspaper3k to extract author names from article URL."""
    try:
        art = Article(url, request_timeout=FETCH_TIMEOUT)
        art.download()
        art.parse()
        return [{"name": a.strip(), "source": "newspaper"} for a in art.authors if a.strip()]
    except Exception:
        return []


def _extract_authors_trafilatura(html: str, url: str) -> List[dict]:
    """Try trafilatura to extract author metadata from already-fetched HTML."""
    try:
        meta = trafilatura.extract_metadata(html, default_url=url)
        if meta and meta.author:
            return [{"name": n.strip(), "source": "trafilatura"} for n in meta.author.split(";") if n.strip()]
    except Exception:
        pass
    return []


def _fetch_byline(article: dict):
    """
    Try to extract at least one author name from the article URL.
    Returns enriched article dict with 'authors' list, or None if no author found.

    Strategy (in order):
    1. Fetch HTML head and parse meta/JSON-LD — works on paywalled articles
    2. If trafilatura available, parse same HTML with it (no second fetch)
    3. newspaper3k as last resort (separate fetch)
    """
    url = article.get("url", "")
    if not url:
        return None

    # Fetch once — meta extraction + trafilatura reuse the same HTML
    html, resolved_url = _fetch_html_head(url)
    if not _is_story_url(resolved_url or url):
        return None
    update = {"url": resolved_url} if resolved_url != url else {}

    author_records = _parse_authors_from_html(html) if html else []

    if not author_records and html and HAS_TRAFILATURA:
        author_records = _extract_authors_trafilatura(html, resolved_url or url)

    if not author_records and HAS_NEWSPAPER:
        author_records = _extract_authors_newspaper(resolved_url or url)

    if not author_records:
        return None

    enriched_records = []
    for record in author_records:
        name = (record.get("name") or "").strip()
        if not name:
            continue
        byline_marker = _has_byline_marker(name, html) if html else False
        source = record.get("source", "unknown")
        confidence = _AUTHOR_SOURCE_SCORES.get(source, 0) + (2 if byline_marker else 0)
        enriched_records.append({
            "name": name,
            "source": source,
            "byline_marker": byline_marker,
            "confidence": confidence,
        })

    enriched_records = _dedupe_author_records(enriched_records)
    if not enriched_records:
        return None

    return {
        **article,
        **update,
        "authors": [record["name"] for record in enriched_records],
        "author_records": enriched_records,
    }


def extract_bylines(articles: List[dict]) -> List[dict]:
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

_NON_PERSON_TOKENS = {
    "media", "video", "agency", "agencies", "studio", "studios", "press",
    "prime", "digital", "talent", "business", "team", "staff", "wire",
    "newsroom", "service", "services", "company", "companies", "group",
    "department", "official", "office", "organization", "network",
    "entertainment", "llc", "inc", "corp", "ltd", "co", "amazon", "google",
    "meta", "microsoft", "apple", "netflix", "youtube",
}


def _is_person_name(name: str) -> bool:
    """Heuristic: a journalist name should look like 'First Last' — 2-4 words, no junk."""
    if len(name) < 5 or len(name) > 60:
        return False
    lower = name.lower()
    if any(frag in lower for frag in _JUNK_FRAGMENTS):
        return False
    if any(ch.isdigit() for ch in name):
        return False
    words = name.split()
    # Must be 2–4 words
    if len(words) < 2 or len(words) > 4:
        return False
    # No word should be a known junk token
    if any(w.lower().rstrip(".,;") in _JUNK_WORDS for w in words):
        return False
    if any(w.lower().rstrip(".,;") in _NON_PERSON_TOKENS for w in words):
        return False
    # Each word should start with a capital letter
    if not all(w[0].isupper() for w in words if w):
        return False
    if not all(re.fullmatch(r"[A-Z][A-Za-z'`.-]*", w) for w in words):
        return False
    # No hyphens spanning the full name (CSS class artifacts like "Margin-Bottom")
    if any("-" in w and len(w) > 8 for w in words):
        return False
    return True


def group_by_journalist(articles_with_bylines: List[dict]) -> List[dict]:
    """
    Group articles by author name. Each journalist entry has their outlet
    and a list of articles they wrote, as evidence of their beat.
    """
    journalist_map: Dict[str, dict] = {}

    for article in articles_with_bylines:
        if not _is_story_url(article.get("url", "")):
            continue
        author_records = article.get("author_records") or [
            {"name": author, "source": "unknown", "confidence": 0, "byline_marker": False}
            for author in article.get("authors", [])
        ]
        for author_record in author_records:
            name = (author_record.get("name") or "").strip().title()
            if not _is_person_name(name):
                continue

            if name not in journalist_map:
                journalist_map[name] = {
                    "name": name,
                    "outlet": article.get("source", ""),
                    "articles": [],
                    "guessed_media_type": _guess_media_type(article.get("source", "")),
                    "author_confidences": [],
                    "author_sources": set(),
                }

            journalist_map[name]["articles"].append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "date": article.get("date", ""),
                "source": article.get("source", ""),
                "relevance_score": article.get("relevance_score", 0),
                "relevance_reason": article.get("relevance_reason", ""),
            })
            journalist_map[name]["author_confidences"].append(author_record.get("confidence", 0))
            journalist_map[name]["author_sources"].add(author_record.get("source", "unknown"))

            # Use the outlet from the most-covered source for this journalist
            # (outlet they appear most with wins)
            outlet_counts: Dict[str, int] = {}
            for a in journalist_map[name]["articles"]:
                s = a.get("source", "")
                if s:
                    outlet_counts[s] = outlet_counts.get(s, 0) + 1
            if outlet_counts:
                journalist_map[name]["outlet"] = max(outlet_counts, key=outlet_counts.__getitem__)
                journalist_map[name]["guessed_media_type"] = _guess_media_type(journalist_map[name]["outlet"])

    for journalist in journalist_map.values():
        journalist["articles"] = _dedupe_articles_by_story(journalist["articles"])
        journalist["articles"] = [article for article in journalist["articles"] if _is_story_url(article.get("url", ""))]
        if not journalist["articles"]:
            continue
        journalist["best_article"] = max(
            journalist["articles"],
            key=lambda article: article.get("relevance_score", 0),
        )
        top_scores = [article.get("relevance_score", 0) for article in journalist["articles"][:3]]
        journalist["topic_fit_score"] = round(
            journalist["best_article"].get("relevance_score", 0) + (sum(top_scores) / max(len(top_scores), 1)),
            1,
        )
        journalist["supporting_evidence"] = journalist["best_article"].get("relevance_reason", "")
        max_author_confidence = max(journalist.get("author_confidences") or [0])
        article_support = min(max(len(journalist["articles"]) - 1, 0), 2)
        identity_score = max_author_confidence + article_support
        journalist["identity_confidence_score"] = identity_score
        journalist["identity_confidence"] = (
            "high" if identity_score >= 5 else
            "medium" if identity_score >= 4 else
            "low"
        )

    journalists = sorted(
        [journalist for journalist in journalist_map.values() if journalist.get("articles")],
        key=lambda j: (j.get("topic_fit_score", 0), len(j["articles"])),
        reverse=True,
    )
    return journalists


def diversify_journalists(
    journalists: List[dict],
    limit: int,
    media_types: List[str],
    is_national: bool,
    location: str = "",
) -> List[dict]:
    filtered = []
    for journalist in journalists:
        if is_national and not _is_national_outlet(journalist.get("outlet", "")):
            continue
        best_article = journalist.get("best_article", {}) or {}
        if not _matches_location_scope(best_article, location, is_national):
            continue
        guessed_type = journalist.get("guessed_media_type", "digital")
        if not _media_type_matches(journalist.get("outlet", ""), guessed_type, media_types):
            continue
        filtered.append(journalist)

    if not filtered:
        filtered = journalists

    selected = []
    outlet_counts: Dict[str, int] = {}
    type_counts: Dict[str, int] = {}
    requested_types = list(media_types or [])
    min_per_type = 1 if requested_types else 0

    for journalist in filtered:
        outlet = (journalist.get("outlet") or "").lower()
        guessed_type = journalist.get("guessed_media_type", "digital")
        if outlet and outlet_counts.get(outlet, 0) >= MAX_PER_OUTLET:
            continue
        if requested_types and type_counts.get(guessed_type, 0) >= max(2, limit // max(len(requested_types), 1) + 1):
            continue
        selected.append(journalist)
        if outlet:
            outlet_counts[outlet] = outlet_counts.get(outlet, 0) + 1
        type_counts[guessed_type] = type_counts.get(guessed_type, 0) + 1
        if len(selected) >= limit:
            break

    if requested_types:
        for media_type in requested_types:
            if type_counts.get(media_type, 0) >= min_per_type:
                continue
            for journalist in filtered:
                if journalist in selected:
                    continue
                if not _media_type_matches(
                    journalist.get("outlet", ""),
                    journalist.get("guessed_media_type", "digital"),
                    [media_type],
                ):
                    continue
                selected.append(journalist)
                type_counts[media_type] = type_counts.get(media_type, 0) + 1
                break

    if len(selected) < limit:
        selected_ids = {j["name"] for j in selected}
        for journalist in filtered:
            if journalist["name"] in selected_ids:
                continue
            selected.append(journalist)
            if len(selected) >= limit:
                break
    return selected


def _fallback_contact_from_journalist(journalist: dict) -> dict:
    name_parts = journalist.get("name", "").split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    best_article = journalist.get("best_article", {}) or {}
    if not _is_story_url(best_article.get("url", "")):
        best_article = next(
            (article for article in journalist.get("articles", []) if _is_story_url(article.get("url", ""))),
            {},
        )
    identity_confidence = journalist.get("identity_confidence", "medium")
    low_confidence = identity_confidence == "low"
    return {
        "first_name": first_name,
        "last_name": last_name,
        "outlet": journalist.get("outlet", ""),
        "outlet_website": "",
        "role": "Reporter / author to verify" if low_confidence else "Reporter",
        "media_type": journalist.get("guessed_media_type", "digital"),
        "location": "",
        "pitch_angle": (
            f"Recent coverage on {best_article.get('title', 'this issue')} makes this reporter a plausible fit for a targeted pitch."
            if best_article.get("title") else "Reporter covers the issue area and warrants manual pitch refinement."
        ),
        "why_now": best_article.get("title", ""),
        "pitch_offer": "",
        "previous_story_title": best_article.get("title", ""),
        "previous_story_url": best_article.get("url", ""),
        "email": "",
        "notes": (
            "Author name comes from weaker article metadata and should be manually confirmed before outreach."
            if low_confidence else
            "Generated from verified article evidence because the enrichment pass returned an incomplete contact set."
        ),
        "contact_status": "low_confidence_named" if low_confidence else "verified_fallback",
        "topic_fit_score": journalist.get("topic_fit_score", 0),
        "supporting_evidence": journalist.get("supporting_evidence", ""),
        "relevance_confidence": "medium",
        "identity_confidence": identity_confidence,
    }


def _story_outlet_website(article: dict) -> str:
    url = (article.get("url") or "").strip()
    domain = _domain_of(url)
    return f"https://{domain}" if domain else ""


def _contact_name_key(first_name: str, last_name: str) -> str:
    return " ".join(part for part in [first_name, last_name] if part).strip().lower()


def _find_supporting_article_for_contact(contact: dict, articles: List[dict]) -> dict:
    story_url = (contact.get("previous_story_url") or "").strip()
    outlet = (contact.get("outlet") or "").strip().lower()
    if story_url and _is_story_url(story_url):
        for article in articles:
            if (article.get("url") or "").strip() == story_url:
                return article
    if outlet:
        matching = [
            article for article in articles
            if ((article.get("source") or _domain_of(article.get("url", ""))).strip().lower() == outlet)
        ]
        if matching:
            story_matches = [article for article in matching if _is_story_url(article.get("url", ""))]
            preferred = story_matches or matching
            return sorted(preferred, key=lambda article: article.get("relevance_score", 0), reverse=True)[0]
    return {}


def _fallback_contact_from_story(article: dict) -> dict:
    source = article.get("source", "") or _domain_of(article.get("url", ""))
    score = article.get("relevance_score", 0)
    return {
        "first_name": "To verify",
        "last_name": "",
        "outlet": source,
        "outlet_website": _story_outlet_website(article),
        "role": "Reporter / author to verify",
        "media_type": _guess_media_type(source),
        "location": "",
        "pitch_angle": (
            f"This outlet's recent coverage on {article.get('title', 'this issue')} is a strong match for a targeted pitch."
            if article.get("title") else "High-confidence story match from a target outlet; author needs verification."
        ),
        "why_now": article.get("title", ""),
        "pitch_offer": "",
        "previous_story_title": article.get("title", ""),
        "previous_story_url": article.get("url", ""),
        "email": "",
        "notes": "High-confidence story lead from a filter-matching outlet. Author identity needs manual verification.",
        "contact_status": "story_lead",
        "topic_fit_score": score,
        "supporting_evidence": article.get("relevance_reason", ""),
        "relevance_confidence": "high",
        "identity_confidence": "unknown",
    }


def _merge_with_fallback_contacts(contacts: List[dict], journalists: List[dict], target_count: int, media_types: List[str]) -> List[dict]:
    merged = list(contacts)
    seen = {
        " ".join(part for part in [c.get("first_name", ""), c.get("last_name", "")] if part).strip().lower()
        for c in merged
    }
    for journalist in journalists:
        if len(merged) >= target_count:
            break
        name_key = journalist.get("name", "").strip().lower()
        if not name_key or name_key in seen:
            continue
        guessed_type = journalist.get("guessed_media_type", "digital")
        if not _media_type_matches(journalist.get("outlet", ""), guessed_type, media_types):
            continue
        merged.append(_fallback_contact_from_journalist(journalist))
        seen.add(name_key)
    return merged


def _article_matches_output_scope(article: dict, media_types: List[str], is_national: bool, location: str = "") -> bool:
    outlet = article.get("source", "") or _domain_of(article.get("url", ""))
    if not outlet:
        return False
    if _is_non_media_url(article.get("url", "")):
        return False
    if article.get("relevance_score", 0) < HIGH_CONFIDENCE_STORY_SCORE:
        return False
    if is_national and not _is_national_outlet(outlet):
        return False
    if not _matches_location_scope(article, location, is_national):
        return False
    if not _is_story_url(article.get("url", "")):
        return False
    guessed_type = _guess_media_type(outlet)
    if not _media_type_matches(outlet, guessed_type, media_types):
        return False
    if not article.get("title") or not article.get("url"):
        return False
    return True


def _merge_with_story_leads(
    contacts: List[dict],
    articles: List[dict],
    target_count: int,
    media_types: List[str],
    is_national: bool,
    location: str = "",
) -> List[dict]:
    merged = list(contacts)
    seen_story_urls = {
        (c.get("previous_story_url") or "").strip()
        for c in merged
        if c.get("previous_story_url")
    }
    outlet_counts: Dict[str, int] = {}
    for contact in merged:
        outlet = (contact.get("outlet") or "").strip().lower()
        if outlet:
            outlet_counts[outlet] = outlet_counts.get(outlet, 0) + 1

    candidates = sorted(
        (article for article in articles if _article_matches_output_scope(article, media_types, is_national, location)),
        key=lambda article: article.get("relevance_score", 0),
        reverse=True,
    )
    for article in candidates:
        if len(merged) >= target_count:
            break
        story_url = (article.get("url") or "").strip()
        if not story_url or story_url in seen_story_urls:
            continue
        outlet = ((article.get("source") or _domain_of(story_url)) or "").strip().lower()
        if outlet and outlet_counts.get(outlet, 0) >= MAX_STORY_ROWS_PER_OUTLET:
            continue
        merged.append(_fallback_contact_from_story(article))
        seen_story_urls.add(story_url)
        if outlet:
            outlet_counts[outlet] = outlet_counts.get(outlet, 0) + 1
    return merged


def _sanitize_generated_contacts(
    contacts: List[dict],
    journalist_lookup: Dict[str, dict],
    articles: List[dict],
    media_types: List[str],
    is_national: bool,
    location: str = "",
) -> List[dict]:
    sanitized = []
    seen_story_urls = set()
    for contact in contacts:
        full_name = _contact_name_key(contact.get("first_name", ""), contact.get("last_name", ""))
        display_name = " ".join(
            part for part in [contact.get("first_name", ""), contact.get("last_name", "")] if part
        ).strip()
        source_journalist = journalist_lookup.get(full_name)
        source_article = _find_supporting_article_for_contact(contact, articles)
        if source_journalist and source_journalist.get("identity_confidence") in {"high", "medium"}:
            contact["contact_status"] = contact.get("contact_status") or "verified"
            contact["identity_confidence"] = source_journalist.get("identity_confidence", "medium")
            if contact.get("email") in {"[RESEARCH NEEDED]", "[VERIFY]"}:
                contact["email"] = ""
            sanitized.append(contact)
            story_url = (contact.get("previous_story_url") or "").strip()
            if story_url:
                seen_story_urls.add(story_url)
            continue

        if source_journalist and source_journalist.get("identity_confidence") == "low" and source_article:
            if not _article_matches_output_scope(source_article, media_types, is_national, location):
                continue
            downgraded = dict(contact)
            downgraded["contact_status"] = "low_confidence_named"
            downgraded["identity_confidence"] = "low"
            if downgraded.get("email") in {"[RESEARCH NEEDED]", "[VERIFY]"}:
                downgraded["email"] = ""
            downgraded["role"] = downgraded.get("role") or "Reporter / author to verify"
            downgraded["notes"] = (
                "Author identity comes from weaker byline evidence. Name, role, and email should be manually confirmed before outreach."
            )
            if not downgraded.get("previous_story_title"):
                downgraded["previous_story_title"] = source_article.get("title", "")
            if not downgraded.get("previous_story_url"):
                downgraded["previous_story_url"] = source_article.get("url", "")
            story_url = (downgraded.get("previous_story_url") or "").strip()
            if story_url and story_url in seen_story_urls:
                continue
            sanitized.append(downgraded)
            if story_url:
                seen_story_urls.add(story_url)
            continue

        if not source_article:
            continue
        if not _article_matches_output_scope(source_article, media_types, is_national, location):
            continue

        if display_name and _is_person_name(display_name):
            inferred = dict(contact)
            inferred["contact_status"] = "low_confidence_named"
            inferred["identity_confidence"] = "low"
            if inferred.get("email") in {"[RESEARCH NEEDED]", "[VERIFY]"}:
                inferred["email"] = ""
            inferred["role"] = inferred.get("role") or "Reporter / author to verify"
            inferred["notes"] = (
                "Name was inferred from the relevant story/outlet context and should be manually confirmed before outreach."
            )
            if not inferred.get("previous_story_title"):
                inferred["previous_story_title"] = source_article.get("title", "")
            if not inferred.get("previous_story_url"):
                inferred["previous_story_url"] = source_article.get("url", "")
            story_url = (inferred.get("previous_story_url") or "").strip()
            if story_url and story_url in seen_story_urls:
                continue
            sanitized.append(inferred)
            if story_url:
                seen_story_urls.add(story_url)
            continue

        story_lead = _fallback_contact_from_story(source_article)
        story_url = (story_lead.get("previous_story_url") or "").strip()
        if story_url and story_url in seen_story_urls:
            continue
        sanitized.append(story_lead)
        if story_url:
            seen_story_urls.add(story_url)

    return sanitized


def _coverage_summary(contacts: List[dict], requested_contacts: int, requested_media_types: List[str]) -> Tuple[dict, List[str], str]:
    counts: Dict[str, int] = {}
    outlets = set()
    for contact in contacts:
        media_type = contact.get("media_type", "other")
        counts[media_type] = counts.get(media_type, 0) + 1
        outlet = (contact.get("outlet") or "").strip().lower()
        if outlet:
            outlets.add(outlet)

    notes = []
    if len(contacts) == 0:
        return counts, ["No usable contacts were returned for the selected issue and scope."], "empty"
    if len(contacts) < requested_contacts:
        notes.append(f"Returned {len(contacts)} of {requested_contacts} requested contacts.")
    story_lead_count = sum(1 for contact in contacts if contact.get("contact_status") == "story_lead")
    if story_lead_count:
        notes.append(f"{story_lead_count} rows are high-confidence story leads where the author still needs verification.")
    low_confidence_named_count = sum(1 for contact in contacts if contact.get("contact_status") == "low_confidence_named")
    if low_confidence_named_count:
        notes.append(f"{low_confidence_named_count} named rows rely on weaker byline evidence and should be checked before outreach.")
    missing_types = [mt for mt in (requested_media_types or []) if counts.get(mt, 0) == 0]
    if missing_types:
        notes.append(f"No usable contacts found for: {', '.join(MEDIA_TYPE_LABELS.get(mt, mt) for mt in missing_types)}.")
    if len(outlets) < min(len(contacts), 3):
        notes.append("Outlet diversity is limited for this run.")

    quality = "complete"
    if len(contacts) == 0:
        quality = "empty"
    elif notes:
        quality = "partial"
    return counts, notes, quality


def _contact_confidence_label(contact: dict) -> str:
    status = contact.get("contact_status")
    if status == "story_lead":
        return "Story Lead"
    if status == "show_only_verify_host":
        return "Show Match"
    if status == "identified_no_contact":
        return "Host Identified"
    if status == "identified_with_contact":
        return "Host + Contact"
    if status == "low_confidence_named":
        return "Low Confidence"
    return "Verified"


def _conservative_why_now(contact: dict) -> str:
    if contact.get("media_type") == "podcast":
        matched_title = (contact.get("matched_title") or "").strip()
        show_name = (contact.get("show_name") or contact.get("outlet") or "").strip()
        evidence_type = (contact.get("matched_evidence_type") or "").replace("_", " ")
        if matched_title and evidence_type:
            return f'{show_name}: matched via {evidence_type} "{matched_title}".'
        if matched_title:
            return f'{show_name}: matched via "{matched_title}".'
        return "Podcast match requires manual review before outreach."
    title = (contact.get("previous_story_title") or "").strip()
    outlet = (contact.get("outlet") or "").strip()
    if contact.get("contact_status") == "story_lead":
        if title and outlet:
            return f'Strong recent story match at {outlet}: "{title}".'
        if title:
            return f'Recent relevant story match: "{title}".'
        return "Strong outlet/story match; author still needs verification."
    if title and outlet:
        return f'Recent relevant coverage at {outlet}: "{title}".'
    if title:
        return f'Recent relevant coverage: "{title}".'
    return "Recent coverage in this issue area suggests a timely outreach opening."


def _contact_thresholds_met(
    contacts: List[dict],
    media_types: List[str],
    strong: bool = False,
    requested_contacts: Optional[int] = None,
) -> bool:
    if not contacts:
        return False
    outlets = {((c.get("outlet") or "").strip().lower()) for c in contacts if c.get("outlet")}
    media_type_counts = {}
    for contact in contacts:
        media_type = contact.get("media_type", "other")
        media_type_counts[media_type] = media_type_counts.get(media_type, 0) + 1

    represented_types = sum(1 for mt in (media_types or []) if media_type_counts.get(mt, 0) > 0)
    if strong:
        target_contacts = min(
            LAYER1_STRONG_STOP_CONTACTS,
            max(requested_contacts or LAYER1_STRONG_STOP_CONTACTS, LAYER1_USABLE_MIN_CONTACTS),
        )
        target_outlets = min(LAYER1_STRONG_STOP_OUTLETS, max(3, target_contacts // 2))
        return (
            len(contacts) >= target_contacts
            and len(outlets) >= target_outlets
            and represented_types >= min(2, len(media_types or []))
        )
    return len(contacts) >= LAYER1_USABLE_MIN_CONTACTS and len(outlets) >= 3


# ---------------------------------------------------------------------------
# Step 4: LLM enrichment
# ---------------------------------------------------------------------------

ENRICH_SYSTEM = """You are a senior public affairs media strategist who has pitched thousands of journalists at national and regional outlets.

You will receive a list of people discovered via article research. Each person comes with actual articles they have written on the topic.

JOURNALISTS ONLY — CRITICAL RULE:
Only include working journalists, reporters, correspondents, editors, columnists, or hosts at actual NEWS MEDIA organizations.
- INCLUDE: newspapers, wire services (AP, Reuters, AFP), TV/radio networks, digital news outlets, news magazines, investigative outlets, podcasts
- EXCLUDE entirely: think tank fellows, law firm associates, NGO staff, government officials, academics, corporate PR
If a person's outlet is clearly not a news media organization, skip them.

PITCH ANGLE AND WHY-NOW QUALITY RULES:

pitch_angle must:
- Connect the reporter's SPECIFIC documented article to a SPECIFIC development (a vote, ruling, filing, deadline, appointment, or newly released document)
- Name the development concretely — bill number, agency name, ruling date, person involved
- Be one or two sentences a real PA professional would write in an email
- Sound like: "Her March piece on FTC enforcement gaps sets up a direct follow: the agency's comment period on the data broker rule closes May 30 — our client has filed technical objections."
- NOT sound like: "Leverage their coverage of tech policy to explore emerging legislative language on AI regulation."

why_now must:
- Name a SPECIFIC trigger: a date, deadline, vote, hearing, ruling, filing, or newly public document
- Be something that happened, is happening, or is imminent — not a trend or pattern
- Sound like: "Senate Finance markup is scheduled for Thursday." / "The ruling came down yesterday." / "Comment period closes Friday."
- NOT sound like: "This issue is gaining traction." / "Timely update given recent developments." / "Emerging consensus around this topic."

pitch_offer must:
- Propose ONE concrete value-add that is plausible given the provided context
- Choose from: named expert available for interview / background call with identified source / access to a specific public filing or data / on-record statement / event access with logistics
- Be honest — do not offer exclusive data, embargoed material, or access that is not grounded in available context
- Sound like: "Our policy director drafted the comment and is available for background this week." / "The filing is public — I can send the relevant sections."
- NOT sound like: "We would be happy to provide a brief background briefing on this issue."

BANNED PHRASES — never use these in any field:
"emerging legislative language" / "timely update" / "updating consensus" / "brief briefing" /
"gaining traction" / "given recent developments" / "story angle" / "could be a great fit" /
"we have exciting news" / "I wanted to flag" / "regulatory landscape" (without naming the specific rule)

ADDITIONAL RULES:
- Do NOT invent or add any journalists not in the input list
- Base all pitch angles on the actual articles provided — do not force analogies
- For email: use the outlet's known pattern (e.g. first.last@nytimes.com). If unknown: [RESEARCH NEEDED]
- media_type: one of "mainstream", "print", "broadcast", "digital", "trade", "podcast"
- outlet_website: full https:// URL for the outlet homepage
- previous_story_title: most relevant article from their list
- previous_story_url: the provided URL — do not fabricate
- location: the journalist's primary city and state (or country if non-US), e.g. "Washington, D.C.", "New York, NY", "Chicago, IL", "London, UK". Use the outlet's known primary bureau if city is not explicit from the article URLs. Never leave blank — use the outlet's headquarter city as fallback.
- GEOGRAPHIC SCOPE: national scope = national-audience outlets only (NYT, WaPo, Politico, NPR). Local scope = include local and regional journalists covering that area.

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
      "why_now": "...",
      "pitch_offer": "...",
      "previous_story_title": "...",
      "previous_story_url": "https://...",
      "email": "...",
      "notes": "..."
    }
  ],
  "pitch_timing": "..."
}"""


def enrich_contacts(journalists: List[dict], issue: str, location: str,
                    media_types: List[str], is_national: bool, client: OpenAI) -> dict:
    """LLM enrichment — adds pitch angles and contact details for real discovered journalists."""

    # Build journalist summaries for the prompt
    journalist_lines = []
    for j in journalists:
        articles_text = "; ".join(
            f'"{a["title"]}" ({a["date"]}) [score={a.get("relevance_score", 0)}; {a.get("relevance_reason", "")}] [{a["url"]}]'
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
        "Prioritize reporters and outlets whose coverage is clearly tied to that exact city or metro. "
        "Do not include journalists from other metros just because they cover a similar issue."
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
        "Write pitch angles based on their actual documented coverage. "
        "Each pitch_angle must be reporter-specific, news-driven, and concrete about what changed or why this matters now. "
        "Use why_now for the specific hook, development, deadline, conflict, or newly salient fact that makes the outreach timely. "
        "Do not force analogies. If the supplied stories are directly on the issue, pitch the direct development instead of a parallel case. "
        "Only reference a prior story if it is plainly relevant to the same issue or a closely connected sanctions/regulatory development."
    )

    response = client.chat.completions.create(
        model=_active_model(MODEL),
        messages=[
            {"role": "system", "content": ENRICH_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        **_max_tokens_kwarg(6000),
        **_response_format_kwarg(),
    )

    return _parse_json_content(response.choices[0].message.content)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_media_list(
    issue: str,
    location: str = "US",
    media_types: Optional[List[str]] = None,
    num_contacts: int = 20,
    source_filter: str = "national",
    broad_topic: str = "",
    coverage_desk: str = "",
    topic_mode: str = "specific",
) -> dict:
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
    broad_topic = (broad_topic or "").strip()
    coverage_desk = (coverage_desk or "").strip()
    topic_mode = (topic_mode or "specific").strip().lower()
    if topic_mode not in {"specific", "broad"}:
        topic_mode = "specific"
    if not (issue or broad_topic or coverage_desk):
        raise ValueError("An issue, broad topic, or coverage desk is required.")
    search_subject = (broad_topic or issue or coverage_desk).strip()
    wants_podcast = "podcast" in (media_types or [])
    podcast_only = set(media_types or []) == {"podcast"}

    is_national = location.upper() in ("US", "USA", "NATIONAL") and source_filter != "all"
    retrieval_layers_used = ["podcast"] if podcast_only else ["layer1"]
    layer1_candidate_count = 0
    layer2_candidate_count = 0
    layer3_candidate_count = 0
    podcast_candidate_count = 0

    # Step 1: Analyze story + build a topic-anchored search plan
    print("Step 1: Analyzing story and expanding search queries...", file=sys.stderr)
    query_plan, story_analysis = expand_queries(
        issue or search_subject,
        location,
        client,
        broad_topic=broad_topic,
        coverage_desk=coverage_desk,
        topic_mode=topic_mode,
    )
    print(f"  Queries: {[q['query'] for q in query_plan]}", file=sys.stderr)

    if podcast_only:
        print("Step 2: Running podcast-only discovery...", file=sys.stderr)
        podcast_contacts = retrieve_podcast_candidates(
            query_plan,
            search_subject,
            location,
            is_national,
            broad_topic,
            coverage_desk,
            topic_mode,
        )
        podcast_candidate_count = len(podcast_contacts)
        for contact in podcast_contacts:
            contact["confidence_label"] = _contact_confidence_label(contact)
            contact["why_now"] = _conservative_why_now(contact)
        coverage_by_media_type, coverage_notes, result_quality = _coverage_summary(
            podcast_contacts[:num_contacts],
            num_contacts,
            media_types,
        )
        supporting_articles = []
        seen_support_urls = set()
        for contact in podcast_contacts[:num_contacts]:
            url = (contact.get("matched_url") or contact.get("show_url") or "").strip()
            if not url or url in seen_support_urls:
                continue
            seen_support_urls.add(url)
            supporting_articles.append({
                "title": contact.get("matched_title", "") or contact.get("show_name", "") or "View show",
                "source": contact.get("show_name", "") or contact.get("outlet", ""),
                "url": url,
                "relevance_score": contact.get("topic_fit_score", 0),
                "relevance_reason": contact.get("supporting_evidence", ""),
            })
        return {
            "issue": issue,
            "search_subject": search_subject,
            "topic_mode": topic_mode,
            "broad_topic": broad_topic,
            "coverage_desk": coverage_desk,
            "location": location,
            "media_types": media_types,
            "contacts": podcast_contacts[:num_contacts],
            "pitch_timing": (
                "Podcast matches are prioritized by host identification and topical fit. "
                "Verify booking preferences before outreach."
                if podcast_contacts else
                "No relevant podcast shows or episodes were found for this topic and scope."
            ),
            "news_research": supporting_articles[:8],
            "story_analysis": story_analysis,
            "requested_contacts": num_contacts,
            "returned_contacts": min(len(podcast_contacts), num_contacts),
            "coverage_by_media_type": coverage_by_media_type,
            "coverage_notes": coverage_notes or (
                ["Podcast rows may be based on a specific episode or on show-level description matching."]
                if podcast_contacts else
                ["No podcast candidates cleared relevance and scope filters."]
            ),
            "result_quality": result_quality,
            "retrieval_layers_used": retrieval_layers_used,
            "layer1_candidate_count": layer1_candidate_count,
            "layer2_candidate_count": layer2_candidate_count,
            "layer3_candidate_count": layer3_candidate_count,
            "podcast_candidate_count": podcast_candidate_count,
            "validated_journalist_count": 0,
        }

    # Stage A: start retrieval layers in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        layer1_future = executor.submit(retrieve_layer1_news, query_plan, search_subject, location)
        layer2_future = executor.submit(
            retrieve_layer2_search,
            query_plan,
            search_subject,
            location,
            media_types,
            is_national,
            broad_topic,
            coverage_desk,
            topic_mode,
        )
        podcast_future = (
            executor.submit(
                retrieve_podcast_candidates,
                query_plan,
                search_subject,
                location,
                is_national,
                broad_topic,
                coverage_desk,
                topic_mode,
            )
            if wants_podcast else None
        )
        if podcast_only:
            articles = []
            journalists = []
            layer2_articles = []
            provider = NoopSearchProvider()
        else:
            print("Step 2: Collecting Layer 1 candidates...", file=sys.stderr)
            try:
                articles = layer1_future.result() or []
            except Exception:
                articles = []
            layer1_candidate_count = len(articles)
            print(f"  Layer 1 found {layer1_candidate_count} unique articles", file=sys.stderr)

            articles = filter_media_articles(articles)
            print(f"  {len(articles)} layer 1 articles remain after source filter", file=sys.stderr)

            print("Step 3: Decoding layer 1 URLs...", file=sys.stderr)
            articles = decode_urls(articles)

            print("Step 3b: Extracting journalist bylines from layer 1...", file=sys.stderr)
            articles_with_bylines = extract_bylines(articles)

            journalists = group_by_journalist(articles_with_bylines)
            journalists = diversify_journalists(journalists, max(num_contacts * 2, num_contacts), media_types, is_national, location)
            print(f"  Layer 1 identified {len(journalists)} unique journalists", file=sys.stderr)

            provisional_contacts = [
                _fallback_contact_from_journalist(journalist)
                for journalist in journalists[: max(num_contacts, LAYER1_USABLE_MIN_CONTACTS)]
            ]

            use_layer2 = not _contact_thresholds_met(
                provisional_contacts,
                media_types,
                strong=True,
                requested_contacts=num_contacts,
            )
            if use_layer2:
                retrieval_layers_used.append("layer2")
                try:
                    layer2_articles, provider = layer2_future.result(timeout=LAYER2_WAIT_TIMEOUT)
                except Exception:
                    layer2_articles, provider = [], NoopSearchProvider()
                layer2_candidate_count = len(layer2_articles)
                print(f"  Layer 2 yielded {layer2_candidate_count} validated broad-web candidates", file=sys.stderr)
                combined = _dedupe_articles_by_story(articles + layer2_articles)
                articles = combined
                print("Step 3c: Extracting bylines from merged layer 1 + layer 2 candidates...", file=sys.stderr)
                combined_with_bylines = extract_bylines(articles)
                journalists = group_by_journalist(combined_with_bylines)
                journalists = diversify_journalists(journalists, max(num_contacts * 2, num_contacts), media_types, is_national, location)
                print(f"  Merged layers identified {len(journalists)} unique journalists", file=sys.stderr)
            else:
                try:
                    layer2_articles, provider = layer2_future.result(timeout=0.01)
                    layer2_candidate_count = len(layer2_articles)
                except Exception:
                    provider = NoopSearchProvider()

    podcast_contacts: List[dict] = []
    if podcast_future:
        try:
            podcast_contacts = podcast_future.result(timeout=10) or []
        except Exception:
            podcast_contacts = []
        podcast_candidate_count = len(podcast_contacts)
        if podcast_contacts:
            retrieval_layers_used.append("podcast")

    trusted_journalists = [
        journalist for journalist in journalists
        if journalist.get("identity_confidence") in {"high", "medium"}
    ]

    if not journalists:
        story_only_contacts = _merge_with_story_leads([], articles, num_contacts, media_types, is_national, location)
        coverage_by_media_type, coverage_notes, result_quality = _coverage_summary(
            story_only_contacts,
            num_contacts,
            media_types,
        )
        if podcast_contacts:
            story_only_contacts = (story_only_contacts + podcast_contacts)[:num_contacts]
            coverage_by_media_type, coverage_notes, result_quality = _coverage_summary(
                story_only_contacts,
                num_contacts,
                media_types,
            )
        if story_only_contacts:
            coverage_notes.insert(
                0,
                "No journalist bylines could be confidently verified; returning high-confidence outlet/story leads instead.",
            )
            supporting_articles = []
            for contact in story_only_contacts:
                supporting_articles.append({
                    "title": contact.get("previous_story_title", "") or "View story",
                    "source": contact.get("outlet", ""),
                    "url": contact.get("previous_story_url", ""),
                    "relevance_score": contact.get("topic_fit_score", 0),
                    "relevance_reason": contact.get("supporting_evidence", ""),
                })
            return {
                "issue": issue,
                "search_subject": search_subject,
                "topic_mode": topic_mode,
                "broad_topic": broad_topic,
                "coverage_desk": coverage_desk,
                "location": location,
                "media_types": media_types,
                "contacts": story_only_contacts,
                "pitch_timing": (
                    "Relevant outlet coverage was found, but reporter identities still need verification before pitching."
                ),
                "news_research": supporting_articles[:8],
                "requested_contacts": num_contacts,
                "returned_contacts": len(story_only_contacts),
                "coverage_by_media_type": coverage_by_media_type,
                "coverage_notes": coverage_notes,
                "result_quality": result_quality,
                "retrieval_layers_used": retrieval_layers_used,
                "layer1_candidate_count": layer1_candidate_count,
                "layer2_candidate_count": layer2_candidate_count,
                "layer3_candidate_count": layer3_candidate_count,
                "podcast_candidate_count": podcast_candidate_count,
                "validated_journalist_count": 0,
            }
        return {
            "issue": issue,
            "search_subject": search_subject,
            "topic_mode": topic_mode,
            "broad_topic": broad_topic,
            "coverage_desk": coverage_desk,
            "location": location,
            "media_types": media_types,
            "contacts": [],
            "pitch_timing": (
                "No journalist bylines could be extracted from recent articles on this topic. "
                "Try broadening the issue description, or manually search trade publications "
                "for journalists covering this beat."
            ),
            "news_research": articles[:10],
            "requested_contacts": num_contacts,
            "returned_contacts": 0,
            "coverage_by_media_type": {},
            "coverage_notes": ["No journalist contacts could be extracted from the retrieved article set."],
            "result_quality": "empty",
            "retrieval_layers_used": retrieval_layers_used,
            "layer1_candidate_count": layer1_candidate_count,
            "layer2_candidate_count": layer2_candidate_count,
            "layer3_candidate_count": layer3_candidate_count,
            "podcast_candidate_count": podcast_candidate_count,
            "validated_journalist_count": 0,
        }

    if not _contact_thresholds_met(
        [_fallback_contact_from_journalist(j) for j in trusted_journalists[:num_contacts]],
        media_types,
        requested_contacts=num_contacts,
    ) and provider.available():
        retrieval_layers_used.append("layer3")
        print("Step 3d: Running validated-seed expansion...", file=sys.stderr)
        layer3_articles = expand_from_validated_seeds(
            journalists,
            articles,
            search_subject,
            location,
            media_types,
            is_national,
            provider,
            broad_topic=broad_topic,
            coverage_desk=coverage_desk,
            topic_mode=topic_mode,
        )
        layer3_candidate_count = len(layer3_articles)
        if layer3_articles:
            articles = _dedupe_articles_by_story(articles + layer3_articles)
            expanded_with_bylines = extract_bylines(articles)
            journalists = group_by_journalist(expanded_with_bylines)
            journalists = diversify_journalists(journalists, max(num_contacts * 2, num_contacts), media_types, is_national, location)
            trusted_journalists = [
                journalist for journalist in journalists
                if journalist.get("identity_confidence") in {"high", "medium"}
            ]
            print(f"  Layer 3 expansion increased pool to {len(journalists)} journalists", file=sys.stderr)

    # Step 4: LLM enrichment
    prompt_journalists = journalists[: max(num_contacts * 2, 8)]
    print(f"Step 4: Enriching {len(prompt_journalists)} contacts with pitch angles...", file=sys.stderr)
    if prompt_journalists:
        enriched = enrich_contacts(prompt_journalists, search_subject, location, media_types, is_national, client)
    else:
        enriched = {"contacts": [], "pitch_timing": ""}

    # Normalize media_type values
    label_to_key = {}
    for key, label in MEDIA_TYPE_LABELS.items():
        label_to_key[key.lower()] = key
        label_to_key[label.lower()] = key

    contacts = enriched.get("contacts", [])
    journalist_lookup = {j["name"].lower(): j for j in journalists}
    for c in contacts:
        full_name = _contact_name_key(c.get("first_name", ""), c.get("last_name", ""))
        source_journalist = journalist_lookup.get(full_name)
        source_article = _find_supporting_article_for_contact(c, articles)
        if not source_article and source_journalist:
            source_article = (source_journalist or {}).get("best_article", {}) if source_journalist else {}
        outlet_name = c.get("outlet", "") or (source_journalist or {}).get("outlet", "") or source_article.get("source", "")
        raw_type = c.get("media_type", "").lower().strip()
        normalized_type = label_to_key.get(raw_type, raw_type)
        derived_type = (source_journalist or {}).get("guessed_media_type") or _guess_media_type(outlet_name)
        c["media_type"] = derived_type or normalized_type
        if not c.get("previous_story_title"):
            c["previous_story_title"] = source_article.get("title", "")
        if not c.get("previous_story_url") or not _is_story_url(c.get("previous_story_url", "")):
            c["previous_story_url"] = source_article.get("url", "")
        c["topic_fit_score"] = (source_journalist or {}).get("topic_fit_score", source_article.get("relevance_score", 0))
        c["supporting_evidence"] = (source_journalist or {}).get("supporting_evidence", source_article.get("relevance_reason", ""))
        c["relevance_confidence"] = (
            "high" if c.get("topic_fit_score", 0) >= 55 else
            "medium" if c.get("topic_fit_score", 0) >= 32 else
            "low"
        )
        if not c.get("why_now"):
            fallback_title = source_article.get("title", "").strip()
            c["why_now"] = (
                f"Recent relevant coverage from this reporter shows an active opening on the issue: {fallback_title}"
                if fallback_title else ""
            )
        if not c.get("pitch_angle"):
            c["pitch_angle"] = c.get("why_now", "") or "Reporter-specific angle needs manual refinement."
        if source_journalist and source_journalist.get("identity_confidence") in {"high", "medium"} and c.get("email") in {"[RESEARCH NEEDED]", "[VERIFY]"}:
            c["email"] = ""

    # Filter by requested media types
    if media_types and set(media_types) != set(MEDIA_TYPE_LABELS.keys()):
        contacts = [
            c for c in contacts
            if _media_type_matches(c.get("outlet", ""), c.get("media_type", ""), media_types)
        ]

    contacts = _sanitize_generated_contacts(contacts, journalist_lookup, articles, media_types, is_national, location)
    contacts = _merge_with_fallback_contacts(contacts, journalists, num_contacts, media_types)
    contacts = _merge_with_story_leads(contacts, articles, num_contacts, media_types, is_national, location)
    contacts = [
        contact for contact in contacts
        if _is_story_url((contact.get("previous_story_url") or "").strip())
    ]
    contacts = [contact for contact in contacts if _matches_contact_location(contact, location, is_national)]
    if podcast_contacts:
        contacts.extend(podcast_contacts)
        deduped_contacts = []
        seen_contact_keys = set()
        for contact in contacts:
            key = (
                (contact.get("media_type") or ""),
                (contact.get("matched_url") or contact.get("previous_story_url") or ""),
                (contact.get("host_name") or _contact_name_key(contact.get("first_name", ""), contact.get("last_name", ""))),
                (contact.get("outlet") or ""),
            )
            if key in seen_contact_keys:
                continue
            seen_contact_keys.add(key)
            deduped_contacts.append(contact)
        contacts = deduped_contacts
    contacts.sort(
        key=lambda c: (
            1 if c.get("contact_status") in {"story_lead", "show_only_verify_host"} else 0,
            0 if c.get("relevance_confidence") == "high" else 1,
            -(c.get("topic_fit_score", 0) or 0),
        )
    )
    contacts = contacts[:num_contacts]
    for contact in contacts:
        contact["confidence_label"] = _contact_confidence_label(contact)
        contact["why_now"] = _conservative_why_now(contact)
    coverage_by_media_type, coverage_notes, result_quality = _coverage_summary(contacts, num_contacts, media_types)

    supporting_articles = []
    seen_support_urls = set()
    for contact in contacts:
        url = (contact.get("previous_story_url") or "").strip()
        if not url or url in seen_support_urls:
            continue
        seen_support_urls.add(url)
        supporting_articles.append({
            "title": contact.get("previous_story_title", "") or "View story",
            "source": contact.get("outlet", ""),
            "url": url,
            "relevance_score": contact.get("topic_fit_score", 0),
            "relevance_reason": contact.get("supporting_evidence", ""),
        })

    return {
        "issue": issue,
        "search_subject": search_subject,
        "topic_mode": topic_mode,
        "broad_topic": broad_topic,
        "coverage_desk": coverage_desk,
        "location": location,
        "media_types": media_types,
        "contacts": contacts,
        "pitch_timing": enriched.get("pitch_timing", ""),
        "news_research": supporting_articles[:8] or [a for a in articles if a.get("relevance_score", 0) >= MIN_RELEVANCE_SCORE][:8],
        "story_analysis": story_analysis,
        "requested_contacts": num_contacts,
        "returned_contacts": len(contacts),
        "coverage_by_media_type": coverage_by_media_type,
        "coverage_notes": coverage_notes,
        "result_quality": result_quality,
        "retrieval_layers_used": retrieval_layers_used,
        "layer1_candidate_count": layer1_candidate_count,
        "layer2_candidate_count": layer2_candidate_count,
        "layer3_candidate_count": layer3_candidate_count,
        "podcast_candidate_count": podcast_candidate_count,
        "validated_journalist_count": len(trusted_journalists),
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
    sections.append("| Name | Confidence | Outlet | Role | Media Type | Email | Pitch Angle |")
    sections.append("|------|------------|--------|------|------------|-------|-------------|")
    for c in result["contacts"]:
        name = (
            f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
            or c.get("host_name", "")
            or ("Host to verify" if c.get("media_type") == "podcast" else "")
        )
        confidence = c.get("confidence_label") or _contact_confidence_label(c)
        outlet = c.get("outlet", "")
        role = c.get("role", "")
        mt = MEDIA_TYPE_LABELS.get(c.get("media_type", ""), c.get("media_type", ""))
        email = c.get("email", "") or "—"
        angle = c.get("pitch_angle", "")[:80]
        sections.append(
            f"| {_escape_markdown_cell(name)} | {_escape_markdown_cell(confidence)} | "
            f"{_escape_markdown_cell(outlet)} | {_escape_markdown_cell(role)} | "
            f"{_escape_markdown_cell(mt)} | {_escape_markdown_cell(email)} | "
            f"{_escape_markdown_cell(angle)} |"
        )

    sections.append("")
    why_now_lines = []
    for c in result["contacts"][:10]:
        name = (
            f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
            or c.get("host_name", "")
            or c.get("outlet", "Unknown contact")
        )
        why_now = c.get("why_now", "")
        if why_now:
            why_now_lines.append(f"- **{_escape_markdown_cell(name)}:** {_escape_markdown_cell(why_now)}")
    if why_now_lines:
        sections.append("## Why Now")
        sections.extend(why_now_lines)
        sections.append("")
    sections.append("---")
    sections.append("*CONFIDENTIAL — FOR INTERNAL USE ONLY*")

    return "\n".join(sections)
