"""
Convert your risk-report JSON into a 1-page PDF.

pip install reportlab
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Union

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch


def _norm(x: Any) -> str:
    """Normalize text for PDF: remove newlines, collapse whitespace, keep safe characters."""
    if x is None:
        return ""
    s = str(x)
    # keep typography safe for ReportLab
    s = s.replace("\u2013", "-").replace("\u2014", "-")  # en/em dash
    s = s.replace("\u00d7", "x")  # multiplication sign
    s = s.replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def json_to_pdf(report: Dict[str, Any], out_path: str) -> str:
    """
    Build a single-page style PDF from the expected report JSON schema.

    report: dict with keys like title, subtitle, executive_summary, findings_overview_table,
            key_notable_examples, risk_implications, recommendations, footer
    out_path: output PDF path

    returns out_path
    """
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleStyle",
            parent=styles["Title"],
            fontSize=20,
            leading=22,
            spaceAfter=8,
            alignment=1,  # center
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubTitleStyle",
            parent=styles["Normal"],
            fontSize=12,
            leading=14,
            textColor=colors.grey,
            spaceAfter=12,
            alignment=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontSize=14,
            leading=16,
            spaceBefore=10,
            spaceAfter=8,
            textColor=colors.darkblue,
        )
    )
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=10, leading=12))
    styles.add(
        ParagraphStyle(
            name="Tiny",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.grey,
        )
    )

    # Use a larger page layout with slightly wider margins for readability
    doc = SimpleDocTemplate(
        out_path,
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    story: List[Any] = []

    # Header: colored bar + Title + Subtitle
    story.append(Spacer(1, 6))
    story.append(Paragraph(_norm(report.get("title", "")), styles["TitleStyle"]))
    subtitle = report.get("subtitle", {}) or {}
    subtitle_line = f"Category: {_norm(subtitle.get('category'))} | Timeframe: {_norm(subtitle.get('timeframe_reviewed'))}"
    story.append(Paragraph(subtitle_line, styles["SubTitleStyle"]))
    # Decorative divider
    story.append(Spacer(1, 4))
    story.append(Table([[""]], colWidths=[7.4 * inch], style=[("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2B6CB0"))], hAlign="CENTER"))
    story.append(Spacer(1, 8))

    # Executive Summary
    # Executive Summary - put inside a light box
    story.append(Paragraph("Executive Summary", styles["H2"]))
    exec_bullets = (report.get("executive_summary", {}) or {}).get("bullets", []) or []
    exec_bullets = [_norm(b) for b in exec_bullets][:4]
    summary_table = Table(
        [[ListFlowable([ListItem(Paragraph(b, styles["Small"]) ) for b in exec_bullets], bulletType="bullet")]],
        colWidths=[7.4 * inch],
        style=[
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F4FF")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BEE3F8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ],
    )
    story.append(summary_table)
    story.append(Spacer(1, 8))

    # Findings Overview Table
    story.append(Paragraph("Findings Overview", styles["H2"]))
    table_rows = report.get("findings_overview_table", []) or []
    table_data = [["Category", "Count", "Key Issues Identified (themes only)", "Timeframe"]]
    for row in table_rows:
        themes = ", ".join([_norm(t) for t in (row.get("key_issues_themes_only") or [])])
        table_data.append(
            [
                _norm(row.get("category", "")),
                str(row.get("count", "")),
                themes,
                _norm(row.get("timeframe", "")),
            ]
        )

    tbl = Table(table_data, colWidths=[1.2 * inch, 0.8 * inch, 4.2 * inch, 1.0 * inch])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6EEF8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1DCEB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(tbl)

    # Key Notable Examples
    story.append(Paragraph("Key Notable Examples", styles["H2"]))
    examples = report.get("key_notable_examples", {}) or {}

    def add_examples(label: str, items: Union[List[Dict[str, Any]], List[str], None], kind: str) -> List[Any]:
        # returns a flowable (list) for placing into a two-column table
        title_para = Paragraph(f"<b>{label}</b>", styles["Small"])
        bullets: List[str] = []
        urls: List[str] = []

        if not items:
            bullets = ["No material examples identified."]
        elif isinstance(items, list) and items and isinstance(items[0], str):
            bullets = [_norm(items[0])]
        else:
            for ex in list(items)[:2]:
                extra = ""
                if kind == "lawsuit" and ex.get("status"):
                    extra = f" (status: {_norm(ex.get('status'))})"
                if kind == "recall" and ex.get("scope"):
                    extra = f" (scope: {_norm(ex.get('scope'))})"
                bullets.append(_norm(ex.get("bullet", "")) + extra)
                if ex.get("source_urls"):
                    urls.append(_norm(ex["source_urls"][0]))

        flow = [title_para]
        flow.append(ListFlowable([ListItem(Paragraph(b, styles["Small"])) for b in bullets[:2]], bulletType="bullet"))
        if urls:
            flow.append(Paragraph("Sources: " + "; ".join(urls[:2]), styles["Tiny"]))
        return flow

    col1 = add_examples("Lawsuits", examples.get("lawsuits"), "lawsuit")
    col2 = add_examples("Recalls", examples.get("recalls"), "recall")
    col3 = add_examples("Warnings", examples.get("warnings"), "warning")

    # Put examples into a 2-column layout: left = lawsuits+recalls, right = warnings
    examples_table = Table(
        [[col1 + col2, col3]],
        colWidths=[4.0 * inch, 3.4 * inch],
        style=[("VALIGN", (0, 0), (-1, -1), "TOP")],
    )
    story.append(examples_table)

    # Risk Implications
    story.append(Paragraph("Risk Implications", styles["H2"]))
    imp_bullets = ((report.get("risk_implications", {}) or {}).get("bullets", []) or [])[:3]
    imp_bullets = [_norm(b) for b in imp_bullets]
    story.append(
        ListFlowable(
            [ListItem(Paragraph(b, styles["Small"]), leftIndent=12) for b in imp_bullets],
            bulletType="bullet",
            leftIndent=18,
        )
    )

    # Recommendations
    story.append(Paragraph("Recommendations", styles["H2"]))
    rec_bullets = ((report.get("recommendations", {}) or {}).get("bullets", []) or [])[:4]
    rec_bullets = [_norm(b) for b in rec_bullets]
    story.append(
        ListFlowable(
            [ListItem(Paragraph(b, styles["Small"]), leftIndent=12) for b in rec_bullets],
            bulletType="bullet",
            leftIndent=18,
        )
    )

    # Footer
    footer = report.get("footer", {}) or {}
    story.append(Spacer(1, 8))
    story.append(Paragraph(_norm(footer.get("methodology_line", "")), styles["Tiny"]))
    story.append(Paragraph(_norm(footer.get("disclaimer_line", "")), styles["Tiny"]))

    doc.build(story)
    return out_path


