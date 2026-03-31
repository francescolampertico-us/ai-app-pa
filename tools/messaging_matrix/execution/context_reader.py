"""
Context Reader
===============
Shared utility for reading PDF, DOCX, and TXT files into plain text.
Used by both the Streamlit page (document upload) and the style analyzer.
"""

import os
from pathlib import Path


def read_file(filepath: str) -> str:
    """Read a single file and return its text content.

    Supports: .pdf, .docx, .txt (and other plain text extensions).
    """
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return _read_pdf(path)
    elif ext == ".docx":
        return _read_docx(path)
    else:
        return _read_text(path)


def read_uploaded_file(uploaded_file) -> str:
    """Read a Streamlit UploadedFile object and return its text content."""
    import tempfile

    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        return read_file(tmp_path)
    finally:
        os.unlink(tmp_path)


def read_directory(dirpath: str, recursive: bool = False) -> list[dict]:
    """Read all supported files in a directory.

    Returns list of {"path": str, "name": str, "text": str}.
    """
    supported = {".pdf", ".docx", ".txt", ".md"}
    path = Path(dirpath)
    if not path.exists():
        return []

    pattern = "**/*" if recursive else "*"
    results = []
    for f in sorted(path.glob(pattern)):
        if f.is_file() and f.suffix.lower() in supported:
            try:
                text = read_file(str(f))
                if text.strip():
                    results.append({
                        "path": str(f),
                        "name": f.name,
                        "text": text,
                    })
            except Exception:
                pass  # Skip unreadable files silently

    return results


def _read_pdf(path: Path) -> str:
    """Extract text from a PDF using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def _read_docx(path: Path) -> str:
    """Extract text from a DOCX using python-docx."""
    from docx import Document

    doc = Document(str(path))
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _read_text(path: Path) -> str:
    """Read a plain text file."""
    return path.read_text(encoding="utf-8", errors="ignore")
