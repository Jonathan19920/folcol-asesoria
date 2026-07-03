# -*- coding: utf-8 -*-
"""
motor_recomendacion.py
=======================
MOTOR DE DECISIÓN AGRONÓMICA + CÁLCULO DE VOLUMEN COMERCIAL — FOLCOL

Cambios de esta versión respecto a la anterior:
  1. Las dosis YA NO son texto ("1.5 - 2.0 L/ha" o "1.5 L/ha"). Ahora cada
     producto de la matriz tiene su dosis como VALOR NUMÉRICO FIJO
     (float) + su UNIDAD separada ("L/ha" o "kg/ha"), para poder operar
     matemáticamente con ella.
  2. Se agrega `calcular_recomendacion_con_volumen()`, que toma el área
     real del lote (en hectáreas) y calcula el TOTAL de producto a
     despachar por cada ítem recomendado (dosis_valor * area_ha).
  3. Se agrega `formatear_para_reporte()`, que deja la recomendación ya
     lista (strings formateados) para inyectar directamente en la tabla
     del PDF/Word, incluyendo la columna "Cantidad Total a Despachar".

La lógica agronómica (qué producto va en qué etapa y por qué) NO cambió;
solo cambió el formato en que se guarda y se calcula la dosis.
"""

# ============================================================================
# 🔧 MARCADOR 1 — BASE DE DATOS COMPLETA DE PRODUCTOS FOLCOL
# ============================================================================
PRODUCTOS_DB = {
    # <<< INSERTAR AQUÍ TU BASE DE DATOS COMPLETA DE PRODUCTOS FOLCOL >>>
    "FolHierro":          {"ingrediente_activo": "Hierro (Fe) 70 g/L",                              "via_aplicacion": "Foliar o fertirriego"},
    "FolKalium":          {"ingrediente_activo": "Potasio (K2O) 500 g/L",                           "via_aplicacion": "Foliar o fertirriego"},
    "FolMagnesio":        {"ingrediente_activo": "Magnesio (MgO) 160 g/L",                          "via_aplicacion": "Foliar o fertirriego"},
    "FolManganeso":       {"ingrediente_activo": "Manganeso (Mn) 64 g/L",                           "via_aplicacion": "Foliar o fertirriego"},
    "Fol-Zinc":           {"ingrediente_activo": "Zinc (Zn) 90 g/L",                                "via_aplicacion": "Foliar o al suelo"},
    "FolCalcio":          {"ingrediente_activo": "Calcio (CaO) 300 g/kg",                           "via_aplicacion": "Foliar, drench o fertirriego"},
    "Foskaprim":          {"ingrediente_activo": "Fósforo (P2O5) 400 g/L - Potasio (K2O) 540 g/L",  "via_aplicacion": "Foliar"},
    "Fol-NiCoMo":         {"ingrediente_activo": "Níquel 14 g/L - Cobalto 10 g/L - Molibdeno 100 g/L","via_aplicacion": "Foliar"},
    "FolKabo":             {"ingrediente_activo": "Boro (B) 160 g/kg - Potasio (K2O) 170 g/kg",      "via_aplicacion": "Foliar, drench o fertirriego"},
    "FolCaña":             {"ingrediente_activo": "NPK + Ca + Mg + Zn + Aminoácidos + Fitohormonas", "via_aplicacion": "Foliar"},
    "FolCaBK":             {"ingrediente_activo": "Calcio 12% - Boro 8% - Potasio 10%",              "via_aplicacion": "Foliar"},
    "FolBoroZinc":         {"ingrediente_activo": "Boro (B) 25 g/L - Zinc (Zn) 50 g/L",              "via_aplicacion": "Foliar"},
    "Fol-5":               {"ingrediente_activo": "N-K + micronutrientes completos (Zn,Fe,Mn,Cu,Mo,Co)", "via_aplicacion": "Foliar"},
    "FolKabo Granulado":   {"ingrediente_activo": "Boro (B) 160 g/kg - Potasio (K2O) 170 g/kg",      "via_aplicacion": "Al suelo"},
    "Kinefol":             {"ingrediente_activo": "Aminoácidos + Kinetinas + micronutrientes bioactivos", "via_aplicacion": "Drench o surco de siembra"},
    "FolBioestimulante":   {"ingrediente_activo": "Aminoácidos libres + extracto de algas Ascophyllum nodosum", "via_aplicacion": "Foliar o fertirriego"},
    # <<< FIN DEL MARCADOR >>>
}


