import os
import numpy as np
import rasterio


def load_vci(month):
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "data", "outputs", f"VCI_2023_{month}.tif")

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Fichier introuvable : {file_path}\n"
            f"Vérifie que le raster du mois {month} existe bien dans data/outputs."
        )

    with rasterio.open(file_path) as src:
        vci = src.read(1).astype(float)

    vci = np.where(vci <= 0, np.nan, vci)

    return vci


def classify_vci(vci):
    classification = np.full(vci.shape, np.nan)

    classification[(vci >= 0) & (vci < 20)] = 1
    classification[(vci >= 20) & (vci < 40)] = 2
    classification[(vci >= 40) & (vci < 60)] = 3
    classification[vci >= 60] = 4

    return classification