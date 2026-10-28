# VoltGuard R0: make the weekly summary report self-explanatory

The weekly manager summary (`backend/voltguard/service/digest.py`, rendered by `render_html` and `pdf_bytes`) is correct but bare. A manager who has not seen the pitch cannot tell:

- what each chart shows
- why there are two date windows
- whether 43.8% vs 25.0% means anything with 16 and 4 inspections
- why a zone with 1 kWh/day is listed but not flagged

Rebuild it so every figure explains itself.

**Reference:** `VoltGuard_weekly_report_SAMPLE.pdf` and `.html` in this folder show the target layout and wording.
- Figures in the sample marked † are illustrative.
- Every number in the real report must come from the database or config, never from the sample.

`VoltGuard_SRS.md` and `VoltGuard_SDD.md` stay the source of truth. Privacy rules do not change: zone-level and case-level counts only, no premise IDs, names or addresses, region-limited by row-level security.

---

## 1. What to add (in this order on the page)

1. **Header:**
   - title and region
   - report ID (`VG-WK-<region>-<ISO week>`)
   - generated time in Malaysia time (MYT, Asia/Kuala_Lumpur, not UTC)
   - intended reader
   - both data windows on the right (meter data dates, field-work dates)
2. **Data-mode banner:** "Simulated data (R0): not TNB data" whenever the active source is simulated (`config/data_sources.yaml`). Hidden for uploaded real data.
3. **"This week in one paragraph":** 3–4 sentences built by fixed rules from the figures (not the language model):
   - level and change of unexplained energy
   - flagged zones and the top zone's share
   - flat 24/7 pattern if present
   - cases and inspections this week
   - plus up to 2 actions (section 4)
4. **Key figures:** six tiles. Each tile has the value, a bold label, a one-line definition and the change vs. the previous week:
   - flagged zones (of total)
   - unexplained kWh/day
   - kWh a month at this level
   - cases opened / closed
   - overdue cases
   - reports exported · open alerts
5. **"Why two dates?" note:** explains the meter-data window vs. the field-work window. If the gap between them is more than 3 days, say why (for example "the simulated meter data end on <date>").
6. **Section 2, "Is energy still going missing?":** the 14-day chart with:
   - a y-axis in kWh/day and date labels
   - the **margin-of-error band**
   - each week's average as a dashed line with its value
   - a "week starts" marker
   - a legend
   - a "What this shows / How to read it" box
   - a rule-based **Takeaway** (e.g. "steady", "rising", "falling", using the week-on-week change and whether the average is outside the band)
7. **Section 3, "Where is it going missing?":**
   - Chart of every zone with a balance: bar coloured by status (flagged / within margin), a margin-of-error whisker and a **threshold marker for that zone**, plus legend and how-to-read box.
   - Table with these columns: zone, district, kWh/day, % of supply, margin, threshold, status, leak started, daily pattern (flat 24/7 with CV, or "varies by hour"), priority (large load above 15%), open cases.
   - Takeaway naming the priority zone. If a listed zone is not flagged, say it is "inside its margin of error".
   - Zones without a transformer meter are listed separately as "no balance available".
8. **Value at risk (estimate):**
   - Show the sum: kWh/day × 30 = kWh/month.
   - RM = kWh × tariff from `config/tariffs.yaml`. While the tariff is unset, show `[TNB tariff: to be supplied]` and no RM figure.
   - Give two figures, both labelled estimates: all unexplained energy (upper estimate), and only the energy above each zone's threshold.
9. **Section 4, "Are inspections finding theft?":**
   - Hit-rate chart and table for model-ranked vs. random-sample inspections, with **95% Wilson intervals** and counts ("7 of 16").
   - Explain what the gap between the two rows means.
   - If the intervals overlap, the takeaway must say the difference is not yet proven and name the number of random checks so far.
   - If outcomes are synthetic, say they show how the measurement works, not real performance.
   - Side by side:
     - this week's outcomes vs. all time (confirmed theft, false alarm, inconclusive, no access, with "not used for learning" on no access)
     - cases by status with a one-line meaning per status (New, Assigned, Visited, Reporting, Closed)
10. **Section 5, "Can these figures be trusted?":**
    - Data quality for the meter week:
      - share of meter-days with at least 90% of readings
      - share of monthly-read meters
      - zones without a transformer meter
      - duplicates or time fixes
      - which fallbacks are active (AS-2, 3, 7, 8, 9), with "voltage is simulated" when relevant
    - Model in use: version, last retrain and label count, alerts this week, the flag thresholds from settings.
11. **Assumptions and limits:** fixed list, with items switched on or off by the data:
    - simulated data and simulated voltage (when true)
    - technical loss is estimated
    - monthly-read meters widen the margin
    - small leaks (about 1% of a zone's supply) can hide inside the margin
    - scores rank risk, not findings of theft
    - tariff not yet supplied (when true)
    - zone-level only, one region
12. **Recommended next steps:** up to 3, from fixed rules. Always add the note "generated from fixed rules on the figures above, not written by the language model." Rules:
    - flagged zones whose top suspects have no open case → "run the case job for …"
    - large-load zone → "suggest a joint operation with police"
    - fewer than 10 random-sample outcomes → "add random routine checks"
    - tariff unset → "confirm the TNB tariff"
    - overdue cases → "follow up N overdue cases"
    - open alerts → "review N data or model alerts"
13. **Glossary:** unexplained energy, margin of error, flagged zone, flat 24/7, hit rate, random routine check.
14. **Footer:** product and release, region, report ID, data and model versions, "scores rank risk; people decide after inspection", page numbers in the PDF.

## 2. Chart and writing rules

- Every chart has:
  - a title that says what it shows
  - axis units
  - a legend
  - a "What this shows / How to read it" box under it
  - a one-sentence takeaway
- Colour is never the only signal: use labels, whiskers or markers too. Text contrast must meet WCAG AA.
- Plain words first, technical term in brackets once (e.g. "margin of error (u)").
- Numbers use thousands separators and tabular figures. Percentages get one decimal place only when needed.
- Empty sections say why (e.g. "No inspections were recorded this week") rather than "None."
- The PDF is A4, with no section heading stranded at the bottom of a page (keep each heading with its chart), and stays readable in black-and-white print.
- Also provide a Bahasa Melayu version of every label, box and rule-based sentence (`lang` parameter; default English).

## 3. Telegram delivery

- **Weekly message to managers:**
  - a short text (headline numbers and the top action)
  - the report link
  - optionally the PDF as a document (`sendDocument`), allowed because the report is zone-level only
- **Output check:** run the existing output check on both the text and the PDF's text before sending.
- **Settings:** schedule (default Monday 08:00 MYT) and recipients (managers of that region with a linked Telegram chat), configurable in Settings.

## 4. Tests and done

- Unit tests for:
  - the summary rules
  - takeaway rules (steady / rising / falling, intervals overlapping or not)
  - Wilson intervals
  - next-step rules
  - empty weeks
  - tariff unset / set
  - simulated vs. uploaded data mode
- Snapshot test that the HTML contains every section heading and no premise IDs or personal details.
- Render the PDF for region CEN, save it as `reports/ui/weekly_report_after.pdf`, and list in `reports/ui/CHANGES.md` how it differs from the old one.

Start by reading `digest.py`, the sample report and the reporting views, then write a short plan.
