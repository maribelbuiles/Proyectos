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
# FILTRADO DE GRUPOS INACTIVOS
# =====================================================
if not df.empty and "grupo" in df.columns:
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
    col2.metric("Fuera de Meta", f"{fuera_meta}/{vehiculos_total}")
else:
    col1.metric("% Ralentí Actual", "0.0%")
    col2.metric("Fuera de Meta", "0/0")

col3.metric("Meta", f"{META_RALENTI}%")

# =====================================================
# GRÁFICOS
# =====================================================

if not dff.empty:
    c1, c2 = st.columns(2)

    with c1:
        grupo_df = (
            dff.groupby("grupo")
            .agg({
                "ralenti_seg":"sum",
                "encendido_seg":"sum"
            })
            .reset_index()
        )

        grupo_df["%ralenti"] = np.where(
            grupo_df["encendido_seg"] > 0,
            (grupo_df["ralenti_seg"] / grupo_df["encendido_seg"]) * 100,
            0
        )
        
        grupo_df = grupo_df.sort_values("%ralenti", ascending=True)

        fig = px.bar(
            grupo_df,
            x="%ralenti",
            y="grupo",
            orientation="h",
            title="% Ralentí por Grupo",
            labels={"%ralenti": "% Ralentí", "grupo": "Grupo"},
            color_discrete_sequence=[COLOR_VERDE],
            text="%ralenti"
        )
        
        fig.update_traces(
            texttemplate='%{text:.0f}%', 
            textposition='outside'
        )
        
        fig.add_vline(x=META_RALENTI, line_dash="dash", line_color="red", annotation_text="Meta")

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with c2:
        tipo_df = (
            dff.groupby("tipo_vehiculo")
            .agg({
                "ralenti_seg":"sum",
                "encendido_seg":"sum"
            })
            .reset_index()
        )

        tipo_df["%ralenti"] = np.where(
            tipo_df["encendido_seg"] > 0,
            (tipo_df["ralenti_seg"] / tipo_df["encendido_seg"]) * 100,
            0
        )
        
        tipo_df = tipo_df.sort_values("%ralenti", ascending=True)

        fig = px.bar(
            tipo_df,
            x="%ralenti",
            y="tipo_vehiculo",
            orientation="h",
            title="% Ralentí por Tipo",
            labels={"%ralenti": "% Ralentí", "tipo_vehiculo": "Tipo"},
            color_discrete_sequence=[COLOR_VERDE],
            text="%ralenti"
        )
        
        fig.update_traces(
            texttemplate='%{text:.0f}%', 
            textposition='outside'
        )
        
        fig.add_vline(x=META_RALENTI, line_dash="dash", line_color="red", annotation_text="Meta")

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # =====================================================
    # TOP 5
    # =====================================================

    top = (
        dff.groupby("nombre_dispositivo")
        .agg({
            "ralenti_seg":"sum",
            "encendido_seg":"sum"
        })
        .reset_index()
    )

    top["%ralenti"] = np.where(
        top["encendido_seg"] > 0,
        (top["ralenti_seg"] / top["encendido_seg"]) * 100,
        0
    )

    top = top.sort_values(
        "%ralenti",
        ascending=False
    ).head(5)

    st.subheader("TOP 5 VEHÍCULOS CON MAYOR % RALENTÍ")

    st.dataframe(
        top,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # EVOLUCIÓN
    # =====================================================

    evo = (
        dff.groupby("fecha")
        .agg({
            "ralenti_seg":"sum",
            "encendido_seg":"sum"
        })
        .reset_index()
    )

    evo["%ralenti"] = np.where(
        evo["encendido_seg"] > 0,
        (evo["ralenti_seg"] / evo["encendido_seg"]) * 100,
        0
    )

    fig = px.line(
        evo,
        x="fecha",
        y="%ralenti",
        markers=True,
        title="EVOLUCIÓN DEL % RALENTÍ",
        labels={"%ralenti": "% Ralentí", "fecha": "Fecha"}
    )

    fig.add_hline(
        y=META_RALENTI,
        line_dash="dash",
        line_color="red",
        annotation_text="Meta Max"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
else:
    st.info("No hay datos disponibles para los filtros seleccionados.")