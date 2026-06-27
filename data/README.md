# Data Files

## Primary Web App Input

`mois-ppltn-data-stus-sido-od-202605.csv`

Required columns used by `index.html`:

```csv
period,origin_code,origin,destination_code,destination,people,male,female,level,source_status,source_endpoint
```

`origin` is the MOIS `mvt*` departure side. `destination` is the MOIS `mvin*` arrival side.

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
