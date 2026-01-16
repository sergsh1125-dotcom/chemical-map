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
1. **Назва речовини:** Вказуйте назву (Хлор, Аміак тощо) при ручному введенні. 
2. **Ручне введення:** Заповніть координати, концентрацію та час. Натисніть "Додати на карту".
3. **Завантаження файлу:** Виберіть CSV (стовпці: `lat`, `lon`, `substance`, `value`, `time`).
4. **Запобіжник:** Якщо на карті вже є дані, програма запропонує або об'єднати їх з новими, або повністю замінити.
5. **Візуалізація:** Всі точки та підписи відображаються **синім кольором** без зайвих рамок.
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

    # --- СЕКЦІЯ 1: Ручне додавання ---
    st.markdown("### ➕ Додати точку вручну")
    substance = st.text_input("Назва речовини", placeholder="Наприклад: Хлор")
    lat = st.number_input("Широта (lat)", format="%.6f", value=50.4501)
    lon = st.number_input("Довгота (lon)", format="%.6f", value=30.5234)
    
    value = st.number_input("Концентрація (мг/м³)", min_value=0.0, step=0.01, format="%.2f")
    time = st.text_input("Час вимірювання", placeholder="14:00")

    if st.button("➕ Додати на карту", use_container_width=True):
        new_row = pd.DataFrame([{"lat": lat, "lon": lon, "substance": substance, "value": value, "time": time}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.toast(f"Дані по {substance} додано!")

    st.divider()

    # --- СЕКЦІЯ 2: Завантаження CSV із ЗАПОБІЖНИКОМ ---
    st.markdown("### 📂 Завантажити масив даних")
    uploaded = st.file_uploader("Виберіть CSV файл", type=["csv"])
    
    if uploaded:
        file_df = pd.read_csv(uploaded)
        
        if not st.session_state.data.empty:
            st.warning(f"На карті вже є {len(st.session_state.data)} точок. Оберіть дію:")
            cb1, cb2 = st.columns(2)
            
            if cb1.button("➕ Об'єднати дані"):
                st.session_state.data = pd.concat([st.session_state.data, file_df], ignore_index=True)
                st.success("Дані об'єднано!")
                st.rerun()
                
            if cb2.button("🔄 Замінити дані"):
                st.session_state.data = file_df
                st.success("Дані оновлено!")
                st.rerun()
        else:
            if st.button("📥 Завантажити файл на карту"):
                st.session_state.data = file_df
                st.success(f"Завантажено {len(file_df)} точок")
                st.rerun()

    st.divider()

    if st.button("🧹 Очистити карту", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.rerun()

# ===============================
# Візуалізація на карті
# ===============================
with col_map:
    if st.session_state.data.empty:
        st.info("Чекаю на дані для відображення хімічної обстановки...")
    else:
        df = st.session_state.data.copy()
        m = folium.Map(location=[df.lat.mean(), df.lon.mean()], zoom_start=11, control_scale=True)

        for _, r in df.iterrows():
            # Синій напис без фонових полів
            label_text = f"{r['substance']}: {r['value']} мг/м³ | {r['time']}"
            
            folium.map.Marker(
                [r.lat, r.lon],
                icon=folium.DivIcon(
                    icon_anchor=(-15, 7),
                    html=f"""<div style="font-family: sans-serif; font-size: 11pt; color: blue; font-weight: bold; white-space: nowrap;">{label_text}</div>"""
                )
            ).add_to(m)
            
            # Синя точка (хімічна небезпека)
            folium.CircleMarker(
                [r.lat, r.lon],
                radius=7,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.8
            ).add_to(m)

        st_folium(m, width="100%", height=650, key="chem_map")

        # Експорт у HTML
        m.save("chemical_map.html")
        with open("chemical_map.html", "rb") as f:
            st.download_button("💾 Завантажити хімічну карту (HTML)", f, file_name="chemical_map.html", use_container_width=True)
