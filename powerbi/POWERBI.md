# Manager dashboard in Power BI (R0)

The manager dashboard reads only the zone-level, pseudonymised reporting views (`rpt_*`). They hold
no premise IDs, premise locations or personal details (SRS FR-UI-01, NFR-07). Power BI connects
with one read-only account, `voltguard_powerbi`, which can read these views and nothing else, so
in R0 every manager sees all regions at zone level (SDD 9.2). Case pages with personal details
stay in the web app behind the API.

## Connect Power BI Desktop

1. Start VoltGuard (`.\make.ps1 up`). The database listens on `127.0.0.1:5432` on the laptop only.
2. Power BI Desktop -> Get data -> PostgreSQL database.
   - Server: `localhost:5432`, Database: `voltguard`, Data connectivity mode: Import.
   - Advanced: leave the SQL statement empty.
3. Credentials: Database, user `voltguard_powerbi`, password `POWERBI_DB_PASSWORD` from `.env`.
   (Power BI may ask about encryption on localhost; the connection never leaves the laptop.)
4. In the Navigator select the six `rpt_` views below and load them. Other tables do not appear
   for this account.
5. Refresh after each detection run (Home -> Refresh).

Without a database (for building the report on another PC): Get data -> Text/CSV and load the files
in `powerbi/snapshot/` (exported by `.\make.ps1 snapshot` from the demo data).

## Views

| View | Grain | Use |
| --- | --- | --- |
| `rpt_network_kpis` | One row: latest run | Key figures |
| `rpt_zone_latest` | Zone, latest run | Map and ranked leaking zones; transformer position rounded to ~100 m |
| `rpt_zone_daily` | Zone x day | Energy balance over time |
| `rpt_case_counts` | Region x district x zone x status x origin x week | Case counts |
| `rpt_outcomes` | Region x district x inspections (model-ranked / random sample) x outcome x month | Hit rates |
| `rpt_flag_rates` | Region x district | Flag rates by area (NFR-11); tenure is not in the R0 data |

Relationships: `rpt_zone_daily[zone]` -> `rpt_zone_latest[zone]` (many to one). Keep the others
unrelated (they are pre-aggregated). Set `zone_lat`/`zone_lon` data categories to Latitude/Longitude.

## Page 1: Network overview

- Cards (from `rpt_network_kpis`): Leaking zones (`flagged_zones`), Unexplained energy in flagged
  zones (`flagged_gap_kwh_per_day`, kWh/day), Zones without balance (`zones_without_balance`),
  Open cases (`open_cases`).
- Map (`rpt_zone_latest`): latitude `zone_lat`, longitude `zone_lon`, bubble size `gap_kwh_per_day`,
  legend `flagged` (true = leaking). Tooltip: zone, district, `gap_pct`, `uncertainty_kwh_per_day`,
  `gap_start`, `flat_24_7`. Zones only; no premise appears.
- Slicers: `region`, `district`.

## Page 2: Leaking zones

- Table (`rpt_zone_latest`, filter `flagged` = true), sorted by `gap_pct` descending: zone, district,
  `gap_pct`, `gap_kwh_per_day`, `uncertainty_kwh_per_day`, `gap_start` (blank = present since data
  start: see `gap_since_start`), `flat_24_7`, `priority`, `open_cases`.
- Line chart (`rpt_zone_daily`): axis `date`; values `supplied_kwh` and `metered_and_estimated_kwh`
  plus `technical_loss_kwh`; drill-through from the table by zone.
- Line chart: `gap_kwh` with `uncertainty_kwh` as an error band (Analytics pane), same drill-through.
- Note on the page: "Scores and flags rank risk; they are not findings of theft."

## Page 3: Cases and hit rates

- Stacked column (`rpt_case_counts`): axis `week`, values sum of `cases`, legend `status`.
- Clustered bar (`rpt_case_counts`): axis `origin` (model / random_sample / manual), values `cases`.
- Matrix (`rpt_outcomes`): rows `inspections` (model-ranked, random sample), columns `outcome`,
  values sum of `outcomes`. Add a measure
  `Hit rate = DIVIDE(CALCULATE(SUM(rpt_outcomes[outcomes]), rpt_outcomes[outcome] = "confirmed_theft"), SUM(rpt_outcomes[outcomes]))`
  and show it per `inspections` row: random-sample inspections are the unbiased reference.
- Table (`rpt_flag_rates`): flag rate and cases opened by district (fairness monitoring, NFR-11).

## R1

In R1 the dashboard either moves behind the API (web app) or uses Power BI row-level security by
region, so each manager sees only their region (SDD 9.2).
