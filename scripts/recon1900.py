#!/usr/bin/env python3
"""Reconstruct a plausible ~1900 color aerial view (v3).

Keep the real 1928 terrain intact; erase only the man-made features.
Development in the 1928 imagery = narrow bright features (dirt/paved roads,
building roofs) against darker land. Wide bright features (the natural wash,
rock faces) are protected by a morphological width test. The masked pixels
are inpainted from their surroundings, then re-textured with matched
high-frequency detail so filled areas don't look airbrushed.
"""
import numpy as np, cv2, rasterio

SRC = "data/processed/v2/era1928_color.tif"
OUT = "data/processed/v2/era1900_color.tif"
PREVIEW = "data/processed/qa/recon1900_preview.jpg"
MASKPRE = "data/processed/qa/recon1900_mask.jpg"
rng = np.random.default_rng(1900)

with rasterio.open(SRC) as s:
    img = np.moveaxis(s.read([1, 2, 3]), 0, -1).copy()
    prof = s.profile.copy()
H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
valid = gray > 0

# --- bright-above-local-baseline
base = cv2.medianBlur(gray, 51)
bright = ((gray.astype(np.int16) - base.astype(np.int16)) > 20) & valid

# --- narrow test: remove wide bright regions (wash, rock, sunlit slopes),
# including their rims, from the mask
bright_u8 = bright.astype(np.uint8)
wide = cv2.morphologyEx(bright_u8, cv2.MORPH_OPEN,
                        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (37, 37)))
wide = cv2.dilate(wide, np.ones((21, 21), np.uint8))
narrow = bright_u8 & ~wide
mask = cv2.dilate(narrow, np.ones((5, 5), np.uint8)).astype(bool) & valid

# --- dense urban cores: where narrow-bright density is very high, take whole area
dens = cv2.boxFilter(narrow.astype(np.float32), -1, (121, 121))
core = dens > 0.20
core = cv2.dilate(core.astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool)
mask |= core & valid
print(f"inpaint mask: {mask.mean():.1%} of image (core {core.mean():.1%})")

sc = 1300 / max(H, W)
cv2.imwrite(MASKPRE, cv2.addWeighted(
    cv2.resize(gray, None, fx=sc, fy=sc), 0.6,
    cv2.resize((mask * 255).astype(np.uint8), None, fx=sc, fy=sc), 0.4, 0),
    [cv2.IMWRITE_JPEG_QUALITY, 80])

# --- inpaint at half resolution for speed, then restore
small = cv2.resize(img, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
msmall = cv2.resize(mask.astype(np.uint8), (W // 2, H // 2),
                    interpolation=cv2.INTER_NEAREST)
print("inpainting...")
inp = cv2.inpaint(small, msmall, 5, cv2.INPAINT_TELEA)
inp_full = cv2.resize(inp, (W, H), interpolation=cv2.INTER_LINEAR)

out = img.copy()
mm = mask
out[mm] = inp_full[mm]

# --- re-texture inpainted areas with high-frequency detail from natural land
nat = (~mask) & valid & (np.abs(gray.astype(np.int16) - base.astype(np.int16)) < 12)
g32 = cv2.cvtColor(out, cv2.COLOR_RGB2GRAY).astype(np.float32)
hp_src = gray.astype(np.float32) - cv2.GaussianBlur(gray.astype(np.float32), (0, 0), 4)
# sample hp texture from a big natural area and tile-randomize it
ys, xs = np.nonzero(cv2.erode(nat.astype(np.uint8), np.ones((130, 130), np.uint8)))
sel = (ys >= 128) & (ys < H - 128) & (xs >= 128) & (xs < W - 128)
ys, xs = ys[sel], xs[sel]
tex = np.zeros((H, W), np.float32)
if len(ys) > 50:
    T = 128
    for gy in range(0, H - T, T):
        for gx in range(0, W - T, T):
            k = rng.integers(0, len(ys))
            sy, sx = int(ys[k]) - T // 2, int(xs[k]) - T // 2
            tex[gy:gy + T, gx:gx + T] = hp_src[sy:sy + T, sx:sx + T]
    tex = cv2.GaussianBlur(tex, (0, 0), 0.6)
add = (tex * 0.7)[..., None]
outf = out.astype(np.float32)
outf[mm] = np.clip(outf[mm] + add[mm], 0, 255)
out = outf.astype(np.uint8)
out[~valid] = 0

with rasterio.open(OUT, "w", **prof) as d:
    d.write(np.moveaxis(out, -1, 0))
print("wrote", OUT)
cv2.imwrite(PREVIEW, cv2.cvtColor(cv2.resize(out, None, fx=sc, fy=sc), cv2.COLOR_RGB2BGR),
            [cv2.IMWRITE_JPEG_QUALITY, 85])
print("wrote", PREVIEW)
