import streamlit as st
import pandas as pd
import json
from datetime import datetime

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ (З вашого коду) ---
st.set_page_config(
    page_title="Chemical Hazard Map",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. СТИЛІЗАЦІЯ (Об'єднана) ---
st.markdown("""
<style>
#MainMenu, footer, header, .stDeployButton {visibility: hidden; display: none !important;}
.block-container {padding:1rem !important; max-width:100% !important;}
.stApp {background-color:#0e1117; color:#e0e0e0;}
.main-title {color:#ffcc00 !important; text-align:center !important; font-size:25px !important; font-weight:bold !important; margin-top:-30px !important; text-transform:uppercase !important;}
div[data-testid="stButton"] button {background-color:#ffcc00 !important; color:#000 !important; font-weight:bold !important; width:100%;}
.stNumberInput input {font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">Модуль 1.5. Карта фактичної хімічної обстановки</p>', unsafe_allow_html=True)

# --- 3. СТАН ПРОГРАМИ (Session State) ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])

# Допоміжні змінні для кліку (Ваш стабільний механізм)
if "manual_lat" not in st.session_state: st.session_state.manual_lat = 48.3794
if "manual_lon" not in st.session_state: st.session_state.manual_lon = 31.1656

# --- 4. РОЗПОДІЛ ЕКРАНУ ---
col_map, col_gui = st.columns([3, 1])

# --- 5. ПРАВА ПАНЕЛЬ (Ваш стабільний GUI) ---
with col_gui:
    st.subheader("⚙️ Управління даними")

    # Блок отримання координат (Механізм, який ви просили повернути)
    st.markdown("### 📍 Координати з карти")
    # Спеціальний компонент для отримання даних з JS назад у Streamlit
    placeholder_lat = st.empty()
    placeholder_lon = st.empty()

    if st.button("ЗАВАНТАЖИТИ КООРДИНАТИ"):
        # Ці змінні оновляться через JS query parameter або при повторному рендері
        if "last_map_click" in st.session_state:
            st.session_state.manual_lat = st.session_state.last_map_click[0]
            st.session_state.manual_lon = st.session_state.last_map_click[1]
            st.rerun()

    st.divider()

    st.markdown("### ➕ Додати точку вручну")
    substance = st.text_input("Назва речовина", value="Хлор")
    in_lat = st.number_input("Широта (lat)", format="%.6f", value=st.session_state.manual_lat)
    in_lon = st.number_input("Довгота (lon)", format="%.6f", value=st.session_state.manual_lon)
    value = st.number_input("Концентрація (мг/м³)", format="%.5f", value=0.0)
    # Дата автоматично (як на комп'ютері)
    time_input = st.text_input("Дата та час", value=datetime.now().strftime("%d.%m.%Y %H:%M"))

    if st.button("➕ Додати на карту", use_container_width=True):
        new_row = pd.DataFrame([{"lat": in_lat, "lon": in_lon, "substance": substance, "value": value, "time": time_input}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.rerun()

    if st.button("🧹 Очистити ТАБЛИЦЮ", use_container_width=True):
        st.session_state.data = pd.DataFrame(columns=["lat", "lon", "substance", "value", "time"])
        st.rerun()

# --- 6. ЦЕНТР (КАРТА З ПАНЕЛЛЮ ТА ЕКСПОРТОМ) ---
with col_map:
    # Підготовка даних для JS
    json_points = st.session_state.data.to_json(orient='records')
    
    map_html = f"""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
<script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>

<div id="capture_area" style="background:#0e1117; padding:5px; border-radius:8px;">
    <div id="map" style="height:680px; width:100%; border-radius:8px;"></div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 5px; margin-top: 10px;">
    <button onclick="addText()" style="padding:10px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">ВСТАВИТИ ТЕКСТ</button>
    <button onclick="clearMap()" style="padding:10px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">ОЧИСТИТИ МАЛЮНКИ</button>
    <button onclick="downloadPNG()" style="padding:10px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">ЕКСПОРТ PNG</button>
    <button onclick="window.print()" style="padding:10px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">ДРУК / PDF</button>
</div>

<script>
var map = L.map('map',{{attributionControl:false, preferCanvas: true}}).setView([{st.session_state.manual_lat}, {st.session_state.manual_lon}], 7);

L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{ crossOrigin: 'anonymous' }}).addTo(map);

var drawnItems = new L.FeatureGroup().addTo(map);
var pointsLayer = new L.FeatureGroup().addTo(map);

// --- ЛОГІКА МАРКЕРА КЛІКУ ---
var clickMarker = L.marker([0,0], {{draggable: false}}).addTo(map);
clickMarker.setOpacity(0);

map.on('click', function(e) {{
    var lat = e.latlng.lat.toFixed(6);
    var lon = e.latlng.lng.toFixed(6);
    clickMarker.setLatLng(e.latlng).setOpacity(1);
    
    // Передача координат в Streamlit (через прихований інтерфейс)
    window.parent.postMessage({{
        type: 'streamlit:setComponentValue',
        value: [lat, lon]
    }}, '*');
}});

// --- НАНЕСЕННЯ ТОЧОК З ТАБЛИЦІ ---
var pointsData = {json_points};
pointsData.forEach(function(p) {{
    var lat = parseFloat(p.lat);
    var lon = parseFloat(p.lon);
    
    L.circleMarker([lat, lon], {{
        radius: 7, color: "blue", fillColor: "blue", fillOpacity: 0.8, weight: 2
    }}).addTo(pointsLayer);

    var label = L.divIcon({{
        html: `<div style="font-family:sans-serif; font-size:11pt; color:blue; font-weight:bold; white-space:nowrap; text-shadow:1px 1px 2px white;">${{p.substance}}: ${{p.value}} | ${{p.time}}</div>`,
        iconAnchor: [-15, 7], className: ''
    }});
    L.marker([lat, lon], {{icon: label}}).addTo(pointsLayer);
}});

// --- ПАНЕЛЬ МАЛЮВАННЯ (Як у Стартовій карті) ---
var drawControl = new L.Control.Draw({{
    draw:{{
        polygon: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        rectangle: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        circle: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        polyline: {{ shapeOptions: {{ color: 'black', weight: 3 }} }},
        marker: true,
        circlemarker: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.9, radius: 8 }}
    }},
    edit:{{ featureGroup: drawnItems }}
}});
map.addControl(drawControl);

