import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuración de la página estilo Dashboard Oscuro
st.set_page_config(layout="wide", page_title="Panel de Control - Entrenamiento")

# Estilo CSS personalizado para fondo oscuro profundo
st.markdown(
    """
    <style>
    .stApp { background-color: #0b111e; color: #ffffff; }
    h1, h2, h3 { color: #00f2fe !important; }
    div[data-testid="stMetricValue"] { color: #00f2fe !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# 1. CARGA Y LIMPIEZA DE DATOS
@st.cache_data(
    ttl=600
)
def cargar_datos():
    # Leer el archivo con los nombres exactos de las columnas
    url_google_sheets = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRhX2B4OK7X7XRhzlwrX5l9myTA_ABoYSVA3hoham6crMfEY9nUkeQ3kz-tFaKedWHXtPyWIfuLFws6/pub?gid=0&single=true&output=csv"
    df = pd.read_csv(url_google_sheets)

    # Convertir fecha
    df["fecha_dt"] = pd.to_datetime(df["fecha [DD/MM/YYYY]"], dayfirst=True)

    # Limpiar columnas numéricas
    df["distancia_limpia"] = pd.to_numeric(
        df["distancia [Km]"], errors="coerce"
    ).fillna(0)
    df["calorias_limpias"] = pd.to_numeric(
        df["calorías [Kcal]"], errors="coerce"
    ).fillna(0)

    # Filtrar el ritmo cardíaco (eliminamos el error de 998 BPM para no romper el promedio)
    df["bpm_limpio"] = pd.to_numeric(
        df["ritmo cardíaco [BPM]"], errors="coerce"
    )
    df.loc[df["bpm_limpio"] > 220, "bpm_limpio"] = (
        None  # Limita pulsaciones imposibles
    )

    # Agrupar por semanas para los gráficos
    df["Semana"] = df["fecha_dt"].dt.isocalendar().week
    df["Semana_Label"] = "Sem " + (df["Semana"] - df["Semana"].min() + 1).astype(
        str
    )

    return df


df = cargar_datos()

# --- ENCABEZADO ---
st.title("📊 PANEL DE CONTROL - ENTRAINAMIENTO")
st.write(
    f"Historial de progresos de Pablo — {df['actividad'].count()} actividades registradas"
)
st.write("---")

# --- FILAS DE METRICAS PRINCIPALES (KPIs) ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="KM TOTALES ACUMULADOS", value=f"{df['distancia_limpia'].sum():.2f} Km"
    )
with col2:
    st.metric(
        label="RITMO CARDÍACO PROMEDIO",
        value=f"{int(df['bpm_limpio'].mean())} BPM",
    )
with col3:
    st.metric(
        label="CALORÍAS ACUMULADAS TOTALES",
        value=f"{df['calorias_limpias'].sum():,.0f} Kcal",
    )

st.write("---")

# --- GRÁFICOS PRINCIPALES ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Gráfico A: Volumen de Kilómetros por Semana")
    fig_a = px.bar(
        df,
        x="Semana_Label",
        y="distancia_limpia",
        color="actividad",
        labels={"distancia_limpia": "Kilómetros", "Semana_Label": "Semanas"},
        template="plotly_dark",
        color_discrete_sequence=["#00adb5", "#ff8710", "#3f72af", "#e12345"],
    )
    fig_a.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_a, use_container_width=True)

with col_right:
    st.subheader("Gráfico B: Distribución de Carga (Esfuerzo por Calorías)")
    fig_b = px.pie(
        df,
        values="calorias_limpias",
        names="actividad",
        hole=0.4,
        template="plotly_dark",
        color_discrete_sequence=["#00adb5", "#ff8710", "#3f72af", "#e12345"],
    )
    fig_b.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_b, use_container_width=True)

st.write("---")

# --- GRÁFICO DE PROGRESO ACUMULADO ---
st.subheader("Evolución de Kilómetros Acumulados")
df_sorted = df.sort_values("fecha_dt")
df_sorted["KM_Acumulados"] = df_sorted["distancia_limpia"].cumsum()

fig_c = px.line(
    df_sorted,
    x="fecha_dt",
    y="KM_Acumulados",
    labels={"fecha_dt": "Fecha de Entrenamiento", "KM_Acumulados": "KM Totales"},
    template="plotly_dark",
    markers=True,
)
fig_c.update_traces(line=dict(color="#00f2fe", width=3))
fig_c.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig_c, use_container_width=True)

st.write("---")

# --- ANÁLISIS DETALLADO POR ACTIVIDAD ---
st.subheader("Análisis de Pulsaciones (BPM) por Disciplina")
fig_bpm = px.line(
    df[df["bpm_limpio"].notna()],
    x="fecha_dt",
    y="bpm_limpio",
    color="actividad",
    facet_col="actividad",
    labels={"bpm_limpio": "Pulsaciones (BPM)", "fecha_dt": "Fecha"},
    template="plotly_dark",
    markers=True,
)
fig_bpm.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig_bpm, use_container_width=True)
