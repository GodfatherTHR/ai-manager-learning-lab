"""Professional PDF session reports for academic submission."""

from __future__ import annotations

import io
import re
import textwrap
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak,
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)

from lab import config, data_store, sessions
from lab.errors import ExportError

NAVY = colors.HexColor("#1F3A5F")
ACCENT = colors.HexColor("#2E6F95")
LIGHT = colors.HexColor("#F2F5F9")
PALE_BLUE = colors.HexColor("#EAF1F8")
BORDER = colors.HexColor("#D5DEE8")
MUTED = colors.HexColor("#687685")
INK = colors.HexColor("#1A1A1A")
WHITE = colors.white

_FONT_FAMILY: str | None = None
_FONT_CANDIDATES = [
    (
        "LabSans",
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/ariali.ttf"),
        Path("C:/Windows/Fonts/arialbi.ttf"),
    ),
    (
        "LabSans",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
    ),
    (
        "LabSans",
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"),
    ),
]


def font_family() -> str:
    global _FONT_FAMILY
    if _FONT_FAMILY:
        return _FONT_FAMILY
    for family, regular, bold, italic, bold_italic in _FONT_CANDIDATES:
        if not all(path.exists() for path in (regular, bold, italic, bold_italic)):
            continue
        try:
            pdfmetrics.registerFont(TTFont(family, str(regular)))
            pdfmetrics.registerFont(TTFont(f"{family}-Bold", str(bold)))
            pdfmetrics.registerFont(TTFont(f"{family}-Italic", str(italic)))
            pdfmetrics.registerFont(TTFont(f"{family}-BoldItalic", str(bold_italic)))
            pdfmetrics.registerFontFamily(
                family,
                normal=family,
                bold=f"{family}-Bold",
                italic=f"{family}-Italic",
                boldItalic=f"{family}-BoldItalic",
            )
            _FONT_FAMILY = family
            return family
        except Exception:
            continue
    _FONT_FAMILY = "Helvetica"
    return _FONT_FAMILY


