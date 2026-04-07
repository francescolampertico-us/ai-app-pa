"""
Shared PDF brand module — PA AI Toolkit.

Uses ReportLab to produce branded PDFs with the cinematic design aesthetic
from the literature review: dark covers with violet glow, clean body pages.

Fonts: Poppins (display) + Inter (body) — TTFs from brand-toolkit/assets/fonts/.

Usage:
    from pdf_brand import build_branded_pdf, heading, body, bullet, callout, meta_block, data_table
"""
from __future__ import annotations
from pathlib import Path

# ─── Locate brand.toml and font assets ───────────────────────────────────────
_HERE         = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[3]
_BRAND_TOML   = _PROJECT_ROOT / "brand-toolkit" / "brand.toml"
_FONTS_DIR    = _PROJECT_ROOT / "brand-toolkit" / "assets" / "fonts"

# ─── Load brand.toml ─────────────────────────────────────────────────────────
_cfg: dict = {}
if _BRAND_TOML.exists():
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            tomllib = None  # type: ignore
    if tomllib is not None:
        try:
            with open(_BRAND_TOML, "rb") as f:
                _cfg = tomllib.load(f)
        except Exception:
            pass


def _c(section: str, key: str, default: str) -> str:
    parts = section.split(".")
    d: dict | str = _cfg
    for p in parts:
        d = d.get(p, {}) if isinstance(d, dict) else {}
    return d.get(key, default) if isinstance(d, dict) else default  # type: ignore


# ─── Brand values ─────────────────────────────────────────────────────────────
COMPANY_NAME = _c("company", "name",        "Strategitect")
SLOGAN       = _c("company", "slogan",      "Architecture for Public Affairs Strategy")
FOOTER_TEXT  = _c("company", "footer_text", "Strategitect — Confidential")
COVER_BADGE  = _c("company", "cover_badge", "CONFIDENTIAL")

_col  = _cfg.get("colors", {})
_zinc = _col.get("zinc", {})
_comp = _cfg.get("components", {})
_call = _comp.get("callout", {})
_tbl  = _comp.get("table", {})

HEX_PRIMARY = _col.get("primary",  "6D28D9")
HEX_ACCENT  = _col.get("accent",   "A78BFA")
HEX_FUCHSIA = _col.get("fuchsia",  "E879F9")
HEX_VOID    = _col.get("void",     "09090B")
HEX_MIST    = _col.get("mist",     "F5F3FF")
HEX_WARNING = _col.get("warning",  "FBBF24")
HEX_SUCCESS = _col.get("success",  "4ADE80")

HEX_Z50  = _zinc.get("50",  "FAFAFA")
HEX_Z100 = _zinc.get("100", "F4F4F5")
HEX_Z200 = _zinc.get("200", "E4E4E7")
HEX_Z400 = _zinc.get("400", "A1A1AA")
HEX_Z500 = _zinc.get("500", "71717A")
HEX_Z600 = _zinc.get("600", "52525B")
HEX_Z700 = _zinc.get("700", "3F3F46")
HEX_Z900 = _zinc.get("900", "18181B")

# Component tokens
HEX_CALL_INFO_BORDER = _call.get("info_border",    "A78BFA")
HEX_CALL_INFO_BG     = _call.get("info_bg",        "F5F3FF")
HEX_CALL_WARN_BORDER = _call.get("warning_border", "FBBF24")
HEX_CALL_WARN_BG     = _call.get("warning_bg",     "FFFBEB")
HEX_CALL_OK_BORDER   = _call.get("success_border", "4ADE80")
HEX_CALL_OK_BG       = _call.get("success_bg",     "F0FDF4")
HEX_TBL_HEADER_BG    = _tbl.get("header_bg",       "6D28D9")
HEX_TBL_ALT_BG       = _tbl.get("row_alt_bg",      "F5F3FF")

# ─── ReportLab ────────────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Flowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

PAGE_W, PAGE_H = A4
MARGIN_L = 28 * mm
MARGIN_R = 28 * mm
MARGIN_T = 22 * mm
MARGIN_B = 22 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


def _h(hex6: str) -> HexColor:
    return HexColor(f"#{hex6.lstrip('#')}")


