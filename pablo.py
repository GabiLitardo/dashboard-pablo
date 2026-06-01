import pandas as pd
import plotly.express as px
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


# 1. CARGA Y LIMPIEZA DE DATOS (Desde el Google Sheets público)
@st.cache_data(ttl=600)  # Se actualiza solo cada 10 minutos
def cargar_datos():
    # REEMPLAZA ESTE LINK por el tuyo de Google Sheets publicado como CSV
    url_google_sheets = "Proyecto pablo - Hoja 1.csv"
    df = pd.read_csv(url_google_sheets)

    df["fecha_dt"] = pd.to_datetime(df["fecha [DD/MM/YYYY]"], dayfirst=True)

    # Creamos columnas limpias
    df["distancia_limpia"] = pd.to_numeric(
        df["distancia [Km]"], errors="coerce"
    ).fillna(0)
    df["calorias_limpias"] = pd.to_numeric(
        df["calorías [Kcal]"], errors="coerce"
    ).fillna(0)

    df["bpm_limpio"] = pd.to_numeric(
        df["ritmo cardíaco [BPM]"], errors="coerce"
    )
    df.loc[df["bpm_limpio"] > 220, "bpm_limpio"] = None

    # Extraer Mes y Año para los filtros del mapa
    df["Mes_Año"] = df["fecha_dt"].dt.strftime("%B %Y").str.capitalize()
    df["Semana"] = df["fecha_dt"].dt.isocalendar().week
    df["Semana_Label"] = "Sem " + (df["Semana"] - df["Semana"].min() + 1).astype(
        str
    )

    return df


df_original = cargar_datos()

# --- ENCABEZADO ---
st.title("📊 PANEL DE CONTROL - ENTRENAMIENTO")

# ========================================================================================
#   FILTROS GENERALES (La barra superior del mapa de tu primo)
# ========================================================================================
st.write("### 🎛️ FILTROS GENERALES")
col_f1, col_f2 = st.columns(2)

with col_f1:
    meses_disponibles = ["Todos"] + list(df_original["Mes_Año"].unique())
    mes_seleccionado = st.selectbox("Seleccionar Mes:", meses_disponibles)

with col_f2:
    actividades_disponibles = ["Todas"] + list(df_original["actividad"].unique())
    actividad_seleccionada = st.selectbox(
        "Seleccionar Actividad:", actividades_disponibles
    )

# Aplicar filtros al DataFrame
df = df_original.copy()
if mes_seleccionado != "Todos":
    df = df[df["Mes_Año"] == mes_seleccionado]
if actividad_seleccionada != "Todas":
    df = df[df["actividad"] == actividad_seleccionada]

st.write("---")

# ========================================================================================
#   INDICADORES PRINCIPALES (Tarjetas Grandes de KPI)
# ========================================================================================
st.write("### 【 INDICADORES PRINCIPALES 】")
col1, col2, col3 = st.columns(3)

km_totales = df["distancia_limpia"].sum()
bpm_promedio = df["bpm_limpio"].mean()
calorias_totales = df["calorias_limpias"].sum()

with col1:
    # Lógica de estatus basado en el mapa
    status_km = "OPTIMO" if km_totales > 20 else "EN PROGRESO"
    st.metric(label="KM TOTALES (PERIODO)", value=f"{km_totales:.2f} Km")
    st.caption(f"Status: **{status_km}**")

with col2:
    # Lógica de estatus cardíaco
    status_bpm = "ZONA GRASA" if 100 <= bpm_promedio <= 130 else "CARDIO"
    val_bpm = f"{int(bpm_promedio)} BPM" if not pd.isna(bpm_promedio) else "0 BPM"
    st.metric(label="RITMO CARDÍACO PROMEDIO", value=val_bpm)
    st.caption(f"Status: **{status_bpm}**")

with col3:
    st.metric(
        label="CALORÍAS ACUMULADAS", value=f"{calorias_totales:,.0f} Kcal"
    )
    st.caption("Status: **Semana de Cierre**")

st.write("---")

# ========================================================================================
#   GRÁFICOS DE CONTROL
# ========================================================================================
st.write("### 【 GRÁFICOS DE CONTROL 】")
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("GRÁFICO A: Volumen de Kilómetros por Semana")
    fig_a = px.bar(
        df,
        x="Semana_Label",
        y="distancia_limpia",
        color="actividad",
        labels={"distancia_limpia": "Kilómetros", "Semana_Label": "Semanas"},
        template="plotly_dark",
        color_discrete_sequence=["#00adb5", "#ff8710", "#3f72af", "#e12345"],
    )
    # Línea de Meta (Meta de Planta: 20 Km) como pide el mapa
    fig_a.add_hline(
        y=20,
        line_dash="dash",
        line_color="red",
        annotation_text="Meta de Planta: 20 Km",
    )
    fig_a.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_a, use_container_width=True)

with col_right:
    st.subheader("GRÁFICO B: Distribución de Carga (Eficiencia)")
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
