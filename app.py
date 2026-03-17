import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# ===============================
# 1. Налаштування сторінки
# ===============================
st.set_page_config(page_title="Chemical Map Pro", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stButton button {font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# Стан програми
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

st.title("Карта хімічної обстановки")
col_map, col_gui = st.columns([2.5, 1])

# ===============================
# 2. Пульт управління
# ===============================
with col_gui:
    st.subheader("Пульт управління")
    if st.session_state.clicked_coords:
        c_lat, c_lon = st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']
        st.write(f"Вибрано: {c_lat:.6f}, {c_lon:.6f}")
        r1, r2 = st.columns(2)
        if r1.button("вставити координати у форму", use_container_width=True):
            st.session_state.manual_lat, st.session_state.manual_lon = c_lat, c_lon
            st.rerun()
        if r2.button("виключити маркер на карті", use_container_width=True):
            st.session_state.clicked_coords = None
            st.rerun()

    st.divider()
    st.markdown("### Нанесення точки вимірювання вручну")
    with st.container(border=True):
        substance = st.text_input("Назва хімічної речовини", placeholder="Хлор")
        v_lat = st.number_input("Широта", format="%.6f", value=st.session_state.get('manual_lat', 50.4501))
        v_lon = st.number_input("Довгота", format="%.6f", value=st.session_state.get('manual_lon', 30.5234))
        concentration = st.number_input("Концентрація (мг/м³)", format="%.4f", step=0.001)
        date_input = st.text_input("Дата вимірювання", value=datetime.now().strftime("%d.%m.%Y"))

        if st.button("Нанести на карту", use_container_width=True):
            new_entry = pd.DataFrame([{"lat": v_lat, "lon": v_lon, "substance": substance, "value": concentration, "time": date_input}])
            st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
            st.rerun()

    st.divider()
    st.markdown("### Нанесення точок вимірювання з таблиці")
    uploaded_file = st.file_uploader("Виберіть файл CSV", type="csv", label_visibility="collapsed")
    if uploaded_file and st.button("завантажити з файлу csv", use_container_width=True):
        st.session_state.data = pd.concat([st.session_state.data, pd.read_csv(uploaded_file)], ignore_index=True)
        st.rerun()

    if st.button("Очистити карту", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.session_state.clicked_coords = None
        st.rerun()

# ===============================
# 3. Візуалізація на карті
# ===============================
with col_map:
    center = [st.session_state.data.lat.iloc[-1], st.session_state.data.lon.iloc[-1]] if not st.session_state.data.empty else [50.4501, 30.5234]
    
    # Створюємо порожню карту
    m = folium.Map(location=center, zoom_start=10, tiles=None, control_scale=True)

    # 1. ПЕРШИМ додаємо OSM і ставимо show=True
    folium.TileLayer('OpenStreetMap', name='Стандартна карта', control=True, show=True).add_to(m)
    
    # 2. ДРУГИМ додаємо Супутник і ставимо show=False
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite', name='Супутник', control=True, show=False
    ).add_to(m)

    if st.session_state.clicked_coords:
        folium.Marker([st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']], icon=folium.Icon(color="red")).add_to(m)

    if not st.session_state.data.empty:
        for d in st.session_state.data['time'].unique():
            group = folium.FeatureGroup(name=f"Дата: {d}")
            day_data = st.session_state.data[st.session_state.data['time'] == d]
            for _, r in day_data.iterrows():
                val_f = f"{r['value']:.4f}".rstrip('0').rstrip('.')
                
                # HTML БЕЗ прямокутників: риска через border-bottom
                label_html = f"""
                <div style="
                    font-family: 'Arial', sans-serif; font-size: 10pt; color: blue; font-weight: bold;
                    text-align: center; background-color: rgba(255, 255, 255, 0.9);
                    padding: 4px 8px; border-radius: 4px; border: 1.2px solid blue;
                    display: inline-block; white-space: nowrap; box-shadow: 2px 2px 8px rgba(0,0,0,0.4);
                ">
                    <div style="border-bottom: 2px solid blue; padding-bottom: 2px; margin-bottom: 2px;">
                        {r['substance']} — {val_f} мг/м³
                    </div>
                    <div>{r['time']}</div>
                </div>
                """
                folium.CircleMarker([r.lat, r.lon], radius=6, color="blue", fill=True, fill_opacity=1).add_to(group)
                folium.map.Marker([r.lat, r.lon], icon=folium.DivIcon(icon_anchor=(70, 50), html=label_html)).add_to(group)
            group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    map_output = st_folium(m, width="100%", height=700, key="main_map")

    if map_output.get("last_clicked") and st.session_state.clicked_coords != map_output["last_clicked"]:
        st.session_state.clicked_coords = map_output["last_clicked"]
        st.rerun()

# ===============================
# 4. Таблиця
# ===============================
st.divider()
if not st.session_state.data.empty:
    ed_df = st.data_editor(st.session_state.data, use_container_width=True, num_rows="dynamic")
    if not ed_df.equals(st.session_state.data):
        st.session_state.data = ed_df
        st.rerun()
    
    c1, c2 = st.columns(2)
    c1.download_button("Завантажити карту в HTML", m._repr_html_(), "map.html", "text/html", use_container_width=True)
    c2.download_button("Зберегти таблицю в CSV", st.session_state.data.to_csv(index=False), "data.csv", "text/csv", use_container_width=True)