C_PRIMARY  = _h(HEX_PRIMARY)
C_ACCENT   = _h(HEX_ACCENT)
C_FUCHSIA  = _h(HEX_FUCHSIA)
C_VOID     = _h(HEX_VOID)
C_MIST     = _h(HEX_MIST)
C_WARNING  = _h(HEX_WARNING)
C_SUCCESS  = _h(HEX_SUCCESS)
C_Z100     = _h(HEX_Z100)
C_Z200     = _h(HEX_Z200)
C_Z400     = _h(HEX_Z400)
C_Z500     = _h(HEX_Z500)
C_Z600     = _h(HEX_Z600)
C_Z700     = _h(HEX_Z700)
C_Z900     = _h(HEX_Z900)

# ─── Font registration ────────────────────────────────────────────────────────
_FONT_FILES = {
    "Poppins-Bold":       "Poppins-Bold.ttf",
    "Poppins-SemiBold":   "Poppins-SemiBold.ttf",
    "Poppins-Regular":    "Poppins-Regular.ttf",
    "Poppins-BoldItalic": "Poppins-BoldItalic.ttf",
    "Inter-Regular":      "Inter-Regular.ttf",
    "Inter-Medium":       "Inter-Medium.ttf",
    "Inter-SemiBold":     "Inter-SemiBold.ttf",
    "Inter-Bold":         "Inter-Bold.ttf",
}

for _name, _file in _FONT_FILES.items():
    _path = _FONTS_DIR / _file
    if _path.exists():
        pdfmetrics.registerFont(TTFont(_name, str(_path)))

registerFontFamily("Poppins",
    normal="Poppins-Regular", bold="Poppins-Bold",
    italic="Poppins-BoldItalic", boldItalic="Poppins-BoldItalic")
registerFontFamily("Inter",
    normal="Inter-Regular", bold="Inter-Bold",
    italic="Inter-Regular", boldItalic="Inter-Bold")

F_DISPLAY  = "Poppins-Bold"
F_SEMI     = "Poppins-SemiBold"
F_BODY     = "Inter-Regular"
F_BOLD     = "Inter-Bold"
F_MED      = "Inter-Medium"

# ─── Paragraph styles ─────────────────────────────────────────────────────────
S_BODY = ParagraphStyle("Body",
    fontName=F_BODY, fontSize=9.5, textColor=C_Z600,
    leading=15, spaceAfter=4 * mm)

S_BODY_TIGHT = ParagraphStyle("BodyTight",
    fontName=F_BODY, fontSize=9.5, textColor=C_Z600,
    leading=14, spaceAfter=2 * mm)

S_HEADING1 = ParagraphStyle("H1",
    fontName=F_DISPLAY, fontSize=15, textColor=C_VOID,
    leading=19, spaceBefore=10 * mm, spaceAfter=2 * mm)

S_HEADING2 = ParagraphStyle("H2",
    fontName=F_SEMI, fontSize=11, textColor=C_VOID,
    leading=15, spaceBefore=6 * mm, spaceAfter=2 * mm)

S_LABEL = ParagraphStyle("Label",
    fontName=F_BOLD, fontSize=7.5, textColor=C_PRIMARY,
    leading=10, spaceBefore=10 * mm, spaceAfter=1 * mm,
    letterSpacing=0.8)

S_BULLET = ParagraphStyle("Bullet",
    fontName=F_BODY, fontSize=9.5, textColor=C_Z600,
    leading=14, leftIndent=5 * mm, spaceAfter=2 * mm)

S_META_LABEL = ParagraphStyle("MetaLabel",
    fontName=F_BOLD, fontSize=8, textColor=C_Z600, leading=12)

S_META_VALUE = ParagraphStyle("MetaValue",
    fontName=F_BODY, fontSize=9, textColor=C_Z700, leading=13)

S_CALLOUT = ParagraphStyle("Callout",
    fontName=F_BODY, fontSize=9, textColor=C_Z700, leading=14)


# ─── Custom flowables ─────────────────────────────────────────────────────────

class _VRule(Flowable):
    """Short violet horizontal rule — sits under a section label."""
    def __init__(self, width=24 * mm, color=None, thickness=1.5):
        Flowable.__init__(self)
        self._w = width
        self._color = color or C_PRIMARY
        self._t = thickness

    def wrap(self, *_):
        return (CONTENT_W, 2 * mm)

    def draw(self):
        self.canv.setStrokeColor(self._color)
        self.canv.setLineWidth(self._t)
        self.canv.line(0, 1, self._w, 1)


