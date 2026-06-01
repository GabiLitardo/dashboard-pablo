"""
Módulo: pablo.py
Descripción: Dashboard de control analítico integrado de alto rendimiento físico.
            Corrección del procesamiento de datos categóricos para unificar variantes 
            de texto en actividades (Ciclismo y Natación) y asegurar la renderización 
            de métricas de frecuencia cardíaca (BPM).
Conexión: Google Sheets Cloud Engine (Real-Time Sync).
Autor: Desarrollo de Productos de Software
Fecha: Junio 2026
Versión: 2.1.0
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ========================================================================================
# CONFIGURACIÓN DE LA INTERFAZ DE USUARIO Y CONFIGURACIÓN ESTÁTICA
# ========================================================================================
st.set_page_config(
    layout="wide",
    page_title="Panel de Control - Entrenamiento",
    initial_sidebar_state="collapsed",
)

# Inyección de estilos CSS para la personalización del tema oscuro (Cyberpunk Dark Mode)
st.markdown(
    """
    <style>
    .stApp { 
        background-color: #0b111e; 
        color: #ffffff; 
    }
    h1, h2, h3, h4 { 
        color: #00f2fe !important; 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    div[data-testid="stMetricValue"] { 
        color: #00f2fe !important; 
        font-size: 2.2rem !important;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        color: #8fa0bc !important;
    }
    .stSelectbox label {
        color: #8fa0bc !important;
    }
    div[data-testid="stCard"] {
        background-color: #11192a !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }
    hr {
        border-color: #1e293b !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ========================================================================================
# CAPA DE ACCESO Y PROCESAMIENTO DE DATOS (ETL)
# ========================================================================================
@st.cache_data(ttl=600)
def cargar_y_limpiar_datos() -> pd.DataFrame:
    """
    Carga el set de datos desde el origen en la nube (Google Sheets), estandariza las
    cadenas de texto de las actividades y normaliza las variables numéricas.
    """
    ruta_origen = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRhX2B4OK7X7XRhzlwrX5l9myTA_ABoYSVA3hoham6crMfEY9nUkeQ3kz-tFaKedWHXtPyWIfuLFws6/pub?gid=0&single=true&output=csv"
    df = pd.read_csv(ruta_origen)

    # Conversión del campo temporal con manejo de formato regional
    df["fecha_dt"] = pd.to_datetime(df["fecha [DD/MM/YYYY]"], dayfirst=True)
    df["Mes_Texto"] = df["fecha_dt"].dt.strftime("%b").str.capitalize()

    # Normalización semántica de la columna actividad para resolver inconsistencias de registro
    df["actividad_normalizada"] = df["actividad"].astype(str).str.strip().str.capitalize()
    
    # Homologación de variantes de texto detectadas en el set de datos origen
    df.loc[df["actividad_normalizada"].str.contains("Ciclismo|Bici|Montar", case=False, na=False), "actividad_normalizada"] = "Ciclismo"
    df.loc[df["actividad_normalizada"].str.contains("Natación|Nadar|Natac", case=False, na=False), "actividad_normalizada"] = "Natación"
    df.loc[df["actividad_normalizada"].str.contains("Caminar|Caminata", case=False, na=False), "actividad_normalizada"] = "Caminar"

    # Sanitización de variables métricas continuas
    df["distancia_limpia"] = pd.to_numeric(
        df["distancia [Km]"], errors="coerce"
    ).fillna(0)
    df["calorias_limpias"] = pd.to_numeric(
        df["calorías [Kcal]"], errors="coerce"
    ).fillna(0)

    # Filtrado analítico de anomalías en frecuencia cardíaca (>220 BPM y valores <= 0)
    df["bpm_limpio"] = pd.to_numeric(
        df["ritmo cardíaco [BPM]"], errors="coerce"
    )
    df.loc[(df["bpm_limpio"] > 220) | (df["bpm_limpio"] <= 0), "bpm_limpio"] = None

    # Agrupaciones temporales relativas para cálculos por semanas del mes
    df["Mes_Año"] = df["fecha_dt"].dt.strftime("%B %Y").str.capitalize()
    df["Semana"] = df["fecha_dt"].dt.isocalendar().week
    df["Semana_Label"] = "Sem " + (df["Semana"] - df["Semana"].min() + 1).astype(
        str
    )

    return df


# Inicialización del DataFrame maestro
df_maestro = cargar_y_limpiar_datos()

# ========================================================================================
# COMPONENTE: ENCABEZADO PRINCIPAL Y FILTROS GENERALES
# ========================================================================================
st.title("PANEL DE CONTROL – ENTRENAMIENTO")
st.write("---")

col_f1, col_f2 = st.columns(2)
with col_f1:
    listado_meses = ["Todos"] + list(df_maestro["Mes_Año"].unique())
    mes_filtro = st.selectbox("MES:", listado_meses, index=0)

with col_f2:
    listado_actividades = ["Todas"] + list(df_maestro["actividad_normalizada"].unique())
    actividad_filtro = st.selectbox("ACTIVIDAD:", listado_actividades, index=0)

# Aplicación de reglas de filtrado dinámico
df_filtrado = df_maestro.copy()
if mes_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Mes_Año"] == mes_filtro]
if actividad_filtro != "Todas":
    df_filtrado = df_filtrado[df_filtrado["actividad_normalizada"] == actividad_filtro]

# ========================================================================================
# SECCIÓN 1: INDICADORES PRINCIPALES (TARJETAS DE KPI SUPERIORES)
# ========================================================================================
st.write("### 【 INDICADORES PRINCIPALES 】")
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

volumen_km_periodo = df_filtrado["distancia_limpia"].sum()
frecuencia_cardiaca_media = df_filtrado["bpm_limpio"].mean()
gasto_calorico_acumulado = df_filtrado["calorias_limpias"].sum()

with col_kpi1:
    estado_volumen = "OPTIMO" if volumen_km_periodo >= 20.0 else "EN PROGRESO"
    st.metric(
        label="KM TOTALES (SEMANA)", value=f"{volumen_km_periodo:.2f} Km"
    )
    st.markdown(f"Status: <span style='color:#00f2fe; font-weight:bold;'>{estado_volumen}</span>", unsafe_allow_html=True)

with col_kpi2:
    if pd.isna(frecuencia_cardiaca_media):
        valor_bpm_str, estado_fisiologico = "0 BPM", "SIN REGISTRO"
    else:
        valor_bpm_str = f"{int(frecuencia_cardiaca_media)} BPM"
        estado_fisiologico = (
            "ZONA GRASA" if 100 <= frecuencia_cardiaca_media <= 130 else "CARDIO"
        )
    st.metric(label="RITMO CARDÍACO PROMEDIO", value=valor_bpm_str)
    st.markdown(f"Status: <span style='color:#ff8710; font-weight:bold;'>{estado_fisiologico}</span>", unsafe_allow_html=True)

with col_kpi3:
    st.metric(
        label="CALORÍAS ACUMULADAS",
        value=f"{gasto_calorico_acumulado:,.0f} Kcal",
    )
    st.markdown("Status: <span style='color:#8fa0bc;'>(Semana de Cierre)</span>", unsafe_allow_html=True)

st.write("---")

# ========================================================================================
# SECCIÓN 2: GRÁFICOS DE CONTROL (BLOQUE INTERMEDIO PRINCIPAL)
# ========================================================================================
st.write("### 【 GRÁFICOS DE CONTROL 】")
col_g1, col_g2, col_g3 = st.columns([1.5, 1.2, 1.3])

with col_g1:
    st.write("##### GRÁFICO A: VOLUMEN DE KILÓMETROS POR SEMANA")
    fig_a = px.bar(
        df_filtrado,
        x="Semana_Label",
        y="distancia_limpia",
        color="actividad_normalizada",
        labels={"distancia_limpia": "Km", "Semana_Label": ""},
        template="plotly_dark",
        color_discrete_sequence=["#00adb5", "#ff8710", "#3f72af", "#e12345"],
    )
    fig_a.add_hline(
        y=20,
        line_dash="dash",
        line_color="#ff2e93",
        annotation_text="Meta de Planta: 20 Km",
        annotation_position="top left",
    )
    fig_a.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(title=dict(text=""), orientation="h", y=-0.2),
    )
    st.plotly_chart(fig_a, use_container_width=True)

with col_g2:
    st.write("##### GRÁFICO B: DISTRIBUCIÓN DE CARGA")
    fig_b = px.pie(
        df_filtrado,
        values="calorias_limpias",
        names="actividad_normalizada",
        hole=0.5,
        template="plotly_dark",
        color_discrete_sequence=["#00adb5", "#ff8710", "#3f72af", "#e12345"],
    )
    fig_b.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig_b, use_container_width=True)

