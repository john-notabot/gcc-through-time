# Modern Base Data (imagery, OSM, elevation, hosting) — Research Findings

Researched 2026-07-03. AOI: lat 34.150–34.195, lon -118.245 to -118.210 (~3.2 × 5.0 km).

## Summary

| Layer | Source | Route | AOI size | License/attribution | Confidence |
|---|---|---|---|---|---|
| Today imagery | NAIP 2022 60 cm | Azure blob, anonymous /vsicurl clip | ~50–90 MB tiled z18 | Public domain; "USDA NAIP" courtesy | Verified live |
| Streets/buildings | OSM via Overpass | overpass-api.de POST | ~2–20 MB | **ODbL: "© OpenStreetMap contributors" REQUIRED** | Verified live |
| Terrain | 3DEP 1 m `CA_LosAngeles_B23` (2023 lidar) | TNM Access API → prd-tnm S3, keyless | <5 MB terrain-rgb | Public domain; "USGS 3DEP" courtesy | Verified live |
| Hosting | PMTiles + maplibre pmtiles plugin on GitHub Pages | rio-pmtiles / pmtiles convert | total ≪ 1 GB limit | — | Verified (docs) |

## 1. Modern aerial imagery — NAIP 2022 (60 cm), keyless Azure route

Latest published year for this AOI is **2022** (verified via Planetary Computer + AWS Earth Search
STAC; no 2023/2024 CA data in the open mirrors). Two source COGs (4-band RGBIR, ~484 MB each):

```
https://naipeuwest.blob.core.windows.net/naip/v002/ca/2022/ca_060cm_2022/34118/m_3411855_nw_11_060_20220505.tif
https://naipeuwest.blob.core.windows.net/naip/v002/ca/2022/ca_060cm_2022/34118/m_3411855_sw_11_060_20220511.tif
```

Anonymous range requests verified working — clip without full download:

```bash
gdalwarp -t_srs EPSG:3857 -te -118.245 34.150 -118.210 34.195 -te_srs EPSG:4326 \
  -b 1 -b 2 -b 3 -r bilinear -co COMPRESS=DEFLATE \
  /vsicurl/https://naipeuwest.blob.core.windows.net/naip/v002/ca/2022/ca_060cm_2022/34118/m_3411855_nw_11_060_20220505.tif \
  /vsicurl/https://naipeuwest.blob.core.windows.net/naip/v002/ca/2022/ca_060cm_2022/34118/m_3411855_sw_11_060_20220511.tif \
  naip2022_aoi.tif
```

Rejected alternatives: AWS s3://naip-* (requester-pays), EarthExplorer (login), USDA Box (no
scripted route). USGS High Resolution Orthoimagery: **zero products for this AOI** (verified).

## 2. Streets/buildings — OSM via Overpass (verified: 10,386 building ways in AOI)

```bash
curl "https://overpass-api.de/api/interpreter" --data-urlencode 'data=
[out:json][timeout:180];
( way["building"](34.150,-118.245,34.195,-118.210);
  way["highway"](34.150,-118.245,34.195,-118.210); );
(._;>;); out body;' > gcc_osm.json
# npx osmtogeojson gcc_osm.json > gcc_osm.geojson
# optional: tippecanoe -o osm.pmtiles -z16 gcc_osm.geojson
```

Fallback: Geofabrik `socal-latest.osm.pbf` (665.8 MB, daily) + `osmium extract`.
Attribution REQUIRED: visible "© OpenStreetMap contributors" → https://www.openstreetmap.org/copyright

## 3. Elevation — USGS 3DEP 1 m DEM (2023 lidar, published Aug 2025)

TNM Access API (no key/login) returns 4 GeoTIFF tiles (10×10 km, ~360 MB each) with public S3 URLs:

```bash
curl "https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Digital%20Elevation%20Model%20(DEM)%201%20meter&bbox=-118.245,34.150,-118.210,34.195&outputFormat=JSON"
# e.g. https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/CA_LosAngeles_B23/TIFF/USGS_1M_11_x38y378_CA_LosAngeles_B23.tif
```

Clip via /vsicurl + gdalwarp. Terrain-RGB pipeline (maintained fork):

```bash
pip install git+https://github.com/acalcutt/rio-rgbify
rio rgbify -b -10000 -i 0.1 --min-z 8 --max-z 15 --format png dem_aoi_3857.tif terrain.mbtiles
pmtiles convert terrain.mbtiles terrain.pmtiles
```

MapLibre: `raster-dem` source, `"encoding": "mapbox"`. AOI z8–15: <5 MB.

## 4. Hosting — GitHub Pages fits easily

- Limits (verified): site ≤ 1 GB, 100 GB/mo soft bandwidth, git 100 MB/file hard limit.
- Total project budget ≈ 60–120 MB for modern layers + historical era tiles → comfortable.
- **Recommended: PMTiles** single-file archives (one per era) + `pmtiles` JS plugin
  (`addProtocol`) in MapLibre. GitHub Pages serves Range requests + CORS — documented working.
- Keep each .pmtiles under 100 MB (split per era if needed).
