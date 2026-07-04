#!/usr/bin/env python3
"""Register all frames of an era against a reference raster and mosaic them.

Per frame: SIFT seed (scan vs reference) -> autogcp round 1 (loose) ->
round 2 (tight) -> order-2 warp to the AOI grid. Then mosaic + QA checkerboard.

Usage: build_era.py --era era1971 --frames tg-2755_25-37,tg-2755_25-38 \
         --reference data/processed/era1981_3857.tif [--seed-file frame=gcps.json]
"""
import argparse, json, subprocess, sys, os
import numpy as np, cv2, rasterio
from rasterio.warp import transform as tr
from rasterio.merge import merge

PY = ".venv/bin/python"
AOI84 = (-118.245, 34.150, -118.210, 34.195)

ap = argparse.ArgumentParser()
ap.add_argument("--era", required=True)
ap.add_argument("--frames", required=True)
ap.add_argument("--reference", required=True)
ap.add_argument("--seed-file", action="append", default=[],
                help="frame=path.json for frames where SIFT seeding fails")
ap.add_argument("--autogcp-reference", default=None,
                help="reference for template matching (default: --reference)")
ap.add_argument("--sift-dim", type=int, default=3000)
ap.add_argument("--min-inliers", type=int, default=10)
ap.add_argument("--margin", default="0.085,0.035,0.03,0.035",
                help="film-collar blanking passed to warp (top,right,bottom,left)")
ap.add_argument("--skip-frames-done", action="store_true")
a = ap.parse_args()
frames = a.frames.split(",")
seed_files = dict(s.split("=", 1) for s in a.seed_file)
os.makedirs("data/processed/frames", exist_ok=True)
os.makedirs("data/processed/qa", exist_ok=True)
os.makedirs("research/gcps", exist_ok=True)


def sift_seed(scan_path, ref_path, out_json):
    def prep(img):
        return cv2.createCLAHE(3.0, (16, 16)).apply(img)
    with rasterio.open(scan_path) as s:
        sc = max(s.width, s.height) / a.sift_dim
        tgt = s.read(1, out_shape=(int(s.height / sc), int(s.width / sc)))
    tgt = prep(tgt)
    m = int(0.08 * min(tgt.shape))
    tgt[:m] = 0; tgt[-m:] = 0; tgt[:, :m] = 0; tgt[:, -m:] = 0
    with rasterio.open(ref_path) as r:
        rsc = max(r.width, r.height) / a.sift_dim
        if r.count >= 3:
            arr = np.moveaxis(r.read([1, 2, 3], out_shape=(3, int(r.height / rsc), int(r.width / rsc))), 0, -1)
            ref = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        else:
            ref = r.read(1, out_shape=(int(r.height / rsc), int(r.width / rsc)))
        ref_T = r.transform
    ref = prep(ref)
    sift = cv2.SIFT_create(nfeatures=16000)
    kt, dt = sift.detectAndCompute(tgt, None)
    kr, dr = sift.detectAndCompute(ref, None)
    if dt is None or dr is None:
        return 0
    fl = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 64})
    good = [m_ for m_, n in fl.knnMatch(dt, dr, k=2) if m_.distance < 0.78 * n.distance]
    if len(good) < a.min_inliers:
        return len(good)
    src = np.float32([kt[m_.queryIdx].pt for m_ in good])
    dst = np.float32([kr[m_.trainIdx].pt for m_ in good])
    M, mask = cv2.estimateAffinePartial2D(src, dst, ransacReprojThreshold=5.0, maxIters=8000)
    if M is None:
        return 0
    inl = mask.ravel().astype(bool)
    n = int(inl.sum())
    if n < a.min_inliers:
        return n
    pts = []
    for s_pt, d_pt in zip(src[inl], dst[inl]):
        px, py = float(s_pt[0] * sc), float(s_pt[1] * sc)
        rx, ry = ref_T * (float(d_pt[0] * rsc), float(d_pt[1] * rsc))
        lon, lat = tr("EPSG:3857", "EPSG:4326", [rx], [ry])
        pts.append({"px": px, "py": py, "lon": lon[0], "lat": lat[0], "id": "sift"})
    json.dump(pts, open(out_json, "w"))
    return n


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = (r.stdout + r.stderr)
    keep = [l for l in out.splitlines() if any(k in l for k in
            ("candidates", "after RANSAC", "residuals", "wrote", "RMS", "too few"))]
    print("   " + "\n   ".join(keep))
    return r.returncode == 0 and "too few" not in out


ok_frames = []
for f in frames:
    scan = f"data/raw/ucsb/{f}.tif"
    out_tif = f"data/processed/frames/{f}_3857.tif"
    if a.skip_frames_done and os.path.exists(out_tif):
        print(f"== {f}: already done"); ok_frames.append(out_tif); continue
    print(f"== {f}")
    seed = f"research/gcps/{f}_seed.json"
    if f in seed_files:
        seed = seed_files[f]
        print(f"   using provided seed {seed}")
    else:
        n = sift_seed(scan, a.reference, seed)
        print(f"   sift seed inliers: {n}")
        if n < a.min_inliers:
            print(f"   !! seeding failed for {f} — provide --seed-file {f}=path.json")
            continue
    g1 = f"research/gcps/{f}_r1.json"
    g2 = f"research/gcps/{f}_auto.json"
    agref = a.autogcp_reference or a.reference
    if not run([PY, "scripts/autogcp.py", scan, agref, seed, g1,
                "--score", "0.15", "--patch", "80", "--search", "100"]):
        print(f"   !! round1 failed for {f}"); continue
    if not run([PY, "scripts/autogcp.py", scan, agref, g1, g2,
                "--score", "0.18", "--patch", "80", "--search", "45",
                "--report", f"research/gcps/{f}_report.txt"]):
        print(f"   !! round2 failed for {f}"); continue
    if not run([PY, "scripts/gcp_tools.py", "warp", scan, g2, out_tif,
                "--order", "2", "--res", "1.0", "--margin", a.margin]):
        print(f"   !! warp failed for {f}"); continue
    ok_frames.append(out_tif)

if not ok_frames:
    sys.exit("no frames registered")

print(f"== mosaic {a.era}: {len(ok_frames)} frames")
srcs = [rasterio.open(p) for p in ok_frames]
mosaic, T = merge(srcs, nodata=0)
prof = srcs[0].profile.copy()
prof.update(height=mosaic.shape[1], width=mosaic.shape[2], transform=T)
era_tif = f"data/processed/{a.era}_3857.tif"
with rasterio.open(era_tif, "w", **prof) as d:
    d.write(mosaic)
for s in srcs: s.close()
cov = float((mosaic[0] > 0).mean())
print(f"wrote {era_tif}  coverage {cov:.1%} of AOI")
run([PY, "scripts/gcp_tools.py", "qa", era_tif, a.reference,
     f"data/processed/qa/{a.era}_qa.jpg", "--square", "300", "--max-dim", "1400"])
