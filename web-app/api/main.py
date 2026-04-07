"""
Strategitect — FastAPI Backend
Wraps toolkit tools as async jobs with polling + file download.
"""
import sys
import csv as csv_mod
import io
import uuid
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ── Paths ──────────────────────────────────────────────────────────────────
HERE = Path(__file__).parent
TOOLKIT = HERE.parent.parent / "toolkit"
TOOLS_DIR = TOOLKIT / "tools"
JOBS_OUTPUT = HERE / "jobs_output"
JOBS_OUTPUT.mkdir(exist_ok=True)

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Strategitect API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory job store ────────────────────────────────────────────────────
JOBS: dict[str, dict] = {}


def make_job(job_id: str):
    JOBS[job_id] = {
        "id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Queued",
        "result_data": None,
        "download_url": None,
        "error": None,
    }
    return JOBS[job_id]


def update_job(job_id, **kwargs):
    JOBS[job_id].update(kwargs)


def find_output_file(output_dir: Path, extensions: list[str]) -> Optional[Path]:
    for ext in extensions:
        matches = list(output_dir.glob(f"**/*.{ext}"))
        if matches:
            return max(matches, key=lambda p: p.stat().st_mtime)
    return None


def run_tool_subprocess(job_id: str, cmd: list[str], output_dir: Path,
                        output_exts: list[str], stages: list[str]):
    """Run a tool as a subprocess and update job status from stdout."""
    update_job(job_id, status="processing", progress=5, message=stages[0])
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(TOOLKIT),
        )
        stage_size = 90 // max(len(stages), 1)
        current_stage = 0
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            # Advance stage on key phrases
            for i, stage in enumerate(stages[current_stage:], current_stage):
                kws = stage.lower().split()[:2]
                if any(k in line.lower() for k in kws):
                    current_stage = i
                    progress = 5 + stage_size * (i + 1)
                    update_job(job_id, progress=min(progress, 90), message=stage)
                    break

        proc.wait()

        if proc.returncode != 0:
            update_job(job_id, status="failed", progress=100,
                       message="Tool execution failed — check server logs.")
            return

        # Find output file
        output_file = find_output_file(output_dir, output_exts)
        if output_file:
            dest = JOBS_OUTPUT / f"{job_id}{output_file.suffix}"
            shutil.copy2(output_file, dest)
            update_job(
                job_id,
                status="completed",
                progress=100,
                message="Complete",
                download_url=f"/api/jobs/{job_id}/download",
            )
        else:
            update_job(job_id, status="completed", progress=100,
                       message="Complete — no downloadable artifact produced.")

    except Exception as e:
        update_job(job_id, status="failed", progress=100, message=str(e))


# ── Status endpoint ────────────────────────────────────────────────────────
@app.get("/api/jobs/{job_id}/status")
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    return job


# ── Download endpoint ──────────────────────────────────────────────────────
@app.get("/api/jobs/{job_id}/download")
def job_download(job_id: str):
    job = JOBS.get(job_id)
    if not job or job["status"] != "completed":
        return JSONResponse({"error": "Not ready"}, status_code=404)
    matches = list(JOBS_OUTPUT.glob(f"{job_id}.*"))
    if not matches:
        return JSONResponse({"error": "File not found"}, status_code=404)
    f = matches[0]
    return FileResponse(str(f), filename=f.name)


# ══════════════════════════════════════════════════════════════════════════
# TOOL ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════

