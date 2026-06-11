# 3. Columna Ranking Tabla
with mid_col3:

    top_df = (
        dff.groupby("nombre_dispositivo")
        .agg({
            "ralenti_seg": "sum",
            "encendido_seg": "sum"
        })
        .reset_index()
    )

    top = top_df.copy()

    top["%ralenti"] = np.where(
        top["encendido_seg"] > 0,
        (top["ralenti_seg"] / top["encendido_seg"]) * 100,
        0
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

    html_top = """
    <div class='section-box'>
        <div style='font-size:14px;
                    font-weight:bold;
                    color:#111;
                    margin-bottom:10px;'>
            TOP 5 (POR % RALENTÍ)
        </div>

        <table style='width:100%;
                      border-collapse: collapse;
                      font-size:12px;
                      text-align:left;'>

            <tr style='border-bottom: 2px solid #edf2f7;
                       color:#555;
                       font-weight:bold;'>

                <th style='padding:6px;'>#</th>
                <th style='padding:6px;'>Placa</th>
                <th style='padding:6px;'>% Ralentí</th>
                <th style='padding:6px;'>Horas en Ralentí</th>
                <th style='padding:6px;'>Horas Operativas</th>

            </tr>
    """

    for idx, (_, row) in enumerate(top.iterrows(), 1):

        html_top += f"""
        <tr style='border-bottom:1px solid #edf2f7;
                   font-weight:600;
                   color:#333;'>

            <td style='padding:7px;'>{idx}</td>

            <td style='padding:7px;
                       color:#1e7e34;'>
                {row['nombre_dispositivo']}
            </td>

            <td style='padding:7px;
                       color:#d93025;'>
                {row['%ralenti']:.1f}%
            </td>

            <td style='padding:7px;'>
                {row['Horas Ralentí']} h
            </td>

            <td style='padding:7px;'>
                {row['Horas Operativas']} h
            </td>

        </tr>
        """

    html_top += "</table></div>"

    st.markdown(
        html_top,
        unsafe_allow_html=True
    )