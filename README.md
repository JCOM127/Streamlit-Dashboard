# Dashboard de Decisión de Inversión — Colombia

Dashboard interactivo en **Streamlit** que responde a la pregunta:
**¿En qué Región × Categoría conviene invertir y por qué?**

Basado en un dataset de 500 proyectos de desarrollo en las 5 regiones naturales de Colombia (Andina, Caribe, Pacífica, Orinoquía, Amazonía) y 6 categorías sectoriales (Educación, Energía, Infraestructura, Medio Ambiente, Salud, Tecnología).

---

## Vista general

El dashboard combina **cuatro visualizaciones complementarias** para guiar una decisión de inversión:

| Sección | Pregunta que responde | Tipo de gráfico |
|---|---|---|
| **Recomendación principal** | ¿Cuál es la mejor combinación por score? | Callout con frase accionable |
| **KPIs** | Top combo · Mejor región · Promedio nacional · Tamaño de muestra | Métricas |
| **Mapa de Colombia** | ¿Qué región rinde mejor en promedio? | Scattergeo con burbujas |
| **Heatmap Categoría × Región** | ¿Dónde se cruzan los picos? | Heatmap con anotación del óptimo |
| **Violín por sector** | ¿Cómo se distribuyen los resultados en cada sector dentro de una región? | Violin plot + semáforo de variabilidad |
| **Ranking top 8** | ¿Cuáles son las mejores combinaciones por score? | Tabla con gradiente |

---

## Conceptos del score de inversión

El usuario controla dos pesos en la sidebar:

- **Impacto** — Promedio del Nivel_Impacto (Bajo=1 · Medio=2 · Alto=3) de los proyectos en cada Región × Categoría. *Más alto = mejor desempeño promedio.*
- **Consistencia** — Inverso de la desviación estándar normalizada. Mide qué tan **predecibles** son los resultados. *Más alto = menos riesgo.* Baja consistencia = "ruleta": algunos exitazos y algunos fracasos en la misma combinación.

`Score = w₁ · impacto_norm + w₂ · consistencia_norm` (normalizado min-max sobre el set filtrado).

Sube el peso de **impacto** si buscas máximo rendimiento esperado. Sube el peso de **consistencia** si priorizas minimizar el riesgo.

---

## Decisiones de diseño visual

- **Paleta secuencial Purples** (single-hue, luminance-based) → segura para daltonismo en mapa y heatmap.
- **Paleta cualitativa Paul Tol "muted"** (`#332288 · #117733 · #CC6677 · #DDCC77 · #88CCEE`) para distinguir categorías de forma colorblind-safe.
- **Redundancia visual** (Tufte / WCAG 1.4.1 "Use of Color"): el óptimo del heatmap se señala con flecha + caja + texto + símbolo ◆, no solo con color.
- **Contraste**: todo el texto cumple WCAG AA o AAA sobre su fondo. El gris secundario es `#4A4A4A` (9.0:1 sobre blanco, AAA).
- **Tema claro forzado** vía `.streamlit/config.toml` — el dashboard se ve igual en macOS dark, Windows light, o cualquier sistema.
- **Bordes negros 1.5 px** en todas las cards para presentación con proyector en aulas iluminadas.
- **Semáforo 🟢🟡🔴** traduce el coeficiente de variación (CV) a "Predecible / Mixto / Variable" para audiencia no técnica.

---

## Instalación local

```bash
git clone https://github.com/JCOM127/Streamlit-Dashboard.git
cd Streamlit-Dashboard

python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Abre automáticamente en `http://localhost:8501`. Para detener: `Ctrl+C` en la terminal.

---

## Estructura del repositorio

```
.
├── app.py                              # Dashboard principal Streamlit
├── requirements.txt                    # Dependencias Python
├── dataset_evaluacion_unidad1.csv      # Dataset base (500 proyectos)
├── .streamlit/
│   └── config.toml                     # Tema y configuración Streamlit
├── .gitignore
└── README.md
```

---

## Despliegue en Streamlit Community Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io) y conecta tu cuenta de GitHub.
2. Click en **"New app"** → selecciona el repo `JCOM127/Streamlit-Dashboard`.
3. Configura:
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **Python version**: 3.11 (recomendado)
4. Click **"Deploy"**. En 1–2 minutos la app queda pública en una URL tipo `https://[nombre].streamlit.app`.

Streamlit Cloud lee `requirements.txt` y `.streamlit/config.toml` automáticamente.

---

## Stack técnico

- [Streamlit](https://streamlit.io/) — framework de UI
- [Plotly](https://plotly.com/python/) — visualizaciones interactivas (mapa, heatmap, violín)
- [Pandas](https://pandas.pydata.org/) — manipulación de datos
- [NumPy](https://numpy.org/) — operaciones numéricas

---

## Dataset

`dataset_evaluacion_unidad1.csv` — 500 proyectos con columnas:

| Columna | Tipo | Descripción |
|---|---|---|
| `ID_Proyecto` | string | Identificador único |
| `Fecha_Inicio` | date | Fecha de inicio del proyecto |
| `Region` | string | Región natural (Caribe, Andina, Pacífica, Orinoquía, Amazonía) |
| `Departamento` | string | Departamento administrativo |
| `Categoria` | string | Sector (6 categorías) |
| `Estado` | string | En Ejecución · Finalizado · Retrasado · En Planeación |
| `Presupuesto_USD` | float | Presupuesto en dólares |
| `Poblacion_Beneficiada` | int | Número de personas beneficiadas |
| `Nivel_Impacto` | string | Bajo · Medio · Alto (codificado 1/2/3 para análisis) |
