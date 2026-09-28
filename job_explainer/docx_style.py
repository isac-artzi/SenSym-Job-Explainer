"""Shared DOCX styling primitives for render.py's report builder.

Single column, standard heading styles, no tables or text boxes, system
fonts. Color, bold weight, size, and a thin accent rule are all safe to lean
on for visual polish: they only change how text looks, never how it flows.
"""

from __future__ import annotations

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

BODY_FONT = "Calibri"
BODY_SIZE = Pt(11)

# Same warm terracotta brand used in the web app (job_explainer/ui.py) and in
# Resume Match, so every SenSym document and app feels like one product.
ACCENT_COLOR = RGBColor(0xC1, 0x66, 0x2E)
TEXT_COLOR = RGBColor(0x2B, 0x24, 0x20)
MUTED_COLOR = RGBColor(0x8A, 0x75, 0x66)
BORDER_COLOR_HEX = "EADFD0"
ACCENT_COLOR_HEX = "C1662E"


def _apply_bottom_border(p_pr, val: str, size: int, color: str) -> None:
    for existing in p_pr.findall(qn("w:pBdr")):
        p_pr.remove(existing)
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), val)
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4" if val == "single" else "0")
    bottom.set(qn("w:color"), color)
    p_bdr.append(bottom)
    p_pr.append(p_bdr)


def add_bottom_border(paragraph, color_hex: str, size: int = 6) -> None:
    """A thin horizontal rule under a paragraph — plain OOXML paragraph
    borders, not a drawn shape or text box, so it reads as ordinary
    formatting to any parser, the same way bold or a font color does."""
    _apply_bottom_border(paragraph._p.get_or_add_pPr(), "single", size, color_hex)


def _clear_style_border(style) -> None:
    """Word's built-in "Title" style ships with its own bottom border baked
    into python-docx's default template; turn it off so the only borders
    visible are the ones this module explicitly adds."""
    _apply_bottom_border(style.element.get_or_add_pPr(), "none", 0, "auto")


def _style_heading(style, size: Pt, color: RGBColor, small_caps: bool = False) -> None:
    style.font.name = BODY_FONT
    style.font.size = size
    style.font.bold = True
    style.font.color.rgb = color
    style.font.small_caps = small_caps


def new_document() -> docx.Document:
    document = docx.Document()

    normal = document.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = BODY_SIZE
    normal.font.color.rgb = TEXT_COLOR

    _style_heading(document.styles["Title"], Pt(26), ACCENT_COLOR)
    _clear_style_border(document.styles["Title"])
    _style_heading(document.styles["Heading 1"], Pt(13), ACCENT_COLOR, small_caps=True)
    _style_heading(document.styles["Heading 2"], Pt(11.5), TEXT_COLOR)

    bullet = document.styles["List Bullet"]
    bullet.font.name = BODY_FONT
    bullet.font.size = BODY_SIZE
    bullet.paragraph_format.space_after = Pt(2)

    for section in document.sections:
        section.left_margin = section.right_margin = Inches(1)
    return document


def usable_width(document: docx.Document) -> Inches:
    section = document.sections[0]
    return section.page_width - section.left_margin - section.right_margin


# (size, color, small_caps) per heading level — applied to each run directly,
# not just left to the style definition. Real Microsoft Word resolves a
# paragraph's style-level formatting correctly, but other DOCX renderers
# (Google Docs, LibreOffice, Apple Pages, various online viewers) are known to
# be inconsistent about honoring custom style definitions written by
# python-docx, and can silently fall back to plain black text. Setting the
# same formatting on the run itself is unambiguous in every renderer.
_HEADING_RUN_STYLE = {
    0: (Pt(26), ACCENT_COLOR, False),
    1: (Pt(13), ACCENT_COLOR, True),
    2: (Pt(11.5), TEXT_COLOR, False),
}


def add_heading(document: docx.Document, text: str, level: int = 1):
    heading = document.add_heading(text, level=level)
    size, color, small_caps = _HEADING_RUN_STYLE.get(level, (BODY_SIZE, TEXT_COLOR, False))
    for run in heading.runs:
        run.font.name = BODY_FONT
        run.font.size = size
        run.font.color.rgb = color
        run.font.bold = True
        run.font.small_caps = small_caps
    if level == 1:
        heading.paragraph_format.space_before = Pt(14)
        heading.paragraph_format.space_after = Pt(4)
        add_bottom_border(heading, ACCENT_COLOR_HEX)
    return heading


def add_table(document: docx.Document, header: list[str], rows: list[list[str]]) -> None:
    """A plain, bordered table — the DOCX equivalent of the pipe tables
    petal prompts are allowed to return (see render.markdown_to_docx)."""
    table = document.add_table(rows=1, cols=len(header))
    table.style = "Light Grid Accent 2"
    for cell, text in zip(table.rows[0].cells, header):
        paragraph = cell.paragraphs[0]
        run = paragraph.add_run(text)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = TEXT_COLOR
    for row_values in rows:
        row = table.add_row()
        for cell, text in zip(row.cells, row_values):
            run = cell.paragraphs[0].add_run(text)
            run.font.size = Pt(10)
            run.font.color.rgb = TEXT_COLOR
