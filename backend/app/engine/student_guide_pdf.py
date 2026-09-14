import io
import os
import html
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage, KeepTogether
)
from reportlab.pdfgen import canvas

class StudentGuideNumberedCanvas(canvas.Canvas):
    """Canvas de dos pasadas para pie de página canónico y numeración 'Pág. X de Y'."""
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
        self.line(36, 36, 559, 36)

        footer_text = "© 2026 Lic. Prof. Alan Canto - taller de Economía para Jóvenes. Todos los derechos reservados."
        self.drawString(36, 24, footer_text)
        
        dev_text = "Desarrollado por Alan Canto ACDEV - @alancanto.insta"
        self.drawRightString(470, 24, dev_text)
        
        page_text = f"Pág. {self._pageNumber} de {page_count}"
        self.drawRightString(559, 24, page_text)
        self.restoreState()


def get_token_img(img_name: str, width: int = 16, height: int = 16):
    """Obtiene flowable de imagen para token Twemoji."""
    static_tokens_dir = os.path.join(os.path.dirname(__file__), "..", "static", "tokens")
    path = os.path.abspath(os.path.join(static_tokens_dir, img_name))
    if os.path.exists(path):
        return RLImage(path, width=width, height=height)
    return Paragraph("★", ParagraphStyle('Sym', fontSize=10, alignment=1))


