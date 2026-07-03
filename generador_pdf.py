# -*- coding: utf-8 -*-
"""
Generador de reporte técnico-comercial en PDF para Folcol.
Usa FPDF2 (paquete 'fpdf2', import fpdf).

Espera recibir una lista de productos con, como mínimo, las claves:
    producto, ingrediente_activo, dosis_por_ha, momento_aplicacion
(la clave "cantidad_total_despachar" puede venir en el dict pero YA NO
se usa ni se muestra en el reporte).
"""
from fpdf import FPDF
from datetime import datetime
import os

VERDE_OSCURO = (11, 84, 58)      # verde corporativo oscuro (tipo logo)
VERDE_CLARO = (13, 158, 92)      # verde corporativo claro
GRIS_TEXTO = (60, 60, 60)
GRIS_CLARO = (235, 240, 237)
GRIS_FILA = (245, 248, 246)
BLANCO = (255, 255, 255)
NEGRO_BORDE = (90, 90, 90)

LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")

LINE_H = 4.5  # alto de línea dentro de las celdas de la tabla


class ReportePDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=10, y=8, w=22)
        self.set_xy(38, 10)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*VERDE_OSCURO)
        self.cell(0, 8, "RECOMENDACIÓN TÉCNICA DE FERTILIZACIÓN", ln=1)
        self.set_x(38)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GRIS_TEXTO)
        self.cell(0, 6, "Asesoría Técnico-Comercial | FOLCOL S.A.S.", ln=1)
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


def _contar_lineas(pdf, texto, ancho):
    """Devuelve cuántas líneas ocupará `texto` al envolverse en una celda de `ancho` mm."""
    lineas = pdf.multi_cell(ancho, LINE_H, str(texto), align="L", split_only=True)
    return max(1, len(lineas))


def _dibujar_celda_centrada(pdf, x, y, ancho, alto_fila, texto, align="L",
                             fill=False, color_relleno=BLANCO, negrita=False,
                             tam_fuente=8.5, color_texto=GRIS_TEXTO):
    """Dibuja el borde completo de la celda (BOX) y coloca el texto centrado
    verticalmente dentro de esa celda, sin dejar espacios en blanco irregulares."""
    # 1) Fondo + borde completo de la celda (estilo grid tipo Excel)
    pdf.set_draw_color(*NEGRO_BORDE)
    pdf.set_line_width(0.25)
    if fill:
        pdf.set_fill_color(*color_relleno)
        pdf.rect(x, y, ancho, alto_fila, style="DF")
    else:
        pdf.rect(x, y, ancho, alto_fila, style="D")

    # 2) Texto centrado verticalmente dentro de la celda
    pdf.set_font("Helvetica", "B" if negrita else "", tam_fuente)
    pdf.set_text_color(*color_texto)
    n_lineas = _contar_lineas(pdf, texto, ancho - 4)  # -4 = padding lateral (2mm cada lado)
    alto_texto = n_lineas * LINE_H
    y_texto = y + (alto_fila - alto_texto) / 2
    pdf.set_xy(x + 2, y_texto)
    pdf.multi_cell(ancho - 4, LINE_H, str(texto), align=align)


def generar_pdf(datos_generales: dict, productos_seleccionados: list, ruta_salida: str):
    """
    datos_generales: dict con keys:
        vendedor, cultivo, etapa, finca, agricultor, area
    productos_seleccionados: lista de dicts, cada uno con (al menos):
        producto, ingrediente_activo, dosis_por_ha, momento_aplicacion
    ruta_salida: path del archivo pdf a generar
    """
    pdf = ReportePDF()
    pdf.add_page()

    # ---- Bloque de datos generales ----
    pdf.set_fill_color(*GRIS_CLARO)
    pdf.rect(10, pdf.get_y(), 190, 38, style="F")
    pdf.ln(3)

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
    pdf.cell(35, 7, "Área del lote:", border=0)
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

    # ============================================================
    # TABLA ESTILO EXCEL — 4 columnas fijas, bordes completos (GRID),
    # texto centrado verticalmente, ancho ajustado para que
    # "Ingrediente activo" y "Momento de aplicación" no se rompan raro.
    # ============================================================
    col_widths = [28, 62, 22, 68]   # Producto | Ingrediente activo | Dosis/ha | Momento de aplicación
    headers = ["Producto", "Ingrediente activo", "Dosis/ha", "Momento de aplicación"]
    x_inicio = 10

    # --- Encabezado de la tabla ---
    y = pdf.get_y()
    x = x_inicio
    for w, h in zip(col_widths, headers):
        _dibujar_celda_centrada(
            pdf, x, y, w, 9, h, align="C",
            fill=True, color_relleno=VERDE_OSCURO, negrita=True, tam_fuente=9,
            color_texto=BLANCO,
        )
        x += w
    pdf.set_xy(x_inicio, y + 9)

    # --- Filas de datos ---
    fill = False
    for prod in productos_seleccionados:
        fila = [
            prod.get("producto", "-"),
            prod.get("ingrediente_activo", "-"),
            prod.get("dosis_por_ha", "-"),
            prod.get("momento_aplicacion", "-"),
        ]

        # Calcular la altura de fila necesaria según la celda con más texto
        y_fila = pdf.get_y()
        alturas = []
        for w, texto in zip(col_widths, fila):
            n_lineas = _contar_lineas(pdf, texto, w - 4)
            alturas.append(n_lineas * LINE_H + 3)  # +3mm de padding vertical
        alto_fila = max(alturas + [9])

        # Salto de página si la fila no cabe
        if y_fila + alto_fila > 277:
            pdf.add_page()
            y_fila = pdf.get_y()

        x = x_inicio
        color_fondo = GRIS_FILA if fill else BLANCO
        for w, texto in zip(col_widths, fila):
            _dibujar_celda_centrada(
                pdf, x, y_fila, w, alto_fila, texto, align="L",
                fill=True, color_relleno=color_fondo, tam_fuente=8.5,
            )
            x += w
        pdf.set_xy(x_inicio, y_fila + alto_fila)
        fill = not fill

    pdf.ln(6)

    # ---- Notas técnicas generales (texto fijo, sin mención a cantidades) ----
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*VERDE_OSCURO)
    pdf.cell(0, 7, "Notas técnicas generales", ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS_TEXTO)

    notas = [
        "La dosis y el momento de aplicacion deben ajustarse de acuerdo con el estado "
        "fenologico real del cultivo, las condiciones agroclimaticas y el criterio del "
        "Ingeniero Agronomo responsable.",
        "Se recomienda realizar pruebas de compatibilidad previas antes de preparar "
        "mezclas en tanque.",
        "Para ajustes finos del programa nutricional, consulte al equipo tecnico de FOLCOL.",
    ]
    for nota in notas:
        pdf.set_x(10)
        pdf.multi_cell(0, 5, f"-  {nota}")
        pdf.ln(1)

    pdf.output(ruta_salida)
    return ruta_salida
