# UI upgrade plan (`VoltGuard_UI_Upgrade_Prompt.md`)

Branch `claude/ui-upgrade`. Before screenshots: `reports/ui/before/` (old build, light theme, local stack
with cases). After screenshots: `reports/ui/after/` (dark default, plus a light set). Script:
`scripts/ui_screenshots.py`. Changes and pairs: `reports/ui/CHANGES.md`.

## Order of work

1. **Design system** (`web/src/styles.css`, `components/ui/`)
   - Tokens for the "network control room" palette; dark default, light theme for projectors/printing,
     toggle in the top bar, remembered in `localStorage` (`vg_theme`), `data-theme` on `<html>`.
   - Space Grotesk (numbers, scores, headings) + IBM Plex Sans (body), self-hosted with `@fontsource`.
   - Shell: slim left rail (icons + labels), top bar with region, run date, data mode, mock badge, theme and
     language toggles. Panel grid layout, right-hand drawer, skeleton/empty/error panel states,
     150-200 ms fades, `prefers-reduced-motion`, visible focus, AA contrast in both themes.
   - Components: `Panel`, `KpiTile` (sparkline + change vs last run), `ScoreRing` (amber), `StatusPill`
     (icon + label, never colour alone), `ReasonBars`, `Drawer`, `Skeleton`, chart text summaries.
2. **Backend for the Must items**
   - 3.1 RM at risk: `service/value.py` (excess gap = max(gap - u, 0), x 30 days x tariff from
     `config/tariffs.yaml`; no tariff = labelled placeholder, never a guessed number); in `/zones`,
     `/zones/{id}/balance`, new `rpt_zone_value` view; admin edits the tariff in Settings
     (`PUT /settings/tariff`, audited, writes `config/tariffs.yaml`, which the weekly report already reads).
   - 3.6 Validation: the simulation report also writes `reports/simulation_summary.json` (held-out results,
     noise sweep, monthly-read sweep); `GET /validation/summary` adds hit rates per model version; missing
     results are `null` ("not run yet").
   - 3.8 Demo guide: `GET /demo/status` (7 pass criteria checked against the database, step targets from
     `config/demo.yaml`), `POST /auth/demo-token` (one-click role cards, only when `DEMO_MODE` is on),
     `POST /admin/demo/reset` (admin job: reset cases, reseed, detection).
   - 3.3 waterfall: pattern-model SHAP sub-reasons stored with values in the feature details.
   - 3.4 timeline + 3.5 why cleared: premise view adds case events and the legitimate-use evidence.
   - 3.7 Back-test: `scripts/backtest.py --replay` writes `reports/backtest_replay.json`; `GET /backtest`,
     `GET /backtest/{zone}` (premise IDs for analysts/supervisors/data scientists only).
   - 3.9 Data health: `GET /admin/data-health` (rows, completeness per meter-day, duplicates removed,
     time-zone fixes, active fallbacks AS-2/3/7/8/9).
3. **Pages** (section 2): Overview (map hero, KPI strip, leaderboard), Zone (balance + hourly + feeder
   schematic + suspect cards + premise drawer), Premise (ring, waterfall, timeline, similar homes, why cleared,
   masked contact), Case (stepper, two signature blocks, audit timeline, paper report), Inspector app
   (big targets, distance, one-screen outcome form, offline/synced banner, BM first), Login (role cards in
   demo mode), new Validation, Back-test, Landlord concept (demo mode only); restyle the rest, Weekly frame only.
4. **Tests**: API tests for every new endpoint; web component tests (`node --test`) for the pure helpers
   (waterfall maths, schematic layout, value labels, i18n coverage EN/BM); e2e web flow updated for the layout.
5. **Docs**: `DEVIATIONS.md` (fonts; Esri dark tiles because CARTO now needs a key; recharts not used),
   `DEMO.md`, `HANDOFF.md`, `reports/ui/CHANGES.md`, after screenshots.

## Rules kept

Overview map shows transformers only; premise details/locations only on an open case for its people
(the API decides; the UI never asks for more); dashboards and `rpt_` views stay zone-level; every number
from the API or config; estimates labelled; EN + BM for every new string; `/field` phone-first and offline.
