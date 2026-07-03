# UCSB Library Aerial Photography Collection (FrameFinder) — Research Findings

Researched 2026-07-03. AOI: lat 34.150–34.195, lon -118.245 to -118.210 (GCC campus, Verdugo foothills, SR-2 corridor).

## Bottom line

**76 scanned frames across 20 flights, 1927–2008, all directly downloadable — no login, no fee.**
This is the imagery backbone of the project. Strongest decades: 1930s–1960s.

## Access infrastructure

- FrameFinder app: https://mil.library.ucsb.edu/ap_indexes/FrameFinder/
- Public, unauthenticated ArcGIS FeatureServer behind it (query by bbox):
  `https://services1.arcgis.com/4TXrdeWh0RyCqPgB/arcgis/rest/services/All_Flights_Merge/FeatureServer/0/query`
  (params: `geometry=<xmin,ymin,xmax,ymax>&geometryType=esriGeometryEnvelope&inSR=4326&outFields=*&outSR=4326&f=json`)
- Direct TIFF URL pattern:
  `https://mil.library.ucsb.edu/ap_images/<flight-lowercase-hyphenated>/<flight>_<frame-lowercase>.tif`
  e.g. `https://mil.library.ucsb.edu/ap_images/c-113/c-113_297.tif`
- Full 76-frame API response with centerpoints: `research/sources/ucsb_aoi_frames.json`

## Flights covering the AOI (all verified via API)

| Date | Flight ID | Scale 1: | Frames in AOI |
|---|---|---|---|
| 1927-08 | C-113 (Fairchild) | 18,000 | 297 (marginal campus coverage — see caveat) |
| 1928-01 | C-300 (Fairchild) | 18,000 | K-177…K-181, K-224, K-225 (7) |
| 1936-06-10 | C-4051 (Fairchild) | **7,200** | 5–10, Z-1, Z-2 (8) — largest scale in the set |
| 1938-01 | AXJ-1938 (USDA) | 20,000 | 24-59, 44-6, 44-7, 72-41…72-43 (6) |
| 1944-11-23 | DDF-1944 | 10,000 | 7-86…7-89, 7-131…7-134, 8-52…8-54 (11) |
| 1952-11-04 | AXJ-1952 (USDA) | 20,000 | 7K-30, 7K-31, 7K-94…7K-96 (5) |
| 1954-10 | C-20941 | 24,000 | 2-23 (1) |
| 1956-07 | C-22555 | 14,400 | 8-31, 8-32, 9-30…9-32 (5) |
| 1960-05 | C-23870 | 14,400 | 1165, 1166, 1194, 1195, 1494…1496 (7) |
| 1962-01-30 | PAI-LA-BASIN-62 | 18,000 | 174V-168, 174V-169 (2) |
| 1962-10 | C-24400 | 12,000 | 4-333, 5-319 (2) |
| 1965-11-28 | C-25019 | 24,000 | 78, 275, 276, 277 (4) |
| 1968-03 | TG-2400 (Teledyne) | 28,800 | 1-87, 1-88 (2) |
| 1971-03 | TG-2755 (Teledyne) | 10,440 | 25-37…25-39, 27-48 (4) |
| 1976-02 | TG-7600 (Teledyne) | 24,000 | 13-24, 13-25, 14A-18 (3) |
| 1979-07 | TG-3800 (Teledyne) | 24,000 | 18-39, 18-40 (2) |
| 1989-03-31 | WAC-89CA | 31,680 | 2-129, 2-130 (2) |
| 1994-06-01 | NAPP-2C (USGS) | 40,000 | 6858-60, 6858-61 (2) |
| 2002-06-07 | NAPP-3C (USGS) | 40,000 | 12461-107 (1) |
| 2008-02-29 | EAG-18 | 28,000 | 1635 (1) |

Dates landing on the 2nd of a month likely mean month/year precision only (placeholder day — inferred).

## Frames best centered on campus (34.167, -118.230)

- 1928: **C-300 K-180** (center 34.1682, -118.2306 — essentially on campus)
- 1936: **C-4051 frame 8** (34.1669, -118.2300 — on campus, 1:7,200)
- 1944: DDF-1944 7-132 / 8-53 · 1952: AXJ-1952 7K-95 · 1956: C-22555 9-31
- 1960: C-23870 1195 · 1962: C-24400 5-319 · 1965: C-25019 276
- 1971: TG-2755 25-38 · 1979: TG-3800 18-40 · 2008: EAG-18 1635

## Caveats

- **C-113 (Aug 1927)**: only frame 297 touches the AOI (center 34.1506, -118.2371); the future
  campus site sits at/just beyond its north edge. Verified by download + visual inspection.
  For true 1920s campus-site coverage use **C-300 K-180 (Jan 1928)**.
- FeatureServer appears to list only scanned holdings; unscanned physical-only flights for
  Glendale were not enumerated.

## File specs (verified by sample download)

- Grayscale 8-bit TIFF, 600 dpi scans; historic frames ~22–31 MB each
  (c-113_297: 5382×4188 px, 22.6 MB). Recent color EAG-18 1635: 228 MB.

## Rights

- UCSB: "UCSB does not hold copyright over materials in the geospatial collection (with very
  few exceptions)." Free download, no fees. Republication permission responsibility rests with user.
- Practical read (not legal advice): pre-1930 Fairchild (C-113, C-300) almost certainly public
  domain; USDA (AXJ) and USGS NAPP flights are federal works, public domain. Teledyne/PAI/WAC/EAG
  status murkier but served without restriction notices.
- **Required credit line**: `[Flight, frame, date. Courtesy of UCSB Library Geospatial Collection.]`

Sources: FrameFinder, UCSB geospatial policy pages, Fairchild Aerial Surveys collection page,
direct FeatureServer queries and sample TIFF downloads.
