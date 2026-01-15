import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ===============================
# Налаштування сторінки
# ===============================
st.set_page_config(
    page_title="Chemical Situation Map",
    layout="wide"
)

# Приховуємо меню та футер
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
    st.session_state.data = pd.DataFrame(columns=["lat","lon","value","time"])

# Виправлено: Порожній рядок замість "Хлор" при завантаженні
if "substance" not in st.session_state:
    st.session_state.substance = ""

# Стан для відображення інструкції (відкрито/закрито)
if "show_instructions" not in st.session_state:
    st.session_state.show_instructions = False

# ===============================
# Заголовок
# ===============================
st.title("🧪 Карта хімічної обстановки")

# ===============================
# Інструкція користування (з функцією перемикання)
# ===============================
if st.button("ℹ️ Інструкція користування", use_container_width=True):
    # Перемикаємо стан: якщо було True, стане False, і навпаки
    st.session_state.show_instructions = not st.session_state.show_instructions

if st.session_state.show_instructions:
    st.info("""
**Призначення:** Програма дозволяє візуалізувати хімічну обстановку, відображаючи точки вимірювань концентрації небезпечної речовини на карті.  

**Можливості програми:** - Додавати точки вручну або завантажувати CSV  
- Відображати назву речовини, концентрацію та час вимірювання  
- Завантажувати готову карту у форматі HTML  

**Алгоритм завантаження та введення даних:** 1. Введіть назву речовини у полі “Назва небезпечної речовини”.  
2. Додайте точку вручну (lat, lon, концентрація, час) або завантажте CSV із колонками: `lat`, `lon`, `value`, `time`.  
3. Дані автоматично з’являються на карті.  

**Вихідні дані:** - Карта Folium з позначками точок  
- HTML-файл карти для подальшого використання  
- Підписи біля точок: назва речовини – концентрація, дата/час вимірювання
""")

# ===============================
# Розділення екрану
# ===============================
col_map, col_gui = st.columns([2.2, 1])

# ===============================
# Права панель (GUI)
# ===============================
with col_gui:
    st.subheader("⚙️ Ввід даних")

    st.session_state.substance = st.text_input(
        "Назва речовини",
        st.session_state.substance,
        placeholder="Наприклад: Хлор"
    )

    st.markdown("### ➕ Додати точку вручну")
    lat = st.number_input("Широта (lat)", format="%.6f", value=50.4501)
    lon = st.number_input("Довгота (lon)", format="%.6f", value=30.5234)
    value = st.number_input("Концентрація (мг/куб.м)", min_value=0.0, step=0.01)
    time = st.text_input("Час вимірювання", placeholder="2026-01-15 12:30")

    if st.button("➕ Додати точку", use_container_width=True):
        new_row = pd.DataFrame([{"lat": lat, "lon": lon, "value": value, "time": time}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)

    st.divider()

    uploaded = st.file_uploader("📂 Завантажити CSV", type=["csv"])
    if uploaded:
        st.session_state.data = pd.read_csv(uploaded)
        st.success(f"Завантажено {len(st.session_state.data)} точок")

    if st.button("🧹 Очистити всі дані", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat","lon","value","time"])
        st.rerun()

# ===============================
# Карта
# ===============================
with col_map:
    if st.session_state.data.empty:
        st.info("Немає даних для відображення. Додайте точки через панель праворуч.")
    else:
        df = st.session_state.data.copy()
        m = folium.Map(location=[df.lat.mean(), df.lon.mean()], zoom_start=10, control_scale=True)

        for _, r in df.iterrows():
            # Виправлено: колір тексту та ліній змінено на синій (blue)
            label_html = f"""
            <div style="
                color: blue;
                font-size: 14px;
                font-weight: bold;
                white-space: nowrap;
                background-color: rgba(255,255,255,0.7);
                padding: 2px;
                border-radius: 3px;
            ">
                {st.session_state.substance} – {r['value']:.2f} мг/куб.м
                <hr style="margin:2px 0; border:1px solid blue;">
                {r['time']}
            </div>
            """
            
            # Виправлено: колір точок змінено на синій (blue)
            folium.CircleMarker(
                [r.lat, r.lon],
                radius=8,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.7
            ).add_to(m)

            folium.Marker(
                [r.lat, r.lon],
                icon=folium.DivIcon(icon_anchor=(0, -15), html=label_html)
            ).add_to(m)

        st_folium(m, width="100%", height=600, key="map")

        # HTML експорт
        m.save("chemical_map.html")
        with open("chemical_map.html", "rb") as f:
            st.download_button(
                "💾 Завантажити карту (HTML)",
                f,
                file_name="chemical_map.html",
                mime="text/html",
                use_container_width=True
            )
