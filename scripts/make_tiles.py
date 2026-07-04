#!/usr/bin/env python3
"""Cut era GeoTIFFs (EPSG:3857, AOI grid) into XYZ WebP tiles for static hosting.

Usage: make_tiles.py <era.tif> <outdir> [--zmin 12] [--zmax 17] [--q 80]
Nodata (0) becomes transparent alpha. Tiles fully outside coverage are skipped.
"""
import argparse, os, math
import numpy as np, rasterio, mercantile
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("raster"); ap.add_argument("outdir")
ap.add_argument("--zmin", type=int, default=12)
ap.add_argument("--zmax", type=int, default=17)
ap.add_argument("--q", type=int, default=80)
a = ap.parse_args()

with rasterio.open(a.raster) as src:
    data = src.read()          # (bands, H, W)
    T = src.transform
    left, top = T.c, T.f
    res = T.a
    H, W = data.shape[1], data.shape[2]
    right, bottom = left + W * res, top - H * res

bands = data.shape[0]
alpha_src = (data.max(axis=0) > 0)

from rasterio.warp import transform as tr
w84, s84 = tr("EPSG:3857", "EPSG:4326", [left], [bottom])
e84, n84 = tr("EPSG:3857", "EPSG:4326", [right], [top])
bbox = (w84[0], s84[0][0] if isinstance(s84[0], list) else s84[0], e84[0], n84[0])
# rasterio transform returns ([x],[y])
w84 = bbox[0]; s84 = bbox[1]; e84 = bbox[2]; n84 = bbox[3]

count = 0
size_total = 0
for z in range(a.zmin, a.zmax + 1):
    for t in mercantile.tiles(w84, s84, e84, n84, [z]):
        tb = mercantile.xy_bounds(t)
        # source pixel window for this tile
        x0 = (tb.left - left) / res; x1 = (tb.right - left) / res
        y0 = (top - tb.top) / res;  y1 = (top - tb.bottom) / res
        xi0, xi1 = int(math.floor(x0)), int(math.ceil(x1))
        yi0, yi1 = int(math.floor(y0)), int(math.ceil(y1))
        if xi1 <= 0 or yi1 <= 0 or xi0 >= W or yi0 >= H:
            continue
        cx0, cy0 = max(0, xi0), max(0, yi0)
        cx1, cy1 = min(W, xi1), min(H, yi1)
        sub = data[:, cy0:cy1, cx0:cx1]
        if sub.size == 0 or not (sub.max(axis=0) > 0).any():
            continue
        # paste into full tile-extent array (handles partial edge tiles)
        fw, fh = xi1 - xi0, yi1 - yi0
        full = np.zeros((bands, fh, fw), dtype=np.uint8)
        full[:, cy0 - yi0:cy1 - yi0, cx0 - xi0:cx1 - xi0] = sub
        am = np.zeros((fh, fw), dtype=np.uint8)
        am[cy0 - yi0:cy1 - yi0, cx0 - xi0:cx1 - xi0] = alpha_src[cy0:cy1, cx0:cx1] * 255
        if bands == 1:
            img = np.stack([full[0]] * 3 + [am], axis=-1)
        else:
            img = np.concatenate([np.moveaxis(full, 0, -1), am[..., None]], axis=-1)
        pil = Image.fromarray(img, "RGBA").resize((256, 256), Image.BILINEAR)
        d = os.path.join(a.outdir, str(z), str(t.x))
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, f"{t.y}.webp")
        pil.save(p, "WEBP", quality=a.q, method=4)
        count += 1
        size_total += os.path.getsize(p)

print(f"{a.raster} -> {a.outdir}: {count} tiles, {size_total/1e6:.1f} MB (z{a.zmin}-{a.zmax})")
