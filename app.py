import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# ===============================
# 1. Налаштування сторінки
# ===============================
st.set_page_config(page_title="Chemical Map Pro", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stButton button {font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ===============================
# 2. Стан програми
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# ===============================
# 3. Заголовок
# ===============================
st.title("Карта хімічної обстановки")
col_map, col_gui = st.columns([2.5, 1])

# ===============================
# 4. Пульт управління
# ===============================
with col_gui:
    st.subheader("Пульт управління")

    if st.session_state.clicked_coords:
        c_lat = st.session_state.clicked_coords['lat']
        c_lon = st.session_state.clicked_coords['lng']
        st.write(f"Вибрано: {c_lat:.6f}, {c_lon:.6f}")

        r1, r2 = st.columns(2)

        if r1.button("вставити координати у форму", use_container_width=True):
            st.session_state.manual_lat = c_lat
            st.session_state.manual_lon = c_lon
            st.rerun()

        if r2.button("виключити маркер на карті", use_container_width=True):
            st.session_state.clicked_coords = None
            st.rerun()

    st.divider()

    st.markdown("### Нанесення точки вручну")
    with st.container(border=True):
        substance = st.text_input("Назва речовини", placeholder="Хлор")

        v_lat = st.number_input("Широта", format="%.6f",
                                value=st.session_state.get('manual_lat', 50.4501))
        v_lon = st.number_input("Довгота", format="%.6f",
                                value=st.session_state.get('manual_lon', 30.5234))

        concentration = st.number_input("Концентрація (мг/м³)", format="%.4f", step=0.001)

        date_input = st.text_input("Дата", value=datetime.now().strftime("%d.%m.%Y"))

        if st.button("Нанести", use_container_width=True):
            new_entry = pd.DataFrame([{
                "lat": v_lat,
                "lon": v_lon,
                "substance": substance,
                "value": concentration,
                "time": date_input
            }])

            st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
            st.rerun()

    st.divider()

    st.markdown("### Завантаження CSV")
    uploaded_file = st.file_uploader("CSV файл", type="csv", label_visibility="collapsed")

    if uploaded_file and st.button("Завантажити", use_container_width=True):
        try:
            df_new = pd.read_csv(uploaded_file)
            st.session_state.data = pd.concat([st.session_state.data, df_new], ignore_index=True)
            st.rerun()
        except:
            st.error("Помилка файлу")

    if st.button("Очистити карту", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.session_state.clicked_coords = None
        st.rerun()

# ===============================
# 5. Карта
# ===============================
with col_map:

    if not st.session_state.data.empty:
        center = [st.session_state.data.lat.iloc[-1], st.session_state.data.lon.iloc[-1]]
    else:
        center = [50.4501, 30.5234]

    m = folium.Map(location=center, zoom_start=10, tiles=None, control_scale=True)

    # Основна карта (за замовчуванням)
    folium.TileLayer(
        'OpenStreetMap',
        name='Стандартна карта',
        overlay=False,
        control=True,
        show=True
    ).add_to(m)

    # Супутник (опціонально)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Супутник',
        overlay=False,
        control=True,
        show=False
    ).add_to(m)

    # Клік по карті
    if st.session_state.clicked_coords:
        folium.Marker(
            [
                st.session_state.clicked_coords['lat'],
                st.session_state.clicked_coords['lng']
            ],
            icon=folium.Icon(color="red")
        ).add_to(m)

    # Точки
    if not st.session_state.data.empty:
        df = st.session_state.data.copy()

        for d in df['time'].unique():
            group = folium.FeatureGroup(name=f"Дата: {d}")
            day_data = df[df['time'] == d]

            for _, r in day_data.iterrows():
                val_f = f"{r['value']:.4f}".rstrip('0').rstrip('.')

                label_html = f"""
<div style="
    display: inline-block;
    font-family: Arial;
    font-size: 10pt;
    color: blue;
    font-weight: bold;
    text-align: center;
    background-color: transparent;
    padding: 2px 4px;
    text-shadow:
        -1px -1px 0 #fff,
         1px -1px 0 #fff,
        -1px  1px 0 #fff,
         1px  1px 0 #fff,
         2px 2px 3px rgba(255,255,255,0.8);
">
    <div style="
        display: inline-block;
        border-bottom: 2px solid blue;
        padding-bottom: 2px;
        margin-bottom: 2px;
        white-space: nowrap;
    ">
        {r['substance']} — {val_f} мг/м³
    </div>
    <div>{r['time']}</div>
</div>
"""

                folium.CircleMarker(
                    [r.lat, r.lon],
                    radius=6,
                    color="blue",
                    fill=True
                ).add_to(group)

                folium.Marker(
                    [r.lat, r.lon],
                    icon=folium.DivIcon(
                        icon_anchor=(70, 45),
                        html=label_html
                    )
                ).add_to(group)

            group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    map_output = st_folium(m, width="100%", height=700, key="main_map")

    # Безпечний обробник кліку
    if map_output and map_output.get("last_clicked"):
        if st.session_state.clicked_coords != map_output["last_clicked"]:
            st.session_state.clicked_coords = map_output["last_clicked"]
            st.rerun()

# ===============================
# 6. Таблиця + експорт
# ===============================
st.divider()

if not st.session_state.data.empty:
    edited_df = st.data_editor(
        st.session_state.data,
        use_container_width=True,
        num_rows="dynamic"
    )

    if not edited_df.equals(st.session_state.data):
        st.session_state.data = edited_df
        st.rerun()

    c1, c2 = st.columns(2)

    c1.download_button(
        "Завантажити карту HTML",
        m._repr_html_(),
        "map.html",
        "text/html",
        use_container_width=True
    )

    c2.download_button(
        "Зберегти CSV",
        st.session_state.data.to_csv(index=False),
        "data.csv",
        "text/csv",
        use_container_width=True
    )
