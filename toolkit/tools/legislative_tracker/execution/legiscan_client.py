"""
LegiScan API Client
====================
Handles all communication with the LegiScan API, including search, bill detail,
bill text retrieval, and local caching.

API docs: https://legiscan.com/legiscan
Free tier: 30,000 requests/month.
"""

from __future__ import annotations

import os
import io
import json
import hashlib
import base64
import re
import html
from pathlib import Path
from datetime import datetime, timedelta

import requests

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


LEGISCAN_BASE_URL = "https://api.legiscan.com/"
CACHE_TTL_HOURS = 24
CHANGE_AGENT_BASE_URL = "https://runpod-proxy-956966668285.us-central1.run.app/v1/"


class LegiScanClient:
    """Client for the LegiScan API with local JSON caching."""

    def __init__(self, api_key: str = None, cache_dir: str = None):
        self.api_key = api_key or os.getenv("LEGISCAN_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "LEGISCAN_API_KEY is required. Get a free key at https://legiscan.com/legiscan"
            )
        self.cache_dir = Path(cache_dir or ".cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core API call with caching
    # ------------------------------------------------------------------

    def _cache_key(self, params: dict) -> str:
        """Generate a deterministic cache filename from request params."""
        raw = json.dumps(params, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest() + ".json"

    def _read_cache(self, key: str) -> dict | None:
        path = self.cache_dir / key
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
            if datetime.now() - cached_at > timedelta(hours=CACHE_TTL_HOURS):
                return None
            return data.get("response")
        except (json.JSONDecodeError, ValueError):
            return None

    def _write_cache(self, key: str, response: dict):
        path = self.cache_dir / key
        data = {"_cached_at": datetime.now().isoformat(), "response": response}
        path.write_text(json.dumps(data, indent=2))

    def _api_call(self, params: dict) -> dict:
        """Make a cached API call to LegiScan."""
        params["key"] = self.api_key
        cache_key = self._cache_key(params)

        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        resp = requests.get(LEGISCAN_BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "ERROR":
            raise RuntimeError(f"LegiScan API error: {data.get('alert', {}).get('message', 'Unknown')}")

        self._write_cache(cache_key, data)
        return data

    def _api_call_nocache(self, params: dict) -> dict:
        """Make a fresh (non-cached) API call to LegiScan."""
        params["key"] = self.api_key
        resp = requests.get(LEGISCAN_BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "ERROR":
            raise RuntimeError(f"LegiScan API error: {data.get('alert', {}).get('message', 'Unknown')}")
        return data

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_bills(self, query: str, state: str = "US", year: int = None,
                     max_results: int = None, title_only: bool = False) -> list[dict]:
        """
        Search for bills matching a query.

        Args:
            query:       Search keywords (or quoted phrase for LegiScan phrase search).
            state:       Two-letter state code or 'US' for federal. Use 'ALL' for all.
            year:        Legislative session year (default: current year from API).
            max_results: Cap on returned results (applied after any filtering).
            title_only:  If True, post-filter to bills whose title contains ALL query
                         words. Narrows results to title matches only, since LegiScan
                         searches full bill text and subjects by default.

        Returns:
            List of bill result dicts with normalized fields.
        """
        params = {"op": "getSearch", "query": query}
        if state and state.upper() != "ALL":
            params["state"] = state.upper()
        if year:
            params["year"] = year

        # For title-only searches, bypass cache so we always get fresh results
        # (cached broad searches for the same query would miss title-matching bills
        # that fell outside LegiScan's top-50 relevance ranking).
        if title_only:
            data = self._api_call_nocache(params)
        else:
            data = self._api_call(params)

        search_list = data.get("searchresult", {})

        results = []
        for key, val in search_list.items():
            if key == "summary":
                continue
            if isinstance(val, dict) and "bill_id" in val:
                results.append(self._normalize_search_result(val))

        results.sort(key=lambda r: r.get("relevance", 0), reverse=True)

        if year:
            year_str = str(year)
            results = [r for r in results if (r.get("last_action_date") or "").startswith(year_str)
                       or (r.get("last_action_date") or "") == ""]

        if title_only:
            phrase = query.strip().lower()
            results = [r for r in results if phrase in r.get("title", "").lower()]
        elif len(results) > 5:
            results = self._llm_filter_results(query, results)

        if max_results:
            results = results[:max_results]
        return results

    def _keyword_title_filter(self, query: str, results: list[dict]) -> list[dict]:
        """Simple fallback: at least one significant query word must appear in the bill title."""
        stop = {"the", "and", "for", "with", "from", "that", "this", "are", "was",
                "act", "of", "to", "in", "a", "an", "its", "not", "has", "have"}
        words = [w.lower() for w in re.split(r"\W+", query.strip())
                 if len(w) > 3 and w.lower() not in stop]
        if not words:
            return results
        return [r for r in results if any(w in r.get("title", "").lower() for w in words)]

    def _llm_filter_results(self, query: str, results: list[dict]) -> list[dict]:
        """Rerank broad search results by LLM relevance without dropping source results."""
        if not results:
            return results
        llm_ranked = None
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=os.getenv("CHANGE_AGENT_API_KEY", ""),
                base_url=CHANGE_AGENT_BASE_URL,
            )
            entries = "\n".join(
                f"{r['bill_id']}|{r['number']}|{r['title']}" for r in results
            )
            prompt = (
                f"Query: \"{query}\"\n\n"
                f"The following bills were returned by a legislative database for this query. "
                f"Many are off-topic because the database searches full bill text, not just titles.\n\n"
                f"Bills (id|number|title):\n{entries}\n\n"
                f"Task: Return a JSON array of bill_ids ordered from most relevant to least relevant. "
                f"A bill is relevant only if its TITLE clearly relates to \"{query}\". "
                f"Exclude bills where the connection is only through a single coincidental word. "
                f"Example: if the query is \"housing affordability\", exclude conservation, "
                f"heritage, homeland security, or civil rights bills even if they mention "
                f"\"land\" or \"community\". Put the strongest title matches first. "
                f"Return ONLY a JSON array of integers, e.g. [123456, 789012]. "
                f"If none are relevant, return []"
            )
            resp = client.chat.completions.create(
                model="ChangeAgent",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            raw = (resp.choices[0].message.content or "").strip()
            # Extract the JSON array — handle code fences and surrounding prose
            match = re.search(r"\[[\s\d,]*\]", raw, re.DOTALL)
            if match:
                ranked_ids = [int(item) for item in json.loads(match.group())]
                if ranked_ids:
                    rank_map = {bill_id: idx for idx, bill_id in enumerate(ranked_ids)}
                    llm_ranked = sorted(
                        results,
                        key=lambda item: (rank_map.get(item["bill_id"], len(results) + 1000), -item.get("relevance", 0)),
                    )
        except Exception:
            pass

        if llm_ranked:
            return llm_ranked

        # LLM rerank failed — fall back to keyword title prioritization without dropping results
        keyword_filtered = self._keyword_title_filter(query, results)
        if keyword_filtered:
            keyword_ids = {item["bill_id"] for item in keyword_filtered}
            keyword_ranked = [item for item in results if item["bill_id"] in keyword_ids]
            keyword_ranked.extend(item for item in results if item["bill_id"] not in keyword_ids)
            return keyword_ranked

        return results

    def _normalize_search_result(self, raw: dict) -> dict:
        """Normalize a LegiScan search result into a clean dict."""
        state = raw.get("state", "")
        number = self.format_bill_number(raw.get("bill_number", ""), state)
        return {
            "bill_id": raw.get("bill_id"),
            "number": number,
            "title": raw.get("title", ""),
            "state": raw.get("state", ""),
            "status": self._status_label(raw.get("status", 0)),
            "status_code": raw.get("status", 0),
            "last_action": raw.get("last_action", ""),
            "last_action_date": raw.get("last_action_date", ""),
            "url": raw.get("url", ""),
            "relevance": raw.get("relevance", 0),
        }

    # ------------------------------------------------------------------
    # Bill detail
    # ------------------------------------------------------------------

    def get_bill(self, bill_id: int) -> dict:
        """
        Get full bill detail including sponsors, history, votes.

        Args:
            bill_id: LegiScan bill ID.

        Returns:
            Normalized bill detail dict.
        """
        data = self._api_call({"op": "getBill", "id": bill_id})
        bill = data.get("bill", {})
        return self._normalize_bill(bill)

    def _normalize_bill(self, raw: dict) -> dict:
        """Normalize a full bill record."""
        sponsors = []
        for s in raw.get("sponsors", []):
            sponsors.append({
                "name": s.get("name", ""),
                "party": s.get("party", ""),
                "role": s.get("role", ""),
                "district": s.get("district", ""),
            })

        history = []
        for h in raw.get("history", []):
            history.append({
                "date": h.get("date", ""),
                "action": h.get("action", ""),
                "chamber": h.get("chamber", ""),
            })

        votes = []
        for v in raw.get("votes", []):
            votes.append({
                "date": v.get("date", ""),
                "description": v.get("desc", ""),
                "yea": v.get("yea", 0),
                "nay": v.get("nay", 0),
                "absent": v.get("absent", 0),
                "roll_call_id": v.get("roll_call_id"),
            })

        subjects = [s.get("subject_name", "") for s in raw.get("subjects", [])]

        texts = []
        for t in raw.get("texts", []):
            texts.append({
                "doc_id": t.get("doc_id"),
                "date": t.get("date", ""),
                "type": t.get("type", ""),
                "mime": t.get("mime", ""),
                "url": t.get("url", ""),
            })

        state = raw.get("state", "")
        number = self.format_bill_number(raw.get("bill_number", ""), state)
        return {
            "bill_id": raw.get("bill_id"),
            "number": number,
            "title": raw.get("title", ""),
            "description": raw.get("description", ""),
            "state": state,
            "state_id": raw.get("state_id"),
            "session": raw.get("session", {}).get("session_name", ""),
            "status": self._status_label(raw.get("status", 0)),
            "status_code": raw.get("status", 0),
            "status_date": raw.get("status_date", ""),
            "url": raw.get("url", ""),
            "state_url": raw.get("state_link", ""),
            "sponsors": sponsors,
            "history": history,
            "votes": votes,
            "subjects": subjects,
            "texts": texts,
            "last_action": raw.get("last_action", ""),
            "last_action_date": raw.get("last_action_date", ""),
        }

    # ------------------------------------------------------------------
    # Bill text
    # ------------------------------------------------------------------

    def get_bill_text(self, doc_id: int) -> str:
        """
        Retrieve and decode the full text of a bill document.

        Handles HTML, PDF, and plain text MIME types from LegiScan.

        Args:
            doc_id: LegiScan document ID (from bill detail texts array).

        Returns:
            Decoded plain text of the bill.
        """
        data = self._api_call({"op": "getBillText", "id": doc_id})
        text_data = data.get("text", {})

        encoded = text_data.get("doc", "")
        if not encoded:
            return ""

        decoded = base64.b64decode(encoded)
        mime = text_data.get("mime", "").lower()

        if "pdf" in mime:
            text = self._extract_pdf_text(decoded)
        elif "html" in mime:
            text = self._strip_html(decoded.decode("utf-8", errors="replace"))
        else:
            text = decoded.decode("utf-8", errors="replace")

        return self._normalize_bill_text(text)

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes using pypdf."""
        if not HAS_PYPDF:
            return "[PDF bill text could not be extracted — pypdf not installed]"

        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)

        if not pages:
            return "[PDF bill text could not be extracted — no readable text in PDF]"

        return "\n\n".join(pages)

    def _normalize_bill_text(self, text: str) -> str:
        """Normalize decoded bill text so downstream extraction sees cleaner structure."""
        if not text:
            return ""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\u00a0", " ").replace("\ufeff", "").replace("\u200b", "")
        text = re.sub(r"([A-Za-z])-\n([A-Za-z])", r"\1\2", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _strip_html(self, html: str) -> str:
        """
        Extract readable plain text from HTML bill text, preserving structure.

        Block-level elements are converted to newlines so section breaks and
        paragraph boundaries survive — the LLM extraction pass relies on this
        structure to identify individual provisions.
        """
        # Remove non-content blocks entirely
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Convert block-level and line-break elements to newlines before stripping
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(
            r"</?(p|div|li|tr|td|th|h[1-6]|section|article|blockquote|pre)[^>]*>",
            "\n",
            text,
            flags=re.IGNORECASE,
        )

        # Strip all remaining tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        text = html.unescape(text)

        # Normalise each line's internal whitespace, then reassemble
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

        # Collapse runs of more than two consecutive blank lines
        result: list[str] = []
        blank_run = 0
        for line in lines:
            if line:
                blank_run = 0
                result.append(line)
            else:
                blank_run += 1
                if blank_run <= 2:
                    result.append("")

        return "\n".join(result).strip()

    @staticmethod
    def score_bill_text(text: str) -> float:
        """
        Heuristic score for bill text usefulness.

        Higher scores reflect richer statutory structure and fewer decoding artifacts.
        Used to choose the best available LegiScan text version across multiple docs.
        """
        if not text:
            return -1.0
        lowered = text.lower()
        if lowered.startswith("[pdf bill text could not be extracted"):
            return -1.0

        score = min(len(text) / 1500.0, 60.0)
        section_markers = len(re.findall(r"(?im)^(?:sec\.|section|title)\b", text))
        score += min(section_markers * 8.0, 48.0)

        if "table of contents" in lowered:
            score -= 6.0
        if lowered.count("\nnone") >= 2 or lowered.count(" none ") >= 4:
            score -= 18.0

        replacement_chars = text.count("\ufffd")
        score -= min(replacement_chars * 0.5, 20.0)

        avg_line_len = (sum(len(line) for line in text.splitlines()) / max(len(text.splitlines()), 1))
        if avg_line_len < 18:
            score -= 8.0

        return score

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _status_label(code: int) -> str:
        """Convert LegiScan numeric status to human-readable label."""
        labels = {
            0: "N/A",
            1: "Introduced",
            2: "Engrossed",
            3: "Enrolled",
            4: "Passed",
            5: "Vetoed",
            6: "Failed",
        }
        return labels.get(code, f"Unknown ({code})")

    @staticmethod
    def format_bill_number(number: str, state: str = "") -> str:
        """Format a raw LegiScan bill number into standard citation style."""
        if not number:
            return number
        if state.upper() != "US":
            return number
        n = number.strip()
        patterns = [
            (r"^SCONRES(\d+)$", "S.Con.Res. "),
            (r"^HCONRES(\d+)$", "H.Con.Res. "),
            (r"^SJRES(\d+)$",   "S.J.Res. "),
            (r"^HJRES(\d+)$",   "H.J.Res. "),
            (r"^SJR(\d+)$",     "S.J.Res. "),
            (r"^HJR(\d+)$",     "H.J.Res. "),
            (r"^SR(\d+)$",      "S.Res. "),
            (r"^HR(\d+)$",      "H.Res. "),
            (r"^SB(\d+)$",      "S. "),
            (r"^HB(\d+)$",      "H.R. "),
        ]
        for pattern, prefix in patterns:
            m = re.match(pattern, n, re.IGNORECASE)
            if m:
                return f"{prefix}{m.group(1)}"
        return number

    @staticmethod
    def format_jurisdiction(state: str) -> str:
        """Return a human-friendly jurisdiction label."""
        if (state or "").upper() == "US":
            return "Federal (US)"
        return state

    @staticmethod
    def state_list() -> list[str]:
        """Return list of valid state codes for LegiScan."""
        return [
            "US", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
            "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
            "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
            "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC", "PR",
        ]
