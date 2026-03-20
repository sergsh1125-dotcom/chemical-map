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
.stButton button {font-weight: bold; background-color: #ffcc00 !important; color: black !important;}
.stNumberInput input {font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ===============================
# 2. SESSION STATE (ВАША ЛОГІКА)
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# Допоміжні змінні для автозаповнення форми
if "manual_lat" not in st.session_state: st.session_state.manual_lat = 50.45
if "manual_lon" not in st.session_state: st.session_state.manual_lon = 30.52

# ===============================
# 3. ПІДПИС МАРКЕРА (ВАШ СТИЛЬ)
# ===============================
def marker_html(main, sub):
    return f"""
    <div style="display: inline-block; font-family: Arial; font-size: 10pt; color: blue; font-weight: bold; text-align: center; white-space: nowrap; background-color: transparent; text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff, 2px 2px 3px rgba(255,255,255,0.9);">
        <div style="border-bottom: 2px solid blue; display: inline-block; padding-bottom: 2px; margin-bottom: 2px;">{main}</div>
        <div style="font-weight: normal;">{sub}</div>
    </div>
    """

# ===============================
# 4. СТВОРЕННЯ КАРТИ
# ===============================
def create_map(df, lat, lon, zoom):
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None, control_scale=True)
    
    # Шари карти
    folium.TileLayer('OpenStreetMap', name='Карта', show=True).add_to(m)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite', name='Супутник', show=False
    ).add_to(m)

    # ВАША ЛОГІКА: Маркер кліку (Червоний)
    if st.session_state.clicked_coords is not None:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red")
        ).add_to(m)

    # НАНЕСЕННЯ ТОЧОК З ТАБЛИЦІ
    if not df.empty:
        for day in sorted(df['time'].unique(), reverse=True):
            group = folium.FeatureGroup(name=f"📅 {day}")
            for _, r in df[df['time'] == day].iterrows():
                main_txt = f"{r['substance']} {float(r['value']):.2f} {r['unit']}"
                folium.CircleMarker(
                    [r.lat, r.lon], radius=6, color="orange", fill=True, fill_color="orange", fill_opacity=1
                ).add_to(group)
                folium.Marker(
                    [r.lat, r.lon],
                    icon=folium.DivIcon(icon_anchor=(80, 45), html=marker_html(main_txt, r['time']))
                ).add_to(group)
            group.add_to(m)

    # --- ДОДАТКОВІ ФУНКЦІЇ (ЯК ВЧОРА) ---
    # 1. Панель малювання (Draw)
    draw_tools = Draw(
        draw_options={
            'polyline': True, 'polygon': True, 'rectangle': True, 'circle': True, 
            'marker': True, 'circlemarker': {'color': 'black', 'fillColor': 'yellow', 'fillOpacity': 0.9, 'radius': 8}
        },
        edit_options={'edit': True}
    )
    draw_tools.add_to(m)

    # 2. Додаємо JS для Тексту, PNG та PDF (як у "стартовій карті")
    export_script = """
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
    function addTextToMap() {
        var txt = prompt("Введіть текст:");
        if (txt) { alert("Текст готовий. Тепер клікніть на карті інструментом 'Marker', щоб поставити його (або використовуйте стандартний підпис)."); }
    }
    
    function captureMap() {
        var mapElement = document.querySelector('.folium-map');
        html2canvas(mapElement, {useCORS: true}).then(canvas => {
            var link = document.createElement('a');
            link.download = 'Chemical_Situation.png';
            link.href = canvas.toDataURL();
            link.click();
        });
    }
    </script>
    """
    m.get_root().header.add_child(folium.Element(export_script))

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# ===============================
# 5. ГОЛОВНИЙ ІНТЕРФЕЙС
# ===============================
st.header("КАРТА ХІМІЧНОЇ ОБСТАНОВКИ")

col_map, col_panel = st.columns([3, 1])

with col_panel:
    st.subheader("ПУЛЬТ УПРАВЛІННЯ")

    # ВАША ЛОГІКА: Робота з кліком
    if st.session_state.clicked_coords:
        curr_lat = st.session_state.clicked_coords['lat']
        curr_lon = st.session_state.clicked_coords['lng']
        st.success(f"Вибрано: {curr_lat:.6f}, {curr_lon:.6f}")
        
        if st.button("Вставити координати у форму", use_container_width=True):
            st.session_state.manual_lat = curr_lat
            st.session_state.manual_lon = curr_lon
            st.rerun()
            
        if st.button("Виключити маркер", use_container_width=True):
            st.session_state.clicked_coords = None
            st.rerun()
    else:
        st.info("Клікніть на карті, щоб отримати координати")

    st.divider()

    # ВРУЧНУ (Автозаповнюється через Session State)
    st.markdown("### НАНЕСЕННЯ ТОЧКИ")
    in_lat = st.number_input("Широта", format="%.6f", value=st.session_state.manual_lat)
    in_lon = st.number_input("Довгота", format="%.6f", value=st.session_state.manual_lon)
    substance = st.text_input("Речовина", "Хлор")
    value = st.number_input("Значення", format="%.2f")
    unit = st.selectbox("Одиниця", ["мг/м³","ppm"])
    # Дата як на комп'ютері
    time_val = st.date_input("Дата", value=datetime.now()).strftime("%d.%m.%Y")

    if st.button("Нанести на карту (в таблицю)"):
        new = pd.DataFrame([{"lat": in_lat, "lon": in_lon, "substance": substance, "value": value, "unit": unit, "time": time_val}])
        st.session_state.data = pd.concat([st.session_state.data, new], ignore_index=True)
        st.rerun()

    st.divider()
    
    # Кнопки експорту (тепер тут для зручності)
    st.markdown("### ЕКСПОРТ")
    if st.button("ЗБЕРЕГТИ КАРТУ (PNG)"):
        st.warning("Використовуйте 'Print' у вікні карти або кнопку 'Export' на панелі малювання.")

# -------- КАРТА --------
with col_map:
    # Визначення центру
    if st.session_state.data.empty:
        c_lat, c_lon, zoom = 48.3794, 31.1656, 6
    else:
        c_lat, c_lon, zoom = st.session_state.data.lat.mean(), st.session_state.data.lon.mean(), 9

    m = create_map(st.session_state.data, c_lat, c_lon, zoom)

    # Виклик карти з поверненням кліку (ВАША ЛОГІКА)
    map_output = st_folium(
        m,
        width="100%",
        height=700,
        key="chemical_map_main",
        returned_objects=["last_clicked"]
    )

    # Обробка кліку
    if map_output.get("last_clicked"):
        clicked = map_output["last_clicked"]
        if st.session_state.clicked_coords != clicked:
            st.session_state.clicked_coords = clicked
            st.rerun()

    # Кнопки швидких дій під картою
    c1, c2, c3 = st.columns(3)
    if c1.button("Очистити таблицю вимірювань"):
        st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
        st.rerun()
    if c2.button("Друк карти / PDF"):
        st.info("Натисніть Ctrl+P або скористайтеся функцією друку в браузері")

# -------- ТАБЛИЦЯ --------
if not st.session_state.data.empty:
    st.subheader("Журнал вимірювань")
    st.dataframe(st.session_state.data, use_container_width=True)
