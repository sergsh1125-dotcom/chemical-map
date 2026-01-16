import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ... (частина коду з налаштуваннями сторінки та session_state залишається без змін)

# ===============================
# Права панель (GUI)
# ===============================
with col_gui:
    st.subheader("⚙️ Управління даними")

    st.markdown("### ➕ Додати точку вручну")
    substance = st.text_input("Назва речовини", placeholder="Наприклад: Хлор")
    lat = st.number_input("Широта (lat)", format="%.6f", value=50.4501)
    lon = st.number_input("Довгота (lon)", format="%.6f", value=30.5234)
    
    # КОРЕКТУВАННЯ: крок 0.00001 та формат з 5 знаками
    value = st.number_input(
        "Концентрація (мг/м³)", 
        min_value=0.0, 
        step=0.00001, 
        format="%.5f"
    )
    time = st.text_input("Час вимірювання", placeholder="14:00")

    if st.button("➕ Додати на карту", use_container_width=True):
        new_row = pd.DataFrame([{"lat": lat, "lon": lon, "substance": substance, "value": value, "time": time}])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.toast(f"Дані по {substance} додано!")

# ... (блок завантаження CSV та очищення залишається без змін)

# ===============================
# Візуалізація на карті
# ===============================
with col_map:
    if st.session_state.data.empty:
        st.info("Чекаю на дані...")
    else:
        df = st.session_state.data.copy()
        m = folium.Map(location=[df.lat.mean(), df.lon.mean()], zoom_start=11, control_scale=True)

        for _, r in df.iterrows():
            # КОРЕКТУВАННЯ: форматування виводу значення r['value'] до 5 знаків {:.5f}
            label_text = f"{r['substance']}: {r['value']:.5f} мг/м³ | {r['time']}"
            
            folium.map.Marker(
                [r.lat, r.lon],
                icon=folium.DivIcon(
                    icon_anchor=(-15, 7),
                    html=f"""<div style="font-family: sans-serif; font-size: 11pt; color: blue; font-weight: bold; white-space: nowrap;">{label_text}</div>"""
                )
            ).add_to(m)
            
            folium.CircleMarker(
                [r.lat, r.lon],
                radius=7,
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.8
            ).add_to(m)

        st_folium(m, width="100%", height=650, key="chem_map")
# ... (експорт у HTML залишається без змін)
