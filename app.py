import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import io

# ===============================
# Налаштування сторінки
# ===============================
st.set_page_config(page_title="Chemical Map Pro", layout="wide")

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

col_map, col_gui = st.columns([2.5, 1])

# ===============================
# Права панель (Пульт управління)
# ===============================
with col_gui:
    st.subheader("Пульт управління")

    # 1. Робота з обраною точкою
    if st.session_state.clicked_coords:
        c_lat = st.session_state.clicked_coords['lat']
        c_lon = st.session_state.clicked_coords['lng']
        st.write(f"Координати: {c_lat:.6f}, {c_lon:.6f}")
        
        row1, row2 = st.columns(2)
        if row1.button("вставити координати у форму", use_container_width=True):
            st.session_state.manual_lat = c_lat
            st.session_state.manual_lon = c_lon
        
        if row2.button("виключити маркер на карті", use_container_width=True):
            st.session_state.clicked_coords = None
            st.rerun()

    st.divider()

    # 2. Форма додавання точки
    st.markdown("### Нанесення точки ідентифікації НХР")
    with st.container(border=True):
        substance = st.text_input("Назва хімічної речовини", placeholder="Хлор")
        
        val_lat = st.number_input("Широта", format="%.6f", value=st.session_state.get('manual_lat', 50.4501))
        val_lon = st.number_input("Довгота", format="%.6f", value=st.session_state.get('manual_lon', 30.5234))
        
        concentration = st.number_input("Концентрація (мг/м³)", format="%.4f", step=0.001)
        
        current_date = datetime.now().strftime("%d.%m.%Y")
        date_input = st.text_input("Дата вимірювання", value=current_date)

        if st.button("Нанести на карту", use_container_width=True):
            new_entry = pd.DataFrame([{
                "lat": val_lat, "lon": val_lon, 
                "substance": substance, "value": concentration, 
                "time": date_input
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
            st.rerun()

    st.divider()

    # 3. Кнопки управління даними
    st.markdown("### Робота з даними")
    
    uploaded_file = st.file_uploader("Виберіть файл CSV", type="csv", label_visibility="collapsed")
    if uploaded_file:
        if st.button("завантажити з файлу csv", use_container_width=True):
            try:
                # Очікуємо колонки: lat, lon, substance, value, time
                new_data = pd.read_csv(uploaded_file)
                st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
                st.success("Дані завантажено")
                st.rerun()
            except Exception as e:
                st.error("Помилка структури CSV")

    if st.button("Очистити карту", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.session_state.clicked_coords = None
        st.rerun()

# ===============================
# Візуалізація на карті
# ===============================
with col_map:
    # Налаштування центру
    if not st.session_state.data.empty:
        m_lat, m_lon = st.session_state.data.lat.iloc[-1], st.session_state.data.lon.iloc[-1]
    else:
        m_lat, m_lon = 50.4501, 30.5234

    m = folium.Map(location=[m_lat, m_lon], zoom_start=10, control_scale=True)

    # Залишаємо Google Satellite та одну базову карту
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Супутник',
        overlay=False,
        control=True
    ).add_to(m)
    folium.TileLayer('OpenStreetMap', name='Стандартна карта').add_to(m)

    # Відображення червоного маркера вибору
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            popup=f"Координати: {st.session_state.clicked_coords['lat']:.5f}, {st.session_state.clicked_coords['lng']:.5f}",
            icon=folium.Icon(color="red")
        ).add_to(m)

    # Нанесення точок обстановки
    if not st.session_state.data.empty:
        df = st.session_state.data.copy()
        dates = df['time'].unique()
        
        for d in dates:
            group = folium.FeatureGroup(name=f"Дата: {d}")
            day_data = df[df['time'] == d]
            
            for _, r in day_data.iterrows():
                val_f = f"{r['value']:.4f}".rstrip('0').rstrip('.')
                
                # HTML напис: СИНІЙ, ЖИРНИЙ, ЦЕНТРОВАНИЙ, ШРИФТ 10pt
                label_html = f"""
                <div style="
                    font-family: 'Arial', sans-serif; 
                    font-size: 10pt; 
                    color: blue; 
                    font-weight: bold;
                    white-space: nowrap;
                    text-align: center;
                    background: rgba(255,255,255,0.6);
                    padding: 2px;
                    border-radius: 3px;
                    line-height: 1.1;
                ">
                    {r['substance']} — {val_f} мг/м³
                    <hr style="border: none; border-top: 1.5px solid blue; margin: 1px 0;">
                    {r['time']}
                </div>
                """
                
                folium.map.Marker(
                    [r.lat, r.lon],
                    icon=folium.DivIcon(
                        icon_anchor=(65, 45),
                        html=label_html
                    )
                ).add_to(group)
                
                folium.CircleMarker(
                    [r.lat, r.lon],
                    radius=6,
                    color="blue",
                    fill=True,
                    fill_opacity=1
                ).add_to(group)
            
            group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    # Відображення
    map_data = st_folium(m, width="100%", height=750, key="main_map")

    # Обробка кліку
    if map_data.get("last_clicked"):
        if st.session_state.clicked_coords != map_data["last_clicked"]:
            st.session_state.clicked_coords = map_data["last_clicked"]
            st.rerun()

    # Експорт у HTML
    if not st.session_state.data.empty:
        html_data = m._repr_html_()
        with col_gui:
            st.download_button(
                label="Завантажити карту в HTML",
                data=html_data,
                file_name="chemical_map.html",
                mime="text/html",
                use_container_width=True
            )
