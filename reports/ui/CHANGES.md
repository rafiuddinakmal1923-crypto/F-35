# UI upgrade: before and after

Brief: `VoltGuard_UI_Upgrade_Prompt.md` (plan in `reports/ui/PLAN.md`). Screenshots at 1440x900 (`_desktop`) and
390x844 (`_phone`), taken with `scripts/ui_screenshots.py` on the local stack (simulated data, `DEMO_MODE=true`):

- `before/`: the build before the upgrade (light theme, English).
- `after/`: dark theme (default), English. `after/light/`: light theme. `after/ms/`: Bahasa Melayu.

Every number on these pages comes from the API or a config file. Estimates are labelled "estimate", and
missing results show "not run yet", never a placeholder number. The privacy rules are unchanged:
- the Overview map shows transformers only;
- personal details and exact locations appear only on an open case, for its people;
- dashboards stay zone-level.

## Design system (section 1)

| Change | Where | Screenshot pair |
| --- | --- | --- |
| "Network control room" palette as CSS tokens: navy shell, amber for risk and the primary action, teal for balanced or cleared, red-orange only for confirmed theft | `web/src/styles.css` | any `before/` vs `after/` |
| Light theme for printing and projectors; toggle in the top bar, remembered (`vg_theme`) | `web/src/theme.js` | `after/zone_desktop.png` vs `after/light/zone_desktop.png` |
| Space Grotesk for numbers and headings, IBM Plex Sans for body text, both self-hosted (works offline); tabular figures | `web/package.json`, `main.jsx` | `before/overview_desktop.png` vs `after/overview_desktop.png` |
| Slim left rail with icons and labels. Top bar: region, run date, data mode, mock badge, search, theme and language | `App.jsx` | `before/work_desktop.png` vs `after/work_desktop.png` |
| Panels in a grid; right-hand drawer for a premise without leaving the zone; skeleton, empty and error states on every panel | `components/ui.jsx` | `after/zone_drawer_desktop.png` |
| KPI tiles with sparkline and change against the run before; score ring; status pills with icon and word (never colour alone) | `components/ui.jsx` | `after/overview_desktop.png` |
| 150-200 ms fades and slides; `prefers-reduced-motion` turns them off; visible focus ring | `styles.css` | n/a |
| Contrast: every text/background token pair measured at 4.5:1 or more in both themes. Light theft text darkened to `#B23A0A` (was 4.2:1) | `styles.css` | `after/light/` |

## Pages (section 2)

| Page | Before | After | Screenshot pair |
| --- | --- | --- | --- |
| Overview | Map and zone table stacked | Map as the hero (Esri dark or grey canvas, transformer dots sized by gap and coloured by status, pulse ring on large-load zones); KPI strip with RM at risk (estimate); "Leaking zones" leaderboard with sparklines | `before/overview_*` vs `after/overview_*` |
| Zone | Long scroll of cards and tables | Energy balance with uncertainty band and "gap opens" marker; hourly gap with "Flat 24/7" badge; feeder schematic; suspect cards in a scrolling column; premise drawer; "Cleared as legitimate" list | `before/zone_*` vs `after/zone_*`, `after/zone_drawer_*` |
| Premise | Reason table | Score ring and reason waterfall (SHAP sub-reasons on click); evidence timeline; use vs similar homes; "why cleared"; Solar check; masked contact panel with lock and reason | `before/premise_*` vs `after/premise_*` |
| Case | Lists | Status stepper; two approvals as signature blocks (content approver, then a different export approver); audit trail as a timeline; report in a paper-style frame | `before/case_*` vs `after/case_*` |
| Inspector app | Small controls | Large tap targets; today's cases in route order with distance; one-screen outcome form with big outcome buttons and a camera button; "saved offline / synced" banner; Bahasa Melayu first when the phone is set to it; solar checklist on solar homes | `before/field_phone.png` vs `after/field_phone.png`, `after/ms/field_phone.png` |
| Sign-in | Form only | Role cards for every test account (demo mode only); password form one click away | `before/login_*` vs `after/login_*` |
| Cases, Dispatch, Assistant, Models, Settings, Audit, Weekly, My work | Old styles | Restyled with the same tokens and panels. Settings edits the tariff. Weekly shows the report itself | matching `before/` and `after/` files |

