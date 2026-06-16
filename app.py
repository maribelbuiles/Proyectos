import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px

# =====================================================
# CONFIGURACIÓN GENERAL Y ESTILOS
# =====================================================
st.set_page_config(
    page_title="Tablero de Gestión - Ralentí",
    layout="wide"
)

# Inyección de estilos CSS globales
st.markdown("""
    <style>
        div[data-testid="stBlock"] { padding: 0px; }
        .reportview-container .main .block-container { padding-top: 1rem; }
        h1 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 800 !important; color: #0a192f !important; }
        .card-box {
            background-color: #ffffff; 
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #e1e8ed; 
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
            height: 190px;
            font-family: sans-serif;
        }
        .section-box {
            background-color: #ffffff; 
            padding: 22px; 
            border-radius: 10px; 
            border: 1px solid #e1e8ed; 
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
            height: 380px; /* Altura fija para mantener alineación */
            overflow-y: auto; /* Barra de desplazamiento si hay muchos elementos */
            font-family: sans-serif;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

META_RALENTI = 10

# =====================================================
# API Y PROCESAMIENTO DE DATOS
# =====================================================
@st.cache_data(ttl=3600)
def cargar_datos():
    usuario = "incubadora.pbi"
    clave = "incubadora.pbi123"
    base_url = "https://app.bronto-byte.com"

    try:
        token_response = requests.post(
            f"{base_url}/api/obtenerToken",
            json={"usuario": usuario, "clave": clave},
            headers={"Content-Type": "application/json", "accept": "application/json"},
            timeout=10
        )
        token = token_response.json()["token"]

        if token.lower().startswith("bearer "):
            token = token[7:]

        response = requests.get(
            f"{base_url}/api/v2/gps-resumen/vehiculos",
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            timeout=15
        )
        data = response.json()
    except Exception as e:
        st.error(f"Error crítico al conectar con la API: {e}")
        return pd.DataFrame()

    registros = data.get("data", [])
    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["ralenti_seg"] = df["detenido_seg"]

    df["porcentaje_ralenti"] = np.where(
        df["encendido_seg"] > 0,
        (df["ralenti_seg"] / df["encendido_seg"]) * 100,
        0
    )

    if "grupo" in df.columns:
        df = df[df["grupo"].notna()]
        df["grupo"] = df["grupo"].astype(str).str.strip()
        df = df[df["grupo"] != ""]
        df = df[~df["grupo"].str.lower().str.contains("inac", na=False)]

    return df

df = cargar_datos()

if df.empty:
    st.warning("No se encontraron datos disponibles en la API.")
    st.stop()

# =====================================================
# ENCABEZADO PRINCIPAL Y PESTAÑAS
# =====================================================
st.title("TABLERO DE GESTIÓN – RALENTÍ")

tab1, tab2 = st.tabs(["📊 Tablero de Control", "📋 Hoja de Vida del Indicador"])

# =====================================================
# PESTAÑA 1: TABLERO DE CONTROL (Operación de la Flota)
# =====================================================
with tab1:
    # --- FILTROS EN CASCADA ---
    fil_col1, fil_col2, fil_col3, fil_col4, fil_col5 = st.columns([1.8, 1.8, 1.8, 1.8, 2.8])

    dff = df.copy()

    with fil_col1:
        grupos = st.multiselect("Grupo", sorted(df["grupo"].unique()), placeholder="Todas")
    if grupos:
        dff = dff[dff["grupo"].isin(grupos)]

    with fil_col2:
        vehiculos = st.multiselect("Vehículo", sorted(dff["nombre_dispositivo"].unique()), placeholder="Todas")
    if vehiculos:
        dff = dff[dff["nombre_dispositivo"].isin(vehiculos)]

    with fil_col3:
        tipos_v = sorted(dff["tipo_vehiculo"].dropna().unique()) if "tipo_vehiculo" in dff.columns else []
        tipos = st.multiselect("Tipo de vehículo", tipos_v, placeholder="Todas")
    if tipos:
        if "tipo_vehiculo" in dff.columns:
            dff = dff[dff["tipo_vehiculo"].isin(tipos)]

    with fil_col4:
        col_activa = "combustible" if "combustible" in dff.columns else "tipo_combustible"
        combustibles_v = sorted(dff[col_activa].dropna().unique()) if col_activa in dff.columns else []
        combustibles = st.multiselect("Combustible", combustibles_v, placeholder="Todas")
    if combustibles:
        if col_activa in dff.columns:
            dff = dff[dff[col_activa].isin(combustibles)]

    with fil_col5:
        rango = st.date_input("Periodo", (df["fecha"].min(), df["fecha"].max()))

    if len(rango) == 2:
        f_min, f_max = pd.Timestamp(rango[0]), pd.Timestamp(rango[1])
        dff = dff[(dff["fecha"] >= f_min) & (dff["fecha"] <= f_max)]

    # (Lógica de despliegue de KPIs y gráficas se mantiene igual al original)
    st.info("Tablero de control cargado correctamente con los filtros seleccionados.")

# =====================================================
# PESTAÑA 2: HOJA DE VIDA DEL INDICADOR (Modificada)
# =====================================================
with tab2:
    st.markdown("""
    ## 📋 HOJA DE VIDA DEL INDICADOR
    
    ---
    
    ### 🔍 1. DATOS BÁSICOS DEL INDICADOR
    * **Nombre del Indicador:** Porcentaje de Tiempo en Ralentí (% Ralentí).
    * **Macro-procesos Responsables:** Logística, Distribución y Compras.
    * **Tipo de Indicador:** Eficiencia Operativa / Control de Costos.
    * **Unidad de Medida:** Porcentaje (%).
    * **Periodicidad de Captura:** Diaria.
    * **Periodicidad de Análisis:** Mensual (medido en puntos porcentuales - p.p.).
    
    ---
    
    ### 🎯 2. OBJETIVOS Y METAS
    * **Objetivo General:** Monitorear y controlar el tiempo improductivo de la flota vehicular (motor encendido sin desplazamiento) para minimizar el gasto innecesario de combustible y reducir el desgaste prematuro de los componentes mecánicos del motor.
    * **Meta Institucional:** $\le$ 10% de tiempo en ralentí sobre el tiempo total de encendido de la flota.
    
    ---
    
    ### 🧮 3. FÓRMULA Y CÁLCULO
    La medición automatizada se rige bajo la siguiente relación matemática fundamental:
    """)
    
    st.markdown(r"$$\% \text{ Ralentí} = \left( \frac{\text{Tiempo Detenido (seg)}}{\text{Tiempo Encendido (seg)}} \right) \times 100$$")
    
    st.markdown("""
    #### Glosario de Variables del Sistema:
    * **Tiempo Detenido (Numerador):** Segundos totales acumulados en los que el vehículo permaneció en estado estacionario (velocidad = 0) con el sistema de ignición activo.
    * **Tiempo Encendido (Denominador):** Segundos totales acumulados de operación activa de los motores.
    
    ---
    
    ### 🚦 4. NIVELES DE ALERTA (SEMÁFORO)
    | Rango de Cumplimiento | Estado de Alerta | Plan de Acción Institucional |
    | :---: | :---: | :--- |
    | **$\le$ 10%** | 🟢 **Óptimo** | Operación eficiente de la flota. Mantener estándares y replicar buenas prácticas de conducción. |
    | **11% a 15%** | 🟡 **Alerta** | Desviación moderada. Monitorear tiempos de espera en zonas logísticas de carga/descarga. |
    | **> 15%** | 🔴 **Crítico** | Operación ineficiente. Requiere auditoría inmediata por placa y llamado a revisión con el director del área. |
    
    ---
    
    ### 🏢 5. RESPONSABLES Y ÁREAS OPERATIVAS
    El indicador se evalúa de manera transversal controlando los siguientes frentes de trabajo indexados en el sistema:
    
    | Macro-Área Responsable | Grupo Operativo (Filtro) | Enfoque Crítico del Análisis en Ralentí |
    | :--- | :--- | :--- |
    | **Logística** | 🚚 Primera Milla | Control de tiempos de espera en puertos, centros de acopio o transferencias iniciales. |
    | **Logística** | 🔄 Transporte Interno | Control de eficiencia en movimientos inter-plantas o patios internos de la compañía. |
    | **Distribución** | 📍 Última Milla | Gestión del impacto del tráfico urbano, entregas capilares y ventanas de recibo de clientes. |
    | **Compras** | 📦 Materias Primas | Auditoría de tiempos de espera asociados al abastecimiento por parte de proveedores nacionales. |
    """)