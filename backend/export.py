"""Markdown -> PDF for the writer's report (reportlab, pure Python)."""
import io, re, html, textwrap
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, PageTemplate, Paragraph,
                                Preformatted, Spacer, Table, TableStyle)

INK, MUTED, LINE, ACCENT = (colors.HexColor(c) for c in ("#12151c", "#5d6472", "#d9dce4", "#3a37e8"))
# Built-in PDF fonts are cp1252 only; map characters LLMs commonly emit.
_MAP = {"\u2011": "-", "\u2010": "-", "\u2212": "-", "\u202f": " ", "\u00a0": " ", "\u2192": "->",
        "\u2190": "<-", "\u2265": ">=", "\u2264": "<=", "\u2248": "~", "\u2009": " ", "\u200b": ""}


def _clean(s):
    for k, v in _MAP.items():
        s = s.replace(k, v)
    return s.encode("cp1252", "replace").decode("cp1252")


def _inline(t):
    t = html.escape(_clean(t), quote=False)
    t = re.sub(r"`([^`]+)`", r'<font face="Courier" size="9.5">\1</font>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", rf'<link href="\2" color="#3a37e8">\1</link>', t)
    t = re.sub(r"(?<![\"'>=])(https?://[^\s<)]*[^\s<).,;:])", r'<link href="\1" color="#3a37e8">\1</link>', t)
    return t


def _styles():
    S = {"title": ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=24, leading=29, textColor=INK, spaceAfter=6),
         "meta": ParagraphStyle("m", fontName="Helvetica", fontSize=9.5, leading=13, textColor=MUTED, spaceAfter=8),
         "body": ParagraphStyle("b", fontName="Times-Roman", fontSize=11, leading=16.5, textColor=INK, spaceAfter=7),
         "code": ParagraphStyle("c", fontName="Courier", fontSize=8.5, leading=11.5, leftIndent=8,
                                backColor=colors.HexColor("#f1f2f6"), borderPadding=6, spaceAfter=10)}
    for n, (sz, ld, bf, af) in {1: (17, 22, 20, 8), 2: (14.5, 19, 18, 6), 3: (12, 16, 12, 4)}.items():
        S[f"h{n}"] = ParagraphStyle(f"h{n}", fontName="Helvetica-Bold", fontSize=sz, leading=ld, spaceBefore=bf,
                                    spaceAfter=af, textColor=INK, keepWithNext=1)
    S["quote"] = ParagraphStyle("q", parent=S["body"], leftIndent=14, textColor=MUTED)
    S["cell"] = ParagraphStyle("cell", parent=S["body"], fontSize=9.5, leading=13, spaceAfter=0)
    return S


def _table(rows, S, width):
    n = max(len(r) for r in rows)
    data = [[Paragraph(("<b>%s</b>" if i == 0 else "%s") % _inline(c), S["cell"]) for c in r + [""] * (n - len(r))]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=[width / n] * n, repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .5, LINE), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f2f6")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return [t, Spacer(1, 8)]


def _flow(md, S, width):
    out, para, lines, i = [], [], md.replace("\r", "").split("\n"), 0

    def flush():
        if para:
            out.append(Paragraph(_inline(" ".join(para)), S["body"]))
            para.clear()

    while i < len(lines):
        ln = lines[i]; s = ln.strip()
        if s.startswith("```"):
            flush(); i += 1; buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(textwrap.fill(_clean(lines[i]), 95, replace_whitespace=False) if lines[i] else ""); i += 1
            out.append(Preformatted("\n".join(buf), S["code"])); i += 1; continue
        if (m := re.match(r"^(#{1,6})\s+(.*?)\s*#*$", s)):
            flush(); out.append(Paragraph(_inline(m[2]), S[f"h{min(len(m[1]), 3)}"])); i += 1; continue
        if re.match(r"^([-*_])\1{2,}$", s):
            flush(); out.append(HRFlowable(width="100%", thickness=.5, color=LINE, spaceBefore=6, spaceAfter=10)); i += 1; continue
        if s.startswith("|"):
            flush(); rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows: out += _table(rows, S, width)
            continue
        if s.startswith(">"):
            flush(); buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip("> ")); i += 1
            out.append(Paragraph(_inline(" ".join(buf)), S["quote"])); continue
        if (lm := re.match(r"^(\s*)([-*\u2022]|\d+[.)])\s+(.*)", ln)):
            flush(); lvl = min(len(lm[1].replace("\t", "  ")) // 2, 3)
            text = [lm[3]]; i += 1
            while i < len(lines) and lines[i].strip() and re.match(r"^\s{2,}\S", lines[i]) \
                    and not re.match(r"^\s*([-*\u2022]|\d+[.)])\s+", lines[i]):
                text.append(lines[i].strip()); i += 1
            st = ParagraphStyle("li", parent=S["body"], leftIndent=18 + 16 * lvl, bulletIndent=4 + 16 * lvl, spaceAfter=3)
            out.append(Paragraph(_inline(" ".join(text)), st, bulletText="\u2022" if lm[2] in "-*\u2022" else lm[2])); continue
        if not s: flush()
        else: para.append(s)
        i += 1
    flush()
    return out


def build_pdf(topic: str, markdown: str, created_at: float) -> bytes:
    S = _styles()
    title, md = topic, markdown
    h1s = re.findall(r"^#\s+(.+?)\s*#*$", md, re.M)
    first = next((l for l in md.split("\n") if l.strip()), "")
    if len(h1s) == 1 and re.match(r"^#\s+", first):  # writer supplied its own title: use it once
        title = h1s[0]; md = md.replace(first, "", 1)
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=22 * mm,
                          bottomMargin=24 * mm, title=_clean(title), author="MindMesh")
    width = A4[0] - 44 * mm

    def decor(c, d):
        c.saveState(); c.setStrokeColor(LINE); c.setLineWidth(.5); c.line(22 * mm, 17 * mm, A4[0] - 22 * mm, 17 * mm)
        c.setFont("Helvetica", 8.5); c.setFillColor(MUTED)
        c.drawString(22 * mm, 12 * mm, "MindMesh research report"); c.drawRightString(A4[0] - 22 * mm, 12 * mm, f"Page {d.page}")
        c.restoreState()

    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, width, A4[1] - 46 * mm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=decor)])
    story = [Paragraph(_inline(title), S["title"]),
             Paragraph("Generated by MindMesh on " + datetime.fromtimestamp(created_at).strftime("%d %B %Y"), S["meta"]),
             HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=12)] + _flow(md, S, width)
    doc.build(story)
    return buf.getvalue()