class _HRule(Flowable):
    def __init__(self, color=None, thickness=0.3):
        Flowable.__init__(self)
        self._color = color or C_Z200
        self._t = thickness

    def wrap(self, *_):
        return (CONTENT_W, 1 * mm)

    def draw(self):
        self.canv.setStrokeColor(self._color)
        self.canv.setLineWidth(self._t)
        self.canv.line(0, 0, CONTENT_W, 0)


# ─── Cover page drawing ───────────────────────────────────────────────────────

def _draw_cover(c, _doc, title: str, subtitle: str, date_str: str):
    w, h = PAGE_W, PAGE_H

    # Void black background
    c.setFillColor(C_VOID)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Primary violet glow — upper right
    cfg_g1 = _cfg.get("cover", {}).get("glow_primary", {})
    gr, gg, gb = cfg_g1.get("r", 0.43), cfg_g1.get("g", 0.16), cfg_g1.get("b", 0.87)
    for i in range(45):
        t = i / 44
        alpha = 0.12 * (1 - t)
        radius = 140 * mm * (0.4 + 0.6 * (1 - t))
        c.setFillColor(Color(gr, gg, gb, alpha))
        c.circle(w * 0.68, h * 0.62, radius, fill=1, stroke=0)

    # Secondary lighter glow — lower left
    cfg_g2 = _cfg.get("cover", {}).get("glow_secondary", {})
    gr2, gg2, gb2 = cfg_g2.get("r", 0.66), cfg_g2.get("g", 0.55), cfg_g2.get("b", 0.98)
    for i in range(30):
        t = i / 29
        alpha = 0.07 * (1 - t)
        radius = 90 * mm * (0.4 + 0.6 * (1 - t))
        c.setFillColor(Color(gr2, gg2, gb2, alpha))
        c.circle(w * 0.28, h * 0.33, radius, fill=1, stroke=0)

    # Badge pill
    pill_w = 54 * mm
    pill_h = 7 * mm
    pill_x = w / 2 - pill_w / 2
    pill_y = h * 0.66
    c.setFillColor(Color(1, 1, 1, 0.07))
    c.setStrokeColor(Color(1, 1, 1, 0.14))
    c.setLineWidth(0.5)
    c.roundRect(pill_x, pill_y, pill_w, pill_h, pill_h / 2, fill=1, stroke=1)
    c.setFillColor(C_ACCENT)
    c.setFont(F_MED, 7)
    c.drawCentredString(w / 2, pill_y + 2.3 * mm, COVER_BADGE)

    # Title
    c.setFillColor(white)
    c.setFont(F_DISPLAY, 30)
    c.drawCentredString(w / 2, h * 0.535, title)

    # Violet rule under title
    rule_w = 36 * mm
    c.setStrokeColor(C_ACCENT)
    c.setLineWidth(1.2)
    c.line(w / 2 - rule_w / 2, h * 0.515, w / 2 + rule_w / 2, h * 0.515)

    # Subtitle — wrap if long
    c.setFillColor(C_Z400)
    c.setFont(F_BODY, 11)
    max_chars = 52
    if len(subtitle) > max_chars:
        split = subtitle.rfind(" ", 0, max_chars)
        split = split if split > 0 else max_chars
        c.drawCentredString(w / 2, h * 0.487, subtitle[:split])
        c.drawCentredString(w / 2, h * 0.466, subtitle[split + 1:])
    else:
        c.drawCentredString(w / 2, h * 0.477, subtitle)

    # Date
    if date_str:
        c.setFillColor(Color(1, 1, 1, 0.28))
        c.setFont(F_BODY, 8.5)
        c.drawCentredString(w / 2, h * 0.415, date_str)

    # Bottom slogan
    c.setFillColor(Color(1, 1, 1, 0.18))
    c.setFont(F_BODY, 8)
    c.drawCentredString(w / 2, 20 * mm, SLOGAN)


