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

    # FILTRADO DE INACTIVOS Y VALORES EN BLANCO
    if "grupo" in df.columns:
        df = df[df["grupo"].notna()]
        df["grupo"] = df["grupo"].astype(str).str.strip()
        df = df[df["grupo"] != ""]
        df = df[~df["grupo"].str.lower().str.contains("inac", na=False)]

    return df


# Carga de datos limpios
df = cargar_datos()

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
    ralenti_actual = round(dff["ralenti_seg"].sum() / dff["encendido_seg"].sum() * 100, 1)
    vehiculos_total = dff["nombre_dispositivo"].nunique()
    fuera_meta = (dff.groupby("nombre_dispositivo")["porcentaje_ralenti"].mean() > META_RALENTI).sum()
    
    # Calcular porcentaje para la tarjeta de "Fuera de Meta"
    porcentaje_fuera = round((fuera_meta / vehiculos_total) * 100) if vehiculos_total > 0 else 0
else:
    ralenti_actual = 0.0
    vehiculos_total = 0
    fuera_meta = 0
    porcentaje_fuera = 0

# --- COLUMNA 1: % RALENTÍ ACTUAL (Diseño Tarjeta Estándar) ---
with col1_kpi:
    st.markdown(f"""
    <div style="background-color: #ffffff; padding: 22px; border-radius: 12px; border: 1px solid #eef2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center; height: 165px;">
        <div style="font-size: 14px; font-weight: bold; color: #666; margin-bottom: 10px;">% RALENTÍ ACTUAL</div>
        <div style="font-size: 42px; font-weight: 800; color: #2c3e50; margin-top: 15px;">{ralenti_actual}%</div>
    </div>
    """, unsafe_allow_html=True)

# --- COLUMNA 2: FUERA DE META (Diseño idéntico a tu imagen) ---
with col2_kpi:
    st.markdown(f"""
    <div style="background-color: #ffffff; padding: 18px; border-radius: 12px; border: 1px solid #eef2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center; font-family: sans-serif; height: 165px;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 5px;">
            <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#ff3b30" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <div style="text-align: left;">
                <div style="font-size: 38px; font-weight: 800; color: #ff3b30; line-height: 1;">{porcentaje_fuera}%</div>
                <div style="font-size: 11px; font-weight: 700; color: #1c1c1e; letter-spacing: 0.5px; margin-top: 2px;">FUERA DE META</div>
            </div>
        </div>
        <div style="font-size: 18px; font-weight: 700; color: #1c1c1e; margin-top: 15px;">{fuera_meta} de {vehiculos_total} vehículos</div>
        <div style="font-size: 14px; font-weight: 600; color: #1c1c1e; margin-top: 5px;">Meta: ≤ {META_RALENTI}%</div>
    </div>
    """, unsafe_allow_html=True)

# --- COLUMNA 3: META DEFINIDA (Diseño Tarjeta Estándar) ---
with col3_kpi:
    st.markdown(f"""
    <div style="background-color: #ffffff; padding: 22px; border-radius: 12px; border: 1px solid #eef2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center; height: 165px;">
        <div style="font-size: 14px; font-weight: bold; color: #666; margin-bottom: 10px;">OBJETIVO INSTITUCIONAL</div>
        <div style="font-size: 42px; font-weight: 800; color: #7f8c8d; margin-top: 15px;">≤ {META_RALENTI}%</div>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# GRÁFICOS
# =====================================================

if not dff.empty:
    st.markdown("<br>", unsafe_allow_html=True) # Espaciador estético
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
            title="% Ralentí por Tipo", labels={"%ralenti": "% Ralentí", "tipo_vehiculo": "Tipo"},
            color_discrete_sequence=[COLOR_VERDE], text="%ralenti"
        )
        fig.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
        fig.add_vline(x=META_RALENTI, line_dash="dash", line_color="red", annotation_text="Meta")
        st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # TOP 5
    # =====================================================

    top = dff.groupby("nombre_dispositivo").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
    top["%ralenti"] = np.where(top["encendido_seg"] > 0, (top["ralenti_seg"] / top["encendido_seg"]) * 100, 0)
    top = top.sort_values("%ralenti", ascending=False).head(5)

    st.subheader("TOP 5 VEHÍCULOS CON MAYOR % RALENTÍ")
    st.dataframe(top, use_container_width=True, hide_index=True)

    # =====================================================
    # EVOLUCIÓN
    # =====================================================

    evo = dff.groupby("fecha").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
    evo["%ralenti"] = np.where(evo["encendido_seg"] > 0, (evo["ralenti_seg"] / evo["encendido_seg"]) * 100, 0)

    fig = px.line(
        evo, x="fecha", y="%ralenti", markers=True,
        title="EVOLUCIÓN DEL % RALENTÍ", labels={"%ralenti": "% Ralentí", "fecha": "Fecha"}
    )
    fig.add_hline(y=META_RALENTI, line_dash="dash", line_color="red", annotation_text="Meta Max")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos disponibles para los filtros seleccionados.")