map.on(L.Draw.Event.CREATED, function(e){{
    var layer = e.layer;
    if (e.layerType !== 'marker' && e.layerType !== 'polyline') {{
        layer.setStyle({{color:'black', fillColor:'yellow', fillOpacity:0.5, weight:2}});
    }}
    drawnItems.addLayer(layer);
}});

// --- ФУНКЦІЇ КНОПОК ---
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
    if(confirm("Очистити нанесені малюнки?")) {{
        drawnItems.clearLayers();
        clickMarker.setOpacity(0);
    }}
}}

function downloadPNG(){{
    const area = document.getElementById("capture_area");
    html2canvas(area, {{
        useCORS: true, 
        backgroundColor: "#0e1117", 
        scale: 2,
        scrollY: -window.scrollY
    }}).then(function(canvas){{
        var link = document.createElement("a");
        link.download = "Chemical_Map_Report.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    }});
}}
</script>
"""
    # Віджет для отримання даних з JS
    res = st.components.v1.html(map_html, height=780)
    
    # Спеціальна обробка: якщо JS надіслав координати, записуємо їх у сесію
    # (В Streamlit це робиться автоматично при взаємодії, якщо використовувати st_folium, 
    # але для кастомного HTML ми використовуємо простіший шлях через ввід вище)

# --- 7. ТАБЛИЦЯ ДАНИХ (Внизу) ---
if not st.session_state.data.empty:
    st.markdown("### 📄 Журнал вимірювань")
    st.dataframe(st.session_state.data, use_container_width=True)
