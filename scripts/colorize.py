#!/usr/bin/env python3
"""Colorize a grayscale era mosaic using the pixel-aligned modern NAIP image.

Method: keep the historical luminance; take chrominance (Lab a,b) from the
aligned NAIP 2022 image, low-pass filtered so modern small-scale detail
(cars, roof colors) doesn't imprint. Where historical and modern content
clearly disagree (new construction, the freeway cut), fall back toward a
neutral terrain palette estimated from the era image itself.

Usage: colorize.py <era_gray.tif> <naip_rgb.tif> <out_rgb.tif> [--sigma 6]
"""
import argparse
import numpy as np, cv2, rasterio

ap = argparse.ArgumentParser()
ap.add_argument("era"); ap.add_argument("naip"); ap.add_argument("out")
ap.add_argument("--sigma", type=float, default=6.0)
ap.add_argument("--preview", default=None)
a = ap.parse_args()

with rasterio.open(a.era) as s:
    L_era = s.read(1)
    prof = s.profile.copy()
    H, W = L_era.shape
with rasterio.open(a.naip) as s:
    naip = np.moveaxis(s.read([1, 2, 3]), 0, -1)
if naip.shape[:2] != (H, W):
    naip = cv2.resize(naip, (W, H), interpolation=cv2.INTER_AREA)

valid = L_era > 0

# --- tone-normalize era luminance to NAIP's L distribution (histogram match)
naip_lab = cv2.cvtColor(naip, cv2.COLOR_RGB2Lab)
L_naip, A_naip, B_naip = cv2.split(naip_lab)
src_vals = L_era[valid].ravel()
ref_vals = L_naip[L_naip > 0].ravel()
s_quant = np.percentile(src_vals, np.linspace(0, 100, 256))
r_quant = np.percentile(ref_vals, np.linspace(0, 100, 256))
lut = np.interp(np.arange(256), s_quant, r_quant).astype(np.uint8)
L_matched = cv2.LUT(L_era, lut)

# --- chroma: low-passed modern a,b
sig = a.sigma
A_lp = cv2.GaussianBlur(A_naip, (0, 0), sig)
B_lp = cv2.GaussianBlur(B_naip, (0, 0), sig)

# --- mismatch mask: where structures differ, modern chroma is wrong.
# compare band-passed luminance structure at medium scale
def structure(x):
    x = x.astype(np.float32)
    return cv2.GaussianBlur(x, (0, 0), 3) - cv2.GaussianBlur(x, (0, 0), 12)
d = np.abs(structure(L_matched) - structure(L_naip))
d = cv2.GaussianBlur(d, (0, 0), 8)
mism = np.clip((d - 6.0) / 18.0, 0, 1)  # 0 = agrees, 1 = disagrees

# neutral terrain chroma: median chroma of low-mismatch vegetated/dirt pixels,
# split into "dark" (vegetation/shadow) and "bright" (dirt/roads) by era luminance
dark = (L_matched < 110) & valid & (mism < 0.3)
bright = (L_matched >= 110) & valid & (mism < 0.3)
def med(ch, m, fallback):
    return float(np.median(ch[m])) if m.sum() > 500 else fallback
A_dark, B_dark = med(A_naip, dark, 122), med(B_naip, dark, 134)
A_brt, B_brt = med(A_naip, bright, 128), med(B_naip, bright, 138)
t = np.clip((L_matched.astype(np.float32) - 90) / 60, 0, 1)
A_neut = (A_dark * (1 - t) + A_brt * t)
B_neut = (B_dark * (1 - t) + B_brt * t)

A_fin = (A_lp * (1 - mism) + A_neut * mism).astype(np.uint8)
B_fin = (B_lp * (1 - mism) + B_neut * mism).astype(np.uint8)

out = cv2.cvtColor(cv2.merge([L_matched, A_fin, B_fin]), cv2.COLOR_Lab2RGB)
out[~valid] = 0

prof.update(count=3, photometric="RGB")
with rasterio.open(a.out, "w", **prof) as d_:
    d_.write(np.moveaxis(out, -1, 0))
print("wrote", a.out)

if a.preview:
    sc = 1300 / max(H, W)
    cv2.imwrite(a.preview, cv2.cvtColor(cv2.resize(out, None, fx=sc, fy=sc), cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("wrote", a.preview)
