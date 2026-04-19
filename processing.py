import ee
import numpy as np
import requests  #télécharger des données depuis une URL
import io #lire les données en mémoire (sans fichier sur disque)

#ee.Initialize(project="secheresse1")

import ee

if not ee.data._credentials:
    ee.Initialize()
# =========================
# ROI
# =========================
def get_roi():
    admin = ee.FeatureCollection("FAO/GAUL/2015/level2")
    roi = admin.filter(
        ee.Filter.And(
            ee.Filter.eq("ADM0_NAME", "Morocco"),
            ee.Filter.stringContains("ADM2_NAME", "Fès")
        )
    )
    return roi.geometry()


# =========================
# VCI CORRECT
# =========================
def compute_vci_gee(year, month):

    geom = get_roi()

    collection = ee.ImageCollection("MODIS/061/MOD13Q1") \
        .select("NDVI") \
        .filterBounds(geom)

    # 📌 période mois année
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, "month")

    ndvi_month = collection.filterDate(start, end).mean()

    # 📌 climatologie mensuelle (2001–2023)
    climatology = collection.filterDate("2001-01-01", "2023-12-31")

    ndvi_min = climatology.min()
    ndvi_max = climatology.max()

    vci = ndvi_month.subtract(ndvi_min) \
        .divide(ndvi_max.subtract(ndvi_min)) \
        .multiply(100) \
        .clip(geom)

    return vci


# =========================
# NDVI CORRECT
# =========================
def compute_ndvi_gee(year, month):

    geom = get_roi()

    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, "month")

    ndvi = ee.ImageCollection("MODIS/061/MOD13Q1") \
        .select("NDVI") \
        .filterBounds(geom) \
        .filterDate(start, end) \
        .mean() \
        .multiply(0.0001) \
        .clip(geom)

    return ndvi


# =========================
# GEE → NUMPY
# =========================
def gee_to_numpy(image, region):

    url = image.getDownloadURL({
        "scale": 250,
        "region": region,
        "format": "NPY"
    })

    response = requests.get(url)
    data = np.load(io.BytesIO(response.content), allow_pickle=True)

    return np.array(data).astype(float)


# =========================
# CORRELATION
# =========================
def vci_ndvi_correlation(vci, ndvi):

    vci = vci.flatten()
    ndvi = ndvi.flatten()

    mask = (~np.isnan(vci)) & (~np.isnan(ndvi))

    if np.sum(mask) == 0:
        return 0

    return np.corrcoef(vci[mask], ndvi[mask])[0, 1]


# =========================
# STATS
# =========================
def compute_stats_from_vci(vci_array):

    total = np.sum(~np.isnan(vci_array))

    if total == 0:
        return {1: 0, 2: 0, 3: 0, 4: 0}

    return {
        1: np.sum(vci_array >= 60) / total * 100,
        2: np.sum((vci_array >= 40) & (vci_array < 60)) / total * 100,
        3: np.sum((vci_array >= 20) & (vci_array < 40)) / total * 100,
        4: np.sum(vci_array < 20) / total * 100,
    }


# =========================
# IMAGE DOWNLOAD
# =========================
def get_vci_png_url(image, region):

    region = region.simplify(1000)

    return image.getThumbURL({
        "min": 0,
        "max": 100,
        "region": region,
        "dimensions": 512,
        "palette": ["#8B0000", "#FF4500", "#FFD700", "#7CFC00", "#006400"]
    })

def get_vci_download_url(image, region, year, month):

    region = region.simplify(1000)

    filename = f"VCI_{year}_{month:02d}"

    url = image.getDownloadURL({
        "scale": 250,
        "region": region,
        "format": "GeoTIFF",
        "fileNamePrefix": filename
    })

    return url, filename