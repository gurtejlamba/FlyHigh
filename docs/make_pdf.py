"""Convert README.md to a styled PDF using reportlab."""
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY  = colors.HexColor("#0D1B2A")
BLUE  = colors.HexColor("#1B6CA8")
CYAN  = colors.HexColor("#00C2D4")
LGRAY = colors.HexColor("#E8ECF0")
DGRAY = colors.HexColor("#556575")
CODE_BG = colors.HexColor("#F0F2F5")

W, H = A4
LEFT = RIGHT = 2.2 * cm
TOP = BOTTOM = 2.0 * cm

# ── Styles ────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def style(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=base[parent])
    for k, v in kw.items():
        setattr(s, k, v)
    return s

S_H1 = style("H1", fontSize=22, textColor=NAVY, spaceAfter=6, spaceBefore=12,
             fontName="Helvetica-Bold", leading=26)
S_H2 = style("H2", fontSize=15, textColor=BLUE, spaceAfter=4, spaceBefore=14,
             fontName="Helvetica-Bold", leading=18)
S_H3 = style("H3", fontSize=12, textColor=NAVY, spaceAfter=3, spaceBefore=8,
             fontName="Helvetica-Bold", leading=15)
S_BODY = style("Body", fontSize=10, leading=15, spaceAfter=4,
               textColor=colors.HexColor("#222222"))
S_BULLET = style("Bullet", fontSize=10, leading=14, spaceAfter=2,
                 leftIndent=16, bulletIndent=4, textColor=colors.HexColor("#222222"))
S_CODE = style("Code", fontName="Courier", fontSize=8.5, leading=12,
               backColor=CODE_BG, textColor=colors.HexColor("#1a1a2e"),
               leftIndent=10, rightIndent=10, spaceBefore=4, spaceAfter=4)
S_ITALIC = style("Italic", fontSize=9, textColor=DGRAY,
                 fontName="Helvetica-Oblique", spaceAfter=8)


def escape(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text


def inline(text: str) -> str:
    """Convert inline markdown (bold, code, links) to reportlab XML."""
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier' size='9' color='#1a1a2e'>\1</font>", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    return text


def parse(md: str) -> list:
    story = []
    lines = md.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # H1
        if re.match(r"^# [^#]", line):
            story.append(Paragraph(inline(line[2:]), S_H1))
            story.append(HRFlowable(width="100%", thickness=1.5, color=CYAN, spaceAfter=6))
            i += 1
            continue

        # H2
        if re.match(r"^## [^#]", line):
            story.append(Paragraph(inline(line[3:]), S_H2))
            story.append(HRFlowable(width="100%", thickness=0.5, color=BLUE, spaceAfter=4))
            i += 1
            continue

        # H3
        if re.match(r"^### ", line):
            story.append(Paragraph(inline(line[4:]), S_H3))
            i += 1
            continue

        # Horizontal rule
        if line.strip() == "---":
            story.append(HRFlowable(width="100%", thickness=0.5, color=LGRAY, spaceAfter=6))
            i += 1
            continue

        # Fenced code block
        if line.startswith("```"):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            code_text = "\n".join(code_lines)
            story.append(Preformatted(code_text, S_CODE))
            i += 1
            continue

        # Table
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if "---" not in lines[i]:
                    cells = [c.strip() for c in lines[i].split("|")[1:-1]]
                    rows.append(cells)
                i += 1
            if rows:
                story.append(_make_table(rows))
                story.append(Spacer(1, 6))
            continue

        # Bullet (- or *)
        if re.match(r"^[-*] ", line):
            story.append(Paragraph("&#8226;  " + inline(line[2:]), S_BULLET))
            i += 1
            continue

        # Blank line
        if not line.strip():
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Normal paragraph
        story.append(Paragraph(inline(line), S_BODY))
        i += 1

    return story


def _make_table(rows: list[list[str]]) -> Table:
    col_count = max(len(r) for r in rows)
    usable = W - LEFT - RIGHT
    col_w = usable / col_count

    # Wrap cells as Paragraphs
    def cell_style(text, is_header):
        s = style("TC", fontSize=8.5, leading=12,
                  fontName="Helvetica-Bold" if is_header else "Helvetica",
                  textColor=colors.white if is_header else colors.HexColor("#222222"))
        return Paragraph(inline(text), s)

    table_data = []
    for ri, row in enumerate(rows):
        padded = row + [""] * (col_count - len(row))
        table_data.append([cell_style(c, ri == 0) for c in padded])

    t = Table(table_data, colWidths=[col_w] * col_count, repeatRows=1)
    ts = TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  BLUE),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LGRAY]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ])
    t.setStyle(ts)
    return t


def build(src="README.md", out="docs/SIFT_documentation.pdf"):
    with open(src) as f:
        md = f.read()

    doc = SimpleDocTemplate(
        out,
        pagesize=A4,
        leftMargin=LEFT, rightMargin=RIGHT,
        topMargin=TOP, bottomMargin=BOTTOM,
        title="SIFT — Data-Analyst Agent on Messy Databases",
        author="Hackathon AI-02",
    )
    story = parse(md)
    doc.build(story)
    print(f"Saved: {out}")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    build()
