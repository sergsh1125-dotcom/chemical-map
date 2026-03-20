import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# 1. КОНФІГУРАЦІЯ
st.set_page_config(page_title="RKhBZ System", layout="wide")

# Примусове скидання стилів для друку
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    @media print {
        .stColumn:last-child, button, .stDownloadButton, [data-testid="stSidebar"] { display: none !important; }
        .stMain { padding: 0 !important; }
        #map-container { width: 100vw !important; height: 100vh !important; }
    }
</style>
""", unsafe_allow_html=True)

# Ініціалізація пам'яті (Session State)
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# 2. ОЧИЩЕННЯ (ФУНКЦІЯ)
def reset_all():
    st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
    st.session_state.clicked_coords = None
    if "manual_lat" in st.session_state: del st.session_state.manual_lat
    if "manual_lon" in st.session_state: del st.session_state.manual_lon
    st.rerun()

# 3. Побудова карти
def get_map(df):
    # Початкова точка - центр України або середня точка даних
    start_lat = df.lat.mean() if not df.empty else 49.0
    start_lon = df.lon.mean() if not df.empty else 31.0
    
    # Створюємо карту зі СВІТЛИМ шаром за замовчуванням
    m = folium.Map(location=[start_lat, start_lon], zoom_start=6, tiles='OpenStreetMap')
    
    # Додаємо супутник як ДОДАТКОВИЙ шар
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google', name='Супутник', overlay=False
    ).add_to(m)

    # Якщо є клік - ставимо маркер
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red")
        ).add_to(m)

    # Малюємо збережені точки
    for _, r in df.iterrows():
        label = f"{r['substance']}: {r['value']} {r['unit']}"
        folium.CircleMarker([r.lat, r.lon], radius=8, color="blue", fill=True).add_to(m)
        folium.Marker([r.lat, r.lon], icon=folium.DivIcon(html=f'<b style="color:red; font-size:12px;">{label}</b>')).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# 4. ІНТЕРФЕЙС
col_map, col_ctrl = st.columns([3, 1])

with col_ctrl:
    st.title("🛡️ РХБЗ")
    lat = st.number_input("Широта", value=st.session_state.get("manual_lat", 50.45), format="%.6f")
    lon = st.number_input("Довгота", value=st.session_state.get("manual_lon", 30.52), format="%.6f")
    sub = st.text_input("Речовина", "Хлор")
    val = st.number_input("Значення", 0.0)
    
    if st.button("ДОДАТИ НА КАРТУ", use_container_width=True):
        new = pd.DataFrame([{"lat": lat, "lon": lon, "substance": sub, "value": val, "unit": "мг/м³", "time": datetime.now().strftime("%H:%M")}])
        st.session_state.data = pd.concat([st.session_state.data, new], ignore_index=True)
        st.rerun()

    st.divider()
    if st.button("🔴 ОЧИСТИТИ КАРТУ ТА МАРКЕР", use_container_width=True):
        reset_all()

with col_map:
    st.markdown('<div id="map-container">', unsafe_allow_html=True)
    m_obj = get_map(st.session_state.data)
    out = st_folium(m_obj, width=None, height=600, key="map_v4")
    st.markdown('</div>', unsafe_allow_html=True)

    if out.get("last_clicked"):
        c = out["last_clicked"]
        if st.session_state.clicked_coords != c:
            st.session_state.clicked_coords = c
            st.session_state.manual_lat, st.session_state.manual_lon = c['lat'], c['lng']
            st.rerun()
