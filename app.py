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

# Inyección de estilos CSS globales
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
            height: 380px; /* Altura fija para mantener alineación */
            overflow-y: auto; /* Barra de desplazamiento si hay muchos elementos */
            font-family: sans-serif;
            margin-bottom: 20px;
        }
        /* Estilos personalizados para el scroll de las tarjetas */
        .section-box::-webkit-scrollbar {
            width: 6px;
        }
        .section-box::-webkit-scrollbar-track {
            background: #f1f1f1; 
            border-radius: 4px;
        }
        .section-box::-webkit-scrollbar-thumb {
            background: #c1c1c1; 
            border-radius: 4px;
        }
        .section-box::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8; 
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
st.title("TABLERO DE GESTIÓN – RALENTÍ")

# =====================================================
# FILTROS
# =====================================================
fil_col1, fil_col2, fil_col3, fil_col4, fil_col5 = st.columns([1.8, 1.8, 1.8, 1.8, 2.8])

with fil_col1:
    grupos = st.multiselect("Grupo", sorted(df["grupo"].unique()), placeholder="Todas")
with fil_col2:
    vehiculos = st.multiselect("Vehículo", sorted(df["nombre_dispositivo"].unique()), placeholder="Todas")
with fil_col3:
    tipos_v = sorted(df["tipo_vehiculo"].dropna().unique()) if "tipo_vehiculo" in df.columns else []
    tipos = st.multiselect("Tipo de vehículo", tipos_v, placeholder="Todas")
with fil_col4:
    if "combustible" in df.columns:
        combustibles_v = sorted(df["combustible"].dropna().unique())
    elif "tipo_combustible" in df.columns:
        combustibles_v = sorted(df["tipo_combustible"].dropna().unique())
    else:
        combustibles_v = []
    combustibles = st.multiselect("Combustible", combustibles_v, placeholder="Todas")
with fil_col5:
    rango = st.date_input("Periodo", (df["fecha"].min(), df["fecha"].max()))

# Filtrado dinámico del DataFrame
dff = df.copy()

if grupos:
    dff = dff[dff["grupo"].isin(grupos)]
if vehiculos:
    dff = dff[dff["nombre_dispositivo"].isin(vehiculos)]
if tipos:
    if "tipo_vehiculo" in dff.columns:
        dff = dff[dff["tipo_vehiculo"].isin(tipos)]
if combustibles:
    col_activa = "combustible" if "combustible" in dff.columns else "tipo_combustible"
    if col_activa in dff.columns:
        dff = dff[dff[col_activa].isin(combustibles)]
if len(rango) == 2:
    f_min, f_max = pd.Timestamp(rango[0]), pd.Timestamp(rango[1])
    dff = dff[(dff["fecha"] >= f_min) & (dff["fecha"] <= f_max)]

