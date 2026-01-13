import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from branca.element import Element
from fpdf import FPDF
import tempfile
import os

st.set_page_config(layout="wide")
st.title("🧪 Хімічна обстановка")

# -----------------------------
# Ввід параметрів
# -----------------------------
substance = st.text_input("Назва небезпечної хімічної речовини", "Хлор")
uploaded_file = st.file_uploader("Завантажити CSV (lat, lon, value, time)", type="csv")

LEVELS = [
    (0.1, "green", "Фон"),
    (0.3, "yellow", "Підвищена"),
    (1.0, "orange", "Небезпечна"),
    (5.0, "red", "Смертельно небезпечна")
]

def get_color(val):
    for limit, color, _ in LEVELS:
        if val <= limit:
            return color
    return "darkred"

def build_map(df):
    m = folium.Map(location=[df.lat.mean(), df.lon.mean()], zoom_start=14)

    for _, r in df.iterrows():
        folium.CircleMarker(
            [r.lat, r.lon],
            radius=8,
            color="black",
            fill=True,
            fill_color=get_color(r.value),
            fill_opacity=0.85
        ).add_to(m)

        folium.Marker(
            [r.lat, r.lon],
            icon=folium.DivIcon(
                icon_size=(0, 0),
                icon_anchor=(10, -10),
                html=f"""
                <div style="
                    font-size:11px;
                    font-weight:bold;
                    background:transparent;
                    white-space:nowrap;
                    color:black;
                    margin-left:8px;">
                    {substance} - {r.value} мг/м³<br>
                    <hr style="margin:1px 0; border:1px solid gray;">
                    {r.time}
                </div>
                """
            )
        ).add_to(m)

    legend = f"""
    <div style="
        position: fixed;
        bottom: 20px;
        left: 20px;
        background: white;
        border:2px solid grey;
        z-index:9999;
        font-size:13px;
        padding:10px;">
        <b>Хімічна обстановка<br>{substance}</b><br>
    """
    for _, color, label in LEVELS:
        legend += f"<span style='color:{color}'>■</span> {label}<br>"
    legend += "</div>"

    m.get_root().html.add_child(Element(legend))
    return m

# -----------------------------
# Основна логіка
# -----------------------------
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    required = {"lat", "lon", "value", "time"}
    if not required.issubset(df.columns):
        st.error("CSV має містити колонки: lat, lon, value, time")
    else:
        df[['lat', 'lon', 'value']] = df[['lat','lon','value']].apply(pd.to_numeric)
        df = df.dropna()

        m = build_map(df)

        col1, col2 = st.columns([3,1])

        with col1:
            st_folium(m, width=900, height=600)

        with col2:
            st.subheader("Експорт")

            # HTML
            if st.button("💾 Експорт HTML"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                    m.save(tmp.name)
                    st.download_button(
                        "⬇ Завантажити HTML",
                        open(tmp.name, "rb"),
                        file_name="chemical_map.html"
                    )

            # PDF
            if st.button("📄 Експорт PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, f"Хімічна обстановка: {substance}", ln=True)
                pdf.ln(5)
                pdf.set_font("Arial", size=11)

                for _, r in df.iterrows():
                    pdf.cell(0, 8, f"{r.lat}, {r.lon} | {r.value} мг/м³ | {r.time}", ln=True)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    st.download_button(
                        "⬇ Завантажити PDF",
                        open(tmp.name, "rb"),
                        file_name="chemical_map.pdf"
                    )