def _styles() -> dict[str, ParagraphStyle]:
    family = font_family()
    body = ParagraphStyle(
        "Body",
        fontName=family,
        fontSize=9.6,
        leading=13.6,
        textColor=INK,
        spaceAfter=5,
        alignment=TA_LEFT,
        splitLongWords=1,
    )
    styles = {
        "body": body,
        "body_italic": ParagraphStyle(
            "BodyItalic", parent=body, fontName=f"{family}-Italic" if family != "Helvetica" else "Helvetica-Oblique",
            textColor=MUTED,
        ),
        "small": ParagraphStyle("Small", parent=body, fontSize=8.0, leading=10.8, textColor=MUTED),
        "small_italic": ParagraphStyle(
            "SmallItalic", parent=body, fontSize=8.0, leading=10.8, textColor=MUTED,
            fontName=f"{family}-Italic" if family != "Helvetica" else "Helvetica-Oblique",
        ),
        "label": ParagraphStyle(
            "Label", parent=body, fontSize=7.4, leading=9.5, textColor=MUTED,
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
        ),
        "h1": ParagraphStyle(
            "H1", parent=body, fontSize=16.0, leading=20.0, textColor=NAVY,
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
            spaceBefore=14, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2", parent=body, fontSize=12.5, leading=16.0, textColor=NAVY,
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
            spaceBefore=10, spaceAfter=5,
        ),
        "h3": ParagraphStyle(
            "H3", parent=body, fontSize=10.8, leading=14.0, textColor=ACCENT,
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
            spaceBefore=8, spaceAfter=4,
        ),
        "h4": ParagraphStyle(
            "H4", parent=body, fontSize=9.8, leading=12.8, textColor=INK,
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
            spaceBefore=6, spaceAfter=3,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=body, leftIndent=13, bulletIndent=2, spaceAfter=2.5,
            bulletFontName=family,
        ),
        "numbered": ParagraphStyle(
            "Numbered", parent=body, leftIndent=16, bulletIndent=2, spaceAfter=2.5,
            bulletFontName=family,
        ),
        "quote": ParagraphStyle(
            "Quote", parent=body, leftIndent=12, rightIndent=12, textColor=MUTED,
            fontName=f"{family}-Italic" if family != "Helvetica" else "Helvetica-Oblique",
            backColor=LIGHT, borderColor=BORDER, borderWidth=0.4, borderPadding=6,
            spaceBefore=4, spaceAfter=6,
        ),
        "code": ParagraphStyle(
            "Code", parent=body, fontName="Courier", fontSize=7.9, leading=9.8,
            textColor=INK, backColor=LIGHT, borderColor=BORDER, borderWidth=0.4,
            borderPadding=5, leftIndent=3, rightIndent=3, spaceBefore=3, spaceAfter=5,
        ),
        "code_inline": ParagraphStyle(
            "CodeInline", parent=body, fontName="Courier", fontSize=8.2, leading=10.5,
        ),
        "query": ParagraphStyle(
            "Query", parent=body, fontSize=9.2, leading=12.8, backColor=PALE_BLUE,
            borderColor=BORDER, borderWidth=0.4, borderPadding=7, leftIndent=4,
            rightIndent=4, spaceBefore=3, spaceAfter=7,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", parent=body, fontSize=7.8, leading=9.8, textColor=WHITE,
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
            spaceAfter=0,
        ),
        "table_cell": ParagraphStyle(
            "TableCell", parent=body, fontSize=7.8, leading=9.8, spaceAfter=0,
        ),
        "table_cell_small": ParagraphStyle(
            "TableCellSmall", parent=body, fontSize=7.0, leading=8.8, spaceAfter=0,
        ),
        "glance": ParagraphStyle(
            "Glance", parent=body, alignment=TA_CENTER, fontSize=8.0, leading=10.0,
            textColor=MUTED, spaceAfter=0,
        ),
        "glance_label": ParagraphStyle(
            "GlanceLabel", parent=body, alignment=TA_CENTER, fontSize=7.0, leading=9.0,
            textColor=MUTED, spaceAfter=0,
        ),
        "turn_heading": ParagraphStyle(
            "TurnHeading", parent=body, fontSize=10.0, leading=12.0, textColor=NAVY,
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
            spaceAfter=0,
        ),
        "turn_time": ParagraphStyle(
            "TurnTime", parent=body, fontSize=7.6, leading=9.6, textColor=MUTED,
            alignment=TA_RIGHT, spaceAfter=0,
        ),
        "cover_kicker": ParagraphStyle(
            "CoverKicker", parent=body, fontSize=8.5, leading=11.0, textColor=colors.HexColor("#BFD4E8"),
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
            spaceAfter=4,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=body, fontSize=25.0, leading=29.0, textColor=WHITE,
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
            spaceAfter=4,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle", parent=body, fontSize=10.5, leading=14.0, textColor=colors.HexColor("#DCE8F2"),
            spaceAfter=0,
        ),
        "cover_company": ParagraphStyle(
            "CoverCompany", parent=body, fontSize=16.0, leading=20.0, textColor=NAVY,
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
            spaceAfter=2,
        ),
        "cover_caption": ParagraphStyle(
            "CoverCaption", parent=body, fontSize=9.5, leading=12.0, textColor=MUTED,
            spaceAfter=14,
        ),
        "cover_label": ParagraphStyle(
            "CoverLabel", parent=body, fontSize=7.2, leading=9.3, textColor=MUTED,
            fontName=f"{family}-Bold" if family != "Helvetica" else "Helvetica-Bold",
            spaceAfter=0,
        ),
        "cover_value": ParagraphStyle(
            "CoverValue", parent=body, fontSize=9.6, leading=12.4, textColor=INK, spaceAfter=0,
        ),
        "footer": ParagraphStyle(
            "Footer", parent=body, fontSize=7.3, leading=9.0, textColor=MUTED,
        ),
    }
    return styles


def _plain_text(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text or "")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_#]", "", text)
    return text


