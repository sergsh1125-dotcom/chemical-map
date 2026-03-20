import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import Print # Додано для стабільного експорту
from datetime import datetime

# ===============================
# 1. СТОРІНКА
# ===============================
st.set_page_config(page_title="КАРТА ХІМІЧНОЇ ОБСТАНОВКИ", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stButton button {font-weight: bold;}
/* Корекція для друку таблиці під картою */
@media print {
    .stColumn:last-child, .stButton, .stDownloadButton { display: none !important; }
    .stApp { background-color: white !important; }
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 2. SESSION STATE
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# ===============================
# 3. ПІДПИС
# ===============================
def marker_html(main, sub):
    return f"""
    <div style="
        display: inline-block;
        font-family: Arial; font-size: 10pt; color: blue; font-weight: bold;
        text-align: center; white-space: nowrap;
        text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;
    ">
        <div style="border-bottom: 2px solid blue; padding-bottom: 2px; margin-bottom: 2px;">{main}</div>
        <div style="font-weight: normal;">{sub}</div>
    </div>
    """

# ===============================
# 4. КАРТА
# ===============================
def create_map(df, lat, lon, zoom):
    # Створюємо карту
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles='OpenStreetMap', control_scale=True)
    
    # Додаємо супутник як альтернативний шар
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Супутник',
        overlay=False,
        control=True
    ).add_to(m)

    # 🔥 РІШЕННЯ ДЛЯ PNG/PDF: Додаємо плагін друку безпосередньо на карту
    # Він автоматично обробляє CORS-тайли і дозволяє зберегти карту правильно
    Print().add_to(m)

    # Маркер кліку
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red")
        ).add_to(m)

    # Нанесення точок
    if not df.empty:
        for _, r in df.iterrows():
            main_txt = f"{r['substance']} {float(r['value']):.2f} {r['unit']}"
            folium.CircleMarker(
                [r.lat, r.lon], radius=6, color="orange", fill=True, fill_color="orange", fill_opacity=1
            ).add_to(m)
            folium.Marker(
                [r.lat, r.lon],
                icon=folium.DivIcon(icon_anchor=(80, 45), html=marker_html(main_txt, r['time']))
            ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# ===============================
# 5. ІНТЕРФЕЙС
# ===============================
st.header("КАРТА ХІМІЧНОЇ ОБСТАНОВКИ")

col_map, col_panel = st.columns([3, 1])

with col_panel:
    st.subheader("ПУЛЬТ УПРАВЛІННЯ")
    if st.session_state.clicked_coords:
        c = st.session_state.clicked_coords
        st.write(f"Координати: {c['lat']:.6f}, {c['lng']:.6f}")
        if st.button("Вставити у форму", use_container_width=True):
            st.session_state.manual_lat = c['lat']
            st.session_state.manual_lon = c['lng']
            st.rerun()
        if st.button("Виключити маркер", use_container_width=True):
            st.session_state.clicked_coords = None
            st.rerun()

    st.divider()
    # Форма вводу
    lat_in = st.number_input("Широта", format="%.6f", value=st.session_state.get("manual_lat", 50.4500))
    lon_in = st.number_input("Довгота", format="%.6f", value=st.session_state.get("manual_lon", 30.5200))
    sub_in = st.text_input("Речовина", "Хлор")
    val_in = st.number_input("Значення", format="%.2f")
    unit_in = st.selectbox("Одиниця", ["мг/м³","ppm"])
    date_in = st.date_input("Дата", value=datetime.now()).strftime("%d.%m.%Y")

    if st.button("Нанести на карту", use_container_width=True):
        new_row = pd.DataFrame([{"lat": lat_in, "lon": lon_in, "substance": sub_in, "value": val_in, "unit": unit_in, "time": date_in}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.rerun()

# -------- КАРТА --------
with col_map:
    # Визначаємо центр карти
    if st.session_state.data.empty:
        c_lat, c_lon, c_zoom = 49.0, 31.0, 6
    else:
        c_lat, c_lon, c_zoom = st.session_state.data.lat.mean(), st.session_state.data.lon.mean(), 9

    m_obj = create_map(st.session_state.data, c_lat, c_lon, c_zoom)
    
    # Вивід карти
    map_data = st_folium(
        m_obj, 
        width="100%", 
        height=700, 
        key="main_map",
        returned_objects=["last_clicked"]
    )

    # Обробка кліку
    if map_data.get("last_clicked"):
        if st.session_state.clicked_coords != map_data["last_clicked"]:
            st.session_state.clicked_coords = map_data["last_clicked"]
            st.rerun()

    # Додаткові кнопки під картою
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Очистити карту", use_container_width=True):
            st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
            st.session_state.clicked_coords = None
            st.rerun()
    with c2:
        st.info("☝️ Для PNG/PDF використовуйте іконку принтера на самій карті (вгорі зліва)")
    with c3:
        if not st.session_state.data.empty:
            st.download_button("Завантажити CSV", st.session_state.data.to_csv(index=False), "data.csv", "text/csv")

# -------- ТАБЛИЦЯ --------
if not st.session_state.data.empty:
    st.subheader("Таблиця вимірювань")
    st.dataframe(st.session_state.data, use_container_width=True)
