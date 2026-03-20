import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ===============================
# Налаштування сторінки
# ===============================
st.set_page_config(
    page_title="Chemical Hazard Map",
    layout="wide"
)

# Приховуємо зайві елементи інтерфейсу Streamlit
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

if "show_instructions" not in st.session_state:
    st.session_state.show_instructions = False

# ===============================
# Заголовок
# ===============================
st.title("🧪 Карта хімічної обстановки")

# ===============================
# Інструкція користування
# ===============================
if st.button("ℹ️ Інструкція користування", use_container_width=True):
    st.session_state.show_instructions = not st.session_state.show_instructions

if st.session_state.show_instructions:
    st.success("""
**Порядок роботи з хімічною картою:**
1. **Назва речовини:** Вказуйте назву (Хлор, Аміак тощо).
2. **Числа:** Нулі після коми автоматично приховуються для кращої читаємості.
3. **Черговість:** Ви можете додавати точки вручну до або після завантаження CSV — шари працюватимуть коректно.
4. **Шари:** Кожен день виділяється в окремий шар, який можна вимкнути в меню на карті.
""")

# ===============================
# Розподіл екрану
# ===============================
col_map, col_gui = st.columns([2.5, 1])

# ===============================
# Права панель (GUI)
# ===============================
with col_gui:
    st.subheader("⚙️ Управління даними")

    st.markdown("### ➕ Додати точку вручну")
    substance = st.text_input("Назва речовини", placeholder="Наприклад: Хлор")
    lat = st.number_input("Широта (lat)", format="%.6f", value=50.4501)
    lon = st.number_input("Довгота (lon)", format="%.6f", value=30.5234)
    
    # Введення до 5 знаків, але відображення без зайвих нулів
    value = st.number_input(
        "Концентрація (мг/м³)", 
        min_value=0.0, 
        step=0.00001, 
        format="%.5f"
    )
    time_input = st.text_input("Дата та час", placeholder="2026-01-16 14:00")

    if st.button("➕ Додати на карту", use_container_width=True):
        new_row = pd.DataFrame([{"lat": lat, "lon": lon, "substance": substance, "value": value, "time": time_input}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.toast(f"Дані по {substance} додано!")

    st.divider()

    st.markdown("### 📂 Завантажити масив даних")
    uploaded = st.file_uploader("Виберіть CSV файл", type=["csv"])
    
    if uploaded:
        file_df = pd.read_csv(uploaded)
        if not st.session_state.data.empty:
            st.warning(f"На карті вже є {len(st.session_state.data)} точок. Оберіть дію:")
            cb1, cb2 = st.columns(2)
            if cb1.button("➕ Об'єднати дані"):
                st.session_state.data = pd.concat([st.session_state.data, file_df], ignore_index=True)
                st.rerun()
            if cb2.button("🔄 Замінити дані"):
                st.session_state.data = file_df
                st.rerun()
        else:
            if st.button("📥 Завантажити на карту"):
                st.session_state.data = file_df
                st.rerun()

    st.divider()
    if st.button("🧹 Очистити карту", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.rerun()

# ===============================
# Візуалізація на карті (з фіксом шарів)
# ===============================
with col_map:
    if st.session_state.data.empty:
        st.info("Чекаю на дані...")
    else:
        df = st.session_state.data.copy()
        
        # КЛЮЧОВИЙ ФІКС: Конвертація часу для стабільної роботи шарів
        df['time_dt'] = pd.to_datetime(df['time'], errors='coerce')
        # Якщо дата не розпізнана, ставимо "Не вказано", інакше беремо дату дня
        df['day_label'] = df['time_dt'].dt.date.astype(str)
        df.loc[df['day_label'] == 'NaT', 'day_label'] = "Інша дата"

        m = folium.Map(location=[df.lat.mean(), df.lon.mean()], zoom_start=11, control_scale=True)
        
        unique_days = sorted(df['day_label'].unique())

        for day in unique_days:
            layer = folium.FeatureGroup(name=f"📅 Дата: {day}")
            day_data = df[df['day_label'] == day]

            for _, r in day_data.iterrows():
                # ФОРМАТУВАННЯ ЧИСЛА: видалення нулів в кінці
                val_formatted = f"{r['value']:.5f}".rstrip('0').rstrip('.')
                
                label_text = f"{r['substance']}: {val_formatted} мг/м³ | {r['time']}"
                
                folium.map.Marker(
                    [r.lat, r.lon],
                    icon=folium.DivIcon(
                        icon_anchor=(-15, 7),
                        html=f"""<div style="font-family: sans-serif; font-size: 11pt; color: blue; font-weight: bold; white-space: nowrap;">{label_text}</div>"""
                    )
                ).add_to(layer)
                
                folium.CircleMarker(
                    [r.lat, r.lon],
                    radius=7,
                    color="blue",
                    fill=True,
                    fill_color="blue",
                    fill_opacity=0.8
                ).add_to(layer)
            
            layer.add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        st_folium(m, width="100%", height=650, key="chem_map_layers_final")

        m.save("chemical_map.html")
        with open("chemical_map.html", "rb") as f:
            st.download_button("💾 Завантажити HTML карту", f, file_name="chemical_map.html", use_container_width=True)
