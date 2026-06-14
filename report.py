"""
report.py — Optional PDF export of ATS scoring results via reportlab.

Exports a clean, readable summary PDF with:
  - Overall score
  - Per-criterion breakdown table
  - Fix recommendations
  - Keyword gap (if JD provided)
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scorer import CriterionResult


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def generate_pdf_report(
    criteria: list["CriterionResult"],
    total_score: int,
    filename: str = "resume_ats_report.pdf",
) -> bytes:
    """
    Build and return a PDF report as bytes using reportlab.
    Returns empty bytes if reportlab is not installed.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            HRFlowable,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        return b""

    buffer = io.BytesIO()

    # ── Document setup ──
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # ── Styles ──
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=24,
        textColor=colors.HexColor("#6c63ff"),
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#8b8fa8"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1a1d27"),
        fontName="Helvetica-Bold",
        spaceBefore=16,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#374151"),
        leading=14,
        spaceAfter=4,
    )
    fix_style = ParagraphStyle(
        "Fix",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#6b7280"),
        leading=13,
        leftIndent=12,
        spaceAfter=8,
    )

    # ── Score color ──
    if total_score >= 80:
        score_color = colors.HexColor("#22c55e")
        verdict = "Strong resume — minor fixes needed"
    elif total_score >= 60:
        score_color = colors.HexColor("#f59e0b")
        verdict = "Decent resume — room for improvement"
    else:
        score_color = colors.HexColor("#ef4444")
        verdict = "Significant gaps found — needs work"

    score_style = ParagraphStyle(
        "Score",
        parent=styles["Normal"],
        fontSize=48,
        textColor=score_color,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    verdict_style = ParagraphStyle(
        "Verdict",
        parent=styles["Normal"],
        fontSize=12,
        textColor=score_color,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName="Helvetica-Bold",
    )

    # ── Status helpers ──
    def status_label(status: str) -> str:
        return {"pass": "✓ Pass", "warn": "⚠ Warn", "fail": "✗ Fail"}.get(status, status)

    def status_color(status: str) -> colors.Color:
        return {
            "pass": colors.HexColor("#22c55e"),
            "warn": colors.HexColor("#f59e0b"),
            "fail": colors.HexColor("#ef4444"),
        }.get(status, colors.gray)

    # ── Build content ──
    content = []

    # Header
    content.append(Paragraph("⚡ ATS Resume Scorer", title_style))
    content.append(Paragraph("Automated Applicant Tracking System Analysis", subtitle_style))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
    content.append(Spacer(1, 0.4 * cm))

    # Overall score
    content.append(Paragraph(str(total_score), score_style))
    content.append(Paragraph("/ 100", subtitle_style))
    content.append(Paragraph(verdict, verdict_style))
    content.append(Spacer(1, 0.3 * cm))

    # ── Breakdown table ──
    content.append(Paragraph("Score Breakdown", heading_style))

    table_data = [["Category", "Score", "Status", "Feedback"]]
    for c in criteria:
        table_data.append([
            Paragraph(f"{c.icon} {c.name}", body_style),
            Paragraph(f"{c.score}/10", body_style),
            Paragraph(status_label(c.status), body_style),
            Paragraph(c.feedback[:120] + ("..." if len(c.feedback) > 120 else ""), fix_style),
        ])

    col_widths = [4.5 * cm, 1.5 * cm, 1.8 * cm, 9.2 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Table styling
    ts = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6c63ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f9fafb"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ])

    # Color status cells
    for i, c in enumerate(criteria, start=1):
        sc = status_color(c.status)
        ts.add("TEXTCOLOR", (2, i), (2, i), sc)
        ts.add("FONTNAME", (2, i), (2, i), "Helvetica-Bold")

    table.setStyle(ts)
    content.append(table)
    content.append(Spacer(1, 0.5 * cm))

    # ── Fix Recommendations ──
    content.append(Paragraph("Fix Recommendations", heading_style))

    failed = [c for c in criteria if c.status == "fail"]
    warned = [c for c in criteria if c.status == "warn"]
    passed = [c for c in criteria if c.status == "pass"]

    for group_label, group, color_hex in [
        ("🔴 Fix Now", failed, "#ef4444"),
        ("🟡 Improve", warned, "#f59e0b"),
        ("🟢 Looking Good", passed, "#22c55e"),
    ]:
        if not group:
            continue
        content.append(Paragraph(
            f'<font color="{color_hex}"><b>{group_label}</b></font>',
            ParagraphStyle("GroupLabel", parent=styles["Normal"],
                           fontSize=11, spaceAfter=4, spaceBefore=10),
        ))
        for c in group:
            content.append(Paragraph(
                f"<b>{c.icon} {c.name}:</b> {c.fix}",
                fix_style,
            ))

    # ── Footer ──
    content.append(Spacer(1, 1 * cm))
    content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
    content.append(Paragraph(
        "Generated by ATS Resume Scorer · No data stored · 100% rule-based",
        ParagraphStyle("Footer", parent=styles["Normal"],
                       fontSize=8, textColor=colors.HexColor("#9ca3af"),
                       alignment=TA_CENTER, spaceBefore=8),
    ))

    doc.build(content)
    return buffer.getvalue()
