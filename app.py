import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime

# ===============================
# Налаштування сторінки
# ===============================
st.set_page_config(
    page_title="Хімічна обстановка",
    layout="wide"
)

st.title("🧪 Карта хімічної обстановки")

# ===============================
# Стан застосунку
# ===============================
if "data" not in st.session_state:
    st.session_state.data = []

# ===============================
# Форма введення даних
# ===============================
with st.sidebar:
    st.header("➕ Додати точку вимірювання")

    substance = st.text_input(
        "Назва небезпечної речовини",
        value="Хлор"
    )

    lat = st.number_input(
        "Широта (lat)",
        format="%.6f",
        value=50.4501
    )

    lon = st.number_input(
        "Довгота (lon)",
        format="%.6f",
        value=30.5234
    )

    concentration = st.number_input(
        "Концентрація, мг/м³",
        min_value=0.0,
        format="%.3f"
    )

    time_meas = st.text_input(
        "Час вимірювання",
        value=datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    if st.button("➕ Додати точку"):
        st.session_state.data.append({
            "substance": substance,
            "lat": lat,
            "lon": lon,
            "concentration": concentration,
            "time": time_meas
        })
        st.success("Точку додано")

    if st.button("🧹 Очистити всі точки"):
        st.session_state.data = []
        st.warning("Дані очищено")

# ===============================
# Побудова карти
# ===============================
def build_map(data):
    if not data:
        return folium.Map(location=[50.45, 30.52], zoom_start=6)

    df = pd.DataFrame(data)

    m = folium.Map(
        location=[df.lat.mean(), df.lon.mean()],
        zoom_start=13,
        control_scale=True
    )

    fg = folium.FeatureGroup(name="Точки вимірювання")

    for _, r in df.iterrows():
        # Кольори (простий приклад)
        color = "green"
        if r.concentration >= 1:
            color = "red"
        elif r.concentration >= 0.5:
            color = "orange"

        # Маркер точки
        folium.CircleMarker(
            location=[r.lat, r.lon],
            radius=7,
            color="black",
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.8
        ).add_to(fg)

        # Підпис біля точки
        folium.Marker(
            location=[r.lat, r.lon],
            icon=folium.features.DivIcon(
                icon_size=(260, 60),
                icon_anchor=(0, 0),
                html=f"""
                <div style="
                    background: transparent;
                    font-size: 12px;
                    font-weight: bold;
                    color: black;
                    white-space: nowrap;
                ">
                    {r.substance} – {r.concentration} мг/м³
                    <div style="
                        font-size: 10px;
                        text-decoration: underline;
                        margin-top: 2px;
                    ">
                        {r.time}
                    </div>
                </div>
                """
            )
        ).add_to(fg)

    fg.add_to(m)

    # LayerControl + фікс видимості
    folium.LayerControl(collapsed=False).add_to(m)

    fix_css = """
    <style>
    .leaflet-control-layers {
        z-index: 9999 !important;
        background: white;
    }
    </style>
    """
    m.get_root().header.add_child(folium.Element(fix_css))

    return m

# ===============================
# Відображення карти
# ===============================
st.subheader("🗺️ Карта")

map_obj = build_map(st.session_state.data)
st_folium(map_obj, width=1200, height=700)

# ===============================
# Таблиця даних (опційно)
# ===============================
if st.session_state.data:
    st.subheader("📋 Вхідні дані")
    st.dataframe(pd.DataFrame(st.session_state.data), use_container_width=True)

