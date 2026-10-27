# Build the VoltGuard AI prototype (R0)

You are building the hackathon prototype (release **R0**) of **VoltGuard AI** for Team F-35 (Hackspire Lumina, Domain 1: Predictive Infrastructure & Energy Analytics). Judges include TNB staff.

Two attached documents are the source of truth:

- `VoltGuard_SRS.md`: what the system must do (FR-/NFR-/AS- IDs, prototype tests, acceptance in section 7)
- `VoltGuard_SDD.md`: how it is built (architecture, components, data model, algorithms, API, agents, deployment, test plan, and the judge demo script in section 10.5)

Read both in full before writing any code. If this prompt and the documents disagree, the documents win, except for sections 3 (data sources) and 7 (machine, storage and deployment) below, which are newer.

---

## 1. What "done" means

1. Every live step in SDD 10.5 (steps 1–7) runs end to end on the team's Windows laptop after one setup command, inside a 5-minute demo.
2. The same build is reachable by judges through a public HTTPS link (section 7.4).
3. Backup steps 8–15 work and are scripted.
4. Every **Must** requirement in the SRS passes its "Prototype test"; Should and Could follow in that order.
5. The R0 acceptance table in SRS section 7 and SDD 10.4 is met. Report results honestly, including failures.
6. The data source can be swapped later by uploading new files, with no code changes (section 3).

## 2. Working rules

- **Repository first.** Run `git init`, add a `.gitignore` (exclude `.env`, data, models, uploads, photos, PDFs and logs), and commit the empty scaffold.
- **Plan first.** Before coding, write `PLAN.md`: milestones, a file tree, which SRS IDs each milestone covers, and open questions. Then start building without waiting, unless a question blocks a Must requirement.
- **Trace everything.** Reference requirement IDs in test names and docstrings (e.g. `test_FR_ZD_02_small_tap_flagged`). Keep `TRACEABILITY.md` mapping each FR/NFR to code and tests.
- **Lite profile by default.** Build the **lite** Docker Compose profile first and make it the default (section 7.2). The full profile with the SDD's heavier services (Airflow, Keycloak, MinIO, Celery/Redis, MLflow, Prometheus/Grafana) is optional. Every lite-profile swap goes behind the same interface as the full component and is recorded with its reason in `DEVIATIONS.md`. Never drop a privacy, audit or approval rule to save time.
- **No invented facts.** Never invent TNB data, statistics or procedures. Use placeholders such as `[TNB procedure: to be supplied]`.
- **Privacy rules are hard requirements.**
  - Personal details live only in `customer_pii` and use fake data in R0.
  - The language model never receives personal details: report drafts use placeholders, and inspector notes are scrubbed into `notes_redacted` before any agent, search or model sees them (SDD 8.4).
  - Personal details and premise locations appear only on an open case, for its assigned analyst, the supervisor and the assigned inspector.
  - Messages carry case links only.
  - Dashboards read zone-level pseudonymised `rpt_` views only.
- **Work in small, verifiable steps.** Commit after each milestone with passing tests. Run the tests yourself and fix failures before moving on.
- **Laptop-friendly.** Target a normal Windows laptop without a GPU (section 7.1). Everything runs through `docker compose` plus a `Makefile`; also provide `make.ps1` (or document `make` via Git Bash/WSL) so Windows users are not stuck.

## 3. Data sources: use current datasets now, swappable later

The final data sources are **not yet confirmed**. Build a data layer that works today with the datasets below and accepts new datasets later without code changes.

### 3.1 Canonical schema (the only thing the pipeline reads)

Use the table names from SDD section 4 exactly (singular):

- `transformer` (with `region`, `dtm_accuracy_class`), `premise` (with `feeder_branch`, `phase`, `distance_m`, `street_seq`, `lat`, `lon`), `meter`
- `meter_reading` (half-hourly kWh, optional voltage), `meter_monthly_reading`, `transformer_reading`
- `account_event`, `duty_roster`, `customer_pii` (fake data in R0)
- Optional historic `inspection_outcome` (labels)

The detection pipeline reads **only** canonical tables, never raw files.

### 3.2 Current datasets (adapters)

Write one adapter per source, each converting to the canonical schema:

