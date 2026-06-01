"""
Módulo: pablo.py
Descripción: Dashboard de control analítico para el seguimiento de rendimiento físico.
Autor: Desarrollo de Productos de Software
Fecha: Junio 2026
Versión: 1.0.0
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ========================================================================================
# CONFIGURACIÓN DE LA INTERFAZ DE USUARIO
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
    h1, h2, h3 { 
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
    div[data-testid="stCaptionCustom"] {
        font-size: 0.9rem !important;
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
    Carga el set de datos desde el origen de datos unificado y ejecuta las transformaciones
    limpieza de anomalías de hardware y normalización de tipos.
    """
    # En entorno de producción, reemplazar esta ruta local por la URL pública del CSV de Google Sheets
    ruta_origen = "Proyecto pablo - Hoja 1.csv"
    df = pd.read_csv(ruta_origen)

    # Conversión del campo temporal con manejo estricto de formato regional (Day-First)
    df["fecha_dt"] = pd.to_datetime(df["fecha [DD/MM/YYYY]"], dayfirst=True)

    # Sanitización de variables métricas continuas
    df["distancia_limpia"] = pd.to_numeric(
        df["distancia [Km]"], errors="coerce"
    ).fillna(0)
    df["calorias_limpias"] = pd.to_numeric(
        df["calorías [Kcal]"], errors="coerce"
    ).fillna(0)

    # Filtrado analítico de anomalías de lectura en sensores de frecuencia cardíaca (>220 BPM)
    df["bpm_limpio"] = pd.to_numeric(
        df["ritmo cardíaco [BPM]"], errors="coerce"
    )
    df.loc[df["bpm_limpio"] > 220, "bpm_limpio"] = None

    # Agrupaciones temporales relativas para cálculos de volumen semanal y mensual
    df["Mes_Año"] = df["fecha_dt"].dt.strftime("%B %Y").str.capitalize()
    df["Semana"] = df["fecha_dt"].dt.isocalendar().week
    df["Semana_Label"] = "Sem " + (df["Semana"] - df["Semana"].min() + 1).astype(
        str
    )

    return df


# Inicialización del DataFrame maestro
df_maestro = cargar_y_limpiar_datos()

# ========================================================================================
# COMPONENTE: ENCABEZADO PRINCIPAL
# ========================================================================================
st.title("PANEL DE CONTROL – ENTRENAMIENTO")
st.write("---")

# ========================================================================================
# COMPONENTE: CONTROLES DE SEGMENTACIÓN (FILTROS)
# ========================================================================================
col_f1, col_f2 = st.columns(2)

with col_f1:
    listado_meses = ["Todos"] + list(df_maestro["Mes_Año"].unique())
    mes_filtro = st.selectbox("MES:", listado_meses, index=0)

with col_f2:
    listado_actividades = ["Todas"] + list(df_maestro["actividad"].unique())
    actividad_filtro = st.selectbox("ACTIVIDAD:", listado_actividades, index=0)

# Aplicación de reglas de filtrado dinámico sobre el set de datos maestro
df_filtrado = df_maestro.copy()
if mes_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Mes_Año"] == mes_filtro]
if actividad_filtro != "Todas":
    df_filtrado = df_filtrado[df_filtrado["actividad"] == actividad_filtro]

st.write("---")

# ========================================================================================
# COMPONENTE: TARJETAS DE INDICADORES CLAVE (KPI METRICS)
# ========================================================================================
st.write("### 【 INDICADORES PRINCIPALES 】")
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

# Cálculo de agregaciones requeridas por las tarjetas KPI
volumen_km_periodo = df_filtrado["distancia_limpia"].sum()
frecuencia_cardiaca_media = df_filtrado["bpm_limpio"].mean()
gasto_calorico_acumulado = df_filtrado["calorias_limpias"].sum()

with col_kpi1:
    # Evaluación del estado volumétrico respecto a umbrales de rendimiento básicos
    estado_volumen = "OPTIMO" if volumen_km_periodo >= 20.0 else "EN PROGRESO"
    st.metric(
        label="KM TOTALES (PERIODO)", value=f"{volumen_km_periodo:.2f} Km"
    )
    st.markdown(f"Status: <span style='color:#00f2fe; font-weight:bold;'>[{estado_volumen}]</span>", unsafe_allow_html=True)

