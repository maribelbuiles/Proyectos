import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px

# =====================================
# CONFIGURACIÓN GENERAL Y ESTILOS
# =====================================
st.set_page_config(
    page_title="Tablero",
    layout="wide"
)

# Estilos CSS globales (Líneas cortas)
css = "<style>"
css += "div[data-testid='stBlock']"
css += " { padding: 0px; }"
css += ".reportview-container .main "
css += ".block-container "
css += "{ padding-top: 1rem; }"
css += "h1 { font-family: "
css += "'Helvetica Neue', Helvetica, "
css += "Arial, sans-serif; "
css += "font-weight: 800 !important; "
css += "color: #0a192f !important; }"
css += ".card-box { "
css += "background-color: #ffffff; "
css += "padding: 20px; "
css += "border-radius: 10px; "
css += "border: 1px solid #e1e8ed; "
css += "box-shadow: 0 2px 6px "
css += "rgba(0,0,0,0.04); "
css += "height: 190px; "
css += "font-family: sans-serif; }"
css += ".section-box { "
css += "background-color: #ffffff; "
css += "padding: 22px; "
css += "border-radius: 10px; "
css += "border: 1px solid #e1e8ed; "
css += "box-shadow: 0 2px 6px "
css += "rgba(0,0,0,0.04); "
css += "min-height: 340px; "
css += "font-family: sans-serif; "
css += "margin-bottom: 20px; }"
css += "</style>"
st.markdown(css, unsafe_allow_html=True)

META_RALENTI = 10

# =====================================
# API Y PROCESAMIENTO DE DATOS
# =====================================
@st.cache_data(ttl=3600)
def cargar_datos():
    u = "incubadora.pbi"
    p = "incubadora.pbi123"
    b = "https://"
    b += "app.bronto-byte.com"

    try:
        r1 = requests.post(
            b + "/api/obtenerToken",
            json={"usuario": u, "clave": p},
            headers={
                "Content-Type":
                "application/json",
                "accept":
                "application/json"
            },
            timeout=10
        )
        t = r1.json()["token"]

        if t.lower().startswith(
            "bearer "
        ):
            t = t[7:]

        h = {
            "Authorization":
            "Bearer " + t,
            "accept":
            "application/json"
        }
        r2 = requests.get(
            b + "/api/v2/gps-resumen/"
            "vehiculos",
            headers=h,
            timeout=15
        )
        data = r2.json()
    except Exception as e:
        st.error(
            "Error API: " + str(e)
        )
        return pd.DataFrame()

    success = data.get("success")
    idc = data.get("id_cliente")
    fd = data.get("fecha_desde")
    fh = data.get("fecha_hasta")

    registros = data.get("data", [])

    if not registros:
        return pd.DataFrame()

    for row in registros:
        row["success"] = success
        row["id_cliente"] = idc
        row["fecha_desde"] = fd
        row["fecha_hasta"] = fh

    df = pd.DataFrame(registros)
    df["fecha"] = pd.to_datetime(
        df["fecha"]
    )
    df["ralenti_seg"] = (
        df["detenido_seg"]
    )

    df["porcentaje_ralenti"] = (
        np.where(
            df["encendido_seg"] > 0,
            (df["ralenti_seg"] /
             df["encendido_seg"])
            * 100,
            0
        )
    )

    if "grupo" in df.columns:
        df = df[df["grupo"].notna()]
        df["grupo"] = (
            df["grupo"]
            .astype(str)
            .str.strip()
        )
        df = df[df["grupo"] != ""]
        low = df["grupo"].str.lower()
        df = df[
            ~low.str.contains(
                "inac",
                na=False
            )
        ]

    return df

df = cargar_datos()

if df.empty:
    st.warning("Sin datos de API.")
    st.stop()

# =====================================
# ENCABEZADO PRINCIPAL
# =====================================
st.title(
    "TABLERO DE GESTIÓN – RALENTÍ"
)

# =====================================
# FILTROS
# =====================================
fil1, fil2, fil3, fil4, fil5 = (
    st.columns(