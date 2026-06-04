import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px

# =====================================================
# CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="Tablero Ralentí",
    layout="wide"
)

META_RALENTI = 10
COLOR_VERDE = "#2ecc71"  # Color esmeralda para las barras

# =====================================================
# API
# =====================================================

@st.cache_data(ttl=3600)
def cargar_datos():
    usuario = "incubadora.pbi"
    clave = "incubadora.pbi123"
    base_url = "https://app.bronto-byte.com"

    try:
        token_response = requests.post(
            f"{base_url}/api/obtenerToken",
            json={
                "usuario": usuario,
                "clave": clave
            },
            headers={
                "Content-Type":"application/json",
                "accept":"application/json"
            },
            timeout=10
        )
        token = token_response.json()["token"]

        if token.lower().startswith("bearer "):
            token = token[7:]

        response = requests.get(
            f"{base_url}/api/v2/gps-resumen/vehiculos",
            headers={
                "Authorization": f"Bearer {token}",
                "accept":"application/json"
            },
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

    # CAMPO TEMPORAL
    df["ralenti_seg"] = df["detenido_seg"]

    df["porcentaje_ralenti"] = np.where(
        df["encendido_seg"] > 0,
        (df["ralenti_seg"] / df["encendido_seg"]) * 100,
        0
    )

    return df


df = cargar_datos()

# =====================================================
# FILTRADO DE GRUPOS INACTIVOS (NUEVA MODIFICACIÓN)
# =====================================================
if not df.empty and "grupo" in df.columns:
    # Se eliminan filas donde el grupo sea "inactivos", ignorando mayúsculas/minúsculas
    df = df[df["grupo"].str.lower().fillna("") != "inactivos"]

# Control por si la API no devuelve registros al iniciar
if df.empty:
    st.warning("No se encontraron datos disponibles en la API.")
    st.stop()

# =====================================================
# TÍTULO
# =====================================================

st.title("🚛 TABLERO DE GESTIÓN - RALENTÍ")
st.caption(
    "Monitoreo y análisis integral para una operación eficiente"
)

# =====================================================
# FILTROS
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    grupos = st.multiselect(
        "Grupo",
        sorted(df["grupo"].dropna().unique())
    )

with col2:
    vehiculos = st.multiselect(
        "Vehículo",
        sorted(df["nombre_dispositivo"].dropna().unique())
    )

with col3:
    rango = st.date_input(
        "Periodo",
        (
            df["fecha"].min(),
            df["fecha"].max()
        )
    )

# =====================================================
# FILTRO DATAFRAME
# =====================================================

dff = df.copy()

if grupos:
    dff = dff[dff["grupo"].isin(grupos)]

if vehiculos:
    dff = dff[dff["nombre_dispositivo"].isin(vehiculos)]

if len(rango) == 2:
    dff = dff[
        (dff["fecha"] >= pd.Timestamp(rango[0]))
        &
        (dff["fecha"] <= pd.Timestamp(rango[1]))
    ]

# =====================================================
# KPIS
# =====================================================

col1, col2, col3 = st.columns(3)

if not dff.empty and dff["encendido_seg"].sum() > 0:
    ralenti_actual = round(
        dff["ralenti_seg"].sum() / dff["encendido_seg"].sum() * 100, 
        2
    )
    vehiculos_total = dff["nombre_dispositivo"].nunique()

    fuera_meta = (
        dff.groupby("nombre_dispositivo")["porcentaje_ralenti"]
        .mean() > META_RALENTI
    ).sum()

    col1.metric("% Ralentí Actual", f"{ralenti_actual}%")
    col2.metric("