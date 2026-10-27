# VoltGuard AI: UI and UX design requirements (R0 → R1 redesign)

This document guides a redesign of the web app and the inspector phone app. It covers who uses the app and
what they need, the design rules, the design tokens, each component and screen, accessibility, and
ready-to-paste prompts for Claude Code and design tools.

It changes no requirement. The SRS and SDD still decide what each role may see and do. Personal details stay
masked, scores are risk only, and agents never act alone.

**Today's problems** (from the end-to-end review):
- **Plain styling:** the pages are white cards with default controls, with no visual hierarchy or brand.
- **Long tables:** the suspect and audit tables are long and dense; the most important number is not the most visible.
- **No "what to do next":** every role lands on a generic page instead of their own task list.
- **Unexplained terms:** "± u", "CV", "gap" and "rank" have no explanation.
- **Phone app:** it works, but it looks like a desktop page shrunk down.

## 1. Users and their first question

| Role | Device | Their first question on opening the app | Home screen should show |
| --- | --- | --- | --- |
| Revenue Protection Manager | Laptop, sometimes a tablet | "Where are we losing the most, and is it getting worse?" | Region KPIs with trend arrows, leaking-zone map, exports waiting for the second approval |
| Analyst | Desktop, two screens | "Which cases are mine, and which premise do I check next?" | Unclaimed cases, my open cases, reports to approve, top suspects of flagged zones |
| Supervisor | Laptop and phone | "Who goes where today?" | Dispatch suggestions waiting, overdue cases, teams on duty, the Telegram chat |
| Field Inspector | Phone outdoors, poor signal, sun glare, gloves | "Where am I going, is it safe, what do I record?" | Today's cases in visiting order, the address with Navigate, safety warning, big outcome buttons |
| Data Scientist / Admin | Desktop | "Did last night's run work; is any data missing?" | Run status, data-quality alerts, model versions |
| Auditor | Desktop | "Who looked at what, and is the log intact?" | Chain status, filters by user, action and date |

## 2. Design principles

1. **Decision first.** Each screen opens with the one decision it supports, the evidence comes next, and the
   detail goes last. Example: a zone page starts with "Flagged · 12.8% gap · 156 kWh/day since 31 Aug ·
   likely mining (flat 24/7)", then the charts, then the suspects.
2. **Risk, never guilt.** Use "risk score", "suspect premise" and "unexplained energy". Never "thief" or
   "stolen by". Use orange for risk, not police red. A shield or lightning-bolt icon, not handcuffs.
