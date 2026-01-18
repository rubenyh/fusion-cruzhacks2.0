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
            fontSize=16,
            leading=18,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubTitleStyle",
            parent=styles["Normal"],
            fontSize=10,
            leading=12,
            textColor=colors.grey,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontSize=12,
            leading=14,
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, leading=11))
    styles.add(
        ParagraphStyle(
            name="Tiny",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.grey,
        )
    )

    doc = SimpleDocTemplate(
        out_path,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.6 * inch,
    )

    story: List[Any] = []

    # Title + Subtitle
    story.append(Paragraph(_norm(report.get("title", "")), styles["TitleStyle"]))
    subtitle = report.get("subtitle", {}) or {}
    subtitle_line = f"Category: {_norm(subtitle.get('category'))} | Timeframe: {_norm(subtitle.get('timeframe_reviewed'))}"
    story.append(Paragraph(subtitle_line, styles["SubTitleStyle"]))

    # Executive Summary
    story.append(Paragraph("Executive Summary", styles["H2"]))
    exec_bullets = (report.get("executive_summary", {}) or {}).get("bullets", []) or []
    exec_bullets = [_norm(b) for b in exec_bullets][:4]
    story.append(
        ListFlowable(
            [ListItem(Paragraph(b, styles["Small"]), leftIndent=12) for b in exec_bullets],
            bulletType="bullet",
            leftIndent=18,
        )
    )

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

    tbl = Table(table_data, colWidths=[1.0 * inch, 0.6 * inch, 3.7 * inch, 1.0 * inch])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(tbl)

    # Key Notable Examples
    story.append(Paragraph("Key Notable Examples", styles["H2"]))
    examples = report.get("key_notable_examples", {}) or {}

    def add_examples(label: str, items: Union[List[Dict[str, Any]], List[str], None], kind: str) -> None:
        story.append(Paragraph(f"{label}:", styles["Small"]))

        bullets: List[str] = []
        urls: List[str] = []

        if not items:
            bullets = ["No material examples identified."]
        elif isinstance(items, list) and items and isinstance(items[0], str):
            # Some generators output ["No material examples identified."] as a list of strings
            bullets = [_norm(items[0])]
        else:
            # list[dict]
            for ex in list(items)[:2]:
                extra = ""
                if kind == "lawsuit" and ex.get("status"):
                    extra = f" (status: {_norm(ex.get('status'))})"
                if kind == "recall" and ex.get("scope"):
                    extra = f" (scope: {_norm(ex.get('scope'))})"
                bullets.append(_norm(ex.get("bullet", "")) + extra)
                if ex.get("source_urls"):
                    urls.append(_norm(ex["source_urls"][0]))

        story.append(
            ListFlowable(
                [ListItem(Paragraph(b, styles["Small"]), leftIndent=12) for b in bullets[:2]],
                bulletType="bullet",
                leftIndent=18,
            )
        )
        if urls:
            story.append(Paragraph("Sources: " + "; ".join(urls[:2]), styles["Tiny"]))

    add_examples("Lawsuits", examples.get("lawsuits"), "lawsuit")
    add_examples("Recalls", examples.get("recalls"), "recall")
    add_examples("Warnings", examples.get("warnings"), "warning")

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


