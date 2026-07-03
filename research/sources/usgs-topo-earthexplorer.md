# USGS Historical Topo Maps (topoView/HTMC) & EarthExplorer — Research Findings

Researched 2026-07-03. AOI: lat 34.150–34.195, lon -118.245 to -118.210.

## TASK A — Historical topographic maps (no login, public domain)

Machine-readable route (verified): TNM Access API, same inventory topoView serves —
`https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Historical%20Topographic%20Maps&bbox=-118.245,34.150,-118.210,34.195&max=100`
→ 48 records with direct S3 URLs.

**Quad correction:** the AOI lies entirely east of -118.25, so the Burbank 7.5' quad is NOT
needed. Relevant quads: **Pasadena** (15' and 7.5') and the early **Glendale 1:24,000
special quad** (1928 series).

### Editions covering the campus point (verified)

| Quad | Scale | Edition / imprint | Notes |
|---|---|---|---|
| Pasadena | 1:62,500 | 1896, 1900 | Pre-development baseline |
| Los Angeles | 1:62,500 | 1894, 1900 | Overlaps AOI from west |
| Glendale | 1:24,000 | survey 1925; imprints 1928, 1932, 1939, 1948 | Brackets campus construction (1937) |
| Pasadena 7.5' | 1:24,000 | 1953 ed. (imprints 1955, 1960) | **Pre-freeway** |
| Pasadena 7.5' | 1:24,000 | 1966 ed. (aerial 1964) | Freeway mid-construction |
| Pasadena 7.5' | 1:24,000 | 1966 photorevised 1972 | SR-2 largely built |
| Pasadena 7.5' | 1:24,000 | 1966 photorevised 1988 | **Post-freeway** |
| Pasadena 7.5' | 1:24,000 | 1995 ed. (aerial 1993) | Modern baseline |
| Los Angeles | 1:100,000 / 1:250,000 | various 1901–1979 | Regional context |

### Download URL patterns (verified HTTP 200, no auth)

- GeoTIFF: `https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/CA_<Quad>_<scanID>_<year>_<scale>_geo.tif`
- Key scan IDs: Pasadena 1896: 298494/298495 · 1900: 298496–298504 · Glendale 1928: 290858,
  1932: 290859, 1939: 290856, 1948: 290857 · Pasadena 7.5' 1953(1955 imprint): 293979,
  1960: 293980/293981 · 1966: 293982 · PR-1972: 293983 · PR-1988: 293984 · 1995: 101744
- GeoPDF and thumbnail variants exist; FGDC XML metadata at thor-f5.er.usgs.gov WAF.

### Rights

All USGS topo maps pre-2009 are **public domain** (verified via USGS FAQ). Credit "USGS" requested.

### To inspect visually (downloadable, unresolved questions)

- Which Glendale imprint (1939 vs 1948) first shows campus buildings.
- Which Pasadena edition (1966 vs PR-1972) first shows SR-2 past campus.

## TASK B — EarthExplorer (login-gated; search-only findings)

M2M API refuses anonymous metadata search (verified) — frame-level inventory needs a free
ERS account.

| Dataset | Years | Expected over Glendale | Digitized? |
|---|---|---|---|
| Aerial Photo Single Frames | 1937–2014 | USGS mapping flights 1964, 1972, 1986, 1993 (proven via HTMC metadata) | Medium-res free; unscanned = **$30/frame + $5, 3–4 wk** — budget/time risk |
| NHAP | 1980–89 | Quad-centered frame over Pasadena quad covers campus | Much scanned free |
| NAPP | 1987–2007 | ~3 dates (late-80s / mid-90s / early-00s), 1:40,000 | Med + high-res free |
| DOQ | 1987–2006 | "Pasadena SW" (+ NW) quarter-quads, 1 m | Fully digital, free |
| High Res Orthoimagery | 2000s–2010s | Possibly LA-region orthos | Digital, free |

### Manual download steps for John

1. Free account: https://ers.cr.usgs.gov/register
2. https://earthexplorer.usgs.gov → Search Criteria → coordinates (34.150, -118.245) to
   (34.195, -118.210), or address "Glendale Community College, CA"
3. Data Sets → Aerial Imagery → check: Aerial Photo Single Frames, NHAP, NAPP, DOQ,
   High Resolution Orthoimagery
4. Results → foot icon for footprint, picture icon for preview
5. Download icon → prefer **Medium Resolution** or **High Resolution Film Scan** (both free,
   instant). "Film — scan on demand" = not digitized: $30/frame, 3–4 weeks — skip unless critical.

### Rights

USGS federal aerial photography and DOQs: public domain; credit "USGS EROS".

**Note:** UCSB already gives us free instant downloads for most of the same eras — EarthExplorer
is a supplement (notably NAPP high-res and the 1-m DOQ orthos), not a blocker.
