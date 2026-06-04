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

# Inyección de estilos CSS globales para asimilar el diseño limpio de la imagen
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
            min-height: 340px;
            font-family: sans-serif;
        }
        .footer-link {
            font-size: 13px; font-weight: 600; color: #1e7e34; text-decoration: none; display: inline-block; margin-top: 15px;
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

    success = data.get("success")
    id_cliente = data.get("id_cliente")
    fecha_desde = data.get("fecha_desde")
    fecha_hasta = data.get("fecha_hasta")

    registros = data.get("data", [])

    if not registros:
        return pd.DataFrame()

    for row in registros:
        row["success"] = success
        row["id_cliente"] = id_cliente
        row["fecha_desde"] = fecha_desde
        row["fecha_hasta"] = fecha_hasta

    df = pd.DataFrame(registros)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["ralenti_seg"] = df["detenido_seg"]

    df["porcentaje_ralenti"] = np.where(
        df["encendido_seg"] > 0,
        (df["ralenti_seg"] / df["encendido_seg"]) * 100,
        0
    )

    # Filtrado inicial de campos vacíos o inactivos
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
# ENCABEZADO PRINCIPAL
# =====================================================
head_col1, head_col2 = st.columns([7, 3])
with head_col1:
    st.title("TABLERO DE GESTIÓN – RALENTÍ")
    st.markdown("<p style='color:#555; margin-top:-15px; font-size:15px;'>Monitoree y análisis integral para una operación eficiente y segura</p>", unsafe_allow_html=True)
with head_col2:
    st.markdown("""
        <div style="text-align: right; margin-top: 15px; font-family: sans-serif; font-size: 13px; color: #333;">
            <span style="font-weight: bold; color: #2c3e50;">👤 MARIANA PORTAL</span> &nbsp;|&nbsp; 🔔 <span style="background-color:red; color:white; border-radius:50%; padding:2px 6px; font-size:10px;">23</span>
        </div>
    """, unsafe_allow_html=True)

# =====================================================
# FILTROS
# =====================================================
fil_col1, fil_col2, fil_col3, fil_col4, fil_col5 = st.columns([2, 2, 2, 3, 1])

with fil_col1:
    grupos = st.multiselect("Grupo", sorted(df["grupo"].unique()), placeholder="Todas")
with fil_col2:
    vehiculos = st.multiselect("Vehículo", sorted(df["nombre_dispositivo"].unique()), placeholder="Todas")
with fil_col3:
    tipos_v = sorted(df["tipo_vehiculo"].dropna().unique()) if "tipo_vehiculo" in df.columns else []
    tipos = st.multiselect("Tipo de vehículo", tipos_v, placeholder="Todas")
with fil_col4:
    rango = st.date_input("Periodo", (df["fecha"].min(), df["fecha"].max()))
with fil_col5:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Limpiar"):
        st.rerun()

# Filtrado dinámico del DataFrame
dff = df.copy()
if grupos:
    dff = dff[dff["grupo"].isin(grupos)]
if vehiculos:
    dff = dff[dff["nombre_dispositivo"].isin(vehiculos)]
if tipos and "tipo_vehiculo" in dff.columns:
    dff = dff[dff["tipo_vehiculo"].isin(tipos)]
if len(rango) == 2:
    dff = dff[(dff["fecha"] >= pd.Timestamp(rango[0])) & (dff["fecha"] <= pd.Timestamp(rango[1]))]

# =====================================================
# RENDIMIENTO DE KPIS (TARJETAS SUPERIORES)
# =====================================================
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

if not dff.empty and dff["encendido_seg"].sum() > 0:
    ralenti_actual =