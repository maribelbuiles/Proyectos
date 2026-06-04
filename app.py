import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Tablero Ralentí",
    layout="wide"
)

META_RALENTI = 10

# =====================================================
# API
# =====================================================

@st.cache_data(ttl=3600)
def cargar_datos():

    usuario = "incubadora.pbi"
    clave = "incubadora.pbi123"
    base_url = "https://app.bronto-byte.com"

    token_response = requests.post(
        f"{base_url}/api/obtenerToken",
        json={
            "usuario": usuario,
            "clave": clave
        },
        headers={
            "Content-Type":"application/json",
            "accept":"application/json"
        }
    )

    token = token_response.json()["token"]

    if token.lower().startswith("bearer "):
        token = token[7:]

    response = requests.get(
        f"{base_url}/api/v2/gps-resumen/vehiculos",
        headers={
            "Authorization": f"Bearer {token}",
            "accept":"application/json"
        }
    )

    data = response.json()

    success = data.get("success")
    id_cliente = data.get("id_cliente")
    fecha_desde = data.get("fecha_desde")
    fecha_hasta = data.get("fecha_hasta")

    registros = data.get("data", [])

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
# TITULO
# =====================================================

st.title("🚛 TABLERO DE GESTIÓN - RALENTÍ")
st.caption(
    "Monitoreo y análisis integral para una operación eficiente"
)

# =====================================================
# FILTROS
# =====================================================

col1,col2,col3 = st.columns(3)

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
    dff = dff[
        dff["grupo"].isin(grupos)
    ]

if vehiculos:
    dff = dff[
        dff["nombre_dispositivo"].isin(vehiculos)
    ]

if len(rango) == 2:

    dff = dff[
        (dff["fecha"] >= pd.Timestamp(rango[0]))
        &
        (dff["fecha"] <= pd.Timestamp(rango[1]))
    ]

# =====================================================
# KPIS
# =====================================================

ralenti_actual = round(

    dff["ralenti_seg"].sum()

    /

    dff["encendido_seg"].sum()

    *100,

    2

)

vehiculos_total = (
    dff["nombre_dispositivo"]
    .nunique()
)

fuera_meta = (

    dff.groupby(
        "nombre_dispositivo"
    )["porcentaje_ralenti"]

    .mean()

    > META_RALENTI

).sum()

col1,col2,col3 = st.columns(3)

col1.metric(
    "% Ralentí Actual",
    f"{ralenti_actual}%"
)

col2.metric(
    "Fuera de Meta",
    f"{fuera_meta}/{vehiculos_total}"
)

col3.metric(
    "Meta",
    f"{META_RALENTI}%"
)

# =====================================================
# GRAFICOS
# =====================================================

c1,c2 = st.columns(2)

with c1:

    grupo_df = (
        dff.groupby("grupo")
        .agg({
            "ralenti_seg":"sum",
            "encendido_seg":"sum"
        })
        .reset_index()
    )

    grupo_df["%ralenti"] = (
        grupo_df["ralenti_seg"]
        /
        grupo_df["encendido_seg"]
        *100
    )

    fig = px.bar(
        grupo_df,
        x="%ralenti",
        y="grupo",
        orientation="h",
        title="% Ralentí por Grupo"
    )

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

    tipo_df["%ralenti"] = (
        tipo_df["ralenti_seg"]
        /
        tipo_df["encendido_seg"]
        *100
    )

    fig = px.bar(
        tipo_df,
        x="%ralenti",
        y="tipo_vehiculo",
        orientation="h",
        title="% Ralentí por Tipo"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# TOP 5
# =====================================================

top = (
    dff.groupby(
        "nombre_dispositivo"
    )
    .agg({
        "ralenti_seg":"sum",
        "encendido_seg":"sum"
    })
    .reset_index()
)

top["%ralenti"] = (
    top["ralenti_seg"]
    /
    top["encendido_seg"]
    *100
)

top = top.sort_values(
    "%ralenti",
    ascending=False
).head(5)

st.subheader("TOP 5 VEHÍCULOS")

st.dataframe(
    top,
    use_container_width=True
)

# =====================================================
# EVOLUCION
# =====================================================

evo = (
    dff.groupby("fecha")
    .agg({
        "ralenti_seg":"sum",
        "encendido_seg":"sum"
    })
    .reset_index()
)

evo["%ralenti"] = (
    evo["ralenti_seg"]
    /
    evo["encendido_seg"]
    *100
)

fig = px.line(
    evo,
    x="fecha",
    y="%ralenti",
    markers=True,
    title="EVOLUCIÓN DEL % RALENTÍ"
)

fig.add_hline(
    y=META_RALENTI,
    line_dash="dash"
)

st.plotly_chart(
    fig,
    use_container_width=True
)