def _inline_markdown(text: str) -> str:
    if text is None:
        return ""
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    tokens: dict[str, str] = {}

    def stash(payload: str) -> str:
        key = f"@@LABTOKEN{len(tokens)}@@"
        tokens[key] = payload
        return key

    def code(match: re.Match) -> str:
        return stash(f'<font name="Courier" size="8.4">{escape(match.group(1))}</font>')

    text = re.sub(r"`([^`\n]+)`", code, text)

    def link(match: re.Match) -> str:
        label = escape(match.group(1))
        url = match.group(2).strip()
        if re.match(r"^(https?://|mailto:)", url, re.IGNORECASE):
            return stash(f'<link href="{escape(url, {chr(34): "&quot;"})}" color="#2E6F95">{label}</link>')
        return stash(label)

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    text = escape(text)
    text = re.sub(r"\*\*([^*\n]+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__([^_\n]+?)__", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    for key, payload in tokens.items():
        text = text.replace(key, payload)
    return text


def _fenced_code_flowable(code: str, styles: dict[str, ParagraphStyle]) -> XPreformatted:
    lines = []
    for line in code.splitlines() or [""]:
        if len(line) <= 96:
            lines.append(line)
        else:
            lines.extend(textwrap.wrap(line, width=96, replace_whitespace=False, drop_whitespace=False) or [""])
    return XPreformatted(escape("\n".join(lines)), styles["code"])


def _is_table_separator(line: str) -> bool:
    if "|" not in line:
        return False
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def _split_table_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    cells = []
    current = []
    escaped = False
    for character in text:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    cells.append("".join(current).strip())
    return cells


def _table_flowable(header: list[str], rows: list[list[str]], styles: dict[str, ParagraphStyle], width: float) -> Table:
    column_count = max(1, len(header))
    normalized_rows = []
    for row in rows:
        padded = (row + [""] * column_count)[:column_count]
        normalized_rows.append(padded)
    header = (header + [""] * column_count)[:column_count]

    weights = []
    for index in range(column_count):
        lengths = [len(_plain_text(header[index]))]
        lengths.extend(len(_plain_text(row[index])) for row in normalized_rows[:20])
        weights.append(min(max(max(lengths, default=4), 8), 46))
    total_weight = sum(weights) or 1
    widths = [width * weight / total_weight for weight in weights]
    minimum = 28 if column_count <= 8 else 22
    widths = [max(minimum, item) for item in widths]
    scale = width / sum(widths)
    widths = [item * scale for item in widths]

    cell_style = styles["table_cell"] if column_count <= 6 else styles["table_cell_small"]
    data = [[Paragraph(_inline_markdown(cell), styles["table_header"]) for cell in header]]
    for row in normalized_rows:
        data.append([Paragraph(_inline_markdown(cell), cell_style) for cell in row])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#F8FAFC")]),
    ]))
    return table


