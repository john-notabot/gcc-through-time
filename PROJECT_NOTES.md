# GCC Through Time — Project Notes

Public-facing time-slider website showing the GCC campus (1500 N Verdugo Rd, Glendale, CA)
and surrounding Verdugo foothills across 5–7 era snapshots, ~1900 to today.

## Key decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-03 | Project lives at `~/Projects/gcc-through-time`, deployed via GitHub Pages | Keeps multi-GB tile data out of Dropbox sync; free hosting, no API keys |
| 2026-07-03 | Neutral/archival visual design, no official GCC logo | Avoids trademark/sign-off issues; GCC named in intro text only |
| 2026-07-03 | Timeline open-ended | Optimize for research and georeferencing quality over speed |
| 2026-07-03 | Login-gated sources (USGS EarthExplorer) flagged with exact instructions for John rather than skipped | Best imagery sometimes lives behind free accounts |
| 2026-07-03 | MapLibre GL JS over Leaflet | Better mobile touch performance and smooth layer crossfading |
| 2026-07-03 | **Era list approved by John**: ~1900 (topo), 1928, 1938, 1956, 1971, 1979, 2022 | Max visual change between stops; all sources free + publishable. 1936 C-4051 reserved for story-pin detail; 1990s stop skipped (login-gated, low visual delta) |
| 2026-07-03 | **Era 6 is 1981, not 1979**: TG-3800 film edge is date-stamped 4/28/81; UCSB index said 1979-07 | Trust the film over the index. Era labels updated. Film-edge dates verified for all key frames: 1928, 6/5/38, 8/22/56, 4/3/71, 4/28/81 |
| 2026-07-03 | Georeferencing method: few manual seed GCPs → gradient template matching at OSM intersections → RANSAC → order-2 polynomial warp | Cross-era SIFT failed (5-10 inliers); local template matching with OSM ground truth gives 30-45 GCPs/frame at ~3-5 m consistency. Eras chain: each matches appearance against the next-later era but coordinates always come from OSM, so errors don't compound |

## Open question for John (era 5)

RESOLVED 2026-07-03: an earlier note here claimed the 3/19/68 frame showed the freeway
open at campus — that was a misreading of Verdugo Rd (then the signed SR-2 surface
route, a busy divided boulevard just west of campus). Georeferenced 1956/1960/1968
comparison confirms the canyon east of campus is uncut through 1968. Original timeline
stands (cut carved early 1970s, opened 1978), so era 5 = 1971 is historically right.
Remaining issue: the 1971 flight's row 26 was never scanned — ~880 m coverage gap
across the campus strip. Options A/B/C presented to John (see chat); recommendation A
(1971 + 1968 fill, labeled as composite).

## Working area

Bounding box (approx): Verdugo foothills north of campus, SR-2 (Glendale Freeway) corridor
to the west, Verdugo Rd / Cañada Blvd corridor. Campus at ~34.167 N, -118.230 W.

## Manual to-dos for John

- [ ] **Email Glendale History Room** (glendalehistoryroom@glendaleca.gov, 818-548-2037) —
      ask for ground-level photos: campus construction 1936–37, N Verdugo Rd streetscapes,
      SR-2/Glendale Freeway construction near Mountain St 1970s. Research is by appointment.
- [ ] **GCC Archives request** (library@glendale.edu or
      https://glendale.libwizard.com/f/GCC-Archives-Request-Form) — early campus photos,
      1937 opening, yearbook aerials (*La Reata*), tent-college era shots.
- [ ] *(Optional — only if we add a 1990s era)* free USGS ERS account at
      https://ers.cr.usgs.gov/register for EarthExplorer NAPP/DOQ downloads.
- [ ] *(Optional, reference only)* LA Public Library card grants remote ProQuest access to
      the offline 1925/1950 Sanborn volumes — useful research, not publishable.

## Phase status

- **Phase 1 — Research & source inventory:** COMPLETE 2026-07-03, era list approved
- **Phase 2 — Georeferencing:** COMPLETE 2026-07-03. All 7 era layers registered
  (RMS 2.1–4.5 m/frame), tiled (25 MB), accuracy documented. John is pursuing the two
  archive to-dos (History Room + GCC Archives) in parallel — photos will slot into pins.
- **Phase 3 — Website:** BUILT & tested locally 2026-07-03 (desktop + mobile viewports).
  **Awaiting: GitHub repo creation + push by John, then phone test = definition of done.**
- Phase 4 — 3D stretch: not started
- Phase 3 — Website: not started
- Phase 4 — 3D stretch: not started

## Source log

(populated during Phase 1 — see `research/source-inventory.md`)
