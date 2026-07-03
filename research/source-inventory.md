# GCC Through Time — Source Inventory & Proposed Eras (Phase 1 Deliverable)

Compiled 2026-07-03. AOI: lat 34.150–34.195, lon -118.245 to -118.210 — GCC campus
(34.167, -118.230), Verdugo foothills, SR-2 corridor, Verdugo Rd/Cañada Blvd.
Detailed per-source reports in `research/sources/`.

---

## 1. What we found, by source

### UCSB Library Aerial Photography (FrameFinder) — ★ imagery backbone
**76 scanned frames, 20 flights, 1927–2008, all free direct downloads, no login.**
600-dpi grayscale TIFFs, ~22–31 MB/frame. Best decades: 1930s–1960s. On-campus frames
exist for 1928, 1936, 1938, 1944, 1952, 1956, 1960, 1962, 1965, 1971, 1976, 1979, more.
Rights: UCSB claims no copyright; pre-1930 and federal flights effectively public domain;
mid-century commercial flights (Teledyne etc.) served without restriction — credit line
required: "Flight, frame, date. Courtesy of UCSB Library Geospatial Collection."
→ `sources/ucsb-framefinder.md`, frame index in `sources/ucsb_aoi_frames.json`

### USGS Historical Topographic Maps (topoView/HTMC) — ★ pre-aerial era + freeway brackets
48 map records, direct S3 GeoTIFF downloads, no login, **all public domain**.
Key editions: Pasadena 15' **1896 & 1900** (pre-development baseline — the only source
for a ~1900 era); Glendale 1:24,000 imprints 1928/1932/1939/1948; Pasadena 7.5'
1953 (pre-freeway), 1966, PR-1972, PR-1988 (post-freeway), 1995. Historical contours
for the Phase 4 terrain reconstruction come from these.
→ `sources/usgs-topo-earthexplorer.md`

### USGS EarthExplorer — supplement only (login-gated)
NAPP (late-80s/mid-90s/early-00s), NHAP (1980s), 1-m DOQ orthos (~1994). Free with a
free ERS account; unscanned frames cost $30 + 3–4 weeks (skip). UCSB covers most of the
same eras without login, so EarthExplorer is only needed if we adopt a 1990s era stop.
→ step-by-step instructions in `sources/usgs-topo-earthexplorer.md`

### LOC Sanborn maps — context material only
Online editions (1908, 1912, 1919 + Montrose 1924) are public domain BUT coverage ends
~0.5 mi west of Verdugo Rd — **the campus site is on no online sheet**. The 1925/1950
volumes that might reach it are offline (ProQuest via LAPL card = reference only, not
publishable). Role: story-pin/context imagery for early-town eras, not base layers.
→ `sources/sanborn-local-archives.md`

### Glendale Library History Room + GCC Archives — story-pin photos (manual requests)
Calisphere has some usable items now (1932 Crestmont Ct & N Verdugo Rd photo adjacent to
campus; 1912 Verdugo Rd; Verdugo Swim Stadium). Ground-level campus-construction and
SR-2-construction photos need requests: glendalehistoryroom@glendaleca.gov and
library@glendale.edu (GCC archives request form). Flagged as manual to-dos.
→ `sources/sanborn-local-archives.md`

### Modern data — all keyless, all verified live
NAIP 2022 60-cm imagery (public domain, Azure blob COGs); OSM via Overpass (ODbL,
attribution required); USGS 3DEP 1-m lidar DEM 2023 (public domain). Hosting: PMTiles
archives on GitHub Pages, total well under the 1 GB limit.
→ `sources/modern-base-data.md`

---

## 2. Proposed era list (7 stops) — FOR APPROVAL

| # | Era stop | Base layer | Scale/quality | The story it tells |
|---|---|---|---|---|
| 1 | **~1900 — Ranchland** | USGS Pasadena 15' topo, 1896/1900 ed. | 1:62,500 map (not photo) | Dirt roads, no city grid, ungraded Verdugos. Only source this old — shown as a styled historical map, clearly labeled. |
| 2 | **1928 — A young college, a bare hillside** | UCSB C-300 (Jan 1928), frame K-180 + neighbors | 1:18,000 aerial | College founded 1927 in borrowed high-school rooms downtown; the future campus site is empty foothill land. |
| 3 | **1938 — The new campus** | UCSB AXJ-1938 (USDA) | 1:20,000 aerial | Brand-new PWA/WPA campus (opened 1937), tent-college days over. |
| 4 | **1956 — Postwar boom** | UCSB C-22555 (Jul 1956) | 1:14,400 aerial | Streets filled in, campus growing, hillsides still whole, **no freeway**. |
| 5 | **1971 — The freeway cut** | UCSB TG-2755 (Mar 1971) | 1:10,440 aerial (2nd-best detail in set) | SR-2 carved through the hills past campus — built by '72 yet unopened until 1978 (famously used as a film set). |
| 6 | **1979 — Freeway open** | UCSB TG-3800 (Jul 1979) | 1:24,000 aerial | The 2 finally open (spring 1978); modern street pattern complete. |
| 7 | **2022 — Today** | USDA NAIP (May 2022) | 60 cm color | Full modern campus against the same hills. |

**Alternates considered:**
- *1936 C-4051 (1:7,200)* — the sharpest imagery in the whole collection, flown the year
  before the campus opened. Recommended as story-pin/detail material inside era 2–3 rather
  than its own stop; could replace 1938 if "eve of construction" beats "new campus".
- *1994 NAPP/DOQ* — would fill the 1979→2022 gap but needs an EarthExplorer login and the
  visual change in that span is modest. Recommended: skip, or add later as an 8th stop.
- *1944 DDF (1:10,000)* and *1960 C-23870 (1:14,400)* — excellent quality; omitted only to
  keep 7 stops with maximal change between adjacent eras.

**Why these seven:** each adjacent pair shows a dramatic, legible change (empty land →
campus → suburban fill → freeway cut → freeway open → today), every base layer is free,
directly downloadable, and publishable with credit, and eras 2–6 all have frames centered
on or near the campus.

---

## 3. Rights summary for the site's credits page

| Source | Status | Required credit |
|---|---|---|
| USGS topo maps, 3DEP, NAIP | Public domain | "USGS" / "USDA NAIP" (courtesy) |
| UCSB aerials | No UCSB copyright; pre-1930 + federal flights PD; Teledyne murkier but served openly | "Flight, frame, date. Courtesy of UCSB Library Geospatial Collection." (required) |
| LOC Sanborn (online eds.) | Public domain (LOC verbatim) | "Library of Congress, Geography and Map Division, Sanborn Maps Collection." |
| OSM | ODbL | "© OpenStreetMap contributors" + link (required) |
| Calisphere/archive photos | Per-item — check each before publishing | per item |

## 4. Known gaps & risks

- **1900 era is a map, not a photo** — no aerial photography existed; the UI should style
  and label it honestly.
- 1928 C-300 covers campus, but the Aug 1927 C-113 flight only grazes the AOI's south edge.
- Teledyne-era (1968–79) copyright is unresolved in the strict sense; UCSB serves these
  freely and without restriction notices. Low practical risk with credit; noted for honesty.
- Georeferencing the 1896/1900 topo (surveyed pre-GPS) will have the loosest alignment —
  expect tens of meters; acceptable for a map-styled era, will be documented in Phase 2.
- Ground-level story-pin photos depend on archive requests (manual to-dos below).