def render_markdown(text: str, styles: dict[str, ParagraphStyle], width: float) -> list:
    flowables = []
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    paragraph_lines: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if not paragraph_lines:
            return
        rendered = ""
        for line_index, raw_line in enumerate(paragraph_lines):
            rendered += _inline_markdown(raw_line.strip())
            if line_index < len(paragraph_lines) - 1:
                rendered += "<br/>" if raw_line.endswith("  ") else " "
        if rendered.strip():
            flowables.append(Paragraph(rendered, styles["body"]))
        paragraph_lines = []

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            index += 1
            continue

        if stripped.startswith("```") or stripped.startswith("~~~"):
            flush_paragraph()
            marker = stripped[:3]
            code_lines = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith(marker):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            flowables.append(_fenced_code_flowable("\n".join(code_lines), styles))
            flowables.append(Spacer(1, 2))
            continue

        if "|" in line and index + 1 < len(lines) and _is_table_separator(lines[index + 1]):
            flush_paragraph()
            header = _split_table_row(line)
            index += 2
            rows = []
            while index < len(lines) and lines[index].strip() and "|" in lines[index]:
                rows.append(_split_table_row(lines[index]))
                index += 1
            flowables.append(_table_flowable(header, rows, styles, width))
            flowables.append(Spacer(1, 5))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            style = styles["h2"] if level == 1 else styles["h3"] if level == 2 else styles["h4"]
            flowables.append(Paragraph(_inline_markdown(heading.group(2)), style))
            index += 1
            continue

        if re.fullmatch(r"\s*([-*_])\1{2,}\s*", line):
            flush_paragraph()
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=4, spaceAfter=5))
            index += 1
            continue

        if re.match(r"^\s*[-*+]\s+", line):
            flush_paragraph()
            while index < len(lines) and re.match(r"^\s*[-*+]\s+", lines[index]):
                match = re.match(r"^(\s*)[-*+]\s+(.*)$", lines[index])
                indent = min(len(match.group(1)) // 2, 3)
                style = styles["bullet"].clone(f"Bullet{indent}", leftIndent=13 + indent * 11, bulletIndent=2 + indent * 11)
                flowables.append(Paragraph(_inline_markdown(match.group(2)), style, bulletText="•"))
                index += 1
            flowables.append(Spacer(1, 2))
            continue

        if re.match(r"^\s*\d+[.)]\s+", line):
            flush_paragraph()
            while index < len(lines) and re.match(r"^\s*\d+[.)]\s+", lines[index]):
                match = re.match(r"^(\s*)(\d+)[.)]\s+(.*)$", lines[index])
                indent = min(len(match.group(1)) // 2, 3)
                style = styles["numbered"].clone(f"Numbered{indent}", leftIndent=16 + indent * 11, bulletIndent=2 + indent * 11)
                flowables.append(Paragraph(_inline_markdown(match.group(3)), style, bulletText=f"{match.group(2)}."))
                index += 1
            flowables.append(Spacer(1, 2))
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(re.sub(r"^\s*>\s?", "", lines[index]))
                index += 1
            rendered = "<br/>".join(_inline_markdown(item) for item in quote_lines)
            flowables.append(Paragraph(rendered, styles["quote"]))
            continue

        paragraph_lines.append(line)
        index += 1

    flush_paragraph()
    return flowables


def _cover(session: sessions.Session, stats: dict, styles: dict[str, ParagraphStyle], width: float) -> list:
    band = Table(
        [[
            [
                Paragraph("AI MANAGER LEARNING LAB", styles["cover_kicker"]),
                Paragraph("Management Session Report", styles["cover_title"]),
                Paragraph("Prepared for academic submission", styles["cover_subtitle"]),
            ]
        ]],
        colWidths=[width],
    )
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    fields = [
        ("Student name", session.student_name or "Not provided"),
        ("Student ID", session.student_id or "Not provided"),
        ("Course", session.course),
        ("Company", session.company or data_store.company_name()),
        ("Session date", sessions.human_date(session.created_at)),
        ("Session ID", session.id),
        ("Agent / harness", session.agent or "Not recorded"),
        ("Status", "Completed" if session.status == "completed" else "In progress"),
    ]
    field_rows = []
    for label, value in fields:
        field_rows.append([
            Paragraph(escape(label.upper()), styles["cover_label"]),
            Paragraph(escape(str(value)), styles["cover_value"]),
        ])
    field_table = Table(field_rows, colWidths=[width * 0.27, width * 0.73], hAlign="LEFT")
    field_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    glance_cells = [
        (stats["turns"], "TURNS LOGGED"),
        (len(stats["instruction_refs"]), "INSTRUCTION FILES"),
        (len(stats["skill_refs"]), "SKILLS USED"),
        (len(stats["document_refs"]), "DATA SOURCES"),
        (stats["evidence_count"], "EVIDENCE POINTS"),
    ]
    glance_data = [[
        Paragraph(
            f'<font size="17" color="#1F3A5F"><b>{value}</b></font><br/>'
            f'<font size="7" color="#687685">{label}</font>',
            styles["glance"],
        )
        for value, label in glance_cells
    ]]
    glance = Table(glance_data, colWidths=[width / len(glance_cells)] * len(glance_cells), hAlign="LEFT")
    glance.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    notice = Paragraph(
        "This report records a management session conducted with the student's own AI Manager harness. "
        "The lab itself does not call an AI model. Student queries are reproduced verbatim from the session log; "
        "AI responses are reproduced as recorded. Every figure attributed to the company should be traceable to "
        "the cited teacher-provided data.",
        styles["small"],
    )

    return [
        band,
        Spacer(1, 16),
        Paragraph(escape(session.company or data_store.company_name()), styles["cover_company"]),
        Paragraph(f"{config.COURSE_NAME} · AI Manager Learning Lab", styles["cover_caption"]),
        field_table,
        Spacer(1, 18),
        Paragraph("SESSION AT A GLANCE", styles["label"]),
        Spacer(1, 5),
        glance,
        Spacer(1, 18),
        notice,
        PageBreak(),
    ]


def _refs_table(
    instruction_refs: list[str],
    skill_refs: list[str],
    document_refs: list[str],
    styles: dict[str, ParagraphStyle],
    width: float,
) -> Table:
    def cell(refs: list[str]) -> Paragraph:
        if not refs:
            return Paragraph("None recorded", styles["table_cell_small"])
        rendered = "<br/>".join(
            f'<font name="Courier" size="7.2">{escape(reference)}</font>' for reference in refs
        )
        return Paragraph(rendered, styles["table_cell_small"])

    table = Table(
        [
            [
                Paragraph("INSTRUCTION FILES APPLIED", styles["table_header"]),
                Paragraph("BUILT-IN SKILLS APPLIED", styles["table_header"]),
                Paragraph("COMPANY DATA CONSULTED", styles["table_header"]),
            ],
            [cell(instruction_refs), cell(skill_refs), cell(document_refs)],
        ],
        colWidths=[width * 0.34, width * 0.28, width * 0.38],
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _summary_section(session: sessions.Session, stats: dict, styles: dict[str, ParagraphStyle], width: float) -> list:
    flowables = [Paragraph("Session Summary", styles["h1"])]
    if session.summary.strip():
        flowables.extend(render_markdown(session.summary, styles, width))
    else:
        flowables.append(Paragraph(
            "No final session summary was recorded. The transcript below is the authoritative record of the session.",
            styles["body_italic"],
        ))
    flowables.extend([
        Spacer(1, 4),
        Paragraph("Sources used across the session", styles["h2"]),
        _refs_table(stats["instruction_refs"], stats["skill_refs"], stats["document_refs"], styles, width),
    ])
    if stats["principles"]:
        flowables.extend([
            Spacer(1, 6),
            Paragraph("Management principles referenced", styles["h2"]),
            Paragraph(escape(", ".join(stats["principles"])), styles["body"]),
        ])
    flowables.extend([
        Spacer(1, 8),
        Paragraph("How to read this report", styles["h2"]),
        Paragraph(
            "Each turn shows the student query exactly as logged, the AI Manager response, and the sources and evidence "
            "the student or agent recorded. Built-in skills are optional methods the student invoked; they are shown "
            "separately from the student's instruction files. The companion ZIP contains the student's Markdown instruction files.",
            styles["small"],
        ),
        PageBreak(),
    ])
    return flowables


def _turn_section(turn: sessions.Turn, styles: dict[str, ParagraphStyle], width: float) -> list:
    flowables: list = [CondPageBreak(120), KeepTogether([
        Table(
            [[
                Paragraph(f"TURN {turn.turn_no}", styles["turn_heading"]),
                Paragraph(sessions.human_time(turn.created_at), styles["turn_time"]),
            ]],
            colWidths=[width * 0.35, width * 0.65],
            hAlign="LEFT",
            style=TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ]),
        ),
        Spacer(1, 6),
        Paragraph("STUDENT QUERY (VERBATIM)", styles["label"]),
        Spacer(1, 2),
    ])]
    query_text = escape(turn.query).replace("\n", "<br/>")
    flowables.append(Paragraph(query_text or " ", styles["query"]))
    flowables.append(Spacer(1, 7))
    flowables.append(Paragraph("AI MANAGER RESPONSE", styles["label"]))
    flowables.append(Spacer(1, 2))
    response_flowables = render_markdown(turn.response, styles, width)
    flowables.extend(response_flowables or [Paragraph("No response was recorded.", styles["body_italic"])])
    flowables.append(Spacer(1, 5))
    flowables.append(_refs_table(turn.instructions, turn.skills, turn.documents, styles, width))
    if turn.evidence:
        flowables.append(Spacer(1, 5))
        flowables.append(Paragraph("EVIDENCE CITED", styles["label"]))
        for item in turn.evidence:
            flowables.append(Paragraph(_inline_markdown(item), styles["bullet"], bulletText="•"))
    if turn.principles:
        flowables.append(Spacer(1, 4))
        flowables.append(Paragraph(
            "MANAGEMENT PRINCIPLES: " + escape(", ".join(turn.principles)),
            styles["small"],
        ))
    if not turn.instructions and not turn.skills and not turn.documents and not turn.evidence and not turn.principles:
        flowables.append(Spacer(1, 3))
        flowables.append(Paragraph(
            "No instructions, skills, company data, evidence, or principles were recorded for this turn.",
            styles["small_italic"],
        ))
    flowables.extend([
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=4, spaceAfter=10),
    ])
    return flowables