# ============================================================================
# 🔧 MARCADOR 2 — MATRIZ DE CONOCIMIENTO AGRONÓMICO (DOSIS NUMÉRICAS FIJAS)
# ============================================================================
# Cada producto ahora tiene:
#   "dosis_valor"      -> float, la cantidad por hectárea (NUNCA un rango)
#   "dosis_unidad"      -> "L/ha" o "kg/ha"
#   "nota_aplicacion"   -> opcional, aclaración de cómo/cuándo aplicar
#                          (esto NO forma parte de la dosis, es solo una nota)
# ----------------------------------------------------------------------------
BASE_CONOCIMIENTO_AGRONOMICO = {

    "Tomate": {
        "Siembra": {
            "requerimiento_fisiologico": "Enraizamiento vigoroso y reserva de Boro para todo el ciclo",
            "productos": [
                {"producto": "Kinefol", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": "Drench o surco de siembra"},
                {"producto": "FolKabo Granulado", "dosis_valor": 20.0, "dosis_unidad": "kg/ha", "nota_aplicacion": "Aplicación al fondo del surco"},
            ],
            "justificacion_tecnica": "El bioestimulante radicular acelera el establecimiento; el "
                "Boro granulado garantiza disponibilidad de este micronutriente durante todo el ciclo.",
        },
        "Vegetativo": {
            "requerimiento_fisiologico": "Balance N-K + Zn/B para crecimiento uniforme de tallo y hoja",
            "productos": [
                {"producto": "Fol-5", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolBoroZinc", "dosis_valor": 1.0, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Fol-5 aporta N-K balanceados y micronutrientes; FolBoroZinc "
                "refuerza la elongación celular y diferenciación de tejidos nuevos.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Energía (P) y diferenciación floral (B)",
            "productos": [
                {"producto": "Foskaprim", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El fósforo sostiene la energía de diferenciación floral; el "
                "Boro prepara la fertilidad floral desde antes de la antesis.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad de polen y equilibrio hídrico durante la antesis",
            "productos": [
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
                {"producto": "Fol-Zinc", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Boro favorece el tubo polínico; el Zinc sostiene la "
                "actividad fotosintética que financia la floración.",
        },
        "Cuajado": {
            "requerimiento_fisiologico": "Fortalecimiento de pared celular y retención de fruto cuajado",
            "productos": [
                {"producto": "FolCalcio", "dosis_valor": 1.5, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Calcio reduce el aborto floral y previene blossom end rot; "
                "el Boro sostenido mejora el porcentaje de cuajado.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Movilización de azúcares y calidad/firmeza de fruto",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolCaBK", "dosis_valor": 1.5, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Potasio moviliza fotoasimilados al fruto; Calcio-Boro-Potasio "
                "complementa firmeza y calidad comercial.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Concentración final de azúcares y maduración uniforme",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Potasio final concentra sólidos solubles y homogeniza la "
                "maduración.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Reactivación metabólica y hormonal tras estrés abiótico/biótico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Aminoácidos y algas aceleran la recuperación fisiológica de la "
                "planta.",
        },
    },

    "Maiz": {
        "Siembra": {
            "requerimiento_fisiologico": "Enraizamiento y reserva de Boro para el ciclo",
            "productos": [
                {"producto": "Kinefol", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": "Surco de siembra"},
                {"producto": "FolKabo Granulado", "dosis_valor": 20.0, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Establecimiento uniforme y disponibilidad temprana de Boro "
                "para el desarrollo posterior de panoja y mazorca.",
        },
        "Vegetativo": {
            "requerimiento_fisiologico": "Nutrición multielemento para crecimiento vegetativo vigoroso (V3-V6)",
            "productos": [
                {"producto": "Fol-5", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolBoroZinc", "dosis_valor": 1.0, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Sostiene el desarrollo de área foliar y el potencial de "
                "hileras de grano.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Energía para diferenciación de panoja y desarrollo de mazorca (V8-VT)",
            "productos": [
                {"producto": "Foskaprim", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "Fol-Zinc", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El fósforo sostiene la diferenciación reproductiva; el Zinc es "
                "determinante en la elongación del jilote.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad de polen y actividad enzimática durante polinización",
            "productos": [
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
                {"producto": "FolManganeso", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Boro mejora viabilidad de polen; el Manganeso sostiene la "
                "actividad enzimática durante la polinización.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Movilización de fotoasimilados hacia el grano",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolMagnesio", "dosis_valor": 2.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Potasio impulsa la translocación de azúcares; Magnesio sostiene "
                "la fotosíntesis que alimenta ese llenado.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Acumulación final de almidón y peso de grano",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Sostiene la acumulación final de almidón sin nitrógeno tardío.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Recuperación tras sequía o estrés térmico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Reactiva el metabolismo de la planta.",
        },
    },

    "Soya": {
        "Siembra": {
            "requerimiento_fisiologico": "Enraizamiento y arranque de la nodulación",
            "productos": [
                {"producto": "Kinefol", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": "Surco de siembra"},
            ],
            "justificacion_tecnica": "Sistema radicular activo, base para la nodulación posterior.",
        },
        "Vegetativo": {
            "requerimiento_fisiologico": "Nutrición general + activación temprana de fijación biológica de N",
            "productos": [
                {"producto": "Fol-5", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "Fol-NiCoMo", "dosis_valor": 0.4, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Ni-Co-Mo activa las enzimas clave de la fijación biológica de "
                "nitrógeno desde etapas tempranas.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Energía reproductiva y eficiencia de fijación de nitrógeno",
            "productos": [
                {"producto": "Foskaprim", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "Fol-NiCoMo", "dosis_valor": 0.4, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El fósforo soporta la transición reproductiva; se mantiene el "
                "refuerzo de N biológico.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad floral y retención de flores (R1-R2)",
            "productos": [
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
                {"producto": "Fol-NiCoMo", "dosis_valor": 0.4, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Boro reduce el aborto floral; el N biológico sostenido evita "
                "competencia planta-nódulo.",
        },
        "Formacion de vainas": {
            "requerimiento_fisiologico": "Desarrollo de vainas y fortalecimiento estructural (R3-R4)",
            "productos": [
                {"producto": "Fol-NiCoMo", "dosis_valor": 0.4, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolCalcio", "dosis_valor": 1.5, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Pico de demanda de N fijado; el Calcio reduce el aborto de "
                "vainas recién formadas.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Llenado de grano y actividad fotosintética sostenida (R5-R6)",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolMagnesio", "dosis_valor": 2.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Potasio moviliza fotoasimilados; Magnesio sostiene la "
                "fotosíntesis en el pico de demanda de carbohidratos.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Maduración uniforme (R7-R8)",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Favorece cierre de ciclo uniforme.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Recuperación tras estrés hídrico o agroquímicos",
            "productos": [
                {"producto": "FolBioestimulante", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Reactiva el metabolismo general.",
        },
    },

    "Caña": {
        "Siembra": {
            "requerimiento_fisiologico": "Enraizamiento y macollamiento vigoroso desde la brotación",
            "productos": [
                {"producto": "Kinefol", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": "Aplicación a la semilla o surco de siembra"},
            ],
            "justificacion_tecnica": "Un sistema radicular activo desde la brotación determina el "
                "número final de tallos por macolla.",
        },
        "Vegetativo": {
            "requerimiento_fisiologico": "Nutrición multielemento para maximizar el número de tallos",
            "productos": [
                {"producto": "Fol-5", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolBoroZinc", "dosis_valor": 1.0, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Sostiene el macollamiento activo, base de la población de "
                "tallos que definirá el rendimiento.",
        },
        "Gran crecimiento": {
            "requerimiento_fisiologico": "Máxima demanda energética y de biomasa del ciclo (elongación de tallos)",
            "productos": [
                {"producto": "FolCaña", "dosis_valor": 4.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "Fol-5", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "FolCaña aporta el paquete NPK+Ca+Mg+Zn+aminoácidos+balance "
                "hormonal que exige la fase de mayor acumulación de biomasa; Fol-5 sostiene "
                "fotosíntesis y desarrollo radicular en simultáneo.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Concentración de sacarosa sin exceso de nitrógeno",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Potasio es determinante en la concentración de sacarosa.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Recuperación tras quema, corte o estrés hídrico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Acelera la reactivación fisiológica de la soca tras el corte.",
        },
    },

    "Citricos": {
        "Vegetativo": {
            "requerimiento_fisiologico": "Brotación uniforme y crecimiento vegetativo activo",
            "productos": [
                {"producto": "Fol-5", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "Fol-Zinc", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Zinc es clave en la brotación cítrica; Fol-5 sostiene el "
                "crecimiento vegetativo del flush.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Inducción floral y diferenciación de yemas",
            "productos": [
                {"producto": "Foskaprim", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolBoroZinc", "dosis_valor": 1.0, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El fósforo favorece la inducción floral; Boro y Zinc mejoran la "
                "diferenciación de yemas.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad de polen y cuajado inicial",
            "productos": [
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Boro es el nutriente de mayor impacto en fertilidad de "
                "polen y retención de flor en cítricos.",
        },
        "Cuajado": {
            "requerimiento_fisiologico": "Retención de fruto y firmeza inicial",
            "productos": [
                {"producto": "FolCalcio", "dosis_valor": 1.5, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Calcio reduce la caída fisiológica de fruto pequeño.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Llenado y calidad de jugo/pulpa",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolMagnesio", "dosis_valor": 2.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Potasio impulsa el llenado; Magnesio sostiene la fotosíntesis "
                "que aporta azúcares al jugo.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Color, grados Brix y maduración uniforme",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolMagnesio", "dosis_valor": 2.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El binomio Potasio-Magnesio mejora azúcares y color de cáscara.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Recuperación tras estrés hídrico o térmico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Reactiva el metabolismo del árbol.",
        },
    },

    "Hortalizas": {
        "Siembra": {
            "requerimiento_fisiologico": "Enraizamiento y reserva de Boro para el ciclo",
            "productos": [
                {"producto": "Kinefol", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": "Drench o surco de siembra"},
                {"producto": "FolKabo Granulado", "dosis_valor": 20.0, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Establecimiento uniforme del trasplante/siembra y "
                "disponibilidad temprana de Boro.",
        },
        "Vegetativo": {
            "requerimiento_fisiologico": "Balance N-K + Zn/B para crecimiento uniforme",
            "productos": [
                {"producto": "Fol-5", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolBoroZinc", "dosis_valor": 1.0, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Sostiene un crecimiento vegetativo vigoroso y homogéneo.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Energía (P) y diferenciación floral (B)",
            "productos": [
                {"producto": "Foskaprim", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El fósforo sostiene la transición reproductiva; el Boro prepara "
                "la fertilidad floral con antelación.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad de polen y equilibrio hídrico",
            "productos": [
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
                {"producto": "Fol-Zinc", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Mejora la polinización efectiva y sostiene la fotosíntesis.",
        },
        "Cuajado": {
            "requerimiento_fisiologico": "Fortalecimiento estructural y retención de fruto/estructura comercial",
            "productos": [
                {"producto": "FolCalcio", "dosis_valor": 1.5, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Calcio reduce desórdenes fisiológicos; el Boro mejora el "
                "porcentaje de cuajado.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Movilización de azúcares y calidad de la estructura comercial",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolCaBK", "dosis_valor": 1.5, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Potasio impulsa el llenado; Calcio-Boro-Potasio mejora "
                "firmeza y calidad comercial.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Concentración final de azúcares y punto óptimo de cosecha",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Favorece uniformidad de maduración y calidad comercial.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Reactivación metabólica tras estrés abiótico/biótico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Acelera la recuperación fisiológica.",
        },
    },

    "Frutales": {
        "Vegetativo": {
            "requerimiento_fisiologico": "Brotación uniforme y crecimiento vegetativo activo",
            "productos": [
                {"producto": "Fol-5", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "Fol-Zinc", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Zinc favorece la brotación; Fol-5 sostiene el desarrollo "
                "vegetativo general.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Inducción floral y diferenciación de yemas",
            "productos": [
                {"producto": "Foskaprim", "dosis_valor": 1.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolBoroZinc", "dosis_valor": 1.0, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El fósforo favorece la inducción floral; Boro y Zinc mejoran la "
                "diferenciación de yemas.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad de polen y cuajado inicial",
            "productos": [
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Boro es el nutriente de mayor impacto en fertilidad de "
                "polen y retención de flor.",
        },
        "Cuajado": {
            "requerimiento_fisiologico": "Retención de fruto y firmeza inicial",
            "productos": [
                {"producto": "FolCalcio", "dosis_valor": 1.5, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
                {"producto": "FolKabo", "dosis_valor": 0.4, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Calcio reduce la caída fisiológica de fruto recién cuajado.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Llenado de fruto y actividad fotosintética sostenida",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolMagnesio", "dosis_valor": 2.0, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Potasio impulsa el llenado; el Magnesio sostiene la "
                "fotosíntesis que aporta esos azúcares.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Concentración de azúcares, color y calidad de cosecha",
            "productos": [
                {"producto": "FolKalium", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
                {"producto": "FolCaBK", "dosis_valor": 1.5, "dosis_unidad": "kg/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "El Potasio concentra azúcares; Calcio-Boro-Potasio mejora "
                "firmeza y vida de anaquel.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Recuperación tras estrés hídrico o térmico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis_valor": 1.5, "dosis_unidad": "L/ha", "nota_aplicacion": None},
            ],
            "justificacion_tecnica": "Reactiva el metabolismo del árbol.",
        },
    },
}


# ============================================================================
# FUNCIÓN 1 — OBTENER LA RECOMENDACIÓN AGRONÓMICA (sin volumen todavía)
# ============================================================================
def obtener_recomendacion(cultivo: str, etapa_key: str) -> dict:
    """Devuelve la recomendación técnica (sin calcular volumen aún)."""
    advertencias = []

    cultivo_data = BASE_CONOCIMIENTO_AGRONOMICO.get(cultivo)
    if cultivo_data is None:
        return {
            "cultivo": cultivo, "etapa": etapa_key,
            "requerimiento_fisiologico": None, "productos": [],
            "justificacion_tecnica": None,
            "advertencias": [f"Cultivo '{cultivo}' no definido. Disponibles: "
                              f"{list(BASE_CONOCIMIENTO_AGRONOMICO.keys())}"],
        }

    etapa_data = cultivo_data.get(etapa_key)
    if etapa_data is None:
        return {
            "cultivo": cultivo, "etapa": etapa_key,
            "requerimiento_fisiologico": None, "productos": [],
            "justificacion_tecnica": None,
            "advertencias": [f"Etapa '{etapa_key}' no definida para '{cultivo}'. Disponibles: "
                              f"{list(cultivo_data.keys())}"],
        }

    productos_enriquecidos = []
    for item in etapa_data["productos"]:
        nombre = item["producto"]
        ficha = PRODUCTOS_DB.get(nombre)
        if ficha is None:
            advertencias.append(
                f"El producto '{nombre}' está en la matriz pero no existe en PRODUCTOS_DB."
            )
        productos_enriquecidos.append({
            "producto": nombre,
            "dosis_valor": item["dosis_valor"],          # <- float puro
            "dosis_unidad": item["dosis_unidad"],         # <- "L/ha" o "kg/ha"
            "nota_aplicacion": item.get("nota_aplicacion"),
            "ingrediente_activo": ficha["ingrediente_activo"] if ficha else "N/A",
            "via_aplicacion": ficha["via_aplicacion"] if ficha else "N/A",
        })

    return {
        "cultivo": cultivo,
        "etapa": etapa_key,
        "requerimiento_fisiologico": etapa_data["requerimiento_fisiologico"],
        "productos": productos_enriquecidos,
        "justificacion_tecnica": etapa_data["justificacion_tecnica"],
        "advertencias": advertencias,
    }


# ============================================================================
# FUNCIÓN 2 — CÁLCULO DE VOLUMEN TOTAL (dosis × área del lote)
# ============================================================================
def calcular_recomendacion_con_volumen(cultivo: str, etapa_key: str, area_ha: float) -> dict:
    """
    Toma la recomendación agronómica y multiplica la dosis por hectárea
    de cada producto por el área real del lote, para obtener la cantidad
    TOTAL a despachar/cotizar.

    Parámetros
    ----------
    cultivo : str
    etapa_key : str
    area_ha : float
        Área del lote/finca, en hectáreas. DEBE ser numérica (no texto).

    Retorna
    -------
    El mismo dict de obtener_recomendacion(), pero cada producto en
    "productos" trae además:
        "area_ha"          -> el área usada para el cálculo
        "cantidad_total"    -> float, dosis_valor * area_ha
    """
    if not isinstance(area_ha, (int, float)) or area_ha <= 0:
        raise ValueError(
            f"El área debe ser un número mayor a 0 (recibido: {area_ha!r}). "
            "Convierte el campo de área a float ANTES de llamar a esta función."
        )

    resultado = obtener_recomendacion(cultivo, etapa_key)

    for producto in resultado["productos"]:
        producto["area_ha"] = area_ha
        producto["cantidad_total"] = round(producto["dosis_valor"] * area_ha, 2)

    return resultado


# ============================================================================
# FUNCIÓN 3 — FORMATEO LISTO PARA EL REPORTE (PDF / Word)
# ============================================================================
def formatear_para_reporte(resultado_con_volumen: dict) -> list:
    """
    Convierte la salida de calcular_recomendacion_con_volumen() en una
    lista de diccionarios ya formateados como strings, lista para
    inyectar directamente en la tabla del generador de PDF/Word.

    Cada fila queda con las columnas que pide el reporte comercial:
        "producto"                   -> nombre del producto
        "ingrediente_activo"         -> ficha técnica resumida
        "dosis_por_ha"               -> ej. "1.5 L/ha"
        "cantidad_total_despachar"   -> ej. "18.75 L"  (columna clave para cotizar)
        "momento_aplicacion"         -> nota de aplicación si existe
        "beneficio_principal"        -> se toma de la justificación técnica global
    """
    filas = []
    justificacion = resultado_con_volumen.get("justificacion_tecnica", "")

    for p in resultado_con_volumen["productos"]:
        unidad_total = p["dosis_unidad"].split("/")[0]  # "L/ha" -> "L" | "kg/ha" -> "kg"
        filas.append({
            "producto": p["producto"],
            "ingrediente_activo": p["ingrediente_activo"],
            "dosis_por_ha": f"{p['dosis_valor']:g} {p['dosis_unidad']}",
            "cantidad_total_despachar": f"{p['cantidad_total']:g} {unidad_total}",
            "momento_aplicacion": p["nota_aplicacion"] or p["via_aplicacion"],
            "beneficio_principal": justificacion,
        })
    return filas


# ============================================================================
# EJEMPLO DE USO / AUTOVALIDACIÓN
# ============================================================================
if __name__ == "__main__":
    # Caso del ejemplo del cliente: Caña, Gran crecimiento, lote de 12.5 ha
    area_lote = 12.5
    resultado = calcular_recomendacion_con_volumen("Caña", "Gran crecimiento", area_lote)

    print(f"Cultivo: {resultado['cultivo']} | Etapa: {resultado['etapa']} | Área: {area_lote} ha\n")
    for p in resultado["productos"]:
        print(f"  {p['producto']:<10} dosis: {p['dosis_valor']} {p['dosis_unidad']:<6} "
              f"-> Total a despachar: {p['cantidad_total']} {p['dosis_unidad'].split('/')[0]}")

    print("\n--- Formato listo para el reporte ---")
    for fila in formatear_para_reporte(resultado):
        print(fila)
