"""
Watchlist Manager
==================
Persists a local JSON watchlist of tracked bills.
Supports add, remove, list, and refresh (re-fetch status for all tracked bills).
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


class WatchlistManager:
    """Manages a persistent bill watchlist stored as a JSON file."""

    def __init__(self, watchlist_path: str = None):
        self.path = Path(watchlist_path or ".cache/watchlist.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        """Load watchlist from disk."""
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except (json.JSONDecodeError, ValueError):
                return {"bills": {}, "last_refreshed": None}
        return {"bills": {}, "last_refreshed": None}

    def _save(self):
        """Persist watchlist to disk."""
        self.path.write_text(json.dumps(self._data, indent=2))

    def add(self, bill_id: int, bill_info: dict) -> bool:
        """
        Add a bill to the watchlist.

        Args:
            bill_id: LegiScan bill ID.
            bill_info: Dict with at minimum: number, title, state, status.

        Returns:
            True if newly added, False if already tracked.
        """
        key = str(bill_id)
        if key in self._data["bills"]:
            return False

        self._data["bills"][key] = {
            "bill_id": bill_id,
            "number": bill_info.get("number", ""),
            "title": bill_info.get("title", ""),
            "state": bill_info.get("state", ""),
            "status": bill_info.get("status", ""),
            "last_action": bill_info.get("last_action", ""),
            "last_action_date": bill_info.get("last_action_date", ""),
            "url": bill_info.get("url", ""),
            "added_at": datetime.now().isoformat(),
            "last_checked": datetime.now().isoformat(),
            "status_history": [
                {
                    "status": bill_info.get("status", ""),
                    "last_action": bill_info.get("last_action", ""),
                    "checked_at": datetime.now().isoformat(),
                }
            ],
        }
        self._save()
        return True

    def remove(self, bill_id: int) -> bool:
        """Remove a bill from the watchlist. Returns True if found and removed."""
        key = str(bill_id)
        if key in self._data["bills"]:
            del self._data["bills"][key]
            self._save()
            return True
        return False

    def list_bills(self) -> list[dict]:
        """Return all tracked bills as a list of dicts."""
        return list(self._data["bills"].values())

    def get(self, bill_id: int) -> dict | None:
        """Get a single tracked bill, or None if not tracked."""
        return self._data["bills"].get(str(bill_id))

    def update_status(self, bill_id: int, new_info: dict) -> dict | None:
        """
        Update a tracked bill's status after a refresh.

        Args:
            bill_id: LegiScan bill ID.
            new_info: Fresh bill data from API.

        Returns:
            Dict with 'changed' (bool) and 'old_status'/'new_status' if changed.
        """
        key = str(bill_id)
        entry = self._data["bills"].get(key)
        if not entry:
            return None

        old_status = entry["status"]
        old_action = entry["last_action"]
        new_status = new_info.get("status", old_status)
        new_action = new_info.get("last_action", old_action)

        changed = old_status != new_status or old_action != new_action

        entry["status"] = new_status
        entry["last_action"] = new_action
        entry["last_action_date"] = new_info.get("last_action_date", entry.get("last_action_date", ""))
        entry["last_checked"] = datetime.now().isoformat()

        if changed:
            entry["status_history"].append({
                "status": new_status,
                "last_action": new_action,
                "checked_at": datetime.now().isoformat(),
            })

        self._save()
        return {
            "changed": changed,
            "old_status": old_status,
            "new_status": new_status,
            "old_action": old_action,
            "new_action": new_action,
        }

    def refresh_all(self, legiscan_client) -> list[dict]:
        """
        Re-fetch status for all tracked bills and report changes.

        Args:
            legiscan_client: An instance of LegiScanClient.

        Returns:
            List of dicts with bill_id, number, changed, and status details.
        """
        results = []
        for key, entry in self._data["bills"].items():
            bill_id = entry["bill_id"]
            try:
                fresh = legiscan_client.get_bill(bill_id)
                update = self.update_status(bill_id, fresh)
                results.append({
                    "bill_id": bill_id,
                    "number": entry["number"],
                    "title": entry["title"],
                    "state": entry["state"],
                    **update,
                })
            except Exception as e:
                results.append({
                    "bill_id": bill_id,
                    "number": entry["number"],
                    "title": entry["title"],
                    "state": entry["state"],
                    "changed": False,
                    "error": str(e),
                })

        self._data["last_refreshed"] = datetime.now().isoformat()
        self._save()
        return results
