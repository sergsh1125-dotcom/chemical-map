import streamlit as st
import pandas as pd
import json
from datetime import datetime

# ===============================
# 1. НАЛАШТУВАННЯ СТОРІНКИ
# ===============================
st.set_page_config(
    page_title="КАРТА ХІМІЧНОЇ ОБСТАНОВКИ",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
/* Приховування службових елементів Streamlit */
#MainMenu, footer, header, .stDeployButton {visibility: hidden; display: none !important;}
.block-container {padding:1rem !important; max-width:100% !important;}
.stApp {background-color:#0e1117; color:#e0e0e0;}

/* НАЗВА ПОРТАЛУ */
.main-title {
    color:#ffcc00 !important;
    text-align:center !important;
    font-size:25px !important;
    font-weight:bold !important;
    margin-top:-30px !important;
    margin-bottom:15px !important;
    text-transform:uppercase !important;
}

/* ЗАГОЛОВКИ МОДУЛІВ */
.module-header {
    color:#ffcc00 !important;
    border-bottom:1px solid #ffcc00 !important;
    margin-top:10px !important;
    margin-bottom:8px !important;
    font-weight:bold !important;
    font-size:18px !important;
    text-transform:uppercase !important;
}

/* СТИЛІЗАЦІЯ КНОПОК */
div[data-testid="stButton"] button {
    background-color:#ffcc00 !important;
    color:#000 !important;
    font-weight:bold !important;
    width:100%;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">Модуль 1.5. Карта фактичної хімічної обстановки</p>', unsafe_allow_html=True)

# ===============================
# 2. SESSION STATE (ДАНІ)
# ===============================
if "chem_data" not in st.session_state:
    st.session_state.chem_data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])

# Перетворення даних таблиці для JavaScript (нанесення "офіційних" точок)
json_data = st.session_state.chem_data.to_json(orient='records')

# ===============================
# 3. ІНТЕРФЕЙС (КОЛОНКИ)
# ===============================
# Трошки розширимо панель для зручності
col_map, col_panel = st.columns([3.3, 1.4])

# -------- ПУЛЬТ УПРАВЛІННЯ (Права панель) --------
with col_panel:
    st.markdown('<p class="module-header">ПУЛЬТ УПРАВЛІННЯ</p>', unsafe_allow_html=True)
    
    # Форма введення точок вимірювання (Ваші оригінальні функції)
    with st.expander("➕ ДОДАТИ ТОЧКУ ВРУЧНУ", expanded=True):
        lat = st.number_input("Широта", format="%.6f", value=48.3794)
        lon = st.number_input("Довгота", format="%.6f", value=31.1656)
        substance = st.text_input("Речовина", "Хлор")
        val = st.number_input("Значення", format="%.2f", value=0.0)
        unit = st.selectbox("Одиниця", ["мг/м³", "ppm"])
        date_str = st.date_input("Дата", value=datetime.now()).strftime("%d.%m.%Y")
        
        if st.button("НАНЕСТИ НА КАРТУ"):
            new_row = pd.DataFrame([{"lat": lat, "lon": lon, "substance": substance, "value": val, "unit": unit, "time": date_str}])
            st.session_state.chem_data = pd.concat([st.session_state.chem_data, new_row], ignore_index=True)
            st.rerun()

    # Завантаження CSV (Ваші оригінальні функції)
    with st.expander("📂 ІМПОРТ З CSV"):
        uploaded_file = st.file_uploader("Виберіть файл", type="csv")
        if uploaded_file and st.button("ЗАВАНТАЖИТИ CSV"):
            try:
                df = pd.read_csv(uploaded_file)
                # Базова перевірка колонок
                required = ["lat", "lon", "substance", "value", "unit", "time"]
                if all(col in df.columns for col in required):
                    st.session_state.chem_data = pd.concat([st.session_state.chem_data, df], ignore_index=True)
                    st.success("Дані завантажено")
                    st.rerun()
                else:
                    st.error(f"Файл має містити колонки: {', '.join(required)}")
            except Exception as e:
                st.error(f"Помилка: {e}")

    if st.button("🗑️ ОЧИСТИТИ ВСІ ДАНІ ТАБЛИЦІ"):
        st.session_state.chem_data = pd.DataFrame(columns=["lat","lon","substance","value","unit","time"])
        st.rerun()

# -------- КАРТА ТА ІНСТРУМЕНТИ (Центральна панель) --------
with col_map:
    # Динамічний центр карти (середнє значення точок або центр України)
    if not st.session_state.chem_data.empty:
        c_lat = st.session_state.chem_data.lat.mean()
        c_lon = st.session_state.chem_data.lon.mean()
        zoom_val = 8
    else:
        c_lat, c_lon, zoom_val = 48.3794, 31.1656, 6

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
    <button onclick="addText()" style="padding:12px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:12px;">ТЕКСТ</button>
    <button onclick="downloadPNG()" style="padding:12px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:12px;">ЕКСПОРТ PNG</button>
    <button onclick="window.print()" style="padding:12px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:12px;">ДРУК / PDF</button>
    <button onclick="clearOperational()" style="padding:12px; background:#ffcc00; color:black; border:none; border-radius:4px; font-weight:bold; cursor:pointer; font-size:12px;">ОЧИСТИТИ ОБСТАНОВКУ</button>
</div>

<script>
var chemData = {json_data};
var map = L.map('map',{{attributionControl:false, preferCanvas: true}}).setView([{c_lat},{c_lon}], {zoom_val});

L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}.png',{{ crossOrigin: 'anonymous' }}).addTo(map);

