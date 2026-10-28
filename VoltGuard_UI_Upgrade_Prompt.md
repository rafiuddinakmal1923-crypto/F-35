# VoltGuard R0: UI upgrade and new demo features

You are improving the existing VoltGuard prototype in this repository (React + Vite in `web/`, FastAPI in `backend/`). The backend logic works; the web app looks like a generic admin panel and does not show off what makes VoltGuard different. Judges scored **User experience 5/10** and **Validation 6/10**, and asked about rooftop solar, simulated voltage and the TNB pilot. This brief fixes the look and adds features that answer those points.

`VoltGuard_SRS.md` and `VoltGuard_SDD.md` remain the source of truth. Every privacy, role and approval rule stays exactly as it is.

---

## 0. Ground rules

- Work on a new branch. Take Playwright screenshots of every page **before** you start (`reports/ui/before/`) and again at the end (`reports/ui/after/`), at 1440×900 and 390×844.
- Keep all existing tests passing; add tests for new endpoints and components.
- **Privacy stays as it is:**
  - the Overview map shows transformers only, never premises
  - personal details and exact locations appear only on an open case for its people
  - dashboards use zone-level data only
- Every new number shown must come from the API or a config file. No hard-coded figures. Anything estimated is labelled "estimate".
- Keep English and Bahasa Melayu labels for every new string (`i18n.js`).
- The inspector app (`/field`) must stay phone-first and work offline.
- Record new dependencies and the reason for each in `DEVIATIONS.md`. Allowed: `recharts`, `lucide-react`, `@fontsource/ibm-plex-sans`, `@fontsource/space-grotesk` (self-hosted fonts, so the demo works offline). Pin exact versions.

## 1. Visual direction: "network control room"

Match the pitch deck so the demo and slides feel like one product.

- **Palette (CSS tokens in `styles.css`):**
  - navy shell `#0F1A2B`; panels `#18273F`; panel border `#2C4468`
  - text `#F6F7F4`; muted `#B8C4D4`
  - amber accent `#F2A33A` for risk and the primary action
  - teal `#2DD4BF` for "balanced / cleared"
  - red-orange `#FB7A3C` only for confirmed theft
  - Keep a light theme (`#F6F7F4` background, `#1B2433` text, darker amber `#9C5708` for text on light) for printing and projectors; toggle in the top bar and remember the choice.
- **Type:** Space Grotesk for numbers, scores and headings; IBM Plex Sans for body. Numbers use tabular figures.
- **Layout:**
  - slim left rail with icons and labels; top bar with region, run date, data mode (simulated / upload) and mock badge
  - content as a grid of panels, never a long scroll of stacked cards
  - a **right-hand detail drawer** opens premises and cases without leaving the zone
- **Components to restyle or create:** KPI tiles with a small sparkline and change vs. last run; score ring (0–100, amber fill); status pills; reason bars; empty, loading (skeleton) and error states for every panel.
- **Motion:** 150–200 ms fades and slides only. Respect `prefers-reduced-motion`.
- **Accessibility:** WCAG AA contrast in both themes; full keyboard use with visible focus; never colour alone (pair with icons or labels); charts get text summaries for screen readers.

## 2. Pages to redesign

1. **Overview (manager, analyst, supervisor):**
   - Full-height dark map as the hero. Use CARTO dark tiles when online; fall back to a plain grid with transformer dots when offline.
   - Transformer dots sized by gap and coloured by status, with a pulse ring on large-load priority zones.
   - KPI strip:
     - flagged zones
     - gap kWh/day
     - **estimated RM at risk per month** (section 3.1)
     - open cases
     - model vs. random-sample hit rate
   - "Leaking zones" leaderboard beside the map, with a mini gap sparkline per zone.
2. **Zone (the main demo screen):**
   - Top: energy balance chart with the uncertainty band and a "gap opens" marker; hourly gap profile with a "flat 24/7" badge.
   - Middle: the **feeder schematic** (section 3.2).
   - Right: ranked suspects as cards (rank, premise ID, score ring, top reason, tags).
   - Clicking a card opens the premise drawer.
3. **Premise drawer / page:**
   - score ring and **reason waterfall** (section 3.3)
   - **evidence timeline** (section 3.4)
   - usage vs. similar homes
   - the "why cleared" box for tagged homes (section 3.5)
   - masked contact panel with a lock icon and a one-line reason
4. **Case:**
   - status stepper: New → Assigned → Visited → Reporting → Closed
   - approvals shown as two signature blocks: content approver, then a different export approver
   - audit trail as a vertical timeline
   - report preview in a paper-style frame
