# Upload area: bring your own datasets

VoltGuard reads only its canonical tables. To run it on new data (for example a TNB extract
for the R1 back-test), upload files here: no code changes are needed. This README is copied to
`DATA_ROOT/uploads/README.md` by `make.ps1 setup`.

## What to upload

One file per canonical table, CSV (UTF-8, comma separated, header row) or Parquet.
`schema.yaml` lists every table, column, type, unit, allowed value and whether it is required.
`templates/` holds one CSV per table with the header row and example rows.

| Table | Needed for | Required? |
| --- | --- | --- |
| `transformer` | Zones, regions, transformer-meter accuracy, loss-model parameters (AS-8) | Yes |
| `premise` | Meter-to-transformer links (AS-1), feeder branch, phase, distance (AS-7) | Yes |
| `meter` | Smart or conventional meter per premise | Yes |
| `meter_reading` | Half-hourly kWh, optional voltage (AS-3) | Yes |
| `transformer_reading` | Supply per transformer (AS-2) | For zone balance |
| `meter_monthly_reading` | Conventional meters | If any |
| `account_event` | Tenancy changes, rooftop solar registrations (AS-6, AS-9) | Optional |
| `district_weather` | Daily temperature and sunshine (FR-DI-07) | Optional |
| `duty_roster` | Field teams and their bases (AS-5) | Optional |
| `customer_pii` | Names and addresses: restricted table, fake data only in R0 | Optional |
| `inspection_outcome` | Historic outcomes as training labels | Optional |

Time zone: Asia/Kuala_Lumpur. Timestamps are ISO 8601, for example `2026-08-01T00:30:00+08:00`,
marking the start of each 30-minute interval. Timestamps without an offset are read in the
time zone set in `column_map.yaml` (default Asia/Kuala_Lumpur) and reported as a warning.

If a dataset lacks a field (voltage, phase, branch, transformer meter or network parameters),
the pipeline does not fail: it uses the SDD fallbacks (AS-2, AS-3, AS-7, AS-8) and marks the
affected results low confidence.

## How to upload

**Option 1: folder + command**

1. Create `DATA_ROOT/uploads/<dataset_name>/` (letters, digits, `_`, `-`, `.`), e.g.
   `D:\VoltGuard\uploads\tnb_extract_2026_10\`.
2. Drop the files in. Name each file after its table (`meter_reading.csv`), or add a
   `column_map.yaml` (see `column_map.example.yaml`) when names or columns differ.
3. Run `.\make.ps1 ingest -Dataset tnb_extract_2026_10` (or `make ingest DATASET=...`).
4. Read the validation report it prints the path of (HTML and JSON, also copied to
   `<dataset>/_reports/v<N>/`). Errors reject the version; warnings do not.
5. Activate it: `docker compose run --rm api python -m voltguard activate tnb_extract_2026_10`,
   which points `config/data_sources.yaml` at this version. Then `.\make.ps1 pipeline`.

**Option 2: Data manager page (admin only)**

Sign in as `admin`, open **Data manager**, upload a CSV or Parquet file, pick its target table,
then validate, preview and activate. Behind it is `POST /admin/datasets`.

## What validation checks

- Missing columns, wrong types, unit conversions (`units:` in the column map)
- Plausible kWh and voltage ranges, allowed values
- At least 90% of the 48 intervals present per meter-day (SRS 5.3); meters below are flagged
- Duplicates (exact ones are dropped; conflicting ones are errors) and time-zone problems
- Timestamps on 30-minute boundaries and at most 48 intervals per day
- Every meter linked to exactly one transformer; readings refer to known meters

## Versions

Every ingest creates a new version (`DATA_ROOT/datasets/<dataset>/v<N>/`) with a manifest
(files, checksums, row counts, status). `config/data_sources.yaml` selects the active source per
table: `simulated`, `london`, `upload:<dataset>` (latest accepted) or `upload:<dataset>@v<N>`.
Switching back is a one-line change plus `make.ps1 pipeline`.
