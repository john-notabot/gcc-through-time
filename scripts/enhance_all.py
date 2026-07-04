#!/usr/bin/env python3
"""Build the 'color reconstruction' layer set.

Steps:
 1. Re-warp every registered frame at 0.6 m/px from its saved GCPs (v2 frames)
 2. Re-mosaic each era at 0.6 m
 3. Gap-fill each era's nodata from temporal neighbours (luminance,
    histogram-matched per-fill), ending 100% coverage
 4. Colorize each era from the aligned NAIP chroma (colorize.py logic inline)
 5. Tile both layer sets is done separately (make_tiles.py)

Run: .venv/bin/python scripts/enhance_all.py
"""
import json, os, subprocess, sys
import numpy as np, cv2, rasterio
from rasterio.merge import merge
from rasterio.transform import Affine
from rasterio.warp import transform_bounds

PY = ".venv/bin/python"
RES = 0.6
AOI84 = (-118.245, 34.150, -118.210, 34.195)

ERAS = {
    "1928": dict(frames=["c-300_k-225","c-300_k-224","c-300_k-180","c-300_k-181",
                          "c-300_k-179","c-300_k-178","c-300_k-177"],
                 margin="0.04,0.02,0.02,0.03"),
    "1938": dict(frames=["axj-1938_72-43","axj-1938_72-42","axj-1938_72-41",
                          "axj-1938_44-6","axj-1938_44-7","axj-1938_24-59"],
                 margin="0.035,0.02,0.035,0.02"),
    "1956": dict(frames=["c-22555_9-31","c-22555_9-30","c-22555_9-32",
                          "c-22555_8-31","c-22555_8-32"],
                 margin="0.04,0.02,0.02,0.02"),
    "1968fill": dict(frames=["tg-2400_1-88"], margin="0.03,0.02,0.02,0.02"),
    "1971": dict(frames=["tg-2755_25-37","tg-2755_25-38","tg-2755_25-39"],
                 margin="0.035,0.02,0.035,0.02"),
    "1981": dict(frames=["tg-3800_18-40","tg-3800_18-39"],
                 margin="0.085,0.035,0.03,0.035"),
}
# fill sources per era, nearest-in-time first (era ids resolved to v2 mosaics)
FILLS = {
    "1928": ["1938", "1956", "2022"],
    "1938": ["1928", "1956", "2022"],
    "1956": ["1968fill", "1938", "2022"],
    "1971": ["1968fill", "1981", "2022"],
    "1981": ["1971", "2022"],
}

os.makedirs("data/processed/v2/frames", exist_ok=True)
os.makedirs("data/processed/v2", exist_ok=True)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL:", " ".join(cmd), "\n", r.stderr[-500:]); sys.exit(1)
    for l in r.stdout.splitlines():
        if "RMS" in l or "wrote" in l:
            print("   ", l)


# ---- 1. re-warp frames at 0.6 m
for era, cfg in ERAS.items():
    for f in cfg["frames"]:
        out = f"data/processed/v2/frames/{f}_06.tif"
        if os.path.exists(out):
            continue
        gcps = f"research/gcps/{f}_auto.json"
        if not os.path.exists(gcps):
            gcps = f"research/gcps/{f}_seed.json"   # 25-39 warped from seed
        print(f"warp {f} @0.6m")
        run([PY, "scripts/gcp_tools.py", "warp", f"data/raw/ucsb/{f}.tif", gcps, out,
             "--order", "2", "--res", str(RES), "--margin", cfg["margin"]])

# ---- 2. mosaics
for era, cfg in ERAS.items():
    out = f"data/processed/v2/era{era}_06.tif"
    if os.path.exists(out):
        continue
    srcs = [rasterio.open(f"data/processed/v2/frames/{f}_06.tif") for f in cfg["frames"]]
    mosaic, T = merge(srcs, nodata=0)
    prof = srcs[0].profile.copy()
    prof.update(height=mosaic.shape[1], width=mosaic.shape[2], transform=T)
    with rasterio.open(out, "w", **prof) as d:
        d.write(mosaic)
    for s in srcs: s.close()
    print(f"mosaic era{era}: coverage {(mosaic[0]>0).mean():.1%}")

