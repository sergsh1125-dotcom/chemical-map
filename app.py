import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import io

# ===============================
# Налаштування сторінки
# ===============================
st.set_page_config(
    page_title="Chemical Hazard Map",
    layout="wide"
)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ===============================
# Стан програми (Session State)
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# ===============================
# Заголовок
# ===============================
st.title("Карта хімічної обстановки")

# ===============================
# Розподіл екрану
# ===============================
col_map, col_gui = st.columns([2.5, 1])

# ===============================
# Права панель (GUI)
# ===============================
with col_gui:
    st.subheader("⚙️ Управління та Координати")

    # СЕКЦІЯ КЛІКУ ПО КАРТІ
    if st.session_state.clicked_coords:
        c_lat = st.session_state.clicked_coords['lat']
        c_lon = st.session_state.clicked_coords['lng']
        
        st.info(f"📍 Координати на карті:\n**Широта:** {c_lat:.6f}\n**Довгота:** {c_lon:.6f}")
        
        c1, c2 = st.columns(2)
        # Збереження обраних координат
        clicked_df = pd.DataFrame([{"lat": c_lat, "lon": c_lon}])
        csv = clicked_df.to_csv(index=False).encode('utf-8')
        c1.download_button("💾 Зберегти координати", csv, "point_coords.csv", "text/csv", use_container_width=True)
        
        if c2.button("✏️ Вставити в форму", use_container_width=True):
            st.session_state.manual_lat = c_lat
            st.session_state.manual_lon = c_lon
            st.rerun()
    else:
        st.write("👆 *Клікніть на карту, щоб визначити координати точки*")

    st.divider()

    # СЕКЦІЯ ДОДАВАННЯ ТОЧКИ
    st.markdown("### ➕ Нанесення точки вручну")
    
    # Використовуємо значення з сесії для автозаповнення
    default_lat = st.session_state.get('manual_lat', 50.4501)
    default_lon = st.session_state.get('manual_lon', 30.5234)

    substance = st.text_input("Назва речовини", placeholder="Наприклад: Хлор")
    lat_input = st.number_input("Широта (lat)", format="%.6f", value=default_lat)
    lon_input = st.number_input("Довгота (lon)", format="%.6f", value=default_lon)
    
    value = st.number_input("Концентрація (мг/куб. м)", min_value=0.0, step=0.001, format="%.4f")
    # Форматування дати за замовчуванням
    default_time = pd.Timestamp.now().strftime("%d.%m.%Y")
    time_input = st.text_input("Дата (ДД.ММ.РРРР)", value=default_time)

    if st.button("✅ Нанести на карту", use_container_width=True):
        new_row = pd.DataFrame([{"lat": lat_input, "lon": lon_input, "substance": substance, "value": value, "time": time_input}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.toast(f"Точку {substance} додано!")
        st.rerun()

    st.divider()
    
    if st.button("🧹 Очистити все", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.session_state.clicked_coords = None
        st.session_state.manual_lat = 50.4501
        st.session_state.manual_lon = 30.5234
        st.rerun()

# ===============================
# Візуалізація на карті
# ===============================
with col_map:
    # Визначаємо центр карти
    if not st.session_state.data.empty:
        center_lat, center_lon, zoom = st.session_state.data.lat.mean(), st.session_state.data.lon.mean(), 11
    else:
        center_lat, center_lon, zoom = 50.4501, 30.5234, 10

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, control_scale=True)

    # 1. Вікно з координатами при кліку
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            popup=folium.Popup(
                f"Координати:<br><b>{st.session_state.clicked_coords['lat']:.6f}</b><br><b>{st.session_state.clicked_coords['lng']:.6f}</b>", 
                max_width=200, show=True
            ),
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
        ).add_to(m)

    # 2. Нанесення існуючих даних
    if not st.session_state.data.empty:
        for _, r in st.session_state.data.iterrows():
            val_formatted = f"{r['value']:.4f}".rstrip('0').rstrip('.')
            
            # HTML-контейнер для дворядкового напису
            label_html = f"""
            <div style="
                font-family: 'Arial', sans-serif; 
                font-size: 10pt; 
                color: black; 
                background-color: rgba(255,255,255,0.85);
                border: 1px solid #333;
                padding: 4px;
                border-radius: 4px;
                white-space: nowrap;
                text-align: center;
                line-height: 1.3;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            ">
                <b>{r['substance']} — {val_formatted} мг/куб. м</b>
                <hr style="margin: 3px 0; border: 0; border-top: 1px solid black;">
                <span>{r['time']}</span>
            </div>
            """
            
            # Напис (Marker) розташовується над точкою
            folium.map.Marker(
                [r.lat, r.lon],
                icon=folium.DivIcon(
                    icon_anchor=(70, 55), # Регулювання позиції напису над точкою
                    html=label_html
                )
            ).add_to(m)
            
            # Сама точка
            folium.CircleMarker(
                [r.lat, r.lon], 
                radius=6, 
                color="blue", 
                fill=True, 
                fill_color="blue", 
                fill_opacity=0.8
            ).add_to(m)

    # Відображення карти
    map_data = st_folium(m, width="100%", height=750, key="main_map")

    # Оновлення координат при кліку
    if map_data.get("last_clicked"):
        if st.session_state.clicked_coords != map_data["last_clicked"]:
            st.session_state.clicked_coords = map_data["last_clicked"]
            st.rerun()
