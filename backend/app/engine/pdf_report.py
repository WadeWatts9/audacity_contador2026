import io
import os
import html
from datetime import datetime
from typing import List, Dict, Any, Optional
import pytz

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
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


TOKEN_IMAGE_MAP = {
    # Símbolos emoji
    "🐓": "gallo.png",
    "🦁": "leon.png",
    "🐕": "perro.png",
    "✋": "mano.png",
    "★": "estrella.png",
    "⭐": "estrella.png",
    "💎": "diamante.png",
    "🚗": "auto.png",
    "🎩": "sombrero.png",
    "🐷": "cerdo.png",
    "🏦": "banco.png",
    # Palabras clave en nombres de equipo o animales
    "gallo": "gallo.png",
    "leon": "leon.png",
    "león": "leon.png",
    "perro": "perro.png",
    "mano": "mano.png",
    "estrella": "estrella.png",
    "diamante": "diamante.png",
    "auto": "auto.png",
    "sombrero": "sombrero.png",
    "cerdo": "cerdo.png",
    "banco": "banco.png",
}

def get_token_flowable(token_symbol: str, team_name: str, fallback_style: ParagraphStyle):
    """
    Retorna un Flowable de imagen PNG para la ficha del equipo sin depender
    de fuentes o emojis del sistema operativo. Si no encuentra la imagen, retorna Paragraph seguro.
    """
    static_tokens_dir = os.path.join(os.path.dirname(__file__), "..", "static", "tokens")
    
    img_name = None
    if token_symbol and token_symbol in TOKEN_IMAGE_MAP:
        img_name = TOKEN_IMAGE_MAP[token_symbol]
    else:
        for key, fname in TOKEN_IMAGE_MAP.items():
            if key in (team_name or "").lower() or key in (token_symbol or "").lower():
                img_name = fname
                break

    if img_name:
        img_path = os.path.abspath(os.path.join(static_tokens_dir, img_name))
        if os.path.exists(img_path):
            return RLImage(img_path, width=15, height=15)

    clean_sym = html.escape(str(token_symbol or "★"))
    return Paragraph(clean_sym, fallback_style)


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
    completa y el podio final de la partida Audacity, adaptando anchos y envolviendo celdas
    en Paragraphs para que ningún texto se superponga jamás.
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
        fontSize=12,
        leading=16,
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

    # Estilos de encabezados de tablas
    th_white = ParagraphStyle(
        'ThWhite',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.white,
        alignment=1
    )
    th_white_left = ParagraphStyle(
        'ThWhiteLeft',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.white,
        alignment=0
    )
    th_white_right = ParagraphStyle(
        'ThWhiteRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.white,
        alignment=2
    )

    # Estilos de celdas estándar
    td_left = ParagraphStyle(
        'TdLeft',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1e293b"),
        alignment=0
    )
    td_bold_left = ParagraphStyle(
        'TdBoldLeft',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0f172a"),
        alignment=0
    )
    td_center = ParagraphStyle(
        'TdCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1e293b"),
        alignment=1
    )
    td_bold_center = ParagraphStyle(
        'TdBoldCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0f172a"),
        alignment=1
    )
    td_right = ParagraphStyle(
        'TdRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1e293b"),
        alignment=2
    )
    td_bold_right = ParagraphStyle(
        'TdBoldRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0f172a"),
        alignment=2
    )

    # Estilos para Libro Diario
    td_ledger = ParagraphStyle(
        'TdLedger',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#1e293b"),
        alignment=0
    )
    td_ledger_bold = ParagraphStyle(
        'TdLedgerBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#0f172a"),
        alignment=0
    )
    td_ledger_right = ParagraphStyle(
        'TdLedgerRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#1e293b"),
        alignment=2
    )
    td_ledger_center = ParagraphStyle(
        'TdLedgerCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#1e293b"),
        alignment=1
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
            Paragraph(f"<b>Partida:</b> {html.escape(game_name)}", body_normal),
            Paragraph(f"<b>Código de Sala:</b> <font color='#1e3a8a'><b>{html.escape(game_code)}</b></font>", body_normal),
            Paragraph(f"<b>Perfil:</b> {html.escape(game_profile.upper())}", body_normal)
        ],
        [
            Paragraph(f"<b>Inicio:</b> {created_str}", body_normal),
            Paragraph(f"<b>Cierre:</b> {fin_str}", body_normal),
            Paragraph(f"<b>Estado:</b> <font color='#166534'><b>{html.escape(game_status.upper())}</b></font>", body_normal)
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
    
    ranking_headers = [
        Paragraph("<b>Puesto</b>", th_white),
        Paragraph("<b>Ficha</b>", th_white),
        Paragraph("<b>Equipo</b>", th_white_left),
        Paragraph("<b>Saldo Disp.<br/>(TDL)</b>", th_white_right),
        Paragraph("<b>Saldo Res.<br/>(TDL)</b>", th_white_right),
        Paragraph("<b>Saldo Total<br/>(TDL)</b>", th_white_right),
        Paragraph("<b>Deuda Pend.<br/>(TDL)</b>", th_white_right),
    ]
    ranking_rows = [ranking_headers]
    for idx, r in enumerate(ranked_teams, 1):
        rank_val = r.get("rank", r.get("position", idx))
        puesto_str = "1º (Ganador)" if rank_val == 1 else f"{rank_val}º"
        
        if 'balance_available' in r:
            disp_cents = r.get('balance_available', 0)
            res_cents = r.get('balance_reserved', 0)
            tot_cents = r.get('balance_total', 0)
        else:
            disp_cents = int(r.get('balance_tdl', 0) * 100)
            res_cents = int(r.get('reserved_tdl', 0) * 100)
            tot_cents = int(r.get('total_tdl', 0) * 100)
            
        deb_cents = r.get('pending_debts', 0)

        disp_tdl = f"{disp_cents / 100:,.2f}"
        res_tdl = f"{res_cents / 100:,.2f}"
        tot_tdl = f"{tot_cents / 100:,.2f}"
        deb_tdl = f"{deb_cents / 100:,.2f}" if deb_cents > 0 else "0.00"

        team_name = str(r.get("team_name") or r.get("name") or f"Equipo {idx}")
        token_sym = str(r.get("token_symbol") or r.get("symbol") or "★")
        token_flowable = get_token_flowable(token_sym, team_name, td_center)

        puesto_style = td_bold_center if rank_val == 1 else td_center
        ranking_rows.append([
            Paragraph(puesto_str, puesto_style),
            token_flowable,
            Paragraph(html.escape(team_name), td_bold_left),
            Paragraph(disp_tdl, td_right),
            Paragraph(res_tdl, td_right),
            Paragraph(tot_tdl, td_bold_right),
            Paragraph(deb_tdl, td_right)
        ])

    ranking_table = Table(ranking_rows, colWidths=[48, 28, 125, 80, 80, 82, 80])
    ranking_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
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
        contract_headers = [
            Paragraph("<b>ID</b>", th_white),
            Paragraph("<b>Tipo</b>", th_white_left),
            Paragraph("<b>Acreedor</b>", th_white_left),
            Paragraph("<b>Deudor</b>", th_white_left),
            Paragraph("<b>Monto Orig.<br/>(TDL)</b>", th_white_right),
            Paragraph("<b>Amortizado<br/>(TDL)</b>", th_white_right),
            Paragraph("<b>Pendiente<br/>(TDL)</b>", th_white_right),
            Paragraph("<b>Estado</b>", th_white),
        ]
        contract_rows = [contract_headers]
        for c in contracts:
            orig = c.get('principal_amount', 0)
            rep = c.get('total_repaid', 0)
            pend = orig - rep
            contract_rows.append([
                Paragraph(str(c.get("id")), td_center),
                Paragraph(html.escape(str(c.get("contract_type", "préstamo")).title()), td_left),
                Paragraph(html.escape(str(c.get("creditor_name", "Banco"))), td_left),
                Paragraph(html.escape(str(c.get("debtor_name", "Equipo"))), td_left),
                Paragraph(f"{orig / 100:,.2f}", td_right),
                Paragraph(f"{rep / 100:,.2f}", td_right),
                Paragraph(f"{pend / 100:,.2f}", td_bold_right),
                Paragraph(html.escape(str(c.get("status", "activo")).upper()), td_center),
            ])
        c_table = Table(contract_rows, colWidths=[25, 60, 85, 85, 72, 72, 72, 52])
        c_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#334155")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(c_table)
        story.append(Spacer(1, 14))

    # 3. Libro Diario Completo de Asientos y Auditoría
    story.append(Paragraph("3. Libro Diario Canónico de Auditoría (Trazabilidad Total)", section_title))
    story.append(Paragraph("Detalle cronológico de cada asiento contable, operación bancaria, reto y efecto registrado:", body_normal))
    story.append(Spacer(1, 6))

    ledger_headers = [
        Paragraph("<b>ID</b>", th_white),
        Paragraph("<b>Hora</b>", th_white),
        Paragraph("<b>Operación</b>", th_white_left),
        Paragraph("<b>Monto<br/>(TDL)</b>", th_white_right),
        Paragraph("<b>Origen</b>", th_white_left),
        Paragraph("<b>Destino</b>", th_white_left),
        Paragraph("<b>Motivo / Efecto Registrado</b>", th_white_left),
        Paragraph("<b>Rev.</b>", th_white),
    ]
    ledger_rows = [ledger_headers]

    for e in ledger_entries:
        if 'amount' in e:
            amount_cents = e.get('amount') or 0
        else:
            amount_cents = int((e.get('amount_tdl') or 0) * 100)
        amount_str = f"{amount_cents / 100:,.2f}"

        time_str = ""
        if e.get("timestamp"):
            time_str = str(e.get("timestamp"))
        elif e.get("created_at"):
            time_val = e.get("created_at")
            if isinstance(time_val, datetime):
                time_str = time_val.strftime("%H:%M:%S")
            else:
                time_str = str(time_val)[11:19]

        op_raw = str(e.get("operation_type", "")).replace("_", " ").title()
        if len(op_raw) > 22:
            op_raw = op_raw[:20] + "..."

        src_raw = str(e.get("source_name") or e.get("source") or e.get("source_id") or "—")
        dst_raw = str(e.get("destination_name") or e.get("destination") or e.get("target") or e.get("destination_id") or "—")
        if len(src_raw) > 24:
            src_raw = src_raw[:22] + "..."
        if len(dst_raw) > 24:
            dst_raw = dst_raw[:22] + "..."

        reason_raw = str(e.get("reason") or e.get("description") or "—").strip()
        if len(reason_raw) > 140:
            reason_raw = reason_raw[:137] + "..."

        rev_str = "SÍ" if e.get("is_reverted") else "NO"

        ledger_rows.append([
            Paragraph(str(e.get("id", "—")), td_ledger_center),
            Paragraph(html.escape(time_str), td_ledger_center),
            Paragraph(html.escape(op_raw), td_ledger_bold),
            Paragraph(amount_str, td_ledger_right),
            Paragraph(html.escape(src_raw), td_ledger),
            Paragraph(html.escape(dst_raw), td_ledger),
            Paragraph(html.escape(reason_raw), td_ledger),
            Paragraph(rev_str, td_ledger_center),
        ])

    ledger_table = Table(ledger_rows, colWidths=[22, 38, 68, 55, 66, 66, 184, 24])
    l_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0f172a")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]

    for idx in range(1, len(ledger_rows)):
        if idx % 2 == 0:
            l_style.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#f8fafc")))

    ledger_table.setStyle(TableStyle(l_style))
    story.append(ledger_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
