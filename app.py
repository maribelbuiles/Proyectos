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
        .section-box { background-color: #ffffff; padding: 22px; border-radius: 10px; border: 1px solid #e1e8ed; box-shadow: 0 2px 6px rgba(0,0,0,0.04); height: 380px; overflow-y: auto; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

META_RALENTI = 10

# =====================================================
# API Y PROCESAMIENTO (Mismo flujo original)
# =====================================================
@st.cache_data(ttl=3600)
def cargar_datos():
    # ... (Tu lógica de API permanece igual)
    # Simulando carga de datos para el ejemplo si no conectas a la API
    # Reemplaza esto con tu lógica real de requests
    return pd.DataFrame() # Aquí iría tu df cargado

df = cargar_datos()

if df.empty:
    st.warning("No se encontraron datos disponibles.")
    st.stop()

# =====================================================
# PESTAÑA 1: TABLERO DE CONTROL
# =====================================================
st.title("TABLERO DE GESTIÓN – RALENTÍ")
tab1, tab2 = st.tabs(["📊 Tablero de Control", "📋 Hoja de Vida"])

with tab1:
    # --- LÓGICA DE FILTROS EN CASCADA ---
    dff = df.copy()

    # 1. Filtro Grupo
    grupos_sel = st.multiselect("Grupo", sorted(df["grupo"].unique()))
    if grupos_sel:
        dff = dff[dff["grupo"].isin(grupos_sel)]

    # 2. Filtro Vehículo (depende de grupos)
    vehiculos_sel = st.multiselect("Vehículo", sorted(dff["nombre_dispositivo"].unique()))
    if vehiculos_sel:
        dff = dff[dff["nombre_dispositivo"].isin(vehiculos_sel)]

    # 3. Filtro Tipo (depende de grupos y vehículos)
    tipos_disponibles = sorted(dff["tipo_vehiculo"].dropna().unique())
    tipos_sel = st.multiselect("Tipo de vehículo", tipos_disponibles)
    if tipos_sel:
        dff = dff[dff["tipo_vehiculo"].isin(tipos_sel)]

    # 4. Filtro Combustible (depende de todo lo anterior)
    col_comb = "combustible" if "combustible" in dff.columns else "tipo_combustible"
    comb_disponibles = sorted(dff[col_comb].dropna().unique())
    comb_sel = st.multiselect("Combustible", comb_disponibles)
    if comb_sel:
        dff = dff[dff[col_comb].isin(comb_sel)]

    # 5. Fecha
    rango = st.date_input("Periodo", (df["fecha"].min(), df["fecha"].max()))
    if len(rango) == 2:
        dff = dff[(dff["fecha"] >= pd.Timestamp(rango[0])) & (dff["fecha"] <= pd.Timestamp(rango[1]))]

    # --- RESTO DEL DASHBOARD CON EL DF FILTRADO (dff) ---
    if not dff.empty:
        # Aquí continúa tu código de KPIs, Gráficos y Tablas usando 'dff'
        st.success(f"Datos filtrados: {len(dff)} registros encontrados.")
        # ... (Insertar aquí el resto de tu lógica de visualización)
    else:
        st.info("No hay datos para la selección actual.")