with col_g3:
    st.write("##### KILÓMETROS ACUMULADOS")
    df_sorted_mes = df_filtrado.sort_values("fecha_dt")
    df_sorted_mes["KM_Acum_Mes"] = df_sorted_mes["distancia_limpia"].cumsum()
    fig_linea_mes = px.line(
        df_sorted_mes,
        x="fecha_dt",
        y="KM_Acum_Mes",
        labels={"fecha_dt": "", "KM_Acum_Mes": "Km"},
        template="plotly_dark",
        markers=True,
    )
    fig_linea_mes.update_traces(line=dict(color="#00f2fe", width=3))
    fig_linea_mes.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_linea_mes, use_container_width=True)

st.write("---")

# ========================================================================================
# SECCIÓN 3: ANÁLISIS POR ACTIVIDAD (HISTÓRICOS MENSUALES Y TENDENCIAS BPM)
# ========================================================================================
st.write("### 【 ANÁLISIS POR ACTIVIDAD 】")

orden_meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

def generar_bloque_actividad(nombre_actividad: str, color_hex: str):
    """Genera las dos gráficas de evolución mensual específicas para cada actividad."""
    df_act = df_maestro[df_maestro["actividad_normalizada"] == nombre_actividad]
    
    df_mensual = df_act.groupby("Mes_Texto").agg(
        Total_Km=("distancia_limpia", "sum"),
        Promedio_BPM=("bpm_limpio", "mean")
    ).reindex(orden_meses).dropna(how='all').reset_index()
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        fig_km = px.bar(
            df_mensual, x="Mes_Texto", y="Total_Km",
            title=f"KM ACUMULADOS POR MES",
            labels={"Total_Km": "Km", "Mes_Texto": ""},
            template="plotly_dark"
        )
        fig_km.update_traces(marker_color=color_hex)
        fig_km.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_km, use_container_width=True)
        
    with col_v2:
        fig_bpm = px.line(
            df_mensual, x="Mes_Texto", y="Promedio_BPM",
            title=f"PROMEDIO DE PULSACIONES (BPM)",
            labels={"Promedio_BPM": "BPM", "Mes_Texto": ""},
            template="plotly_dark", markers=True
        )
        fig_bpm.update_traces(line=dict(color=color_hex, width=3))
        fig_bpm.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bpm, use_container_width=True)

