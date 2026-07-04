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

| Era layer | Source frames | GCPs | RMS (m) | Notes |
|---|---|---|---|---|
| 2022 (NAIP) | 2 COG quarter-quads | — | native | USDA orthoimagery, used as base truth |
| 1981 frame 18-40 | TG-3800 | 32 | 3.6 | matched vs NAIP |
| 1981 frame 18-39 | TG-3800 | 33 | 3.2 | SIFT-seeded from 18-40, matched vs NAIP |
| 1971 | TG-2755 ×4 | (pending) | | |
| 1956 | C-22555 ×5 | (pending) | | |
| 1938 | AXJ-1938 ×6 | (pending) | | |
| 1928 | C-300 ×7 | (pending) | | |
| 1900 topo | USGS Pasadena 15' 1900 ed. | — | map-inherent | HTMC georeferencing used as-is; expect tens of meters (1890s survey); acceptable for a map-styled era |

## Known limitations

- **Relief displacement**: scans are not orthorectified; hillside features shift by up to
  a few tens of meters depending on elevation and position in frame. Street-grid (valley)
  alignment is what the residuals measure and what the crossfade needs. Canyon-floor
  features (the freeway cut) can show local offsets against the modern layer.
- **Film-collar masking**: fixed fractional margins per flight blank the instrument strip
  and frame edges before warping (see build_era.py --margin).
- Frame date stamps override the UCSB index where they disagree (TG-3800: stamped
  4/28/81 vs indexed 1979-07).