## New features (section 3)

| # | Feature | Priority | Where | Screenshot |
| --- | --- | --- | --- | --- |
| 3.1 | RM at risk per flagged zone: excess gap x 30 days x tariff from `config/tariffs.yaml`. Shown in kWh with `[TNB domestic tariff: to confirm]` until a tariff is set; always labelled "estimate"; also in `rpt_zone_latest` | Must | `service/value.py`, Overview, Zone, Settings | `after/overview_desktop.png` |
| 3.2 | Feeder schematic: phase lanes, branches, premises in street order, risk colour, voltage-dip overlay, fitted tap; a note when voltage is off | Must | `components/FeederSchematic.jsx`, `lib/schematic.js` | `after/zone_desktop.png` |
| 3.3 | Reason waterfall ending exactly at the score; penalties step down; SHAP sub-reasons expand | Must | `components/Waterfall.jsx`, `lib/waterfall.js` | `after/premise_desktop.png` |
| 3.4 | Evidence timeline: zone gap start, the premise's change point, tenancy change, solar registration, case events | Should | `components/EvidenceTimeline.jsx` | `after/premise_desktop.png` |
| 3.5 | Why cleared: EV charging, rooftop solar, metered mining, vacancy, with the facts the scorer used | Should | `components/WhyCleared.jsx`, `service/explain.py` | `after/zone_desktop.png` (Cleared as legitimate) |
| 3.6 | Validation page from `reports/simulation_summary.json` and model versions; "not run yet" when missing | Must | `pages/Validation.jsx`, `GET /validation/summary` | `after/validation_*` |
| 3.7 | Back-test replay with a day slider and "time to detection" | Should | `pages/Backtest.jsx`, `GET /backtest/{zone}` | `after/backtest_*` |
| 3.8 | Demo guide: 7 steps with narration, a button to the right page and role, and a check mark when each pass criterion holds; Reset demo (measured 10.6 s) | Must | `components/DemoGuide.jsx`, `service/demo_guide.py` | any `after/*_desktop.png` (amber button) |
| 3.9 | Data health card: rows, completeness per meter-day, duplicates removed, time-zone fixes, fallbacks AS-2/3/7/8/9 | Should | `pages/DataManager.jsx`, `GET /admin/data-health` | `after/data_manager_*` |
| 3.10 | Today's route: straight-line distance from the team base, labelled | Could | inspector app | `after/field_phone.png` |
| 3.11 | Landlord alert concept ("Concept: R2, opt-in only"), mock only, sends nothing, demo mode only | Could | `pages/LandlordConcept.jsx` | `after/landlord_concept_*` |

## Checks

- Web unit tests (`cd web; npm test`): reason waterfall maths, schematic layout, value-at-risk labels, solar
  wording, and English/Bahasa Melayu coverage of every label.
- Backend tests: `tests/test_ui_upgrade.py` (new endpoints), `tests/test_solar.py`.
- Browser tests: `pytest -m e2e` (`tests/e2e/`), updated for the new layout. The 7 live steps run in about
  25 s in mock mode.
- Not checked: a screen-reader pass and a usability test with inspectors (NFR-13). Full WCAG validation needs
  manual testing with assistive technologies.

---

# Weekly summary report: before and after

Brief: `VoltGuard_Report_Upgrade_Prompt.md`; target layout: `VoltGuard_weekly_report_SAMPLE.pdf` / `.html`.
Files here, region CEN, rendered from the live demo data on 28 Oct 2026:

- `weekly_report_before.pdf` / `.html`: the old report (one page, bare figures).
- `weekly_report_after.pdf` / `.html`: the new report in English (6 A4 pages, page numbers in the footer).
- `weekly_report_after_ms.pdf` / `.html`: the same report in Bahasa Melayu.