5. **Inspector app:**
   - large tap targets; a today's-cases list with distance
   - one-screen outcome form with big outcome buttons and a camera button
   - clear "saved offline / synced" banner; Bahasa Melayu first if the phone is set to it
6. **Login:** a role picker with the test accounts as cards (demo only, behind `DEMO_MODE=true`), so judges can switch roles in one click.

## 3. New features

Build Must items first.

### 3.1 RM at risk (Must)
- Estimate RM per month for each flagged zone: excess gap kWh × a tariff from `config/tariffs.yaml`.
- Default the tariff to a clearly labelled placeholder such as `[TNB domestic tariff: to confirm]` with an editable value.
- Show it on Overview and Zone, always labelled "estimate". Add it to the `rpt_` zone views.

### 3.2 Feeder schematic (Must)
- An SVG one-line diagram of the zone: transformer at the left, each phase as a lane, branches as lines, premises as nodes in street order.
- Node colour = risk score; a voltage-residual overlay shows the dip deepening towards the tap.
- The suspect highlighted; hovering shows premise ID, score and residual.
- Uses the existing `/zones/{id}/voltage` and `/suspects` data, and needs no exact locations.
- When voltage data is off, show the schematic without the overlay and a "voltage not available: ranking uses balance and usage" note.

### 3.3 Reason waterfall (Must)
- Horizontal waterfall: each reason's contribution, legitimate-use penalties as negative bars, "other" and "capped" lines, ending exactly at the score.
- Pattern-model SHAP sub-reasons expand on click.
- Plain-language label on every bar.

### 3.4 Evidence timeline (Should)
One time axis per premise showing:
- the zone's gap start
- the premise's change point
- tenancy change
- solar registration
- case events

### 3.5 Why cleared (Should)
- For homes tagged EV charging, rooftop solar, metered mining or vacancy, show why they were not ranked high. Example: "Drop is daytime-only and follows sunny days; night use unchanged. Solar registration on 2026-03-02."
- Answers the judges' rooftop-solar question on screen.

### 3.6 Validation page (Must)
New page `/validation` for manager, analyst and data scientist. It reads a JSON summary written by the simulation report (add `reports/simulation_summary.json` and `GET /validation/summary`) and shows:
- held-out results: share of injected thefts in the top 5%; inspections per theft found, model vs. random order
- **where it breaks:** smallest detectable tap vs. noise level, and detection vs. share of monthly-read meters
- model-ranked vs. random-sample hit rate per model version
- a limits panel: voltage is simulated; SGCC is daily data from China; results are simulation, not TNB

Numbers come only from the files. Missing results show "not run yet", never a placeholder number.

### 3.7 Back-test replay (Should)
- Page `/backtest`: pick a zone with a known case, then drag a day slider. The zone balance, flag state and suspect ranking replay day by day.
- A marker shows the first day the known case entered the top 5% ("time to detection").
- Uses `scripts/backtest.py` output through `GET /backtest/{zone}`.
- This is the demo of the pilot ask.

### 3.8 Guided demo mode (Must)
- With `DEMO_MODE=true`, add a floating "Demo guide" panel that walks through the 7 live steps of SDD 10.5. Each step has:
  - a one-line narration
  - a button that navigates to the right page and role
  - a check mark when its pass criterion is met
- Add a "Reset demo" admin action that reseeds in under 30 seconds.
- Judges reaching the app through the tunnel can follow it on their own.

### 3.9 Data health (Should)
Extend the Data manager with a per-table health card:
- rows
- completeness per meter-day
- duplicates removed
- time-zone fixes
- which fallbacks (AS-2, 3, 7, 8, 9) are active

This answers "explains data quality and preparation".

### 3.10 Today's route (Could)
- For a supervisor or inspector, order the day's assigned cases by travel distance from the team base (straight-line is fine; label it).
- Show the order in the inspector app.

### 3.11 Landlord alert concept (Could, mock only)
- A clearly labelled "Concept: R2, opt-in only" screen showing a consent-based alert to a property owner when a rented premise's zone is flagged.
- Uses simulated data, sends nothing, and is not linked from the main nav unless `DEMO_MODE=true`.
- The SRS keeps the landlord portal out of scope for R0.

## 4. Done means

- Before and after screenshots are in `reports/ui/`, and `reports/ui/CHANGES.md` lists each change with the screenshot pair.
- All Must items in section 3 work in both themes, at desktop and phone widths, and in English and Bahasa Melayu.
- Existing and new tests pass, including `backend/tests/e2e/test_web_flow.py` updated for the new layout.
- The 7 live demo steps still run inside 5 minutes, now driven from the demo guide.
- `DEMO.md` is updated with the new screens.

Start by taking the before screenshots, then write a short plan in `reports/ui/PLAN.md`, then build.
