# -*- coding: utf-8 -*-
"""
motor_recomendacion.py
=======================
MOTOR DE DECISIÓN AGRONÓMICA — FOLCOL

Este módulo reemplaza la lógica de "filtrar por columna" que se usaba antes
(cruzar cultivos_objetivo / etapas_objetivo en el CSV) por una matriz de
conocimiento técnico explícita: para cada combinación real de
Cultivo -> Etapa fenológica, se define QUÉ necesita fisiológicamente la
planta en ese momento, y CUÁL paquete de productos Folcol (con dosis fija)
resuelve esa necesidad. Esto es lo que haría un Ingeniero Agrónomo de campo:
primero diagnostica la demanda fisiológica, y de ahí se desprende el producto
— nunca al revés.

--------------------------------------------------------------------------
CRITERIO AGRONÓMICO APLICADO (resumen del razonamiento usado para construir
la matriz, por bloque fenológico — válido de forma transversal a los 7
cultivos, con matices propios de cada especie):

1. SIEMBRA / ESTABLECIMIENTO
   Prioridad: enraizamiento y arranque metabólico.
   -> Bioestimulante radicular (aminoácidos + kinetinas) vía drench/surco,
      y en algunos casos reserva edáfica de Boro para todo el ciclo.

2. VEGETATIVO (crecimiento de tallo, hoja, macollamiento, brotación)
   Prioridad: N y K balanceados + Zn/B para diferenciación activa de
   tejidos nuevos, apoyados en micronutrientes de rápida disponibilidad.
   -> Producto multielemento (N-K + micronutrientes) + refuerzo específico
      de Boro-Zinc para brotación y elongación celular.

3. PREFLORACIÓN (inducción floral, diferenciación de yemas/primordios)
   Prioridad: Fósforo (energía, transferencia de ATP) + Boro/Zinc
   (diferenciación floral). En leguminosas se suma el paquete de fijación
   biológica de nitrógeno (Ni-Co-Mo) para que la planta llegue a floración
   con la ruta de N ya activa.
   -> Fuente PK de alta concentración + Boro/Zinc (o Ni-Co-Mo en soya).

4. FLORACIÓN
   Prioridad: Boro (fertilidad de polen, tubo polínico) + Potasio
   (equilibrio hídrico durante antesis).
   -> Fuente de Boro-Potasio + Zinc como apoyo a la actividad fotosintética
      durante el gasto energético de la floración.

5. CUAJADO / FORMACIÓN DE VAINAS
   Prioridad: Calcio (fortalecimiento de pared celular, evita aborto floral
   y rajado temprano) + Boro (retención de flor/fruto cuajado).
   -> Fuente de Calcio + Boro-Potasio. En soya, se mantiene el paquete
      Ni-Co-Mo porque la formación de vainas coincide con el pico de
      demanda de nitrógeno fijado biológicamente.

6. GRAN CRECIMIENTO (caso especial: caña de azúcar, elongación de tallos)
   Prioridad: máxima demanda energética y de biomasa del ciclo completo.
   -> Paquete tecnológico específico de alta carga nutricional + hormonal
      (FolCaña) reforzado con un multielemento (Fol-5) para sostener
      fotosíntesis y desarrollo radicular simultáneo.

7. LLENADO (de fruto, grano o tallo)
   Prioridad: Potasio (motor de movilización de azúcares/almidón hacia el
   órgano de cosecha) + Magnesio (sostiene la fotosíntesis que sigue
   alimentando ese llenado) + Calcio-Boro cuando el objetivo es fruto
   (firmeza y calidad comercial, no solo grano/tallo).
   -> Fuente de Potasio + Magnesio (+ Calcio-Boro-Potasio en frutos).

8. MADURACIÓN
   Prioridad: Potasio para concentración final de azúcares/almidón y
   maduración uniforme, evitando exceso de Nitrógeno que retrasaría el
   punto de corte o cosecha. En frutales/cítricos se agrega Magnesio
   (color, grados brix).
   -> Fuente de Potasio (+ Magnesio en frutales/cítricos).

9. RECUPERACIÓN POST-ESTRÉS (clima, plagas, agroquímicos)
   Prioridad: reactivar metabolismo y balance hormonal antes de retomar
   cualquier otro objetivo nutricional.
   -> Bioestimulante de aminoácidos + algas (y Hierro si el estrés dejó
      clorosis asociada, criterio que el asesor puede activar en campo).
--------------------------------------------------------------------------

Las claves de "cultivo" y "etapa" usadas aquí son EXACTAMENTE las mismas
`key` internas ya definidas en `etapas_fenologicas.py` (sin tildes), para
que este motor conecte directo con el formulario existente sin tener que
tocar la interfaz.
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
    # <<< FIN DEL MARCADOR — agrega aquí cualquier producto nuevo del portafolio >>>
}


# ============================================================================
# 🔧 MARCADOR 2 — MATRIZ DE CONOCIMIENTO AGRONÓMICO
# ============================================================================
BASE_CONOCIMIENTO_AGRONOMICO = {

    # ------------------------------------------------------------------ #
    "Tomate": {
        "Siembra": {
            "requerimiento_fisiologico": "Enraizamiento vigoroso y reserva de Boro para todo el ciclo",
            "productos": [
                {"producto": "Kinefol", "dosis": "1 L/ha (drench o surco de siembra)"},
                {"producto": "FolKabo Granulado", "dosis": "20 kg/ha (aplicación al fondo del surco)"},
            ],
            "justificacion_tecnica": "El bioestimulante radicular acelera el establecimiento y la "
                "diferenciación de raíces secundarias; el Boro granulado garantiza disponibilidad "
                "de este micronutriente crítico durante todo el ciclo sin depender de aplicaciones "
                "foliares repetidas.",
        },
        "Vegetativo": {
            "requerimiento_fisiologico": "Balance N-K + Zn/B para crecimiento uniforme de tallo y hoja",
            "productos": [
                {"producto": "Fol-5", "dosis": "1.5 L/ha"},
                {"producto": "FolBoroZinc", "dosis": "1 kg/ha"},
            ],
            "justificacion_tecnica": "Fol-5 aporta nitrógeno y potasio balanceados junto con el "
                "paquete completo de micronutrientes; FolBoroZinc refuerza específicamente la "
                "elongación celular y la diferenciación de tejidos nuevos.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Energía (P) y diferenciación floral (B)",
            "productos": [
                {"producto": "Foskaprim", "dosis": "1 L/ha"},
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
            ],
            "justificacion_tecnica": "El fósforo de alta concentración sostiene la síntesis y "
                "transferencia de energía necesaria para iniciar la diferenciación de primordios "
                "florales; el Boro prepara la fertilidad floral desde antes de la antesis.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad de polen y equilibrio hídrico durante la antesis",
            "productos": [
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
                {"producto": "Fol-Zinc", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "El Boro favorece el desarrollo del tubo polínico y la "
                "polinización efectiva; el Zinc sostiene la actividad fotosintética que financia "
                "energéticamente la floración.",
        },
        "Cuajado": {
            "requerimiento_fisiologico": "Fortalecimiento de pared celular y retención de fruto cuajado",
            "productos": [
                {"producto": "FolCalcio", "dosis": "1.5 kg/ha"},
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
            ],
            "justificacion_tecnica": "El Calcio reduce el aborto floral y previene desórdenes como "
                "el blossom end rot; el Boro sostenido en esta etapa mejora el porcentaje de cuajado.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Movilización de azúcares y calidad/firmeza de fruto",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
                {"producto": "FolCaBK", "dosis": "1.5 kg/ha"},
            ],
            "justificacion_tecnica": "El Potasio es el motor de la translocación de fotoasimilados "
                "hacia el fruto; el paquete Calcio-Boro-Potasio complementa firmeza y calidad "
                "comercial del fruto en desarrollo.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Concentración final de azúcares y maduración uniforme",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "El aporte final de Potasio concentra sólidos solubles y "
                "homogeniza el punto de maduración, evitando prolongar el nitrógeno que retrasaría "
                "la cosecha.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Reactivación metabólica y hormonal tras estrés abiótico/biótico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Los aminoácidos y extractos de algas aceleran la recuperación "
                "fisiológica de la planta antes de retomar cualquier otro objetivo nutricional.",
        },
    },

    # ------------------------------------------------------------------ #
    "Maiz": {
        "Siembra": {
            "requerimiento_fisiologico": "Enraizamiento y reserva de Boro para el ciclo",
            "productos": [
                {"producto": "Kinefol", "dosis": "1 L/ha (surco de siembra)"},
                {"producto": "FolKabo Granulado", "dosis": "20 kg/ha"},
            ],
            "justificacion_tecnica": "Establecimiento uniforme y disponibilidad temprana de Boro, "
                "clave para el desarrollo posterior de la panoja y el jilote.",
        },
        "Vegetativo": {
            "requerimiento_fisiologico": "Nutrición multielemento para crecimiento vegetativo vigoroso (V3-V6)",
            "productos": [
                {"producto": "Fol-5", "dosis": "1.5 L/ha"},
                {"producto": "FolBoroZinc", "dosis": "1 kg/ha"},
            ],
            "justificacion_tecnica": "El maíz en esta fase define área foliar y número potencial de "
                "hileras de grano; el balance N-K-micronutrientes sostiene ese desarrollo vegetativo.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Energía para diferenciación de panoja y desarrollo de mazorca (V8-VT)",
            "productos": [
                {"producto": "Foskaprim", "dosis": "1 L/ha"},
                {"producto": "Fol-Zinc", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "El fósforo de alta concentración sostiene la diferenciación "
                "reproductiva; el Zinc es determinante en la elongación del jilote y el número de "
                "óvulos fecundables.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad de polen y actividad enzimática durante polinización",
            "productos": [
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
                {"producto": "FolManganeso", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "El Boro mejora viabilidad de polen; el Manganeso sostiene la "
                "actividad fotosintética y enzimática durante la ventana crítica de polinización.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Movilización de fotoasimilados hacia el grano",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
                {"producto": "FolMagnesio", "dosis": "2 L/ha"},
            ],
            "justificacion_tecnica": "El Potasio impulsa la translocación de azúcares al grano; el "
                "Magnesio mantiene activa la fotosíntesis que sigue alimentando ese llenado.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Acumulación final de almidón y peso de grano",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Sostiene la acumulación final de almidón sin prolongar "
                "artificialmente el ciclo con nitrógeno tardío.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Recuperación tras sequía o estrés térmico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Reactiva el metabolismo de la planta antes de continuar con el "
                "programa nutricional regular.",
        },
    },

    # ------------------------------------------------------------------ #
    "Soya": {
        "Siembra": {
            "requerimiento_fisiologico": "Enraizamiento y arranque de la nodulación",
            "productos": [
                {"producto": "Kinefol", "dosis": "1 L/ha (surco de siembra)"},
            ],
            "justificacion_tecnica": "Favorece un sistema radicular activo, base física para el "
                "establecimiento posterior de nódulos fijadores de nitrógeno.",
        },
        "Vegetativo": {
            "requerimiento_fisiologico": "Nutrición general + activación temprana de fijación biológica de N",
            "productos": [
                {"producto": "Fol-5", "dosis": "1.5 L/ha"},
                {"producto": "Fol-NiCoMo", "dosis": "0.4 L/ha"},
            ],
            "justificacion_tecnica": "El paquete Ni-Co-Mo activa las enzimas clave (nitrogenasa, "
                "ureasas) de la fijación biológica de nitrógeno en los nódulos desde etapas tempranas.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Energía reproductiva y eficiencia de fijación de nitrógeno",
            "productos": [
                {"producto": "Foskaprim", "dosis": "1 L/ha"},
                {"producto": "Fol-NiCoMo", "dosis": "0.4 L/ha"},
            ],
            "justificacion_tecnica": "El fósforo soporta la transición a fase reproductiva; se "
                "mantiene el refuerzo de Ni-Co-Mo porque la demanda de nitrógeno fijado se acelera "
                "justo antes de floración.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad floral y retención de flores (R1-R2)",
            "productos": [
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
                {"producto": "Fol-NiCoMo", "dosis": "0.4 L/ha"},
            ],
            "justificacion_tecnica": "El Boro reduce el aborto floral, típico en soya bajo estrés; "
                "el nitrógeno biológico sostenido evita competencia entre planta y nódulo.",
        },
        "Formacion de vainas": {
            "requerimiento_fisiologico": "Desarrollo de vainas y fortalecimiento estructural (R3-R4)",
            "productos": [
                {"producto": "Fol-NiCoMo", "dosis": "0.4 L/ha"},
                {"producto": "FolCalcio", "dosis": "1.5 kg/ha"},
            ],
            "justificacion_tecnica": "Coincide con el pico de demanda de nitrógeno fijado "
                "biológicamente; el Calcio reduce el aborto de vainas recién formadas.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Llenado de grano y actividad fotosintética sostenida (R5-R6)",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
                {"producto": "FolMagnesio", "dosis": "2 L/ha"},
            ],
            "justificacion_tecnica": "El Potasio moviliza fotoasimilados al grano; el Magnesio "
                "sostiene la fotosíntesis en la fase de mayor demanda de carbohidratos del ciclo.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Maduración uniforme (R7-R8)",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Favorece cierre de ciclo uniforme y buen llenado final de "
                "grano.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Recuperación tras estrés hídrico o aplicación de agroquímicos",
            "productos": [
                {"producto": "FolBioestimulante", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Reactiva metabolismo general antes de continuar el programa "
                "nutricional regular.",
        },
    },

    # ------------------------------------------------------------------ #
    "Caña": {
        "Siembra": {
            "requerimiento_fisiologico": "Enraizamiento y macollamiento vigoroso desde la brotación de la semilla",
            "productos": [
                {"producto": "Kinefol", "dosis": "1 L/ha (aplicación a la semilla o surco de siembra)"},
            ],
            "justificacion_tecnica": "Un sistema radicular activo desde la brotación determina el "
                "número final de tallos por macolla.",
        },
        "Vegetativo": {
            "requerimiento_fisiologico": "Nutrición multielemento para maximizar el número de tallos (macollamiento)",
            "productos": [
                {"producto": "Fol-5", "dosis": "1.5 L/ha"},
                {"producto": "FolBoroZinc", "dosis": "1 kg/ha"},
            ],
            "justificacion_tecnica": "El balance N-K y micronutrientes sostiene el macollamiento "
                "activo, base de la población de tallos que definirá el rendimiento en toneladas "
                "por hectárea.",
        },
        "Gran crecimiento": {
            "requerimiento_fisiologico": "Máxima demanda energética y de biomasa del ciclo (elongación de tallos)",
            "productos": [
                {"producto": "FolCaña", "dosis": "4 L/ha"},
                {"producto": "Fol-5", "dosis": "1 L/ha"},
            ],
            "justificacion_tecnica": "FolCaña aporta el paquete NPK + Ca + Mg + Zn + aminoácidos + "
                "balance hormonal (auxinas, giberelinas, citoquininas) que la caña exige en su fase "
                "de mayor acumulación de biomasa; el refuerzo de Fol-5 sostiene la actividad "
                "fotosintética y el desarrollo radicular en simultáneo con la elongación de tallos.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Concentración de sacarosa sin exceso de nitrógeno",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "El Potasio es determinante en la conversión y concentración de "
                "sacarosa; se evita nitrógeno tardío para no prolongar el crecimiento vegetativo en "
                "detrimento del contenido de azúcar.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Recuperación tras quema, corte o estrés hídrico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Acelera la reactivación fisiológica de la soca tras el corte o "
                "eventos de estrés.",
        },
    },

    # ------------------------------------------------------------------ #
    "Citricos": {
        "Vegetativo": {
            "requerimiento_fisiologico": "Brotación uniforme y crecimiento vegetativo activo",
            "productos": [
                {"producto": "Fol-5", "dosis": "1.5 L/ha"},
                {"producto": "Fol-Zinc", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "El Zinc es clave en la brotación cítrica (síntesis de auxinas) "
                "y el Fol-5 sostiene el crecimiento vegetativo general del flush.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Inducción floral y diferenciación de yemas",
            "productos": [
                {"producto": "Foskaprim", "dosis": "1 L/ha"},
                {"producto": "FolBoroZinc", "dosis": "1 kg/ha"},
            ],
            "justificacion_tecnica": "El fósforo favorece la inducción floral; Boro y Zinc mejoran la "
                "diferenciación de yemas florales y el futuro cuajado.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad de polen y cuajado inicial",
            "productos": [
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
            ],
            "justificacion_tecnica": "El Boro es el nutriente de mayor impacto sobre la fertilidad "
                "del polen y la retención de flor en cítricos.",
        },
        "Cuajado": {
            "requerimiento_fisiologico": "Retención de fruto y firmeza inicial",
            "productos": [
                {"producto": "FolCalcio", "dosis": "1.5 kg/ha"},
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
            ],
            "justificacion_tecnica": "El Calcio reduce la caída fisiológica de fruto pequeño; el "
                "Boro sostenido mejora el porcentaje final de cuajado.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Llenado y calidad de jugo/pulpa",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
                {"producto": "FolMagnesio", "dosis": "2 L/ha"},
            ],
            "justificacion_tecnica": "El Potasio impulsa el llenado de fruto; el Magnesio sostiene la "
                "fotosíntesis que aporta azúcares al jugo en desarrollo.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Color, grados Brix y maduración uniforme",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
                {"producto": "FolMagnesio", "dosis": "2 L/ha"},
            ],
            "justificacion_tecnica": "El binomio Potasio-Magnesio mejora simultáneamente contenido de "
                "azúcares y color de la cáscara en la recta final de maduración.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Recuperación tras estrés hídrico o térmico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Reactiva el metabolismo del árbol antes de continuar el "
                "programa nutricional regular.",
        },
    },

    # ------------------------------------------------------------------ #
    "Hortalizas": {
        "Siembra": {
            "requerimiento_fisiologico": "Enraizamiento y reserva de Boro para el ciclo",
            "productos": [
                {"producto": "Kinefol", "dosis": "1 L/ha (drench o surco de siembra)"},
                {"producto": "FolKabo Granulado", "dosis": "20 kg/ha"},
            ],
            "justificacion_tecnica": "Establecimiento uniforme del trasplante/siembra y "
                "disponibilidad temprana de Boro para todo el ciclo.",
        },
        "Vegetativo": {
            "requerimiento_fisiologico": "Balance N-K + Zn/B para crecimiento uniforme",
            "productos": [
                {"producto": "Fol-5", "dosis": "1.5 L/ha"},
                {"producto": "FolBoroZinc", "dosis": "1 kg/ha"},
            ],
            "justificacion_tecnica": "Sostiene un crecimiento vegetativo vigoroso y homogéneo, base "
                "de una buena estructura comercial posterior.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Energía (P) y diferenciación floral (B)",
            "productos": [
                {"producto": "Foskaprim", "dosis": "1 L/ha"},
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
            ],
            "justificacion_tecnica": "El fósforo sostiene la transición reproductiva; el Boro prepara "
                "la fertilidad floral con antelación.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad de polen y equilibrio hídrico",
            "productos": [
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
                {"producto": "Fol-Zinc", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Mejora la polinización efectiva y sostiene la actividad "
                "fotosintética durante la floración.",
        },
        "Cuajado": {
            "requerimiento_fisiologico": "Fortalecimiento estructural y retención de fruto/estructura comercial",
            "productos": [
                {"producto": "FolCalcio", "dosis": "1.5 kg/ha"},
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
            ],
            "justificacion_tecnica": "El Calcio reduce desórdenes fisiológicos asociados a "
                "deficiencia (necrosis apical, rajado); el Boro mejora el porcentaje de cuajado.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Movilización de azúcares y calidad de la estructura comercial",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
                {"producto": "FolCaBK", "dosis": "1.5 kg/ha"},
            ],
            "justificacion_tecnica": "El Potasio impulsa el llenado; el paquete Calcio-Boro-Potasio "
                "mejora firmeza y calidad comercial del producto final.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Concentración final de azúcares y punto óptimo de cosecha",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Favorece uniformidad de maduración y calidad comercial en el "
                "punto de corte.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Reactivación metabólica tras estrés abiótico/biótico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Acelera la recuperación fisiológica antes de continuar el "
                "programa nutricional regular.",
        },
    },

    # ------------------------------------------------------------------ #
    "Frutales": {
        "Vegetativo": {
            "requerimiento_fisiologico": "Brotación uniforme y crecimiento vegetativo activo",
            "productos": [
                {"producto": "Fol-5", "dosis": "1.5 L/ha"},
                {"producto": "Fol-Zinc", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "El Zinc favorece la brotación (síntesis de auxinas) y el Fol-5 "
                "sostiene el desarrollo vegetativo general.",
        },
        "Prefloracion": {
            "requerimiento_fisiologico": "Inducción floral y diferenciación de yemas",
            "productos": [
                {"producto": "Foskaprim", "dosis": "1 L/ha"},
                {"producto": "FolBoroZinc", "dosis": "1 kg/ha"},
            ],
            "justificacion_tecnica": "El fósforo favorece la inducción floral; Boro y Zinc mejoran la "
                "diferenciación de yemas y el futuro cuajado.",
        },
        "Floracion": {
            "requerimiento_fisiologico": "Fertilidad de polen y cuajado inicial",
            "productos": [
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
            ],
            "justificacion_tecnica": "El Boro es el nutriente de mayor impacto sobre fertilidad de "
                "polen y retención de flor en frutales.",
        },
        "Cuajado": {
            "requerimiento_fisiologico": "Retención de fruto y firmeza inicial",
            "productos": [
                {"producto": "FolCalcio", "dosis": "1.5 kg/ha"},
                {"producto": "FolKabo", "dosis": "0.4 kg/ha"},
            ],
            "justificacion_tecnica": "El Calcio reduce la caída fisiológica de fruto recién cuajado; "
                "el Boro sostenido mejora el porcentaje final de cuajado.",
        },
        "Llenado": {
            "requerimiento_fisiologico": "Llenado de fruto y actividad fotosintética sostenida",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
                {"producto": "FolMagnesio", "dosis": "2 L/ha"},
            ],
            "justificacion_tecnica": "El Potasio impulsa el llenado de fruto; el Magnesio sostiene la "
                "fotosíntesis que aporta los azúcares necesarios para ese llenado.",
        },
        "Maduracion": {
            "requerimiento_fisiologico": "Concentración de azúcares, color y calidad de cosecha",
            "productos": [
                {"producto": "FolKalium", "dosis": "1.5 L/ha"},
                {"producto": "FolCaBK", "dosis": "1.5 kg/ha"},
            ],
            "justificacion_tecnica": "El Potasio concentra azúcares; el paquete Calcio-Boro-Potasio "
                "mejora firmeza y vida de anaquel del fruto cosechado.",
        },
        "Recuperacion de estres": {
            "requerimiento_fisiologico": "Recuperación tras estrés hídrico o térmico",
            "productos": [
                {"producto": "FolBioestimulante", "dosis": "1.5 L/ha"},
            ],
            "justificacion_tecnica": "Reactiva el metabolismo del árbol antes de continuar el "
                "programa nutricional regular.",
        },
    },
}


# ============================================================================
# FUNCIÓN PRINCIPAL DEL MOTOR DE RECOMENDACIÓN
# ============================================================================
def obtener_recomendacion(cultivo: str, etapa_key: str) -> dict:
    """
    Devuelve la recomendación técnica exacta para una combinación de
    Cultivo + Etapa fenológica, con base en la matriz de conocimiento
    agronómico definida arriba.
    """
    advertencias = []

    cultivo_data = BASE_CONOCIMIENTO_AGRONOMICO.get(cultivo)
    if cultivo_data is None:
        return {
            "cultivo": cultivo,
            "etapa": etapa_key,
            "requerimiento_fisiologico": None,
            "productos": [],
            "justificacion_tecnica": None,
            "advertencias": [
                f"El cultivo '{cultivo}' no está definido en la matriz de conocimiento "
                f"agronómico. Cultivos disponibles: {list(BASE_CONOCIMIENTO_AGRONOMICO.keys())}"
            ],
        }

    etapa_data = cultivo_data.get(etapa_key)
    if etapa_data is None:
        return {
            "cultivo": cultivo,
            "etapa": etapa_key,
            "requerimiento_fisiologico": None,
            "productos": [],
            "justificacion_tecnica": None,
            "advertencias": [
                f"La etapa '{etapa_key}' no está definida para el cultivo '{cultivo}'. "
                f"Etapas disponibles: {list(cultivo_data.keys())}"
            ],
        }

    productos_enriquecidos = []
    for item in etapa_data["productos"]:
        nombre_producto = item["producto"]
        ficha = PRODUCTOS_DB.get(nombre_producto)
        if ficha is None:
            advertencias.append(
                f"El producto '{nombre_producto}' está referenciado en la matriz de "
                f"conocimiento pero no existe en PRODUCTOS_DB. Verifica que esté "
                f"correctamente cargado en tu base de datos completa de productos Folcol."
            )
        productos_enriquecidos.append({
            "producto": nombre_producto,
            "dosis": item["dosis"],
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
# EJEMPLO DE USO / AUTOVALIDACIÓN RÁPIDA
# ============================================================================
if __name__ == "__main__":
    resultado = obtener_recomendacion("Caña", "Gran crecimiento")
    print("Cultivo:", resultado["cultivo"])
    print("Etapa:", resultado["etapa"])
    print("Requerimiento fisiológico:", resultado["requerimiento_fisiologico"])
    print("Productos recomendados:")
    for p in resultado["productos"]:
        print(f"  - {p['producto']} | Dosis: {p['dosis']} | {p['ingrediente_activo']}")
    print("Justificación técnica:", resultado["justificacion_tecnica"])
    if resultado["advertencias"]:
        print("⚠ Advertencias:", resultado["advertencias"])

    print("\n--- Validación cruzada de toda la matriz contra PRODUCTOS_DB ---")
    total_advertencias = 0
    for cultivo in BASE_CONOCIMIENTO_AGRONOMICO:
        for etapa in BASE_CONOCIMIENTO_AGRONOMICO[cultivo]:
            r = obtener_recomendacion(cultivo, etapa)
            if r["advertencias"]:
                total_advertencias += len(r["advertencias"])
                for a in r["advertencias"]:
                    print(f"[{cultivo} / {etapa}] {a}")
    print(f"\nTotal de advertencias encontradas: {total_advertencias}")
