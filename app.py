import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
from datetime import datetime

# ===============================
# 1. НАЛАШТУВАННЯ ТА СТИЛІ
# ===============================
st.set_page_config(page_title="Chemical Hazard Map", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu, footer, header, .stDeployButton {visibility: hidden; display: none !important;}
.block-container {padding:1rem !important; max-width:100% !important;}
.stApp {background-color:#0e1117; color:#e0e0e0;}
.main-title {color:#ffcc00 !important; text-align:center !important; font-size:22px !important; font-weight:bold !important; margin-top:-20px !important; text-transform:uppercase !important;}
div[data-testid="stButton"] button {background-color:#ffcc00 !important; color:#000 !important; font-weight:bold !important; width:100%; height: 45px;}
.stNumberInput input {font-weight: bold; font-size: 16px !important;}
.coord-box {background-color: #262730; padding: 10px; border: 1px solid #ffcc00; border-radius: 5px; text-align: center; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">Модуль 1.5. Карта фактичної хімічної обстановки</p>', unsafe_allow_html=True)

# ===============================
# 2. СТАН ПРОГРАМИ (SESSION STATE)
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

if "manual_lat" not in st.session_state: st.session_state.manual_lat = 48.3794
if "manual_lon" not in st.session_state: st.session_state.manual_lon = 31.1656

# ===============================
# 3. ФУНКЦІЇ ВІЗУАЛІЗАЦІЇ
# ===============================
def marker_html(label, time):
    return f"""
    <div style="font-family: Arial; font-size: 11pt; color: blue; font-weight: bold; white-space: nowrap; text-shadow: 1px 1px 2px white;">
        <div style="border-bottom: 2px solid blue;">{label}</div>
        <div style="font-weight: normal; font-size: 9pt;">{time}</div>
    </div>
    """

# ===============================
# 4. ІНТЕРФЕЙС (ПУЛЬТ ТА КАРТА)
# ===============================
col_map, col_gui = st.columns([3, 1])

with col_gui:
    st.subheader("📍 КООРДИНАТИ")
    
    # Вивід поточного кліку
    if st.session_state.clicked_coords:
        lat_c = st.session_state.clicked_coords[0]
        lon_c = st.session_state.clicked_coords[1]
        st.markdown(f'<div class="coord-box"><b>Широта:</b> {lat_c}<br><b>Довгота:</b> {lon_c}</div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("ЗАВАНТАЖИТИ"):
            st.session_state.manual_lat = lat_c
            st.session_state.manual_lon = lon_c
            st.rerun()
        if c2.button("ВИКЛЮЧИТИ"):
            st.session_state.clicked_coords = None
            st.rerun()
    else:
        st.info("Клікніть на карті для вибору")

    st.divider()
    
    st.markdown("### ➕ ДОДАТИ ДАНІ")
    substance = st.text_input("Речовина", value="Хлор")
    in_lat = st.number_input("Широта", format="%.6f", value=float(st.session_state.manual_lat))
    in_lon = st.number_input("Довгота", format="%.6f", value=float(st.session_state.manual_lon))
    value = st.number_input("Значення", format="%.4f")
    time_now = st.text_input("Дата/Час", value=datetime.now().strftime("%d.%m.%Y %H:%M"))

    if st.button("НАНЕСТИ НА КАРТУ"):
        new_point = pd.DataFrame([{"lat": in_lat, "lon": in_lon, "substance": substance, "value": value, "time": time_now}])
        st.session_state.data = pd.concat([st.session_state.data, new_point], ignore_index=True)
        st.rerun()

    if st.button("🧹 ОЧИСТИТИ ТАБЛИЦЮ"):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.rerun()

with col_map:
    # Створення карти
    m = folium.Map(location=[st.session_state.manual_lat, st.session_state.manual_lon], zoom_start=7, tiles="OpenStreetMap")
    
    # 1. Синій маркер ВИЗНАЧЕННЯ КООРДИНАТ (тільки якщо є клік)
    if st.session_state.clicked_coords:
        folium.Marker(
            st.session_state.clicked_coords,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    # 2. Офіційні точки з таблиці
    for _, r in st.session_state.data.iterrows():
        folium.CircleMarker(
            [r.lat, r.lon], radius=7, color="blue", fill=True, fill_color="blue", fill_opacity=0.8
        ).add_to(m)
        folium.Marker(
            [r.lat, r.lon],
            icon=folium.DivIcon(icon_anchor=(-15, 7), html=marker_html(f"{r.substance}: {r.value}", r.time))
        ).add_to(m)

    # 3. СТАНДАРТНА ПАНЕЛЬ МАЛЮВАННЯ (Жовтий/Чорний)
    draw_options = {
        'polyline': {'shapeOptions': {'color': 'black', 'weight': 3}},
        'polygon': {'shapeOptions': {'color': 'black', 'fillColor': 'yellow', 'fillOpacity': 0.5, 'weight': 2}},
        'rectangle': {'shapeOptions': {'color': 'black', 'fillColor': 'yellow', 'fillOpacity': 0.5, 'weight': 2}},
        'circle': {'shapeOptions': {'color': 'black', 'fillColor': 'yellow', 'fillOpacity': 0.5, 'weight': 2}},
        'marker': False, # Вимкнено стандартний маркер щоб не плутати
        'circlemarker': {'color': 'black', 'fillColor': 'yellow', 'fillOpacity': 0.9, 'radius': 8}
    }
    
    Draw(
        export=True,
        draw_options=draw_options,
        edit_options={'poly': {'allowIntersection': False}}
    ).add_to(m)

    # ВІДОБРАЖЕННЯ КАРТИ
    output = st_folium(m, width="100%", height=650, key="chem_map_v5")

    # ОБРОБКА КЛІКУ: Отримуємо координати назад у Streamlit
    # Важливо: ігноруємо кліки, якщо користувач малює фігуру (це автоматично обробляє st_folium)
    if output.get("last_clicked"):
        lat_f = output["last_clicked"]["lat"]
        lon_f = output["last_clicked"]["lng"]
        new_click = [lat_f, lon_f]
        
        # Оновлюємо тільки якщо клікнули в нове місце
        if st.session_state.clicked_coords != new_click:
            st.session_state.clicked_coords = new_click
            st.rerun()

    # Кнопки під картою (Текст, Експорт)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("ВСТАВИТИ ТЕКСТ"):
            st.info("Використовуйте стандартний інструмент малювання або маркер для позначок.")
    with c2:
        if st.button("ОЧИСТИТИ МАЛЮНКИ"):
            st.rerun() # st_folium автоматично очистить незбережені малюнки
    with c3:
        st.download_button("ЕКСПОРТ ДАНИХ (CSV)", st.session_state.data.to_csv(index=False), "chemical_data.csv")
    with c4:
        if st.button("ДРУК / PDF"):
            st.write("Натисніть Ctrl+P для друку звіту")

# ===============================
# 5. ТАБЛИЦЯ
# ===============================
if not st.session_state.data.empty:
    st.dataframe(st.session_state.data, use_container_width=True)
