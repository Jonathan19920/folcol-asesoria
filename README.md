# Folcol — App de Asesoría Técnico-Comercial

Aplicación web (Streamlit) para generar recomendaciones técnicas de fertilización
a partir del portafolio de productos Folcol, con reporte final en PDF corporativo
(logo, datos del agricultor/finca/vendedor y tabla de recomendación).

## Estructura del proyecto

```
folcol_app/
├── app.py                      # App principal de Streamlit (interfaz)
├── generador_pdf.py            # Módulo que construye el PDF corporativo (FPDF2)
├── etapas_fenologicas.py       # Diccionarios de cultivos y etapas fenológicas
├── logo.png                    # Logo de Folcol (usado en la app y en el PDF)
├── requirements.txt            # Dependencias
├── data/
│   └── productos_folcol.csv    # Base de datos de fichas técnicas (editable)
└── README.md
```

## 1. Cómo correrla localmente

```bash
# 1. Crear entorno virtual (opcional pero recomendado)
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar
streamlit run app.py
```

Se abrirá automáticamente en `http://localhost:8501`.

## 2. Estructura del archivo de Fichas Técnicas (Excel/CSV)

La app lee un archivo con **separador `;`** (o lo detecta automáticamente si subes
un CSV con otro separador) y las siguientes columnas obligatorias:

| Columna               | Descripción                                                                 | Ejemplo                                  |
|------------------------|-----------------------------------------------------------------------------|-------------------------------------------|
| `producto`             | Nombre comercial del producto                                              | FolKalium                                 |
| `linea`                | Línea de producto                                                          | FOLES                                     |
| `ingrediente_activo`   | Nutriente(s) y concentración                                               | Potasio (K2O) 500 g/L                     |
| `concentracion`        | Grado o concentración                                                      | 0-0-50                                    |
| `dosis_recomendada`    | Dosis sugerida                                                             | 1.0 - 2.0 L/ha                            |
| `unidad_dosis`         | Unidad de la dosis                                                         | L/ha                                      |
| `momento_aplicacion`   | Texto libre describiendo cuándo aplicar                                    | Llenado de fruto o grano                  |
| `via_aplicacion`       | Foliar, fertirriego, al suelo, drench, etc.                                | Foliar o fertirriego                      |
| `cultivos_objetivo`    | Lista de cultivos separada por comas (debe coincidir con los nombres de la app: `Tomate, Maiz, Soya, Caña, Citricos, Hortalizas, Frutales`) | Tomate,Maiz,Soya |
| `etapas_objetivo`      | Lista de etapas separada por comas (**sin tildes**, deben coincidir con las `key` internas — ver tabla abajo) | Floracion,Cuajado |
| `beneficio_principal`  | Frase corta del beneficio agronómico principal                             | Favorece el cuajado de frutos             |
| `registro_ica`         | Registro ICA si aplica (o "N/A")                                           | 11008                                     |

### Claves internas (`key`) de etapas fenológicas válidas

`Siembra`, `Establecimiento`, `Enraizamiento`, `Vegetativo`, `Prefloracion`,
`Floracion`, `Cuajado`, `Formacion de vainas`, `Llenado`, `Gran crecimiento`,
`Maduracion`, `Desarrollo`, `Recuperacion de estres`

> Puedes ver el detalle completo de las etapas por cultivo (y agregar o modificar
> ciclos fenológicos) editando el archivo `etapas_fenologicas.py`.

### Cargar tu propio archivo actualizado

En la barra lateral izquierda de la app hay un botón **"Cargar archivo de Fichas
Técnicas"** que permite subir un Excel (`.xlsx`) o CSV actualizado sin tocar el
código. Si no se sube ningún archivo, la app usa automáticamente
`data/productos_folcol.csv` (ya cargado con el portafolio actual de Folcol).

## 3. Flujo de uso

1. El vendedor diligencia sus datos, el cultivo, la etapa fenológica, la finca,
   el agricultor y el área.
2. Al presionar **"Generar recomendación técnica"**, la app filtra la base de
   datos y muestra los productos sugeridos para esa combinación cultivo/etapa.
3. El vendedor puede ajustar la selección (agregar o quitar productos) usando
   el campo de selección múltiple.
