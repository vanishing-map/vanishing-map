# Data Files

## Primary Web App Input

`mois-ppltn-data-stus-sido-od-202605-age-gender.csv`

Required columns used by `index.html`:

```csv
period,origin_code,origin,destination_code,destination,people,male,female,age_0_14,age_0_14_male,age_0_14_female,age_15_24,age_15_24_male,age_15_24_female,age_25_39,age_25_39_male,age_25_39_female,age_40_54,age_40_54_male,age_40_54_female,age_55_64,age_55_64_male,age_55_64_female,age_65_plus,age_65_plus_male,age_65_plus_female,level,source_status,source_endpoint
```

`origin` is the MOIS `mvt*` departure side. `destination` is the MOIS `mvin*` arrival side.

The app uses these columns to recalculate the visible flow volume when age and gender filters change.

## Interregional Web App Input

`mois-ppltn-data-stus-sido-od-202605-age-gender-interregional.csv`

This excludes same-province self loops and keeps the same total, gender, age, and age-by-gender columns.

## Dashboard Flow Export

`mois-sido-flows-interregional.csv`

This excludes same-province self loops so the arc map is not dominated by internal movement.

Columns:

```csv
origin,destination,people,reason_group,source_status,period,origin_code,destination_code
```

## KOSIS Aggregate Data

`kosis-dt-1b26001-a01-monthly-sido.csv`

This has monthly total in/out/net movement by province. It is useful for background metrics but does not contain origin-to-destination pairs.

## Demo Legacy Files

The `sample-2025-*` files are old demo data and should not be used for factual claims.
