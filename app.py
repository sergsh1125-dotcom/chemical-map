import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import streamlit.components.v1 as components

# 1. СТИЛІ ТА ВЕЛИКІ КНОПКИ (Як у вашій першій версії)
st.set_page_config(page_title="RKhBZ Monitoring", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stButton button {
    font-weight: bold; 
    font-size: 22px !important; 
    background-color: #FFD600 !important; /* Яскраво-жовтий */
    color: black !important;
    height: 3em;
    border-radius: 10px;
}
/* Спеціальний режим друку для усунення "білих полів" */
@media print {
    .stColumn:last-child, button, .stDownloadButton, header { display: none !important; }
    .stColumn:first-child { width: 100% !important; }
    #map-container { width: 100% !important; height: 98vh !important; }
}
</style>
""", unsafe_allow_html=True)

# Пам'ять додатка
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# 2. ПРАВИЛЬНА КАРТА (Світла за замовчуванням)
def create_map(df, lat, lon, zoom):
    # ПРІОРИТЕТ 1: OpenStreetMap (щоб не було самовільного супутника)
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles='OpenStreetMap', control_scale=True)
    
    # ПРІОРИТЕТ 2: Супутник (тільки як опція в меню)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google', name='Супутник (Гібрид)', overlay=False
    ).add_to(m)

    # Червоний маркер вибору (видаляється після нанесення точки)
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    # Точки вимірювання з ПОВНИМ описом
    for _, r in df.iterrows():
        txt = f"{r['substance']} {r['value']} {r['unit']}"
        time_txt = f"{r['time']}"
        
        folium.CircleMarker([r.lat, r.lon], radius=7, color="orange", fill=True, fill_opacity=1).add_to(m)
        
        # HTML-підпис (Синій колір, без рамок, як ви звикли)
        html_label = f"""
        <div style="font-family: Arial; font-weight: bold; color: blue; white-space: nowrap;">
            <div>{txt}</div>
            <div style="font-weight: normal; font-size: 10px;">{time_txt}</div>
        </div>
        """
        folium.Marker(
            [r.lat, r.lon],
            icon=folium.DivIcon(html=html_label, icon_anchor=(70, 35))
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# 3. ІНТЕРФЕЙС
st.header("📍 МОНІТОРИНГ ХІМІЧНОЇ ОБСТАНОВКИ")
col_map, col_panel = st.columns([3, 1])

with col_panel:
    st.write("### 📝 ВВІД ДАНИХ")
    
    lat_in = st.number_input("Широта", format="%.6f", value=st.session_state.get("manual_lat", 50.4500))
    lon_in = st.number_input("Довгота", format="%.6f", value=st.session_state.get("manual_lon", 30.5200))
    sub_in = st.text_input("Речовина", "Хлор")
    val_in = st.number_input("Значення", format="%.2f")
    unit_in = st.selectbox("Одиниця", ["мг/м³", "ppm"])
    date_in = st.text_input("Дата/Час", datetime.now().strftime("%d.%m.%Y %H:%M"))
    
    if st.button("✅ НАНЕСТИ НА КАРТУ"):
        new_row = pd.DataFrame([{"lat": lat_in, "lon": lon_in, "substance": sub_in, "value": val_in, "unit": unit_in, "time": date_in}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.session_state.clicked_coords = None # Видаляємо маркер вибору
        st.rerun()

    st.divider()
    
    # Кнопка для PDF (працює через системний друк, без білих плям)
    if st.button("📄 ЗБЕРЕГТИ КАРТУ (PDF)"):
        components.html("<script>window.print();</script>", height=0)
    
    if st.button("🗑️ ОЧИСТИТИ ВСЕ"):
        st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
        st.session_state.clicked_coords = None
        st.rerun()

    if not st.session_state.data.empty:
        st.download_button("📥 СКАЧАТИ CSV", st.session_state.data.to_csv(index=False), "rkhbz_data.csv")

with col_map:
    # Центруємо по точках або по Києву
    c_lat = st.session_state.data.lat.mean() if not st.session_state.data.empty else 50.45
    c_lon = st.session_state.data.lon.mean() if not st.session_state.data.empty else 30.52
    
    m_obj = create_map(st.session_state.data, c_lat, c_lon, 6 if st.session_state.data.empty else 9)
    
    st.markdown('<div id="map-container">', unsafe_allow_html=True)
    map_res = st_folium(m_obj, width="100%", height=750, key="stable_v1", returned_objects=["last_clicked"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Логіка кліку
    if map_res.get("last_clicked"):
        clicked = map_res["last_clicked"]
        if st.session_state.clicked_coords != clicked:
            st.session_state.clicked_coords = clicked
            st.session_state.manual_lat = clicked["lat"]
            st.session_state.manual_lon = clicked["lng"]
            st.rerun()

# Таблиця даних
if not st.session_state.data.empty:
    st.dataframe(st.session_state.data, use_container_width=True)