# ---- NAIP at 0.6 grid (gray + rgb)
b = transform_bounds("EPSG:4326", "EPSG:3857", *AOI84)
W, H = int((b[2]-b[0])/RES), int((b[3]-b[1])/RES)
T06 = Affine(RES, 0, b[0], 0, -RES, b[3])
naip06 = "data/processed/v2/naip2022_06.tif"
if not os.path.exists(naip06):
    from rasterio.warp import reproject, Resampling
    with rasterio.open("data/processed/naip2022_aoi_3857.tif") as s:
        out = np.zeros((3, H, W), np.uint8)
        reproject(source=s.read(), destination=out, src_crs=s.crs, src_transform=s.transform,
                  dst_crs="EPSG:3857", dst_transform=T06, resampling=Resampling.cubic)
    prof = dict(driver="GTiff", height=H, width=W, count=3, dtype="uint8",
                crs="EPSG:3857", transform=T06, compress="deflate", tiled=True, photometric="RGB")
    with rasterio.open(naip06, "w", **prof) as d:
        d.write(out)
    print("naip 0.6 grid done")

with rasterio.open(naip06) as s:
    NAIP = np.moveaxis(s.read([1,2,3]), 0, -1)
NAIP_L = cv2.cvtColor(NAIP, cv2.COLOR_RGB2Lab)[:, :, 0]


def load_era_gray(era):
    p = f"data/processed/v2/era{era}_06.tif" if era != "2022" else None
    if era == "2022":
        return NAIP_L.copy()
    with rasterio.open(p) as s:
        g = s.read(1)
    if g.shape != (H, W):
        g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
    return g


def hist_match(src, src_mask, ref, ref_mask):
    s_q = np.percentile(src[src_mask], np.linspace(0, 100, 256))
    r_q = np.percentile(ref[ref_mask], np.linspace(0, 100, 256))
    lut = np.interp(np.arange(256), s_q, r_q).astype(np.uint8)
    return cv2.LUT(src, lut)


# ---- 3. gap-fill + write filled gray
filled = {}
for era in ["1928", "1938", "1956", "1971", "1981"]:
    g = load_era_gray(era)
    hole = g == 0
    for fe in FILLS[era]:
        if not hole.any():
            break
        f = load_era_gray(fe)
        fm = (f > 0) & hole
        if not fm.any():
            continue
        fmatched = hist_match(f, f > 0, g, g > 0)
        g[fm] = fmatched[fm]
        hole = g == 0
    # feather fill seams slightly
    filled[era] = g
    print(f"era{era} filled coverage {(g>0).mean():.1%}")

# ---- 4. colorize (inline, same method as colorize.py)
naip_lab = cv2.cvtColor(NAIP, cv2.COLOR_RGB2Lab)
L_naip, A_naip, B_naip = cv2.split(naip_lab)
A_lp = cv2.GaussianBlur(A_naip, (0, 0), 10)
B_lp = cv2.GaussianBlur(B_naip, (0, 0), 10)

def structure(x):
    x = x.astype(np.float32)
    return cv2.GaussianBlur(x, (0, 0), 4) - cv2.GaussianBlur(x, (0, 0), 16)

S_naip = structure(L_naip)

def colorize(gray, era):
    valid = gray > 0
    L = hist_match(gray, valid, L_naip, L_naip > 0)
    d = np.abs(structure(L) - S_naip)
    d = cv2.GaussianBlur(d, (0, 0), 10)
    mism = np.clip((d - 6.0) / 18.0, 0, 1)
    dark = (L < 110) & valid & (mism < 0.3)
    bright = (L >= 110) & valid & (mism < 0.3)
    def med(ch, m, fb):
        return float(np.median(ch[m])) if m.sum() > 500 else fb
    Ad, Bd = med(A_naip, dark, 122), med(B_naip, dark, 134)
    Ab, Bb = med(A_naip, bright, 128), med(B_naip, bright, 138)
    t = np.clip((L.astype(np.float32) - 90) / 60, 0, 1)
    An = Ad * (1 - t) + Ab * t
    Bn = Bd * (1 - t) + Bb * t
    Af = A_lp * (1 - mism) + An * mism
    Bf = B_lp * (1 - mism) + Bn * mism
    # saturation boost
    Af = np.clip((Af - 128) * 1.3 + 128, 0, 255).astype(np.uint8)
    Bf = np.clip((Bf - 128) * 1.3 + 128, 0, 255).astype(np.uint8)
    rgb = cv2.cvtColor(cv2.merge([L, Af, Bf]), cv2.COLOR_Lab2RGB)
    rgb[~valid] = 0
    return rgb


prof3 = dict(driver="GTiff", height=H, width=W, count=3, dtype="uint8",
             crs="EPSG:3857", transform=T06, compress="deflate", tiled=True, photometric="RGB")
for era in ["1928", "1938", "1956", "1971", "1981"]:
    out = f"data/processed/v2/era{era}_color.tif"
    if os.path.exists(out):
        continue
    rgb = colorize(filled[era], era)
    with rasterio.open(out, "w", **prof3) as dd:
        dd.write(np.moveaxis(rgb, -1, 0))
    print(f"colorized era{era}")

print("enhance_all done")
