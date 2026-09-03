#!/usr/bin/env python3
"""Build a print-friendly Chinese edition PDF from the translated Markdown."""
from __future__ import annotations

import base64
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Image, PageBreak, PageTemplate, Paragraph, Spacer, Frame

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "The Accidental CTO.zh-CN.md"
OUT = ROOT / "output/pdf/The Accidental CTO.zh-CN.pdf"
TMP = ROOT / "tmp/pdfs"
PAGE = portrait((499, 709))


def register_fonts() -> str:
    candidates = [
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
    ]
    for path, index in candidates:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont("BookCJK", path, subfontIndex=index))
                return "BookCJK"
            except Exception:
                continue
    raise RuntimeError("No usable Chinese system font was found")


FONT = register_fonts()


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"<font name='Helvetica'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__([^_]+)__", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    return text


class BookDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        margin_x, margin_y = 23 * mm, 22 * mm
        frame = Frame(margin_x, margin_y, PAGE[0] - 2 * margin_x,
                      PAGE[1] - 2 * margin_y, id="normal", showBoundary=0)
        self.addPageTemplates([PageTemplate(id="book", frames=frame,
                                             onPage=self.draw_page)])

    def draw_page(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#dddddd"))
        canvas.setLineWidth(0.35)
        canvas.line(23 * mm, 15 * mm, PAGE[0] - 23 * mm, 15 * mm)
        canvas.setFont(FONT, 8)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawCentredString(PAGE[0] / 2, 10 * mm, str(doc.page - 1))
        canvas.restoreState()


class HeadingTOC(Paragraph):
    """Paragraph that registers headings for the generated table of contents."""
    def __init__(self, text, style, level):
        self.level = level
        super().__init__(text, style)

    def afterFlowable(self, doc):
        pass


def image_flowable(line: str):
    match = re.search(r"data:image/[^;]+;base64,([^)]+)", line)
    if not match:
        return None
    TMP.mkdir(parents=True, exist_ok=True)
    target = TMP / "embedded-image.png"
    if not target.exists():
        target.write_bytes(base64.b64decode(match.group(1)))
    img = Image(str(target))
    img._restrictSize(PAGE[0] - 46 * mm, PAGE[1] - 55 * mm)
    return img


def build_story():
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontName=FONT,
                           fontSize=27, leading=34, alignment=TA_CENTER,
                           textColor=colors.HexColor("#171717"), spaceAfter=12 * mm)
    subtitle = ParagraphStyle("subtitle", parent=styles["Normal"], fontName=FONT,
                              fontSize=12, leading=20, alignment=TA_CENTER,
                              textColor=colors.HexColor("#555555"), spaceAfter=8 * mm)
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontName=FONT,
                        fontSize=19, leading=27, spaceBefore=9 * mm,
                        spaceAfter=5 * mm, textColor=colors.HexColor("#171717"),
                        keepWithNext=True)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName=FONT,
                        fontSize=14, leading=21, spaceBefore=6 * mm,
                        spaceAfter=3 * mm, textColor=colors.HexColor("#333333"),
                        keepWithNext=True)
    h3 = ParagraphStyle("h3", parent=styles["Heading3"], fontName=FONT,
                        fontSize=11, leading=17, spaceBefore=4 * mm,
                        spaceAfter=2 * mm, textColor=colors.HexColor("#555555"),
                        keepWithNext=True)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName=FONT,
                          fontSize=9.4, leading=16.5, spaceAfter=3.5 * mm,
                          alignment=TA_LEFT, textColor=colors.HexColor("#202020"))
    bullet = ParagraphStyle("bullet", parent=body, leftIndent=5 * mm,
                            firstLineIndent=-3 * mm, bulletIndent=0,
                            spaceAfter=1.5 * mm)
    quote = ParagraphStyle("quote", parent=body, leftIndent=7 * mm,
                           rightIndent=3 * mm, borderPadding=4 * mm,
                           borderColor=colors.HexColor("#6366f1"),
                           borderWidth=1, borderLeft=True,
                           textColor=colors.HexColor("#555555"),
                           fontSize=9.2)
    code = ParagraphStyle("code", parent=body, fontName="Helvetica", fontSize=7.8,
                          leading=11, backColor=colors.HexColor("#f2f2f2"),
                          borderPadding=3 * mm)

    story = []
    cover = ROOT / "cover.png"
    if cover.exists():
        img = Image(str(cover)); img._restrictSize(PAGE[0] - 28 * mm, 115 * mm)
        story += [Spacer(1, 22 * mm), img, Spacer(1, 10 * mm)]
    story += [Paragraph("意外成为 CTO", title),
              Paragraph("中文译本", subtitle),
              Paragraph("基于作者公开英文原稿的中文翻译", subtitle), PageBreak()]

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    paragraph = []
    in_code = False
    for raw in lines:
        line = raw.strip()
        if line.startswith("```"):
            if paragraph:
                story.append(Paragraph(inline(" ".join(paragraph)), body)); paragraph = []
            in_code = not in_code
            continue
        if in_code:
            story.append(Paragraph(inline(raw), code)); continue
        if not line:
            if paragraph:
                story.append(Paragraph(inline(" ".join(paragraph)), body)); paragraph = []
            continue
        if line.startswith("![](data:image"):
            if paragraph:
                story.append(Paragraph(inline(" ".join(paragraph)), body)); paragraph = []
            img = image_flowable(line)
            if img: story += [Spacer(1, 3 * mm), img, Spacer(1, 3 * mm)]
            continue
        match = re.match(r"^(#{1,4})\s+(.+)$", line)
        if match:
            if paragraph:
                story.append(Paragraph(inline(" ".join(paragraph)), body)); paragraph = []
            level, text = len(match.group(1)), match.group(2).strip("*")
            story.append(Paragraph(inline(text), {1: h1, 2: h2, 3: h3, 4: h3}[level]))
            continue
        if line.startswith(">"):
            if paragraph:
                story.append(Paragraph(inline(" ".join(paragraph)), body)); paragraph = []
            story.append(Paragraph(inline(line[1:].strip()), quote)); continue
        if re.match(r"^[-*]\s+", line):
            if paragraph:
                story.append(Paragraph(inline(" ".join(paragraph)), body)); paragraph = []
            item = re.sub(r"^[-*]\s+", "", line)
            story.append(Paragraph("• " + inline(item), bullet)); continue
        paragraph.append(line)
    if paragraph:
        story.append(Paragraph(inline(" ".join(paragraph)), body))
    return story


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BookDocTemplate(str(OUT), pagesize=PAGE, title="意外成为 CTO", author="Subhash Choudhary")
    doc.build(build_story())
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
