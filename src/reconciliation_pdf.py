"""Create a human-readable PDF from a validated reconciliation report."""

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from html import escape
from io import BytesIO
import json
from pathlib import Path
from typing import Any

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PALETTE = {
    "blue": colors.HexColor("#3D6EA7"),
    "ink": colors.HexColor("#101828"),
    "muted": colors.HexColor("#595959"),
    "border": colors.HexColor("#D9D9D9"),
    "surface": colors.HexColor("#F5F7FA"),
}

CATEGORY_INFO = (
    (
        "exact_matches",
        "Coincidencias exactas",
        "Cruces confirmados por las reglas deterministas implementadas.",
    ),
    (
        "fuzzy_fee_matches",
        "Coincidencias de tarifa",
        "Cruces compatibles con las reglas PoC de tarifa y liquidación.",
    ),
    (
        "reconciliation_exceptions",
        "Excepciones",
        "Diferencias o relaciones no resueltas; requieren revisión de evidencia.",
    ),
    (
        "orphan_transactions",
        "Posibles transacciones huérfanas",
        "Hallazgos reportados como huérfanos. La falta de contraparte en un lote "
        "parcial no demuestra por sí sola que una transacción sea huérfana.",
    ),
    (
        "compliance_alerts",
        "Alertas AML ilustrativas",
        "Alertas de reglas de prueba, no una conclusión de delito ni política "
        "regulatoria aprobada. Requieren revisión humana.",
    ),
)


def _register_fonts() -> None:
    font_dir = Path(reportlab.__file__).parent / "fonts"
    registered_fonts = set(pdfmetrics.getRegisteredFontNames())
    if "Vera" not in registered_fonts:
        pdfmetrics.registerFont(TTFont("Vera", str(font_dir / "Vera.ttf")))
    if "Vera-Bold" not in registered_fonts:
        pdfmetrics.registerFont(TTFont("Vera-Bold", str(font_dir / "VeraBd.ttf")))