Every number comes from the database or `config/` (never from the sample), and every sentence comes from
fixed rules on those numbers, not from the language model. Code: `backend/voltguard/service/digest.py`
(figures, on the caller's region-limited connection) and `digest_render.py` (rules, charts, HTML, PDF).

## What changed

| Area | Before | After |
| --- | --- | --- |
| Header | Title, both windows in one grey line, time in UTC | Report ID `VG-WK-<region>-<ISO week>`, time in MYT, intended reader, both windows on the right |
| Data mode | Not stated | "Simulated data (R0): not TNB data" banner, taken from the latest run's data sources; hidden for uploaded data |
| Summary | None | "This week in one paragraph": level and change, flagged zones and the top zone's share, flat 24/7 pattern, cases and inspections, up to two actions |
| Key figures | Six bare numbers | Six tiles with value, label, one-line definition and change vs the previous week |
| Two windows | Listed without explanation | "Why two dates?" note; explains a gap of more than 3 days (simulated data end, or late meter data) |
| Energy chart | Unlabelled line | Axis in kWh/day, dates, margin-of-error band, weekly averages with values, week marker, legend, how-to-read box, rule-based takeaway (steady / rising / falling, inside or outside the band) |
| Zones | Top-5 bar chart | Every zone with a balance: status colour plus label, margin whisker, that zone's threshold mark; table with district, % of supply, margin, threshold, status, leak start, daily pattern, priority, open cases; zones without a transformer meter listed separately |
| Value at risk | "[TNB tariff: to be supplied]" | kWh/day ├ù 30 shown as a sum; RM only when `config/tariffs.yaml` has a tariff; upper estimate and above-threshold estimate, both labelled estimates |
| Hit rates | Table of rates | Chart and table with 95% Wilson ranges and counts ("6 of 10"); takeaway says when ranges overlap, names the number of random checks, and flags simulated outcomes |
| Outcomes and cases | One line | This week vs all time (No access marked "not used for learning"); cases by status with a one-line meaning |
| Trust | None | Data quality (complete meter-days, monthly-read share, zones without a transformer meter, fallbacks AS-2/3/7/8/9 in use), model in use, alerts, thresholds from Settings |
| Limits and steps | None | Assumptions and limits (switched on by the data), up to three rule-based next steps with the "not written by the language model" note, glossary, footer with data and model versions |
| Language | English only | English or Bahasa Melayu (`?lang=en|ms`); the web page follows the interface language |
| Telegram | Headline text at a fixed time (Mon 07:45 server time) | Headline with the top action, plus the PDF (`sendDocument`) after an output check on the PDF's own text; day, time, PDF on/off and supervisor copies set in Settings (`weekly.*`, MYT), applied without a restart |
| Web page | Separate React charts | A dashboard of the week: the summary paragraph and actions, six KPI tiles, daily energy with the margin band, zone bars with margin and threshold, hit rates with 95% ranges, cases and outcomes, next steps, data and model. Sentences come from the same rules as the PDF (`GET /weekly?lang=` returns them as `text`). Download PDF gives the full report; Send to my chat sends it |

## Fixed on the way

- **Region leak in hit rates (FR-AD-01).** The `training_label` view ran with its owner's rights, so row-level
  security did not apply: each region's weekly hit rates (and the Assistant's hit-rate answer) counted every
  region's labels (20 instead of 10 for CEN). The view now has `security_invoker = true`; `rpt_outcomes` reads
  the base tables so Power BI keeps its zone-level, all-region view. Regression test:
  `test_FR_AD_01_training_labels_and_hit_rates_are_region_limited`.
- "All time" outcomes now count the same outcomes the hit rates learn from (live and historic).

## Tests

- `backend/tests/test_digest_render.py` (no database): summary rules, takeaways (steady / rising / falling,
  ranges overlapping or apart), Wilson intervals, next-step rules, empty weeks, tariff unset / set, simulated
  vs uploaded data, the weekly schedule, Bahasa Melayu sentences, and an HTML snapshot of every section heading
  in both languages with no premise IDs or personal details.
- `backend/tests/test_digest.py` (database): region limits, the HTML page in both languages, the PDF and the
  Telegram message with the PDF attached.