def generate_student_guide_pdf() -> bytes:
    """Genera la Guía de Uso del Estudiante en formato PDF A4 de 2 páginas."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=44
    )

    styles = getSampleStyleSheet()

    # Estilos tipográficos
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=1
    )
    section_heading = ParagraphStyle(
        'SecHead',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=8,
        spaceAfter=4
    )
    body_text = ParagraphStyle(
        'BodyTxt',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155")
    )
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0f172a")
    )
    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )
    td_style = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1e293b")
    )
    td_bold = ParagraphStyle(
        'TDBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0f172a")
    )
    card_title = ParagraphStyle(
        'CardTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )
    card_desc = ParagraphStyle(
        'CardDesc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10,
        textColor=colors.HexColor("#475569")
    )

    story = []

    # ==========================================
    # PÁGINA 1: IDENTIFICACIÓN Y ESTADO FINANCIERO
    # ==========================================

    story.append(Paragraph("AUDACITY 2.0 · ECONOMÍA PARA JÓVENES", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("GUÍA RÁPIDA DEL ESTUDIANTE · ROL: CONTADOR DEL EQUIPO", subtitle_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=6))

    # Bienvenida / Rol
    welcome_box = [
        [
            Paragraph(
                "<b>¡Bienvenido al equipo contable de Audacity!</b><br/>"
                "En esta simulación económica, eres el <b>Contador Oficial</b> de tu equipo. Tu misión fundamental es custodiar "
                "los fondos en <b>TDL (Talentos de Dinero)</b>, supervisar cada cobro o pago del Banco Central, auditar las transferencias "
                "con otros equipos y asesorar a tus compañeros para maximizar el patrimonio final de la empresa.",
                body_text
            )
        ]
    ]
    w_table = Table(welcome_box, colWidths=[523])
    w_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#93c5fd")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(w_table)
    story.append(Spacer(1, 8))

    # Sección 1: Inicio de Sesión
    story.append(Paragraph("1. ¿Cómo ingresar a tu Panel de Contador?", section_heading))
    story.append(Paragraph(
        "1. Abrí el navegador web (Google Chrome, Firefox, Safari o Edge) e ingresá a la dirección indicada por el docente (ej. <code>http://192.168.1.XX:3003</code> o el enlace del aula).<br/>"
        "2. En la pantalla de ingreso, seleccioná o escribí tu <b>Usuario</b> y tu <b>Contraseña con PIN secreto</b> entregada por el docente.",
        body_text
    ))
    story.append(Spacer(1, 6))

    # Tabla de Equipos y Usuarios
    teams_table_data = [
        [
            Paragraph("<b>Ficha</b>", th_style),
            Paragraph("<b>Equipo</b>", th_style),
            Paragraph("<b>Usuario del Contador</b>", th_style),
            Paragraph("<b>Formato Contraseña (PIN Único)</b>", th_style),
            Paragraph("<b>Color Distintivo</b>", th_style)
        ],
        # Genially
        [get_token_img("gallo.png"), Paragraph("Contador Gallo", td_bold), Paragraph("<code>gallo_contador</code>", td_style), Paragraph("<code>contadorgallo####</code>", td_style), Paragraph("Celeste Suave", td_style)],
        [get_token_img("leon.png"), Paragraph("Contador León", td_bold), Paragraph("<code>leon_contador</code>", td_style), Paragraph("<code>contadorleon####</code>", td_style), Paragraph("Amarillo Dorado", td_style)],
        [get_token_img("perro.png"), Paragraph("Contador Perro", td_bold), Paragraph("<code>perro_contador</code>", td_style), Paragraph("<code>contadorperro####</code>", td_style), Paragraph("Rosa Coral", td_style)],
        [get_token_img("mano.png"), Paragraph("Contador Mano", td_bold), Paragraph("<code>mano_contador</code>", td_style), Paragraph("<code>contadormano####</code>", td_style), Paragraph("Verde Claro", td_style)],
        [get_token_img("estrella.png"), Paragraph("Contador Estrella", td_bold), Paragraph("<code>estrella_contador</code>", td_style), Paragraph("<code>contadorestrella####</code>", td_style), Paragraph("Violeta Lavanda", td_style)],
        # Prezi
        [get_token_img("diamante.png"), Paragraph("Contador Diamante", td_bold), Paragraph("<code>diamante_contador</code>", td_style), Paragraph("<code>contadordiamante####</code>", td_style), Paragraph("Azul Marino", td_style)],
        [get_token_img("auto.png"), Paragraph("Contador Auto", td_bold), Paragraph("<code>auto_contador</code>", td_style), Paragraph("<code>contadorauto####</code>", td_style), Paragraph("Verde Bosque", td_style)],
        [get_token_img("sombrero.png"), Paragraph("Contador Sombrero", td_bold), Paragraph("<code>sombrero_contador</code>", td_style), Paragraph("<code>contadorsombrero####</code>", td_style), Paragraph("Dorado Oscuro", td_style)],
        [get_token_img("cerdo.png"), Paragraph("Contador Cerdo", td_bold), Paragraph("<code>cerdo_contador</code>", td_style), Paragraph("<code>contadorcerdo####</code>", td_style), Paragraph("Magenta", td_style)],
    ]
    t_table = Table(teams_table_data, colWidths=[36, 115, 120, 162, 90])
    t_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    for i in range(1, len(teams_table_data)):
        if i % 2 == 0:
            t_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor("#f8fafc"))]))
    story.append(t_table)
    story.append(Spacer(1, 8))

    # Sección 2: Estructura Patrimonial
    story.append(Paragraph("2. ¿Qué significan los Saldos de tu Empresa?", section_heading))
    story.append(Paragraph(
        "En el centro de tu pantalla verás los 4 indicadores financieros más importantes. Como contador, debés dominarlos:",
        body_text
    ))
    story.append(Spacer(1, 5))

    balances_data = [
        [
            Paragraph("<b>💰 Saldo Disponible (TDL)</b>", card_title),
            Paragraph("<b>🔒 Saldo Reservado (TDL)</b>", card_title),
        ],
        [
            Paragraph("Es tu <b>dinero líquido e inmediato</b>. Se utiliza para pagar compras, tarifas de tarjetas, multas del Banco o transferir a otros equipos. <i>¡Nunca debe quedar en negativo!</i>", card_desc),
            Paragraph("Dinero inmovilizado temporalmente (por ejemplo ahorros programados o garantías). No podés gastarlo de inmediato, pero <b>suma a tu patrimonio</b> y genera rendimientos.", card_desc),
        ],
        [
            Paragraph("<b>🏆 Saldo Total (Patrimonio Neto)</b>", card_title),
            Paragraph("<b>📜 Deudas / Préstamos Activos</b>", card_title),
        ],
        [
            Paragraph("<b>Suma de Disponible + Reservado</b>. Este es el indicador definitivo de riqueza de tu empresa. <b>¡El equipo con mayor Saldo Total gana la partida al cierre!</b>", card_desc),
            Paragraph("Monto pendiente de amortización con el Banco Central o acreedores. Si tu equipo contrae deudas, deberán pagarlas en cuotas para no perder puntos en el podio final.", card_desc),
        ]
    ]
    b_table = Table(balances_data, colWidths=[256, 256])
    b_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 1), colors.HexColor("#f0fdf4")),
        ('BOX', (0, 0), (0, 1), 1, colors.HexColor("#86efac")),
        ('BACKGROUND', (1, 0), (1, 1), colors.HexColor("#eff6ff")),
        ('BOX', (1, 0), (1, 1), 1, colors.HexColor("#93c5fd")),
        ('BACKGROUND', (0, 2), (0, 3), colors.HexColor("#fefce8")),
        ('BOX', (0, 2), (0, 3), 1, colors.HexColor("#fde047")),
        ('BACKGROUND', (1, 2), (1, 3), colors.HexColor("#fef2f2")),
        ('BOX', (1, 2), (1, 3), 1, colors.HexColor("#fca5a5")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(b_table)

    # Forzar salto a página 2
    story.append(Spacer(1, 14))

    # ==========================================
    # PÁGINA 2: OPERACIONES, REGLAS Y BUENAS PRÁCTICAS
    # ==========================================

    story.append(Paragraph("3. Pestañas y Herramientas de tu Tablero", section_heading))

    features_data = [
        [
            Paragraph("<b>🎲 Pestaña: Tablero y Turnos</b>", card_title),
            Paragraph("Te muestra la casilla actual del tablero donde cayó la ficha, el valor del dado y el estado del turno. Si tu equipo cayó en una casilla de 'Pierde Turno' o posee una póliza de seguro activa (E11), aquí verás el aviso en color verde o rojo.", card_desc)
        ],
        [
            Paragraph("<b>❓ Pestaña: Preguntas y Retos (P01 - P15)</b>", card_title),
            Paragraph("Te permite ver qué números de tarjetas de preguntas económicas ya salieron y cuáles aún siguen en el mazo. <i>Por ética y juego limpio, el contenido de la pregunta sólo se revela cuando el docente la extrae en clase.</i>", card_desc)
        ],
        [
            Paragraph("<b>📖 Pestaña: Libro Diario Contable</b>", card_title),
            Paragraph("Cada transacción (ingreso de fondos, cobro bancario, transferencia o ajuste) queda grabada con número de asiento, hora exacta, monto y motivo. Si detectás algún error, podés pedirle al docente que revise el asiento.", card_desc)
        ]
    ]
    f_table = Table(features_data, colWidths=[150, 363])
    f_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(f_table)
    story.append(Spacer(1, 8))

    # Sección 4: El Código del Buen Contador
    story.append(Paragraph("4. Las 4 Reglas de Oro del Contador Exitoso", section_heading))

    rules_data = [
        [
            Paragraph("<b>1. Trazabilidad Total</b>", body_bold),
            Paragraph("Cada TDL cuenta. Mirá tu Libro Diario después de cada turno para confirmar que los premios se acreditaron y las compras se debitaron de forma correcta.", body_text)
        ],
        [
            Paragraph("<b>2. Cuidado con el Endeudamiento</b>", body_bold),
            Paragraph("Pedir un crédito al Banco Central te da liquidez hoy, pero las cuotas vencerán en turnos futuros. No pidas préstamos si no tenés un plan claro para pagarlos.", body_text)
        ],
        [
            Paragraph("<b>3. Ahorro e Inversión Estratégica</b>", body_bold),
            Paragraph("Aprovechá las tarjetas de Ahorro Programado e Inversión de Futuro. Proteger tu dinero en el Saldo Reservado te blinda ante eventos de inflación o pérdidas.", body_text)
        ],
        [
            Paragraph("<b>4. Comunicación en Equipo</b>", body_bold),
            Paragraph("Sos el asesor económico de tu grupo. Avisales a tus compañeros cuánto pueden gastar antes de que tomen decisiones impulsivas en el tablero.", body_text)
        ]
    ]
    r_table = Table(rules_data, colWidths=[145, 368])
    r_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor("#ffffff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(r_table)
    story.append(Spacer(1, 8))

    # Sección 5: Preguntas Frecuentes
    story.append(Paragraph("5. Preguntas Frecuentes del Contador", section_heading))

    faq_data = [
        [
            Paragraph("<b>¿Qué hago si se debitó un importe incorrecto en mi cuenta?</b>", body_bold),
        ],
        [
            Paragraph("Avisale inmediatamente al profesor (Banco Central). El docente tiene una herramienta de <i>Deshacer Operación</i> que revierte el asiento al instante y restablece los fondos.", body_text),
        ],
        [
            Paragraph("<b>¿Puedo transferir dinero a otro equipo del aula?</b>", body_bold),
        ],
        [
            Paragraph("Sí, siempre que haya un acuerdo comercial o intercambio entre empresas. El Banco Central autorizará y registrará la transferencia directa entre ambas cuentas.", body_text),
        ],
        [
            Paragraph("<b>¿Cómo se define el equipo ganador de la partida?</b>", body_bold),
        ],
        [
            Paragraph("Al finalizar el juego, el docente oprime el botón <b>FIN DE PARTIDA</b>. El sistema congela el tablero, deduce automáticamente deudas impagas y consagra ganador al equipo con mayor <b>Saldo Total (TDL)</b>, emitiendo el Informe Oficial de Auditoría en PDF.", body_text),
        ]
    ]
    faq_table = Table(faq_data, colWidths=[523])
    faq_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 2), (0, 2), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 4), (0, 4), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(faq_table)

    doc.build(story, canvasmaker=StudentGuideNumberedCanvas)
    return buffer.getvalue()


if __name__ == "__main__":
    pdf_bytes = generate_student_guide_pdf()
    output_path = os.environ.get("OUTPUT_PDF_PATH") or os.path.join(os.getcwd(), "guia_estudiante_audacity.pdf")
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"Guía generada exitosamente en: {output_path} ({len(pdf_bytes)} bytes)")