# ── Hearing Memo ───────────────────────────────────────────────────────────
@app.post("/api/tools/execute/hearing_memo_generator")
async def run_hearing_memo(
    background_tasks: BackgroundTasks,
    youtube_url: str = Form(""),
    memo_from: str = Form(""),
    memo_date: str = Form(""),
    subject_override: str = Form(""),
    hearing_title: str = Form(""),
    hearing_date: str = Form(""),
    hearing_time: str = Form(""),
    committee: str = Form(""),
    confidentiality: str = Form(""),
    file: Optional[UploadFile] = File(None),
):
    job_id = str(uuid.uuid4())
    make_job(job_id)

    output_dir = JOBS_OUTPUT / job_id
    output_dir.mkdir()
    upload_path = None

    if file and file.filename:
        upload_path = output_dir / file.filename
        content = await file.read()
        upload_path.write_bytes(content)

    if not upload_path and not youtube_url:
        update_job(job_id, status="failed", message="No input provided (file or YouTube URL required)")
        return {"job_id": job_id}

    script = str(TOOLS_DIR / "hearing_memo_generator" / "execution" / "run.py")
    cmd = [sys.executable, script]

    if upload_path:
        cmd += ["--input", str(upload_path)]
    elif youtube_url:
        cmd += ["--input", youtube_url]

    cmd += ["--output", str(output_dir / "memo.docx")]
    if memo_from:    cmd += ["--from", memo_from]
    if memo_date:    cmd += ["--memo-date", memo_date]
    if subject_override: cmd += ["--subject", subject_override]
    if hearing_title:    cmd += ["--hearing-title", hearing_title]
    if hearing_date:     cmd += ["--hearing-date", hearing_date]
    if hearing_time:     cmd += ["--hearing-time", hearing_time]
    if committee:        cmd += ["--committee", committee]
    if confidentiality:  cmd += ["--confidentiality-footer", confidentiality]
    cmd += ["--json-output", str(output_dir / "result.json")]

    stages = ["Parsing transcript", "Extracting content", "Composing memo", "Verifying output"]
    t = threading.Thread(target=run_tool_subprocess,
                         args=(job_id, cmd, output_dir, ["docx"], stages), daemon=True)
    t.start()
    return {"job_id": job_id}


# ── Media Clips ────────────────────────────────────────────────────────────
@app.post("/api/tools/execute/media_clips")
async def run_media_clips(
    background_tasks: BackgroundTasks,
    topic: str = Form(...),
    queries: str = Form(...),
    period: str = Form("24h"),
    output_dir_param: str = Form(""),
):
    job_id = str(uuid.uuid4())
    make_job(job_id)
    output_dir = JOBS_OUTPUT / job_id
    output_dir.mkdir()

    script = str(TOOLS_DIR / "media_clips" / "execution" / "run.py")
    cmd = [
        sys.executable, script,
        "--topic", topic,
        "--queries", queries,
        "--period", period or "24h",
        "--output-dir", str(output_dir),
        "--no-email",
    ]
    stages = ["Fetching articles", "Filtering duplicates", "Generating clips", "Formatting report"]
    t = threading.Thread(target=run_tool_subprocess,
                         args=(job_id, cmd, output_dir, ["docx"], stages), daemon=True)
    t.start()
    return {"job_id": job_id}


# ── Legislative Tracker ────────────────────────────────────────────────────
@app.post("/api/tools/execute/legislative_tracker")
async def run_legislative_tracker(
    query: str = Form(...),
    state: str = Form("US"),
    year: str = Form(""),
):
    job_id = str(uuid.uuid4())
    make_job(job_id)
    output_dir = JOBS_OUTPUT / job_id
    output_dir.mkdir()

    script = str(TOOLS_DIR / "legislative_tracker" / "execution" / "run.py")
    cmd = [sys.executable, script, "--query", query, "--out", str(output_dir)]
    if state: cmd += ["--state", state]
    if year:  cmd += ["--year", year]

    stages = ["Querying LegiScan", "Filtering results", "Summarizing bills", "Exporting report"]
    t = threading.Thread(target=run_tool_subprocess,
                         args=(job_id, cmd, output_dir, ["docx", "csv", "md"], stages), daemon=True)
    t.start()
    return {"job_id": job_id}


# ── Stakeholder Map ────────────────────────────────────────────────────────
@app.post("/api/tools/execute/stakeholder_map_builder")
async def run_stakeholder_map(
    policy_issue: str = Form(...),
    scope: str = Form("federal"),
    include_types: str = Form(""),
):
    job_id = str(uuid.uuid4())
    make_job(job_id)
    output_dir = JOBS_OUTPUT / job_id
    output_dir.mkdir()

    script = str(TOOLS_DIR / "stakeholder_map_builder" / "execution" / "run.py")
    cmd = [sys.executable, script, "--policy-issue", policy_issue,
           "--scope", scope or "federal", "--out", str(output_dir)]
    if include_types: cmd += ["--include-types", include_types]

    stages = ["Discovering actors", "Classifying stakeholders", "Building network", "Generating report"]
    t = threading.Thread(target=run_tool_subprocess,
                         args=(job_id, cmd, output_dir, ["docx", "html"], stages), daemon=True)
    t.start()
    return {"job_id": job_id}


