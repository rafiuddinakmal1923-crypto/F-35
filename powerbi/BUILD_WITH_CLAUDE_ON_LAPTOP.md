# Build the Power BI dashboard with Claude on your laptop

Power BI Desktop runs only on Windows, so the `.pbix` is built on the team laptop: by Claude in the Desktop
app (Cowork, with your Power BI connection), or by hand with the same steps. Everything it needs is in
this folder:
- `voltguard_theme.json`: colours that match the web app;
- `measures.dax`: the measures;
- `snapshot/*.csv`: offline data;
- `POWERBI.md`: the page layout.

## Before you start (5 minutes)

1. Start VoltGuard: `docker compose up -d`, or `.\make.ps1 demo` for fresh data. The database is on
   `localhost:15432`, or your `DB_HOST_PORT`.
2. Find the read-only password: open `.env` and copy `POWERBI_DB_PASSWORD`. Don't paste it into a chat;
   type it only into Power BI's own sign-in box.
3. Optional, for the cases pages: as `supervisor.cen`, run the case job and approve some suggestions, then
   record a few outcomes on the phone app, so the case and hit-rate visuals have data.

## Prompt to paste into Claude (Cowork / Desktop on the laptop)

> Build a Power BI Desktop report for VoltGuard AI and save it as `C:\Users\user\Desktop\coding\F-35\powerbi\VoltGuard.pbix`.
>
> **Data**
> - Get data → PostgreSQL database, server `localhost:15432`, database `voltguard`, Import mode, user
>   `voltguard_powerbi`. I will type the password myself when asked.
> - Load exactly these six views: `rpt_network_kpis`, `rpt_zone_latest`, `rpt_zone_daily`,
>   `rpt_case_counts`, `rpt_outcomes`, `rpt_flag_rates`.
> - If the database is not reachable, use Text/CSV with the files in `powerbi\snapshot\` instead, with the
>   same table names.
>
> **Model**
> - One relationship: `rpt_zone_daily[zone]` → `rpt_zone_latest[zone]` (many to one, single direction).
> - Set `rpt_zone_latest[zone_lat]` to Latitude and `[zone_lon]` to Longitude.
> - Set the date columns (`date`, `week`, `month`, `run_date`) to Date.
> - Add every measure in `powerbi\measures.dax`.
> - Apply the theme `powerbi\voltguard_theme.json` (View → Themes → Browse).
>
> **Page 1 "Network overview"**
> - Four cards: Leaking zones, Unexplained kWh per day, Zones without balance, Open cases.
> - A card for Gap change % formatted as a percentage with a ▲/▼ sign.
> - A map of `rpt_zone_latest` (bubble size `gap_kwh_per_day`, legend `flagged`, tooltips zone, district,
>   gap_pct, uncertainty_kwh_per_day, gap_start, flat_24_7).
> - Slicers for region and district.
> - A text box: "Scores and flags rank risk; they are not findings of theft. Zone-level data only."
>
> **Page 2 "Leaking zones"**
> - A table of `rpt_zone_latest` filtered to flagged = true, sorted by gap_pct descending, with conditional
>   formatting (orange data bars) on gap_kwh_per_day.
> - A line chart from `rpt_zone_daily`: date against supplied_kwh, metered_and_estimated_kwh and
>   technical_loss_kwh.
> - A second line chart of gap_kwh with an error band from uncertainty_kwh.
> - Drill-through from the table to these charts by zone.
>
> **Page 3 "Cases and hit rates"**
> - A stacked column of Cases by week and status.
> - A clustered bar of Cases by origin.
> - A bar pair: Hit rate model-ranked vs Hit rate random sample, with the subtitle "random sample = unbiased reference".
> - A matrix of rpt_outcomes: inspections × outcome.
> - A table of rpt_flag_rates by district (fairness, NFR-11).
>
> **Rules**
> - Never add a premise ID, a premise location or a personal detail: the views don't hold any, and the
>   report must not join anything else.
> - Use "risk", never "thief".
> - When done, refresh once, save, and give me a short list of what you built and any visual you could
>   not make.

## Check the result

- Each page loads with no warning icons; the slicers change every visual.
- No column named `premise`, `holder`, `address` or `contact` appears anywhere (Data view → search).
- Page 3 shows both hit rates side by side.
- Save it, then commit `powerbi/VoltGuard.pbix` if the team wants it in the repository. It holds only
  zone-level data, but check `.gitignore` and the team's rules first.

## If Claude cannot open Power BI

Follow the same steps by hand from `POWERBI.md`. The theme and measures files save most of the work.
