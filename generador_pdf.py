# -*- coding: utf-8 -*-
"""
Generador de reporte técnico-comercial en PDF para Folcol.
Usa FPDF2 (paquete 'fpdf2', import fpdf).
"""
from fpdf import FPDF
from datetime import datetime
import os

VERDE_OSCURO = (11, 84, 58)      # verde corporativo oscuro (tipo logo)
VERDE_CLARO = (13, 158, 92)      # verde corporativo claro
GRIS_TEXTO = (60, 60, 60)
GRIS_CLARO = (235, 240, 237)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")


class ReportePDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Logo arriba a la izquierda
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=10, y=8, w=22)
        # Franja verde de título
        self.set_xy(38, 10)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*VERDE_OSCURO)
        self.cell(0, 8, "RECOMENDACIÓN TÉCNICA DE FERTILIZACIÓN", ln=1)
        self.set_x(38)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GRIS_TEXTO)
        self.cell(0, 6, "Asesoría Técnico-Comercial | FOLCOL S.A.S.", ln=1)
        # Línea separadora
        self.set_draw_color(*VERDE_CLARO)
        self.set_line_width(0.8)
        self.line(10, 30, 200, 30)
        self.ln(8)

    def footer(self):
        self.set_y(-18)
        self.set_draw_color(*VERDE_CLARO)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5,
                   "Foliares Colombianos FOLCOL S.A.S. | Calle 1 # 3-191, La Esperanza, Cartago - Valle del Cauca, Colombia",
                   ln=1, align="C")
        self.cell(0, 5, "www.folcol.co | 312 297 6226", ln=1, align="C")
        self.set_y(-8)
        self.cell(0, 4, f"Página {self.page_no()}", align="C")


def _celda_dato(pdf, etiqueta, valor, ancho_etq=42, ancho_val=None):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*VERDE_OSCURO)
    pdf.cell(ancho_etq, 7, etiqueta, border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS_TEXTO)
    if ancho_val:
        pdf.cell(ancho_val, 7, str(valor), border=0, ln=1)
    else:
        pdf.cell(0, 7, str(valor), border=0, ln=1)


def generar_pdf(datos_generales: dict, productos_seleccionados: list, ruta_salida: str):
    """
    datos_generales: dict con keys:
        vendedor, cultivo, etapa, finca, agricultor, area
    productos_seleccionados: lista de dicts, cada uno con:
        producto, ingrediente_activo, dosis_recomendada, momento_aplicacion,
        via_aplicacion, beneficio_principal
    ruta_salida: path del archivo pdf a generar
    """
    pdf = ReportePDF()
    pdf.add_page()

    # ---- Bloque de datos generales ----
    pdf.set_fill_color(*GRIS_CLARO)
    pdf.rect(10, pdf.get_y(), 190, 38, style="F")
    pdf.ln(3)

    x0 = pdf.get_x()
    y0 = pdf.get_y()

    pdf.set_xy(14, y0 + 2)
    _celda_dato(pdf, "Fecha:", datetime.now().strftime("%d/%m/%Y"))
    pdf.set_x(14)
    _celda_dato(pdf, "Vendedor:", datos_generales.get("vendedor", "-"))
    pdf.set_x(14)
    _celda_dato(pdf, "Agricultor:", datos_generales.get("agricultor", "-"))
    pdf.set_x(14)
    _celda_dato(pdf, "Finca:", datos_generales.get("finca", "-"))

    pdf.set_xy(110, y0 + 2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*VERDE_OSCURO)
    pdf.cell(35, 7, "Cultivo:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.cell(0, 7, str(datos_generales.get("cultivo", "-")), ln=1)

    pdf.set_x(110)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*VERDE_OSCURO)
    pdf.cell(35, 7, "Etapa fenológica:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.multi_cell(65, 7, str(datos_generales.get("etapa", "-")))

    pdf.set_x(110)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*VERDE_OSCURO)
    pdf.cell(35, 7, "Área:", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.cell(0, 7, str(datos_generales.get("area", "-")), ln=1)

    pdf.set_y(y0 + 40)
    pdf.ln(4)

    # ---- Título de tabla ----
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*VERDE_OSCURO)
    pdf.cell(0, 8, "Programa de Recomendación Técnica", ln=1)
    pdf.ln(1)

    # ---- Tabla de productos ----
    col_widths = [32, 42, 30, 40, 24, 22]
    headers = ["Producto", "Ingrediente activo", "Dosis", "Momento de aplicación", "Vía", "Beneficio"]
    # Ajuste: usaremos 5 columnas más legibles
    col_widths = [30, 45, 28, 45, 42]
    headers = ["Producto", "Ingrediente activo", "Dosis", "Momento de aplicación", "Beneficio principal"]

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*VERDE_OSCURO)
    pdf.set_text_color(255, 255, 255)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 8, h, border=0, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*GRIS_TEXTO)
    fill = False
    for prod in productos_seleccionados:
        fila = [
            prod.get("producto", "-"),
            prod.get("ingrediente_activo", "-"),
            prod.get("dosis_recomendada", "-"),
            prod.get("momento_aplicacion", "-"),
            prod.get("beneficio_principal", "-"),
        ]
        # Calcular altura de fila según el texto más largo (multi_cell)
        alturas = []
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        for w, texto in zip(col_widths, fila):
            n_lineas = max(1, len(str(texto)) // 28 + 1)
            alturas.append(n_lineas * 4.2)
        row_h = max(alturas + [8])

        pdf.set_fill_color(245, 248, 246) if fill else pdf.set_fill_color(255, 255, 255)
        x = x_start
        for w, texto in zip(col_widths, fila):
            pdf.set_xy(x, y_start)
            pdf.multi_cell(w, 4.2, str(texto), border=1, align="L", fill=True)
            x += w
        pdf.set_xy(x_start, y_start + row_h)
        fill = not fill

    pdf.ln(6)

    # ---- Notas técnicas ----
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*VERDE_OSCURO)
    pdf.cell(0, 7, "Notas técnicas generales", ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS_TEXTO)
    notas = (
        "- La dosis y el momento de aplicación deben ajustarse de acuerdo con el estado fenológico real "
        "del cultivo, las condiciones agroclimáticas y el criterio del Ingeniero Agrónomo responsable.\n"
        "- Se recomienda realizar pruebas de compatibilidad previas antes de preparar mezclas en tanque.\n"
        "- Evitar mezclas con fuentes altamente ácidas o concentradas de fósforo salvo validación previa "
        "de compatibilidad.\n"
        "- Para ajustes finos del programa nutricional, consulte al equipo técnico de FOLCOL."
    )
    pdf.multi_cell(0, 5, notas)
    pdf.ln(4)

    # ---- Firma ----
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.cell(90, 6, "_____________________________", ln=0)
    pdf.cell(0, 6, "_____________________________", ln=1)
    pdf.cell(90, 5, "Firma Asesor Técnico-Comercial", ln=0)
    pdf.cell(0, 5, "Firma Agricultor / Recibido", ln=1)
    pdf.cell(90, 5, str(datos_generales.get("vendedor", "")), ln=0)
    pdf.cell(0, 5, str(datos_generales.get("agricultor", "")), ln=1)

    pdf.output(ruta_salida)
    return ruta_salida
