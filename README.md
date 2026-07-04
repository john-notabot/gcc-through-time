# GCC Through Time

A time-slider map of the Glendale Community College campus and the Verdugo
foothills, 1900 → today. Drag the slider to watch the campus appear, the
streets fill in, and the Glendale Freeway cut through the hills.

Built for the GCC community. Not an official college publication.

## Eras

~1900 (USGS topo) · 1928 · 1938 · 1956 · 1971 (1968–71 composite) · 1981 · 2022

Historical aerial photography courtesy of the **UCSB Library Geospatial
Collection**; topographic maps and modern imagery from **USGS** and **USDA NAIP**
(public domain). Street data © OpenStreetMap contributors (ODbL).

## Structure

- `site/` — the static website (MapLibre GL JS, self-contained; deployed via GitHub Pages)
- `site/tiles/<era>/` — XYZ WebP tiles, z12–17, cut from georeferenced era mosaics
- `scripts/` — the full reproducible pipeline: download → georeference → mosaic → tile
- `research/` — source inventory, per-frame ground-control points, accuracy log
- `PROJECT_NOTES.md` — decisions and provenance

## Accuracy

Historical frames are aligned to the modern street grid via template matching
against ~450 OpenStreetMap intersection coordinates (RMS 2–5 m per frame).
Hillsides can shift a few tens of meters between eras (the scans are not
orthorectified). Details: `research/georeferencing-accuracy.md`.

## Rebuilding

```
python3 -m venv .venv && .venv/bin/pip install rasterio==1.3.11 numpy pillow opencv-python-headless mercantile
.venv/bin/python scripts/... # see PROJECT_NOTES.md for the era build sequence
```

Local preview: `python3 -m http.server 8722 --directory site`
