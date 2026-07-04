#!/usr/bin/env python3
"""Register an unreferenced aerial scan to a georeferenced reference raster.

Approach: SIFT keypoints + FLANN matching + RANSAC homography between a
downsampled reference (rendered from the georeferenced GeoTIFF) and the raw
scan. Inlier matches become GCPs; the scan is warped to EPSG:3857 with a
thin-plate-spline-like polynomial fit. Outputs a georeferenced GeoTIFF, a QA
blend image, and residual statistics.

Usage: register.py <target_scan.tif> <reference_geotiff> <out.tif> [--order 2] [--max-dim 3200]
"""
import sys, json, argparse
import numpy as np
import cv2
import rasterio
from rasterio.transform import Affine, from_gcps
from rasterio.control import GroundControlPoint
from rasterio.warp import reproject, Resampling, transform_bounds

AOI84 = (-118.245, 34.150, -118.210, 34.195)


def read_gray_downsampled(path, max_dim):
    with rasterio.open(path) as s:
        scale = max(s.width, s.height) / max_dim
        out_w, out_h = int(s.width / scale), int(s.height / scale)
        if s.count >= 3:
            arr = s.read([1, 2, 3], out_shape=(3, out_h, out_w))
            g = cv2.cvtColor(np.moveaxis(arr, 0, -1), cv2.COLOR_RGB2GRAY)
        else:
            g = s.read(1, out_shape=(out_h, out_w))
        return g, scale, s.transform, s.crs


def mask_margin(img, frac):
    """Zero out the outer border so film collar, fiducials and date stamps
    produce no keypoints."""
    h, w = img.shape
    out = img.copy()
    my, mx = int(h * frac), int(w * frac)
    out[:my], out[-my:], out[:, :mx], out[:, -mx:] = 0, 0, 0, 0
    return out


def match(ref_g, tgt_g):
    sift = cv2.SIFT_create(nfeatures=20000)
    kr, dr = sift.detectAndCompute(ref_g, None)
    kt, dt = sift.detectAndCompute(tgt_g, None)
    flann = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 64})
    raw = flann.knnMatch(dt, dr, k=2)
    good = [m for m, n in raw if m.distance < 0.75 * n.distance]
    if len(good) < 12:
        raise RuntimeError(f"only {len(good)} ratio-test matches")
    src = np.float32([kt[m.queryIdx].pt for m in good])   # target px (downsampled)
    dst = np.float32([kr[m.trainIdx].pt for m in good])   # reference px (downsampled)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
    inl = mask.ravel().astype(bool)
    return src[inl], dst[inl], len(good)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target"); ap.add_argument("reference"); ap.add_argument("out")
    ap.add_argument("--order", type=int, default=2)
    ap.add_argument("--max-dim", type=int, default=3200)
    ap.add_argument("--qa", default=None)
    ap.add_argument("--margin", type=float, default=0.08,
                    help="fraction of target border to mask (film collar)")
    a = ap.parse_args()

    ref_g, ref_scale, ref_T, ref_crs = read_gray_downsampled(a.reference, a.max_dim)
    tgt_g, tgt_scale, _, _ = read_gray_downsampled(a.target, a.max_dim)
    # normalize contrast for cross-era matching
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(16, 16))
    ref_g, tgt_g = clahe.apply(ref_g), clahe.apply(tgt_g)
    tgt_g = mask_margin(tgt_g, a.margin)

    src, dst, n_good = match(ref_g, tgt_g)
    print(f"matches: {n_good} ratio-test, {len(src)} RANSAC inliers")

    # thin the inliers to a well-spread subset for GCPs
    idx = np.argsort(src[:, 0])
    keep = idx[:: max(1, len(idx) // 120)]
    gcps = []
    for s_pt, d_pt in zip(src[keep], dst[keep]):
        # target full-res pixel
        col, row = float(s_pt[0] * tgt_scale), float(s_pt[1] * tgt_scale)
        # reference full-res pixel -> map coords
        rx, ry = ref_T * (float(d_pt[0] * ref_scale), float(d_pt[1] * ref_scale))
        gcps.append(GroundControlPoint(row=row, col=col, x=rx, y=ry))

    # residuals of a global affine fit (sanity metric, meters)
    A, _ = cv2.estimateAffine2D(src, dst, ransacReprojThreshold=4.0)
    pred = cv2.transform(src[None], A)[0]
    res_px = np.linalg.norm(pred - dst, axis=1)
    px_m = abs(ref_T.a) * ref_scale
    print(f"affine residuals (m): median {np.median(res_px)*px_m:.1f}, "
          f"p90 {np.percentile(res_px, 90)*px_m:.1f}, max {res_px.max()*px_m:.1f}")

    with rasterio.open(a.target) as ts:
        data = ts.read(1) if ts.count == 1 else cv2.cvtColor(
            np.moveaxis(ts.read([1, 2, 3]), 0, -1), cv2.COLOR_RGB2GRAY)

    dst_bounds = transform_bounds("EPSG:4326", "EPSG:3857", *AOI84)
    RES = 1.0
    W = int((dst_bounds[2] - dst_bounds[0]) / RES)
    Hh = int((dst_bounds[3] - dst_bounds[1]) / RES)
    dst_T = Affine(RES, 0, dst_bounds[0], 0, -RES, dst_bounds[3])
    out = np.zeros((Hh, W), np.uint8)
    reproject(
        source=data, destination=out,
        src_crs=ref_crs, gcps=gcps,
        dst_crs="EPSG:3857", dst_transform=dst_T,
        resampling=Resampling.bilinear,
        warp_extras={"POLYNOMIAL_ORDER": str(a.order)} if a.order else {},
    )
    prof = {"driver": "GTiff", "height": Hh, "width": W, "count": 1, "dtype": "uint8",
            "crs": "EPSG:3857", "transform": dst_T, "compress": "deflate", "tiled": True}
    with rasterio.open(a.out, "w", **prof) as d:
        d.write(out, 1)
    print("wrote", a.out)

    if a.qa:
        # 50/50 blend with reference rendered on same grid
        ref_on_grid = np.zeros((Hh, W), np.uint8)
        with rasterio.open(a.reference) as rs:
            rdata = rs.read(1) if rs.count == 1 else cv2.cvtColor(
                np.moveaxis(rs.read([1, 2, 3]), 0, -1), cv2.COLOR_RGB2GRAY)
            reproject(source=rdata, destination=ref_on_grid,
                      src_crs=rs.crs, src_transform=rs.transform,
                      dst_crs="EPSG:3857", dst_transform=dst_T,
                      resampling=Resampling.bilinear)
        blend = cv2.addWeighted(out, 0.5, ref_on_grid, 0.5, 0)
        # checkerboard too (400px squares): more revealing of misalignment
        cb = np.zeros_like(out)
        yy, xx = np.mgrid[0:Hh, 0:W]
        m = ((yy // 400 + xx // 400) % 2).astype(bool)
        cb[m], cb[~m] = out[m], ref_on_grid[~m]
        qa = np.vstack([cv2.resize(blend, (W // 4, Hh // 4)), cv2.resize(cb, (W // 4, Hh // 4))])
        cv2.imwrite(a.qa, qa, [cv2.IMWRITE_JPEG_QUALITY, 82])
        print("wrote", a.qa)


if __name__ == "__main__":
    main()
