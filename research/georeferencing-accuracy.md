# Georeferencing Accuracy Log — Phase 2

Method (all aerial eras): a few manual seed correspondences → coarse rectification →
gradient-magnitude template matching around OSM street intersections (modern coordinates
as ground truth) → RANSAC consistency filter → order-2 polynomial warp to EPSG:3857,
1 m/px, AOI grid (-118.245..-118.210, 34.150..34.195). Residuals below are against the
kept GCPs' best-fit affine; independent QA by visual checkerboard against the reference.

Chaining: each era template-matches its appearance against the *next-later* era's
registered raster, but GCP coordinates always come from present-day OSM — so chain
errors do not accumulate geometrically, they only inherit the reference's local error
at patch centers (~its own RMS).

| Era layer | Source frames | GCPs | RMS (m) | AOI coverage | Notes |
|---|---|---|---|---|---|
| 2022 (NAIP) | 2 COG quarter-quads | — | native | 100% | USDA orthoimagery, base truth |
| 1981 | TG-3800 18-39, 18-40 | 33+32 | 3.2–3.6 | 84.7% | matched vs NAIP; missing NE mountain corner |
| 1971 composite | TG-2755 25-37/38/39 + TG-2400 1-88 fill | 13+11+46+35 | 2.7–3.7 | 98.9% | flight row 26 never scanned → campus strip filled with tone-matched 3/19/68 frame; labeled 1968–71 composite (John approved 2026-07-03). NW frame 27-48 unseedable, covered by fill |
| 1968 (fill layer) | TG-2400 1-88 | 35 | 3.3 | 91.8% | single wide frame |
| 1960 (extra, unused era) | C-23870 1195 | 45 | 3.4 | 65.5% | registered while investigating freeway history; available for story pins |
| 1956 | C-22555 ×5 | 14–36 | 2.9–4.4 | 88.9% | |
| 1938 | AXJ-1938 ×6 | 11–34 | 2.2–4.0 | 100% | |
| 1928 | C-300 ×7 | 13–31 | 2.1–4.5 | 87.1% | missing NE mountains |
| 1900 topo | USGS Pasadena 15' 1900 | — | map-inherent | 100% | HTMC georeferencing as-is |

(previous provisional table replaced with final numbers 2026-07-03; per-frame GCP lists in research/gcps/)

## Known limitations

- **Relief displacement**: scans are not orthorectified; hillside features shift by up to
  a few tens of meters depending on elevation and position in frame. Street-grid (valley)
  alignment is what the residuals measure and what the crossfade needs. Canyon-floor
  features (the freeway cut) can show local offsets against the modern layer.
- **Film-collar masking**: fixed fractional margins per flight blank the instrument strip
  and frame edges before warping (see build_era.py --margin).
- Frame date stamps override the UCSB index where they disagree (TG-3800: stamped
  4/28/81 vs indexed 1979-07).

## Color reconstruction layer set (added 2026-07-04)

Second tile set `site/tiles/color/` (default view; toggle for originals):
- All frames re-warped at 0.6 m/px from the saved GCPs (recovers native scan detail)
- Every era gap-filled to 100% AOI coverage from temporal neighbours
  (1928←1938, 1938←1928/1956, 1956←1968, 1971←1968/1981, 1981←1971/2022),
  luminance histogram-matched per fill
- Colorized by transferring low-passed Lab chrominance from the aligned NAIP 2022
  image; where historical/modern structure disagrees, chroma falls back to a neutral
  terrain palette. Luminance histogram-matched to NAIP for era-to-era tonal consistency
- ~1900 color layer is SYNTHETIC: colorized 1928 photography with development removed
  (narrow-bright-feature inpainting + donor-texture synthesis in the flats). Labeled
  as an AI-assisted reconstruction in the site UI. Known artifacts: faint grid ghosts,
  patch seams in the flats, mushy far-SE corner. Iterate later.
