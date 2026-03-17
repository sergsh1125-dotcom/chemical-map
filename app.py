import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# ===============================
# 1. Налаштування сторінки
# ===============================
st.set_page_config(page_title="КАРТА ХІМІЧНОЇ ОБСТАНОВКИ", page_icon="🧪", layout="wide")

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
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
if "clicked_coords" not in st.session_state:
    st.session_state.clicked_coords = None

# ===============================
# 3. Функція маркеру з підписом
# ===============================
def get_custom_marker_html(substance_text, value_text, date_text):
    html = f"""
    <div style="position: relative; display: flex; align-items: center; width: 220px;">
        <div style="
            width: 10px; 
            height: 10px; 
            background-color: blue; 
            border-radius: 50%; 
            border: 1px solid white;
            flex-shrink: 0;">
        </div>
        <div style="
            margin-left: 8px;
            color: blue; 
            font-family: 'Segoe UI', Tahoma, sans-serif; 
            font-size: 10pt; 
            font-weight: bold; 
            line-height: 1.2;
            white-space: nowrap;
            text-shadow: 1px 1px 2px white, -1px -1px 2px white, 1px -1px 2px white, -1px 1px 2px white;">
            <div>{substance_text} — {value_text} мг/м³</div>
            <div style="border-top: 1px solid blue; margin: 1px 0;"></div>
            <div>{date_text}</div>
        </div>
    </div>
    """
    return html

def create_map(df_data, start_lat, start_lon, zoom_val):
    m = folium.Map(location=[start_lat, start_lon], zoom_start=zoom_val, tiles=None, control_scale=True)
    
    folium.TileLayer('OpenStreetMap', name='Стандартна карта', show=True).add_to(m)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', name='Супутник', show=False).add_to(m)
    
    if not df_data.empty:
        df = df_data.copy()
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.dropna(subset=['lat','lon','value'])
        for day_val in sorted(df['time'].unique(), reverse=True):
            gp = folium.FeatureGroup(name=f"📅 {day_val}")
            for _, r in df[df['time']==day_val].iterrows():
                val_label = f"{r['value']:.2f}".rstrip('0').rstrip('.')
                folium.Marker(
                    [r.lat, r.lon],
                    icon=folium.DivIcon(
                        icon_anchor=(5, 12),
                        html=get_custom_marker_html(r['substance'], val_label, r['time'])
                    )
                ).add_to(gp)
            gp.add_to(m)
    
    if st.session_state.clicked_coords:
        folium.Marker(
            [st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']],
            icon=folium.Icon(color="red")
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# ===============================
# 4. Інтерфейс (Пульт управління)
# ===============================
st.header("🧪 КАРТА ХІМІЧНОЇ ОБСТАНОВКИ")
col_map, col_gui = st.columns([3,1])

with col_gui:
    st.subheader("ПУЛЬТ УПРАВЛІННЯ")

    if st.session_state.clicked_coords:
        c_lat, c_lon = st.session_state.clicked_coords['lat'], st.session_state.clicked_coords['lng']
        st.write(f"Вибрано: {c_lat:.6f}, {c_lon:.6f}")
        r1, r2 = st.columns(2)
        if r1.button("Вставити координати у форму", use_container_width=True):
            st.session_state.manual_lat, st.session_state.manual_lon = c_lat, c_lon
            st.rerun()
        if r2.button("Виключити маркер на карті", use_container_width=True):
            st.session_state.clicked_coords = None
            st.rerun()

    st.divider()
    st.markdown("### НАНЕСЕННЯ ТОЧКИ ВИМІРЮВАННЯ ВРУЧНУ")
    lat_input = st.number_input("Широта", format="%.6f", value=st.session_state.get('manual_lat', 50.4501))
    lon_input = st.number_input("Довгота", format="%.6f", value=st.session_state.get('manual_lon', 30.5234))
    substance_input = st.text_input("Назва хімічної речовини", placeholder="Хлор")
    value_input = st.number_input("Значення", format="%.2f", step=0.01)
    date_input = st.date_input("Дата", value=datetime.now()).strftime("%d.%m.%Y")

    if st.button("Нанести на карту", use_container_width=True):
        new_row = pd.DataFrame([{
            "lat": lat_input,
            "lon": lon_input,
            "substance": substance_input,
            "value": value_input,
            "time": date_input
        }])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.rerun()

    st.divider()
    st.markdown("### НАНЕСЕННЯ ТОЧОК ВИМІРЮВАННЯ З ТАБЛИЦІ")
    up_file = st.file_uploader("📁 CSV файл", type=["csv"], label_visibility="collapsed")
    if up_file and st.button("Завантажити з файлу", use_container_width=True):
        try:
            df_new = pd.read_csv(up_file)
            if 'time' in df_new.columns:
                df_new['time'] = pd.to_datetime(df_new['time'], dayfirst=True, errors='coerce').dt.strftime('%d.%m.%Y')
            st.session_state.data = pd.concat([st.session_state.data, df_new], ignore_index=True)
            st.rerun()
        except:
            st.error("Помилка файлу")

    st.divider()
    if st.button("Очистити карту", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat","lon","substance","value","time"])
        st.session_state.clicked_coords = None
        st.rerun()

# ===============================
# 5. Візуалізація карти
# ===============================
with col_map:
    if st.session_state.data.empty:
        s_lat, s_lon, s_zoom = 49.0, 31.0, 6
    else:
        df_c = st.session_state.data.copy()
        df_c['lat'] = pd.to_numeric(df_c['lat'], errors='coerce')
        df_c['lon'] = pd.to_numeric(df_c['lon'], errors='coerce')
        df_c = df_c.dropna(subset=['lat','lon'])
        s_lat, s_lon, s_zoom = (df_c.lat.mean(), df_c.lon.mean(), 9) if not df_c.empty else (49.0,31.0,6)

    final_map = create_map(st.session_state.data, s_lat, s_lon, s_zoom)
    map_out = st_folium(final_map, width="100%", height=700, key="chem_map_final_adapt")

# ===============================
# 6. Таблиця та завантаження
# ===============================
st.divider()
if not st.session_state.data.empty:
    st.subheader("Список нанесених точок вимірювання")
    ed_df = st.data_editor(
        st.session_state.data,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "lat": st.column_config.NumberColumn("Широта", format="%.6f"),
            "lon": st.column_config.NumberColumn("Довгота", format="%.6f"),
            "substance": st.column_config.TextColumn("Речовина"),
            "value": st.column_config.NumberColumn("Значення", format="%.2f"),
            "time": st.column_config.TextColumn("Дата"),
        }
    )
    if not ed_df.equals(st.session_state.data):
        st.session_state.data = ed_df
        st.rerun()

    c1, c2 = st.columns(2)
    c1.download_button(
        label="Завантажити карту в HTML",
        data=final_map._repr_html_(),
        file_name=f"chemical_map_{datetime.now().strftime('%Y%m%d')}.html",
        mime="text/html",
        use_container_width=True
    )
    c2.download_button(
        label="Завантажити таблицю",
        data=st.session_state.data.to_csv(index=False),
        file_name=f"chemical_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
