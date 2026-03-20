import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
from datetime import datetime

# ===============================
# 1. КОНФІГУРАЦІЯ ТА СТИЛІ
# ===============================
st.set_page_config(page_title="КАРТА ХІМІЧНОЇ ОБСТАНОВКИ", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stButton button {font-weight: bold; background-color: #ffcc00 !important; color: black !important; width: 100%;}
.stNumberInput input {font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ===============================
# 2. SESSION STATE (ЗБЕРЕЖЕННЯ ДАНИХ)
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

if "manual_lat" not in st.session_state: st.session_state.manual_lat = 48.3794
if "manual_lon" not in st.session_state: st.session_state.manual_lon = 31.1656

# НОВЕ: Список для зберігання нарисованих об'єктів (щоб не зникали)
if "drawn_items" not in st.session_state:
    st.session_state.drawn_items = []

# ===============================
# 3. ДОПОМІЖНІ ФУНКЦІЇ
# ===============================
def marker_html(main, sub):
    return f"""
    <div style="display: inline-block; font-family: Arial; font-size: 10pt; color: blue; font-weight: bold; text-align: center; white-space: nowrap; text-shadow: 2px 2px 2px #fff;">
        <div style="border-bottom: 2px solid blue; padding-bottom: 2px; margin-bottom: 2px;">{main}</div>
        <div style="font-weight: normal;">{sub}</div>
    </div>
    """

# Стилі для інструментів малювання
draw_style = {'color': 'black', 'fillColor': 'yellow', 'fillOpacity': 0.5, 'weight': 2}

# ===============================
# 4. СТВОРЕННЯ КАРТИ
# ===============================
def create_map(df, lat, lon, zoom):
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None, control_scale=True)
    
    folium.TileLayer('OpenStreetMap', name='Карта', show=True).add_to(m)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite', name='Супутник', show=False
    ).add_to(m)

    # 1. Відображення збережених нарисованих об'єктів
    for item in st.session_state.drawn_items:
        folium.GeoJson(item, style_function=lambda x: draw_style).add_to(m)

    # 2. Маркер кліку (Червоний)
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    # 3. Офіційні точки з таблиці
    if not df.empty:
        for _, r in df.iterrows():
            main_txt = f"{r['substance']} {r['value']} {r['unit']}"
            folium.CircleMarker(
                [r.lat, r.lon], radius=6, color="orange", fill=True, fill_color="orange", fill_opacity=1
            ).add_to(m)
            folium.Marker(
                [r.lat, r.lon],
                icon=folium.DivIcon(icon_anchor=(80, 45), html=marker_html(main_txt, r['time']))
            ).add_to(m)

    # 4. Налаштування панелі малювання (ВИПРАВЛЕНО КОЛЬОРИ ТА ТИПИ)
    draw_plugin = Draw(
        export=False,
        draw_options={
            'polyline': {'shapeOptions': {'color': 'black', 'weight': 3}},
            'polygon': {'shapeOptions': draw_style},
            'rectangle': {'shapeOptions': draw_style},
            'circle': {'shapeOptions': draw_style},
            'marker': True,
            'circlemarker': False # Вимкнено, щоб не плутати з колом
        },
        edit_options={'edit': True, 'remove': True}
    )
    draw_plugin.add_to(m)

    return m

# ===============================
# 5. ІНТЕРФЕЙС
# ===============================
st.header("1.5. КАРТА ФАКТИЧНОЇ ХІМІЧНОЇ ОБСТАНОВКИ")

col_map, col_panel = st.columns([3, 1])

with col_panel:
    st.subheader("ПУЛЬТ УПРАВЛІННЯ")

    # ЛОГІКА КЛІКУ
    if st.session_state.clicked_coords:
        c_lat = st.session_state.clicked_coords['lat']
        c_lon = st.session_state.clicked_coords['lng']
        st.success(f"Координати: {c_lat:.6f}, {c_lon:.6f}")
        
        if st.button("ЗАВАНТАЖИТИ КООРДИНАТИ"):
            st.session_state.manual_lat = c_lat
            st.session_state.manual_lon = c_lon
            st.rerun()
            
        if st.button("ВИКЛЮЧИТИ МАРКЕР"):
            st.session_state.clicked_coords = None
            st.rerun()
    else:
        st.info("Клікніть на карті для вибору точки")

    st.divider()

    # ФОРМА ВВОДУ
    in_lat = st.number_input("Широта", format="%.6f", value=st.session_state.manual_lat)
    in_lon = st.number_input("Довгота", format="%.6f", value=st.session_state.manual_lon)
    substance = st.text_input("Речовина", "Хлор")
    value = st.number_input("Значення", format="%.2f")
    unit = st.selectbox("Одиниця", ["мг/м³","ppm"])
    time_val = st.date_input("Дата", value=datetime.now()).strftime("%d.%m.%Y")

    if st.button("НАНЕСТИ НА КАРТУ"):
        new = pd.DataFrame([{"lat": in_lat, "lon": in_lon, "substance": substance, "value": value, "unit": unit, "time": time_val}])
        st.session_state.data = pd.concat([st.session_state.data, new], ignore_index=True)
        st.rerun()

    st.divider()
    if st.button("🗑️ ОЧИСТИТИ ВСЕ (МАЛЮНКИ + ТАБЛИЦЯ)"):
        st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
        st.session_state.drawn_items = []
        st.session_state.clicked_coords = None
        st.rerun()

# -------- ВІДОБРАЖЕННЯ КАРТИ --------
with col_map:
    # Центрування
    if st.session_state.data.empty:
        start_lat, start_lon, zoom = 48.3794, 31.1656, 6
    else:
        start_lat, start_lon, zoom = st.session_state.data.lat.iloc[-1], st.session_state.data.lon.iloc[-1], 10

    m = create_map(st.session_state.data, start_lat, start_lon, zoom)

    # Виклик компонента карти
    map_output = st_folium(
        m,
        width="100%",
        height=700,
        key="chem_map_v4",
        returned_objects=["last_clicked", "all_drawings"]
    )

    # ОБРОБКА МАЛЮНКІВ (збереження в пам'ять)
    if map_output.get("all_drawings"):
        # Якщо кількість нарисованих об'єктів змінилася, оновлюємо сесію
        if map_output["all_drawings"] != st.session_state.drawn_items:
            st.session_state.drawn_items = map_output["all_drawings"]
            st.rerun()

    # ОБРОБКА КЛІКУ
    if map_output.get("last_clicked"):
        clicked = map_output["last_clicked"]
        if st.session_state.clicked_coords != clicked:
            st.session_state.clicked_coords = clicked
            st.rerun()

# -------- ТАБЛИЦЯ --------
if not st.session_state.data.empty:
    st.dataframe(st.session_state.data, use_container_width=True)
