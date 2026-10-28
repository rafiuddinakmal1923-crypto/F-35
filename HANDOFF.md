# Hand-off: VoltGuard AI R0 build

Read this first when you continue the build in a new session. It is updated after every
finished part (`make.ps1 handoff` or `bash scripts/handoff.sh` refreshes the auto part, the
graphify graph in `graphify-out/` and `TRACEABILITY.md`).

## How to resume in a new session

1. Read `VoltGuard_ClaudeCode_Prompt.md` (build brief; its sections 3 and 7 override the
   documents), then `VoltGuard_SRS.md` and `VoltGuard_SDD.md`. The PDFs hold the same text.
2. Read this file, `PLAN.md`, `DEVIATIONS.md` and `TRACEABILITY.md`.
3. Skim `graphify-out/GRAPH_REPORT.md` for the code map (god nodes = core abstractions).
4. Set up and check that everything passes before changing anything:
   ```bash
   python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt graphifyy
   cd backend && ../.venv/bin/python -m voltguard train-models && ../.venv/bin/python -m pytest
   ```
   Database tests start a throwaway PostgreSQL from local binaries
   (`/usr/lib/postgresql/16/bin`) or use `TEST_DATABASE_URL`.
5. Continue with the first unchecked milestone below. Commit and push after each part,
   then run `bash scripts/handoff.sh` and commit `HANDOFF.md`, `TRACEABILITY.md` and
   `graphify-out/` (the cache folder is git-ignored).

## Status by milestone (PLAN.md)

- [x] **M3 Detection engine** (first session): simulator, load-flow model, zone balance with
  uncertainty, voltage locator, features and tags, additive score with exact reasons,
  pattern model (XGBoost), autoencoder, tuning, simulation report.
- [x] **M1 Scaffold** (this session): CLI (`python -m voltguard`), `Makefile`, `make.ps1`,
  `.env.example`, `docker-compose.yml` (lite default, full/tunnel profiles), Dockerfile,
  Caddy proxy, detection tests (25, named after SRS IDs), traceability generator, this hand-off.
- [x] **M2 Data layer**: adapters (`data/adapters/`: London, SGCC, data.gov.my, converted to
  Parquet once), `scripts/fetch_datasets.py` (never blocks), upload area (`data/uploads/`
  README, templates, `schema.yaml`, `column_map.example.yaml`), validation (`data/validation.py`,
  HTML + JSON reports), versions + activation (`data/ingest.py`, `data/sources.py`), CLI
  `ingest`, `activate`, `sources`, `convert`, `upload-kit`. Still to do in M4/M5: the
  `pipeline` command (needs the database), `POST /admin/datasets` and the Data manager page,
  both calling `ingest.ingest()` / `ingest.activate_dataset()` / `ingest.preview()`.
- [x] **M4 API and security**: `sql/001_core.sql` (SDD 4 tables, audit chain function
  `vg_audit`, personal details only via `vg_case_contact`/`vg_report_contact`),
  `sql/002_security.sql` (roles, column grants, row-level security by region; re-applied on
  every migrate), `db.py` (pools, `app_connection(caller)` sets `app.*`), `service/pipeline.py`
  (sources -> DB -> read back -> engine -> results), `service/jobs.py` (one heavy job at a time),
  `auth.py` (scrypt + JWT + remote sign-out), `audit.py` (independent verify + write-once anchors),
  `storage.py` (Fernet-encrypted files), `api/` (auth, zones, premises, jobs, Data manager,
  settings, audit), `agents/scrubber.py` (Malaysian recognisers; used by the pipeline already).
  Tests: `tests/test_api_security.py` on a throwaway Postgres (`tests/pg_server.py`).
