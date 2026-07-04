#!/usr/bin/env python3
"""Clip NAIP 2022 COGs to AOI via bounded WarpedVRTs (only AOI window requested)."""
import numpy as np, rasterio
from rasterio.vrt import WarpedVRT
from rasterio.transform import Affine
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling

AOI = (-118.245, 34.150, -118.210, 34.195)
URLS = [
 "https://naipeuwest.blob.core.windows.net/naip/v002/ca/2022/ca_060cm_2022/34118/m_3411855_nw_11_060_20220505.tif",
 "https://naipeuwest.blob.core.windows.net/naip/v002/ca/2022/ca_060cm_2022/34118/m_3411855_sw_11_060_20220511.tif",
]
b = transform_bounds("EPSG:4326", "EPSG:3857", *AOI)
RES = 0.72
W, H = int((b[2]-b[0])/RES), int((b[3]-b[1])/RES)
T = Affine(RES, 0, b[0], 0, -RES, b[3])
acc = np.zeros((3, H, W), np.uint8)
for u in URLS:
    with rasterio.open("/vsicurl/" + u) as s:
        with WarpedVRT(s, crs="EPSG:3857", transform=T, width=W, height=H,
                       resampling=Resampling.bilinear) as v:
            d = v.read([1, 2, 3])
            m = d.any(axis=0)
            acc[:, m] = d[:, m]
    print("done", u.rsplit('/',1)[1], flush=True)
prof = dict(driver="GTiff", height=H, width=W, count=3, dtype="uint8", crs="EPSG:3857",
            transform=T, compress="deflate", tiled=True, photometric="RGB")
with rasterio.open("data/processed/naip2022_aoi_3857.tif", "w", **prof) as dst:
    dst.write(acc)
print("wrote data/processed/naip2022_aoi_3857.tif", acc.shape)
