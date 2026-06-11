# =====================================================
# TOP 5 VEHÍCULOS
# =====================================================

top = (
    dff.groupby("nombre_dispositivo")
    .agg(
        horas_ralenti=("ralenti_seg", "sum"),
        horas_operativas=("encendido_seg", "sum")
    )
    .reset_index()
)

top["%ralenti"] = (
    top["horas_ralenti"]
    /
    top["horas_operativas"]
    * 100
)

top["horas_ralenti"] = (
    top["horas_ralenti"] / 3600
).round(1)

top["horas_operativas"] = (
    top["horas_operativas"] / 3600
).round(1)

top = (
    top.sort_values(
        "%ralenti",
        ascending=False
    )
    .head(5)
)

top = top[
    [
        "nombre_dispositivo",
        "%ralenti",
        "horas_ralenti",
        "horas_operativas"
    ]
]

st.subheader("🏆 TOP 5 VEHÍCULOS")

st.dataframe(
    top.rename(
        columns={
            "nombre_dispositivo": "Vehículo",
            "%ralenti": "% Ralentí",
            "horas_ralenti": "Horas en Ralentí",
            "horas_operativas": "Horas Operativas"
        }
    ),
    use_container_width=True,
    hide_index=True
)