def _footer_callback(company: str):
    def draw(canvas, doc):
        canvas.saveState()
        left = 17 * mm
        right = A4[0] - 17 * mm
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.4)
        canvas.line(left, 16 * mm, right, 16 * mm)
        canvas.setFont(font_family(), 7.2)
        canvas.setFillColor(MUTED)
        canvas.drawString(left, 11.5 * mm, "AI Manager Learning Lab")
        canvas.drawCentredString(A4[0] / 2, 11.5 * mm, company[:70])
        canvas.drawRightString(right, 11.5 * mm, f"Page {doc.page}")
        if doc.page > 1:
            canvas.setFont(font_family(), 7.0)
            canvas.drawString(left, A4[1] - 11 * mm, "Management Session Report")
            canvas.drawRightString(right, A4[1] - 11 * mm, config.APP_TITLE)
        canvas.restoreState()
    return draw


def render_session_pdf(session: sessions.Session) -> bytes:
    try:
        styles = _styles()
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=17 * mm - 6,
            rightMargin=17 * mm - 6,
            topMargin=18 * mm - 6,
            bottomMargin=20 * mm - 6,
            title=f"{config.APP_TITLE} — {session.title}",
            author=session.student_name or "Student",
            subject=f"{config.COURSE_NAME} management session report",
            creator=config.APP_TITLE,
        )
        width = doc.width - 12
        stats = sessions.session_stats(session)
        story = []
        story.extend(_cover(session, stats, styles, width))
        story.extend(_summary_section(session, stats, styles, width))
        story.append(Paragraph("Conversation Transcript", styles["h1"]))
        if not session.turns:
            story.append(Paragraph("No turns were logged in this session.", styles["body_italic"]))
        for turn in session.turns:
            story.append(Spacer(1, 4))
            story.extend(_turn_section(turn, styles, width))
        story.extend([
            Spacer(1, 8),
            CondPageBreak(170),
            Paragraph("Submission Note", styles["h1"]),
            Paragraph(
                "This PDF is the session report component of the submission. The second required component is a ZIP "
                "archive containing the student's Markdown management instruction files. The company dataset, session "
                "database, and application code are not part of the submission.",
                styles["body"],
            ),
            Spacer(1, 12),
            Paragraph("Student declaration", styles["h2"]),
            Paragraph(
                "I confirm that the management instruction files in the companion ZIP were authored by me, and that "
                "this report is the record of my AI Manager session for the Principles of Management course.",
                styles["body"],
            ),
            Spacer(1, 22),
            Table(
                [[
                    Paragraph("Student signature: ______________________________", styles["small"]),
                    Paragraph("Date: __________________", styles["small"]),
                ]],
                colWidths=[width * 0.65, width * 0.35],
                style=TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]),
            ),
            Spacer(1, 18),
            Paragraph(
                f"Generated {datetime.now().astimezone().strftime('%d %b %Y, %H:%M')} from session {session.id}.",
                styles["small"],
            ),
        ])
        footer = _footer_callback(session.company or data_store.company_name())
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        return buffer.getvalue()
    except ExportError:
        raise
    except Exception as exc:
        raise ExportError(f"Could not build the PDF report: {exc}") from exc


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", (value or "").strip()).strip("._-")
    return text or "student"


def default_pdf_name(session: sessions.Session) -> str:
    return f"{_slug(session.student_name)}_session_{session.id}.pdf"


def write_session_pdf(session: sessions.Session, data: bytes, out_path: Path | None = None) -> Path:
    destination = out_path.resolve() if out_path else (config.EXPORTS_DIR / default_pdf_name(session))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    try:
        temporary.write_bytes(data)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def export_session_pdf(session_id: str | None = None, out_path: Path | None = None) -> Path:
    session = sessions.get_session(session_id)
    data = render_session_pdf(session)
    return write_session_pdf(session, data, out_path)
