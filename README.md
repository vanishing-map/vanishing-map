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

- `data/mois-ppltn-data-stus-sido-od-202605-age-gender.csv`: normalized official MOIS province-level OD matrix for May 2026, with total, gender, and age-by-gender movement counts.
- `data/mois-ppltn-data-stus-sido-od-202605-age-gender-interregional.csv`: same OD data excluding same-province internal movement.
- `data/mois-ppltn-data-stus-sido-od-202605.csv`: earlier total/gender-only normalized MOIS province-level OD matrix for May 2026.
- `data/mois-sido-flows-interregional.csv`: same OD data reduced to inter-province dashboard flow rows.
- `data/kosis-dt-1b26001-a01-monthly-sido.csv`: KOSIS aggregate in/out/net movement by province for recent months. This is not OD flow data.

## Visual Contract

- Basemap: South Korea only. No 3D globe.
- Arc geometry: curved, elevated-feeling origin-to-destination paths over the basemap.
- Line thickness: selected movement volume. Default is `people`; filters can switch the volume basis by age and gender.
- Color: reserved for future attribute layers. It is not used for direction.
- Direction: arc direction and arrowhead.
- Node size: total inflow/outflow hub strength.
- Filters: age (`전체`, `0-14`, `15-24`, `25-39`, `40-54`, `55-64`, `65+`) and gender (`전체`, `남성`, `여성`) recalculate arc thickness, ranking, hub size, metrics, and table values.

## Source Notes

MOIS API path used for OD collection:

```text
https://apis.data.go.kr/1741000/ppltnDataStus/selectPpltnDataStus
```

Required parameters include `mvinAdmmCd`, `mvtAdmmCd`, `srchFrYm`, `srchToYm`, `lv`, and `serviceKey`.
