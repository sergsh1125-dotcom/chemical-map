import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# ===============================
# 1. СТОРІНКА
# ===============================
st.set_page_config(page_title="КАРТА ХІМІЧНОЇ ОБСТАНОВКИ", page_icon="☣️", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stButton button {font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ===============================
# 2. SESSION STATE
# ===============================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])

if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# ===============================
# 3. ПІДПИС
# ===============================
def marker_html(main, sub):
    return f"""
    <div style="
        display: inline-block;
        font-family: Arial;
        font-size: 10pt;
        color: blue;
        font-weight: bold;
        text-align: center;
        white-space: nowrap;
        background-color: transparent;
        text-shadow:
            -1px -1px 0 #fff,
             1px -1px 0 #fff,
            -1px  1px 0 #fff,
             1px  1px 0 #fff,
             2px  2px 3px rgba(255,255,255,0.9);
    ">
        <div style="
            border-bottom: 2px solid blue;
            display: inline-block;
            padding-bottom: 2px;
            margin-bottom: 2px;
        ">
            {main}
        </div>
        <div style="font-weight: normal;">
            {sub}
        </div>
    </div>
    """

# ===============================
# 4. КАРТА
# ===============================
def create_map(df, lat, lon, zoom):

    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None, control_scale=True)

    # ОСНОВА
    folium.TileLayer('OpenStreetMap', name='Карта', show=True).add_to(m)

    # СУПУТНИК (НЕ АКТИВНИЙ)
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Супутник',
        show=False
    ).add_to(m)

    # МАРКЕР КЛІКУ
    if st.session_state.clicked_coords is not None:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red")
        ).add_to(m)

    # ТОЧКИ
    if not df.empty:
        for day in sorted(df['time'].unique(), reverse=True):
            group = folium.FeatureGroup(name=f"📅 {day}")

            for _, r in df[df['time'] == day].iterrows():

                main = f"{r['substance']} {float(r['value']):.2f} {r['unit']}"
                sub = r['time']

                folium.CircleMarker(
    [r.lat, r.lon],
    radius=6,
    color="orange",
    fill=True,
    fill_color="orange",
    fill_opacity=1
).add_to(group)

                folium.Marker(
                    [r.lat, r.lon],
                    icon=folium.DivIcon(
                        icon_anchor=(80, 45),
                        html=marker_html(main, sub)
                    )
                ).add_to(group)

            group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# ===============================
# 5. ІНТЕРФЕЙС
# ===============================
st.header("☣️ КАРТА ХІМІЧНОЇ ОБСТАНОВКИ")

col_map, col_panel = st.columns([3,1])

# -------- ПУЛЬТ --------
with col_panel:
    st.subheader("ПУЛЬТ УПРАВЛІННЯ")

    if st.session_state.clicked_coords is not None:
        lat = st.session_state.clicked_coords['lat']
        lon = st.session_state.clicked_coords['lng']

        st.write(f"Координати: {lat:.6f}, {lon:.6f}")

        c1, c2 = st.columns(2)

        if c1.button("Вставити координати у форму", use_container_width=True):
            st.session_state.manual_lat = lat
            st.session_state.manual_lon = lon
            st.rerun()

        if c2.button("Виключити маркер", use_container_width=True):
            st.session_state.clicked_coords = None
            st.rerun()

    st.divider()

    # ВРУЧНУ
    st.markdown("### НАНЕСЕННЯ ТОЧКИ ВРУЧНУ")

    lat = st.number_input("Широта", format="%.6f", value=st.session_state.get("manual_lat", 50.45))
    lon = st.number_input("Довгота", format="%.6f", value=st.session_state.get("manual_lon", 30.52))

    substance = st.text_input("Речовина", "Хлор")
    value = st.number_input("Значення", format="%.2f")
    unit = st.selectbox("Одиниця", ["мг/м³","ppm"])
    time = st.date_input("Дата", value=datetime.now()).strftime("%d.%m.%Y")

    if st.button("Нанести на карту"):
        new = pd.DataFrame([{
            "lat": lat,
            "lon": lon,
            "substance": substance,
            "value": value,
            "unit": unit,
            "time": time
        }])
        st.session_state.data = pd.concat([st.session_state.data, new], ignore_index=True)
        st.rerun()

    st.divider()

    # CSV
    st.markdown("### НАНЕСЕННЯ З ТАБЛИЦІ")

    file = st.file_uploader("CSV", type=["csv"])

    if file and st.button("Імпортувати", use_container_width=True):
        df = pd.read_csv(file)
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce').dt.strftime('%d.%m.%Y')

        st.session_state.data = pd.concat([st.session_state.data, df], ignore_index=True)
        st.rerun()

# -------- КАРТА --------
with col_map:

    if st.session_state.data.empty:
        lat, lon, zoom = 49, 31, 6
    else:
        lat = st.session_state.data.lat.mean()
        lon = st.session_state.data.lon.mean()
        zoom = 9

    m = create_map(st.session_state.data, lat, lon, zoom)

    # 🔥 ГОЛОВНЕ ВИПРАВЛЕННЯ
    map_output = st_folium(
        m,
        width="100%",
        height=750,
        key="chem_map",  # ОБОВ’ЯЗКОВО
        returned_objects=["last_clicked"]
    )

    clicked = map_output.get("last_clicked")

    if clicked is not None:
        if st.session_state.clicked_coords != clicked:
            st.session_state.clicked_coords = clicked
            st.rerun()

    # КНОПКИ
    c1, c2 = st.columns(2)

    if c1.button("Очистити карту", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
        st.session_state.clicked_coords = None
        st.rerun()

    if not st.session_state.data.empty:

        st.subheader("Таблиця вимірювань")

        st.dataframe(
            st.session_state.data.rename(columns={
                "lat":"Широта",
                "lon":"Довгота",
                "substance":"Речовина",
                "value":"Значення",
                "unit":"Одиниця",
                "time":"Дата"
            }),
            use_container_width=True
        )

        if c2.button("Завантажити карту в HTML", use_container_width=True):
            st.download_button(
                "Скачати HTML",
                m._repr_html_(),
                "chemical_map.html",
                "text/html"
            )

        if c2.button("Завантажити таблицю", use_container_width=True):
            st.download_button(
                "Скачати CSV",
                st.session_state.data.to_csv(index=False),
                "chemical_data.csv",
                "text/csv"
            )
