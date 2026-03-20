import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import streamlit.components.v1 as components

# 1. НАЛАШТУВАННЯ ТА СТИЛІ
st.set_page_config(page_title="RKhBZ Monitoring", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stButton button {font-weight: bold; width: 100%; border-radius: 8px;}
/* Стиль для друку: ховаємо все зайве, залишаємо карту */
@media print {
    .stColumn:last-child, button, .stDownloadButton, .stMarkdown, header { display: none !important; }
    .stColumn:first-child { width: 100% !important; }
    #map-container { width: 100% !important; height: 95vh !important; }
}
</style>
""", unsafe_allow_html=True)

# Стан програми
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# 2. ФУНКЦІЯ КАРТИ
def create_map(df, lat, lon, zoom):
    # ПЕРША КАРТА - ЗВИЧАЙНА (Світла)
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles='OpenStreetMap', control_scale=True)
    
    # ДРУГА КАРТА - СУПУТНИК (Можна перемкнути в меню)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google', name='Супутник (Гібрид)', overlay=False
    ).add_to(m)

    # Відображення тимчасового червоного маркера
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red", icon="plus")
        ).add_to(m)

    # Нанесення збережених точок
    for _, r in df.iterrows():
        label = f"{r['substance']} {r['value']} {r['unit']}"
        folium.CircleMarker([r.lat, r.lon], radius=7, color="orange", fill=True, fill_opacity=1).add_to(m)
        folium.Marker(
            [r.lat, r.lon],
            icon=folium.DivIcon(html=f'<div style="font-size:10pt; color:blue; font-weight:bold; width:150px; text-shadow: 1px 1px white;">{label}</div>')
        ).add_to(m)

    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    return m

# 3. ІНТЕРФЕЙС
st.subheader("🛰️ СИСТЕМА МОНІТОРИНГУ РХБЗ")
col_map, col_panel = st.columns([3, 1])

with col_panel:
    st.write("### ⚙️ ПАРАМЕТРИ")
    
    lat_in = st.number_input("Широта", format="%.6f", value=st.session_state.get("manual_lat", 50.4500))
    lon_in = st.number_input("Довгота", format="%.6f", value=st.session_state.get("manual_lon", 30.5200))
    sub_in = st.text_input("Речовина", "Хлор")
    val_in = st.number_input("Значення", format="%.2f")
    unit_in = st.selectbox("Одиниця", ["мг/м³", "ppm"])
    
    if st.button("✅ ДОДАТИ ТОЧКУ"):
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        new_row = pd.DataFrame([{"lat": lat_in, "lon": lon_in, "substance": sub_in, "value": val_in, "unit": unit_in, "time": now}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.rerun()

    st.divider()
    
    if st.button("📄 ЕКСПОРТ У PDF (ДРУК)"):
        # Це відкриє вікно друку браузера - оберіть "Зберегти як PDF"
        components.html("<script>window.print();</script>", height=0)
    
    if st.button("🗑️ ОЧИСТИТИ ВСЕ"):
        st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
        st.session_state.clicked_coords = None
        st.session_state.manual_lat = 50.4500
        st.session_state.manual_lon = 30.5200
        st.rerun()

    st.info("💡 **PNG:** Натисніть правою кнопкою на карту -> 'Зберегти як зображення'")

with col_map:
    # Центрування
    c_lat = st.session_state.data.lat.mean() if not st.session_state.data.empty else 49.0
    c_lon = st.session_state.data.lon.mean() if not st.session_state.data.empty else 31.0
    
    m_obj = create_map(st.session_state.data, c_lat, c_lon, 6 if st.session_state.data.empty else 9)
    
    st.markdown('<div id="map-container">', unsafe_allow_html=True)
    map_res = st_folium(m_obj, width="100%", height=700, key="stable_map", returned_objects=["last_clicked"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Логіка кліку
    if map_res.get("last_clicked"):
        clicked = map_res["last_clicked"]
        if st.session_state.clicked_coords != clicked:
            st.session_state.clicked_coords = clicked
            st.session_state.manual_lat = clicked["lat"]
            st.session_state.manual_lon = clicked["lng"]
            st.rerun()

# Таблиця
if not st.session_state.data.empty:
    st.dataframe(st.session_state.data, use_container_width=True)
