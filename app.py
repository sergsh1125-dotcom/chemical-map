import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# ===============================
# Сторінка
# ===============================
st.set_page_config(
    page_title="Хімічна обстановка",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Приховати стандартні кнопки Streamlit
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("🧪 Карта хімічної обстановки")

# ===============================
# Session state
# ===============================
if "data" not in st.session_state:
    st.session_state.data = []

# ===============================
# Сайдбар для ручного введення
# ===============================
with st.sidebar:
    st.header("➕ Додати точку вимірювання")

    substance = st.text_input(
        "Назва небезпечної речовини",
        value="Хлор"
    )

    lat = st.number_input(
        "Широта (lat)",
        format="%.6f",
        value=50.4501
    )

    lon = st.number_input(
        "Довгота (lon)",
        format="%.6f",
        value=30.5234
    )

    concentration = st.number_input(
        "Концентрація, мг/м³",
        min_value=0.0,
        format="%.3f"
    )

    time_meas = st.text_input(
        "Час вимірювання",
        value=datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    if st.button("➕ Додати точку"):
        st.session_state.data.append({
            "substance": substance,
            "lat": lat,
            "lon": lon,
            "concentration": concentration,
            "time": time_meas
        })
        st.success("Точку додано")

    if st.button("🧹 Очистити всі точки"):
        st.session_state.data = []
        st.warning("Дані очищено")

    st.subheader("📂 Завантажити CSV")
    uploaded_file = st.file_uploader("CSV файл (lat, lon, value, time)", type="csv")
    if uploaded_file:
        df_csv = pd.read_csv(uploaded_file)
        df_csv[['lat','lon','value']] = df_csv[['lat','lon','value']].apply(pd.to_numeric, errors="coerce")
        df_csv = df_csv.dropna()
        for _, r in df_csv.iterrows():
            st.session_state.data.append({
                "substance": substance,
                "lat": r.lat,
                "lon": r.lon,
                "concentration": r.value,
                "time": r.time
            })
        st.success(f"Завантажено {len(df_csv)} точок")

    st.subheader("💾 Експорт")
    if st.button("Зберегти карту в HTML"):
        if st.session_state.data:
            df_export = pd.DataFrame(st.session_state.data)
            # Створюємо карту
            m = folium.Map(location=[df_export.lat.mean(), df_export.lon.mean()], zoom_start=13)
            for _, r in df_export.iterrows():
                folium.CircleMarker([r.lat, r.lon], radius=7,
                                    color="black", fill=True, fill_color="red", fill_opacity=0.8).add_to(m)
                folium.Marker([r.lat, r.lon],
                              icon=folium.features.DivIcon(
                                  icon_size=(260, 60),
                                  icon_anchor=(0, 0),
                                  html=f"<div style='background: transparent; font-size:12px; font-weight:bold;'>{r.substance} – {r.concentration} мг/м³<br><u>{r.time}</u></div>"
                              )).add_to(m)
            m.save("chemical_map.html")
            st.success("Файл chemical_map.html створено")
        else:
            st.warning("Спершу додайте точки")

    if st.button("Зберегти дані в PDF"):
        if st.session_state.data:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Хімічна обстановка", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("Arial", "", 12)
            pdf.cell(40, 8, "Substance", 1)
            pdf.cell(30, 8, "Lat", 1)
            pdf.cell(30, 8, "Lon", 1)
            pdf.cell(40, 8, "Concentration", 1)
            pdf.cell(50, 8, "Time", 1)
            pdf.ln()
            for r in st.session_state.data:
                pdf.cell(40,8,str(r['substance']),1)
                pdf.cell(30,8,str(r['lat']),1)
                pdf.cell(30,8,str(r['lon']),1)
                pdf.cell(40,8,str(r['concentration']),1)
                pdf.cell(50,8,str(r['time']),1)
                pdf.ln()
            pdf.output("chemical_map.pdf")
            st.success("Файл chemical_map.pdf створено")
        else:
            st.warning("Спершу додайте точки")

# ===============================
# Функція побудови карти
# ===============================
def build_map(data):
    if not data:
        return folium.Map(location=[50.45,30.52], zoom_start=6)

    df = pd.DataFrame(data)
    m = folium.Map(location=[df.lat.mean(), df.lon.mean()], zoom_start=13, control_scale=True)

    fg = folium.FeatureGroup(name="Точки вимірювання")

    for _, r in df.iterrows():
        color = "green"
        if r['concentration'] >= 1:
            color = "red"
        elif r['concentration'] >= 0.5:
            color = "orange"

        folium.CircleMarker([r['lat'], r['lon']],
                            radius=7,
                            color="black",
                            weight=1,
                            fill=True,
                            fill_color=color,
                            fill_opacity=0.8).add_to(fg)

        folium.Marker([r['lat'], r['lon']],
                      icon=folium.features.DivIcon(
                          icon_size=(260, 60),
                          icon_anchor=(0, 0),
                          html=f"<div style='background: transparent; font-size:12px; font-weight:bold;'>{r['substance']} – {r['concentration']} мг/м³<br><u>{r['time']}</u></div>"
                      )).add_to(fg)

    fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m

# ===============================
# Відображення карти
# ===============================
st.subheader("🗺️ Карта")
map_obj = build_map(st.session_state.data)
st_folium(map_obj, width=1200, height=700)

# ===============================
# Таблиця даних
# ===============================
if st.session_state.data:
    st.subheader("📋 Вхідні дані")
    st.dataframe(pd.DataFrame(st.session_state.data), use_container_width=True)

