import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(layout="wide")

# --- MAIN DASHBOARD CONTENT (Skip omitted header, title, and profile sections) ---
# Start directly with content, effectively omitting everything in the visual header.

with st.container():
    # Visual separation signifies the start of the dashboard content
    st.write("---")

    # --- KPI CARD ROW ---
    # Create fictional numerical and text data for metrics
    data_kpi = {
        'ralenti_actual': 20.84,
        'ralenti_meta': 10.0,
        'critico_threshold': 15.0,
        'fuera_meta_val': 28.0,
        'fuera_meta_num_vehicles': 34,
        'fuera_meta_total_vehicles': 120,
        'fuera_meta_meta_vehicles': 10,
        'vs_last_month_change_pp': "+3.24 p.p.",
        'vs_last_month_current_val': 20.84,
        'vs_last_month_previous_val': 17.60
    }

    # Render key performance indicators (KPIs) in three columns
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

    # Key Indicator 1: "% RALENTÍ ACTUAL"
    kpi_col1.markdown(f"""
        <div style="background-color:#ffe6e6; padding:20px; border-radius:10px; height:100%; border:1px solid #ddd;">
            <div style="font-size:16px; color:#555;">% RALENTÍ ACTUAL</div>
            <div style="font-size:40px; color:#d63031; font-weight:bold;">{data_kpi['ralenti_actual']}%</div>
            <div style="font-size:14px; color:#555;">Meta: {data_kpi['ralenti_meta']}%</div>
            <div style="background-color:#d63031; color:white; padding:5px 10px; border-radius:5px; display:inline-block; margin-top:10px; font-weight:bold;">⚠️ CRÍTICO (> {data_kpi['critico_threshold']}%)</div>
        </div>
    """, unsafe_allow_html=True)

    # Key Indicator 2: "FUERA DE META"
    kpi_col2.markdown(f"""
        <div style="background-color:#fff; padding:20px; border-radius:10px; height:100%; border:1px solid #ddd; display:flex;">
            <div style="width:30%; display:flex; align-items:center; justify-content:center;">
                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#d63031" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
            </div>
            <div style="width:70%; text-align:right;">
                <div style="font-size:40px; color:#d63031; font-weight:bold;">{data_kpi['fuera_meta_val']}%</div>
                <div style="font-size:16px; color:#555;">FUERA DE META</div>
                <div style="font-size:14px; color:#555; margin-top:10px;">{data_kpi['fuera_meta_num_vehicles']} de {data_kpi['fuera_meta_total_vehicles']} vehículos</div>
                <div style="font-size:14px; color:#555;">Meta: ≤ {data_kpi['fuera_meta_meta_vehicles']}%</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Key Indicator 3: "VS. MES ANTERIOR"
    kpi_col3.markdown(f"""
        <div style="background-color:#fff; padding:20px; border-radius:10px; height:100%; border:1px solid #ddd; display:flex;">
            <div style="width:30%; display:flex; align-items:center; justify-content:center;">
                <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#2ecc71" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
                 </svg>
            </div>
            <div style="width:70%; text-align:right;">
                <div style="font-size:40px; color:#d63031; font-weight:bold;">{data_kpi['vs_last_month_change_pp']}</div>
                <div style="font-size:16px; color:#555;">VS. MES ANTERIOR</div>
                <div style="font-size:14px; color:#555; margin-top:10px;">Anterior: {data_kpi['vs_last_month_previous_val']}% | Actual: {data_kpi['vs_last_month_current_val']}%</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- MIDDLE DATA SECTION ---
    # Create fictional numerical and text data for mid-row tables
    data_grupo = {
        'Grupo': ['Materias Primas', 'Transporte Interno', 'Primera Milla', 'Última Milla'],
        '% Ralentí': [24.0, 21.0, 18.0, 12.0],
        'vs meta (10%)': ['+14.0 p.p.', '+11.0 p.p.', '+8.0 p.p.', '+2.0 p.p.'],
        'color': ['#e17055', '#fab1a0', '#00b894', '#55efc4'],
        'bar_val': [24.0