with st.expander("🚲 CICLISMO", expanded=True):
    generar_bloque_actividad("Ciclismo", "#00adb5")

with st.expander("🚶 CAMINAR", expanded=True):
    generar_bloque_actividad("Caminar", "#ff8710")

with st.expander("🏊 NATACIÓN", expanded=True):
    generar_bloque_actividad("Natación", "#3f72af")

st.write("---")

# ========================================================================================
# SECCIÓN 4: RESUMEN GENERAL Y AVANCE DE OBJETIVO MENSUAL (PIE DE PÁGINA)
# ========================================================================================
st.write("### 【 RESUMEN GENERAL Y OBJETIVO MENSUAL 】")
col_r1, col_r2, col_r3, col_r4 = st.columns(4)

total_historico_km = df_maestro["distancia_limpia"].sum()
total_historico_bpm = df_maestro["bpm_limpio"].mean()
total_historico_cal = df_maestro["calorias_limpias"].sum()

with col_r1:
    st.metric("KM TOTALES HISTÓRICOS", f"{total_historico_km:.2f} Km")
with col_r2:
    st.metric("RITMO CARDÍACO PROMEDIO", f"{int(total_historico_bpm)} BPM")
with col_r3:
    st.metric("CALORÍAS TOTALES", f"{total_historico_cal:,.0f} Kcal")
with col_r4:
    meta_objetivo = 80.0
    porcentaje_avance = min(int((volumen_km_periodo / meta_objetivo) * 100), 100)
    st.write(f"**OBJETIVO MENSUAL (Meta: {meta_objetivo} Km)**")
    st.progress(porcentaje_avance / 100.0)
    st.caption(f"Progreso actual: {porcentaje_avance}% del objetivo cumplido.")
