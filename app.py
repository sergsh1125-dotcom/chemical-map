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
st.title("🧪 Карта хімічної обстановки")

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
        
        st.info(f"📍 Обрано точку:\n**Lat:** {c_lat:.6f}, **Lon:** {c_lon:.6f}")
        
        c1, c2 = st.columns(2)
        # Функція завантаження саме цих координат
        clicked_df = pd.DataFrame([{"lat": c_lat, "lon": c_lon}])
        csv = clicked_df.to_csv(index=False).encode('utf-8')
        c1.download_button("💾 Завантажити координати", csv, "coords.csv", "text/csv", use_container_width=True)
        
        if c2.button("✏️ Вставити в форму", use_container_width=True):
            st.session_state.manual_lat = c_lat
            st.session_state.manual_lon = c_lon
            st.rerun()
    else:
        st.write("👆 *Клікніть на будь-яке місце на карті, щоб отримати координати*")

    st.divider()

    # СЕКЦІЯ ДОДАВАННЯ ТОЧКИ
    st.markdown("### ➕ Додати точку вручну")
    
    # Використовуємо значення з сесії, якщо вони там є (після кліку)
    default_lat = st.session_state.get('manual_lat', 50.4501)
    default_lon = st.session_state.get('manual_lon', 30.5234)

    substance = st.text_input("Назва речовини", placeholder="Наприклад: Хлор")
    lat_input = st.number_input("Широта (lat)", format="%.6f", value=default_lat)
    lon_input = st.number_input("Довгота (lon)", format="%.6f", value=default_lon)
    
    value = st.number_input("Концентрація (мг/м³)", min_value=0.0, step=0.00001, format="%.5f")
    time_input = st.text_input("Дата та час", value=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))

    if st.button("✅ Додати на карту", use_container_width=True):
        new_row = pd.DataFrame([{"lat": lat_input, "lon": lon_input, "substance": substance, "value": value, "time": time_input}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.toast(f"Дані додано!")
        st.rerun()

    st.divider()
    
    # ФУНКЦІЇ ОЧИЩЕННЯ ТА CSV
    uploaded = st.file_uploader("📂 Імпорт CSV", type=["csv"])
    if uploaded:
        file_df = pd.read_csv(uploaded)
        if st.button("📥 Завантажити CSV на карту"):
            st.session_state.data = pd.concat([st.session_state.data, file_df], ignore_index=True)
            st.rerun()

    if st.button("🧹 Очистити все", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.session_state.clicked_coords = None
        st.rerun()

# ===============================
# Візуалізація на карті
# ===============================
with col_map:
    # Визначаємо центр
    if not st.session_state.data.empty:
        center_lat, center_lon, zoom = st.session_state.data.lat.mean(), st.session_state.data.lon.mean(), 11
    else:
        center_lat, center_lon, zoom = 50.4501, 30.5234, 10

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, control_scale=True)

    # Наносимо існуючі дані
    if not st.session_state.data.empty:
        df = st.session_state.data.copy()
        df['time_dt'] = pd.to_datetime(df['time'], errors='coerce')
        df['day_label'] = df['time_dt'].dt.date.astype(str)
        
        for day in sorted(df['day_label'].unique()):
            layer = folium.FeatureGroup(name=f"📅 {day}")
            day_data = df[df['day_label'] == day]
            for _, r in day_data.iterrows():
                val_formatted = f"{r['value']:.5f}".rstrip('0').rstrip('.')
                folium.map.Marker(
                    [r.lat, r.lon],
                    icon=folium.DivIcon(icon_anchor=(-15, 7),
                    html=f"""<div style="font-family: sans-serif; font-size: 11pt; color: blue; font-weight: bold; white-space: nowrap;">{r['substance']}: {val_formatted}</div>""")
                ).add_to(layer)
                folium.CircleMarker([r.lat, r.lon], radius=7, color="blue", fill=True, fill_opacity=0.8).add_to(layer)
            layer.add_to(m)
        folium.LayerControl(collapsed=False).add_to(m)

    # ВІДОБРАЖЕННЯ КАРТИ ТА ЗАХОПЛЕННЯ КЛІКУ
    map_data = st_folium(m, width="100%", height=750, key="main_map")

    # Оновлення вибраних координат при кліку
    if map_data.get("last_clicked"):
        if st.session_state.clicked_coords != map_data["last_clicked"]:
            st.session_state.clicked_coords = map_data["last_clicked"]
            st.rerun()