# ── Influence Disclosure Tracker ───────────────────────────────────────────
def _run_disclosure_subprocess(job_id: str, cmd: list, output_dir: Path):
    """Run disclosure tracker, capture CSV + report, store in job result_data."""
    stages = ["Querying LDA", "Querying FARA", "Normalizing records", "Generating report"]
    stage_size = 90 // len(stages)
    update_job(job_id, status="processing", progress=5, message=stages[0])
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, cwd=str(TOOLS_DIR / "influence_disclosure_tracker" / "execution"))
        current_stage = 0
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            for i, stage in enumerate(stages[current_stage:], current_stage):
                if any(k in line.lower() for k in stage.lower().split()[:2]):
                    current_stage = i
                    update_job(job_id, progress=min(5 + stage_size * (i + 1), 90), message=stage)
                    break
        proc.wait()

        if proc.returncode != 0:
            update_job(job_id, status="failed", progress=100, message="Tool execution failed.")
            return

        # Read report.md
        report_text = ""
        report_files = list(output_dir.rglob("report.md"))
        if report_files:
            report_text = report_files[0].read_text(encoding="utf-8", errors="replace")

        # Read all CSVs
        csv_data = {}
        for csv_file in output_dir.rglob("*.csv"):
            try:
                reader = csv_mod.DictReader(io.StringIO(csv_file.read_text(encoding="utf-8", errors="replace")))
                csv_data[csv_file.stem] = list(reader)
            except Exception:
                pass

        update_job(job_id, status="completed", progress=100, message="Complete",
                   result_data={"report": report_text, "csv_data": csv_data})
    except Exception as e:
        update_job(job_id, status="failed", progress=100, message=str(e))


@app.post("/api/tools/execute/influence_disclosure_tracker")
async def run_influence_tracker(
    entities: str = Form(...),
    search_field: str = Form("both"),
    filing_years: str = Form(""),
    all_years: str = Form("false"),
    quarters: str = Form("Q1,Q2,Q3,Q4"),
    from_date: str = Form(""),
    to_date: str = Form(""),
    sources: str = Form("lda,irs990"),
    mode: str = Form("basic"),
    max_results: str = Form("500"),
    fuzzy_threshold: str = Form("85"),
):
    job_id = str(uuid.uuid4())
    make_job(job_id)
    output_dir = JOBS_OUTPUT / job_id
    output_dir.mkdir()

    script = str(TOOLS_DIR / "influence_disclosure_tracker" / "execution" / "run.py")
    cmd = [sys.executable, script,
           "--entities", entities,
           "--search-field", search_field or "both",
           "--out", str(output_dir),
           "--mode", mode or "basic",
           "--max-results", str(max_results or 500),
           "--fuzzy-threshold", str(fuzzy_threshold or 85),
           "--sources", sources or "lda,irs990",
           "--filing-periods", quarters or "Q1,Q2,Q3,Q4",
    ]
    # all_years = omit --filing-years entirely (tool searches all)
    if all_years.lower() != "true" and filing_years:
        cmd += ["--filing-years", filing_years]
    if from_date: cmd += ["--from", from_date]
    if to_date:   cmd += ["--to", to_date]

    t = threading.Thread(target=_run_disclosure_subprocess,
                         args=(job_id, cmd, output_dir), daemon=True)
    t.start()
    return {"job_id": job_id}


# ── Messaging Matrix ───────────────────────────────────────────────────────
@app.post("/api/tools/execute/messaging_matrix")
async def run_messaging_matrix(
    position: str = Form(...),
    core_messages: str = Form(""),
    facts: str = Form(""),
    context: str = Form(""),
    organization: str = Form(""),
    target_audience: str = Form(""),
):
    job_id = str(uuid.uuid4())
    make_job(job_id)
    output_dir = JOBS_OUTPUT / job_id
    output_dir.mkdir()

    script = str(TOOLS_DIR / "messaging_matrix" / "execution" / "run.py")
    cmd = [sys.executable, script, "--position", position, "--out", str(output_dir)]
    if core_messages:   cmd += ["--core-messages", core_messages]
    if facts:           cmd += ["--facts", facts]
    if context:         cmd += ["--context", context]
    if organization:    cmd += ["--organization", organization]
    if target_audience: cmd += ["--audience", target_audience]

    stages = ["Building message house", "Generating talking points", "Writing press statement", "Formatting matrix"]
    t = threading.Thread(target=run_tool_subprocess,
                         args=(job_id, cmd, output_dir, ["docx"], stages), daemon=True)
    t.start()
    return {"job_id": job_id}


