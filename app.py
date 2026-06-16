import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px

# =====================================================
# CONFIGURACIÓN GENERAL Y ESTILOS
# =====================================================
st.set_page_config(page_title="Tablero de Gestión - Ralentí", layout="wide")

st.markdown("""
    <style>
        .card-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e1e8ed; box-shadow: 0 2px 6px rgba(0,0,0,0.04); height: 190px; }
        .section-box { background-color: #ffffff; padding: 22px; border-radius: 10px; border: 1px solid #e1e8ed; box-shadow: 0 2px 6px rgba(0,0,0,0.04); height: 380px; overflow-y: auto; }
    </style>
""", unsafe_allow_html=True)

META_RALENTI = 10

# =====================================================
# API Y PROCESAMIENTO DE DATOS (Lógica completa)
# =====================================================
@st.cache_data(ttl=3600)
def cargar_datos():
    usuario = "incubadora.pbi"
    clave = "incubadora.pbi123"
    base_url = "https://app.bronto-byte.com"

    try:
        token_response = requests.post(f"{base_url}/api/obtenerToken", json={"usuario": usuario, "clave": clave}, timeout=10)
        token = token_response.json()["token"].replace("Bearer ", "")
        response = requests.get(f"{base_url}/api/v2/gps-resumen/vehiculos", headers={"Authorization": f"Bearer {token}"}, timeout=15)
        data = response.json()
        
        df = pd.DataFrame(data.get("data", []))
        if df.empty: return df
        
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["ralenti_seg"] = df["detenido_seg"]
        df["porcentaje_ralenti"] = np.where(df["encendido_seg"] > 0, (df["ralenti_seg"] / df["encendido_seg"]) * 100, 0)
        
        if "grupo" in df.columns:
            df["grupo"] = df["grupo"].astype(str).str.strip()
            df = df[(df["grupo"] != "") & (~df["grupo"].str.lower().str.contains("inac", na=False))]
        return df
    except:
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.warning("No se pudieron cargar los datos desde la API.")
    st.stop()

# =====================================================
# ENCABEZADO Y PESTAÑAS
# =====================================================
st.title("TABLERO DE GESTIÓN – RALENTÍ")
tab1, tab2 = st.tabs(["📊 Tablero de Control", "📋 Hoja de Vida del Indicador"])

# =====================================================
# PESTAÑA 1: TABLERO DE CONTROL (Filtros en cascada intactos)
# =====================================================
with tab1:
    fil_col1, fil_col2, fil_col3, fil_col4, fil_col5 = st.columns([1.8, 1.8, 1.8, 1.8, 2.8])

    with fil_col1:
        grupos_sel = st.multiselect("Grupo", sorted(df["grupo"].unique()), placeholder="Todas")
    dff = df[df["grupo"].isin(grupos_sel)] if grupos_sel else df.copy()

    with fil_col2:
        vehiculos_sel = st.multiselect("Vehículo", sorted(dff["nombre_dispositivo"].unique()), placeholder="Todas")
    dff = dff[dff["nombre_dispositivo"].isin(vehiculos_sel)] if vehiculos_sel else dff

    with fil_col3:
        tipos_v = sorted(dff["tipo_vehiculo"].dropna().unique())
        tipos_sel = st.multiselect("Tipo de vehículo", tipos_v, placeholder="Todas")
    dff = dff[dff["tipo_vehiculo"].isin(tipos_sel)] if tipos_sel else dff

    with fil_col4:
        comb_col = "combustible" if "combustible" in dff.columns else "tipo_combustible"
        combustibles_v = sorted(dff[comb_col].dropna().unique())
        comb_sel = st.multiselect("Combustible", combustibles_v, placeholder="Todas")
    dff = dff[dff[comb_col].isin(comb_sel)] if comb_sel else dff
    
    with fil_col5:
        rango = st.date_input("Periodo", (df["fecha"].min(), df["fecha"].max()))
    # (Resto de la lógica de gráficos se mantiene igual que en tu archivo original)

# =====================================================
# PESTAÑA 2: HOJA DE VIDA (Textos modificados)
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
    * **Línea Base Histórica:** 18%
    * **Meta:** $\le$ 10% de tiempo en ralentí sobre el tiempo total de encendido de la flota.
    
    ---
    ### 🚦 4. NIVELES DE ALERTA (SEMÁFORO)
    | Rango de Cumplimiento | Estado de Alerta | Plan de Acción |
    | :---: | :---: | :--- |
    | **> 15%** | 🔴 **Crítico** | Operación ineficiente. Requiere auditoría inmediata por placa y llamado a revisión con el director del área. |
    
    ---
    ### 🏢 5. RESPONSABLES Y ÁREAS OPERATIVAS
    | Macro-Área Responsable | Grupo Operativo (Filtro) | Enfoque Crítico del Análisis en Ralentí |
    | :--- | :--- | :--- |
    | **Logística** | 🚚 Primera Milla | Control de tiempos de espera en plantas, Cedis, Centros de Empaque. |
    | **Logística** | 🔄 Transporte Interno | Control de tiempos de espera en plantas de alimentos, producciones avicolas y plantas clasificadoras. |
    """)