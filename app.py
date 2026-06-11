```python
import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Tablero de Gestión - Ralentí",
    layout="wide"
)

META_RALENTI = 10

# =====================================================
# ESTILOS
# =====================================================

st.markdown("""
<style>

.card-box{
    background:white;
    padding:20px;
    border-radius:10px;
    border:1px solid #e5e7eb;
    box-shadow:0 2px 6px rgba(0,0,0,.05);
}

.section-box{
    background:white;
    padding:20px;
    border-radius:10px;
    border:1px solid #e5e7eb;
    box-shadow:0 2px 6px rgba(0,0,0,.05);
}

</style>
""", unsafe_allow_html=True)

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
            timeout=15
        )

        token = token_response.json()["token"]

        if token.lower().startswith("bearer "):
            token = token[7:]

        response = requests.get(
            f"{base_url}/api/v2/gps-resumen/vehiculos",
            headers={
                "Authorization":f"Bearer {token}",
                "accept":"application/json"
            },
            timeout=20
        )

        data = response.json()

    except Exception as e:

        st.error(f"Error API: {e}")
        return pd.DataFrame()

    registros = data.get("data", [])

    if len(registros) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(registros)

    df["fecha"] = pd.to_datetime(df["fecha"])

    df["ralenti_seg"] = df["detenido_seg"]

    df["porcentaje_ralenti"] = np.where(
        df["encendido_seg"] > 0,
        (df["ralenti_seg"] / df["encendido_seg"]) * 100,
        0
    )

    return df


df = cargar_datos()

if df.empty:
    st.warning("No hay datos disponibles.")
    st.stop()

# =====================================================
# TITULO
# =====================================================

st.title("🚛 TABLERO DE GESTIÓN - RALENTÍ")

# =====================================================
# FILTROS
# =====================================================

c1,c2,c3,c4 = st.columns(4)

with c1:

    grupos = st.multiselect(
        "Grupo",
        sorted(df["grupo"].dropna().unique())
    )

with c2:

    vehiculos = st.multiselect(
        "Vehículo",
        sorted(df["nombre_dispositivo"].dropna().unique())
    )

with c3:

    tipos = st.multiselect(
        "Tipo Vehículo",
        sorted(df["tipo_vehiculo"].dropna().unique())
    )

with c4:

    rango = st.date_input(
        "Periodo",
        (
            df["fecha"].min(),
            df["fecha"].max()
        )
    )

# =====================================================
# FILTROS DATAFRAME
# =====================================================

dff = df.copy()

if grupos:
    dff = dff[dff["grupo"].isin(grupos)]

if vehiculos:
    dff = dff[dff["nombre_dispositivo"].isin(vehiculos)]

if tipos:
    dff = dff[dff["tipo_vehiculo"].isin(tipos)]

if len(rango) == 2:

    dff = dff[
        (dff["fecha"] >= pd.Timestamp(rango[0]))
        &
        (dff["fecha"] <= pd.Timestamp(rango[1]))
    ]

# =====================================================
# KPIS
# =====================================================

total_encendido = dff["encendido_seg"].sum()

total_ralenti = dff["ralenti_seg"].sum()

ralenti_actual = round(
    (total_ralenti / total_encendido) * 100,
    2
) if total_encendido > 0 else 0

vehiculos_total = dff["nombre_dispositivo"].nunique()

fuera_meta = (
    dff.groupby("nombre_dispositivo")["porcentaje_ralenti"]
    .mean()
    .gt(META_RALENTI)
    .sum()
)

k1,k2,k3 = st.columns(3)

k1.metric(
    "% Ralentí",
    f"{ralenti_actual}%"
)

k2.metric(
    "Fuera Meta",
    f"{fuera_meta}/{vehiculos_total}"
)

k3.metric(
    "Meta",
    f"{META_RALENTI}%"
)

# =====================================================
# GRÁFICOS
# =====================================================

g1,g2 = st.columns(2)

with g1:

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

    fig1 = px.bar(
        grupo_df.sort_values("%ralenti"),
        x="%ralenti",
        y="grupo",
        orientation="h",
        color_discrete_sequence=["#1e7e34"]
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

with g2:

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

    fig2 = px.bar(
        tipo_df.sort_values("%ralenti"),
        x="%ralenti",
        y="tipo_vehiculo",
        orientation="h",
        color_discrete_sequence=["#1e7e34"]
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

# =====================================================
# TOP 5
# =====================================================

st.subheader("TOP 5 VEHÍCULOS")

top = (
    dff.groupby("nombre_dispositivo")
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

top["Horas Ralentí"] = round(
    top["ralenti_seg"] / 3600,
    1
)

top["Horas Operativas"] = round(
    top["encendido_seg"] / 3600,
    1
)

top = (
    top.sort_values(
        "%ralenti",
        ascending=False
    )
    .head(5)
)

st.dataframe(
    top[
        [
            "nombre_dispositivo",
            "%ralenti",
            "Horas Ralentí",
            "Horas Operativas"
        ]
    ],
    use_container_width=True
)

# =====================================================
# EVOLUCIÓN
# =====================================================

st.subheader("EVOLUCIÓN % RALENTÍ")

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

fig3 = px.line(
    evo,
    x="fecha",
    y="%ralenti",
    markers=True
)

fig3.update_traces(
    line_color="#1e7e34",
    marker_color="#1e7e34"
)

fig3.add_hline(
    y=META_RALENTI,
    line_dash="dash",
    line_color="#e67e22"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)
```