# ── Background Memo ────────────────────────────────────────────────────────
@app.post("/api/tools/execute/background_memo_generator")
async def run_background_memo(
    subject: str = Form(...),
    memo_date: str = Form(""),
    sections_text: str = Form(""),
    sections: str = Form(""),
    context: str = Form(""),
    file: Optional[UploadFile] = File(None),
):
    job_id = str(uuid.uuid4())
    make_job(job_id)
    output_dir = JOBS_OUTPUT / job_id
    output_dir.mkdir()

    upload_path = None
    if file and file.filename:
        upload_path = output_dir / file.filename
        content = await file.read()
        upload_path.write_bytes(content)

    # sections_text is newline-separated (from textarea); sections is comma-separated (legacy)
    raw = sections_text or sections or "Overview,Key Facts,Recent Activity,Stakeholders"
    if "\n" in raw:
        section_list = [s.strip() for s in raw.splitlines() if s.strip()]
    else:
        section_list = [s.strip() for s in raw.split(",") if s.strip()]

    script = str(TOOLS_DIR / "background_memo_generator" / "execution" / "run.py")
    cmd = [sys.executable, script, "--subject", subject,
           "--sections"] + section_list + ["--out", str(output_dir / "memo.docx")]
    if memo_date: cmd += ["--date", memo_date]
    if context:   cmd += ["--context", context]

    stages = ["Researching subject", "Querying disclosures", "Generating content", "Exporting memo"]
    t = threading.Thread(target=run_tool_subprocess,
                         args=(job_id, cmd, output_dir, ["docx"], stages), daemon=True)
    t.start()
    return {"job_id": job_id}


# ── Stakeholder Briefing ───────────────────────────────────────────────────
@app.post("/api/tools/execute/stakeholder_briefing")
async def run_stakeholder_briefing(
    stakeholder: str = Form(...),
    client: str = Form(""),
    policy_issue: str = Form(""),
    meeting_date: str = Form(""),
    meeting_purpose: str = Form(""),
):
    job_id = str(uuid.uuid4())
    make_job(job_id)
    output_dir = JOBS_OUTPUT / job_id
    output_dir.mkdir()

    script = str(TOOLS_DIR / "stakeholder_briefing" / "execution" / "run.py")
    cmd = [sys.executable, script, "--stakeholder", stakeholder,
           "--out", str(output_dir / "briefing.docx")]
    if client:          cmd += ["--client", client]
    if policy_issue:    cmd += ["--policy-issue", policy_issue]
    if meeting_date:    cmd += ["--meeting-date", meeting_date]
    if meeting_purpose: cmd += ["--meeting-purpose", meeting_purpose]

    stages = ["Profiling stakeholder", "Researching positions", "Generating briefing", "Exporting"]
    t = threading.Thread(target=run_tool_subprocess,
                         args=(job_id, cmd, output_dir, ["docx"], stages), daemon=True)
    t.start()
    return {"job_id": job_id}


# ── Media List Builder ─────────────────────────────────────────────────────
@app.post("/api/tools/execute/media_list_builder")
async def run_media_list_builder(
    topic: str = Form(...),
    beat: str = Form(""),
    region: str = Form(""),
    outlet_types: str = Form(""),
):
    job_id = str(uuid.uuid4())
    make_job(job_id)
    output_dir = JOBS_OUTPUT / job_id
    output_dir.mkdir()

    script = str(TOOLS_DIR / "media_list_builder" / "execution" / "run.py")
    cmd = [sys.executable, script, "--topic", topic, "--out", str(output_dir)]
    if beat:          cmd += ["--beat", beat]
    if region:        cmd += ["--region", region]
    if outlet_types:  cmd += ["--outlet-types", outlet_types]

    stages = ["Identifying journalists", "Filtering by beat", "Scoring relevance", "Exporting list"]
    t = threading.Thread(target=run_tool_subprocess,
                         args=(job_id, cmd, output_dir, ["csv", "docx"], stages), daemon=True)
    t.start()
    return {"job_id": job_id}


# ── Remy Chat ─────────────────────────────────────────────────────────────
@app.post("/api/remy/chat")
async def remy_chat(request: Request):
    body = await request.json()
    message = body.get("message", "")
    history = body.get("history", [])
    model   = body.get("model", "gpt-4o-mini")

    app_dir = str(TOOLKIT / "app")
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    try:
        from remy_assistant import chat_with_remy  # type: ignore
        response = chat_with_remy(
            user_message=message,
            history=history,
            uploaded_files=[],
            model=model,
        )
        return response
    except Exception as e:
        return JSONResponse({"text": f"Remy error: {e}", "tool_events": []}, status_code=500)


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "toolkit": str(TOOLKIT)}
