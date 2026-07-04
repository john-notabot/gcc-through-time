#!/usr/bin/env python3
"""Automatic GCP refinement by local template matching.

Pipeline: coarse-rectify the raw scan onto the reference grid using a seed
affine (from a few manual GCPs) -> gradient-magnitude template matching in a
local window around each OSM intersection -> RANSAC consistency filter ->
back-transform matched points to raw-scan pixel coords -> GCP json.

Usage: autogcp.py <scan> <reference> <seed_gcps.json> <out_gcps.json>
"""
import json, argparse
import numpy as np, cv2, rasterio
from rasterio.warp import transform as tr

ap = argparse.ArgumentParser()
ap.add_argument("scan"); ap.add_argument("reference")
ap.add_argument("seed"); ap.add_argument("out")
ap.add_argument("--intersections", default="research/gcp_intersections.json")
ap.add_argument("--patch", type=int, default=64)    # half-size on common grid (px = RES m)
ap.add_argument("--search", type=int, default=70)   # search halo (px)
ap.add_argument("--score", type=float, default=0.30)
ap.add_argument("--max-pts", type=int, default=45)
ap.add_argument("--grid-cell", type=int, default=350)
ap.add_argument("--report", default=None)
a = ap.parse_args()
RES = 1.0  # common grid resolution, m/px (EPSG:3857)

def grad(img):
    img = cv2.createCLAHE(3.0, (12, 12)).apply(img)
    gx = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=3)
    return cv2.GaussianBlur(cv2.magnitude(gx, gy), (0, 0), 1.2)

# --- seed affine: scan px -> 3857
seed = json.load(open(a.seed))
A = np.array([[g["px"], g["py"], 1] for g in seed])
xs, ys = tr("EPSG:4326", "EPSG:3857", [g["lon"] for g in seed], [g["lat"] for g in seed])
coef, *_ = np.linalg.lstsq(A, np.column_stack([xs, ys]), rcond=None)

with rasterio.open(a.scan) as s:
    scan = s.read(1)
sh, sw = scan.shape

# --- coarse-rectify scan to 3857 grid covering the scan footprint
corners = np.array([[0, 0, 1], [sw, 0, 1], [sw, sh, 1], [0, sh, 1]]) @ coef
x0, y0 = corners[:, 0].min(), corners[:, 1].min()
x1, y1 = corners[:, 0].max(), corners[:, 1].max()
W, H = int((x1 - x0) / RES), int((y1 - y0) / RES)
# scan px -> rect px:  M23 (2x3, cv2 convention)
# rect px = ((coef^T . [px,py,1]) - [x0,y1_flip]) / RES  with y flipped
M = np.array([
    [coef[0, 0] / RES, coef[1, 0] / RES, (coef[2, 0] - x0) / RES],
    [-coef[0, 1] / RES, -coef[1, 1] / RES, (y1 - coef[2, 1]) / RES],
])
rect = cv2.warpAffine(scan, M, (W, H), flags=cv2.INTER_LINEAR)
Minv = cv2.invertAffineTransform(M)

def rect_px_of_3857(x, y):
    return (x - x0) / RES, (y1 - y) / RES

# --- reference rendered on same grid
with rasterio.open(a.reference) as r:
    ref = r.read(1) if r.count == 1 else cv2.cvtColor(
        np.moveaxis(r.read([1, 2, 3]), 0, -1), cv2.COLOR_RGB2GRAY)
    inv_ref = ~r.transform
    # sample reference onto rect grid (nearest is fine for gradients after blur)
    ref_full = ref

def ref_patch(x, y, P):
    """reference gradient patch centered at 3857 (x,y), resampled to RES"""
    # reference native res
    rc = inv_ref * (x, y)
    step = RES / abs(r_T.a)
    half = int(P * step)
    cx, cy = int(rc[0]), int(rc[1])
    p = refg_full[cy - half:cy + half, cx - half:cx + half]
    if p.shape != (2 * half, 2 * half) or half == 0:
        return None
    raw = ref_full[cy - half:cy + half, cx - half:cx + half]
    if (raw > 0).mean() < 0.85:   # reference has nodata here
        return None
    return cv2.resize(p, (2 * P, 2 * P))

with rasterio.open(a.reference) as rr:
    r_T = rr.transform
refg_full = grad(ref_full)
rectg = grad(rect)

cands = json.load(open(a.intersections))
picked, cells = [], set()
for c in cands:
    x, y = tr("EPSG:4326", "EPSG:3857", [c["lon"]], [c["lat"]])
    rx, ry = rect_px_of_3857(x[0], y[0])
    # ensure inside rectified content (not just bbox)
    if not (150 < rx < W - 150 and 150 < ry < H - 150):
        continue
    if rect[int(ry), int(rx)] == 0:
        continue
    cell = (int(rx // a.grid_cell), int(ry // a.grid_cell))
    if cell in cells:
        continue
    cells.add(cell)
    picked.append((c, (rx, ry), (x[0], y[0])))

P, S = a.patch, a.search
results = []
for c, (rx, ry), (x, y) in picked:
    rp = ref_patch(x, y, P)
    if rp is None:
        continue
    W2 = P + S
    cx, cy = int(rx), int(ry)
    sp = rectg[cy - W2:cy + W2, cx - W2:cx + W2]
    if sp.shape != (2 * W2, 2 * W2):
        continue
    res = cv2.matchTemplate(sp, rp, cv2.TM_CCOEFF_NORMED)
    _, mx, _, ml = cv2.minMaxLoc(res)
    if mx < a.score:
        continue
    mrx, mry = cx - W2 + ml[0] + P, cy - W2 + ml[1] + P
    # back to raw scan pixels
    px, py = Minv @ np.array([mrx, mry, 1.0])
    results.append({"id": c["streets"][:40], "px": float(px), "py": float(py),
                    "lon": c["lon"], "lat": c["lat"], "score": round(float(mx), 3)})

print(f"{len(picked)} candidates, {len(results)} matched (score>={a.score})")
if len(results) < 6:
    raise SystemExit("too few matches — lower --score or fix seed")

src = np.float32([[t["px"], t["py"]] for t in results])
xs, ys = tr("EPSG:4326", "EPSG:3857", [t["lon"] for t in results], [t["lat"] for t in results])
dst = np.float32(np.column_stack([xs, ys]))
M2, mask = cv2.estimateAffine2D(src, dst - dst.mean(axis=0), ransacReprojThreshold=10.0, maxIters=8000)
inl = mask.ravel().astype(bool)
kept = sorted((t for t, k in zip(results, inl) if k), key=lambda t: -t["score"])[:a.max_pts]
print(f"{len(kept)} after RANSAC")

srcm = np.array([[t["px"], t["py"], 1] for t in kept])
xs, ys = tr("EPSG:4326", "EPSG:3857", [t["lon"] for t in kept], [t["lat"] for t in kept])
X = np.column_stack([xs, ys])
coef2, *_ = np.linalg.lstsq(srcm, X, rcond=None)
R = np.linalg.norm(srcm @ coef2 - X, axis=1) * np.cos(np.radians(34.17))
print(f"kept-GCP affine residuals (m): median {np.median(R):.1f}, p90 {np.percentile(R,90):.1f}, max {R.max():.1f}")
json.dump(kept, open(a.out, "w"), indent=1)
print("wrote", a.out)
if a.report:
    lines = [f"{t['id']:42s} score {t['score']:.2f} res {rr:5.1f} m" for t, rr in zip(kept, R)]
    open(a.report, "w").write("\n".join(lines) + "\n")