# =====================================================
# RENDIMIENTO DEL TABLERO
# =====================================================
if not dff.empty:
    
    # --- CÁLCULO DE KPIS (Convertidos a Enteros) ---
    total_encendido = dff["encendido_seg"].sum()
    total_ralenti = dff["ralenti_seg"].sum()
    ralenti_actual = int(round((total_ralenti / total_encendido) * 100)) if total_encendido > 0 else 0
    
    vehiculos_total = dff["nombre_dispositivo"].nunique()
    promedios_vehiculo = dff.groupby("nombre_dispositivo")["porcentaje_ralenti"].mean()
    fuera_meta = int((promedios_vehiculo > META_RALENTI).sum())
    porcentaje_fuera = int(round((fuera_meta / vehiculos_total) * 100)) if vehiculos_total > 0 else 0
    
    anterior_pct = 18
    pp_diff = int(round(ralenti_actual - anterior_pct))
    pp_str = f"+{pp_diff} p.p." if pp_diff >= 0 else f"{pp_diff} p.p."

    # --- TARJETAS DE KPIS SUPERIORES ---
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

    with kpi_col1:
        is_critico = "background-color: #fce8e6; border: 1px solid #f5c2c1;" if ralenti_actual > 15 else ""
        html_kpi1 = "<div class='card-box' style='" + is_critico + " text-align: center;'>"
        html_kpi1 += "<div style='font-size: 12px; font-weight: bold; color: #555; letter-spacing:0.5px;'>% RALENTÍ ACTUAL</div>"
        html_kpi1 += "<div style='font-size: 38px; font-weight: 800; color: #d93025; margin-top: 5px;'>" + str(ralenti_actual) + "%</div>"
        html_kpi1 += "<div style='font-size: 13px; font-weight: 600; color: #555; margin-top:2px;'>Meta: " + str(META_RALENTI) + "%</div>"
        html_kpi1 += "<div style='display: inline-block; background-color: #d93025; color: white; font-size: 11px; font-weight: bold; padding: 4px 12px; border-radius: 4px; margin-top: 12px;'>⚠️ CRÍTICO (>15%)</div>"
        html_kpi1 += "</div>"
        st.markdown(html_kpi1, unsafe_allow_html=True)

    with kpi_col2:
        html_kpi2 = "<div class='card-box' style='text-align: center;'>"
        html_kpi2 += "<div style='display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 5px;'>"
        html_kpi2 += "<svg width='36' height='36' viewBox='0 0 24 24' fill='none' stroke='#d93025' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'>"
        html_kpi2 += "<path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'></path><circle cx='9' cy='7' r='4'></circle>"
        html_kpi2 += "<path d='M23 21v-2a4 4 0 0 0-3-3.87'></path><path d='M16 3.13a4 4 0 0 1 0 7.75'></path></svg>"
        html_kpi2 += "<div style='text-align: left;'>"
        html_kpi2 += "<div style='font-size: 36px; font-weight: 800; color: #d93025; line-height: 1;'>" + str(porcentaje_fuera) + "%</div>"
        html_kpi2 += "<div style='font-size: 11px; font-weight: 700; color: #111; letter-spacing: 0.5px;'>FUERA DE META</div>"
        html_kpi2 += "</div></div>"
        html_kpi2 += "<div style='font-size: 17px; font-weight: 700; color: #111; margin-top: 20px;'>" + str(fuera_meta) + " de " + str(vehiculos_total) + " vehículos</div>"
        html_kpi2 += "<div style='font-size: 13px; font-weight: 500; color: #444; margin-top: 2px;'>Meta: ≤ " + str(META_RALENTI) + "%</div></div>"
        st.markdown(html_kpi2, unsafe_allow_html=True)

    with kpi_col3:
        html_kpi3 = "<div class='card-box' style='text-align: center;'>"
        html_kpi3 += "<div style='display: flex; justify-content: center; align-items: center; gap: 20px; margin-top: 5px;'>"
        html_kpi3 += "<svg width='38' height='38' viewBox='0 0 24 24' fill='none' stroke='#1e7e34' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'>"
        html_kpi3 += "<polyline points='23 6 13.5 15.5 8.5 10.5 1 18'></polyline><polyline points='17 6 23 6 23 12'></polyline></svg>"
        html_kpi3 += "<div style='text-align: left;'>"
        html_kpi3 += "<div style='font-size: 34px; font-weight: 800; color: #d93025; line-height: 1;'>" + pp_str + "</div>"
        html_kpi3 += "<div style='font-size: 11px; font-weight: 700; color: #555; letter-spacing: 0.3px;'>VS. MES ANTERIOR</div>"
        html_kpi3 += "</div></div><hr style='margin: 15px 0 10px 0; border: 0; border-top: 1px solid #eee;'>"
        html_kpi3 += "<div style='display: flex; justify-content: space-around; font-size: 13px; font-weight: 600; color: #333;'>"
        html_kpi3 += "<div>Anterior: <span style='font-weight:800;'>" + str(anterior_pct) + "%</span></div>"
        html_kpi3 += "<div>Actual: <span style='font-weight:800; color:#d93025;'>" + str(ralenti_actual) + "%</span></div>"
        html_kpi3 += "</div></div>"
        st.markdown(html_kpi3, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- FILA CENTRAL ---
    mid_col1, mid_col2, mid_col3 = st.columns([1, 1, 1.2])

    # 1. Columna Grupo
    with mid_col1:
        g_df = dff.groupby("grupo").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
        g_df["%ralenti"] = np.where(g_df["encendido_seg"] > 0, (g_df["ralenti_seg"] / g_df["encendido_seg"]) * 100, 0)
        grupo_df = g_df.sort_values("%ralenti", ascending=False)
        
        html_grupo = "<div class='section-box'><div style='font-size:14px; font-weight:bold; color:#111; margin-bottom:15px;'>% RALENTÍ POR GRUPO ℹ️</div>"
        for _, row in grupo_df.iterrows():
            pct = int(round(row["%ralenti"]))
            dev_val = int(round(pct - META_RALENTI))
            dev_str = f"+{dev_val} p.p." if dev_val >= 0 else f"{dev_val} p.p."
            dev_color = "#d93025" if dev_val > 0 else "#1e7e34"
            bar_color = "#e67e22" if pct > META_RALENTI else "#2ecc71"
            html_grupo += "<div style='margin-bottom: 11px; font-size:13px;'>"
            html_grupo += "<div style='display:flex; justify-content:space-between; margin-bottom:3px; font-weight:600;'>"
            html_grupo += "<span style='color:#333;'>" + str(row['grupo']) + "</span>"
            html_grupo += "<span style='color:#111;'>" + str(pct) + "% <span style='color:" + dev_color + "; font-size:11px; margin-left:5px;'>" + dev_str + "</span></span></div>"
            html_grupo += "<div style='background-color:#edf2f7; border-radius:4px; height:8px; width:100%;'>"
            html_grupo += "<div style='background-color:" + bar_color + "; width:" + str(min(pct, 100)) + "%; height:8px; border-radius:4px;'></div></div></div>"
        html_grupo += "</div>"
        st.markdown(html_grupo, unsafe_allow_html=True)

    # 2. Columna Tipo de Vehículo
    with mid_col2:
        html_tipo = "<div class='section-box'><div style='font-size:14px; font-weight:bold; color:#111; margin-bottom:15px;'>% RALENTÍ POR TIPO DE VEHÍCULO ℹ️</div>"
        if "tipo_vehiculo" in dff.columns and not dff["tipo_vehiculo"].isna().all():
            t_df = dff.groupby("tipo_vehiculo").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
            t_df["%ralenti"] = np.where(t_df["encendido_seg"] > 0, (t_df["ralenti_seg"] / t_df["encendido_seg"]) * 100, 0)
            tipo_df = t_df.sort_values("%ralenti", ascending=False)
            
            for _, row in tipo_df.iterrows():
                pct = int(round(row["%ralenti"]))
                dev_val = int(round(pct - META_RALENTI))
                dev_str = f"+{dev_val} p.p." if dev_val >= 0 else f"{dev_val} p.p."
                dev_color = "#d93025" if dev_val > 0 else "#1e7e34"
                bar_color = "#1e7e34" if pct <= META_RALENTI else "#e67e22"
                html_tipo += "<div style='margin-bottom: 11px; font-size:13px;'>"
                html_tipo += "<div style='display:flex; justify-content:space-between; margin-bottom:3px; font-weight:600;'>"
                html_tipo += "<span style='color:#333;'>" + str(row['tipo_vehiculo']) + "</span>"
                html_tipo += "<span style='color:#111;'>" + str(pct) + "% <span style='color:" + dev_color + "; font-size:11px; margin-left:5px;'>" + dev_str + "</span></span></div>"
                html_tipo += "<div style='background-color:#edf2f7; border-radius:4px; height:8px; width:100%;'>"
                html_tipo += "<div style='background-color:" + bar_color + "; width:" + str(min(pct, 100)) + "%; height:8px; border-radius:4px;'></div></div></div>"
        else:
            html_tipo += "<p style='color:#777; font-size:13px; padding-top:10px;'>No hay datos de tipo de vehículo disponibles.</p>"
        html_tipo += "</div>"
        st.markdown(html_tipo, unsafe_allow_html=True)

    # 3. Columna Ranking Tabla
    with mid_col3:
        top_df = dff.groupby("nombre_dispositivo").agg({"ralenti_seg": "sum", "encendido_seg": "sum", "grupo": "first"}).reset_index()
        top = top_df.copy()
        top["%ralenti"] = np.where(top["encendido_seg"] > 0, (top["ralenti_seg"] / top["encendido_seg"]) * 100, 0)
        
        top["Horas Ralentí"] = (top["ralenti_seg"] / 3600).round().astype(int)
        top["Horas Operativas"] = (top["encendido_seg"] / 3600).round().astype(int)
        top = top.sort_values("%ralenti", ascending=False).head(5)
        
        html_top = "<div class='section-box'><div style='font-size:14px; font-weight:bold; color:#111; margin-bottom:10px;'>TOP 5 (POR % RALENTÍ)</div>"
        html_top += "<table style='width:100%; border-collapse: collapse; font-size:12px; text-align:left;'>"
        
        html_top += "<tr style='border-bottom: 2px solid #edf2f7; color:#555; font-weight:bold; white-space: nowrap;'><th style='padding:6px;'>#</th><th style='padding:6px;'>Placa</th><th style='padding:6px;'>Grupo</th><th style='padding:6px;'>% Ralentí (Horas)</th><th style='padding:6px;'>Horas Operativas</th></tr>"
        for idx, (_, row) in enumerate(top.iterrows(), 1):
            html_top += "<tr style='border-bottom: 1px solid #edf2f7; font-weight:600; color:#333; white-space: nowrap;'>"
            html_top += "<td style='padding:7px;'>" + str(idx) + "</td>"
            html_top += "<td style='padding:7px; color:#1e7e34;'>" + str(row['nombre_dispositivo']) + "</td>"
            html_top += "<td style='padding:7px; color:#555;'>" + str(row['grupo']) + "</td>" 
            
            pct_entero = int(round(row['%ralenti']))
            horas_ral_entero = int(row['Horas Ralentí'])
            horas_op_entero = int(row['Horas Operativas'])
            
            html_top += "<td style='padding:7px; color:#d93025;'>" + str(pct_entero) + "% <span style='color:#555; font-weight:normal; font-size:11px;'>(" + str(horas_ral_entero) + " h)</span></td>"
            html_top += "<td style='padding:7px;'>" + str(horas_op_entero) + " h</td></tr>"
        html_top += "</table></div>"
        st.markdown(html_top, unsafe_allow_html=True)

    # --- EVOLUCIÓN GRÁFICA INFERIOR ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    ultima_fecha = dff["fecha"].max()
    ultimo_mes = ultima_fecha.month
    ultimo_ano = ultima_fecha.year
    nombre_mes_ano = ultima_fecha.strftime('%m/%Y')
    
    st.markdown(f"<div style='font-size:14px; font-weight:bold; color:#111; margin-left:5px; margin-bottom:5px;'>EVOLUCIÓN DEL % RALENTÍ (ÚLTIMO MES DISPONIBLE: {nombre_mes_ano}) ℹ️</div>", unsafe_allow_html=True)
    
    dff_ultimo_mes = dff[(dff["fecha"].dt.month == ultimo_mes) & (dff["fecha"].dt.year == ultimo_ano)]

    if not dff_ultimo_mes.empty:
        evo = dff_ultimo_mes.groupby("fecha").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
        evo["%ralenti"] = np.where(evo["encendido_seg"] > 0, (evo["ralenti_seg"] / evo["encendido_seg"]) * 100, 0)
        
        evo["%ralenti"] = evo["%ralenti"].round().astype(int)
        evo["fecha_str"] = evo["fecha"].dt.strftime('%d/%m')

        fig = px.line(evo, x="fecha_str", y="%ralenti", markers=True, text="%ralenti")
        fig.update_traces(line_color="#1e7e34", line_width=2.5, marker=dict(size=7, color="#1e7e34"), textposition="top center", texttemplate="%{text}%")
        fig.add_hline(y=META_RALENTI, line_dash="dash", line_color="#e67e22", line_width=1.5)
        fig.update_layout(
            xaxis_title="", yaxis_title="", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=25, b=10), height=260,
            yaxis=dict(showgrid=True, gridcolor='#f0f0f0', range=[0, max(evo["%ralenti"].max() + 5, 20)])
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No se registran datos para graficar en el rango seleccionado.")

else:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info("⚠️ No hay datos disponibles para los filtros seleccionados. Intenta cambiar el rango de fechas o los filtros.")