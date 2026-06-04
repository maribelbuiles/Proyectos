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

    # CAMPO TEMPORAL
    df["ralenti_seg"] = df["detenido_seg"]

    df["porcentaje_ralenti"] = np.where(
        df["encendido_seg"] > 0,
        (df["ralenti_seg"] / df["encendido_seg"]) * 100,
        0
    )

    # -----------------------------------------------------------------
    # FILTRADO DE INACTIVOS Y VALORES EN BLANCO (DENTRO DEL CACHÉ)
    # -----------------------------------------------------------------
    if "grupo" in df.columns:
        # 1. Eliminar filas donde el grupo sea completamente nulo (NaN)
        df = df[df["grupo"].notna()]
        
        # 2. Limpiar espacios extras alrededor del texto
        df["grupo"] = df["grupo"].astype(str).str.strip()
        
        # 3. Quitar los que quedaron vacíos o "en blanco" ("")
        df = df[df["grupo"] != ""]
        
        # 4. Quitar los que contengan la palabra "inac" (Inactivos)
        df = df[~df["grupo"].str.lower().str.contains("inac", na=False)]

    return df


# Carga de datos limpios
df = cargar_datos()

# Control de seguridad si el dataframe queda vacío tras los filtros
if df.empty:
    st.warning("No se encontraron datos disponibles o válidos en la API.")
    st.stop()

# =====================================================
# TÍTULO
# =====================================================

st.title("🚛 TABLERO DE GESTIÓN - RALENTÍ")
st.caption("Monitoreo y análisis integral para una operación eficiente")

# =====================================================
# FILTROS
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:
    grupos = st.multiselect("Grupo", sorted(df["grupo"].dropna().unique()))

with col2:
    vehiculos = st.multiselect("Vehículo", sorted(df["nombre_dispositivo"].dropna().unique()))

with col3:
    rango = st.date_input("Periodo", (df["fecha"].min(), df["fecha"].max()))

# =====================================================
# FILTRO DATAFRAME
# =====================================================

dff = df.copy()

if grupos:
    dff = dff[dff["grupo"].isin(grupos)]

if vehiculos:
    dff = dff[dff["nombre_dispositivo"].isin(vehiculos)]

if len(rango) == 2:
    dff = dff[(dff["fecha"] >= pd.Timestamp(rango[0])) & (dff["fecha"] <= pd.Timestamp(rango[1]))]

# =====================================================
# KPIS
# =====================================================

col1_kpi, col2_kpi, col3_kpi = st.columns(3)

if not dff.empty and dff["encendido_seg"].sum() > 0:
    ralenti_actual = round(dff["ralenti_seg"].sum() / dff["encendido_seg"].sum() * 100, 2)
    vehiculos_total = dff["nombre_dispositivo"].nunique()
    fuera_meta = (dff.groupby("nombre_dispositivo")["porcentaje_ralenti"].mean() > META_RALENTI).sum()

    col1_kpi.metric("% Ralentí Actual", f"{ralenti_actual}%")
    col2_kpi.metric("Fuera de Meta", f"{fuera_meta}/{vehiculos_total}")
else:
    col1_kpi.metric("% Ralentí Actual", "0.0%")
    col2_kpi.metric("Fuera de Meta", "0/0")

col3_kpi.metric("Meta", f"{META_RALENTI}%")

# =====================================================
# GRÁFICOS
# =====================================================

if not dff.empty:
    c1, c2 = st.columns(2)

    with c1:
        grupo_df = dff.groupby("grupo").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
        grupo_df["%ralenti"] = np.where(grupo_df["encendido_seg"] > 0, (grupo_df["ralenti_seg"] / grupo_df["encendido_seg"]) * 100, 0)
        grupo_df = grupo_df.sort_values("%ralenti", ascending=True)

        fig = px.bar(
            grupo_df, x="%ralenti", y="grupo", orientation="h",
            title="% Ralentí por Grupo", labels={"%ralenti": "% Ralentí", "grupo": "Grupo"},
            color_discrete_sequence=[COLOR_VERDE], text="%ralenti"
        )
        fig.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
        fig.add_vline(x=META_RALENTI, line_dash="dash", line_color="red", annotation_text="Meta")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        tipo_df = dff.groupby("tipo_vehiculo").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
        tipo_df["%ralenti"] = np.where(tipo_df["encendido_seg"] > 0, (tipo_df["ralenti_seg"] / tipo_df["encendido_seg"]) * 100, 0)
        tipo_df = tipo_df.sort_values("%ralenti", ascending=True)

        fig = px.bar(
            tipo_df, x="%ralenti", y="tipo_vehiculo", orientation="h",
            title="% Ralentí por Tipo", labels={"%ralenti": "% Ral