- [x] **M5 Cases and apps**: `service/cases.py` (case job + random sample, manual cases, claim,
  supervisor-only assignment, outcomes with scrubbed notes, status rules), `agents/dispatch.py`
  (nearest on-duty team, joint operation, reminders/escalation on demo timers), `service/notify.py`
  (Telegram or console, case link only, output check), `api/routes_cases.py`, `sql/003_cases.sql`
  (sequences, `training_label` view). Web app in `web/` (React + Vite, hash routes): overview with
  map, zone, premise, cases, case, Data manager, settings, audit; inspector PWA at `#/field`
  (`web/src/field/`: AES-GCM store with a non-extractable key, offline queue, wipe after sync / 24 h /
  remote sign-out, service worker `web/public/sw.js`). Browser test: `pytest -m e2e`
  (`tests/e2e/test_web_flow.py`, uses `tests/local_stack.py`). Run the whole stack without Docker:
  `cd backend && ../.venv/bin/python -m tests.local_stack --cases` (web on :4173, password demo-pass-1).
  Fixed on the way: `vg_case_contact` leaked details on unclaimed cases (NULL comparison); a
  regression test now covers it.
- [x] **M6 Agents and RAG**: `agents/llm.py` (Ollama or mock; prompts checked for personal
  details), `agents/embed.py` (e5 via ONNX or hashing fallback), `agents/guardrails.py` (tool
  allow-lists, forbidden-action refusal, injection neutraliser, output check), `agents/rag.py`
  (approved docs in `data/docs_rag/` + fetched public texts + closed-case summaries; cited answers or
  "not found"; similar cases), `agents/report.py` + `pdf.py` (placeholders, analyst then manager
  approval, PDF via Playwright/fpdf2, case closes), `agents/chatbot.py` (whitelisted query templates,
  region refusal, POST /query), `service/seed.py` (20 closed cases with planted fake details, index,
  pre-drafted assessment), `api/routes_agents.py`, web Assistant page and field "Ask" box.
  Tests: `tests/test_agents.py` (agent safety, SDD 10.1). CLI: `seed`, `index-docs`, `fetch-models`.
- [x] **M7 Learning and monitoring**: `service/learning.py` (label model on outcomes, weighted
  for how cases were chosen; versions in `model_version` + MLflow file store; hit rate and
  precision for model-ranked vs random-sample), `service/monitoring.py` (data-quality, PSI drift,
  unusual-access alerts), `api/routes_models.py` (/models, /models/retrain, /alerts), web Models
  page; settings (FR-AD-03) were done in M4. Tests: `tests/test_learning.py`.
- [x] **M8 Dashboards**: `sql/004_reporting.sql` (six zone-level `rpt_` views; only
  `voltguard_powerbi` may read them), `snapshot` CLI, `powerbi/POWERBI.md` (page-by-page layout,
  connection), `powerbi/snapshot/*.csv` from the demo data. Tests: `tests/test_reporting.py`.
- [x] **M9 Demo**: `service/demo.py` (`demo` CLI: reset rehearsal cases, seed, detection, pre-warm,
  printed script and accounts; setup scripts generate DEMO_PASSWORDS), `DEMO.md` (live and backup
  steps, rehearsal checklist), `scripts/backtest.py` (+ `reports/backtest_report.md`), simulation
  report regenerated (sweep of both flag-rule parts), `README.md` status summary, `MODELS.md`,
  `.dockerignore`, API container migrates on start. Browser rehearsal of all 7 live steps:
  `tests/e2e/test_demo_rehearsal.py` (~20 s, mock mode). Docker images: see "Docker check" below.

## Decisions to keep

- Tuned weights live in `config/tuned_weights.yaml` (committed). The first session kept them
  under `DATA_ROOT` and lost them; `python -m voltguard tune` regenerates them from the tuning
  split only.
- Models (`DATA_ROOT/models`) are not committed; `python -m voltguard train-models` rebuilds
  them in under a minute.
- Library swaps are listed in `DEVIATIONS.md`; add every new one there.

## Docker check (this session)

