import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import streamlit.components.v1 as components

# ===============================
# 1. КОНФІГУРАЦІЯ ТА СТИЛІ
# ===============================
st.set_page_config(page_title="RKhBZ Map Control", layout="wide")

# Спеціальний CSS для друку: залишає тільки карту на весь аркуш
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stButton button {font-weight: bold; border-radius: 5px;}
@media print {
    /* Приховуємо все, крім контейнера з картою */
    .stColumn:last-child, button, .stDownloadButton, .stHeader, header, footer { 
        display: none !important; 
    }
    .stColumn:first-child { width: 100% !important; }
    #map-container { width: 100% !important; height: 100vh !important; }
}
</style>
""", unsafe_allow_html=True)

# Стан програми
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# ===============================
# 2. ФУНКЦІЇ
# ===============================
def create_map(df, lat, lon, zoom):
    # Базова карта (OpenStreetMap)
    m = folium.Map(location=[lat, lon], zoom_start=zoom, control_scale=True)
    
    # Додаємо Гібридний шар (Супутник + Назви)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google', name='Супутник (Гібрид)', overlay=False
    ).add_to(m)

    # Маркер поточного кліку
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    # Нанесення точок вимірювань
    for _, r in df.iterrows():
        label = f"{r['substance']} {r['value']} {r['unit']}"
        folium.CircleMarker(
            [r.lat, r.lon], radius=7, color="orange", fill=True, fill_opacity=1
        ).add_to(m)
        folium.Marker(
            [r.lat, r.lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10pt; color:blue; font-weight:bold; width:150px; text-shadow: 1px 1px white;">{label}</div>',
                icon_anchor=(0, 0)
            )
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m

# ===============================
# 3. ІНТЕРФЕЙС
# ===============================
st.header("КАРТА ХІМІЧНОЇ ОБСТАНОВКИ")

col_map, col_panel = st.columns([3, 1])

with col_panel:
    st.subheader("📊 УПРАВЛІННЯ")
    
    # Поля вводу
    lat_in = st.number_input("Широта", format="%.6f", value=st.session_state.get("manual_lat", 50.4500))
    lon_in = st.number_input("Довгота", format="%.6f", value=st.session_state.get("manual_lon", 30.5200))
    sub_in = st.text_input("Речовина", "Хлор (Cl2)")
    val_in = st.number_input("Значення", format="%.2f")
    unit_in = st.selectbox("Одиниця", ["мг/м³","ppm"])
    
    if st.button("➕ НАНЕСТИ НА КАРТУ", use_container_width=True):
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        new_row = pd.DataFrame([{"lat": lat_in, "lon": lon_in, "substance": sub_in, "value": val_in, "unit": unit_in, "time": now}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.rerun()

    st.divider()
    
    # Кнопки експорту
    st.markdown("### 📥 ЕКСПОРТ")
    if st.button("📄 ЗБЕРЕГТИ ЯК PDF", use_container_width=True):
        # Виклик системного друку браузера
        components.html("<script>window.print();</script>", height=0)
    
    if not st.session_state.data.empty:
        st.download_button(
            "Excel/CSV Таблиця", 
            st.session_state.data.to_csv(index=False), 
            "chem_data.csv", 
            "text/csv",
            use_container_width=True
        )
        
        if st.button("🧹 ОЧИСТИТИ КАРТУ", use_container_width=True):
            st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
            st.session_state.clicked_coords = None
            st.rerun()

    st.info("💡 Порада: Для збереження **PNG** натисніть правою кнопкою миші на карту і оберіть 'Зберегти зображення як...'")

with col_map:
    # Визначення центру карти
    if not st.session_state.data.empty:
        c_lat, c_lon, c_zoom = st.session_state.data.lat.mean(), st.session_state.data.lon.mean(), 9
    else:
        c_lat, c_lon, c_zoom = 49.0, 31.0, 6

    m_obj = create_map(st.session_state.data, c_lat, c_lon, c_zoom)
    
    # Вивід карти в спеціальному контейнері для друку
    st.markdown('<div id="map-container">', unsafe_allow_html=True)
    map_output = st_folium(m_obj, width="100%", height=750, key="rkhbz_map", returned_objects=["last_clicked"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Обробка кліку по карті
    if map_output.get("last_clicked"):
        clicked = map_output["last_clicked"]
        if st.session_state.clicked_coords != clicked:
            st.session_state.clicked_coords = clicked
            st.session_state.manual_lat = clicked["lat"]
            st.session_state.manual_lon = clicked["lng"]
            st.rerun()

# Таблиця під картою
if not st.session_state.data.empty:
    st.subheader("📋 Журнал вимірювань")
    st.dataframe(st.session_state.data, use_container_width=True)
