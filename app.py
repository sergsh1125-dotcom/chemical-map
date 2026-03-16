import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# ===============================
# Налаштування сторінки
# ===============================
st.set_page_config(page_title="Chemical Hazard Map", layout="wide")

# Приховуємо елементи Streamlit
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stNumberInput input { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ===============================
# Стан програми
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# Зберігаємо значення полів введення в сесії для автозаповнення
if "form_lat" not in st.session_state:
    st.session_state.form_lat = 50.4501
if "form_lon" not in st.session_state:
    st.session_state.form_lon = 30.5234

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
    
    with st.form("add_point_form", clear_on_submit=False):
        st.markdown("### Нанесення точки")
        substance = st.text_input("Назва хімічної речовини", placeholder="Наприклад: Хлор")
        
        # Поля, які оновлюються при кліку на карту
        lat_val = st.number_input("Широта", format="%.6f", value=st.session_state.form_lat)
        lon_val = st.number_input("Довгота", format="%.6f", value=st.session_state.form_lon)
        
        concentration = st.number_input("Концентрація (мг/куб. м)", min_value=0.0, step=0.001, format="%.4f")
        
        # Дата за замовчуванням сьогодні
        date_input = st.date_input("Дата вимірювання", datetime.now())
        
        submit_button = st.form_submit_button("Нанести на карту", use_container_width=True)

    if submit_button:
        new_date = date_input.strftime("%d.%m.%Y")
        new_row = pd.DataFrame([{
            "lat": lat_val, 
            "lon": lon_val, 
            "substance": substance, 
            "value": concentration, 
            "time": new_date
        }])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.success("Точку додано")
        st.rerun()

    st.divider()
    
    if st.button("Очистити карту", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.session_state.clicked_coords = None
        st.rerun()

# ===============================
# Візуалізація карти
# ===============================
with col_map:
    # Базові налаштування центру
    m = folium.Map(
        location=[st.session_state.form_lat, st.session_state.form_lon], 
        zoom_start=10, 
        control_scale=True
    )

    # 1. Обробка кліку: малюємо тимчасове віконце з координатами
    if st.session_state.clicked_coords:
        c_lat = st.session_state.clicked_coords['lat']
        c_lng = st.session_state.clicked_coords['lng']
        
        folium.Marker(
            [c_lat, c_lng],
            popup=folium.Popup(f"Координати захоплено:<br><b>{c_lat:.5f}, {c_lng:.5f}</b>", max_width=200, show=True),
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

    # 2. Нанесення існуючих точок обстановки
    if not st.session_state.data.empty:
        for _, r in st.session_state.data.iterrows():
            val_fmt = f"{r['value']:.4f}".rstrip('0').rstrip('.')
            
            # Створення дворядкового напису з рискою
            label_html = f"""
            <div style="
                font-family: Arial, sans-serif; 
                font-size: 10pt; 
                color: black; 
                background-color: rgba(255,255,255,0.8);
                border: 1px solid gray;
                padding: 3px;
                border-radius: 3px;
                white-space: nowrap;
                text-align: center;
                line-height: 1.2;
            ">
                <b>{r['substance']} — {val_fmt} мг/куб. м</b>
                <hr style="margin: 2px 0; border: 0; border-top: 1px solid black;">
                {r['time']}
            </div>
            """
            
            # Текстовий напис над точкою
            folium.map.Marker(
                [r.lat, r.lon],
                icon=folium.DivIcon(
                    icon_anchor=(60, 45), # Зміщення, щоб напис був над точкою
                    html=label_html
                )
            ).add_to(m)
            
            # Сама точка (кружечок)
            folium.CircleMarker(
                [r.lat, r.lon],
                radius=6,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.9
            ).add_to(m)

    # Відображення карти та зчитування подій
    map_output = st_folium(m, width="100%", height=750, key="chem_map_main")

    # Обробка логіки кліку
    if map_output.get("last_clicked"):
        clicked = map_output["last_clicked"]
        # Перевіряємо, чи це новий клік
        if st.session_state.clicked_coords != clicked:
            st.session_state.clicked_coords = clicked
            # Завантажуємо в пульт управління
            st.session_state.form_lat = clicked['lat']
            st.session_state.form_lon = clicked['lng']
            st.rerun()