def _draw_footer(c, doc):
    c.setFillColor(C_Z400)
    c.setFont(F_BODY, 7.5)
    c.drawString(MARGIN_L, 13 * mm, FOOTER_TEXT)
    c.drawRightString(PAGE_W - MARGIN_R, 13 * mm, str(doc.page - 1))
    c.setStrokeColor(C_Z200)
    c.setLineWidth(0.3)
    c.line(MARGIN_L, 17 * mm, PAGE_W - MARGIN_R, 17 * mm)


# ─── Public builder ───────────────────────────────────────────────────────────

def build_branded_pdf(out_path: str, title: str, subtitle: str,
                      date_str: str, story: list) -> None:
    """
    Build a branded PDF.
    Page 1 = cinematic dark cover (drawn entirely on canvas, no flowables).
    Pages 2+ = body with footer, built from the story list.
    """
    def on_cover(c, doc):
        c.saveState()
        _draw_cover(c, doc, title, subtitle, date_str)
        c.restoreState()

    def on_body(c, doc):
        c.saveState()
        _draw_footer(c, doc)
        c.restoreState()

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
    )

    # PageBreak as first flowable = cover is a blank canvas page (art drawn via onFirstPage)
    full_story = [PageBreak()] + story
    doc.build(full_story, onFirstPage=on_cover, onLaterPages=on_body)


# ─── Story helpers ────────────────────────────────────────────────────────────

def heading(text: str, level: int = 1) -> list:
    if level == 1:
        return [
            Paragraph(text.upper(), S_LABEL),
            _VRule(),
            Spacer(1, 1 * mm),
            Paragraph(text, S_HEADING1),
        ]
    elif level == 2:
        return [Paragraph(text, S_HEADING2)]
    else:
        return [Paragraph(text.upper(), S_LABEL)]


def body(text: str, tight: bool = False) -> Paragraph:
    return Paragraph(text, S_BODY_TIGHT if tight else S_BODY)


def bullet(text: str) -> Paragraph:
    return Paragraph(f"\u2022\u2002{text}", S_BULLET)


def callout(text: str, kind: str = "info") -> list:
    """Callout box implemented as a styled Table — reliable rendering."""
    _kinds = {
        "info":     (HEX_CALL_INFO_BORDER,  HEX_CALL_INFO_BG),
        "warning":  (HEX_CALL_WARN_BORDER,  HEX_CALL_WARN_BG),
        "positive": (HEX_CALL_OK_BORDER,    HEX_CALL_OK_BG),
    }
    border_hex, bg_hex = _kinds.get(kind, _kinds["info"])

    para = Paragraph(text, S_CALLOUT)
    t = Table([[para]], colWidths=[CONTENT_W - 6 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _h(bg_hex)),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBEFORE",    (0, 0), (-1, -1), 3, _h(border_hex)),
        ("ROUNDEDCORNERS", [2]),
    ]))
    return [t, Spacer(1, 4 * mm)]


def meta_block(rows: list[tuple[str, str]]) -> list:
    data = [
        [Paragraph(k, S_META_LABEL), Paragraph(v, S_META_VALUE)]
        for k, v in rows
    ]
    t = Table(data, colWidths=[42 * mm, CONTENT_W - 42 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), C_Z100),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.3, C_Z200),
    ]))
    return [t, Spacer(1, 6 * mm)]


def data_table(headers: list[str], rows: list[list[str]]) -> list:
    th_style = ParagraphStyle("TH",
        fontName=F_BOLD, fontSize=8.5, textColor=white, leading=12)
    td_style = ParagraphStyle("TD",
        fontName=F_BODY, fontSize=9, textColor=C_Z700, leading=13)

    header_row = [Paragraph(h, th_style) for h in headers]
    data_rows  = [[Paragraph(str(v), td_style) for v in row] for row in rows]

    col_w = CONTENT_W / len(headers)
    t = Table([header_row] + data_rows, colWidths=[col_w] * len(headers))

    style = [
        ("BACKGROUND",    (0, 0), (-1,  0), C_PRIMARY),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("LINEBELOW",     (0, 1), (-1, -1), 0.3, C_Z200),
    ]
    for i in range(1, len(rows) + 1):
        if i % 2 == 1:
            style.append(("BACKGROUND", (0, i), (-1, i), C_Z100))

    t.setStyle(TableStyle(style))
    return [t, Spacer(1, 6 * mm)]
