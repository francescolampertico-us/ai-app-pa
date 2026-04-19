"""
Typed internal contracts for the Background Memo Generator.

BackgroundMemoResult  — the validated output of a single generate_memo() call.
BackgroundMemoJobResult — the full result_data shape stored in the job record.

Both are Pydantic models so field names and types are enforced at runtime.
Pydantic is available because this code runs inside the FastAPI process.
"""
from typing import Optional

from pydantic import BaseModel, Field


# ── Generator-level contract ──────────────────────────────────────────────────

class MemoSubsection(BaseModel):
    heading: Optional[str] = None
    paragraphs: list[str] = Field(default_factory=list)


class MemoSection(BaseModel):
    heading: str
    subsections: list[MemoSubsection] = Field(default_factory=list)


class MemoLink(BaseModel):
    label: str
    url: str


class BackgroundMemoResult(BaseModel):
    """Validated output from generate_memo(). This is the primary internal contract."""
    subject: str
    sections_requested: list[str] = Field(default_factory=list)
    overview: str = ""
    fast_facts: list[str] = Field(default_factory=list)
    sections: list[MemoSection] = Field(default_factory=list)
    links: list[MemoLink] = Field(default_factory=list)


# ── Job-level contract ────────────────────────────────────────────────────────

class BackgroundMemoJobResult(BaseModel):
    """
    Full result_data stored in the job record after a completed run.

    Memo content fields are flat (not nested under a 'result' key) so the
    frontend can access job.result_data.overview directly.
    """
    # Identity
    subject: str
    memo_date: str
    sections_requested: list[str] = Field(default_factory=list)
    # Primary memo content
    overview: str = ""
    fast_facts: list[str] = Field(default_factory=list)
    sections: list[MemoSection] = Field(default_factory=list)
    links: list[MemoLink] = Field(default_factory=list)
    # Export artifact (secondary)
    markdown: str = ""
    # Research context (supplementary — not primary output)
    research_md: str = ""
    disclosure_md: str = ""
    disclosure_csv_data: dict = Field(default_factory=dict)


# Force Pydantic to resolve all forward references using this module's globals.
# Required because _load_module (importlib) does not register the module in
# sys.modules, so Pydantic's normal forward-ref resolution finds an empty namespace.
BackgroundMemoResult.model_rebuild()
BackgroundMemoJobResult.model_rebuild()
