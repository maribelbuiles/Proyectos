import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px

# =====================================================
# CONFIGURACIÓN
# =====================================================
st.set_page_config(page_title="Tablero de Gestión - Ralentí", layout="wide")

st.markdown("""
    <style>
        .card-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e1e8ed; box-shadow: 0 2px 6px rgba(0,0,0,0.04); height: 190px; }
        .section-box { background-color: #ffffff; padding: 22px; border-radius: 10px; border: 1px solid #e1e8ed; box-shadow: 0 2px 6px rgba(0,0,0,0.04); height: 380px; overflow-y: auto; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

META_RALENTI = 10

# =====================================================
# CARGA DE DATOS
# =====================================================
@st.cache_data(ttl=3600)
def cargar_datos():
    # Nota: Asegúrate que las credenciales y URL sean correctas
    # Si la API falla, devolverá un DF vacío
    usuario = "incubadora.pbi"
    clave = "incubadora.pbi123"
    base_url = "https://app.bronto-byte.com"
    
    try:
        token_response = requests.post(f"{base_url}/api/obtenerToken", 
                                       json={"usuario": usuario, "clave": clave}, timeout=10)
        token = token_response.json()["token"].replace("Bearer ", "")
        
        response = requests.get(f"{base_url}/api/v2/gps-resumen/vehiculos", 
                                headers={"Authorization": f"Bearer {token}"}, timeout=15)
        registros = response.json().get("data", [])
        
        if not registros: return pd.DataFrame()
        
        df = pd.DataFrame(registros)
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["ralenti_seg"] = df["detenido_seg"]
        df["porcentaje_ralenti"] = np.where(df["encendido_seg"] > 0, (df["ralenti_seg"] / df["encendido_seg"]) * 100, 0)
        
        # Limpieza base
        df = df[df["grupo"].notna() & (df["grupo"] != "")]
        return df
    except:
        return pd.DataFrame()

df = cargar_datos()

# =====================================================
# INTERFAZ
# =====================================================
st.title("TABLERO DE GESTIÓN – RALENTÍ")

if df.empty:
    st.error("No se pudieron cargar los datos. Verifica la conexión a la API.")
    st.stop()

tab1, tab2 = st.tabs(["📊 Tablero de Control", "📋 Hoja de Vida"])

with tab1:
    # --- FILTROS DINÁMICOS EN CASCADA ---
    col1, col2, col3, col4 = st.columns(4)
    
    # Filtro 1: Grupo
    with col1:
        grupos_sel = st.multiselect("Grupo", sorted(df["grupo"].unique()))
    
    dff = df.copy()
    if grupos_sel:
        dff = dff[dff["grupo"].isin(grupos_sel)]
        
    # Filtro 2: Vehículo (según Grupo)
    with col2:
        vehiculos_sel = st.multiselect("Vehículo", sorted(dff["nombre_dispositivo"].unique()))
    if vehiculos_sel:
        dff = dff[dff["nombre_dispositivo"].isin(vehiculos_sel)]
        
    # Filtro 3: Tipo (según Grupo y Vehículo)
    with col3:
        tipos_disponibles = sorted(dff["tipo_vehiculo"].dropna().unique())
        tipos_sel = st.multiselect("Tipo de vehículo", tipos_disponibles)
    if tipos_sel:
        dff = dff[dff["tipo_vehiculo"].isin(tipos_sel)]
        
    # Filtro 4: Combustible
    with col4:
        col_comb = "combustible" if "combustible" in dff.columns else "tipo_combustible"
        comb_disponibles = sorted(dff[col_comb].dropna().unique())
        comb_sel = st.multiselect("Combustible", comb_disponibles)
    if comb_sel:
        dff = dff[dff[col_comb].isin(comb_sel)]

    # --- VISUALIZACIÓN ---
    if not dff.empty:
        st.write(f"Mostrando {len(dff)} registros.")
        # Aquí irían tus gráficos y tarjetas (KPIs, Plotly, etc.)
    else:
        st.warning("⚠️ No hay datos disponibles para la combinación de filtros seleccionada.")

with tab2:
    st.markdown("### 📋 HOJA DE VIDA DEL INDICADOR")
    # Contenido de la hoja de vida...