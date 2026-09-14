import io
from datetime import datetime
from typing import List, Dict, Any, Optional
import pytz

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasadas para numeración de páginas 'Página X de Y' y footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#334155"))
        
        # Línea divisoria de pie de página
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 38, 559, 38)

        footer_text = "© 2026 Lic. Prof. Alan Canto - taller de Economía para Jóvenes. Todos los derechos reservados."
        self.drawString(36, 26, footer_text)
        
        dev_text = "Desarrollado por Alan Canto ACDEV - @alancanto.insta"
        self.drawRightString(470, 26, dev_text)
        
        page_text = f"Pág. {self._pageNumber} de {page_count}"
        self.drawRightString(559, 26, page_text)
        self.restoreState()


def generate_game_audit_pdf(
    game_code: str,
    game_name: str,
    game_profile: str,
    game_status: str,
    created_at: datetime,
    finalized_at: Optional[datetime],
    bank_balance_tdl: float,
    ranked_teams: List[Dict[str, Any]],
    ledger_entries: List[Dict[str, Any]],
    contracts: List[Dict[str, Any]],
    timezone_name: str = "America/Montevideo"
) -> bytes:
    """
    Genera en memoria un documento PDF completo, vectorizado y canónico con la auditoría
    completa y el podio final de la partida Audacity.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=1
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6
    )
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b")
    )
    body_normal = ParagraphStyle(
        'BodyNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155")
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )

    story = []

    # Encabezado principal
    story.append(Paragraph("AUDACITY 2.0 · ECONOMÍA PARA JÓVENES", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("INFORME OFICIAL DE AUDITORÍA Y CIERRE DE PARTIDA", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=10))

    tz = pytz.timezone(timezone_name)
    now_str = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S %Z")
    created_str = created_at.replace(tzinfo=pytz.utc).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S") if created_at else "—"
    fin_str = finalized_at.replace(tzinfo=pytz.utc).astimezone(tz).strftime("%d/%m/%Y %H:%M:%S") if finalized_at else now_str

    # Ficha técnica de la partida
    meta_data = [
        [
            Paragraph(f"<b>Partida:</b> {game_name}", body_normal),
            Paragraph(f"<b>Código de Sala:</b> <font color='#1e3a8a'><b>{game_code}</b></font>", body_normal),
            Paragraph(f"<b>Perfil:</b> {game_profile.upper()}", body_normal)
        ],
        [
            Paragraph(f"<b>Inicio:</b> {created_str}", body_normal),
            Paragraph(f"<b>Cierre:</b> {fin_str}", body_normal),
            Paragraph(f"<b>Estado:</b> <font color='#166534'><b>{game_status.upper()}</b></font>", body_normal)
        ],
        [
            Paragraph(f"<b>Fondo Banco Central:</b> {bank_balance_tdl:,.2f} TDL", body_bold),
            Paragraph(f"<b>Equipos Participantes:</b> {len(ranked_teams)}", body_normal),
            Paragraph(f"<b>Fecha de Emisión:</b> {now_str}", body_normal)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[180, 180, 163])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # 1. Podio y Clasificación Final
    story.append(Paragraph("1. Podio y Estado Patrimonial Final de los Equipos", section_title))
    
    ranking_headers = ["Puesto", "Ficha", "Equipo", "Saldo Disp. (TDL)", "Saldo Res. (TDL)", "Saldo Nominal (TDL)", "Deuda Pend."]
    ranking_rows = [ranking_headers]
    for idx, r in enumerate(ranked_teams, 1):
        rank_val = r.get("rank", idx)
        puesto_str = f"1º (Ganador)" if rank_val == 1 else f"{rank_val}º"
        disp_cents = r.get('balance_available', int(r.get('balance_tdl', 0) * 100))
        res_cents = r.get('balance_reserved', int(r.get('reserved_tdl', 0) * 100))
        tot_cents = r.get('balance_total', int(r.get('total_tdl', 0) * 100))
        deb_cents = r.get('pending_debts', 0)

        disp_tdl = f"{disp_cents / 100:,.2f}"
        res_tdl = f"{res_cents / 100:,.2f}"
        tot_tdl = f"{tot_cents / 100:,.2f}"
        deb_tdl = f"{deb_cents / 100:,.2f}" if deb_cents > 0 else "0.00"
        
        ranking_rows.append([
            puesto_str,
            r.get("token_symbol", "★"),
            r.get("team_name", r.get("name", f"Equipo {idx}")),
            disp_tdl,
            res_tdl,
            tot_tdl,
            deb_tdl
        ])

    ranking_table = Table(ranking_rows, colWidths=[65, 30, 145, 75, 75, 75, 58])
    ranking_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (2, -1), 'LEFT'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]

    if len(ranking_rows) > 1:
        ranking_style.append(('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#fef3c7")))
    for i in range(2, len(ranking_rows)):
        if i % 2 == 1:
            ranking_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#f8fafc")))

    ranking_table.setStyle(TableStyle(ranking_style))
    story.append(ranking_table)
    story.append(Spacer(1, 14))

    # 2. Contratos y Compromisos Financieros
    if contracts:
        story.append(Paragraph("2. Registro de Contratos y Deudas Financieras", section_title))
        contract_headers = ["ID", "Tipo", "Acreedor", "Deudor", "Monto Orig.", "Amortizado", "Pendiente", "Estado"]
        contract_rows = [contract_headers]
        for c in contracts:
            contract_rows.append([
                str(c.get("id")),
                c.get("contract_type", "préstamo"),
                c.get("creditor_name", "Banco"),
                c.get("debtor_name", "Equipo"),
                f"{c.get('principal_amount', 0) / 100:,.2f}",
                f"{c.get('total_repaid', 0) / 100:,.2f}",
                f"{(c.get('principal_amount', 0) - c.get('total_repaid', 0)) / 100:,.2f}",
                c.get("status", "activo").upper()
            ])
        c_table = Table(contract_rows, colWidths=[25, 65, 85, 85, 65, 65, 65, 68])
        c_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#334155")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7.5),
            ('ALIGN', (0, 0), (3, -1), 'LEFT'),
            ('ALIGN', (4, 0), (-2, -1), 'RIGHT'),
            ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(c_table)
        story.append(Spacer(1, 14))

    # 3. Libro Diario Completo de Asientos y Auditoría
    story.append(Paragraph("3. Libro Diario Canónico de Auditoría (Trazabilidad Total)", section_title))
    story.append(Paragraph("Detalle cronológico de cada asiento contable, operación bancaria, reto y efecto registrado:", body_normal))
    story.append(Spacer(1, 6))

    ledger_headers = ["ID", "Hora", "Operación", "Monto TDL", "Origen", "Destino", "Motivo / Efecto Registrado", "Rev."]
    ledger_rows = [ledger_headers]

    for e in ledger_entries:
        amount_str = f"{e['amount'] / 100:,.2f}" if e.get('amount') else "0.00"
        rev_str = "SÍ" if e.get("is_reverted") else "NO"
        reason_p = Paragraph(str(e.get("reason", "")), table_cell)
        
        ledger_rows.append([
            str(e.get("id")),
            e.get("timestamp", ""),
            e.get("operation_type", "").replace("_", " "),
            amount_str,
            str(e.get("source_name") or e.get("source_id") or "—"),
            str(e.get("destination_name") or e.get("destination_id") or "—"),
            reason_p,
            rev_str
        ])

    ledger_table = Table(ledger_rows, colWidths=[25, 42, 75, 55, 60, 60, 180, 26])
    l_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('ALIGN', (0, 0), (2, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('ALIGN', (4, 0), (5, -1), 'LEFT'),
        ('ALIGN', (7, 0), (7, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]

    for idx in range(1, len(ledger_rows)):
        if idx % 2 == 0:
            l_style.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#f8fafc")))

    ledger_table.setStyle(TableStyle(l_style))
    story.append(ledger_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
