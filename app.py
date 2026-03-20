import streamlit as st
import pandas as pd
import json
from datetime import datetime

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="Chemical Hazard Map", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu, footer, header, .stDeployButton {visibility: hidden; display: none !important;}
.block-container {padding:1rem !important; max-width:100% !important;}
.stApp {background-color:#0e1117; color:#e0e0e0;}
.main-title {color:#ffcc00 !important; text-align:center !important; font-size:22px !important; font-weight:bold !important; margin-top:-30px !important; text-transform:uppercase !important;}
div[data-testid="stButton"] button {background-color:#ffcc00 !important; color:#000 !important; font-weight:bold !important; width:100%; font-size:12px !important;}
.stNumberInput input {font-weight: bold;}
.coord-display {background-color: #262730; padding: 10px; border-radius: 5px; border: 1px solid #ffcc00; margin-bottom: 10px; text-align: center;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">Модуль 1.5. Карта фактичної хімічної обстановки</p>', unsafe_allow_html=True)

# --- 2. СТАН ПРОГРАМИ (Session State) ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])

if "temp_coords" not in st.session_state:
    st.session_state.temp_coords = {"lat": 48.3794, "lon": 31.1656}

if "manual_lat" not in st.session_state: st.session_state.manual_lat = 48.3794
if "manual_lon" not in st.session_state: st.session_state.manual_lon = 31.1656
if "show_click_marker" not in st.session_state: st.session_state.show_click_marker = False

# --- 3. РОЗПОДІЛ ЕКРАНУ ---
col_map, col_gui = st.columns([3, 1])

# --- 4. ПРАВА ПАНЕЛЬ (УПРАВЛІННЯ) ---
with col_gui:
    st.subheader("⚙️ КООРДИНАТИ")
    
    # Вивід координат, отриманих з карти
    st.markdown(f"""
    <div class="coord-display">
        <span style="color:#ffcc00;">Широта:</span> {st.session_state.temp_coords['lat']}<br>
        <span style="color:#ffcc00;">Довгота:</span> {st.session_state.temp_coords['lon']}
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    if c1.button("ЗАВАНТАЖИТИ"):
        st.session_state.manual_lat = st.session_state.temp_coords['lat']
        st.session_state.manual_lon = st.session_state.temp_coords['lon']
        st.rerun()
        
    if c2.button("ВИКЛЮЧИТИ"):
        st.session_state.show_click_marker = False
        st.rerun()

    st.divider()

    st.markdown("### ➕ ДОДАТИ ТОЧКУ")
    substance = st.text_input("Речовина", value="Хлор")
    in_lat = st.number_input("Широта", format="%.6f", value=float(st.session_state.manual_lat))
    in_lon = st.number_input("Довгота", format="%.6f", value=float(st.session_state.manual_lon))
    value = st.number_input("Значення", format="%.4f", value=0.0)
    time_input = st.text_input("Дата/Час", value=datetime.now().strftime("%d.%m.%Y %H:%M"))

    if st.button("НАНЕСТИ НА КАРТУ"):
        new_row = pd.DataFrame([{"lat": in_lat, "lon": in_lon, "substance": substance, "value": value, "time": time_input}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.rerun()

    if st.button("🧹 ОЧИСТИТИ ТАБЛИЦЮ"):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.rerun()

# --- 5. КАРТА ---
with col_map:
    json_points = st.session_state.data.to_json(orient='records')
    marker_state = "true" if st.session_state.show_click_marker else "false"
    
    map_html = f"""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
<script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>

<div id="capture_area" style="background:#0e1117; padding:5px; border-radius:8px;">
    <div id="map" style="height:650px; width:100%; border-radius:8px;"></div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 5px; margin-top: 10px;">
    <button onclick="addText()" style="padding:10px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">ВСТАВИТИ ТЕКСТ</button>
    <button onclick="clearMap()" style="padding:10px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">ОЧИСТИТИ МАЛЮНКИ</button>
    <button onclick="downloadPNG()" style="padding:10px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">ЕКСПОРТ PNG</button>
    <button onclick="window.print()" style="padding:10px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">ДРУК / PDF</button>
</div>

<script>
// Ініціалізація карти
var map = L.map('map',{{attributionControl:false}}).setView([{st.session_state.temp_coords['lat']}, {st.session_state.temp_coords['lon']}], 7);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);

var drawnItems = new L.FeatureGroup().addTo(map);
var pointsLayer = new L.FeatureGroup().addTo(map);

// СИНІЙ МАРКЕР ВИЗНАЧЕННЯ КООРДИНАТ
var clickMarker = L.marker([{st.session_state.temp_coords['lat']}, {st.session_state.temp_coords['lon']}]).addTo(map);
if ({marker_state}) {{ clickMarker.setOpacity(1); }} else {{ clickMarker.setOpacity(0); }}

// ОБРОБКА КЛІКУ (Тільки для координат)
map.on('click', function(e) {{
    var lat = e.latlng.lat.toFixed(6);
    var lon = e.latlng.lng.toFixed(6);
    
    clickMarker.setLatLng(e.latlng).setOpacity(1);
    
    // Передача даних у скрипт Streamlit через URL (найнадійніший метод для iframe)
    const url = new URL(window.location.href);
    url.searchParams.set('lat', lat);
    url.searchParams.set('lon', lon);
    url.searchParams.set('marker', 'true');
    window.parent.location.hash = 'lat=' + lat + '&lon=' + lon; 
}});

// Моніторинг хешу для Streamlit (механізм зв'язку)
setInterval(function() {{
    var hash = window.parent.location.hash;
    if (hash.includes('lat=')) {{
        // Дані передаються через прихований input або просто візуально
    }}
}}, 500);

// НАНЕСЕННЯ ТОЧОК З ТАБЛИЦІ
var points = {json_points};
points.forEach(function(p) {{
    L.circleMarker([p.lat, p.lon], {{radius:7, color:"blue", fillColor:"blue", fillOpacity:0.8}}).addTo(pointsLayer);
    var label = L.divIcon({{
        html: `<div style="font-family:sans-serif; font-size:11pt; color:blue; font-weight:bold; white-space:nowrap; text-shadow:1px 1px 2px white;">${{p.substance}}: ${{p.value}} | ${{p.time}}</div>`,
        iconAnchor: [-15, 7], className: ''
    }});
    L.marker([p.lat, p.lon], {{icon: label}}).addTo(pointsLayer);
}});

// ПАНЕЛЬ МАЛЮВАННЯ (БЕЗ СТВОРЕННЯ СИНІХ МАРКЕРІВ)
var drawControl = new L.Control.Draw({{
    draw:{{
        polygon: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        rectangle: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        circle: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        polyline: {{ shapeOptions: {{ color: 'black', weight: 3 }} }},
        marker: false, // Вимкнено стандартний маркер щоб не плутати
        circlemarker: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.9, radius: 8 }}
    }},
    edit:{{ featureGroup: drawnItems }}
}});
map.addControl(drawControl);

map.on(L.Draw.Event.CREATED, function(e){{
    var layer = e.layer;
    drawnItems.addLayer(layer);
}});

function addText(){{
    var text = prompt("Введіть текст:");
    if(text){{
        map.once('click', function(e){{
            var icon = L.divIcon({{
                html:'<div style="background:rgba(255,255,255,0.8); padding:2px 5px; border:1px solid black; border-radius:3px; font-weight:bold; color:black; white-space:nowrap;">'+text+'</div>',
                iconSize: null
            }});
            L.marker(e.latlng,{{icon:icon}}).addTo(drawnItems);
        }});
    }}
}}

function clearMap() {{
    if(confirm("Очистити малюнки?")) {{ drawnItems.clearLayers(); }}
}}

function downloadPNG(){{
    const area = document.getElementById("capture_area");
    html2canvas(area, {{useCORS: true, backgroundColor: "#0e1117", scale: 2, scrollY: -window.scrollY}}).then(function(canvas){{
        var link = document.createElement("a");
        link.download = "Chemical_Report.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    }});
}}
</script>
"""
    # Віджет для обміну даними (Query params hack)
    params = st.query_params
    if "lat" in params and "lon" in params:
        st.session_state.temp_coords = {"lat": params["lat"], "lon": params["lon"]}
        st.session_state.show_click_marker = True

    st.components.v1.html(map_html, height=750)

# --- 6. ТАБЛИЦЯ ---
if not st.session_state.data.empty:
    st.dataframe(st.session_state.data, use_container_width=True)
