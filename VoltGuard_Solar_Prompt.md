# VoltGuard R0: finish the rooftop-solar handling (FR-PS-10) and show it

A mentor asked how VoltGuard tells rooftop solar from theft, and how it catches theft hidden behind solar.

**Already working in `backend/voltguard/detection/features.py`:**
- the solar tag, from: registration (`account_event.solar_registration`), export readings, daytime-only drop, sun-shaped drop, midday near-zero, sunshine correlation
- night-time-only evidence for solar homes
- a test that solar homes stay out of the top suspects

**Gaps:**
- a loophole in scoring
- no test of theft hidden behind solar
- missing checks
- nothing in the UI, the inspector app or the report shows the solar check, so users and judges cannot see it

Keep every existing privacy, role and approval rule. Reference FR-PS-10 and AS-9 in tests and docstrings. Record any new assumption in `DEVIATIONS.md`.

## 1. Close the loophole (Must)

`scoring.py` subtracts the solar penalty whenever the tag is present, so a thief who installs solar also gets points removed.

- Apply the solar penalty only to the **daytime** part of the evidence.
- If night-time evidence is strong, drop the penalty and add the reason: "Solar explains the daytime drop only; night-time use still fell X% from its own history and is Y% below similar homes."
  - Night-time evidence comes from: night drop vs. own history, night use vs. similar homes, night-time flatness, and the night-time voltage dip.
  - Set "strong" in `config/thresholds.yaml`, default: night drop ≥ 25% or night use ≥ 30% below peers.

## 2. Add the missing checks (Must unless marked)

1. **Energy budget:**
   - Add `capacity_kwp` (optional) to solar registrations: canonical schema, upload template, simulator.
   - Expected daily solar generation = capacity × peak-sun-hours from the district's daily sunshine. When no weather is loaded, use a configurable default range labelled `[peak sun hours: to confirm]`.
   - If the daytime drop is more than 1.2× the most the system could produce, the excess counts as unexplained, with the reason: "Daytime use fell more than a 4 kWp system can produce."
2. **Rainy-day rebound:** after the change point, compare daytime use on the cloudiest third of days with the sunniest third. Solar homes use more on cloudy days; a bypass stays low whatever the weather. Store the result as `rain_rebound` and use it in the solar decision.
3. **Timing vs. registration:** if the drop starts more than 14 days **before** the solar registration date, or within 3 days of the zone's gap start while the home is unregistered, add a supporting reason. Never use it on its own.
4. **Voltage signature (Should, needs voltage data):**
   - A midday voltage **rise** at the premise (reverse power flow) supports solar.
   - A night-time voltage **dip** near the premise supports a hidden load.
   - Show both in the solar check.
5. **Unregistered export:** export readings with no registration get an admin follow-up note: "Solar export with no registration: check the Solar ATAP / NEM / SelCo record." This is not scored as theft.
6. **Home battery (limit):** a battery can move solar energy into the evening. Add `has_battery` to registrations; when it is true, mark the night-time comparison as low confidence instead of skipping it.

## 3. Simulator and tests (Must)

New injected cases:
- `solar_with_theft`: solar installed, plus a night-time partial bypass or a flat 24/7 rig, registered for some homes and not for others
- `solar_unregistered_export`
- `solar_with_battery`

Tests:
- `test_FR_PS_10_solar_masking_theft_still_top`: solar + theft lands in the top 5% and its reasons mention night-time evidence
- plain solar homes stay out of the top suspects
- the energy-budget excess is flagged
- the rainy-day rebound separates solar from bypass
- the penalty is dropped when night evidence is strong

Add these rows to `reports/simulation_report.md` and `simulation_summary.json`: "solar homes in top suspects" and "solar + theft found in top 5%".

## 4. Show it (Must)

- **Premise page: a "Solar check" panel.** Each check on one line, with its number and a pass / not seen / no data mark:
  - registration (date, kWp)
  - export readings
  - daytime vs. night change
  - drop shape follows the sun
  - rainy-day rebound
  - energy budget
  - voltage signature
  - verdict, e.g. "Daytime drop explained by solar; night use normal: not counted as theft" or "Solar explains only part of the drop: night use fell 40%, still a suspect"
- **Zone page:** a "Cleared as legitimate" list showing solar, EV and metered-mining homes with their one-line reason; and a "Solar with unexplained night use" marker on suspects where the penalty was dropped.
- **Weekly report:** count of solar-tagged homes, solar homes still suspected, and unregistered exports, each with a one-line explanation.
- **Inspector app, solar homes:** checklist items:
  - panels and inverter seen
  - inverter's total generation reading (kWh) vs. expected
  - registration seen (Solar ATAP, NEM or SelCo)
  - wiring before the meter checked for bypass, even when solar is confirmed
  - new outcome reasons: "solar confirmed, no theft" and "solar plus bypass"
- **Field assistant documents:** add a short public explainer of Solar ATAP / NEM / SelCo to `data/docs_rag/`, with its source.

## 5. Done means

- All Must items pass tests.
- The demo zone includes one `solar_with_theft` home that ranks in the top 5%, and one plain solar home that is cleared.
- Both are visible on the Zone and Premise pages with their reasons.
- `DEMO.md` has a 20-second backup step: "Mentor question: what about solar?"
