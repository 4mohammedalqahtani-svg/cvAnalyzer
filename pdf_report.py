import io
import re
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    ListFlowable,
    ListItem,
)

_BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")


def _inline_markdown_to_html(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = _BOLD_PATTERN.sub(r"<b>\1</b>", text)
    return text


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#555555"),
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.white,
            backColor=colors.HexColor("#1a1a2e"),
            spaceBefore=14,
            spaceAfter=8,
            leftIndent=6,
            borderPadding=(6, 6, 6, 6),
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletTextCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            spaceAfter=4,
        )
    )
    return styles


def _parse_critique_to_flowables(critique_text: str, styles):
    flowables = []
    bullet_buffer = []

    def flush_bullets():
        if bullet_buffer:
            items = [
                ListItem(Paragraph(_inline_markdown_to_html(b), styles["BulletTextCustom"]))
                for b in bullet_buffer
            ]
            flowables.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=18,
                    bulletFontSize=8,
                    spaceAfter=8,
                )
            )
            bullet_buffer.clear()

    for raw_line in critique_text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_bullets()
            continue
        if line.startswith("## "):
            flush_bullets()
            heading = line[3:].strip()
            flowables.append(Paragraph(_inline_markdown_to_html(heading), styles["SectionHeading"]))
        elif line.startswith("- ") or line.startswith("* "):
            bullet_buffer.append(line[2:].strip())
        else:
            flush_bullets()
            flowables.append(Paragraph(_inline_markdown_to_html(line), styles["BodyTextCustom"]))

    flush_bullets()
    return flowables


def generate_pdf(critique_text: str, candidate_name: str = "") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        title="ATS Resume Audit Report",
    )

    styles = _build_styles()
    story = []

    story.append(Paragraph("ATS Resume Audit Report", styles["ReportTitle"]))
    subtitle_bits = []
    if candidate_name.strip():
        subtitle_bits.append(f"Candidate: {candidate_name.strip()}")
    subtitle_bits.append(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    subtitle_bits.append("Prepared by: The Candid Mentor (AI Career Auditor)")
    story.append(Paragraph(" | ".join(subtitle_bits), styles["ReportSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 10))

    story.extend(_parse_critique_to_flowables(critique_text, styles))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
