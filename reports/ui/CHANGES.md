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
| Value at risk | "[TNB tariff: to be supplied]" | kWh/day × 30 shown as a sum; RM only when `config/tariffs.yaml` has a tariff; upper estimate and above-threshold estimate, both labelled estimates |
| Hit rates | Table of rates | Chart and table with 95% Wilson ranges and counts ("6 of 10"); takeaway says when ranges overlap, names the number of random checks, and flags simulated outcomes |
| Outcomes and cases | One line | This week vs all time (No access marked "not used for learning"); cases by status with a one-line meaning |
| Trust | None | Data quality (complete meter-days, monthly-read share, zones without a transformer meter, fallbacks AS-2/3/7/8/9 in use), model in use, alerts, thresholds from Settings |
| Limits and steps | None | Assumptions and limits (switched on by the data), up to three rule-based next steps with the "not written by the language model" note, glossary, footer with data and model versions |
| Language | English only | English or Bahasa Melayu (`?lang=en|ms`); the web page follows the interface language |
| Telegram | Headline text at a fixed time (Mon 07:45 server time) | Headline with the top action, plus the PDF (`sendDocument`) after an output check on the PDF's own text; day, time, PDF on/off and supervisor copies set in Settings (`weekly.*`, MYT), applied without a restart |
| Web page | Separate React charts | Shows the report itself (same HTML as the PDF), with Download PDF and Send to my chat |

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
