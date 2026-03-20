import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import streamlit.components.v1 as components

# 1. НАЛАШТУВАННЯ ТА СТИЛІ (Повертаємо великі шрифти та жовті кнопки)
st.set_page_config(page_title="RKhBZ Monitoring", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stButton button {
    font-weight: bold; 
    font-size: 20px !important; 
    height: 3em;
    background-color: #FFEB3B !important; /* Жовтий колір для помітності */
    color: black !important;
}
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

# 2. ФУНКЦІЯ КАРТИ (Повертаємо підписи: Речовина, Значення, Одиниці, Дата)
def create_map(df, lat, lon, zoom):
    # Перша карта - звичайна (OpenStreetMap)
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles='OpenStreetMap', control_scale=True)
    
    # Супутник (Гібрид) як опція
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google', name='Супутник (Гібрид)', overlay=False
    ).add_to(m)

    # Червоний маркер кліку (Тимчасовий)
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red", icon="screenshot", prefix="fa")
        ).add_to(m)

    # Нанесення точок з ПОВНИМ ПІДПИСОМ
    for _, r in df.iterrows():
        # Формуємо рядок: Речовина + Значення + Одиниця
        main_label = f"{r['substance']} {r['value']} {r['unit']}"
        time_label = f"{r['time']}"
        
        folium.CircleMarker([r.lat, r.lon], radius=7, color="orange", fill=True, fill_opacity=1).add_to(m)
        
        # HTML-контент для підпису без прямокутників (як ви просили раніше)
        html_content = f"""
        <div style="font-family: Arial; font-weight: bold; color: blue; white-space: nowrap; text-align: center;">
            <div style="border-bottom: 1px solid blue; padding-bottom: 2px;">{main_label}</div>
            <div style="font-weight: normal; font-size: 9pt;">{time_label}</div>
        </div>
        """
        folium.Marker(
            [r.lat, r.lon],
            icon=folium.DivIcon(html=html_content, icon_anchor=(75, 40))
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# 3. ІНТЕРФЕЙС
st.header("КАРТА ХІМІЧНОЇ ОБСТАНОВКИ")
col_map, col_panel = st.columns([3, 1])

with col_panel:
    st.subheader("📝 ВВІД ДАНИХ")
    
    lat_in = st.number_input("Широта", format="%.6f", value=st.session_state.get("manual_lat", 50.4500))
    lon_in = st.number_input("Довгота", format="%.6f", value=st.session_state.get("manual_lon", 30.5200))
    sub_in = st.text_input("Речовина", "Хлор")
    val_in = st.number_input("Значення (мг/м³ або ppm)", format="%.2f")
    unit_in = st.selectbox("Одиниця виміру", ["мг/м³", "ppm"])
    date_in = st.text_input("Дата та час", datetime.now().strftime("%d.%m.%Y %H:%M"))
    
    if st.button("➕ НАНЕСТИ НА КАРТУ"):
        new_row = pd.DataFrame([{"lat": lat_in, "lon": lon_in, "substance": sub_in, "value": val_in, "unit": unit_in, "time": date_in}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        # Очищуємо червоний маркер після нанесення точки
        st.session_state.clicked_coords = None
        st.rerun()

    st.divider()
    
    # КНОПКИ УПРАВЛІННЯ
    if st.button("📄 ЗБЕРЕГТИ КАРТУ (PDF)"):
        components.html("<script>window.print();</script>", height=0)
    
    if st.button("🔴 ВИДАЛИТИ МАРКЕР ТА ОЧИСТИТИ"):
        st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
        st.session_state.clicked_coords = None
        st.rerun()

    if not st.session_state.data.empty:
        st.download_button("📥 СКАЧАТИ ТАБЛИЦЮ (CSV)", st.session_state.data.to_csv(index=False), "data.csv")

with col_map:
    # Визначаємо центр
    c_lat = st.session_state.data.lat.mean() if not st.session_state.data.empty else 49.0
    c_lon = st.session_state.data.lon.mean() if not st.session_state.data.empty else 31.0
    
    m_obj = create_map(st.session_state.data, c_lat, c_lon, 6 if st.session_state.data.empty else 9)
    
    st.markdown('<div id="map-container">', unsafe_allow_html=True)
    map_res = st_folium(m_obj, width="100%", height=700, key="final_v_1", returned_objects=["last_clicked"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Обробка кліку: маркер з'являється і передає координати у форму
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
