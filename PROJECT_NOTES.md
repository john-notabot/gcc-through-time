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

- **Phase 1 — Research & source inventory:** research COMPLETE 2026-07-03; source inventory
  written (`research/source-inventory.md`); **awaiting John's approval of the 7-era list**
- Phase 2 — Georeferencing: not started
- Phase 3 — Website: not started
- Phase 4 — 3D stretch: not started

## Source log

(populated during Phase 1 — see `research/source-inventory.md`)
