import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from fpdf import FPDF

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
# СТАН
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(
        columns=["lat", "lon", "value", "time"]
    )

if "substance" not in st.session_state:
    st.session_state.substance = "Хлор"

# ===============================
# GUI
# ===============================
st.title("🧪 Карта хімічної обстановки")

col_map, col_gui = st.columns([2.2, 1])

# ===============================
# ПРАВА ПАНЕЛЬ — КЕРУВАННЯ
# ===============================
with col_gui:
    st.subheader("⚙️ Ввід даних")

    st.session_state.substance = st.text_input(
        "Назва небезпечної речовини",
        st.session_state.substance
    )

    # --------- РУЧНИЙ ВВІД ----------
    st.markdown("### ✍️ Додати точку вручну")

    lat = st.number_input("Широта (lat)", format="%.6f")
    lon = st.number_input("Довгота (lon)", format="%.6f")
    value = st.number_input(
        "Концентрація (мг/куб.м)",
        min_value=0.0,
        step=0.01
    )
    time = st.text_input(
        "Час вимірювання",
        placeholder="2026-01-09 12:30"
    )

    if st.button("➕ Додати точку"):
        new_row = {
            "lat": lat,
            "lon": lon,
            "value": value,
            "time": time
        }
        st.session_state.data = pd.concat(
            [st.session_state.data, pd.DataFrame([new_row])],
            ignore_index=True
        )

    st.divider()

    # --------- CSV ----------
    uploaded = st.file_uploader(
        "📂 Завантажити CSV",
        type=["csv"]
    )

    if uploaded:
        df = pd.read_csv(uploaded)
        st.session_state.data = df
        st.success(f"Завантажено {len(df)} точок")

    if st.button("🧹 Очистити всі дані"):
        st.session_state.data = st.session_state.data.iloc[0:0]

    st.divider()

# ===============================
# КАРТА
# ===============================
with col_map:
    if st.session_state.data.empty:
        st.info("Немає даних для відображення")
    else:
        df = st.session_state.data.copy()

        m = folium.Map(
            location=[df.lat.mean(), df.lon.mean()],
            zoom_start=13
        )

        for _, r in df.iterrows():
            # 🟤 КОРИЧНЕВИЙ ТЕКСТ + МАРКЕР
            label_html = f"""
            <div style="
                color: brown;
                font-size: 13px;
                font-weight: bold;
                white-space: nowrap;
                background-color: rgba(255,255,255,0.0);
            ">
                {st.session_state.substance} – {r['value']} мг/куб.м
                <hr style="margin:2px 0;border:1px solid brown;">
                {r['time']}
            </div>
            """

            # КОРИЧНЕВА ТОЧКА
            folium.CircleMarker(
                [r.lat, r.lon],
                radius=6,
                color="brown",
                fill=True,
                fill_color="brown",
                fill_opacity=0.9
            ).add_to(m)

            # ПІДПИС ПОРУЧ
            folium.Marker(
                [r.lat, r.lon],
                icon=folium.DivIcon(
                    icon_anchor=(0, -10),
                    html=label_html
                )
            ).add_to(m)

        st_folium(m, width=900, height=600, key="map")

        # ===============================
        # ЕКСПОРТ
        # ===============================
        def export_html(map_obj):
            map_obj.save("chemical_map.html")
            with open("chemical_map.html", "rb") as f:
                st.download_button(
                    "💾 Завантажити HTML",
                    f,
                    file_name="chemical_map.html",
                    mime="text/html"
                )

        def export_pdf(df):
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font("DejaVu", "", fname=None, uni=True)
            pdf.set_font("DejaVu", "", 12)

            pdf.cell(0, 10, "Карта хімічної обстановки", ln=True)
            pdf.ln(5)

            for _, r in df.iterrows():
                text = (
                    f"{st.session_state.substance} – "
                    f"{r['value']} мг/куб.м\n"
                    f"{r['time']}"
                )
                pdf.multi_cell(0, 8, text)
                pdf.ln(2)

            pdf.output("chemical_map.pdf")

            with open("chemical_map.pdf", "rb") as f:
                st.download_button(
                    "📄 Завантажити PDF",
                    f,
                    file_name="chemical_map.pdf",
                    mime="application/pdf"
                )

        export_html(m)
        export_pdf(df)