3. **Privacy is visible.** Masked fields show a lock and say why ("Shown on an open case to its analyst,
   supervisor and inspector"). Unmasking is a deliberate, logged step with a small "logged" badge.
4. **Explain every number.** Every KPI and chart has a one-line plain-English (or BM) tooltip.
   Units are always shown (kWh/day, %, V, km).
5. **One accent per screen.** Brand navy for structure; orange only for risk; green for confirmed or OK;
   amber for warnings. No rainbow charts.
6. **Calm density.** Desktop is for experts: compact tables are fine, but use 8-pt spacing, sticky headers,
   tabular numbers and at most 10 rows before "show more".
7. **Phone is its own app.** One column, 48-px tap targets, sticky bottom action bar, readable in sunlight
   (high contrast mode), works offline with an obvious banner.
8. **Bilingual from the start.** Every string goes through `t()`. Bahasa Melayu labels can be 30% longer,
   so layouts must not break.

## 3. Visual language and design tokens

Keep the token names in `web/src/styles.css` (so charts and both themes keep working) and change their
values and scale.

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--brand` | `#0B3954` (deep navy) | `#123E5C` | Top bar, primary buttons, selected nav |
| `--brand-2` (new) | `#087E8B` (teal) | `#2BB3C0` | Secondary accents, links, focus ring |
| `--accent` | `#F5B700` (amber, the "volt") | same | Logo, tap marker, highlights; never for text on white |
| `--risk` | `#C2410C` | `#FB923C` | Flagged, risk score, suspects |
| `--ok` | `#15803D` | `#4ADE80` | Approved, confirmed, synced |
| `--warn` | `#A16207` | `#FBBF24` | Low confidence, no balance, offline |
| `--bg` / `--surface` / `--surface-2` | `#F4F6F9` / `#FFFFFF` / `#EDF1F6` | `#0B1118` / `#121A23` / `#1A2430` | Layers |
| `--text` / `--muted` | `#0F1B2A` / `#556273` | `#E6EDF5` / `#93A1B1` | Text (contrast at least 4.5:1) |
| Series 1–4 | `#2563EB`, `#C2410C`, `#0D9488`, `#7C3AED` | lighter versions | Charts, in this order |

- **Type:** Inter (or the system UI font) at 14 / 16 / 20 / 24 / 32 px. Tabular numbers for all figures.
  Weights 400, 600 and 700 only.
- **Spacing:** a 4-px base; 8 / 12 / 16 / 24 / 32 px gaps; cards with a 16-px padding and a 12-px radius.
- **Elevation:**
  - one soft shadow for cards;
  - one stronger shadow for popovers;
  - none in dark mode (use borders instead).
- **Icons:** one outline icon set (Lucide or Tabler, MIT), 18 px in tables, 20 px in nav.
  - Map pin = zone; home = premise; clipboard = case; send = dispatch; shield = audit.
- **Motion:**
  - 150–200 ms ease-out for hover and expand;
  - none for data changes;
  - respect `prefers-reduced-motion`.

## 4. Components

| Component | Requirement |
| --- | --- |
| App shell | Top bar with logo, global search (zone, premise or case ID), region chip, language, user menu. Left nav with icons, labels and count badges (Cases 5, Dispatch 3). The nav collapses to icons under 1200 px and becomes a bottom tab bar on phones |
| KPI card | Big number, unit, label, a 7-day sparkline and a change arrow ("▲ 8% vs last week"). Click opens the filtered list |
| Risk score badge | A 0–100 ring, coloured by band (0–19 grey, 20–39 amber, 40+ orange), with "rank 1 of 72" under it |
| Reason list | Signed contribution bars (orange adds, green subtracts), "Lines add up to 60 = score". Tooltips explain each feature |
| Data table | Sticky header, sortable columns, row hover, 10 rows with "show all", column chooser, CSV export, empty state with the next step |
| Chips | Status (new, assigned, visited, reporting, closed) with fixed colours. Tags (EV charging, solar) are green; low confidence is amber |
| Masked field | Lock icon, dashed border, the reason. When shown: an amber card with a "logged" badge |
| Charts | Line (time), bars (categories), voltage strip. Labelled axes with units, a legend, hover tooltips with exact values, a "view data" table toggle, colour-blind-safe series |
| Case timeline | Vertical, with one icon per event (created, suggested, approved, accepted via Telegram, on the way, visited, report, approvals, closed), relative times ("2 h ago") and the actor |
| Telegram chat | As built: phone-styled chat, inline buttons, answered stamp. Add a date separator, unread count and a "Link Telegram" QR code |
| Toasts | Bottom-right on desktop, top on phones; success, warning or error; an undo where the action can be reversed |
| Empty, loading and error states | Skeleton rows while loading; empty state with an illustration and the next action; errors in plain words with a retry |
| Confirm dialog | Only for destructive or outward actions (remote sign-out, reject suggestion, export). Says exactly what will happen |

## 5. Screens

1. **Overview (manager, analyst, supervisor)**
   - Layout: a KPI row (leaking zones, unexplained energy kWh/day, est. RM/month (R1), open cases, hit
     rate), then a large map on the left (60%) and the leaking-zone list on the right.
   - Map: zones are circles sized by kWh/day and coloured by state. A legend explains them. On hover, a
     card shows the zone, its gap and its trend.
   - Filters: district, date and "flagged only", shown as chips above the map.
2. **Zone**
   - Header sentence (decision first), chips (flagged, large load, flat 24/7, gap since).
   - Tabs: *Evidence* (energy balance with the uncertainty band, hourly gap profile), *Suspects* (top 10
     with score rings and the first reason), *Voltage* (the strip, with the located tap highlighted).
   - The manager sees the Evidence tab only, with the note on why.
3. **Premise**
   - Left: score ring, reasons, tags, confidence.
   - Right: masked or contact card, account events, "Open a case" (primary).
   - Below: use vs similar homes (with a marker for when the gap opened), neighbour voltage.
4. **Cases**
   - A Kanban view (New → Assigned → Visited → Reporting → Closed) next to the table view.
   - Cards show the case ID, premise, score, team and an overdue badge.
   - Filters: mine, unclaimed, overdue, random sample.
5. **Case**
   - A sticky header with the status stepper and the main action for the viewer's role (Claim, Approve
     dispatch, Draft report, Approve content, Approve export, Download PDF).
   - Then: people, contact (masked or shown), timeline, outcomes with photo gallery, similar cases, report.
