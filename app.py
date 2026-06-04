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
# ENCABEZADO PRINCIPAL CON IMAGEN DE TRACTOCAMIÓN
# =====================================================
head_col1, head_col2 = st.columns([7, 3])
with head_col1:
    st.title("TABLERO DE GESTIÓN – RALENTÍ")
    st.markdown("<p style='color:#555; margin-top:-15px; font-size:15px;'>Monitoree y análisis integral para una operación eficiente y segura</p>", unsafe_allow_html=True)

with head_col2:
    # URL pública de una imagen de tractocamión en alta definición
    url_tractocamion = "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=400&auto=format&fit=crop&q=80"
    
    # Contenedor HTML para darle esquinas redondeadas y alineación perfecta
    st.markdown(f"""
        <div style="text-align: right; margin-top: 5px;">
            <img src="{url_tractocamion}" style="width: 100%; max-width: 260px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border: 1px solid #e1e8ed;">
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

# Inicialización por defecto de variables
ralenti_actual = 0.0
vehiculos_total = 0
fuera_meta = 0
porcentaje_fuera = 0
anterior_pct = 17.60
pp_str = "0.0 p.p."

if not dff.empty:
    total_encendido = dff["encendido_seg"].sum()
    total_ralenti = dff["ralenti_seg"].sum()
    
    if total_encendido > 0:
        ralenti_actual = round((total_ralenti / total_encendido) * 100, 2)
        
    vehiculos_total = dff["nombre_dispositivo"].nunique()
    
    promedios_vehiculo = dff.groupby("nombre_dispositivo")["porcentaje_ralenti"].mean()
    fuera_meta = int((promedios_vehiculo > META_RALENTI).sum())
    
    if vehiculos_total > 0:
        porcentaje_fuera = round((fuera_meta / vehiculos_total) * 100)
        
    pp_diff = round(ralenti_actual - anterior_pct, 2)
    if pp_diff >= 0:
        pp_str = f"+{pp_diff} p.p."
    else:
        pp_str = f"{pp_diff} p.p."

# --- TARJETA 1: % RALENTÍ ACTUAL ---
with kpi_col1:
    is_critico = "background-color: #fce8e6; border: 1px solid #f5c2c1;" if ralenti_actual > 15 else ""
    st.markdown(f"""
    <div class="card-box" style="{is_critico} text-align: center;">
        <div style="font-size: 12px; font-weight: bold; color: #555; letter-spacing:0.5px;">% RALENTÍ ACTUAL</div>
        <div style="font-size: 38px; font-weight: 800; color: #d93025; margin-top: 5px;">{ralenti_actual}%</div>
        <div style="font-size: 13px; font-weight: 600; color: #555; margin-top:2px;">Meta: {META_RALENTI}%</div>
        <div style="display: inline-block; background-color: #d93025; color: white; font-size: 11px; font-weight: bold; padding: 4px 12px; border-radius: 4px; margin-top: 12px;">
            ⚠️ CRÍTICO (>15%)
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- TARJETA 2: FUERA DE META ---
with kpi_col2:
    st.markdown(f"""
    <div class="card-box" style="text-align: center;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 5px;">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d93025" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <div style="text-align: left;">
                <div style="font-size: 36px; font-weight: 800; color: #d93025; line-height: 1;">{porcentaje_fuera}%</div>
                <div style="font-size: 11px; font-weight: 700; color: #111; letter-spacing: 0.5px;">FUERA DE META</div>
            </div>
        </div>
        <div style="font-size: 17px; font-weight: 700; color: #111; margin-top: 20px;">{fuera_meta} de {vehiculos_total} vehículos</div>
        <div style="font-size: 13px; font-weight: 500; color: #444; margin-top: 2px;">Meta: ≤ {META_RALENTI}%</div>
    </div>
    """, unsafe_allow_html=True)

# --- TARJETA 3: VS MES ANTERIOR ---
with kpi_col3:
    st.markdown(f"""
    <div class="card-box" style="text-align: center;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 20px; margin-top: 5px;">
            <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#1e7e34" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                <polyline points="17 6 23 6 23 12"></polyline>
            </svg>
            <div style="text-align: left;">
                <div style="font-size: 34px; font-weight: 800; color: #d93025; line-height: 1;">{pp_str}</div>
                <div style="font-size: 11px; font-weight: 700; color: #555; letter-spacing: 0.3px;">VS. MES ANTERIOR</div>
            </div>
        </div>
        <hr style="margin: 15px 0 10px 0; border: 0; border-top: 1px solid #eee;">
        <div style="display: flex; justify-content: space-around; font-size: 13px; font-weight: 600; color: #333;">
            <div>Anterior: <span style="font-weight:800;">{anterior_pct}%</span></div>
            <div>Actual: <span style="font-weight:800; color:#d93025;">{ralenti_actual}%</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================
# FILA CENTRAL: GRUPOS, TIPOS Y RANKING
# =====================================================
if not dff.empty:
    mid_col1, mid_col2, mid_col3 = st.columns([1, 1, 1.2])

    # --- SECCIÓN 1: % RALENTÍ POR GRUPO ---
    with mid_col1:
        st.markdown("<div class='section-box'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:14px; font-weight:bold; color:#111; margin-bottom:15px;'>% RALENTÍ POR GRUPO ℹ️</div>", unsafe_allow_html=True)
        
        grupo_df = dff.groupby("grupo").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
        grupo_df["%ralenti"] = np.where(grupo_df["encendido_seg"] > 0, (grupo_df["ralenti_seg"] / grupo_df["encendido_seg"]) * 100, 0)
        grupo_df = grupo_df.sort_values("%ralenti", ascending=False)
        
        for _, row in grupo_df.head(4).iterrows():
            pct = round(row["%ralenti"], 1)
            dev_val = round(pct - META_RALENTI, 1)
            dev_str = f"+{dev_val} p.p." if dev_val >= 0 else f"{dev_val} p.p."
            dev_color = "#d93025" if dev_val > 0 else "#1e7e34"
            bar_color = "#e67e22" if pct > META_RALENTI else "#2ecc71"
            
            st.markdown(f"""
                <div style="margin-bottom: 11px; font-size:13px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px; font-weight:600;">
                        <span style="color:#333;">{row['grupo']}</span>
                        <span style="color:#111;">{pct}% <span style="color:{dev_color}; font-size:11px; margin-left:5px;">{dev_str}</span></span>
                    </div>
                    <div style="background-color:#edf2f7; border-radius:4px; height:8px; width:100%;">
                        <div style="background-color:{bar_color}; width:{min(pct, 100)}%; height:8px; border-radius:4px;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("<a href='#' class='footer-link'>Ver detalle por grupo ></a></div>", unsafe_allow_html=True)

    # --- SECCIÓN 2: % RALENTÍ POR TIPO DE VEHÍCULO ---
    with mid_col2:
        st.markdown("<div class='section-box'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:14px; font-weight:bold; color:#111; margin-bottom:15px;'>% RALENTÍ POR TIPO DE VEHÍCULO ℹ️</div>", unsafe_allow_html=True)
        
        if "tipo_vehiculo" in dff.columns:
            tipo_df = dff.groupby("tipo_vehiculo").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
            tipo_df["%ralenti"] = np.where(tipo_df["encendido_seg"] > 0, (tipo_df["ralenti_seg"] / tipo_df["encendido_seg"]) * 100, 0)
            tipo_df = tipo_df.sort_values("%ralenti", ascending=False)
            
            for _, row in tipo_df.head(4).iterrows():
                pct = round(row["%ralenti"], 1)
                dev_val = round(pct - META_RALENTI, 1)
                dev_str = f"+{dev_val} p.p." if dev_val >= 0 else f"{dev_val} p.p."
                dev_color = "#d93025" if dev_val > 0 else "#1e7e34"
                bar_color = "#1e7e34" if pct <= META_RALENTI else "#e67e22"
                
                st.markdown(f"""
                    <div style="margin-bottom: 11px; font-size:13px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:3px; font-weight:600;">
                            <span style="color:#333;">{row['tipo_vehiculo']}</span>
                            <span style="color:#111;">{pct}% <span style="color:{dev_color}; font-size:11px; margin-left:5px;">{dev_str}</span></span>
                        </div>
                        <div style="background-color:#edf2f7; border-radius:4px; height:8px; width:100%;">
                            <div style="background-color:{bar_color}; width:{min(pct, 100)}%; height:8px; border-radius:4px;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Métrica no disponible.")
        st.markdown("<a href='#' class='footer-link'>Ver detalle por tipo de vehículo ></a></div>", unsafe_allow_html=True)

    # --- SECCIÓN 3: TABLA TOP 5 ---
    with mid_col3:
        st.markdown("<div class='section-box'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:14px; font-weight:bold; color:#111; margin-bottom:10px;'>TOP 5 (POR % RALENTÍ)</div>", unsafe_allow_html=True)
        
        top = dff.groupby("nombre_dispositivo").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
        top["%ralenti"] = np.where(top["encendido_seg"] > 0, (top["ralenti_seg"] / top["encendido_seg"]) * 100, 0)
        top["Horas Ralentí"] = round(top["ralenti_seg"] / 3600, 1)
        top["Horas Operativas"] = round(top["encendido_seg"] / 3600, 1)
        
        eventos_map = dff.groupby("nombre_dispositivo").size().to_dict()
        top["Eventos"] = top["nombre_dispositivo"].map(eventos_map)
        
        top = top.sort_values("%ralenti", ascending=False).head(5)
        
        tabla_html = """<table style='width:100%; border-collapse: collapse; font-size:12px; text-align:left;'>
            <tr style='border-bottom: 2px solid #edf2f7; color:#555; font-weight:bold;'>
                <th style='padding:6px;'>#</th><th style='padding:6px;'>Placa</th>
                <th style='padding:6px;'>% Ralentí</th><th style='padding:6px;'>Horas en Ralentí</th>
                <th style='padding:6px;'>Horas Operativas</th><th style='padding:6px;'>Eventos</th>
            </tr>"""
        
        for idx, (_, row) in enumerate(top.iterrows(), 1):
            tabla_html += f"""<tr style='border-bottom: 1px solid #edf2f7; font-weight:600; color:#333;'>
                <td style='padding:7px;'>{idx}</td><td style='padding:7px; color:#1e7e34;'>{row['nombre_dispositivo']}</td>
                <td style='padding:7px; color:#d93025;'>{round(row['%ralenti'], 1)}%</td><td style='padding:7px;'>{row['Horas Ralentí']} h</td>
                <td style='padding:7px;'>{row['Horas Operativas']} h</td><td style='padding:7px;'>{row['Eventos']}</td>
            </tr>"""
        tabla_html += "</table>"
        
        st.markdown(tabla_html, unsafe_allow_html=True)
        st.markdown("<a href='#' class='footer-link'>Ver top completo ></a></div>", unsafe_allow_html=True)

    # =====================================================
    # EVOLUCIÓN GRÁFICA INFERIOR
    # =====================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:14px; font-weight:bold; color:#111; margin-left:5px; margin-bottom:5px;'>EVOLUCIÓN DEL % RALENTÍ ℹ️</div>", unsafe_allow_html=True)
    
    evo = dff.groupby("fecha").agg({"ralenti_seg": "sum", "encendido_seg": "sum"}).reset_index()
    evo["%ralenti"] = np.where(evo["encendido_seg"] > 0, (evo["ralenti_seg"] / evo["encendido_seg"]) * 100, 0)
    evo["%ralenti"] = round(evo["%ralenti"], 1)
    evo["fecha_str"] = evo["fecha"].dt.strftime('%d/%m')

    fig = px.line(
        evo, x="fecha_str", y="%ralenti", markers=True,
        text="%ralenti"
    )
    
    fig.update_traces(
        line_color="#1e7e34", line_width=2.5, marker=dict(size=7, color="#1e7e34"),
        textposition="top center", texttemplate="%{text}%"
    )
    
    fig.add_hline(y=META_RALENTI, line_dash="dash", line_color="#e67e22", line_width=1.5)
    
    fig.update_layout(
        xaxis_title="", yaxis_title="",
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=25, b=10), height=260,
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', range=[0, max(evo["%ralenti"].max() + 5, 20)])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("<div style='margin-top:-10px; margin-left:5px;'><a href='#' class='footer-link'>Ver análisis detallado ></a></div>", unsafe_allow_html=True)

# =====================================================
# PIE DE PÁGINA
# =====================================================
st.markdown("<hr style='border:0; border-top:1px solid #ddd; margin-top:30px;'>", unsafe_allow_html=True)
st.markdown("<p style='font-size:12px; color:#555;'>ℹ️ Los tiempos de ralentí consideran motor encendido y velocidad = 0 km/h.</p>", unsafe_allow_html=True)