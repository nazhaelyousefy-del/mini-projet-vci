import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import folium
from streamlit_folium import st_folium
import ee

from processing import load_vci, classify_vci

st.set_page_config(page_title="Carte de sécheresse (VCI)", layout="wide")

st.title("🌍 Carte de sécheresse basée sur le VCI")

# Choix du mois
month = st.slider("Choisir le mois", min_value=1, max_value=12, value=1)

# Chargement des données
vci = load_vci(month)
classified = classify_vci(vci)

# Affichage des cartes
col1, col2 = st.columns(2)

with col1:
    st.subheader("Carte VCI")
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.imshow(vci, cmap="RdYlGn", vmin=0, vmax=100)
    ax.set_title(f"VCI - Mois {month}")
    ax.axis("off")
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    st.pyplot(fig)

with col2:
    st.subheader("Carte de classification de la sécheresse")
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    cax2 = ax2.imshow(classified, cmap="RdYlGn_r", vmin=1, vmax=4)
    ax2.set_title(f"Classes de sécheresse - Mois {month}")
    ax2.axis("off")
    fig2.colorbar(cax2, ax=ax2, fraction=0.046, pad=0.04)
    fig2.tight_layout()
    st.pyplot(fig2)

# Evolution mensuelle du VCI
st.subheader("📊 Évolution mensuelle moyenne du VCI")

vci_means = []
for month_idx in range(1, 13):
    v = load_vci(month_idx)
    vci_means.append(np.nanmean(v))

st.line_chart(vci_means)

# Carte interactive
st.subheader("🗺️ Carte interactive de la zone d'étude")

try:
    ee.Initialize(project="secheresse1")

    admin = ee.FeatureCollection("FAO/GAUL/2015/level2")

    roi = admin.filter(
        ee.Filter.And(
            ee.Filter.eq("ADM0_NAME", "Morocco"),
            ee.Filter.stringContains("ADM2_NAME", "Fès")
        )
    )

    roi_geojson = roi.getInfo()

    geom = roi.geometry()
    centroid = geom.centroid().getInfo()
    coords = centroid["coordinates"]

    lat = coords[1]
    lon = coords[0]

    folium_map = folium.Map(location=[lat, lon], zoom_start=8)

    folium.GeoJson(
        roi_geojson,
        name="Zone d'étude",
        style_function=lambda x: {
            "fillColor": "blue",
            "color": "red",
            "weight": 2,
            "fillOpacity": 0.1,
        },
    ).add_to(folium_map)

    st_folium(folium_map, width=900, height=500)

except Exception as e:
    st.warning("La carte interactive Earth Engine n'a pas pu être chargée.")
    st.error(str(e))