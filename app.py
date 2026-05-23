"""
Dashboard de decisión de inversión — Colombia
Pregunta: ¿En qué Región × Categoría conviene invertir y por qué?

Run:
    streamlit run app.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------- Config ----------
st.set_page_config(
    page_title="¿Dónde invertir? · Impacto por región y categoría",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSV_PATH = Path(__file__).parent / "dataset_evaluacion_unidad1.csv"
IMPACT_MAP = {"Bajo": 1, "Medio": 2, "Alto": 3}
# Paletas accesibles (WCAG AA + colorblind-safe)
# - Sequential (mapa, heatmap): Purples es single-hue, luminance-based → CVD-safe
# - Qualitative (box plot por región): Okabe-Ito vía Plotly "Safe", indistinguible solo por color → diseñada para CVD
SEQ = "Purples"
QUAL_CB_SAFE = [
    "#332288",  # azul oscuro
    "#117733",  # verde
    "#DDCC77",  # arena
    "#CC6677",  # rosado
    "#88CCEE",  # cian
]  # Paul Tol "muted" — colorblind-safe, ordenado por luminancia
ACCENT = "#D7263D"        # rojo accent solo para destacar (siempre con flecha/borde, no solo color)
INK = "#1A1A1A"           # texto principal — 17.4:1 sobre blanco (AAA)
MUTED = "#4A4A4A"         # texto secundario — 9.0:1 sobre blanco (AAA)
BG_CARD = "#FFFFFF"

# Centroides aproximados regiones naturales de Colombia
CENTROIDS = {
    "Caribe":    (10.0, -74.5),
    "Andina":    ( 5.5, -75.0),
    "Pacífica":  ( 4.0, -77.0),
    "Orinoquía": ( 5.0, -71.0),
    "Amazonía":  (-1.0, -72.0),
}

# ---------- Estilos ----------
st.markdown(f"""
<style>
  /* ===== Main area ===== */
  .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px;
                      background: #FAFAFA; }}
  h1, h2, h3, h4 {{ color: {INK} !important; letter-spacing: -0.01em; }}
  p, span, label, li {{ color: {INK}; }}

  /* ===== Metric cards (KPI) — altura flexible para que no se corte el texto ===== */
  div[data-testid="stMetric"] {{
    background: {BG_CARD}; border: 1.5px solid #1A1A1A; border-radius: 8px;
    padding: 14px 16px;
    height: 100%;
    display: flex; flex-direction: column; justify-content: flex-start;
    overflow: visible !important;
  }}
  div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] > div,
  div[data-testid="stMetricLabel"] p {{
    color: {INK} !important; font-weight: 600 !important; font-size: 13px !important;
    opacity: 1 !important;
    white-space: normal !important; overflow: visible !important;
  }}
  div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] > div {{
    color: {INK} !important; font-weight: 700 !important;
    font-size: 1.35rem !important; line-height: 1.25 !important;
    white-space: normal !important; word-break: break-word; overflow-wrap: anywhere;
    overflow: visible !important;
  }}
  div[data-testid="stMetricDelta"], div[data-testid="stMetricDelta"] > div,
  div[data-testid="stMetricDelta"] svg {{
    color: {MUTED} !important; fill: {MUTED} !important; font-weight: 500 !important;
    white-space: normal !important;
  }}

  /* ===== Captions (la línea bajo el título y otras) ===== */
  div[data-testid="stCaptionContainer"], .stCaption,
  div[data-testid="stCaptionContainer"] p {{
    color: {MUTED} !important; font-size: 13px !important; opacity: 1 !important;
  }}

  /* ===== Sidebar — alto contraste sobre fondo lavanda claro ===== */
  section[data-testid="stSidebar"] {{
    background: #F0EFF4 !important;
    border-right: 1px solid #D9D9D9;
  }}
  section[data-testid="stSidebar"] *,
  section[data-testid="stSidebar"] p,
  section[data-testid="stSidebar"] label,
  section[data-testid="stSidebar"] span,
  section[data-testid="stSidebar"] div {{
    color: {INK} !important;
  }}
  section[data-testid="stSidebar"] .stCaption,
  section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] p {{
    color: {MUTED} !important; font-size: 13px !important;
  }}
  section[data-testid="stSidebar"] h1,
  section[data-testid="stSidebar"] h2,
  section[data-testid="stSidebar"] h3 {{ color: {INK} !important; }}

  /* Sliders ticks */
  section[data-testid="stSidebar"] [data-baseweb="slider"] div {{ color: {INK} !important; }}

  /* ===== Componentes propios ===== */
  .subq {{ font-size: 18px; font-weight: 600; color: {INK}; margin: 0 0 4px 0; }}
  .subn {{ font-size: 13px; color: {MUTED}; margin: 0 0 8px 0; line-height: 1.4; }}
  .callout {{ background: #FFF1F3; border-left: 4px solid {ACCENT};
              padding: 14px 18px; font-size: 15px; border-radius: 4px; margin: 8px 0 4px;
              color: {INK}; }}
  .callout strong {{ color: #A8001E; font-weight: 700; }}
  .foot {{ font-size: 12px; color: {MUTED}; margin-top: 10px; line-height: 1.5; }}

  /* ===== Tabla / dataframe ===== */
  div[data-testid="stDataFrame"] {{ color: {INK}; }}

  /* ===== Cards de los gráficos (mapa, heatmap, violín) — borde negro ===== */
  div[data-testid="stPlotlyChart"] {{
    border: 1.5px solid #1A1A1A;
    border-radius: 8px;
    background: {BG_CARD};
    padding: 10px;            /* más aire entre el chart y el borde negro */
    margin-bottom: 32px;
    overflow: hidden;          /* recorta el blanco del chart en las esquinas redondeadas */
  }}

  /* ===== Multiselect: chips rojos con texto blanco (contraste 9:1) ===== */
  span[data-baseweb="tag"] {{
    background-color: #A8001E !important;
    color: #FFFFFF !important;
    border: 1px solid #A8001E !important;
  }}
  span[data-baseweb="tag"] *,
  span[data-baseweb="tag"] span,
  span[data-baseweb="tag"] div {{
    color: #FFFFFF !important;
  }}
  span[data-baseweb="tag"] svg,
  span[data-baseweb="tag"] path {{
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
  }}
  /* Hover sobre la "x" de eliminar */
  span[data-baseweb="tag"] [role="button"]:hover {{
    background-color: rgba(255,255,255,0.2) !important;
  }}

  /* ===== Slider: valor numérico sobre el thumb ===== */
  div[data-baseweb="slider"] [role="slider"] {{
    background-color: #A8001E !important;
    border-color: #A8001E !important;
  }}
  /* Tooltip del slider — texto blanco sobre fondo rojo */
  div[data-baseweb="slider"] div[data-testid="stTickBarMin"],
  div[data-baseweb="slider"] div[data-testid="stTickBarMax"] {{
    color: {INK} !important;
  }}
</style>
""", unsafe_allow_html=True)

# ---------- Data ----------
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["impacto_num"] = df["Nivel_Impacto"].map(IMPACT_MAP)
    df["Fecha_Inicio"] = pd.to_datetime(df["Fecha_Inicio"], errors="coerce")
    df["Año"] = df["Fecha_Inicio"].dt.year
    df["Trimestre"] = df["Fecha_Inicio"].dt.to_period("Q").astype(str)
    return df

df = load_data(CSV_PATH)

# ---------- Sidebar (filtros de decisión) ----------
with st.sidebar:
    st.markdown("### Filtros de decisión")
    st.markdown(
        f"<p style='color:{MUTED};font-size:13px;margin:-6px 0 12px 0;line-height:1.4'>"
        f"Acota el universo de proyectos antes de comparar.</p>",
        unsafe_allow_html=True,
    )

    estados = sorted(df["Estado"].unique())
    sel_estados = st.multiselect(
        "Estado del proyecto",
        estados, default=estados,
        help="¿Qué tipo de proyectos cuentan como evidencia? (ej. solo Finalizados para evidencia consolidada)",
    )

    años = sorted(df["Año"].dropna().unique().astype(int))
    if años:
        a_min, a_max = int(min(años)), int(max(años))
        rango = st.slider("Año de inicio", a_min, a_max, (a_min, a_max))
    else:
        rango = None

    st.markdown("---")
    st.markdown(
        f"<p style='color:{INK};font-size:14px;font-weight:600;margin:0 0 6px 0'>"
        f"Ponderación del score de inversión</p>",
        unsafe_allow_html=True,
    )
    with st.expander("¿Qué significan impacto y consistencia?", expanded=False):
        st.markdown(
            f"""
<div style='color:{INK};font-size:13px;line-height:1.55'>
<b>Impacto</b> — Promedio del Nivel_Impacto (Bajo=1, Medio=2, Alto=3) de los
proyectos en cada Región × Categoría. <i>Más alto = mejor desempeño promedio.</i><br><br>

<b>Consistencia</b> — Inverso de la desviación estándar del impacto, normalizado.
Mide qué tan <i>predecibles</i> son los resultados. <i>Más alto = los proyectos
rinden parecido entre sí (menos riesgo).</i> Baja consistencia significa "ruleta":
algunos exitazos y algunos fracasos en la misma combinación.<br><br>

<b>Score</b> = w₁·impacto + w₂·consistencia (normalizados min-max). Sube el peso
de <b>impacto</b> si buscas máximo rendimiento esperado; sube el peso de
<b>consistencia</b> si priorizas minimizar el riesgo.
</div>
            """,
            unsafe_allow_html=True,
        )
    w_imp = st.slider("Peso: impacto promedio", 0.0, 1.0, 0.6, 0.05,
                      help="Cuánto pesa el rendimiento promedio en el score.")
    w_cons = st.slider("Peso: consistencia (1 − desviación)", 0.0, 1.0, 0.4, 0.05,
                       help="Cuánto pesa la baja volatilidad (predictibilidad) en el score.")
    st.markdown(
        f"<p style='color:{MUTED};font-size:12px;margin:4px 0 0 0'>"
        f"Total: {w_imp + w_cons:.2f} (se normaliza)</p>",
        unsafe_allow_html=True,
    )

# Aplicar filtros
mask = df["Estado"].isin(sel_estados)
if rango:
    mask &= df["Año"].between(rango[0], rango[1])
fdf = df[mask].copy()

if fdf.empty:
    st.warning("No hay proyectos con los filtros actuales.")
    st.stop()

# ---------- Cálculos clave ----------
agg = (fdf.groupby(["Region", "Categoria"])["impacto_num"]
         .agg(["mean", "std", "count"])
         .reset_index())
agg["std"] = agg["std"].fillna(0)

# Score normalizado (min-max sobre el set filtrado)
def mm(s):
    rng = s.max() - s.min()
    return (s - s.min()) / rng if rng else pd.Series(0.5, index=s.index)

agg["impacto_norm"] = mm(agg["mean"])
agg["consistencia_norm"] = mm(-agg["std"])  # menos desviación = mejor
w_sum = w_imp + w_cons or 1
agg["score"] = (w_imp * agg["impacto_norm"] + w_cons * agg["consistencia_norm"]) / w_sum

top = agg.sort_values("score", ascending=False).iloc[0]
region_mean = fdf.groupby("Region")["impacto_num"].mean().round(3)
prom_nacional = fdf["impacto_num"].mean()

# ---------- Header ----------
st.markdown("# ¿En qué región y categoría conviene invertir?")
st.markdown(
    f"<p style='color:{MUTED};font-size:14px;margin:-8px 0 16px 0;line-height:1.5'>"
    f"Decisión basada en <b style='color:{INK}'>{len(fdf)} proyectos</b> · "
    f"Escala impacto: Bajo=1 · Medio=2 · Alto=3 · "
    f"Score = {w_imp/w_sum:.0%} impacto + {w_cons/w_sum:.0%} consistencia</p>",
    unsafe_allow_html=True,
)

# Recomendación principal (callout verde — afirma la acción a tomar)
st.markdown(
    f"<div class='callout' style='border-left-color:#117733; background:#EEF7EF; "
    f"margin-bottom:32px'>"
    f"<strong style='color:#0E5A28'>Recomendación principal:</strong> invertir en "
    f"<strong style='color:#0E5A28'>{top['Region']} × {top['Categoria']}</strong> — "
    f"impacto promedio {top['mean']:.2f} (vs. nacional {prom_nacional:.2f}), "
    f"desviación {top['std']:.2f}, evidencia sobre {int(top['count'])} proyectos."
    f"</div>",
    unsafe_allow_html=True,
)

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Top combinación", f"{top['Region']} · {top['Categoria']}", f"score {top['score']:.2f}")
k2.metric("Mejor región", region_mean.idxmax(), f"{region_mean.max():.2f} prom.")
k3.metric("Promedio nacional", f"{prom_nacional:.2f}", "escala 1–3")
k4.metric("Proyectos en muestra", f"{len(fdf)}", f"{fdf['Region'].nunique()} regiones")

st.markdown("---")

# ---------- Row 1: Mapa + Heatmap ----------
col_map, col_heat = st.columns(2)

# --- 1. MAPA ---
with col_map:
    st.markdown("<p class='subq'>¿Qué región rinde mejor en promedio?</p>", unsafe_allow_html=True)
    st.markdown("<p class='subn'>Tamaño y color = impacto promedio · clic en cada burbuja para ver el dato</p>", unsafe_allow_html=True)

    rm = region_mean.reset_index().rename(columns={"impacto_num": "Impacto"})
    rm["lat"] = rm["Region"].map(lambda r: CENTROIDS[r][0])
    rm["lon"] = rm["Region"].map(lambda r: CENTROIDS[r][1])

    fig_map = go.Figure(go.Scattergeo(
        lat=rm["lat"], lon=rm["lon"],
        text=[f"<b>{r}</b><br>Impacto: {v:.2f}" for r, v in zip(rm["Region"], rm["Impacto"])],
        hoverinfo="text",
        mode="markers+text",
        textposition=["bottom center" if r == "Pacífica" else "top center"
                      for r in rm["Region"]],
        textfont=dict(size=13, color=INK, family="-apple-system, Inter, sans-serif"),
        marker=dict(
            # Normalización min-max → mapeo a [20, 54] px. Estira un rango
            # comprimido (Δ≈0.21) a 34 px de diferencia entre extremos.
            size=20 + ((rm["Impacto"] - rm["Impacto"].min())
                       / max(rm["Impacto"].max() - rm["Impacto"].min(), 1e-9)) * 34,
            color=rm["Impacto"],
            colorscale=SEQ,
            cmin=float(rm["Impacto"].min()),
            cmax=float(rm["Impacto"].max()),
            showscale=False,   # el heatmap al lado ya muestra la escala
            line=dict(color="#1A1A1A", width=1.2),
        ),
    ))
    fig_map.update_layout(
        margin=dict(l=12, r=12, t=12, b=30), height=460,
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(
            scope="south america",
            showcountries=True, countrycolor="#BBBBBB",
            showland=True, landcolor="#E2E2E2",
            showocean=True, oceancolor="#F4F4F4",
            showframe=False,
            domain=dict(x=[0, 1], y=[0, 1]),   # ocupa toda la tarjeta
            lataxis=dict(range=[-4.5, 13]),
            lonaxis=dict(range=[-80, -66]),
            projection_type="mercator",
        ),
    )
    st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})

# --- 2. HEATMAP ---
with col_heat:
    st.markdown("<p class='subq'>¿Dónde se cruzan los picos?</p>", unsafe_allow_html=True)
    st.markdown("<p class='subn'>Impacto promedio por Categoría × Región · celda señalada = óptimo de inversión</p>", unsafe_allow_html=True)

    pivot = (fdf.groupby(["Categoria", "Region"])["impacto_num"].mean()
                .unstack().round(2))

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=SEQ,
        zmin=float(np.nanmin(pivot.values)), zmax=float(np.nanmax(pivot.values)),
        colorbar=dict(title=dict(text="Impacto", font=dict(size=13, color=INK)),
                      thickness=12, len=0.7, tickfont=dict(size=12, color=INK)),
        hovertemplate="<b>%{y} · %{x}</b><br>Impacto: %{z:.2f}<extra></extra>",
        xgap=3, ygap=3,
    ))
    # Anotar valores. Umbral basado en luminancia de Purples:
    # cuando la celda cae por encima del 55% del rango, el fondo es lo bastante oscuro
    # para necesitar texto blanco (contraste >= 4.5:1 → AA).
    annotations = []
    zmin_v = float(np.nanmin(pivot.values))
    zmax_v = float(np.nanmax(pivot.values))
    threshold = zmin_v + 0.55 * (zmax_v - zmin_v)
    for i, cat in enumerate(pivot.index):
        for j, reg in enumerate(pivot.columns):
            v = pivot.values[i, j]
            if np.isnan(v):
                continue
            annotations.append(dict(
                x=reg, y=cat, text=f"{v:.2f}", showarrow=False,
                font=dict(size=13,
                          color="#FFFFFF" if v >= threshold else INK,
                          family="-apple-system, Inter, sans-serif"),
            ))
    # Destacar la top combinación — redundante con forma (flecha + caja + texto)
    # para no depender solo del color (criterio WCAG 1.4.1 "Use of Color")
    annotations.append(dict(
        x=top["Region"], y=top["Categoria"],
        ax=55, ay=-38, text="◆ óptimo", showarrow=True,
        arrowhead=2, arrowcolor="#1A1A1A", arrowwidth=2.5,
        arrowside="end",
        standoff=18,  # detiene la punta 18 px antes del centro → aterriza arriba del número
        font=dict(size=12, color="#FFFFFF", family="-apple-system, Inter, sans-serif"),
        bgcolor="#1A1A1A", bordercolor="#1A1A1A", borderwidth=1.5, borderpad=5,
    ))
    fig_heat.update_layout(
        margin=dict(l=130, r=30, t=22, b=60), height=460,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, Inter, sans-serif", size=12, color=INK),
        annotations=annotations,
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

# ---------- Row 2: Violin plot — distribución de impacto por sector en una región ----------
# Spacer: empuja toda la sección 2 (violín) 2px hacia abajo
st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
st.markdown("<p class='subq'>¿Cómo se distribuyen los resultados en cada sector?</p>",
            unsafe_allow_html=True)
st.markdown(
    "<p class='subn'>Selecciona una región. Cada violín muestra la distribución de "
    "impacto de los proyectos en ese sector: forma angosta y alta = resultados "
    "parecidos · forma ancha o doble = resultados dispares.</p>",
    unsafe_allow_html=True,
)

ctrl_l, ctrl_r = st.columns([1, 2])
with ctrl_l:
    regs_disponibles = sorted(fdf["Region"].unique())
    default_reg_idx = (regs_disponibles.index(top["Region"])
                       if top["Region"] in regs_disponibles else 0)
    region_sel = st.selectbox(
        "Región a inspeccionar",
        regs_disponibles, index=default_reg_idx,
    )
with ctrl_r:
    cats_disponibles = sorted(fdf["Categoria"].unique())
    cats_sel = st.multiselect(
        "Sectores a comparar",
        cats_disponibles, default=cats_disponibles,
        help="Quita sectores para enfocar la comparación.",
    )

vdf = fdf[(fdf["Region"] == region_sel) & (fdf["Categoria"].isin(cats_sel))].copy()

if vdf.empty or not cats_sel:
    st.info("No hay datos para esta combinación. Ajusta los selectores.")
else:
    cats_orden = [c for c in cats_disponibles if c in cats_sel]

    fig_v = go.Figure()
    for cat in cats_orden:
        sub = vdf[vdf["Categoria"] == cat]
        if sub.empty:
            continue
        fig_v.add_trace(go.Violin(
            y=sub["impacto_num"],
            name=cat,
            box_visible=False,
            meanline_visible=False,
            points=False,
            line_color="#1A1A1A",
            line_width=1.8,
            fillcolor="rgba(74,55,119,0.70)",
            opacity=1,
            spanmode="hard",
            bandwidth=0.20,        # KDE más sensible → picos más marcados
            scalegroup="all",       # comparte escala entre violines
            scalemode="count",      # ancho proporcional a número de proyectos
            width=0.3,             # ancho del violín (0–1)
            hovertemplate=f"<b>{cat}</b><br>Impacto: %{{y:.0f}}<extra></extra>",
        ))

    for y in (1, 2, 3):
        fig_v.add_hline(y=y, line_dash="dot", line_color="#D9D9D9", line_width=1)

    fig_v.update_layout(
        margin=dict(l=60, r=20, t=12, b=30), height=440,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, Inter, sans-serif", size=13, color=INK),
        showlegend=False,
        xaxis=dict(
            tickfont=dict(size=12, color=INK),
            gridcolor="#FFFFFF", title="",
        ),
        yaxis=dict(
            title=dict(text="Nivel de impacto", font=dict(size=13, color=INK)),
            tickvals=[1, 2, 3], ticktext=["Bajo", "Medio", "Alto"],
            tickfont=dict(size=12, color=INK),
            range=[0.5, 3.5], gridcolor="#FFFFFF",
        ),
        violinmode="group",
    )
    st.plotly_chart(fig_v, use_container_width=True, config={"displayModeBar": False})

    # Semáforo: CV por sector dentro de la región seleccionada
    var = (vdf.groupby("Categoria")["impacto_num"]
              .agg(mean="mean", std="std", n="count")
              .reset_index())
    var["std"] = var["std"].fillna(0)
    var["cv"] = (var["std"] / var["mean"]).fillna(0)

    if len(var) >= 2:
        q33 = var["cv"].quantile(0.33)
        q66 = var["cv"].quantile(0.66)
    else:
        q33 = q66 = float(var["cv"].iloc[0])

    def etiqueta_cv(cv):
        if cv <= q33: return ("🟢", "Predecible")
        if cv <= q66: return ("🟡", "Mixto")
        return ("🔴", "Variable")

    mas_pred = var.sort_values("cv").iloc[0]
    mas_var = var.sort_values("cv", ascending=False).iloc[0]
    chip_p, lab_p = etiqueta_cv(mas_pred["cv"])
    chip_v, lab_v = etiqueta_cv(mas_var["cv"])

    # Proporciones del sector más predecible — lenguaje "de cada 10"
    pico = vdf[vdf["Categoria"] == mas_pred["Categoria"]]
    if not pico.empty:
        dist = pico["Nivel_Impacto"].value_counts(normalize=True)
        partes = " · ".join(
            f"{int(round(dist.get(lvl, 0)*10))} de 10 {lvl}"
            for lvl in ["Alto", "Medio", "Bajo"] if dist.get(lvl, 0) > 0
        )
    else:
        partes = ""

    cA, cB = st.columns(2)
    with cA:
        st.markdown(
            f"<div class='callout' style='border-left-color:#117733;background:#EEF7EF'>"
            f"{chip_p} <b>Sector más predecible en {region_sel}:</b> "
            f"{mas_pred['Categoria']} — {lab_p}.<br>"
            f"<span style='font-size:13px;color:{MUTED}'>{partes}</span></div>",
            unsafe_allow_html=True,
        )
    with cB:
        st.markdown(
            f"<div class='callout' style='border-left-color:#CC6677;background:#FBEFF1'>"
            f"{chip_v} <b>Sector más variable en {region_sel}:</b> "
            f"{mas_var['Categoria']} — {lab_v}.<br>"
            f"<span style='font-size:13px;color:{MUTED}'>"
            f"Resultados dispares entre proyectos — apuesta de mayor riesgo.</span></div>",
            unsafe_allow_html=True,
        )

# ---------- Ranking de inversión ----------
st.markdown("### Ranking de combinaciones (top 8 por score)")
st.markdown(
    f"<p style='color:{MUTED};font-size:13px;margin:-6px 0 10px 0;line-height:1.5'>"
    f"Score combina impacto promedio + consistencia (menor desviación). "
    f"Ajusta los pesos en la barra lateral.</p>",
    unsafe_allow_html=True,
)

rank = (agg.sort_values("score", ascending=False)
           .head(8)
           .rename(columns={"mean": "Impacto promedio",
                            "std": "Desviación estándar",
                            "count": "# proyectos",
                            "score": "Score"})
           [["Region", "Categoria", "Impacto promedio",
             "Desviación estándar", "# proyectos", "Score"]]
           .reset_index(drop=True))
rank.index = rank.index + 1

# Umbral: los 4 scores más altos van con texto blanco (morado más oscuro → AA)
_topN_cutoff = float(rank["Score"].nlargest(4).min())

def _score_col_colors(col):
    # !important: vence la regla más específica `#T_xxx td { color: INK }`
    # que set_table_styles genera (ID+element gana al selector solo-ID por cell).
    return [
        f"color: {'#FFFFFF' if v >= _topN_cutoff else INK} !important; font-weight: 600;"
        for v in col
    ]

styler = (
    rank.style
        .format({"Impacto promedio": "{:.2f}", "Desviación estándar": "{:.2f}",
                 "Score": "{:.2f}"})
        .background_gradient(subset=["Score"], cmap="Purples")
        .apply(_score_col_colors, subset=["Score"])
        # Todas las celdas centradas
        .set_properties(**{"text-align": "center"})
        # Columnas estrechas: Region / Categoría / Impacto promedio
        .set_properties(subset=["Region", "Categoria", "Impacto promedio"],
                        **{"width": "110px", "max-width": "110px"})
        .set_table_styles([
            {"selector": "",
             "props": [("border", "1.5px solid #1A1A1A"),
                       ("border-collapse", "collapse"),
                       ("width", "100%"),
                       ("font-family", "-apple-system, Inter, sans-serif"),
                       ("font-size", "13px"),
                       ("table-layout", "fixed")]},
            {"selector": "th, td",
             "props": [("border", "1px solid #1A1A1A"),
                       ("padding", "8px 10px"),
                       ("color", INK),
                       ("text-align", "center")]},
            {"selector": "thead th",
             "props": [("background-color", "#F0EFF4"),
                       ("font-weight", "600"),
                       ("text-align", "center"),
                       ("border-bottom", "1.5px solid #1A1A1A")]},
        ])
)
# Card wrapper consistente con las cards de los charts (borde negro + padding)
st.markdown(
    "<div style='border:1.5px solid #1A1A1A; border-radius:8px; "
    "background:#FFFFFF; padding:10px; margin-bottom:32px; overflow:hidden'>"
    + styler.to_html()
    + "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='foot'>Fuente: dataset_evaluacion_unidad1.csv · "
    "Codificación ordinal Bajo/Medio/Alto → 1/2/3 · "
    "Score normalizado min-max sobre el set filtrado.</div>",
    unsafe_allow_html=True,
)