6. **Dispatch (supervisor)**
   - As built, plus: teams on duty with their base and count of open cases.
   - Suggestions show the distance and a mini map.
   - Inspector phones with the last sync time.
7. **Assistant**
   - As built (chat, charts, table, query, CSV), plus: follow-up suggestions under each answer, "pin to my
     dashboard", and a source drawer for procedure answers.
8. **Models (data scientist)**
   - Version cards side by side with model-ranked vs random-sample hit rates (bar pair), precision, label count.
   - Alerts as a list with severity and acknowledge.
9. **Data manager (admin)**
   - A stepper: upload → validate (report) → preview → activate.
   - Active sources as a small diagram (table → source).
10. **Settings (admin)**
    - Grouped sliders and number fields with the default and current value.
    - "Preview effect" shows how many zones would be flagged.
    - Changes need a reason and are logged.
11. **Audit (auditor)**
    - The chain status banner at the top (intact or tampered).
    - Filters (user, action, object, date range).
    - Rows expand to show the details; export.
12. **Inspector phone app**
    - Bottom tabs: *Today*, *Messages*, *Assistant*, *Me*.
    - Case card: address (large), distance, joint-operation banner, status.
    - Case screen:
      - Navigate (Google Maps / Waze) and Call supervisor buttons;
      - reasons (3 lines) and a collapsible safety checklist;
      - outcome as 4 big tiles, notes with a voice-typing hint, camera grid, sticky "Submit" bar.
    - Offline banner at the top; pending-sync count on the *Today* tab.

## 6. Accessibility and language (must pass before release)

- Meets WCAG 2.2 AA:
  - contrast at least 4.5:1 for text and 3:1 for chart lines;
  - visible focus;
  - every control reachable by keyboard;
  - no information by colour alone (add icons or text);
  - charts have a text summary and a data-table toggle.
- Tap targets at least 44 × 44 px; form fields with real labels; error messages next to the field.
- Every visible string in `i18n.js` in English and Bahasa Melayu, including chart labels and toasts.
  Numbers and dates use the Malaysian locale (`en-MY`, `ms-MY`).
- Phone layout tested at 360 px wide and at 200% text size with no sideways scrolling. Today's layout passes
  at 390 px; check 360 px again after the redesign.

## 7. How to build it (suggested tools)

**Plugins in your Claude catalog that fit this work** (install from claude.ai → Settings → Plugins):

| Plugin | Why |
| --- | --- |
| **frontend-design** (Anthropic) | Builds distinctive, production-grade React UI instead of generic layouts. Use it for the shell, overview, case and phone screens |
| **Design** (Anthropic knowledge-work) | Design critique, design-system management, UX writing (copy in plain words and BM), accessibility review and dev handoff |
| **A11y Enforcer** (community) | Checks the React code for WCAG 2.2 issues (labels, focus, contrast) and fixes them |

**Skills already available in this session:**
- `dataink:dashboard-design` (KPI hierarchy and layout);
- `dataink:data-visualization` and `dataviz` (chart rules and palette);
- `dataink:visualization-review` (P0–P2 chart audit);
- `dataink:table-design` (suspect and audit tables).

**Libraries, if a component kit is wanted** (all MIT; keep the bundle small):
- **Radix UI primitives** (dialogs, tabs, tooltips: accessible behaviour without styles);
- **Lucide** icons;
- **Recharts** or **visx** for interactive charts. The current hand-made SVG charts are fine for R0.

Avoid heavy kits that fight the tokens. Keep the CSS-variable tokens as the single source of colour.

## 8. Prompts

Paste these into Claude Code (with the frontend-design plugin enabled) one screen at a time. Each prompt
repeats the constraints that must not change.

**Shell and tokens**

