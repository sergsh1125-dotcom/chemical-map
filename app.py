import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from branca.element import DivIcon

# ===============================
# Налаштування сторінки
# ===============================
st.set_page_config(page_title="Хімічна обстановка", layout="wide")
st.title("🧪 Карта хімічної обстановки")

# ===============================
# Session state
# ===============================
if "measurements" not in st.session_state:
    st.session_state.measurements = []

# ===============================
# Ввід назви речовини
# ===============================
substance = st.text_input(
    "Назва небезпечної хімічної речовини",
    value="Хлор"
)

# ===============================
# Форма ручного введення
# ===============================
st.subheader("➕ Додати точку вимірювання")

with st.form("input_form"):
    col1, col2 = st.columns(2)

    with col1:
        lat = st.number_input("Широта (lat)", format="%.6f")
        value = st.number_input("Концентрація, мг/м³", min_value=0.0, step=0.01)

    with col2:
        lon = st.number_input("Довгота (lon)", format="%.6f")
        time = st.text_input("Дата і час вимірювання", "2026-01-09 12:00")

    submitted = st.form_submit_button("➕ Додати")

    if submitted:
        st.session_state.measurements.append({
            "lat": lat,
            "lon": lon,
            "value": value,
            "time": time
        })
        st.success("Точку додано")

# ===============================
# Завантаження CSV
# ===============================
st.subheader("📂 Завантажити CSV")
uploaded_file = st.file_uploader("CSV файл (lat, lon, value, time)", type="csv")

if uploaded_file:
    df_csv = pd.read_csv(uploaded_file)
    df_csv[['lat','lon','value']] = df_csv[['lat','lon','value']].apply(pd.to_numeric, errors="coerce")
    df_csv = df_csv.dropna()

    for _, r in df_csv.iterrows():
        st.session_state.measurements.append({
            "lat": r.lat,
            "lon": r.lon,
            "value": r.value,
            "time": r.time
        })

    st.success(f"Завантажено {len(df_csv)} точок")

# ===============================
# Функція кольору
# ===============================
def get_color(v):
    if v < 0.1:
        return "green"
    elif v < 0.5:
        return "orange"
    else:
        return "red"

# ===============================
# Побудова карти
# ===============================
def build_map(df):
    m = folium.Map(
        location=[df.lat.mean(), df.lon.mean()],
        zoom_start=14,
        control_scale=True
    )

    for _, r in df.iterrows():
        color = get_color(r.value)

        # Точка
        folium.CircleMarker(
            [r.lat, r.lon],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8
        ).add_to(m)

        # Підпис
        label_html = f"""
        <div style="
            font-size:12px;
            color:black;
            background-color: rgba(255,255,255,0);
            white-space: nowrap;">
            {substance} – {r.value} мг/м³<br>
            <u>{r.time}</u>
        </div>
        """

        folium.Marker(
            [r.lat, r.lon],
            icon=DivIcon(
                icon_size=(250,36),
                icon_anchor=(0,-10),
                html=label_html
            )
        ).add_to(m)

    # Легенда
    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        width: 200px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:14px;
        padding: 10px;">
        <b>Концентрація</b><br>
        <span style="color:green;">■</span> &lt; 0.1 мг/м³<br>
        <span style="color:orange;">■</span> 0.1–0.5 мг/м³<br>
        <span style="color:red;">■</span> &gt; 0.5 мг/м³
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m

# ===============================
# Відображення карти
# ===============================
if st.session_state.measurements:
    df = pd.DataFrame(st.session_state.measurements)
    m = build_map(df)
    st_folium(m, width=1100, height=650)

    # Експорт HTML
    if st.button("💾 Зберегти карту в HTML"):
        m.save("chemical_map.html")
        st.success("Файл chemical_map.html створено")

# ===============================
# Очистка
# ===============================
if st.button("🧹 Очистити всі дані"):
    st.session_state.measurements = []
    st.experimental_rerun()