| Source | Use | Where it goes |
| --- | --- | --- |
| London smart meter data (half-hourly kWh per household; Kaggle "Smart meters in London" or London Datastore) | Household load profiles for the simulator | `${DATA_ROOT}/raw/london/` |
| SGCC electricity theft dataset (Kaggle; daily kWh plus theft flag) | Training the pattern model only (SDD 5.4) | `${DATA_ROOT}/raw/sgcc/` |
| data.gov.my monthly electricity consumption (`https://storage.data.gov.my/energy/electricity_consumption.parquet`) | Rescaling profiles to Malaysian consumption levels | `${DATA_ROOT}/raw/datagovmy/` |

**Load speed:** files shared from a Windows drive into Docker are read slowly. Each adapter converts its raw CSV to Parquet **once** (`${DATA_ROOT}/processed/`) and later runs read only the Parquet. For London, default to a subset (a few hundred households, set in `config/data_sources.yaml`); the full set is optional.

Downloads may fail: Kaggle needs an API key, and networks may block sites. **Never block on a download.** Write `scripts/fetch_datasets.py`, which tries each source and prints manual download steps if it fails. Also include a built-in synthetic profile generator (tropical, aircon-heavy daily shapes) so the whole demo runs offline with zero downloads. The README must state which mode was used.

### 3.3 Simulator (SDD 10.2)

Build a simulator that outputs canonical tables plus a separate ground-truth file:

- 50–100 homes per transformer, branching feeders on three phases
- Losses and voltages from a load flow (pandapower)
- A configurable share of monthly-read conventional meters; some zones without a transformer meter
- Injected cases: full-bypass mining (including one present from day one), partial bypass, metered mining, EV charging, home business, a tenancy change with no theft, and rooftop solar installed partway through (one self-consumption home with no export, one with export), each with a matching solar registration in `account_event` for some and none for others
- Voltages are generated by the load flow because the open datasets hold kWh only. Say so in the README and in `simulation_report.md`.
- Tuning and held-out settings split by zone size, tap size, noise, profile set and seed
- Fake personal details for `customer_pii`; about 20 synthetic closed cases with notes (SDD 10.5 demo kit). Plant fake personal details in a few of those notes (e.g. "Encik Ahmad bin Ali", "Kumar a/l Muthu", an IC number with and without dashes, a phone number, "No. 12, Jalan Mawar 3, Taman Seri") so the notes scrubber is actually tested.

Ground truth goes to `${DATA_ROOT}/simulated/<run>/ground_truth.json` and is **never** loaded into tables the model reads.

### 3.4 Upload area for future datasets

This is a required deliverable: the team will upload new datasets here later.

