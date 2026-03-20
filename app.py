import streamlit as st
import pandas as pd
import json
from datetime import datetime

# ===============================
# 1. НАЛАШТУВАННЯ СТОРІНКИ
# ===============================
st.set_page_config(page_title="КАРТА ХІМІЧНОЇ ОБСТАНОВКИ", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu, footer, header, .stDeployButton {visibility: hidden; display: none !important;}
.block-container {padding:1rem !important; max-width:100% !important;}
.stApp {background-color:#0e1117; color:#e0e0e0;}
.main-title {color:#ffcc00 !important; text-align:center !important; font-size:25px !important; font-weight:bold !important; margin-top:-30px !important; text-transform:uppercase !important;}
.module-header {color:#ffcc00 !important; border-bottom:1px solid #ffcc00 !important; margin-top:10px !important; font-weight:bold !important; font-size:18px !important; text-transform:uppercase !important;}
div[data-testid="stButton"] button {background-color:#ffcc00 !important; color:#000 !important; font-weight:bold !important; width:100%;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">Модуль 1.5. Карта фактичної хімічної обстановки</p>', unsafe_allow_html=True)

# ===============================
# 2. SESSION STATE (ДАНІ)
# ===============================
if "chem_data" not in st.session_state:
    st.session_state.chem_data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])

json_data = st.session_state.chem_data.to_json(orient='records')

# ===============================
# 3. ІНТЕРФЕЙС (КОЛОНКИ)
# ===============================
col_map, col_panel = st.columns([3.3, 1.4])

with col_panel:
    st.markdown('<p class="module-header">ПУЛЬТ УПРАВЛІННЯ</p>', unsafe_allow_html=True)
    
    with st.expander("➕ ДОДАТИ ТОЧКУ ВРУЧНУ", expanded=True):
        # Порада для користувача
        st.info("💡 Клікніть на карті, щоб отримати координати, потім вставте їх сюди.")
        lat_input = st.number_input("Широта", format="%.6f", value=48.3794)
        lon_input = st.number_input("Довгота", format="%.6f", value=31.1656)
        substance = st.text_input("Речовина", "Хлор")
        val = st.number_input("Значення", format="%.2f", value=0.0)
        unit = st.selectbox("Одиниця", ["мг/м³", "ppm"])
        date_str = st.date_input("Дата", value=datetime.now()).strftime("%d.%m.%Y")
        
        if st.button("НАНЕСТИ НА КАРТУ"):
            new_row = pd.DataFrame([{"lat": lat_input, "lon": lon_input, "substance": substance, "value": val, "unit": unit, "time": date_str}])
            st.session_state.chem_data = pd.concat([st.session_state.chem_data, new_row], ignore_index=True)
            st.rerun()

    with st.expander("📂 ІМПОРТ З CSV"):
        uploaded_file = st.file_uploader("Виберіть файл", type="csv")
        if uploaded_file and st.button("ЗАВАНТАЖИТИ CSV"):
            df = pd.read_csv(uploaded_file)
            st.session_state.chem_data = pd.concat([st.session_state.chem_data, df], ignore_index=True)
            st.rerun()

    if st.button("🗑️ ОЧИСТИТИ ТАБЛИЦЮ"):
        st.session_state.chem_data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
        st.rerun()

# ===============================
# 4. КАРТА ТА ІНСТРУМЕНТИ
# ===============================
with col_map:
    if not st.session_state.chem_data.empty:
        c_lat, c_lon, zoom_val = st.session_state.chem_data.lat.mean(), st.session_state.chem_data.lon.mean(), 8
    else:
        c_lat, c_lon, zoom_val = 48.3794, 31.1656, 6

    map_html = f"""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
<script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>

<div id="capture_area" style="background:#0e1117; padding:5px; border-radius:8px;">
    <div id="coords_info" style="background:#ffcc00; color:black; padding:8px; margin-bottom:5px; border-radius:4px; font-weight:bold; display:flex; justify-content:between; align-items:center;">
        <span id="display_latlon">Клікніть на карті для отримання координат</span>
        <button onclick="copyCoords()" id="copy_btn" style="display:none; margin-left:15px; background:black; color:white; border:none; padding:3px 8px; border-radius:3px; cursor:pointer; font-size:10px;">КОПІЮВАТИ</button>
    </div>
    <div id="map" style="height:620px; width:100%; border-radius:8px;"></div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 5px; margin-top: 10px;">
    <button onclick="addText()" style="padding:12px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:12px;">ТЕКСТ</button>
    <button onclick="downloadPNG()" style="padding:12px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:12px;">ЕКСПОРТ PNG</button>
    <button onclick="window.print()" style="padding:12px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:12px;">ДРУК / PDF</button>
    <button onclick="clearOperational()" style="padding:12px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:12px;">ОЧИСТИТИ МАЛЮНКИ</button>
</div>

<script>
var chemData = {json_data};
var map = L.map('map',{{attributionControl:false, preferCanvas: true}}).setView([{c_lat},{c_lon}], {zoom_val});

L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{ crossOrigin: 'anonymous' }}).addTo(map);

var dataGroup = L.featureGroup().addTo(map);
var operationalGroup = L.featureGroup().addTo(map);
var clickMarker = L.marker([0,0]).addTo(map); // Маркер кліку
clickMarker.setOpacity(0);

// --- 1. ЛОГІКА КЛІКУ (Повернення координат) ---
map.on('click', function(e) {{
    var lat = e.latlng.lat.toFixed(6);
    var lon = e.latlng.lng.toFixed(6);
    document.getElementById('display_latlon').innerText = "Координати: " + lat + ", " + lon;
    document.getElementById('copy_btn').style.display = "block";
    
    // Візуальний маркер кліку
    clickMarker.setLatLng(e.latlng).setOpacity(1);
    
    // Зберігаємо в глобальну змінну для копіювання
    window.lastCoords = lat + ", " + lon;
}});

function copyCoords() {{
    navigator.clipboard.writeText(window.lastCoords);
    alert("Координати скопійовано! Тепер вставте їх у форму справа.");
}}

// --- 2. ОФІЦІЙНІ ДАНІ ---
chemData.forEach(function(r) {{
    var lat = parseFloat(r.lat);
    var lon = parseFloat(r.lon);
    L.circleMarker([lat, lon], {{ radius: 6, color: "orange", fillColor: "orange", fillOpacity: 1, weight: 2 }}).addTo(dataGroup);
    var labelHtml = `<div style="display:inline-block; font-family:Arial; font-size:10pt; color:blue; font-weight:bold; text-align:center; white-space:nowrap; text-shadow:2px 2px 2px #fff;"><div style="border-bottom: 2px solid blue; padding-bottom:2px; margin-bottom:2px;">${{r.substance}} ${{r.value}} ${{r.unit}}</div><div style="font-weight:normal;">${{r.time}}</div></div>`;
    L.marker([lat, lon], {{ icon: L.divIcon({{ html: labelHtml, iconAnchor: [80, 45], className: '' }}) }}).addTo(dataGroup);
}});

// --- 3. ПАНЕЛЬ МАЛЮВАННЯ ---
var drawControl = new L.Control.Draw({{
    draw:{{
        polygon: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        rectangle: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        circle: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        marker: true,
        circlemarker: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.9, radius: 8 }}
    }},
    edit: {{ featureGroup: operationalGroup }}
}});
map.addControl(drawControl);

map.on(L.Draw.Event.CREATED, function(e){{
    var layer = e.layer;
    if(e.layerType !== 'marker' && e.layerType !== 'circlemarker') {{
        layer.setStyle({{color:'black', fillColor:'yellow', fillOpacity:0.5}});
    }}
    operationalGroup.addLayer(layer);
    drawControl._toolbars.draw._modes[e.layerType].handler.disable();
}});

function addText() {{
    var t = prompt("Введіть текст:");
    if(t) {{
        map.once('click', function(e){{
            L.marker(e.latlng, {{ icon: L.divIcon({{ html: '<div style="background:white; border:1px solid black; padding:2px; font-weight:bold; color:black;">'+t+'</div>', className: '' }}) }}).addTo(operationalGroup);
        }});
    }}
}}

function clearOperational() {{
    if(confirm("Видалити малюнки?")) {{ operationalGroup.clearLayers(); clickMarker.setOpacity(0); }}
}}

function downloadPNG() {{
    const area = document.getElementById("capture_area");
    html2canvas(area, {{ useCORS: true, scale: 2, scrollY: -window.scrollY }}).then(canvas => {{
        var link = document.createElement("a");
        link.download = "Chemical_Report.png";
        link.href = canvas.toDataURL();
        link.click();
    }});
}}
</script>
"""
    st.components.v1.html(map_html, height=760)

if not st.session_state.chem_data.empty:
    st.markdown('<p class="module-header">ЖУРНАЛ ВИМІРЮВАНЬ</p>', unsafe_allow_html=True)
    st.dataframe(st.session_state.chem_data, use_container_width=True)
