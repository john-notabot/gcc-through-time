#!/bin/bash
# Download era imagery: UCSB aerial frames + USGS historical topos
set -u
cd "$(dirname "$0")/.."
mkdir -p data/raw/ucsb data/raw/usgs_topo

python3 -c "
import json
for r in json.load(open('research/sources/download_manifest.json')):
    print(r['url'])" | while read -r url; do
  f="data/raw/ucsb/$(basename "$url")"
  if [ -s "$f" ]; then echo "SKIP $f"; continue; fi
  echo "GET  $url"
  curl -sS --fail --retry 3 --retry-delay 5 -o "$f" "$url" || { echo "FAIL $url"; rm -f "$f"; }
  sleep 2
done

# USGS topos: Pasadena 15' 1900 + 1896 (era 1), Glendale 1928 + Pasadena 7.5' 1953 (Phase 4 contours)
for u in \
  "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/CA_Pasadena_298496_1900_62500_geo.tif" \
  "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/CA_Pasadena_298494_1896_62500_geo.tif" \
  "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/CA_Glendale_290858_1928_24000_geo.tif" \
  "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/CA_Pasadena_293979_1953_24000_geo.tif" ; do
  f="data/raw/usgs_topo/$(basename "$u")"
  if [ -s "$f" ]; then echo "SKIP $f"; continue; fi
  echo "GET  $u"
  curl -sS --fail --retry 3 --retry-delay 5 -o "$f" "$u" || { echo "FAIL $u"; rm -f "$f"; }
done

echo "DONE. Inventory:"
du -sh data/raw/ucsb data/raw/usgs_topo
echo "ucsb frame count: $(ls data/raw/ucsb | wc -l | tr -d ' ')"
