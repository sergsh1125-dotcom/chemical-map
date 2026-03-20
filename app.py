import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import Print
from datetime import datetime
from fpdf import FPDF
import io

# ===============================
# 1. КОНФІГУРАЦІЯ ТА СТИЛІ
# ===============================
st.set_page_config(page_title="RKhBZ Map Control", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stButton button {font-weight: bold; border-radius: 5px;}
@media print {
    .stColumn:last-child, button, .stDownloadButton { display: none !important; }
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 2. СТАН ПРОГРАМИ
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# ===============================
# 3. ГЕНЕРАЦІЯ PDF ЗВІТУ (fpdf2)
# ===============================
def generate_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "ЗВІТ ПРО ХІМІЧНУ ОБСТАНОВКУ", ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Дата генерації: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Заголовки таблиці
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(30, 10, "Речовина", 1, 0, 'C', True)
    pdf.cell(30, 10, "Значення", 1, 0, 'C', True)
    pdf.cell(30, 10, "Широта", 1, 0, 'C', True)
    pdf.cell(30, 10, "Довгота", 1, 0, 'C', True)
    pdf.cell(40, 10, "Дата/Час", 1, 1, 'C', True)
    
    # Дані
    for _, r in df.iterrows():
        pdf.cell(30, 10, str(r['substance']), 1)
        pdf.cell(30, 10, f"{r['value']} {r['unit']}", 1)
        pdf.cell(30, 10, str(round(r['lat'], 4)), 1)
        pdf.cell(30, 10, str(round(r['lon'], 4)), 1)
        pdf.cell(40, 10, str(r['time']), 1, 1)
    
    return pdf.output()

# ===============================
# 4. ЛОГІКА КАРТИ
# ===============================
def create_map(df, lat, lon, zoom):
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles='OpenStreetMap', control_scale=True)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', # Гібрид (супутник + назви)
        attr='Google', name='Супутник (Гібрид)', overlay=False
    ).add_to(m)

    # Кнопка для PNG/PDF друку прямо на карті
    Print().add_to(m)

    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red", icon="screenshot", prefix="fa")
        ).add_to(m)

    for _, r in df.iterrows():
        label = f"{r['substance']} {r['value']} {r['unit']}"
        folium.CircleMarker([r.lat, r.lon], radius=7, color="orange", fill=True, fill_opacity=1).add_to(m)
        folium.Marker(
            [r.lat, r.lon],
            icon=folium.DivIcon(html=f'<div style="font-size:10pt; color:blue; font-weight:bold; width:150px;">{label}</div>', icon_anchor=(0, 0))
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m

# ===============================
# 5. ОСНОВНИЙ ІНТЕРФЕЙС
# ===============================
st.subheader("📊 Моніторинг хімічної обстановки")

col_map, col_panel = st.columns([3, 1])

with col_panel:
    with st.expander("📍 КЕРУВАННЯ ТОЧКОЮ", expanded=True):
        if st.session_state.clicked_coords:
            c = st.session_state.clicked_coords
            st.success(f"Обрано: {c['lat']:.5f}, {c['lng']:.5f}")
            if st.button("Вставити координати"):
                st.session_state.manual_lat, st.session_state.manual_lon = c['lat'], c['lng']
                st.rerun()

        lat_in = st.number_input("Широта", format="%.6f", value=st.session_state.get("manual_lat", 50.45))
        lon_in = st.number_input("Довгота", format="%.6f", value=st.session_state.get("manual_lon", 30.52))
        sub_in = st.text_input("Речовина", "NH3 (Аміак)")
        val_in = st.number_input("Концентрація", format="%.2f")
        unit_in = st.selectbox("Одиниця", ["мг/м³","ppm"])
        date_in = st.text_input("Дата/Час", datetime.now().strftime("%d.%m.%Y %H:%M"))

        if st.button("НАНЕСТИ НА КАРТУ", use_container_width=True):
            new_row = pd.DataFrame([{"lat": lat_in, "lon": lon_in, "substance": sub_in, "value": val_in, "unit": unit_in, "time": date_in}])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            st.rerun()

    if not st.session_state.data.empty:
        st.divider()
        # Кнопка для PDF Звіту через fpdf2
        pdf_data = generate_pdf(st.session_state.data)
        st.download_button("📥 СКАЧАТИ PDF ЗВІТ", pdf_data, "report.pdf", "application/pdf", use_container_width=True)
        
        if st.button("🧹 ОЧИСТИТИ ВСЕ", use_container_width=True):
            st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
            st.rerun()

with col_map:
    center = [st.session_state.data.lat.mean(), st.session_state.data.lon.mean()] if not st.session_state.data.empty else [49.0, 31.0]
    m_obj = create_map(st.session_state.data, center[0], center[1], 6 if st.session_state.data.empty else 9)
    
    map_data = st_folium(m_obj, width="100%", height=650, key="v_stable", returned_objects=["last_clicked"])

    if map_data.get("last_clicked"):
        if st.session_state.clicked_coords != map_data["last_clicked"]:
            st.session_state.clicked_coords = map_data["last_clicked"]
            st.rerun()

# -------- ТАБЛИЦЯ НИЖЧЕ --------
if not st.session_state.data.empty:
    st.dataframe(st.session_state.data, use_container_width=True)
