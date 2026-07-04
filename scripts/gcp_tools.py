#!/usr/bin/env python3
"""Helpers for manual GCP picking.

mark  <geotiff> <out.jpg> --points p1.json   annotate georeferenced raster with labeled points
crop  <raster> <out.jpg> --cx --cy --hw      crop raw scan around pixel, grid ticks every 100 px
warp  <scan> <gcps.json> <out.tif>           warp scan to 3857 AOI grid using GCP list
                                             gcps.json: [{"px":..,"py":..,"lon":..,"lat":..}]
"""
import sys, json, argparse
import numpy as np, cv2, rasterio
from rasterio.transform import Affine
from rasterio.control import GroundControlPoint
from rasterio.warp import reproject, Resampling, transform_bounds, transform as rio_transform

AOI84 = (-118.245, 34.150, -118.210, 34.195)


def read_rgb(path, max_dim=None):
    with rasterio.open(path) as s:
        if max_dim:
            sc = max(s.width, s.height) / max_dim
            shape = (int(s.height / sc), int(s.width / sc))
        else:
            sc, shape = 1.0, (s.height, s.width)
        if s.count >= 3:
            a = np.moveaxis(s.read([1, 2, 3], out_shape=(3,) + shape), 0, -1)
        else:
            g = s.read(1, out_shape=shape)
            a = np.stack([g, g, g], -1)
        return np.ascontiguousarray(a), sc, s.transform, s.crs


def cmd_mark(a):
    img, sc, T, crs = read_rgb(a.raster, a.max_dim)
    pts = json.load(open(a.points))
    inv = ~T
    for p in pts:
        x, y = rio_transform("EPSG:4326", crs, [p["lon"]], [p["lat"]])
        col, row = inv * (x[0], y[0])
        c, r = int(col / sc), int(row / sc)
        cv2.drawMarker(img, (c, r), (255, 0, 0), cv2.MARKER_CROSS, 28, 2)
        cv2.putText(img, p["id"], (c + 8, r - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    cv2.imwrite(a.out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("wrote", a.out)


def cmd_crop(a):
    with rasterio.open(a.raster) as s:
        hw = a.hw
        cx, cy = a.cx, a.cy
        win = ((max(0, cy - hw), min(s.height, cy + hw)), (max(0, cx - hw), min(s.width, cx + hw)))
        g = s.read(1, window=win)
    img = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    y0, x0 = win[0][0], win[1][0]
    step = 100
    for gx in range((x0 // step) * step + step, win[1][1], step):
        cv2.line(img, (gx - x0, 0), (gx - x0, img.shape[0]), (0, 220, 255), 1)
        cv2.putText(img, str(gx), (gx - x0 + 2, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)
    for gy in range((y0 // step) * step + step, win[0][1], step):
        cv2.line(img, (0, gy - y0), (img.shape[1], gy - y0), (0, 220, 255), 1)
        cv2.putText(img, str(gy), (2, gy - y0 + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)
    cv2.drawMarker(img, (cx - x0, cy - y0), (0, 0, 255), cv2.MARKER_CROSS, 40, 1)
    if a.scale != 1.0:
        img = cv2.resize(img, None, fx=a.scale, fy=a.scale, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(a.out, img, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print("wrote", a.out, img.shape)


def cmd_warp(a):
    gcps_in = json.load(open(a.gcps))
    gcps = []
    for p in gcps_in:
        x, y = rio_transform("EPSG:4326", "EPSG:3857", [p["lon"]], [p["lat"]])
        gcps.append(GroundControlPoint(row=p["py"], col=p["px"], x=x[0], y=y[0]))
    # report affine fit residuals
    A = np.array([[p["px"], p["py"], 1] for p in gcps_in])
    X = np.array([[g.x, g.y] for g in gcps])
    coef, res, *_ = np.linalg.lstsq(A, X, rcond=None)
    pred = A @ coef
    r = np.linalg.norm(pred - X, axis=1)
    lat0 = float(np.mean([p["lat"] for p in gcps_in]))
    scale = np.cos(np.radians(lat0))  # mercator -> ground meters
    print("affine residuals (ground m):", " ".join(f"{v*scale:.1f}" for v in r))
    print(f"RMS {np.sqrt((r**2).mean())*scale:.1f} m")

    b = transform_bounds("EPSG:4326", "EPSG:3857", *AOI84)
    RES = a.res
    W, H = int((b[2] - b[0]) / RES), int((b[3] - b[1]) / RES)
    T = Affine(RES, 0, b[0], 0, -RES, b[3])
    with rasterio.open(a.scan) as s:
        data = s.read(1)
    out = np.zeros((H, W), np.uint8)
    reproject(source=data, destination=out, src_crs="EPSG:3857", gcps=gcps,
              dst_crs="EPSG:3857", dst_transform=T, resampling=Resampling.bilinear,
              warp_extras={"POLYNOMIAL_ORDER": str(a.order)})
    prof = dict(driver="GTiff", height=H, width=W, count=1, dtype="uint8", crs="EPSG:3857",
                transform=T, compress="deflate", tiled=True)
    with rasterio.open(a.out, "w", **prof) as d:
        d.write(out, 1)
    print("wrote", a.out)


def cmd_qa(a):
    """checkerboard of two rasters already on the AOI grid"""
    A_, _, _, _ = read_rgb(a.raster_a)
    B_, _, _, _ = read_rgb(a.raster_b)
    ga = cv2.cvtColor(A_, cv2.COLOR_RGB2GRAY); gb = cv2.cvtColor(B_, cv2.COLOR_RGB2GRAY)
    if gb.shape != ga.shape:
        gb = cv2.resize(gb, (ga.shape[1], ga.shape[0]))
    h, w = ga.shape
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((yy // a.square + xx // a.square) % 2).astype(bool)
    cb = np.where(m, ga, gb)
    k = max(1, int(max(h, w) / a.max_dim))
    cv2.imwrite(a.out, cb[::k, ::k], [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("wrote", a.out)


p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
m = sub.add_parser("mark"); m.add_argument("raster"); m.add_argument("out")
m.add_argument("--points", required=True); m.add_argument("--max-dim", type=int, default=1600)
c = sub.add_parser("crop"); c.add_argument("raster"); c.add_argument("out")
c.add_argument("--cx", type=int, required=True); c.add_argument("--cy", type=int, required=True)
c.add_argument("--hw", type=int, default=300); c.add_argument("--scale", type=float, default=1.0)
w = sub.add_parser("warp"); w.add_argument("scan"); w.add_argument("gcps"); w.add_argument("out")
w.add_argument("--order", type=int, default=1); w.add_argument("--res", type=float, default=1.0)
q = sub.add_parser("qa"); q.add_argument("raster_a"); q.add_argument("raster_b"); q.add_argument("out")
q.add_argument("--square", type=int, default=400); q.add_argument("--max-dim", type=int, default=1500)
a = p.parse_args()
{"mark": cmd_mark, "crop": cmd_crop, "warp": cmd_warp, "qa": cmd_qa}[a.cmd](a)