// Група для нанесення "офіційних" даних (з таблиці)
var dataGroup = L.featureGroup().addTo(map);
// Група для нанесення оперативної обстановки (вручну)
var operationalGroup = L.featureGroup().addTo(map);

// --- 1. ВІДОБРАЖЕННЯ ДАНИХ З ТАБЛИЦІ (Ваші оригінальні стилі) ---
chemData.forEach(function(r) {{
    var lat = parseFloat(r.lat);
    var lon = parseFloat(r.lon);
    
    // Точка вимірювання (Помаранчева, як у вас)
    L.circleMarker([lat, lon], {{
        radius: 6, color: "orange", fillColor: "orange", fillOpacity: 1, weight: 2
    }}).addTo(dataGroup);

    // Підпис (Синій текст з лінією, як у вас)
    var labelHtml = `
        <div style="display:inline-block; font-family:Arial; font-size:10pt; color:blue; font-weight:bold; text-align:center; white-space:nowrap; text-shadow:2px 2px 2px #fff;">
            <div style="border-bottom: 2px solid blue; padding-bottom:2px; margin-bottom:2px;">
                ${{r.substance}} ${{r.value}} ${{r.unit}}
            </div>
            <div style="font-weight:normal;">${{r.time}}</div>
        </div>`;
    
    L.marker([lat, lon], {{
        icon: L.divIcon({{ html: labelHtml, iconAnchor: [80, 45], className: '' }})
    }}).addTo(dataGroup);
}});

// --- 2. ПАНЕЛЬ МАЛЮВАННЯ (Як вчора, але маркер дефолтний) ---
// Більше не визначаємо custom radIcon. Leaflet.draw використає дефолтну синю шпильку.

var drawControl = new L.Control.Draw({{
    draw:{{
        polygon: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        rectangle: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        circle: {{ shapeOptions: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.5, weight: 2 }} }},
        polyline: {{ shapeOptions: {{ color: 'black', weight: 3 }} }},
        // ЗМІНЕНО: marker:true активує стандартну синю шпильку
        marker: true,
        // Жовта точка (фіксований розмір)
        circlemarker: {{ color: 'black', fillColor: 'yellow', fillOpacity: 0.9, radius: 8 }}
    }},
    edit: {{ featureGroup: operationalGroup }}
}});
map.addControl(drawControl);

map.on(L.Draw.Event.CREATED, function(e){{
    var layer = e.layer;
    // Дефолтний маркер залишаємо як є, для інших фігур - жовте заповнення
    if(e.layerType !== 'marker' && e.layerType !== 'circlemarker' && e.layerType !== 'polyline') {{
        layer.setStyle({{color:'black', fillColor:'yellow', fillOpacity:0.5}});
    }}
    // Додаємо в групу оперативної обстановки
    operationalGroup.addLayer(layer);
    
    // Завершення операції (один клік - одна фігура)
    drawControl._toolbars.draw._modes[e.layerType].handler.disable();
}});

// --- 3. ФУНКЦІЇ ІНТЕРФЕЙСУ ---
function addText(){{{
    var t = prompt("Введіть текст:");
    if(t) {{{
        map.once('click', function(e){{{
            L.marker(e.latlng, {{{ icon: L.divIcon({{{
                html: '<div style="background:white; border:1px solid black; padding:2px; font-weight:bold; color:black;">'+t+'</div>',
                className: ''
            }}}) }}}).addTo(operationalGroup);
        }}});
    }}}
}}}

function clearOperational() {{{
    if(confirm("Видалити нанесену оперативну обстановку (фігури, текст)? Таблиця вимірювань залишиться.")) {{{
        operationalGroup.clearLayers();
    }}}
}}}

function downloadPNG(){{{
    const area = document.getElementById("capture_area");
    html2canvas(area, {{{
        useCORS: true, 
        scale: 2, 
        scrollY: -window.scrollY // Стабільний експорт
    }}}).then(canvas => {{{
        var link = document.createElement("a");
        link.download = "Chemical_Situation_Report.png";
        link.href = canvas.toDataURL();
        link.click();
    }}});
}}}
</script>
"""
    components.html(map_html, height=730)

# -------- ТАБЛИЦЯ ДАНИХ (Внизу сторінки) --------
if not st.session_state.chem_data.empty:
    st.markdown('<p class="module-header">ЖУРНАЛ ХІМІЧНИХ ВИМІРЮВАНЬ</p>', unsafe_allow_html=True)
    # Зручніше відображення
    df_display = st.session_state.chem_data.rename(columns={
        "lat":"Широта", "lon":"Довгота", "substance":"Речовина", 
        "value":"Значення", "unit":"Одиниця", "time":"Дата/Час"
    })
    st.dataframe(df_display, use_container_width=True)
