# -*- coding: utf-8 -*-
"""
Folcol | Asesoría Técnico-Comercial
App Streamlit para generar recomendaciones técnicas de fertilización
con base en el portafolio de productos de Folcol, y exportarlas a PDF
con diseño corporativo.
"""
import os
import tempfile
from datetime import datetime

import pandas as pd
import streamlit as st

from etapas_fenologicas import CULTIVOS, get_etapas, get_etapa_key
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

# Buscamos el archivo de productos en varias ubicaciones posibles,
# por si en algún momento quedó fuera de la carpeta "data".
_POSIBLES_RUTAS_DATA = [
    os.path.join(BASE_DIR, "data", "productos_folcol.csv"),
    os.path.join(BASE_DIR, "productos_folcol.csv"),
]
DATA_PATH = next((p for p in _POSIBLES_RUTAS_DATA if os.path.exists(p)), _POSIBLES_RUTAS_DATA[0])

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
# CARGA DE LA BASE DE DATOS DE PRODUCTOS
# ----------------------------------------------------------------------
@st.cache_data
def cargar_base_default():
    if not os.path.exists(DATA_PATH):
        rutas_buscadas = "\n".join(f"- `{p}`" for p in _POSIBLES_RUTAS_DATA)
        st.error(
            "⚠️ No se encontró el archivo de productos en el servidor.\n\n"
            f"Se buscó en estas ubicaciones:\n{rutas_buscadas}\n\n"
            "**Cómo solucionarlo:** entra a tu repositorio de GitHub y confirma que el archivo "
            "`productos_folcol.csv` exista dentro de una carpeta llamada `data` "
            "(o al menos suelto en la carpeta principal del repositorio). "
            "Luego reinicia la app desde Streamlit Cloud (botón 'Manage app' → 'Reboot app')."
        )
        st.stop()
    try:
        return pd.read_csv(DATA_PATH, sep=";")
    except Exception as e:
        st.error(
            "⚠️ El archivo de productos existe pero no se pudo leer correctamente.\n\n"
            f"Detalle técnico: {e}\n\n"
            "Verifica que el archivo `productos_folcol.csv` no esté dañado y que use el "
            "separador `;` entre columnas."
        )
        st.stop()


def normalizar_lista(celda: str):
    """Convierte 'a,b,c' en ['a','b','c'] limpiando espacios."""
    if pd.isna(celda):
        return []
    return [x.strip() for x in str(celda).split(",")]


with st.sidebar:
    st.header("⚙️ Base de datos de productos")
    st.caption(
        "Por defecto la app usa el portafolio Folcol precargado. "
        "Opcionalmente puedes cargar tu propio archivo actualizado."
    )
    archivo_subido = st.file_uploader(
        "Cargar archivo de Fichas Técnicas (Excel o CSV)",
        type=["csv", "xlsx"],
        help="Debe seguir la misma estructura de columnas que la plantilla base (ver documentación).",
    )

    if archivo_subido is not None:
        try:
            if archivo_subido.name.endswith(".csv"):
                df_productos = pd.read_csv(archivo_subido, sep=None, engine="python")
            else:
                df_productos = pd.read_excel(archivo_subido)
            st.success(f"Archivo cargado: {archivo_subido.name} ({len(df_productos)} productos)")
        except Exception as e:
            st.error(f"No se pudo leer el archivo: {e}")
            df_productos = cargar_base_default()
    else:
        df_productos = cargar_base_default()
        st.info(f"Usando base de datos precargada ({len(df_productos)} productos Folcol).")

    with st.expander("Ver estructura esperada del archivo"):
        st.code(
            "producto;linea;ingrediente_activo;concentracion;dosis_recomendada;"
            "unidad_dosis;momento_aplicacion;via_aplicacion;cultivos_objetivo;"
            "etapas_objetivo;beneficio_principal;registro_ica",
            language="text",
        )
        st.caption(
            "• `cultivos_objetivo` y `etapas_objetivo` deben ser listas separadas por comas.\n"
            "• Cultivos válidos: Tomate, Maiz, Soya, Caña, Citricos, Hortalizas, Frutales.\n"
            "• Etapas válidas (keys internas): Siembra, Vegetativo, Prefloracion, Floracion, "
            "Cuajado, Formacion de vainas, Llenado, Gran crecimiento, Maduracion, "
            "Recuperacion de estres, Establecimiento, Enraizamiento, Desarrollo, Prefloracion."
        )

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
        area = st.text_input("Área del lote/finca (ej. 12.5 ha)")
    with c3:
        cultivo = st.selectbox("Cultivo *", CULTIVOS)
        etapas_disponibles = [e["label"] for e in get_etapas(cultivo)]
        etapa_label = st.selectbox("Edad / Ciclo fenológico *", etapas_disponibles)

    submitted = st.form_submit_button("🔍 Generar recomendación técnica")

