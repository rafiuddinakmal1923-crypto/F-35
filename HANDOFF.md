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

## Known issues

- NFR-09 holds for ranked zones (18/18) but not overall (18/24): partial bypasses of about 1% of
  supply in zones with no other theft stay inside the uncertainty margin u, so no flag threshold
  makes them visible (`reports/simulation_report.md`, sweep section). Narrowing u needs TNB inputs.
- Fixed this session: metered mining no longer reaches the held-out top 5% (re-tuned weights);
  the sweep now varies both parts of the flag rule.
- Not exercised here: a live Ollama model, live Telegram, Cloudflare tunnels, the full profile.

## Ideas for a next session

- Measure NFR-01 at 100,000 simulated meters (zone-by-zone processing is in place).
- Wire the full profile (Keycloak OIDC, MinIO, Celery) behind the existing interfaces.
- Try narrowing u (e.g. per-zone loss-model calibration) and re-run the held-out report.

<!-- auto:start -->
## Auto-generated state (scripts/handoff.sh)

- Generated: 2026-10-27T08:52
- Branch: `claude/practical-clarke-t5uwrc`; last commit: `0d4b295 Verify the compose stack on TimescaleDB and pgvector; fix empty settings and local paths`
- Tests collected: 74 tests
- Requirement coverage: see `TRACEABILITY.md`
- Code graph: `graphify-out/GRAPH_REPORT.md` (open `graphify-out/graph.html` in a browser;
  query with `graphify query "<question>"` or `graphify explain "<name>"`)

### Graph summary

- 1897 nodes · 4390 edges · 126 communities (113 shown, 13 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 252 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

Most connected (core abstractions):
1. `Caller` - 102 edges
2. `Requirements` - 62 edges
3. `login()` - 37 edges
4. `audit()` - 35 edges
5. `t()` - 33 edges
6. `admin_connection()` - 30 edges
7. `simulate_zone()` - 28 edges
8. `run_detection()` - 28 edges
9. `command()` - 27 edges
10. `ingest()` - 27 edges

### File tree

- `./`: .dockerignore, .env.example, .gitignore, DEMO.md, DEVIATIONS.md, HANDOFF.md, MODELS.md, Makefile, PLAN.md, README.md, TRACEABILITY.md, VoltGuard AI Software Design Document (SDD).pdf, ... (+6)
- `backend/`: Dockerfile, pytest.ini, requirements.txt
- `backend/tests/`: conftest.py, local_stack.py, pg_server.py, test_agents.py, test_api_security.py, test_cases.py, test_data_layer.py, test_detection.py, test_learning.py, test_reporting.py
- `backend/tests/e2e/`: __init__.py, test_demo_rehearsal.py, test_web_flow.py
- `backend/voltguard/`: __init__.py, __main__.py, audit.py, auth.py, cli.py, config.py, db.py, evaluation.py, network.py, pdf.py, storage.py
- `backend/voltguard/agents/`: __init__.py, chatbot.py, dispatch.py, embed.py, guardrails.py, llm.py, rag.py, report.py, scrubber.py
- `backend/voltguard/api/`: __init__.py, deps.py, main.py, routes_admin.py, routes_agents.py, routes_auth.py, routes_cases.py, routes_models.py, routes_zones.py
- `backend/voltguard/data/`: __init__.py, adapters/__init__.py, adapters/datagovmy.py, adapters/london.py, adapters/sgcc.py, canonical.py, fakes.py, ingest.py, profiles.py, simulator.py, sources.py, validation.py
- `backend/voltguard/detection/`: __init__.py, anomaly.py, balance.py, engine.py, features.py, pattern.py, scoring.py, voltage.py, zone_input.py
- `backend/voltguard/service/`: __init__.py, cases.py, commands.py, demo.py, jobs.py, learning.py, monitoring.py, notify.py, pipeline.py, scheduler.py, seed.py, settings.py, ... (+1)
- `backend/voltguard/sql/`: 001_core.sql, 002_security.sql, 003_cases.sql, 004_reporting.sql
- `config/`: data_sources.yaml, demo.yaml, thresholds.yaml, tuned_weights.yaml
- `data/docs_rag/`: README.md, field_evidence_checklist.md, report_template.md, sources.yaml, voltguard_guide.md
- `data/uploads/`: README.md, column_map.example.yaml, schema.yaml
- `data/uploads/templates/`: account_event.csv, customer_pii.csv, district_weather.csv, duty_roster.csv, inspection_outcome.csv, meter.csv, meter_monthly_reading.csv, meter_reading.csv, premise.csv, transformer.csv, transformer_reading.csv
- `deploy/airflow/dags/`: voltguard_nightly.py
- `deploy/caddy/`: Caddyfile
- `deploy/cloudflared/`: config.example.yml
- `deploy/prometheus/`: prometheus.yml
- `powerbi/`: POWERBI.md
- `powerbi/snapshot/`: rpt_case_counts.csv, rpt_flag_rates.csv, rpt_network_kpis.csv, rpt_outcomes.csv, rpt_zone_daily.csv, rpt_zone_latest.csv
- `reports/`: backtest_report.md, simulation_report.md
- `scripts/`: backtest.py, fetch_datasets.py, fetch_docs.py, handoff.sh, setup_env.py, traceability.py, tunnel.sh
- `web/`: .dockerignore, .gitignore, Dockerfile, index.html, nginx.conf, package-lock.json, package.json, vite.config.js
- `web/public/`: icon.svg, manifest.webmanifest, sw.js
- `web/src/`: App.jsx, api.js, i18n.js, main.jsx, styles.css
- `web/src/components/`: Charts.jsx, Common.jsx, ZoneMap.jsx
- `web/src/field/`: FieldApp.jsx, secureStore.js
- `web/src/pages/`: Assistant.jsx, Audit.jsx, Case.jsx, Cases.jsx, DataManager.jsx, Login.jsx, Models.jsx, Overview.jsx, Premise.jsx, Settings.jsx, Zone.jsx, extra.js
<!-- auto:end -->
