import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from fpdf import FPDF
from datetime import datetime
import io

# ===============================
# Налаштування сторінки
# ===============================
st.set_page_config(
    page_title="Chemical Situation Map",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ===============================
# Стан
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame()

if "substance" not in st.session_state:
    st.session_state.substance = "Хлор"

# ===============================
# GUI
# ===============================
st.title("🧪 Карта хімічної обстановки")

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("⚙️ Ввід даних")

    st.session_state.substance = st.text_input(
        "Назва небезпечної речовини",
        value=st.session_state.substance
    )

    uploaded_file = st.file_uploader(
        "Завантажити CSV (lat, lon, value, time)",
        type=["csv"]
    )

    if uploaded_file:
        st.session_state.data = pd.read_csv(uploaded_file)
        st.success(f"Завантажено {len(st.session_state.data)} точок")

    if st.button("🧹 Очистити дані"):
        st.session_state.data = pd.DataFrame()

    st.divider()

    if not st.session_state.data.empty:
        # ---------- HTML ----------
        def export_html(map_obj):
            map_obj.save("chemical_map.html")
            with open("chemical_map.html", "rb") as f:
                st.download_button(
                    "💾 Завантажити HTML",
                    f,
                    file_name="chemical_map.html",
                    mime="text/html"
                )

        # ---------- PDF ----------
        def export_pdf(df):
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font("DejaVu", "", fname=None, uni=True)
            pdf.set_font("DejaVu", "", 12)

            pdf.cell(0, 10, "Карта хімічної обстановки", ln=True)
            pdf.ln(5)

            for _, r in df.iterrows():
                line = (
                    f"{st.session_state.substance} – "
                    f"{r['value']} мг/куб.м\n"
                    f"Дата: {r['time']}"
                )
                pdf.multi_cell(0, 8, line)
                pdf.ln(1)

            pdf.output("chemical_map.pdf")

            with open("chemical_map.pdf", "rb") as f:
                st.download_button(
                    "📄 Завантажити PDF",
                    f,
                    file_name="chemical_map.pdf",
                    mime="application/pdf"
                )

# ===============================
# Карта
# ===============================
with col1:
    if st.session_state.data.empty:
        st.info("Завантажте CSV для відображення карти")
    else:
        df = st.session_state.data.copy()

        m = folium.Map(
            location=[df.lat.mean(), df.lon.mean()],
            zoom_start=13
        )

        for _, r in df.iterrows():
            label_html = f"""
            <div style="
                background: rgba(255,255,255,0.0);
                font-size: 12px;
                white-space: nowrap;">
                <b>{st.session_state.substance} – {r['value']} мг/куб.м</b><br>
                <u>{r['time']}</u>
            </div>
            """

            folium.Marker(
                [r.lat, r.lon],
                icon=folium.DivIcon(
                    html=label_html
                )
            ).add_to(m)

        # Карта НЕ мигає, бо ключ фіксований
        st_folium(m, width=900, height=600, key="map")

        # Кнопки експорту
        export_html(m)
        export_pdf(df)

