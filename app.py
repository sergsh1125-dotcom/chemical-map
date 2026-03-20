import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# ===============================
# 1. Налаштування сторінки
# ===============================
st.set_page_config(page_title="КАРТА РХБ ОБСТАНОВКИ", page_icon="☢️", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stButton button {font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ===============================
# 2. Стан програми
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "value", "unit", "time", "type", "substance"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# ===============================
# 3. Підпис маркеру
# ===============================
def get_custom_marker_html(value_text, date_text):
    return f"""
<div style="display:inline-block; font-family: Arial; font-size:10pt; color:blue; font-weight:bold; text-align:center;
text-shadow:-1px -1px 0 #fff,1px -1px 0 #fff,-1px 1px 0 #fff,1px 1px 0 #fff;">
    <div style="white-space: nowrap;">{value_text}</div>
    <div>{date_text}</div>
</div>
"""

# ===============================
# 4. Створення карти
# ===============================
def create_map(df_data, start_lat, start_lon, zoom_val):
    m = folium.Map(location=[start_lat, start_lon], zoom_start=zoom_val, tiles=None, control_scale=True)

    folium.TileLayer('OpenStreetMap', name='Стандартна карта', show=True).add_to(m)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Супутник',
        show=False
    ).add_to(m)

    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red")
        ).add_to(m)

    if not df_data.empty:
        for day_val in sorted(df_data['time'].unique(), reverse=True):
            group = folium.FeatureGroup(name=f"📅 {day_val}")

            for _, r in df_data[df_data['time'] == day_val].iterrows():

                color = "blue" if r["type"] == "радіоактивне забруднення" else "black"

                val_label = (
                    f"☢ {float(r['value']):.2f} {r['unit']}"
                    if r["type"] == "радіоактивне забруднення"
                    else f"☣ {r['substance']} {float(r['value']):.2f} {r['unit']}"
                )

                folium.CircleMarker(
                    [r.lat, r.lon],
                    radius=6,
                    color=color,
                    fill=True,
                    fill_color=color
                ).add_to(group)

                folium.Marker(
                    [r.lat, r.lon],
                    icon=folium.DivIcon(
                        icon_anchor=(70, 45),
                        html=get_custom_marker_html(val_label, str(r['time']))
                    )
                ).add_to(group)

            group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# ===============================
# 5. ПУЛЬТ УПРАВЛІННЯ
# ===============================
st.header("☢️ КАРТА РХБ ОБСТАНОВКИ")

col_map, col_gui = st.columns([3, 1])

with col_gui:
    st.subheader("ПУЛЬТ УПРАВЛІННЯ")

    # ===== Координати =====
    if st.session_state.clicked_coords:
        c_lat, c_lon = st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']
        st.write(f"Вибрано: {c_lat:.6f}, {c_lon:.6f}")

        c1, c2 = st.columns(2)
        if c1.button("Вставити координати у форму"):
            st.session_state.manual_lat = c_lat
            st.session_state.manual_lon = c_lon
            st.rerun()

        if c2.button("Виключити маркер"):
            st.session_state.clicked_coords = None
            st.rerun()

    st.divider()

    # ===== Вибір типу =====
    data_type = st.radio(
        "Тип забруднення",
        ["радіоактивне забруднення", "хімічне забруднення"]
    )

    # ===== Координати =====
    st.markdown("### Точка вимірювання")

    l1 = st.number_input("Широта", format="%.6f", value=st.session_state.get('manual_lat', 50.4501))
    l2 = st.number_input("Довгота", format="%.6f", value=st.session_state.get('manual_lon', 30.5234))

    # ===== Речовина =====
    substance = ""

    if data_type == "хімічне забруднення":
        substance = st.text_input("Речовина")

    # ===== Значення =====
    val = st.number_input("Значення", step=0.01, format="%.2f")

    # ===== Одиниці =====
    if data_type == "радіоактивне забруднення":
        uni = st.selectbox("Одиниця", ["мкЗв/год", "мЗв/год"])
    else:
        uni = st.selectbox("Одиниця", ["мг/м³"])

    tim = st.date_input("Дата", value=datetime.now()).strftime("%d.%m.%Y")

    if st.button("Нанести на карту"):
        new_row = pd.DataFrame([{
            "lat": l1,
            "lon": l2,
            "value": val,
            "unit": uni,
            "time": tim,
            "type": data_type,
            "substance": substance
        }])

        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.rerun()

    st.divider()

    # ===== CSV =====
    uploaded_file = st.file_uploader("CSV", type=["csv"], label_visibility="collapsed")

    if uploaded_file and st.button("Імпортувати"):
        df_new = pd.read_csv(uploaded_file)

        if 'time' in df_new.columns:
            df_new['time'] = pd.to_datetime(df_new['time'], dayfirst=True, errors='coerce').dt.strftime('%d.%m.%Y')

        st.session_state.data = pd.concat([st.session_state.data, df_new], ignore_index=True)
        st.rerun()

# ===============================
# 6. КАРТА
# ===============================
with col_map:
    if st.session_state.data.empty:
        s_lat, s_lon, s_zoom = 49.0, 31.0, 6
    else:
        df_c = st.session_state.data.dropna(subset=['lat', 'lon'])
        s_lat, s_lon = df_c.lat.mean(), df_c.lon.mean()
        s_zoom = 9

    m = create_map(st.session_state.data, s_lat, s_lon, s_zoom)

    map_output = st_folium(
        m, width="100%", height=750, returned_objects=["last_clicked"]
    )

    clicked = map_output.get("last_clicked")

    if clicked and st.session_state.clicked_coords != clicked:
        st.session_state.clicked_coords = clicked
        st.rerun()

    # ===== Кнопки =====
    c1, c2 = st.columns(2)

    if c1.button("Очистити карту"):
        st.session_state.data = pd.DataFrame(columns=["lat","lon","value","unit","time","type","substance"])
        st.session_state.clicked_coords = None
        st.rerun()

    if not st.session_state.data.empty:
        st.subheader("Точки")

        st.dataframe(
            st.session_state.data,
            use_container_width=True
        )

        if c2.button("Завантажити HTML"):
            st.download_button(
                "Завантажити карту",
                m._repr_html_(),
                f"map_{datetime.now().strftime('%Y%m%d')}.html",
                "text/html"
            )

        if c2.button("Завантажити CSV"):
            st.download_button(
                "Завантажити дані",
                st.session_state.data.to_csv(index=False),
                f"data_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
