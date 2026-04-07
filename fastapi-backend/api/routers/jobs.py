from __future__ import annotations

import datetime
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter()

JOB_STORE: Dict[str, dict] = {}


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


def create_job() -> str:
    job_id = str(uuid.uuid4())
    JOB_STORE[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Job initialized",
        "created_at": datetime.datetime.now().isoformat(),
        "artifacts": [],
        "result_data": None,
    }
    return job_id


def update_job(
    job_id: str,
    status: str | None = None,
    progress: int | None = None,
    message: str | None = None,
    artifacts: list[dict] | None = None,
    result_data: dict | None = None,
):
    job = JOB_STORE.get(job_id)
    if not job:
        return
    if status is not None:
        job["status"] = status
    if progress is not None:
        job["progress"] = progress
    if message is not None:
        job["message"] = message
    if artifacts is not None:
        job["artifacts"] = artifacts
    if result_data is not None:
        job["result_data"] = result_data


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
    job = JOB_STORE.get(job_id)
    if not job:
        return
    current_paths = [artifact["path"] for artifact in job.get("artifacts", [])]
    current_paths.extend(file for file in files if file and file not in current_paths)
    set_job_artifacts(job_id, current_paths)


@router.get("/{job_id}/status", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    download_url = None
    artifacts = job.get("artifacts", [])
    if artifacts:
        download_url = artifacts[0]["url"]

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
    job = JOB_STORE.get(job_id)
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
