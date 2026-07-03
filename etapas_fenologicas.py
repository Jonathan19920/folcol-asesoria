# -*- coding: utf-8 -*-
"""
Diccionario de ciclos / etapas fenológicas por cultivo.
Cada etapa tiene:
  - "label": texto que ve el usuario en el desplegable (con tildes, legible)
  - "key": clave interna usada para cruzar contra la columna 'etapas_objetivo'
           del archivo de productos (sin tildes, para evitar problemas de
           codificación en comparaciones de texto).

Estas etapas fueron definidas con base en las escalas de desarrollo
agronómico estándar usadas comercialmente en Colombia para cada cultivo
(BBCH simplificado / fenología comercial de campo).
"""

ETAPAS_POR_CULTIVO = {
    "Tomate": [
        {"label": "Siembra / Trasplante", "key": "Siembra"},
        {"label": "Vegetativo (crecimiento de tallo y hojas)", "key": "Vegetativo"},
        {"label": "Prefloración", "key": "Prefloracion"},
        {"label": "Floración", "key": "Floracion"},
        {"label": "Cuajado de fruto", "key": "Cuajado"},
        {"label": "Llenado de fruto", "key": "Llenado"},
        {"label": "Maduración / Cosecha", "key": "Maduracion"},
        {"label": "Recuperación post-estrés (clima, plagas, agroquímicos)", "key": "Recuperacion de estres"},
    ],
    "Maiz": [
        {"label": "Siembra / Germinación", "key": "Siembra"},
        {"label": "Vegetativo (V3 - V6)", "key": "Vegetativo"},
        {"label": "Prefloración (V8 - VT)", "key": "Prefloracion"},
        {"label": "Floración / Espigamiento", "key": "Floracion"},
        {"label": "Llenado de grano", "key": "Llenado"},
        {"label": "Maduración fisiológica", "key": "Maduracion"},
        {"label": "Recuperación post-estrés", "key": "Recuperacion de estres"},
    ],
    "Soya": [
        {"label": "Siembra / Germinación", "key": "Siembra"},
        {"label": "Vegetativo (V2 - V5)", "key": "Vegetativo"},
        {"label": "Prefloración", "key": "Prefloracion"},
        {"label": "Floración (R1 - R2)", "key": "Floracion"},
        {"label": "Formación de vainas (R3 - R4)", "key": "Formacion de vainas"},
        {"label": "Llenado de grano (R5 - R6)", "key": "Llenado"},
        {"label": "Maduración (R7 - R8)", "key": "Maduracion"},
        {"label": "Recuperación post-estrés", "key": "Recuperacion de estres"},
    ],
    "Caña": [
        {"label": "Siembra / Establecimiento", "key": "Siembra"},
        {"label": "Macollamiento (vegetativo)", "key": "Vegetativo"},
        {"label": "Gran crecimiento (elongación de tallos)", "key": "Gran crecimiento"},
        {"label": "Maduración (acumulación de sacarosa)", "key": "Maduracion"},
        {"label": "Recuperación post-estrés (hídrico, quema, plagas)", "key": "Recuperacion de estres"},
    ],
    "Citricos": [
        {"label": "Brotación / Vegetativo", "key": "Vegetativo"},
        {"label": "Prefloración", "key": "Prefloracion"},
        {"label": "Floración", "key": "Floracion"},
        {"label": "Cuajado de fruto", "key": "Cuajado"},
        {"label": "Llenado de fruto", "key": "Llenado"},
        {"label": "Maduración / Cosecha", "key": "Maduracion"},
        {"label": "Recuperación post-estrés", "key": "Recuperacion de estres"},
    ],
    "Hortalizas": [
        {"label": "Siembra / Trasplante", "key": "Siembra"},
        {"label": "Vegetativo", "key": "Vegetativo"},
        {"label": "Prefloración", "key": "Prefloracion"},
        {"label": "Floración", "key": "Floracion"},
        {"label": "Cuajado", "key": "Cuajado"},
        {"label": "Llenado / Formación de estructura comercial", "key": "Llenado"},
        {"label": "Maduración / Cosecha", "key": "Maduracion"},
        {"label": "Recuperación post-estrés", "key": "Recuperacion de estres"},
    ],
    "Frutales": [
        {"label": "Brotación / Vegetativo", "key": "Vegetativo"},
        {"label": "Prefloración", "key": "Prefloracion"},
        {"label": "Floración", "key": "Floracion"},
        {"label": "Cuajado de fruto", "key": "Cuajado"},
        {"label": "Llenado de fruto", "key": "Llenado"},
        {"label": "Maduración / Cosecha", "key": "Maduracion"},
        {"label": "Recuperación post-estrés", "key": "Recuperacion de estres"},
    ],
}

CULTIVOS = list(ETAPAS_POR_CULTIVO.keys())


def get_etapas(cultivo: str):
    """Devuelve la lista de etapas (dict con label/key) para un cultivo dado."""
    return ETAPAS_POR_CULTIVO.get(cultivo, [])


def get_etapa_key(cultivo: str, etapa_label: str):
    """Convierte el label visible seleccionado por el usuario en la key interna."""
    for etapa in get_etapas(cultivo):
        if etapa["label"] == etapa_label:
            return etapa["key"]
    return None