4. Al presionar **"Generar PDF de recomendación"**, se construye el documento
   final con el logo de Folcol, los datos generales y la tabla técnica.
5. El botón **"Descargar Recomendación en PDF"** entrega el archivo listo para
   compartir con el agricultor.

## 4. Despliegue en la nube (Streamlit Community Cloud) — Recomendado

Streamlit Community Cloud es gratuito y es la forma más simple de que todo el
equipo comercial acceda a la app desde un enlace, sin instalar nada.

### Paso a paso

1. **Crear un repositorio en GitHub**
   - Crea una cuenta en [github.com](https://github.com) si no tienes una.
   - Crea un nuevo repositorio (puede ser privado), por ejemplo `folcol-asesoria-tecnica`.
   - Sube TODOS los archivos de esta carpeta (`app.py`, `generador_pdf.py`,
     `etapas_fenologicas.py`, `logo.png`, `requirements.txt`, y la carpeta `data/`)
     manteniendo la misma estructura de carpetas.
     - Opción rápida vía web: en GitHub, botón "Add file" → "Upload files", y
       arrastras todo el contenido de la carpeta `folcol_app/`.
     - Opción por terminal:
       ```bash
       cd folcol_app
       git init
       git add .
       git commit -m "App inicial Folcol"
       git branch -M main
       git remote add origin https://github.com/TU_USUARIO/folcol-asesoria-tecnica.git
       git push -u origin main
       ```

2. **Crear la app en Streamlit Community Cloud**
   - Ingresa a [share.streamlit.io](https://share.streamlit.io) e inicia sesión
     con tu cuenta de GitHub.
   - Clic en **"New app"**.
   - Selecciona el repositorio `folcol-asesoria-tecnica`, la rama `main` y el
     archivo principal `app.py`.
   - Clic en **"Deploy"**.
   - En 1-2 minutos la app quedará publicada en una URL tipo:
     `https://folcol-asesoria-tecnica.streamlit.app`

3. **Compartir el enlace**
   - Copia esa URL y compártela con todo el equipo comercial. Podrán acceder
     desde cualquier computador o celular con navegador, sin instalar nada.
   - Cada vez que actualices el archivo `data/productos_folcol.csv` (o
     cualquier otro archivo) en GitHub, la app se actualiza automáticamente
     (o puedes forzar el redeploy desde el panel de Streamlit Cloud, botón
     "Reboot app").

### Actualizar el portafolio de productos sin tocar código

Hay dos formas:
- **Opción rápida (temporal):** cada vendedor sube su propio Excel/CSV
  actualizado directamente desde la barra lateral de la app.
- **Opción permanente (recomendada):** editar el archivo
  `data/productos_folcol.csv` directamente en GitHub (botón de lápiz "Edit")
  y hacer commit. La app en la nube tomará el cambio automáticamente.

## 5. Despliegue alternativo en Render

Si prefieres Render en vez de Streamlit Cloud:

1. Sube el proyecto a GitHub (igual que el paso 1 anterior).
2. En [render.com](https://render.com), clic en **"New" → "Web Service"**.
3. Conecta tu repositorio de GitHub.
4. Configura:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. Clic en **"Create Web Service"**. Render asignará una URL pública tipo
   `https://folcol-asesoria-tecnica.onrender.com`.

> Nota: en el plan gratuito de Render, el servicio puede "dormirse" tras un
> periodo de inactividad y tardar unos segundos en despertar en el primer
> acceso del día. Streamlit Community Cloud no tiene esa limitación para uso
> normal de equipos pequeños/medianos.

## 6. Personalización rápida

- **Colores corporativos:** editar las variables `VERDE_OSCURO` / `VERDE_CLARO`
  en `app.py` (interfaz) y en `generador_pdf.py` (PDF).
- **Nuevos cultivos o etapas:** editar `etapas_fenologicas.py`.
- **Nuevos productos:** editar `data/productos_folcol.csv` (o subir un archivo
  actualizado desde la app).
- **Datos de contacto / dirección en el PDF y footer:** editar el pie de página
  en `generador_pdf.py` y el `st.caption` final de `app.py`.
