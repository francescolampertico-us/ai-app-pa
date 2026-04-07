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
import time
import hashlib
import base64
import re
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

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_bills(self, query: str, state: str = "US", year: int = None, max_results: int = None) -> list[dict]:
        """
        Search for bills matching a query.

        Args:
            query: Search keywords.
            state: Two-letter state code or 'US' for federal. Use 'ALL' for all.
            year: Legislative session year (default: current year from API).

        Returns:
            List of bill result dicts with normalized fields.
        """
        params = {"op": "getSearch", "query": query}
        if state and state.upper() != "ALL":
            params["state"] = state.upper()
        if year:
            params["year"] = year

        data = self._api_call(params)
        search_list = data.get("searchresult", {})

        # LegiScan returns results as numbered keys + a "summary" key
        results = []
        for key, val in search_list.items():
            if key == "summary":
                continue
            if isinstance(val, dict) and "bill_id" in val:
                results.append(self._normalize_search_result(val))

        results.sort(key=lambda r: r.get("relevance", 0), reverse=True)
        if max_results:
            results = results[:max_results]
        return results

    def _normalize_search_result(self, raw: dict) -> dict:
        """Normalize a LegiScan search result into a clean dict."""
        return {
            "bill_id": raw.get("bill_id"),
            "number": raw.get("bill_number", ""),
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

        return {
            "bill_id": raw.get("bill_id"),
            "number": raw.get("bill_number", ""),
            "title": raw.get("title", ""),
            "description": raw.get("description", ""),
            "state": raw.get("state", ""),
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
            return self._extract_pdf_text(decoded)
        elif "html" in mime:
            return self._strip_html(decoded.decode("utf-8", errors="replace"))
        else:
            return decoded.decode("utf-8", errors="replace")

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

    def _strip_html(self, html: str) -> str:
        """Basic HTML tag removal for bill text."""
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

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
    def state_list() -> list[str]:
        """Return list of valid state codes for LegiScan."""
        return [
            "US", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
            "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
            "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
            "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC", "PR",
        ]
