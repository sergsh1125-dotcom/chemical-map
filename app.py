import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ===============================
# Налаштування сторінки (ВАЖЛИВО)
# ===============================
st.set_page_config(
    page_title="Chemical Situation Map",
    layout="wide"
)

# Приховуємо службові елементи Streamlit
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Мобільна адаптація */
@media (max-width: 768px) {
    .block-container {
        padding: 0.5rem;
    }
}
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
# ЗАГОЛОВОК
# ===============================
st.title("🧪 Хімічна обстановка")

# ===============================
# МОБІЛЬНИЙ GUI (ЗГОРТАННЯ)
# ===============================
with st.expander("⚙️ Ввід даних / Data input", expanded=False):

    st.session_state.substance = st.text_input(
        "Назва небезпечної речовини",
        st.session_state.substance
    )

    st.markdown("### ➕ Додати точку")

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

    if st.button("➕ Додати точку", use_container_width=True):
        st.session_state.data = pd.concat(
            [
                st.session_state.data,
                pd.DataFrame([{
                    "lat": lat,
                    "lon": lon,
                    "value": value,
                    "time": time
                }])
            ],
            ignore_index=True
        )

    st.divider()

    uploaded = st.file_uploader(
        "📂 Завантажити CSV",
        type=["csv"]
    )

    if uploaded:
        st.session_state.data = pd.read_csv(uploaded)
        st.success(f"Завантажено {len(st.session_state.data)} точок")

    if st.button("🧹 Очистити всі дані", use_container_width=True):
        st.session_state.data = st.session_state.data.iloc[0:0]

# ===============================
# КАРТА (НА ВСЮ ШИРИНУ)
# ===============================
if st.session_state.data.empty:
    st.info("Немає даних для відображення")
else:
    df = st.session_state.data.copy()

    m = folium.Map(
        location=[df.lat.mean(), df.lon.mean()],
        zoom_start=13,
        control_scale=True
    )

    for _, r in df.iterrows():
        label_html = f"""
        <div style="
            color: brown;
            font-size: 14px;
            font-weight: bold;
            white-space: nowrap;
        ">
            {st.session_state.substance} – {r['value']} мг/куб.м
            <hr style="margin:2px 0;border:1px solid brown;">
            {r['time']}
        </div>
        """

        folium.CircleMarker(
            [r.lat, r.lon],
            radius=7,
            color="brown",
            fill=True,
            fill_color="brown",
            fill_opacity=0.9
        ).add_to(m)

        folium.Marker(
            [r.lat, r.lon],
            icon=folium.DivIcon(
                icon_anchor=(0, -12),
                html=label_html
            )
        ).add_to(m)

    # width=None → автоадаптація під екран
    st_folium(
        m,
        width=None,
        height=500,
        key="mobile_map"
    )

    # ===============================
    # HTML ЕКСПОРТ
    # ===============================
    m.save("chemical_map.html")
    with open("chemical_map.html", "rb") as f:
        st.download_button(
            "💾 Завантажити карту (HTML)",
            f,
            file_name="chemical_map.html",
            mime="text/html",
            use_container_width=True
        )

