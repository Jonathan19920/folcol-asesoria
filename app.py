# -*- coding: utf-8 -*-
"""
Folcol | Asesoría Técnico-Comercial
App Streamlit para generar recomendaciones técnicas de fertilización
con base en el motor de conocimiento agronómico de Folcol (dosis fijas +
cálculo automático de volumen total por lote), y exportarlas a PDF con
diseño corporativo.
"""
import os
import tempfile
from datetime import datetime

import streamlit as st

from etapas_fenologicas import CULTIVOS, get_etapas, get_etapa_key
from motor_recomendacion import calcular_recomendacion_con_volumen, formatear_para_reporte
from generador_pdf import generar_pdf

# ----------------------------------------------------------------------
# CONFIGURACIÓN GENERAL DE LA PÁGINA
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Folcol | Asesoría Técnico-Comercial",
    page_icon="🌱",
    layout="wide",
)

BASE_DIR = os.path.dirname(__file__)
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

VERDE_OSCURO = "#0B543A"
VERDE_CLARO = "#0D9E5C"

# ----------------------------------------------------------------------
# ESTILOS CORPORATIVOS
# ----------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        .main {{ background-color: #FAFCFB; }}
        h1, h2, h3 {{ color: {VERDE_OSCURO}; }}
        div.stButton > button:first-child {{
            background-color: {VERDE_OSCURO};
            color: white;
            border-radius: 6px;
            border: none;
            padding: 0.6em 1.2em;
            font-weight: 600;
        }}
        div.stButton > button:first-child:hover {{
            background-color: {VERDE_CLARO};
            color: white;
        }}
        div.stDownloadButton > button:first-child {{
            background-color: {VERDE_CLARO};
            color: white;
            border-radius: 6px;
            border: none;
            font-weight: 600;
        }}
        .folcol-header {{
            display: flex;
            align-items: center;
            gap: 18px;
            padding-bottom: 6px;
            border-bottom: 3px solid {VERDE_CLARO};
            margin-bottom: 20px;
        }}
        .stDataFrame {{ border-radius: 8px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# ENCABEZADO CON LOGO
# ----------------------------------------------------------------------
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=90)
with col_titulo:
    st.markdown(
        f"<h1 style='margin-bottom:0;'>Asesoría Técnico-Comercial</h1>"
        f"<p style='color:#555;margin-top:0;'>Generador de recomendaciones técnicas de fertilización — FOLCOL S.A.S.</p>",
        unsafe_allow_html=True,
    )
st.divider()

# ----------------------------------------------------------------------
# FORMULARIO PRINCIPAL DE DATOS
# ----------------------------------------------------------------------
st.subheader("1️⃣ Datos de la visita técnica")

with st.form("form_datos_generales"):
    c1, c2, c3 = st.columns(3)
    with c1:
        vendedor = st.text_input("Nombre del Vendedor *")
        finca = st.text_input("Nombre de la Finca *")
    with c2:
        agricultor = st.text_input("Nombre del Agricultor *")
        area = st.number_input(
            "Área del lote/finca (hectáreas) *",
            min_value=0.1,
            value=1.0,
            step=0.5,
            format="%.2f",
            help="Ingresa el área en hectáreas. Este valor se usa para calcular la "
                 "cantidad total de producto a despachar.",
        )
    with c3:
        cultivo = st.selectbox("Cultivo *", CULTIVOS)
        etapas_disponibles = [e["label"] for e in get_etapas(cultivo)]
        etapa_label = st.selectbox("Edad / Ciclo fenológico *", etapas_disponibles)

    submitted = st.form_submit_button("🔍 Generar recomendación técnica")

# ----------------------------------------------------------------------
# LÓGICA DE RECOMENDACIÓN (motor agronómico + cálculo de volumen)
# ----------------------------------------------------------------------
if submitted:
    campos_obligatorios = [vendedor, finca, agricultor, cultivo, etapa_label]
    if not all(str(c).strip() for c in campos_obligatorios):
        st.error("Por favor completa todos los campos obligatorios (*) antes de continuar.")
    elif area <= 0:
        st.error("El área del lote debe ser mayor a 0.")
    else:
        etapa_key = get_etapa_key(cultivo, etapa_label)

        resultado = calcular_recomendacion_con_volumen(cultivo, etapa_key, area_ha=area)

        if resultado["advertencias"]:
            for a in resultado["advertencias"]:
                st.warning(a)

        st.session_state["resultado_motor"] = resultado
        st.session_state["datos_generales"] = {
            "vendedor": vendedor,
            "finca": finca,
            "agricultor": agricultor,
            "area": f"{area:g} ha",
            "cultivo": cultivo,
            "etapa": etapa_label,
        }

# ----------------------------------------------------------------------
# SELECCIÓN / CONFIRMACIÓN DE PRODUCTOS Y REPORTE
# ----------------------------------------------------------------------
if "resultado_motor" in st.session_state:
    st.divider()
    st.subheader("2️⃣ Productos recomendados — confirma o ajusta la selección")

    resultado = st.session_state["resultado_motor"]
    filas = formatear_para_reporte(resultado)

    if not filas:
        st.warning(
            "No hay un paquete técnico definido para esta combinación exacta de cultivo y "
            "etapa. Contacta al equipo técnico de Folcol para revisar este caso."
        )
        productos_finales_dict = []
    else:
        st.info(f"**Requerimiento fisiológico:** {resultado['requerimiento_fisiologico']}")

        nombres = [f["producto"] for f in filas]
        seleccion = st.multiselect(
            "Productos a incluir en el reporte (edita la selección si lo requieres)",
            options=nombres,
            default=nombres,
        )
        filas_finales = [f for f in filas if f["producto"] in seleccion]

        st.dataframe(
            [
                {
                    "Producto": f["producto"],
                    "Ingrediente activo": f["ingrediente_activo"],
                    "Dosis por ha": f["dosis_por_ha"],
                    "Cantidad Total a Despachar": f["cantidad_total_despachar"],
                    "Momento de aplicación": f["momento_aplicacion"],
                }
                for f in filas_finales
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Justificación técnica: {resultado['justificacion_tecnica']}")

        productos_finales_dict = filas_finales

    st.divider()
    st.subheader("3️⃣ Generar y descargar reporte")

    if not productos_finales_dict:
        st.info("Selecciona al menos un producto para poder generar el reporte en PDF.")
    else:
        if st.button("📄 Generar PDF de recomendación"):
            lista_productos = productos_finales_dict
            datos_generales = st.session_state["datos_generales"]

            with tempfile.TemporaryDirectory() as tmpdir:
                nombre_archivo = (
                    f"Recomendacion_Folcol_{datos_generales['agricultor'].replace(' ', '_')}_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                )
                ruta_pdf = os.path.join(tmpdir, nombre_archivo)
                generar_pdf(datos_generales, lista_productos, ruta_pdf)

                with open(ruta_pdf, "rb") as f:
                    pdf_bytes = f.read()

                st.session_state["pdf_bytes"] = pdf_bytes
                st.session_state["pdf_nombre"] = nombre_archivo
                st.success("¡Reporte generado exitosamente!")

        if "pdf_bytes" in st.session_state:
            st.download_button(
                label="⬇️ Descargar Recomendación en PDF",
                data=st.session_state["pdf_bytes"],
                file_name=st.session_state["pdf_nombre"],
                mime="application/pdf",
            )

# ----------------------------------------------------------------------
# PIE DE PÁGINA
# ----------------------------------------------------------------------
st.divider()
st.caption(
    "Foliares Colombianos FOLCOL S.A.S. · Calle 1 # 3-191, La Esperanza, Cartago - Valle del Cauca, Colombia "
    "· www.folcol.co · 312 297 6226"
)