- `web` image: built with the repository's own `web/Dockerfile`.
- `api` image: built from a sandbox copy of `backend/Dockerfile` that only adds this cloud
  session's proxy certificate; every requirement installed on Python 3.12. The sandbox network
  blocks the Chromium download for PDFs (Playwright) and the Debian mirrors, which a normal network
  allows; PDF export falls back to fpdf2 when no browser is present.
- `docker compose up db api web proxy` with the real `timescale/timescaledb-ha:pg16` image: the API
  migrated on start (TimescaleDB hypertables on both reading tables, pgvector `embedding` column),
  `python -m voltguard demo` ran in 16 s, the proxy routed `/api`, blocked `/api/metrics` and the
  API docs, served the web app and set the security headers, and a browser signed in on desktop
  and on the phone app through it. All 73 database tests also passed against that server.
- Not run here: Ollama (no model download), Cloudflare tunnels, the full profile.

## Review round (after the team's laptop test, 2026-10-27)

Full report: `docs/REVIEW_AND_TEST_REPORT.md`. Redesign brief: `docs/UI_UX_DESIGN_REQUIREMENTS.md`.

- **End-to-end run of every use case** (`scripts/e2e_use_cases.py`): it starts its own stack and
  drives 68 browser and API checks for every account. All pass. Your own passwords: `VG_PASSWORDS_FILE`
  (JSON kept outside the repository).
- **Telegram dispatch bot**: `service/telegram.py`, `api/routes_telegram.py`, `sql/005_telegram.sql`.
  - Buttons on dispatch messages: supervisor Approve / Reject; team Accept / On my way / Can't attend.
  - Chat linking with `/start CODE`, plus `/mycases`, `/whoami` and `/unlink`.
  - Long polling starts in the API when `TELEGRAM_BOT_TOKEN` is set.
  - The in-app simulator (`components/TelegramChat.jsx`) is on the Dispatch page (`pages/Dispatch.jsx`,
    which also has remote sign-out) and in the inspector Messages tab.
  - Tests: `tests/test_telegram.py`.
- **Assistant charts**: query templates carry a chart spec, and answers are sentences built from the rows.
  - New templates: zone and region gap trends, gap by district, outcomes.
  - The front end: `QueryChart` in `components/Charts.jsx`, and a chat-style `pages/Assistant.jsx`.
- **Fixed**:
  - voltage strip marked a tap on every line;
  - usage chart broke on monthly-read meters and started with a partial day;
  - "0 m from this premise" wording;
  - manager 403 on evidence photos;
  - no notification of pending dispatch suggestions;
  - top bar overflow on phones;
  - **an async photo-upload endpoint blocked the event loop and could deadlock the API on the audit
    lock** (now plain functions everywhere, with a guard test);
  - laptop setup: Debian 12 base image, `DB_HOST_PORT` and `WEB_PORT`, map tiles sending the origin.

## Laptop round (2026-10-28)

- **Ollama on the GPU**: `docker-compose.gpu.yml`, added automatically by `make.ps1`/`Makefile` when
  `nvidia-smi` exists (`VG_GPU=0` forces CPU); models in the `ollama_models` volume. Qwen2.5-7B answers in
  2–3 s, so `REPORT_MODE=live` fits the demo. The live report model gets finished figures with units
  (`report.live_facts`); the Assistant labels any valid model reply as live and cleans the model's parameters.
- **Weekly report upgrade** (`VoltGuard_Report_Upgrade_Prompt.md`): `service/digest.py` (figures) +
  `service/digest_render.py` (rules, charts, HTML, PDF, EN/BM), `/weekly/html?lang=`, PDF on Telegram after an
  output check, schedule in Settings (`weekly.*`), tariff in `config/tariffs.yaml`. Before/after in
  `reports/ui/` with `CHANGES.md`.
- **Fixed**: `training_label` ran as its owner, so hit rates counted every region (now `security_invoker`).
- Windows: database tests run against a throwaway `timescale/timescaledb-ha:pg16` container via
  `TEST_DATABASE_URL` (126 pass).
