import io
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict
from urllib.parse import parse_qs, unquote, urlparse

import requests

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


MIN_TEXT_CHARS = 250
MAX_PAGES = 18


class IRS990PDFParser:
    """
    Best-effort fallback parser for IRS 990 PDFs when XML is unavailable.
    Extracts a conservative set of trustworthy fields plus narrative excerpts.
    """

    def __init__(self, pdf_url: str):
        self.pdf_url = pdf_url
        self.text = ""
        self.error = ""
        self.parse_status = ""
        self.source_url = pdf_url
        self.extraction_method = ""

    @staticmethod
    def resolve_pdf_urls(pdf_url: str) -> list[str]:
        if not pdf_url:
            return []

        urls: list[str] = []
        parsed = urlparse(pdf_url)
        if "projects.propublica.org" in parsed.netloc and parsed.path.endswith("/download-filing"):
            encoded_path = parse_qs(parsed.query).get("path", [""])[0]
            filename = Path(unquote(encoded_path)).name
            if filename:
                urls.append(f"https://apps.irs.gov/pub/epostcard/cor/{filename}")

        urls.append(pdf_url)

        deduped: list[str] = []
        seen = set()
        for candidate in urls:
            if candidate and candidate not in seen:
                seen.add(candidate)
                deduped.append(candidate)
        return deduped

    def fetch_and_parse(self) -> bool:
        if not self.pdf_url:
            self.parse_status = "unavailable"
            self.error = "missing pdf_url"
            return False

        pdf_bytes = self._fetch_pdf_bytes()
        if not pdf_bytes:
            self.parse_status = "fetch_failed"
            return False

        native_text = self._normalize_text(self._extract_text_pypdf(pdf_bytes))
        if self._text_is_usable(native_text):
            self.text = native_text
            self.extraction_method = "pypdf"
            self.parse_status = "parsed"
            return True

        pdftotext_text = self._normalize_text(self._extract_text_pdftotext(pdf_bytes))
        if self._text_is_usable(pdftotext_text):
            self.text = pdftotext_text
            self.extraction_method = "pdftotext"
            self.parse_status = "parsed"
            return True

        ocr_text = self._normalize_text(self._extract_text_ocr(pdf_bytes))
        if self._text_is_usable(ocr_text):
            self.text = ocr_text
            self.extraction_method = "ocr"
            self.parse_status = "parsed"
            return True

        if self.parse_status == "ocr_failed":
            return False

        self.parse_status = "native_text_empty"
        if not self.error:
            self.error = "native PDF extraction yielded too little usable filing text"
        return False

    def _fetch_pdf_bytes(self) -> bytes:
        last_error = "unable to fetch PDF"
        for candidate_url in self.resolve_pdf_urls(self.pdf_url):
            try:
                response = requests.get(
                    candidate_url,
                    timeout=20,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        "Referer": "https://projects.propublica.org/nonprofits/",
                        "Accept": "application/pdf,*/*",
                    },
                )
                response.raise_for_status()
                self.source_url = candidate_url
                return response.content
            except Exception as exc:  # pragma: no cover
                last_error = f"{candidate_url}: {exc}"

        self.error = last_error
        return b""

    def _extract_text_pypdf(self, pdf_bytes: bytes) -> str:
        if PdfReader is None:
            return ""

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            pages = []
            for page in reader.pages[:MAX_PAGES]:
                try:
                    text = page.extract_text(extraction_mode="layout") or ""
                except TypeError:
                    text = page.extract_text() or ""
                pages.append(text)
            return "\n".join(pages)
        except Exception:
            return ""

    def _extract_text_pdftotext(self, pdf_bytes: bytes) -> str:
        if shutil.which("pdftotext") is None:
            return ""

        temp_dir = self._make_tempdir()
        try:
            pdf_path = os.path.join(temp_dir, "filing.pdf")
            with open(pdf_path, "wb") as handle:
                handle.write(pdf_bytes)

            result = subprocess.run(
                ["pdftotext", "-layout", pdf_path, "-"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if result.returncode != 0:
                return ""
            return result.stdout or ""
        except Exception:
            return ""
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _extract_text_ocr(self, pdf_bytes: bytes) -> str:
        if shutil.which("pdftoppm") is None or shutil.which("tesseract") is None:
            self.parse_status = "ocr_failed"
            self.error = "OCR dependencies unavailable (requires pdftoppm and tesseract)"
            return ""

        temp_dir = self._make_tempdir()
        try:
            pdf_path = os.path.join(temp_dir, "filing.pdf")
            with open(pdf_path, "wb") as handle:
                handle.write(pdf_bytes)

            image_prefix = os.path.join(temp_dir, "page")
            render = subprocess.run(
                ["pdftoppm", "-f", "1", "-l", str(MAX_PAGES), "-png", pdf_path, image_prefix],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if render.returncode != 0:
                self.parse_status = "ocr_failed"
                self.error = (render.stderr or "pdftoppm failed").strip()
                return ""

            pages = sorted(str(path) for path in Path(temp_dir).glob("page-*.png"))
            if not pages:
                self.parse_status = "ocr_failed"
                self.error = "OCR rendering produced no page images"
                return ""

            ocr_chunks: list[str] = []
            for page_path in pages:
                result = subprocess.run(
                    ["tesseract", page_path, "stdout", "--psm", "6"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                if result.returncode != 0 and not (result.stdout or "").strip():
                    self.parse_status = "ocr_failed"
                    self.error = (result.stderr or "tesseract failed").strip()
                    return ""
                if result.stdout:
                    ocr_chunks.append(result.stdout)

            if not "".join(ocr_chunks).strip():
                self.parse_status = "ocr_failed"
                self.error = "OCR returned no text"
                return ""

            return "\n".join(ocr_chunks)
        except Exception as exc:
            self.parse_status = "ocr_failed"
            self.error = str(exc)
            return ""
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def _make_tempdir() -> str:
        try:
            base_dir = os.getcwd()
        except Exception:  # pragma: no cover
            base_dir = None
        return tempfile.mkdtemp(prefix=".irs990_pdf_", dir=base_dir)

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""

        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\x0c", "\n").replace("\u00a0", " ")
        text = text.replace("|", " ").replace("‘", "'").replace("’", "'")
        text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = []
        for line in text.splitlines():
            cleaned = re.sub(r"\s+", " ", line).strip()
            if re.fullmatch(r"[_\-. ]{3,}", cleaned or ""):
                continue
            if cleaned.startswith("Form 990 (") and len(cleaned) < 40:
                continue
            lines.append(cleaned)
        text = "\n".join(line for line in lines if line)
        return text.strip()

    @staticmethod
    def _text_is_usable(text: str) -> bool:
        if not text:
            return False

        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) < MIN_TEXT_CHARS:
            return False

        alpha_chars = sum(1 for ch in compact if ch.isalpha())
        if alpha_chars < 120:
            return False

        form_markers = [
            "form 990",
            "return of organization exempt from income tax",
            "part i",
            "part iii",
            "total revenue",
        ]
        lowered = compact.lower()
        return sum(1 for marker in form_markers if marker in lowered) >= 2

    def _search_money(self, patterns: list[str], min_digits: int = 1) -> str:
        for pattern in patterns:
            match = re.search(pattern, self.text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                cleaned = self._clean_value(match.group(1))
                if len(re.sub(r"[^0-9]", "", cleaned)) >= min_digits:
                    return cleaned
        return "0"

    @staticmethod
    def _clean_value(value: str) -> str:
        value = value or ""
        value = value.replace("(", "-").replace(")", "")
        cleaned = re.sub(r"[^0-9\-]", "", value)
        cleaned = re.sub(r"-{2,}", "-", cleaned)
        if cleaned in ("", "-"):
            return "0"
        return cleaned

    def _extract_after_anchor(self, anchor_patterns: list[str], max_chars: int = 420) -> str:
        end_markers = [
            r"\nPart [IVX]+\b",
            r"\nForm 990\b",
            r"\n[A-Z]\s+[A-Z][a-z]",
            r"\n\d{1,2}[a-z]?\s",
        ]
        for pattern in anchor_patterns:
            match = re.search(pattern, self.text, flags=re.IGNORECASE | re.DOTALL)
            if not match:
                continue

            tail = self.text[match.end(): match.end() + 1400]
            stop = len(tail)
            for end_pattern in end_markers:
                end_match = re.search(end_pattern, tail, flags=re.IGNORECASE)
                if end_match:
                    stop = min(stop, end_match.start())
            snippet = tail[:stop]
            snippet = re.sub(r"\s+", " ", snippet).strip(" .:-")
            if snippet.lower().startswith("check if schedule o"):
                continue
            if len(snippet) >= 40:
                return snippet[:max_chars]
        return ""

    def extract_profile(self) -> Dict[str, str]:
        website = ""
        website_match = re.search(
            r"(?:Website|WWW|Web site)[\s:]+(https?://\S+|www\.\S+|\S+\.(?:org|com|net|edu))",
            self.text,
            flags=re.IGNORECASE,
        )
        if website_match:
            website = website_match.group(1).strip().rstrip(").,;")

        mission_excerpt = self._extract_after_anchor([
            r"mission\s+or\s+most\s+significant\s+activities[:\s]*",
            r"primary\s+exempt\s+purpose[:\s]*",
            r"describe\s+the\s+organization'?s\s+mission[:\s]*",
        ])
        program_excerpt = self._extract_after_anchor([
            r"program\s+service\s+accomplishments[:\s]*",
            r"describe\s+the\s+organization'?s\s+program\s+service\s+accomplishments[:\s]*",
            r"4a\s+code[:\s].{0,120}",
        ])

        schedule_hits = []
        for schedule, marker in [
            ("Schedule C", "schedule c"),
            ("Schedule I", "schedule i"),
            ("Schedule J", "schedule j"),
            ("Schedule R", "schedule r"),
            ("Schedule F", "schedule f"),
        ]:
            if marker in self.text.lower():
                schedule_hits.append(schedule)

        return {
            "website": website,
            "formation_year": "",
            "state_of_domicile": "",
            "total_employees": self._search_money([
                r"total number of employees[^\n\d\-]{0,40}([0-9,()\-]+)",
                r"employees[^\n\d\-]{0,20}([0-9,()\-]+)",
            ]),
            "total_volunteers": self._search_money([
                r"total number of volunteers[^\n\d\-]{0,40}([0-9,()\-]+)",
                r"volunteers[^\n\d\-]{0,20}([0-9,()\-]+)",
            ]),
            "total_revenue": self._search_money([
                r"total revenue[^\n\d\-]{0,60}([0-9,()\-]+)",
                r"cytotalrevenueamt[^\n\d\-]{0,20}([0-9,()\-]+)",
            ], min_digits=4),
            "total_expenses": self._search_money([
                r"total expenses[^\n\d\-]{0,60}([0-9,()\-]+)",
                r"cytotalexpenseamt[^\n\d\-]{0,20}([0-9,()\-]+)",
            ], min_digits=4),
            "net_assets": self._search_money([
                r"net assets or fund balances[^\n\d\-]{0,80}([0-9,()\-]+)",
                r"net assets[^\n\d\-]{0,40}([0-9,()\-]+)",
                r"netassetsorfundbalanceseoyamt[^\n\d\-]{0,20}([0-9,()\-]+)",
            ], min_digits=4),
            "mission_excerpt": mission_excerpt,
            "program_excerpt": program_excerpt,
            "schedule_mentions": ", ".join(schedule_hits),
        }

    def narrative_blocks(self) -> str:
        excerpts = []
        profile = self.extract_profile()
        if profile.get("mission_excerpt"):
            excerpts.append(f"Mission / purpose excerpt: {profile['mission_excerpt']}")
        if profile.get("program_excerpt"):
            excerpts.append(f"Program service excerpt: {profile['program_excerpt']}")
        if profile.get("schedule_mentions"):
            excerpts.append(f"Schedules referenced in PDF text: {profile['schedule_mentions']}")
        return "\n".join(excerpts)