- `${DATA_ROOT}/uploads/` with a `README.md` explaining what to upload and how (mirror the README in the repo's `data/uploads/`).
- `data/uploads/templates/`: one CSV template per canonical table, with a header row and 2–3 example rows.
- `data/uploads/schema.yaml`: columns, types, units, required or optional, allowed values, time zone (Asia/Kuala_Lumpur, ISO 8601).
- `column_map.yaml` per uploaded dataset, so files with different column names can be mapped without code.
- **Two ways to upload:**
  1. Drop files into `${DATA_ROOT}/uploads/<dataset_name>/`, then run `make ingest DATASET=<dataset_name>`.
  2. An admin-only **Data manager** page in the web app (`POST /admin/datasets`): upload CSV or Parquet, pick the target table, validate, preview, then activate.
- **Validation report** (HTML and JSON) checking:
  - missing columns, types and units
  - plausible kWh and voltage ranges
  - at least 90% of intervals present per meter-day (SRS 5.3)
  - duplicates and time-zone problems
  - every meter linked to exactly one transformer
  - Rejects for blocking errors, warnings otherwise.
- Every uploaded dataset is versioned. `config/data_sources.yaml` selects the active source per table: `simulated`, `london`, `sgcc`, `datagovmy` or `upload:<dataset_name>`. Switching sources is a config change plus `make pipeline`.
- If a new dataset lacks a field (e.g. voltage or phase), the pipeline uses the SDD fallbacks (AS-2, AS-3, AS-7, AS-8) and marks affected results low confidence. It never crashes.

## 4. Build order (milestones)

Build in this order; Must items in each milestone come first.

1. **Scaffold:** `git init`; repo layout; lite Compose profile (section 7.2) plus an optional `full` profile; `Makefile` and `make.ps1`; `.env.example` with every variable in section 7.3; CI-style `make test`.
2. **Data layer:** section 3 in full (schema, adapters, simulator, upload area, validation, Data manager page). Covers FR-DI-01–07.
3. **Detection engine:** SDD section 5.
   - Engineering loss model and zone balance with the uncertainty margin u = √(u_conv² + u_meter² + u_loss²) (FR-ZD-01–06)
   - Voltage locator relative to the transformer, within phase and branch; residual signal only when network parameters exist (AS-8), otherwise change signal only (FR-PS-02)
   - Premise features and legitimate-use tags, which subtract a penalty and show as negative reasons (FR-PS-03–05, 09)
   - Rooftop-solar check (FR-PS-10, SDD 5.3): solar registration from `account_event`, daytime-only drop vs. night-time use, and correlation with daily sunshine when a public weather series is loaded. A solar-explained drop is tagged; a night-time drop still counts.
   - Additive R0 score, clipped to 0–100, with exact reasons (top three plus "other", adding up to the score; when clipping applies, a "capped" line shows the difference); SGCC-trained XGBoost and an autoencoder as two of the inputs; SHAP sub-reasons (FR-PS-01, 06–08)
   - `POST /jobs/run-detection` runs ingest to scoring and creates **no** cases.
4. **API and security:** SDD section 7 endpoints.
   - Sign-in with one test account per role across two regions; PostgreSQL row-level security by region
   - Masking rules from SRS 2.2 and FR-UI-03
   - Hash-chained audit log, with the latest hash copied daily to `${DATA_ROOT}/audit_anchor/` outside the database (NFR-12)
   - File storage for photos and PDFs under `${DATA_ROOT}`
5. **Cases and apps:**
   - Separate case job `POST /jobs/create-cases`: threshold cases, plus a random sample drawn uniformly from **all premises in flagged zones**, regardless of score and excluding premises with an open case (FR-IW-05). Label these "routine meter check" in the inspector app.
   - Manual cases; analyst claim (`POST /cases/{id}/claim`), which runs alongside the dispatch suggestion, not before it; supervisor-only assignment
   - The user who created or claimed a case cannot approve its export; content and export approvers must differ
   - Statuses New → Assigned → Visited → Reporting → Closed; No access returns the case to Assigned and is not a training label (FR-IW-01–05)
   - Case pages web app (zone, premise and case views)
   - Inspector PWA: offline, encrypted local storage, auto-wipe, remote sign-out (NFR-16). It needs HTTPS, which the tunnel provides.
6. **Agents and RAG:** SDD section 8.
   - Report generator triggered by a Confirmed theft outcome: placeholders, analyst content approval, manager export approval (different person), PDF via an HTML template and Playwright (FR-AG-01, FR-UI-05)
   - Dispatch with scheduled reminders and escalation on shortened demo timers; Telegram bot, with a console notifier fallback when no token is set (FR-AG-02)
   - Analyst chatbot through the region-limited query service (FR-AG-03)
   - Field assistant RAG over public documents in `data/docs_rag/`, with citations or "not found" (FR-AG-04)
   - Similar-case finder over redacted notes (FR-AG-05)
   - Notes scrubber, writing `notes_redacted`. Presidio's name detection is built for English and misses Malaysian names, so add custom recognisers for:
     - IC numbers with or without dashes: `\b\d{6}-?\d{2}-?\d{4}\b`
     - Malaysian phone numbers (e.g. `01x-xxx xxxx`, `+60…`)
     - Names after honorifics (Encik, En., Puan, Pn., Cik, Tuan, Haji, Hajah, Datuk, Dato', Datin, Tan Sri, Dr.) and names around `bin`, `binti`, `bte`, `a/l`, `a/p`
     - Addresses: `No.`, `Lot`, `Jalan`/`Jln`, `Lorong`, `Taman`/`Tmn`, `Kampung`/`Kg`, `Persiaran`, `Bandar`, 5-digit postcodes
     - A test asserts that every planted detail in the synthetic notes is removed.
   - Guardrails: tool allow-lists, a personal-details output check, injection-resistant handling of retrieved text (FR-AG-06, NFR-15)
   - Models: section 7.3
7. **Learning and monitoring:** retrain on demand with recorded model versions (MLflow file store under `${DATA_ROOT}/mlruns` in the lite profile); model-ranked vs. random-sample hit rates (FR-ML-01–02); data-quality and drift alerts (FR-ML-03); admin settings for thresholds and weights (FR-AD-03).
8. **Dashboards:** create the zone-level pseudonymised `rpt_` views (no premise IDs or locations) and one read-only database role for Power BI. Write `powerbi/POWERBI.md` with a page-by-page layout (network overview, leaking zones, case counts) and how to connect Power BI Desktop. Also export a CSV snapshot of the views, so the team can build the `.pbix` by hand.
9. **Tests, deployment and demo:**
   - Unit and integration tests
   - `reports/simulation_report.md`: held-out NFR-09 results and every stress test in SDD 10.3. Start it with a one-table summary that the team copies into the pitch deck's results slide:
     - share of injected thefts in the top 5% on held-out settings
     - inspections needed per theft found (model ranking vs. random order)
     - whether the day-one tap and the partial bypass were flagged
     - whether EV, rooftop solar, metered mining or tenancy-change-only homes reached the top suspects
     - pattern model AUC on a held-out SGCC split (secondary)
     - where detection breaks in the stress tests (smallest tap found, noise level, share of monthly-read meters)
     Report failures as they are; never tune on held-out settings.
   - `scripts/backtest.py` (for the R1 back-test): runs the pipeline day by day over a past period and reports where known confirmed cases ranked. Demonstrate it on simulated history with ground truth.
   - Agent safety tests (SDD 10.1), including a planted "send the customer's address" note
   - Deployment per section 7, with `make tunnel`
   - `make demo`: fresh setup, seed, detection run, and printed step-by-step instructions with test accounts for the 7 live steps
   - `DEMO.md`: the full live and backup script from SDD 10.5, plus the rehearsal checklist in section 7.5

## 5. Defaults to use (configurable)

These come from the SDD and are placeholders to tune in simulation. Keep them in `config/thresholds.yaml`, never hard-coded:

- Flag a zone when the gap exceeds max(5% of supply, minimum kWh/day) plus the uncertainty margin u, for 7 days; above 15% marks large-load priority
- Flatness: coefficient of variation < 0.2
- Tenancy-change signal weight capped (FR-PS-09)
- Reminder after 24 h and escalation after 72 h (shortened timers in demo mode)
- Random-sample share of inspections: configurable, default small

## 6. Final deliverables

- Working repo with `README.md` (setup on Windows, D: storage, data modes, upload guide, tunnel, demo), `PLAN.md`, `TRACEABILITY.md`, `DEVIATIONS.md`, `DEMO.md`
- The upload area with templates, schema, README and Data manager page
- `reports/simulation_report.md` and test results
- `powerbi/POWERBI.md` plus the CSV snapshot
- A short summary listing what works, what does not, and the open issues from SDD 11.2 that still need TNB input (voltage data, baseline hit rate, phase data, loss-model parameters)

## 7. Machine, storage, models and deployment

### 7.1 Target machine

- A team member's Windows 10/11 laptop with Docker Desktop (WSL 2 backend), no GPU, at least 16 GB RAM recommended (8 GB works with the small model or mock mode).
- **All storage goes on the D: drive.** Nothing large is written to C:.
- **Memory:** WSL 2 gets only about half the laptop's RAM by default, which is tight for Postgres, the API and a 7B model. The README tells the team to create `%UserProfile%\.wslconfig`, then run `wsl --shutdown` and restart Docker Desktop:

  ```
  [wsl2]
  memory=12GB   # on a 16 GB laptop; leave ~4 GB for Windows
  swap=8GB
  ```

  With 8 GB RAM, use the small model or mock mode.

### 7.2 Compose profiles

| Profile | Services | Use |
| --- | --- | --- |
| `lite` (default) | `db` (PostgreSQL 16 + TimescaleDB + pgvector), `api` (FastAPI with APScheduler for jobs, reminders and the daily audit anchor), `web` (React case pages, inspector PWA, Data manager), `ollama`, `proxy` (one entry point for web and API, e.g. Caddy or nginx) | Development, demo, judging |
| `full` (optional) | lite plus Airflow, Keycloak, MinIO, Celery + Redis, MLflow server, Prometheus + Grafana | Showing the R1 architecture if the laptop can carry it |

Lite-profile swaps, each behind the same interface and logged in `DEVIATIONS.md`: APScheduler and a CLI runner instead of Airflow and Celery; local files under `${DATA_ROOT}` instead of MinIO; built-in sign-in with the same roles and regions instead of Keycloak; MLflow file store instead of an MLflow server; `/metrics` endpoint plus logs instead of Prometheus/Grafana.

### 7.3 Storage and model variables (`.env.example`)

```
DATA_ROOT=D:/VoltGuard              # datasets, uploads, photos, PDFs, logs, audit anchor, mlruns
OLLAMA_MODELS=D:/VoltGuard/models/ollama
HF_HOME=D:/VoltGuard/models/hf      # embedding model cache
LLM_MODE=ollama                     # or: mock (deterministic templates, no model needed)
LLM_MODEL=qwen2.5:7b-instruct       # ~7B open-weight instruct model, Apache 2.0
LLM_FALLBACK_MODEL=phi3.5           # smaller model for low-memory machines, MIT
REPORT_MODE=predrafted              # or: mock, live (live = slow on a laptop CPU)
EMBED_MODEL=intfloat/multilingual-e5-small   # MIT; English and Bahasa Melayu
TELEGRAM_BOT_TOKEN=                 # empty = console notifier
PUBLIC_BASE_URL=                    # set to the tunnel address for case links
```

- Bind-mount `${DATA_ROOT}` subfolders into the containers. Keep PostgreSQL on a **named Docker volume** (bind-mounting Postgres data from a Windows drive is slow and can break permissions).
- In `README.md`, tell the team to move Docker Desktop's disk image to D: (Docker Desktop → Settings → Resources → Advanced → Disk image location) so the database volume and images also live on D:.
- `make models` pulls the language and embedding models into the D: paths. Record each model's licence in `MODELS.md`.
- If the model is slow or missing, the app falls back to mock mode with a visible "mock" badge rather than failing.
- multilingual-e5 expects prefixes: embed documents as `passage: <text>` and questions as `query: <text>`, or retrieval quality drops.
- A 4-bit 7B model on a laptop CPU writes only a few words a second, so a full report draft can take minutes. Report drafting uses `REPORT_MODE=predrafted` (a stored draft for the demo case, built by the real model during setup) or mock by default; `REPORT_MODE=live` is optional.

### 7.4 Public link with Cloudflare Tunnel

Judges reach the laptop through Cloudflare Tunnel, which needs no open router ports and gives HTTPS (required for the inspector PWA).

- **Quick tunnel (testing):** `make tunnel` runs `cloudflared tunnel --url http://localhost:8080` against the `proxy` service. No Cloudflare account is needed. The address is random and changes every run; quick tunnels have no uptime guarantee, cap at 200 in-flight requests, and **do not support server-sent events**, so use polling or WebSockets for live updates.
- **Named tunnel (judging):** if the team has a domain on Cloudflare, `make tunnel-named` uses a named tunnel with a stable hostname (config in `deploy/cloudflared/config.yml`, credentials kept out of git). Use this for judging.
- **If only a quick tunnel is possible:** start it once on demo day and never restart it. A new address breaks the phone app's saved sign-in and offline cases (they belong to the old origin) and every Telegram link already sent. `make tunnel` writes the current address to `PUBLIC_BASE_URL` and prints a warning if one was already running.
- **Exposure rules:**
  - Expose only the `proxy` service; never the database, Ollama or admin ports.
  - The public build holds simulated data and fake personal details only.
  - Test accounts use strong generated passwords, printed by `make demo` and stored in `.env`, never committed.
  - Document optional Cloudflare Access (allow-list of judges' emails) in `README.md`.
  - Set `PUBLIC_BASE_URL` to the tunnel address so Telegram case links work.
- The laptop must stay on, plugged in, with sleep disabled, during judging. Write this into `DEMO.md`.

### 7.5 Demo rehearsal

- Rehearse the 7 live steps of SDD 10.5 in 5 minutes on the laptop, once with `LLM_MODE=ollama` and once with `LLM_MODE=mock`; keep mock as the fallback.
- Pre-seed and pre-warm: run detection once before the demo, load the model, and open the main pages, so nothing is cold.
- Run one heavy job at a time (detection, retrain or model loading); show the job status instead of running jobs in parallel.
- Step 6 (report) uses the pre-drafted report or mock mode by default; switch to the live model only if time allows.
- Demo step order: run detection (no cases yet) → ranked suspects → top premise (reasons plus "other", masked details) → run the case job; dispatch suggestion while the analyst claims the case → inspector outcome on a phone through the tunnel link → report draft and two approvals → retrain.

Start by reading both documents, then write `PLAN.md`.