def _value_text(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if value is None:
        return "No especificado"
    return str(value)


def _paragraph(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(_value_text(text)), style)


def _validate_report(report: Mapping[str, Any]) -> None:
    if report.get("report_type") != "financial_reconciliation_audit":
        raise ValueError("El reporte no tiene un tipo de conciliación reconocido.")
    if not isinstance(report.get("summary"), Mapping):
        raise ValueError("El reporte no contiene un resumen válido.")
    for key, _, _ in CATEGORY_INFO:
        if not isinstance(report.get(key), list):
            raise ValueError(f"La sección '{key}' no contiene una lista válida.")


def _draw_page(canvas: Any, document: SimpleDocTemplate) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(PALETTE["border"])
    canvas.line(
        document.leftMargin,
        height - 17 * mm,
        width - document.rightMargin,
        height - 17 * mm,
    )
    canvas.setFont("Vera-Bold", 8)
    canvas.setFillColor(PALETTE["blue"])
    canvas.drawString(document.leftMargin, height - 13 * mm, "AGENT BANCA · INFORME DE PRUEBA")
    canvas.setFont("Vera", 8)
    canvas.setFillColor(PALETTE["muted"])
    canvas.drawRightString(width - document.rightMargin, 11 * mm, f"Página {document.page}")
    canvas.restoreState()


def build_reconciliation_pdf(
    report: Mapping[str, Any],
    sources: Sequence[str] = (),
) -> bytes:
    """Render a concise Spanish explanation with report evidence and counts."""
    _validate_report(report)
    _register_fonts()
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=23 * mm,
        bottomMargin=18 * mm,
        title="Informe de conciliación - Agent Concilation",
        author="Agent Concilation",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Vera-Bold",
        fontSize=20,
        leading=25,
        alignment=TA_LEFT,
        textColor=PALETTE["ink"],
        spaceAfter=5 * mm,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Vera-Bold",
        fontSize=13,
        leading=17,
        textColor=PALETTE["ink"],
        spaceBefore=5 * mm,
        spaceAfter=2 * mm,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Vera",
        fontSize=9,
        leading=13,
        textColor=PALETTE["ink"],
        spaceAfter=2 * mm,
        wordWrap="CJK",
    )
    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=body_style,
        fontSize=8,
        leading=11,
        textColor=PALETTE["muted"],
    )
    item_style = ParagraphStyle(
        "FindingTitle",
        parent=body_style,
        fontName="Vera-Bold",
        fontSize=9,
        leading=12,
        spaceBefore=2 * mm,
        spaceAfter=1 * mm,
    )
    table_style = ParagraphStyle(
        "SummaryCell",
        parent=body_style,
        fontSize=8,
        leading=11,
        spaceAfter=0,
    )

    story = [
        _paragraph("Informe de conciliación", title_style),
        _paragraph(
            "Resultado explicativo del PoC. Resume los conteos y presenta las "
            "referencias observables del reporte; no reemplaza la revisión "
            "humana ni constituye una decisión contable o regulatoria.",
            body_style,
        ),
    ]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(_paragraph(f"Generado: {generated_at}", meta_style))
    if sources:
        story.append(_paragraph("Archivos: " + " · ".join(sources), meta_style))

    summary = report["summary"]
    summary_rows = [[
        _paragraph("Sección", table_style),
        _paragraph("Cantidad", table_style),
        _paragraph("Qué significa", table_style),
    ]]
    for key, label, explanation in CATEGORY_INFO:
        summary_rows.append(
            [
                _paragraph(label, table_style),
                _paragraph(summary.get(key, 0), table_style),
                _paragraph(explanation, table_style),
            ]
        )
    summary_table = Table(
        summary_rows,
        colWidths=(48 * mm, 20 * mm, 106 * mm),
        repeatRows=1,
        hAlign="LEFT",
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PALETTE["surface"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), PALETTE["ink"]),
                ("FONTNAME", (0, 0), (-1, 0), "Vera-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, PALETTE["border"]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([Spacer(1, 3 * mm), summary_table])

    for key, label, explanation in CATEGORY_INFO:
        items = report[key]
        story.append(_paragraph(f"{label} ({len(items)})", heading_style))
        story.append(_paragraph(explanation, body_style))
        if not items:
            story.append(_paragraph("No hay elementos en esta sección.", meta_style))
            continue
        for item in items:
            if not isinstance(item, Mapping):
                raise ValueError(f"Un elemento de '{key}' no es un objeto válido.")
            if key == "compliance_alerts":
                identifier = item.get("rule_id", "Alerta")
                refs = item.get("record_ids", [])
                payout_ids = item.get("payout_ids", [])
                details = [
                    ("Severidad reportada", item.get("severity")),
                    ("Referencias", refs),
                    ("Payouts", payout_ids),
                    ("Descripción", item.get("description")),
                    (
                        "Revisión humana requerida",
                        item.get("human_review_required"),
                    ),
                ]
            else:
                identifier = item.get("payout_id") or "Sin payout_id"
                details = [
                    ("Referencias de origen", item.get("record_ids", [])),
                    ("Estado", item.get("status")),
                    ("Motivo", item.get("reason")),
                    ("Detalles", item.get("details", {})),
                ]
            story.append(_paragraph(f"{label}: {identifier}", item_style))
            for detail_label, value in details:
                story.append(
                    _paragraph(f"{detail_label}: {_value_text(value)}", body_style)
                )

    story.append(Spacer(1, 4 * mm))
    story.append(
        _paragraph(
            "Alcance: este PoC procesa esquemas JSON sintéticos de banco, "
            "pasarela y libro mayor. No demuestra soporte para formatos "
            "oficiales de banco central, procesamiento masivo ni uso en producción.",
            meta_style,
        )
    )
    document.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
    return output.getvalue()