- Not done: the UI upgrade brief (`VoltGuard_UI_Upgrade_Prompt.md`).

## Known issues

- NFR-09 holds for ranked zones (18/18) but not overall (18/24): partial bypasses of about 1% of
  supply in zones with no other theft stay inside the uncertainty margin u, so no flag threshold
  makes them visible (`reports/simulation_report.md`, sweep section). Narrowing u needs TNB inputs.
- Fixed this session: metered mining no longer reaches the held-out top 5% (re-tuned weights);
  the sweep now varies both parts of the flag rule.
- Not exercised here: a live Ollama model, a real Telegram bot token (the bot path is tested with a
  recorded Telegram API), Cloudflare tunnels, the full profile.

## Ideas for a next session

- NFR-01: the nightly run now streams readings in meter batches and detects in zone batches.
  It has been measured up to 13,088 homes (3.1 GB, 219 s, nearly flat memory). Still to do: load only
  the new day each night once real AMI extracts arrive daily (today every source is reloaded in full).
- UI redesign per `docs/UI_UX_DESIGN_REQUIREMENTS.md` (prompts in section 8).
- Wire the full profile (Keycloak OIDC, MinIO, Celery) behind the existing interfaces.
- Try narrowing u (e.g. per-zone loss-model calibration) and re-run the held-out report.

<!-- auto:start -->
## Auto-generated state (scripts/handoff.py)

- Generated: 2026-10-28T12:40
- Branch: `claude/ui-upgrade`; last commit: `e8d30d3 UI upgrade: design system, redesigned pages and new pages (checkpoint)`
- Tests collected: 136 tests
- Requirement coverage: see `TRACEABILITY.md`
- Code graph: `graphify-out/GRAPH_REPORT.md` (open `graphify-out/graph.html` in a browser;
  query with `graphify query "<question>"` or `graphify explain "<name>"`)

### Graph summary