# ----------------------------------------------------------------------
# LÓGICA DE RECOMENDACIÓN
# ----------------------------------------------------------------------
if submitted:
    campos_obligatorios = [vendedor, finca, agricultor, cultivo, etapa_label]
    if not all(str(c).strip() for c in campos_obligatorios):
        st.error("Por favor completa todos los campos obligatorios (*) antes de continuar.")
    else:
        etapa_key = get_etapa_key(cultivo, etapa_label)

        df = df_productos.copy()
        df["_cultivos_lista"] = df["cultivos_objetivo"].apply(normalizar_lista)
        df["_etapas_lista"] = df["etapas_objetivo"].apply(normalizar_lista)

        mask = df.apply(
            lambda row: (cultivo in row["_cultivos_lista"]) and (etapa_key in row["_etapas_lista"]),
            axis=1,
        )
        recomendados = df[mask].drop(columns=["_cultivos_lista", "_etapas_lista"])

        st.session_state["recomendados"] = recomendados
        st.session_state["datos_generales"] = {
            "vendedor": vendedor,
            "finca": finca,
            "agricultor": agricultor,
            "area": area if area else "-",
            "cultivo": cultivo,
            "etapa": etapa_label,
        }

# ----------------------------------------------------------------------
# SELECCIÓN / CONFIRMACIÓN DE PRODUCTOS Y REPORTE
# ----------------------------------------------------------------------
if "recomendados" in st.session_state:
    st.divider()
    st.subheader("2️⃣ Productos sugeridos — confirma o ajusta la selección")

    recomendados = st.session_state["recomendados"]

    if recomendados.empty:
        st.warning(
            "No se encontraron productos programados específicamente para esta combinación "
            "de cultivo y etapa en la base de datos actual. Puedes ampliar la búsqueda "
            "revisando el catálogo completo abajo, o actualizar el archivo de fichas técnicas."
        )
        catalogo_manual = df_productos
        seleccion_manual = st.multiselect(
            "Selecciona manualmente productos del catálogo completo",
            options=catalogo_manual["producto"].tolist(),
        )
        productos_finales = catalogo_manual[catalogo_manual["producto"].isin(seleccion_manual)]
    else:
        st.success(f"Se encontraron {len(recomendados)} producto(s) recomendados para esta etapa.")
        opciones = recomendados["producto"].tolist()
        seleccion = st.multiselect(
            "Productos a incluir en el reporte (edita la selección si lo requieres)",
            options=opciones,
            default=opciones,
        )
        productos_finales = recomendados[recomendados["producto"].isin(seleccion)]

        st.dataframe(
            productos_finales[
                ["producto", "ingrediente_activo", "dosis_recomendada",
                 "momento_aplicacion", "via_aplicacion", "beneficio_principal"]
            ].rename(columns={
                "producto": "Producto",
                "ingrediente_activo": "Ingrediente activo",
                "dosis_recomendada": "Dosis",
                "momento_aplicacion": "Momento de aplicación",
                "via_aplicacion": "Vía",
                "beneficio_principal": "Beneficio principal",
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.subheader("3️⃣ Generar y descargar reporte")

    if productos_finales.empty:
        st.info("Selecciona al menos un producto para poder generar el reporte en PDF.")
    else:
        if st.button("📄 Generar PDF de recomendación"):
            lista_productos = productos_finales.to_dict(orient="records")
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
