from __future__ import annotations

import datetime
import json
import mimetypes
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter()

# SQLite file lives next to main.py so it's outside the source tree but inside the backend dir.
DB_PATH = Path(__file__).resolve().parents[2] / "jobs.db"
JOBS_OUTPUT_ROOT = Path(__file__).resolve().parents[2] / "jobs_output"


def _conn() -> sqlite3.Connection:
    """Open a per-call connection with WAL mode for safe concurrent writes from background threads."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          TEXT PRIMARY KEY,
                status      TEXT NOT NULL DEFAULT 'pending',
                progress    INTEGER DEFAULT 0,
                message     TEXT DEFAULT '',
                created_at  TEXT NOT NULL,
                result_data TEXT,
                artifacts   TEXT NOT NULL DEFAULT '[]'
            )
        """)


_init_db()


# ── Pydantic models ──────────────────────────────────────────────────────────

class ArtifactStatus(BaseModel):
    name: str
    path: str
    size_bytes: int
    media_type: str
    url: str


class JobStatus(BaseModel):
    id: str
    status: str
    progress: Optional[int] = 0
    message: Optional[str] = ""
    download_url: Optional[str] = None
    created_at: str
    result_data: Optional[dict] = None
    artifacts: list[ArtifactStatus] = []


# ── Internal helpers ─────────────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["artifacts"] = json.loads(d.get("artifacts") or "[]")
    d["result_data"] = json.loads(d["result_data"]) if d.get("result_data") else None
    return d


def _get_job(job_id: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_dict(row) if row else None


def _parse_iso_datetime(value: str | None) -> datetime.datetime | None:
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value)
    except ValueError:
        return None


def _recover_result_data(output_dir: Path) -> dict | None:
    json_candidates = sorted(
        [p for p in output_dir.glob("*.json") if p.is_file()],
        key=lambda p: (p.name.endswith("_data.json"), p.stat().st_size),
        reverse=True,
    )
    for candidate in json_candidates:
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return None


def _reconcile_job_from_output(job_id: str, job: dict) -> dict:
    if not job or job.get("status") not in {"pending"}:
        return job
    output_dir = JOBS_OUTPUT_ROOT / job_id
    if not output_dir.exists():
        return job

    files = sorted([p for p in output_dir.iterdir() if p.is_file()])
    if not files:
        return job

    created_at = _parse_iso_datetime(job.get("created_at"))
    latest_mtime = max(datetime.datetime.fromtimestamp(p.stat().st_mtime) for p in files)
    now = datetime.datetime.now()
    if created_at and (now - created_at).total_seconds() < 15:
        return job
    if (now - latest_mtime).total_seconds() < 10:
        return job

    artifacts = [build_artifact(str(p), job_id, idx) for idx, p in enumerate(files)]
    result_data = job.get("result_data") or _recover_result_data(output_dir)
    message = job.get("message") or "Job completed."
    if not message.lower().startswith("job completed"):
        message = f"{message} Recovered completed outputs from disk."

    update_job(
        job_id,
        status="completed",
        progress=100,
        message=message,
        artifacts=artifacts,
        result_data=result_data,
    )
    refreshed = _get_job(job_id)
    return refreshed or job


# ── Public API (same signatures as before) ───────────────────────────────────

def create_job() -> str:
    job_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO jobs (id, status, progress, message, created_at, artifacts) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, "pending", 0, "Job initialized", datetime.datetime.now().isoformat(), "[]"),
        )
    return job_id


def update_job(
    job_id: str,
    status: str | None = None,
    progress: int | None = None,
    message: str | None = None,
    artifacts: list[dict] | None = None,
    result_data: dict | None = None,
):
    sets: list[str] = []
    params: list[Any] = []
    if status is not None:
        sets.append("status = ?"); params.append(status)
    if progress is not None:
        sets.append("progress = ?"); params.append(progress)
    if message is not None:
        sets.append("message = ?"); params.append(message)
    if artifacts is not None:
        sets.append("artifacts = ?"); params.append(json.dumps(artifacts))
    if result_data is not None:
        sets.append("result_data = ?"); params.append(json.dumps(result_data))
    if not sets:
        return
    params.append(job_id)
    with _conn() as conn:
        conn.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE id = ?", params)


def build_artifact(path: str, job_id: str, index: int) -> dict[str, Any]:
    file_path = Path(path)
    media_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    return {
        "name": file_path.name,
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        "media_type": media_type,
        "url": f"/api/jobs/{job_id}/artifacts/{index}",
    }


def set_job_artifacts(job_id: str, files: list[str]):
    existing = []
    for file_path in files:
        if not file_path:
            continue
        path_obj = Path(file_path)
        if path_obj.exists() and path_obj.is_file():
            existing.append(str(path_obj))
    artifacts = [build_artifact(path, job_id, idx) for idx, path in enumerate(existing)]
    update_job(job_id, artifacts=artifacts)


def append_job_artifacts(job_id: str, files: list[str]):
    job = _get_job(job_id)
    if not job:
        return
    current_paths = [artifact["path"] for artifact in job.get("artifacts", [])]
    current_paths.extend(file for file in files if file and file not in current_paths)
    set_job_artifacts(job_id, current_paths)


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job = _reconcile_job_from_output(job_id, job)

    artifacts = job.get("artifacts", [])
    download_url = artifacts[0]["url"] if artifacts else None

    return JobStatus(
        id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        message=job.get("message", ""),
        download_url=download_url,
        created_at=job["created_at"],
        result_data=job.get("result_data"),
        artifacts=artifacts,
    )


@router.get("/{job_id}/artifacts/{artifact_index}")
async def download_job_artifact(job_id: str, artifact_index: int):
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    artifacts = job.get("artifacts", [])
    if artifact_index < 0 or artifact_index >= len(artifacts):
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact = artifacts[artifact_index]
    path = artifact["path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=500, detail="Artifact file is missing on the server")

    return FileResponse(
        path=path,
        filename=artifact["name"],
        media_type=artifact.get("media_type") or "application/octet-stream",
    )