with col_kpi2:
    # Determinación de zona fisiológica de entrenamiento basada en la frecuencia cardíaca media
    if pd.isna(frecuencia_cardiaca_media):
        valor_bpm_str, estado_fisiologico = "0 BPM", "SIN REGISTRO"
    else:
        valor_bpm_str = f"{int(frecuencia_cardiaca_media)} BPM"
        estado_fisiologico = (
            "ZONA GRASA" if 100 <= frecuencia_cardiaca_media <= 130 else "CARDIO"
        )

    st.metric(label="RITMO CARDÍACO PROMEDIO", value=valor_bpm_str)
    st.markdown(f"Status: <span style='color:#ff8710; font-weight:bold;'>[{estado_fisiologico}]</span>", unsafe_allow_html=True)

with col_kpi3:
    st.metric(
        label="CALORÍAS ACUMULADAS",
        value=f"{gasto_calorico_acumulado:,.0f} Kcal",
    )
    st.markdown("Status: <span style='color:#8fa0bc;'>[Semana de Cierre]</span>", unsafe_allow_html=True)

st.write("---")

# ========================================================================================
# COMPONENTE: GRÁFICOS DE CONTROL ANÁLITICO
# ========================================================================================
st.write("### 【 GRÁFICOS DE CONTROL 】")
col_grafico_izq, col_grafico_der = st.columns(2)

with col_grafico_izq:
    st.write("#### GRÁFICO A: VOLUMEN DE KILÓMETROS POR SEMANA")

    # Generación del gráfico de columnas apiladas por clúster semanal
    fig_columnas_apiladas = px.bar(
        df_filtrado,
        x="Semana_Label",
        y="distancia_limpia",
        color="actividad",
        labels={"distancia_limpia": "Kilómetros", "Semana_Label": "Semanas"},
        template="plotly_dark",
        color_discrete_sequence=["#00adb5", "#ff8710", "#3f72af", "#e12345"],
    )

    # Proyección lineal estática del umbral objetivo de rendimiento (Meta de Planta)
    fig_columnas_apiladas.add_hline(
        y=20,
        line_dash="dash",
        line_color="#ff2e93",
        annotation_text="Meta de Planta: 20 Km",
        annotation_position="top left",
    )

    fig_columnas_apiladas.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(title=dict(text="Actividad"), orientation="h", y=-0.2),
    )
    st.plotly_chart(fig_columnas_apiladas, use_container_width=True)

with col_grafico_der:
    st.write("#### GRÁFICO B: DISTRIBUCIÓN DE CARGA (EFICIENCIA)")

    # Generación de la gráfica de anillo para la distribución proporcional del gasto calórico
    fig_anillo_eficiencia = px.pie(
        df_filtrado,
        values="calorias_limpias",
        names="actividad",
        hole=0.4,
        template="plotly_dark",
        color_discrete_sequence=["#00adb5", "#ff8710", "#3f72af", "#e12345"],
    )

    fig_anillo_eficiencia.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig_anillo_eficiencia, use_container_width=True)

st.write("---")

# ========================================================================================
# COMPONENTE: EVOLUCIÓN HISTÓRICA CONTINUA (KILÓMETROS ACUMULADOS)
# ========================================================================================
st.write("#### EVOLUCIÓN DE KILÓMETROS ACUMULADOS (PROGRESO TOTAL)")

# Aislamiento analítico de datos volumétricos históricos para evitar roturas por filtrado cero
df_linea_historica = df_maestro[df_maestro["distancia_limpia"] > 0].sort_values(
    "fecha_dt"
)

if not df_linea_historica.empty:
    df_linea_historica["KM_Acumulados"] = df_linea_historica[
        "distancia_limpia"
    ].cumsum()

    # Modelado de la serie de tiempo para la proyección acumulada de distancia
    fig_linea_progreso = px.line(
        df_linea_historica,
        x="fecha_dt",
        y="KM_Acumulados",
        labels={
            "fecha_dt": "Línea de Tiempo",
            "KM_Acumulados": "Kilómetros Totales",
        },
        template="plotly_dark",
        markers=True,
    )

    fig_linea_progreso.update_traces(line=dict(color="#00f2fe", width=3))
    fig_linea_progreso.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_linea_progreso, use_container_width=True)
else:
    st.info("No se registran vectores de distancia válidos en el histórico.")
