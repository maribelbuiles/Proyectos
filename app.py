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
# CARGA DE DATOS (Lógica de API Original Restaurada)
# =====================================================
@st.cache_data(ttl=3600)
def cargar_datos():
    usuario, clave = "incubadora.pbi", "incubadora.pbi123"
    base_url = "https://app.bronto-byte.com"
    try:
        # Obtener token
        token_response = requests.post(f"{base_url}/api/obtenerToken", json={"usuario": usuario, "clave": clave}, timeout=10)
        token = token_response.json()["token"].replace("Bearer ", "")
        # Obtener datos
        response = requests.get(f"{base_url}/api/v2/gps-resumen/vehiculos", headers={"Authorization": f"Bearer {token}"}, timeout=15)
        registros = response.json().get("data", [])
        
        df = pd.DataFrame(registros)
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["ralenti_seg"] = df["detenido_seg"]
        df["porcentaje_ralenti"] = np.where(df["encendido_seg"] > 0, (df["ralenti_seg"] / df["encendido_seg"]) * 100, 0)
        
        # Limpieza básica
        if "grupo" in df.columns:
            df["grupo"] = df["grupo"].astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

df = cargar_datos()

# =====================================================
# INTERFAZ Y PESTAÑAS
# =====================================================
st.title("TABLERO DE GESTIÓN – RALENTÍ")
tab1, tab2 = st.tabs(["📊 Tablero de Control", "📋 Hoja de Vida del Indicador"])

with tab1:
    # --- FILTROS EN CASCADA ORIGINALES ---
    col1, col2, col3, col4, col5 = st.columns(5)
    
    grupos_sel = col1.multiselect("Grupo", sorted(df["grupo"].unique()))
    dff = df[df["grupo"].isin(grupos_sel)] if grupos_sel else df.copy()
    
    vehiculos_sel = col2.multiselect("Vehículo", sorted(dff["nombre_dispositivo"].unique()))
    dff = dff[dff["nombre_dispositivo"].isin(vehiculos_sel)] if vehiculos_sel else dff
    
    tipos_sel = col3.multiselect("Tipo de vehículo", sorted(dff["tipo_vehiculo"].dropna().unique()))
    dff = dff[dff["tipo_vehiculo"].isin(tipos_sel)] if tipos_sel else dff
    
    comb_col = "combustible" if "combustible" in dff.columns else "tipo_combustible"
    comb_sel = col4.multiselect("Combustible", sorted(dff[comb_col].dropna().unique()))
    dff = dff[dff[comb_col].isin(comb_sel)] if comb_sel else dff
    
    st.info("Tablero cargado correctamente.")

with tab2:
    # --- HOJA DE VIDA (TEXTOS SOLICITADOS) ---
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
    * **Objetivo General:** Monitorear y controlar el tiempo improductivo de la flota.
    * **Línea Base Histórica:** 18%
    * **Meta:** $\le$ 10% de tiempo en ralentí sobre el tiempo total de encendido.
    
    ---
    ### 🚦 4. NIVELES DE ALERTA (SEMÁFORO)
    | Rango | Estado | Plan de Acción |
    | :--- | :--- | :--- |
    | **> 15%** | 🔴 **Crítico** | Operación ineficiente. Requiere auditoría inmediata por placa y llamado a revisión con el director del área. |
    
    ---
    ### 🏢 5. RESPONSABLES Y ÁREAS OPERATIVAS
    | Macro-Área | Grupo Operativo | Enfoque Crítico del Análisis en Ralentí |
    | :--- | :--- | :--- |
    | **Logística** | 🚚 Primera Milla | Control de tiempos de espera en plantas, Cedis, Centros de Empaque |
    | **Logística** | Transporte Interno | Control de tiempos de espera en plantas de alimentos, producciones avicolas y plantas clasificadoras |
    """)