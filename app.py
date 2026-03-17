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
/* Стиль для жирного тексту в інпутах */
.stTextInput font-weight: bold;
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

col_map, col_gui = st.columns([2.5, 1])

# ===============================
# Права панель (Пульт управління)
# ===============================
with col_gui:
    st.subheader("⚙️ Пульт управління")

    # 1. Робота з обраною точкою
    if st.session_state.clicked_coords:
        c_lat = st.session_state.clicked_coords['lat']
        c_lon = st.session_state.clicked_coords['lng']
        st.info(f"📍 Обрано: {c_lat:.6f}, {c_lon:.6f}")
        
        row1, row2 = st.columns(2)
        if row1.button("✏️ Вставити у форму", use_container_width=True):
            st.session_state.manual_lat = c_lat
            st.session_state.manual_lon = c_lon
        
        if row2.button("❌ Прибрати маркер", use_container_width=True):
            st.session_state.clicked_coords = None
            st.rerun()

    st.divider()

    # 2. Форма додавання точки
    st.markdown("### ➕ Нанесення точки")
    with st.container(border=True):
        substance = st.text_input("Хімічна речовина", placeholder="Хлор", key="sub_in")
        
        val_lat = st.number_input("Широта", format="%.6f", value=st.session_state.get('manual_lat', 50.4501))
        val_lon = st.number_input("Довгота", format="%.6f", value=st.session_state.get('manual_lon', 30.5234))
        
        concentration = st.number_input("Концентрація (мг/м³)", format="%.4f", step=0.001)
        
        # Автоматична дата (як на комп'ютері) з можливістю редагування
        current_date = datetime.now().strftime("%d.%m.%Y")
        date_input = st.text_input("Дата вимірювання", value=current_date)

        if st.button("🚀 Нанести на карту", use_container_width=True):
            new_entry = pd.DataFrame([{
                "lat": val_lat, "lon": val_lon, 
                "substance": substance, "value": concentration, 
                "time": date_input
            }])
            st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
            st.rerun()

    st.divider()

    # 3. Кнопки управління файлами
    st.markdown("### 📂 Робота з даними")
    
    # Завантаження CSV
    uploaded_file = st.file_uploader("Виберіть файл CSV", type="csv", label_visibility="collapsed")
    if uploaded_file:
        if st.button("📥 Завантажити з файлу CSV", use_container_width=True):
            new_data = pd.read_csv(uploaded_file)
            st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
            st.rerun()

    # Збереження HTML (створюємо карту окремо для експорту)
    if not st.session_state.data.empty:
        if st.button("💾 Зберегти карту в HTML", use_container_width=True):
            # Тут ми просто створюємо буфер, функція збереження нижче
            st.info("Карта готова до завантаження під цим повідомленням")

    if st.button("🧹 Очистити карту", use_container_width=True):
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

    # Створення карти з декількома шарами
    m = folium.Map(location=[m_lat, m_lon], zoom_start=10, control_scale=True)

    # Додаємо шар Супутник
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Супутник (Google)',
        overlay=False,
        control=True
    ).add_to(m)
    folium.TileLayer('OpenStreetMap', name='Стандартна карта').add_to(m)

    # Відображення маркера вибору (червоний)
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            popup=f"Координати: {st.session_state.clicked_coords['lat']:.5f}, {st.session_state.clicked_coords['lng']:.5f}",
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
        ).add_to(m)

    # Нанесення точок обстановки по дням
    if not st.session_state.data.empty:
        df = st.session_state.data.copy()
        # Групування за датами для легенди
        dates = df['time'].unique()
        
        for d in dates:
            group = folium.FeatureGroup(name=f"📅 Дата: {d}")
            day_data = df[df['time'] == d]
            
            for _, r in day_data.iterrows():
                val_f = f"{r['value']:.4f}".rstrip('0').rstrip('.')
                
                # HTML напис: СИНІЙ, ЖИРНИЙ, З РИСКОЮ
                label_html = f"""
                <div style="
                    font-family: 'Arial', sans-serif; 
                    font-size: 11pt; 
                    color: blue; 
                    font-weight: bold;
                    white-space: nowrap;
                    text-align: center;
                    background: rgba(255,255,255,0.7);
                    padding: 2px;
                    border-radius: 4px;
                ">
                    {r['substance']} — {val_f} мг/м³
                    <hr style="border: none; border-top: 2px solid blue; margin: 2px 0;">
                    {r['time']}
                </div>
                """
                
                # Напис над точкою
                folium.map.Marker(
                    [r.lat, r.lon],
                    icon=folium.DivIcon(
                        icon_anchor=(70, 50),
                        html=label_html
                    )
                ).add_to(group)
                
                # Синя точка
                folium.CircleMarker(
                    [r.lat, r.lon],
                    radius=6,
                    color="blue",
                    fill=True,
                    fill_opacity=1
                ).add_to(group)
            
            group.add_to(m)

    # Додаємо контроль шарів (Легенда)
    folium.LayerControl(collapsed=False).add_to(m)

    # Відображення в Streamlit
    map_data = st_folium(m, width="100%", height=750, key="main_map")

    # Обробка кліку
    if map_data.get("last_clicked"):
        if st.session_state.clicked_coords != map_data["last_clicked"]:
            st.session_state.clicked_coords = map_data["last_clicked"]
            st.rerun()

    # Кнопка збереження HTML (якщо дані є)
    if not st.session_state.data.empty:
        html_data = m._repr_html_()
        with col_gui:
            st.download_button(
                label="📥 Натисніть для завантаження HTML",
                data=html_data,
                file_name="chemical_map_export.html",
                mime="text/html",
                use_container_width=True
            )