- 2562 nodes · 5669 edges · 147 communities (139 shown, 8 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 180 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

Most connected (core abstractions):
1. `Caller` - 141 edges
2. `t()` - 97 edges
3. `login()` - 66 edges
4. `audit()` - 45 edges
5. `get()` - 42 edges
6. `admin_connection()` - 41 edges
7. `useLoad()` - 33 edges
8. `shot()` - 32 edges
9. `request()` - 30 edges
10. `run_detection()` - 29 edges

### File tree

- `./`: .dockerignore, .env.example, .gitignore, DEMO.md, DEVIATIONS.md, HANDOFF.md, HOW_TO_RUN.md, MODELS.md, Makefile, PLAN.md, README.md, TRACEABILITY.md, ... (+13)
- `backend/`: Dockerfile, pytest.ini, requirements.txt
- `backend/tests/`: conftest.py, local_stack.py, pg_server.py, test_agents.py, test_api_security.py, test_cases.py, test_data_layer.py, test_detection.py, test_digest.py, test_digest_render.py, test_learning.py, test_pipeline_batches.py, ... (+5)
- `backend/tests/e2e/`: __init__.py, test_demo_rehearsal.py, test_web_flow.py
- `backend/voltguard/`: __init__.py, __main__.py, audit.py, auth.py, cli.py, config.py, db.py, evaluation.py, network.py, pdf.py, storage.py
- `backend/voltguard/agents/`: __init__.py, chatbot.py, dispatch.py, embed.py, guardrails.py, llm.py, rag.py, report.py, route.py, scrubber.py
- `backend/voltguard/api/`: __init__.py, deps.py, main.py, routes_admin.py, routes_agents.py, routes_auth.py, routes_cases.py, routes_models.py, routes_telegram.py, routes_ui.py, routes_zones.py
- `backend/voltguard/data/`: __init__.py, adapters/__init__.py, adapters/datagovmy.py, adapters/london.py, adapters/sgcc.py, canonical.py, fakes.py, ingest.py, profiles.py, simulator.py, sources.py, validation.py
- `backend/voltguard/detection/`: __init__.py, anomaly.py, balance.py, engine.py, features.py, pattern.py, scoring.py, voltage.py, zone_input.py
- `backend/voltguard/service/`: __init__.py, cases.py, commands.py, data_health.py, demo.py, demo_guide.py, digest.py, digest_render.py, explain.py, jobs.py, learning.py, monitoring.py, ... (+9)
- `backend/voltguard/sql/`: 001_core.sql, 002_security.sql, 003_cases.sql, 004_reporting.sql, 005_telegram.sql
- `config/`: data_sources.yaml, demo.yaml, tariffs.yaml, thresholds.yaml, tuned_weights.yaml
- `data/docs_rag/`: README.md, field_evidence_checklist.md, report_template.md, sources.yaml, voltguard_guide.md
- `data/uploads/`: README.md, column_map.example.yaml, schema.yaml
- `data/uploads/templates/`: account_event.csv, customer_pii.csv, district_weather.csv, duty_roster.csv, inspection_outcome.csv, meter.csv, meter_monthly_reading.csv, meter_reading.csv, premise.csv, transformer.csv, transformer_reading.csv
- `deploy/airflow/dags/`: voltguard_nightly.py
- `deploy/caddy/`: Caddyfile
- `deploy/cloudflared/`: config.example.yml
- `deploy/prometheus/`: prometheus.yml
- `docs/`: REVIEW_AND_TEST_REPORT.md, UI_UX_DESIGN_REQUIREMENTS.md
- `powerbi/`: BUILD_WITH_CLAUDE_ON_LAPTOP.md, POWERBI.md, measures.dax, voltguard_theme.json
- `powerbi/snapshot/`: rpt_case_counts.csv, rpt_flag_rates.csv, rpt_network_kpis.csv, rpt_outcomes.csv, rpt_zone_daily.csv, rpt_zone_latest.csv
- `reports/`: backtest_replay.json, backtest_report.md, simulation_report.md, simulation_summary.json
- `reports/ui/`: CHANGES.md, PLAN.md, weekly_report_after.html, weekly_report_after.pdf, weekly_report_after_ms.html, weekly_report_after_ms.pdf, weekly_report_before.html, weekly_report_before.pdf
- `reports/ui/before/`: assistant_desktop.png, assistant_phone.png, audit_desktop.png, audit_phone.png, case_desktop.png, case_phone.png, cases_desktop.png, cases_phone.png, data_manager_desktop.png, data_manager_phone.png, dispatch_desktop.png, dispatch_phone.png, ... (+18)
- `scripts/`: backtest.py, e2e_use_cases.py, fetch_datasets.py, fetch_docs.py, handoff.py, handoff.sh, setup_env.py, traceability.py, tunnel.sh, ui_screenshots.py
- `web/`: .dockerignore, .gitignore, Dockerfile, index.html, nginx.conf, package-lock.json, package.json, vite.config.js
- `web/public/`: icon.svg, manifest.webmanifest, sw.js
- `web/src/`: App.jsx, api.js, i18n.js, main.jsx, styles.css, theme.js
- `web/src/components/`: BaseTiles.jsx, Charts.jsx, Common.jsx, DemoGuide.jsx, EvidenceTimeline.jsx, FeederSchematic.jsx, PremiseDetail.jsx, RouteMap.jsx, TelegramChat.jsx, Waterfall.jsx, WhyCleared.jsx, ZoneMap.jsx, ... (+1)
- `web/src/field/`: FieldApp.jsx, secureStore.js
- `web/src/lib/`: format.js, schematic.js, waterfall.js
- `web/src/pages/`: Assistant.jsx, Audit.jsx, Backtest.jsx, Case.jsx, Cases.jsx, DataManager.jsx, Dispatch.jsx, LandlordConcept.jsx, Login.jsx, Models.jsx, Overview.jsx, Premise.jsx, ... (+6)
- `web/tests/`: i18n.test.js, lib.test.js
<!-- auto:end -->