> Redesign the VoltGuard web app shell in `web/src` (React 18 + Vite, plain CSS in `styles.css`, no Tailwind).
> Follow `docs/UI_UX_DESIGN_REQUIREMENTS.md` sections 2–4: new token values in `:root` and the dark theme,
> Inter font, a top bar with global search (zone, premise or case ID → navigate), a left nav with Lucide icons
> and count badges from `/cases` and `/telegram/chats`, and a bottom tab bar under 760 px. Keep every route,
> role check and `t()` label. Do not change the API, masking or wording rules ("risk", never "thief").
> Check at 1440, 1024 and 360 px and in dark mode; no sideways scrolling.

**Overview**

> Rebuild `pages/Overview.jsx` per section 5.1: KPI cards with 7-day sparklines (use `/zones/{id}/balance`
> or add a small `/zones/trend` endpoint), a larger Leaflet map with circles sized by kWh/day and a legend,
> and the leaking-zone list as a compact sortable table. Zone-level data only: no premise IDs on this page
> (FR-UI-01). Keep the district and date filters.

**Zone and premise**

> Rebuild `pages/Zone.jsx` and `pages/Premise.jsx` per sections 5.2–5.3: a decision-first header sentence,
> tabs (Evidence, Suspects, Voltage), a score ring component, reason bars that add up to the score with
> tooltips, the top 10 suspects with "show all". Managers see the Evidence tab only. Keep `Masked` and the
> logged contact card exactly as they behave now.

**Case and Kanban**

> Add a Kanban view to `pages/Cases.jsx` and a sticky status stepper with the role's main action to
> `pages/Case.jsx` (section 5.4–5.5). Show case events (including `accepted`, `en_route` and `declined` from
> the Telegram bot) as an icon timeline. Every action still calls the same API endpoint.

**Inspector phone app**

> Redesign `field/FieldApp.jsx` as a phone-first app (section 5.12): bottom tabs Today, Messages,
> Assistant, Me; large address with Navigate (a `geo:` or Google Maps link built from the address shown
> to the assigned inspector only) and Call supervisor; outcome tiles; camera grid; a sticky Submit bar; an
> offline banner. Keep the encrypted store, the offline queue, the wipe rules and remote sign-out exactly as
> they are (NFR-16). Test at 360 × 740 with `is_mobile`.

**Copy and Bahasa Melayu**

> Using the Design plugin's UX-writing skill, rewrite every user-facing string in `web/src` in plain
> English at reading age 12, then add the Bahasa Melayu version in `i18n.js`. Risk wording only, never
> accusatory. Return a table of old, new and BM for review before changing the code.

**Accessibility pass**

> Run an accessibility review (A11y Enforcer or the Design plugin) on `web/src`: contrast, focus,
> keyboard, labels, chart text alternatives, colour-only meaning. Fix every issue at WCAG 2.2 AA and list
> what changed.

**Image or mock-up prompt (for a design tool, before coding)**

> A clean, modern operations dashboard for an electricity utility's revenue-protection team in Malaysia.
> Deep navy top bar with an amber lightning-bolt logo "VoltGuard AI", left icon navigation, light grey
> background, white cards with 12 px radius. Top row: five KPI cards with sparklines (Leaking zones 2,
> Unexplained energy 284 kWh/day, Open cases 5, Hit rate 47%). Below: a map of Selangor with orange and
> blue circles for transformer zones, and a ranked table of leaking zones with orange "flagged" and amber
> "flat 24/7" chips. Calm, data-dense, accessible, no people, no police imagery, Inter font, 1440 × 900.

## 9. Acceptance checks for the redesign

- [ ] The end-to-end run (`scripts/e2e_use_cases.py`) still passes all checks; update its selectors in the same change.
- [ ] Each role's home screen answers their first question (table in section 1) without scrolling at 1440 × 900.
- [ ] No premise ID or personal detail appears on manager or overview screens; masked fields show the lock and reason.
- [ ] WCAG 2.2 AA: automated check clean; keyboard walk-through of the demo steps works.
- [ ] Bahasa Melayu: every screen switched, with no truncated labels.
- [ ] Phone: 360 px, offline banner, outcome submitted offline and synced; tap targets at least 44 px.
- [ ] Bundle under 500 kB gzipped; zone and premise pages still load under 3 s (NFR-02).
