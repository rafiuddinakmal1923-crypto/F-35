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
- [ ] **M2 Data layer remainder**: adapters (London, SGCC, data.gov.my), `scripts/fetch_datasets.py`,
  upload area (`data/uploads/` README, templates, `schema.yaml`), `column_map.yaml`,
  validation report (HTML + JSON), dataset versions, `make ingest`.
- [ ] **M4 API and security**: Postgres schema + RLS, pipeline into the database, FastAPI
  endpoints (SDD 7), built-in sign-in, masking, hash-chained audit + daily anchor, file storage.
- [ ] **M5 Cases and apps**: case job + random sample, claim, assignment, outcomes, React case
  pages, Data manager page, inspector PWA (offline, encrypted, auto-wipe, remote sign-out).
- [ ] **M6 Agents and RAG**: report (placeholders, two approvals, PDF), dispatch + reminders,
  chatbot, field assistant, similar cases, notes scrubber, guardrails, safety tests.
- [ ] **M7 Learning and monitoring**: retrain with versions and both hit rates, alerts, settings.
- [ ] **M8 Dashboards**: `rpt_` views, Power BI role, `powerbi/POWERBI.md`, CSV snapshot.
- [ ] **M9 Demo**: `make demo`, `DEMO.md`, `scripts/backtest.py`, final simulation report, summary.

## Decisions to keep

- Tuned weights live in `config/tuned_weights.yaml` (committed). The first session kept them
  under `DATA_ROOT` and lost them; `python -m voltguard tune` regenerates them from the tuning
  split only.
- Models (`DATA_ROOT/models`) are not committed; `python -m voltguard train-models` rebuilds
  them in under a minute.
- Library swaps are listed in `DEVIATIONS.md`; add every new one there.

## Known issues (from the review at the start of this session)

- NFR-09 is not met: partial bypasses below ~1.5% of supply in zones with no other theft do
  not flag their zone (reported honestly in `reports/simulation_report.md`).
- Metered mining reached the top 5% in one held-out zone.
- The threshold sweep in the report only varies the supply share; the 15 kWh/day minimum
  hides the effect. The report must also sweep the minimum (OI-7).

<!-- auto:start -->
## Auto-generated state (scripts/handoff.sh)

- Generated: 2026-10-27T07:15
- Branch: `claude/practical-clarke-t5uwrc`; last commit: `8b0000a Add VoltGuard R0 core: simulator, detection engine, tuning and simulation report`
- Tests collected: 25 tests
- Requirement coverage: see `TRACEABILITY.md`
- Code graph: `graphify-out/GRAPH_REPORT.md` (open `graphify-out/graph.html` in a browser;
  query with `graphify query "<question>"` or `graphify explain "<name>"`)

### Graph summary

- 679 nodes · 1201 edges · 46 communities (42 shown, 4 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 90 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

Most connected (core abstractions):
1. `simulate_zone()` - 27 edges
2. `ZoneInput` - 26 edges
3. `Requirements` - 25 edges
4. `build_features()` - 24 edges
5. `locate()` - 19 edges
6. `simulation_report()` - 19 edges
7. `run_zones()` - 18 edges
8. `Scenario` - 17 edges
9. `services` - 16 edges
10. `simulate()` - 14 edges

### File tree

- `./`: .env.example, .gitignore, DEVIATIONS.md, HANDOFF.md, Makefile, PLAN.md, README.md, TRACEABILITY.md, VoltGuard AI Software Design Document (SDD).pdf, VoltGuard AI Software Requirements Specification (SRS).pdf, VoltGuard_ClaudeCode_Prompt.md, VoltGuard_SDD.md, ... (+3)
- `backend/`: Dockerfile, pytest.ini, requirements.txt
- `backend/tests/`: conftest.py, test_detection.py
- `backend/voltguard/`: __init__.py, __main__.py, cli.py, config.py, evaluation.py, network.py
- `backend/voltguard/data/`: __init__.py, canonical.py, fakes.py, profiles.py, simulator.py
- `backend/voltguard/detection/`: __init__.py, anomaly.py, balance.py, engine.py, features.py, pattern.py, scoring.py, voltage.py, zone_input.py
- `config/`: data_sources.yaml, demo.yaml, thresholds.yaml, tuned_weights.yaml
- `deploy/airflow/dags/`: voltguard_nightly.py
- `deploy/caddy/`: Caddyfile
- `deploy/cloudflared/`: config.example.yml
- `deploy/prometheus/`: prometheus.yml
- `reports/`: simulation_report.md
- `scripts/`: handoff.sh, setup_env.py, traceability.py, tunnel.sh
<!-- auto:end -->
