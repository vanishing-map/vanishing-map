# vanishing_map

Static web app for visualizing South Korea population movement as elevated origin-to-destination arcs.

## Run

This page loads local CSV data with `fetch`, so serve the folder locally:

```bash
python3 -m http.server 4173
```

Then open:

```text
http://127.0.0.1:4173/
```

## Current Data

- `data/mois-ppltn-data-stus-sido-od-202605.csv`: normalized official MOIS province-level OD matrix for May 2026.
- `data/mois-sido-flows-interregional.csv`: same OD data reduced to inter-province dashboard flow rows.
- `data/kosis-dt-1b26001-a01-monthly-sido.csv`: KOSIS aggregate in/out/net movement by province for recent months. This is not OD flow data.

## Visual Contract

- Basemap: South Korea only. No 3D globe.
- Arc geometry: curved, elevated-feeling origin-to-destination paths over the basemap.
- Line thickness: movement volume (`people`) using a log-like scale.
- Color: reserved for future attribute layers. It is not used for direction.
- Direction: arc direction and arrowhead.
- Node size: total inflow/outflow hub strength.

## Source Notes

MOIS API path used for OD collection:

```text
https://apis.data.go.kr/1741000/ppltnDataStus/selectPpltnDataStus
```

Required parameters include `mvinAdmmCd`, `mvtAdmmCd`, `srchFrYm`, `srchToYm`, `lv`, and `serviceKey`.
