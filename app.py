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

# ===============================
# 2. Стан програми (Session State)
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# ===============================
# 3. Заголовок
# ===============================
st.title("Карта хімічної обстановки")

col_map, col_gui = st.columns([2.5, 1])

# ===============================
# 4. Права панель (Пульт управління)
# ===============================
with col_gui:
    st.subheader("Пульт управління")

    if st.session_state.clicked_coords:
        c_lat = st.session_state.clicked_coords['lat']
        c_lon = st.session_state.clicked_coords['lng']
        st.write(f"Вибрано: {c_lat:.6f}, {c_lon:.6f}")
        
        row1, row2 = st.columns(2)
        if row1.button("вставити координати у форму", use_container_width=True):
            st.session_state.manual_lat = c_lat
            st.session_state.manual_lon = c_lon
            st.rerun()
        
        if row2.button("виключити маркер на карті", use_container_width=True):
            st.session_state.clicked_coords = None
            st.rerun()

    st.divider()

    st.markdown("### Нанесення точки вимірювання вручну")
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

    st.markdown("### Нанесення точок вимірювання з таблиці")
    uploaded_file = st.file_uploader("Виберіть файл CSV", type="csv", label_visibility="collapsed")
    
    if uploaded_file:
        if st.button("завантажити з файлу csv", use_container_width=True):
            try:
                new_data = pd.read_csv(uploaded_file)
                st.session_state.data = pd.concat([st.session_state.data, new_data], ignore_index=True)
                st.rerun()
            except:
                st.error("Помилка файлу")

    if st.button("Очистити карту", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.session_state.clicked_coords = None
        st.rerun()

# ===============================
# 5. Візуалізація на карті
# ===============================
with col_map:
    if not st.session_state.data.empty:
        m_lat, m_lon = st.session_state.data.lat.iloc[-1], st.session_state.data.lon.iloc[-1]
    else:
        m_lat, m_lon = 50.4501, 30.5234

    # ГАРАНТОВАНО завантажуємо OpenStreetMap як основну
    m = folium.Map(location=[m_lat, m_lon], zoom_start=10, tiles='OpenStreetMap', control_scale=True)

    # Додаємо супутник як ОПЦІОНАЛЬНИЙ шар (overlay=False робить його перемикачем)
   # Базова карта (звичайна)
m = folium.Map(
    location=[m_lat, m_lon],
    zoom_start=10,
    tiles=None,  # ВАЖЛИВО: відключаємо автозавантаження
    control_scale=True
)

# Основна карта (буде за замовчуванням)
folium.TileLayer(
    'OpenStreetMap',
    name='Стандартна карта',
    overlay=False,
    control=True,
    show=True  # <-- ГАРАНТУЄ, що вона активна
).add_to(m)

# Супутникова (тільки як опція)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satellite',
    name='Супутник',
    overlay=False,
    control=True,
    show=False  # <-- ВАЖЛИВО: не активна при старті
).add_to(m)

    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red")
        ).add_to(m)

    if not st.session_state.data.empty:
        df = st.session_state.data.copy()
        for d in df['time'].unique():
            group = folium.FeatureGroup(name=f"Дата: {d}")
            day_data = df[df['time'] == d]
            
            for _, r in day_data.iterrows():
                val_f = f"{r['value']:.4f}".rstrip('0').rstrip('.')
                
                # Покращений HTML-підпис (без зайвих прямокутників, з чіткою лінією)
                label_html = f"""
                <div style="
                    font-family: 'Arial', sans-serif; 
                    font-size: 10pt; 
                    color: blue; 
                    font-weight: bold;
                    text-align: center;
                    background-color: rgba(255, 255, 255, 0.85);
                    padding: 5px;
                    border-radius: 5px;
                    border: 1.5px solid blue;
                    display: inline-block;
                    white-space: nowrap;
                    box-shadow: 3px 3px 10px rgba(0,0,0,0.3);
                ">
                    <div style="margin-bottom: 2px;">{r['substance']} — {val_f} мг/м³</div>
                    <div style="height: 2px; background-color: blue; width: 100%; margin: 2px 0;"></div>
                    <div style="margin-top: 2px;">{r['time']}</div>
                </div>
                """
                
                # Синя точка вимірювання
                folium.CircleMarker(
                    [r.lat, r.lon], radius=6, color="blue", fill=True, fill_opacity=1
                ).add_to(group)

                # Текстовий напис (Marker з DivIcon)
                folium.map.Marker(
                    [r.lat, r.lon],
                    icon=folium.DivIcon(
                        icon_anchor=(70, 50), 
                        html=label_html
                    )
                ).add_to(group)
            
            group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    map_data = st_folium(m, width="100%", height=700, key="main_map")

    if map_data.get("last_clicked"):
        if st.session_state.clicked_coords != map_data["last_clicked"]:
            st.session_state.clicked_coords = map_data["last_clicked"]
            st.rerun()

# ===============================
# 6. Таблиця та Експорт
# ===============================
st.divider()
t_col1, t_col2 = st.columns([3, 1])

with t_col1:
    st.subheader("Список нанесених точок вимірювання")
    if not st.session_state.data.empty:
        edited_df = st.data_editor(
            st.session_state.data,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "lat": st.column_config.NumberColumn("Широта", format="%.6f"),
                "lon": st.column_config.NumberColumn("Довгота", format="%.6f"),
                "value": st.column_config.NumberColumn("мг/м³", format="%.4f"),
            }
        )
        if not edited_df.equals(st.session_state.data):
            st.session_state.data = edited_df
            st.rerun()

with t_col2:
    st.subheader("Експорт")
    if not st.session_state.data.empty:
        html_data = m._repr_html_()
        st.download_button(
            label="Завантажити карту в HTML",
            data=html_data,
            file_name="chem_map.html",
            mime="text/html",
            use_container_width=True
        )
        csv_data = st.session_state.data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Зберегти таблицю в CSV",
            data=csv_data,
            file_name="chem_data.csv",
            mime="text/csv",
            use_container_width=True
        )
