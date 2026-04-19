import streamlit as st
import folium
from streamlit_folium import st_folium
import ee
import processing
import numpy as np
import pandas as pd

st.set_page_config(page_title="VCI App", layout="wide")
st.title("🌍 Carte de sécheresse VCI")

# =========================
# INPUT
# =========================
year = st.selectbox("Année", [2021, 2022, 2023])
month = st.slider("Mois", 1, 12, 1)

roi = processing.get_roi()

# =========================
# VCI & NDVI
# =========================
vci_image = processing.compute_vci_gee(year, month)
ndvi_image = processing.compute_ndvi_gee(year, month)

vci_array = processing.gee_to_numpy(vci_image, roi)
ndvi_array = processing.gee_to_numpy(ndvi_image, roi)

corr = processing.vci_ndvi_correlation(vci_array, ndvi_array)

st.metric("Corrélation VCI / NDVI", round(corr, 3))

# =========================
# IMAGE VCI
# =========================
st.subheader("Carte VCI")

url = processing.get_vci_png_url(vci_image, roi)
st.image(url, width=600)

# =========================
# STATS
# =========================
st.subheader("Statistiques")

stats = processing.compute_stats_from_vci(vci_array)

st.write(stats)

# =========================
# 3 ANS EVOLUTION
# =========================
years = [2021, 2022, 2023]
values = []

for y in years:
    img = processing.compute_vci_gee(y, month)
    arr = processing.gee_to_numpy(img, roi)
    values.append(np.nanmean(arr))

df = pd.DataFrame({
    "Année": years,
    "VCI": values
})

st.subheader("Évolution 3 ans")
st.line_chart(df.set_index("Année"))

# =========================
# MAP
# =========================
centroid = roi.centroid().getInfo()["coordinates"]

m = folium.Map(location=[centroid[1], centroid[0]], zoom_start=8)

map_id = vci_image.getMapId({
    "min": 0,
    "max": 100,
    "palette": ["red", "yellow", "green"]
})

folium.TileLayer(
    tiles=map_id["tile_fetcher"].url_format,
    attr="GEE",
    name="VCI"
).add_to(m)

folium.LayerControl().add_to(m)

st_folium(m, width=900, height=500)



st.subheader("📥 Télécharger VCI")

if st.button("⬇️ Télécharger GeoTIFF"):

    try:
        region = roi

        url, filename = processing.get_vci_download_url(
            vci_image,
            region,
            year,
            month
        )

        st.success("Téléchargement prêt")

        st.markdown(f"""
        ### 📥 Fichier : **{filename}.tif**
        👉 [Clique ici pour télécharger]({url})
        """)

    except Exception as e:
        st.error("Erreur téléchargement")
        st.error(str(e))