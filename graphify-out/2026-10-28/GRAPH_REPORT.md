# Graph Report - wt-ui  (2026-10-28)

## Corpus Check
- 187 files · ~337,670 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2562 nodes · 5669 edges · 147 communities (139 shown, 8 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 180 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e8d30d3a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- pg_server.py
- get
- weights
- VoltGuard AI: Software Design Document (SDD)
- columns
- 3. Functional requirements
- config.py
- tables
- Build the VoltGuard AI prototype (R0)
- test_data_layer.py
- e2e_use_cases.py
- teams
- test_detection.py
- weights
- zone
- os
- Simulation report
- VoltGuard AI R0: build plan
- scrape_configs
- thresholds.yaml
- cases.py
- config.example.yml
- route.py
- local_stack.py
- dispatch
- features
- routes_admin.py
- make.ps1
- cases
- main.py
- voltage
- handoff.sh script
- tunnel.sh
- worker
- ingest.py
- db
- services
- keycloak
- minio
- airflow
- tunnel-named
- proxy
- settings.py
- mlflow
- columns
- prometheus
- columns
- meter_id
- premise_id
- tables
- columns
- routes_ui.py
- columns
- columns
- embed.py
- kwh
- kwh_supplied
- distance_m
- pipeline.py
- report.py
- api
- environment
- digest_render.py
- db.py
- App.jsx
- voltage_v
- engine.py
- conftest.py
- dependencies
- post
- t
- Caller
- Charts.jsx
- timedelta
- evaluation.py
- routes_cases.py
- anomaly.py
- sources.py
- guardrails.py
- test_cases.py
- pattern.py
- Build the Power BI dashboard with Claude on your laptop
- chatbot.py
- login
- ollama
- london.py
- routes_zones.py
- pathlib
- api.js
- secureStore.js
- build_zone_inputs
- VoltGuard AI R0: review and end-to-end test report
- ValidationReport
- simulator.py
- Zone.jsx
- VoltGuard AI: UI and UX design requirements (R0 → R1 redesign)
- Waterfall.jsx
- sunshine_hours
- How to run VoltGuard AI (and share it with a public link)
- test_telegram.py
- 3. New features
- test_agents.py
- sw.js
- i18n.js
- command
- rag.py
- Manager dashboard in Power BI (R0)
- answer
- Upload area: bring your own datasets
- llm.py
- test_ui_upgrade.py
- re
- documents
- voltguard_guide.md
- audit.py
- demo_guide.py
- field_evidence_checklist.md
- Documents for the field assistant and the report agent (RAG)
- routes_agents.py
- Deviations from the SDD
- json
- monitoring.py
- pipeline
- Traceability
- Hand-off: VoltGuard AI R0 build
- VoltGuard AI demo script (R0)
- MODELS.md
- backtest_report.md
- handoff.py
- tunnel-token
- psycopg
- learning.py
- ui_screenshots.py
- test_digest.py
- seed.py
- digest.py
- demo.py
- route
- VoltGuard R0: finish the rooftop-solar handling (FR-PS-10) and show it
- VoltGuard R0: make the weekly summary report self-explanatory
- agents/__init__.py
- Weekly summary report: before and after
- canonical.py
- UI upgrade plan (`VoltGuard_UI_Upgrade_Prompt.md`)
- vite.config.js

## God Nodes (most connected - your core abstractions)
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

## Surprising Connections (you probably didn't know these)
- `require()` --indirect_call--> `check()`  [INFERRED]
  backend/voltguard/api/deps.py → scripts/e2e_use_cases.py
- `create_cases()` --indirect_call--> `run()`  [INFERRED]
  backend/voltguard/api/routes_cases.py → scripts/handoff.py
- `status()` --calls--> `check()`  [INFERRED]
  backend/voltguard/service/demo_guide.py → scripts/e2e_use_cases.py
- `_safe()` --indirect_call--> `run()`  [INFERRED]
  backend/voltguard/service/scheduler.py → scripts/handoff.py
- `pg()` --uses--> `TempPostgres`  [INFERRED]
  backend/tests/conftest.py → backend/tests/pg_server.py

## Import Cycles
- None detected.

## Communities (147 total, 8 thin omitted)

### Community 0 - "pg_server.py"
Cohesion: 0.14
Nodes (11): _bin(), ExternalPostgres, _free_port(), make_postgres(), A throwaway PostgreSQL for database tests. Uses TEST_DATABASE_URL (owner…, Throwaway database: on TEST_DATABASE_URL's server when set, else a local…, A fresh database on the server named by TEST_DATABASE_URL (Windows: a throwaway…, TempPostgres (+3 more)

### Community 1 - "get"
Cohesion: 0.12
Nodes (30): get(), put(), session(), ErrorBox(), useLoad(), PremiseDetail(), Panel(), Assistant() (+22 more)

### Community 2 - "weights"
Cohesion: 0.17
Nodes (12): weights, anomaly, change_from_history, flatness, gap_from_similar, night_to_day, pattern_model, tenancy_change (+4 more)

### Community 3 - "VoltGuard AI: Software Design Document (SDD)"
Cohesion: 0.05
Nodes (39): 10.1 Test levels, 10.2 Simulated zone, 10.3 Stress tests, 10.4 Acceptance criteria, 10.5 Prototype demo for judges, 10. Testing and validation plan, 11.1 Requirements to design, 11.2 Open issues (+31 more)

### Community 4 - "columns"
Cohesion: 0.07
Nodes (28): CABLE_M, ENERGY_KWH, INTERVAL_START, KWH_IMPORT, LV_BRANCH, METER_NO, PHASE, PREMISE_REF (+20 more)

### Community 5 - "3. Functional requirements"
Cohesion: 0.06
Nodes (31): 1.1 Purpose, 1.2 Scope, 1.3 Releases, 1.4 Definitions, 1.5 References, 1. Introduction, 2.1 Product perspective, 2.2 User classes (+23 more)

### Community 6 - "config.py"
Cohesion: 0.15
Nodes (24): test_sgcc_adapter_feeds_pattern_model(), admin_database_url(), config_dir(), data_root(), data_sources(), database_url(), deep_merge(), demo_config() (+16 more)

### Community 7 - "tables"
Cohesion: 0.08
Nodes (24): downloads, london, sgcc, london, households, region, zone_size, pattern_training (+16 more)

### Community 8 - "Build the VoltGuard AI prototype (R0)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "test_data_layer.py"
Cohesion: 0.13
Nodes (25): isolated(), DataFrame, fixture, Data layer: upload area, validation, versions, source switching and adapters…, Same simulated data as an upload: activation is a config change and detection…, Own DATA_ROOT and a copy of config/, so activation never touches the repository., small_scenario(), test_bad_upload_is_rejected_with_reasons() (+17 more)

### Community 10 - "e2e_use_cases.py"
Cohesion: 0.08
Nodes (51): playwright_sync_api, adm_data(), adm_settings(), adm_upload(), api(), ask(), bm(), check() (+43 more)

### Community 11 - "teams"
Cohesion: 0.12
Nodes (16): demo_seed, demo_zone, regions, code, name, teams, base_lat, base_lon (+8 more)

### Community 12 - "test_detection.py"
Cohesion: 0.11
Nodes (14): case_premise(), rank_of(), top_k(), Detection engine prototype tests (SRS 3.1-3.3, SDD 5) on simulated zones., POST /jobs/run-detection creates no cases: the engine returns scores only., test_detection_creates_no_cases(), test_FR_DI_05_tenancy_change_at_injected_thief(), test_FR_PS_02_voltage_locates_tap_on_its_phase() (+6 more)

### Community 13 - "weights"
Cohesion: 0.10
Nodes (20): _tuning, objective, seed, split, tuned_at, zones, weights, anomaly (+12 more)

### Community 14 - "zone"
Cohesion: 0.18
Nodes (11): zone, change_min_segment_days, change_min_shift_share, consecutive_days, conventional_daily_cv, flat_cv, large_load_share, loss_model_error_share (+3 more)

### Community 15 - "os"
Cohesion: 0.15
Nodes (14): airflow_operators_python, Full profile only: the nightly pipeline as an Airflow DAG (SDD 6.1). In the…, os, requests, apply_overrides(), fetch_kaggle(), fetch_url(), main() (+6 more)

### Community 16 - "Simulation report"
Cohesion: 0.22
Nodes (8): Demo zone TX-CEN-001, Flag threshold sweep (held-out settings, for OI-7), Held-out thefts, one by one, How to read this, Simulation report, Stress tests (SDD 10.3): where detection breaks, Summary (copy into the pitch deck), Where it breaks: noise and monthly-read meters

### Community 17 - "VoltGuard AI R0: build plan"
Cohesion: 0.33
Nodes (5): File tree, Key decisions (details in DEVIATIONS.md), Milestones, Open questions (do not block Must requirements), VoltGuard AI R0: build plan

### Community 18 - "scrape_configs"
Cohesion: 0.25
Nodes (7): global, scrape_interval, scrape_configs, job_name, metrics_path, static_configs, targets

### Community 19 - "thresholds.yaml"
Cohesion: 0.18
Nodes (10): monitoring, drift_psi_alert, min_interval_completeness, penalties, ev_charging, solar, vacancy, tenancy (+2 more)

### Community 20 - "cases.py"
Cohesion: 0.06
Nodes (69): engine(), _known_patterns(), _presidio_analyzer(), Notes scrubber (SDD 8.4, NFR-15): inspector notes -> notes_redacted before any…, presidio=False runs only the Malaysian recognisers (for templated text whose…, Presidio with an installed spaCy model (en_core_web_sm, else _lg); never…, scrub(), ScrubResult (+61 more)

### Community 21 - "config.example.yml"
Cohesion: 0.33
Nodes (5): credentials-file, ingress, hostname, service, tunnel

### Community 22 - "route.py"
Cohesion: 0.11
Nodes (28): test_FR_AG_02_reminder_then_escalation_on_demo_timers(), test_route_order_beats_nearest_neighbour_and_is_close_to_the_best(), haversine_km(), Connection, date, datetime, Dispatch and reminder agent (SDD 8.1, FR-AG-02). Tools allowed: read the case…, Today's shift if the roster covers it, else the latest shift on record… (+20 more)

### Community 23 - "local_stack.py"
Cohesion: 0.11
Nodes (23): atexit, fixture, Automated rehearsal of the 7 live demo steps (SDD 10.5, DEMO.md) in a real…, Zone and premise pages within 3 s (NFR-02); the inspector view on a phone…, run_job_and_wait(), sign_in(), stack(), test_demo_live_steps_1_to_7() (+15 more)

### Community 24 - "dispatch"
Cohesion: 0.40
Nodes (5): dispatch, demo_escalation_minutes, demo_reminder_minutes, escalation_hours, reminder_hours

### Community 25 - "features"
Cohesion: 0.40
Nodes (5): features, history_weeks, recent_days, timing_tau_days, zero_kwh

### Community 26 - "routes_admin.py"
Cohesion: 0.10
Nodes (31): bad_request(), audit_log(), audit_verify(), dataset_activate(), dataset_preview(), dataset_report(), datasets(), job_status() (+23 more)

### Community 27 - "make.ps1"
Cohesion: 0.38
Nodes (4): Invoke-Setup(), Invoke-Tunnel(), New-Secret(), Test-PublicLink()

### Community 28 - "cases"
Cohesion: 0.50
Nodes (4): cases, case_threshold, max_cases_per_zone, random_sample_per_zone

### Community 29 - "main.py"
Cohesion: 0.11
Nodes (20): apscheduler_schedulers_background, lifespan(), FastAPI application: the only way clients and agents reach the data (SDD 7).…, Job scheduler inside the API (lite profile for Celery + Redis; SDD 3 "Job…, Modules add their periodic jobs here (e.g. register('reminders', fn,…, register(), _safe(), start() (+12 more)

### Community 30 - "voltage"
Cohesion: 0.50
Nodes (4): voltage, min_drop_v, proximity_scale_m, window_days

### Community 33 - "worker"
Cohesion: 0.17
Nodes (13): build, context, dockerfile, web, worker, build, restart, build (+5 more)

### Community 34 - "ingest.py"
Cohesion: 0.17
Nodes (22): Content of data/uploads/schema.yaml., schema_document(), build_tables(), _checksum(), cmd_ingest(), cmd_upload_kit(), context_for(), ingest() (+14 more)

### Community 35 - "db"
Cohesion: 0.15
Nodes (13): environment, healthcheck, image, ports, restart, volumes, POSTGRES_DB, POSTGRES_PASSWORD (+5 more)

### Community 36 - "services"
Cohesion: 0.11
Nodes (17): image, profiles, name, image, profiles, services, grafana, redis (+9 more)

### Community 37 - "keycloak"
Cohesion: 0.25
Nodes (8): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_BOOTSTRAP_ADMIN_USERNAME, command, environment, image, profiles, volumes, keycloak

### Community 38 - "minio"
Cohesion: 0.25
Nodes (8): MINIO_ROOT_PASSWORD, MINIO_ROOT_USER, command, environment, image, profiles, volumes, minio

### Community 39 - "airflow"
Cohesion: 0.29
Nodes (7): command, environment, image, profiles, volumes, AIRFLOW__CORE__LOAD_EXAMPLES, airflow

### Community 40 - "tunnel-named"
Cohesion: 0.29
Nodes (7): tunnel-named, command, depends_on, image, profiles, restart, volumes

### Community 41 - "proxy"
Cohesion: 0.33
Nodes (6): depends_on, image, ports, restart, volumes, proxy

### Community 42 - "settings.py"
Cohesion: 0.24
Nodes (13): get_thresholds(), overrides(), Any, Connection, Thresholds and weights (FR-AD-03): config/thresholds.yaml, tuned weights, then…, Only known numeric settings may change; weights must stay between 0 and 1., save(), thresholds() (+5 more)

### Community 43 - "mlflow"
Cohesion: 0.40
Nodes (5): command, image, profiles, volumes, mlflow

### Community 44 - "columns"
Cohesion: 0.10
Nodes (20): max, min, required, type, max, min, required, type (+12 more)

### Community 45 - "prometheus"
Cohesion: 0.50
Nodes (4): image, profiles, volumes, prometheus

### Community 46 - "columns"
Cohesion: 0.10
Nodes (21): required, type, case_id, notes, origin, outcome, reason_tag, recorded_at (+13 more)

### Community 47 - "meter_id"
Cohesion: 0.11
Nodes (19): installed_on, meter_id, meter_type, read_frequency, required, type, columns, description (+11 more)

### Community 48 - "premise_id"
Cohesion: 0.12
Nodes (16): columns, event_date, event_id, event_type, premise_id, required, type, required (+8 more)

### Community 49 - "tables"
Cohesion: 0.12
Nodes (15): description, key, description, key, description, key, tables, account_event (+7 more)

### Community 50 - "columns"
Cohesion: 0.15
Nodes (13): required, type, address, contact, holder_name, required, type, columns (+5 more)

### Community 51 - "routes_ui.py"
Cohesion: 0.11
Nodes (30): backtest_zone(), backtest_zones(), demo_accounts(), _demo_only(), demo_reset(), demo_status(), demo_token(), DemoSignIn (+22 more)

### Community 52 - "columns"
Cohesion: 0.06
Nodes (34): max, min, required, type, unit, capacity_kva, district, dtm_accuracy_class (+26 more)

### Community 53 - "columns"
Cohesion: 0.07
Nodes (30): feeder_branch, lat, phase, premise_type, street_seq, tariff, description, required (+22 more)

### Community 54 - "embed.py"
Cohesion: 0.20
Nodes (15): cosine(), download(), embed(), _hash_embed(), keyword_overlap(), _model_dir(), model_name(), _onnx() (+7 more)

### Community 55 - "kwh"
Cohesion: 0.13
Nodes (15): kwh, month, description, max, min, required, type, unit (+7 more)

### Community 56 - "kwh_supplied"
Cohesion: 0.11
Nodes (18): kwh_supplied, transformer_id, ts, max, min, required, type, unit (+10 more)

### Community 57 - "distance_m"
Cohesion: 0.29
Nodes (7): distance_m, description, max, min, required, type, unit

### Community 58 - "pipeline.py"
Cohesion: 0.13
Nodes (32): Nightly run in batches (NFR-01): small meter and zone batches give the same…, _scores(), test_NFR_01_small_batches_give_the_same_results(), _chunks(), copy_in(), copy_out(), _csv(), detect_in_batches() (+24 more)

### Community 59 - "report.py"
Cohesion: 0.15
Nodes (25): The live model once turned a raw gap share of 0.0012 into "0.001%": it now gets…, test_FR_AG_01_live_model_gets_figures_with_units(), approve_content(), approve_export(), _assessment(), _assessment_mock(), build_draft(), draft_for_case() (+17 more)

### Community 60 - "api"
Cohesion: 0.29
Nodes (7): depends_on, env_file, restart, volumes, condition, db, api

### Community 61 - "environment"
Cohesion: 0.38
Nodes (7): environment, ADMIN_DATABASE_URL, DATA_ROOT, DATABASE_URL, HF_HOME, OLLAMA_URL, environment

### Community 62 - "digest_render.py"
Cohesion: 0.08
Nodes (67): Without Chromium (e.g. a minimal image) the export still produces a PDF with…, test_FR_UI_05_pdf_fallback_without_a_browser(), parametrize, Weekly report rules and page (no database): summary, takeaways, Wilson…, Figures shaped like digest.build() for region CEN (the demo's current week)., test_empty_week(), test_energy_takeaways(), test_headline_counts_only() (+59 more)

### Community 63 - "db.py"
Cohesion: 0.09
Nodes (29): caller(), conflict(), connection(), current_session(), Request dependencies: sign-in token, role checks and the caller's database…, me(), BaseModel, get (+21 more)

### Community 64 - "App.jsx"
Cohesion: 0.12
Nodes (16): onSessionChange(), App(), Guarded(), ICONS, ID_ROUTES, NAV, SearchBox(), Shell() (+8 more)

### Community 65 - "voltage_v"
Cohesion: 0.13
Nodes (15): quality_flag, voltage_v, columns, description, key, allowed, description, required (+7 more)

### Community 66 - "engine.py"
Cohesion: 0.08
Nodes (46): balance_zone(), BalanceResult, change_point(), data_quality_flags(), estimate_conventional(), fill_smart_readings(), network_for(), ndarray (+38 more)

### Community 67 - "conftest.py"
Cohesion: 0.12
Nodes (23): api(), cfg(), demo_run(), demo_run_all(), demo_sim(), models(), pg(), fixture (+15 more)

### Community 68 - "dependencies"
Cohesion: 0.06
Nodes (31): @fontsource/ibm-plex-sans, @fontsource/space-grotesk, leaflet, lucide-react, react, react-dom, react-leaflet, react-router-dom (+23 more)

### Community 69 - "post"
Cohesion: 0.15
Nodes (19): pollJob(), post(), JobButton(), start(), DemoGuide(), go(), reset(), fill() (+11 more)

### Community 70 - "t"
Cohesion: 0.11
Nodes (32): Confidence(), Masked(), reasonLabel(), Reasons(), TAG_KEY, Tags(), EvidenceTimeline(), KINDS (+24 more)

### Community 71 - "Caller"
Cohesion: 0.07
Nodes (54): test_FR_AD_01_database_enforces_region_and_pii_rules(), The training_label view once ran as its owner, so each region's hit rate…, test_FR_AD_01_training_labels_and_hit_rates_are_region_limited(), test_unusual_access_alert(), Dependency: the caller must have one of these roles., require(), create_cases(), The case job (runs after scoring): threshold cases plus the random sample. (+46 more)

### Community 72 - "Charts.jsx"
Cohesion: 0.22
Nodes (13): bandPath(), BarChart(), CategoryBars(), LineChart(), niceTicks(), PALETTE, QueryChart(), scale() (+5 more)

### Community 73 - "timedelta"
Cohesion: 0.12
Nodes (18): test_FR_DI_06_missing_day_flags_meter(), Learning and monitoring (SRS FR-ML-01-03, FR-IW-04)., test_FR_ML_01_FR_ML_02_retrain_records_version_with_both_hit_rates(), SGCC electricity-theft adapter (prompt 3.2): daily kWh per customer plus a…, _sort_key(), _days_in(), date, polars (+10 more)

### Community 74 - "evaluation.py"
Cohesion: 0.10
Nodes (20): cmd_detect(), cmd_simreport(), cmd_tune(), Command line: `python -m voltguard <command>`. `make.ps1` and the Makefile call…, load_truth(), evaluate(), _fast_scores(), _fmt() (+12 more)

### Community 75 - "routes_cases.py"
Cohesion: 0.11
Nodes (36): ApiError, forbidden(), not_found(), Remote sign-out of a lost phone (NFR-16): every token of that user stops…, remote_sign_out(), assign(), Assignment, _call() (+28 more)

### Community 76 - "anomaly.py"
Cohesion: 0.23
Nodes (13): cmd_train_models(), Autoencoder, load(), model_path(), ndarray, Anomaly score (SDD 5.3): how badly an autoencoder trained on normal homes…, Last 7 days of half-hourly kWh -> 168 hourly values scaled by their mean., Train on normal homes from the tuning simulation (never the held-out settings). (+5 more)

### Community 77 - "sources.py"
Cohesion: 0.19
Nodes (19): activate_dataset(), Point every table this dataset version holds at it in data_sources.yaml., dataset_versions(), datasets_root(), load_table(), date, LazyFrame, Path (+11 more)

### Community 78 - "guardrails.py"
Cohesion: 0.25
Nodes (10): test_FR_AG_06_no_tools_to_act_and_requests_refused(), allow(), check_output(), OutputBlocked, Exception, Agent guardrails (SDD 8.4, FR-AG-06, NFR-15). * Fixed tool list per agent. No…, Block personal details in anything an agent returns (placeholders such as…, ToolNotAllowed (+2 more)

### Community 79 - "test_cases.py"
Cohesion: 0.23
Nodes (10): find(), Inspection workflow (SRS FR-IW-01-05, FR-UI-03, FR-AG-02; SDD 6.2) end to end…, Regression: a new case with no assigned analyst must not show details to any…, test_FR_AG_02_dispatch_suggestion_claim_and_approval(), test_FR_IW_01_case_job_creates_threshold_cases(), test_FR_IW_01_manual_cases_and_only_supervisor_assigns(), test_FR_IW_02_FR_IW_03_FR_IW_04_outcomes_status_and_labels(), test_FR_IW_05_random_sample_presented_as_routine_check() (+2 more)

### Community 80 - "pattern.py"
Cohesion: 0.18
Nodes (18): auc(), load(), model_path(), PatternModel, ndarray, Pattern model (SDD 5.4): XGBoost on daily-consumption windows, one input of the…, SHAP contributions (log-odds) of the strongest inputs, for the premise page's…, Train on SGCC if loaded, else the synthetic set; hold out 20% to report AUC. (+10 more)

### Community 81 - "Build the Power BI dashboard with Claude on your laptop"
Cohesion: 0.33
Nodes (5): Before you start (5 minutes), Build the Power BI dashboard with Claude on your laptop, Check the result, If Claude cannot open Power BI, Prompt to paste into Claude (Cowork / Desktop on the laptop)

### Community 82 - "chatbot.py"
Cohesion: 0.13
Nodes (22): ask(), _ask_model(), _chart_choice(), _model_params(), _num(), other_region_named(), parse(), parse_mock() (+14 more)

### Community 83 - "login"
Cohesion: 0.15
Nodes (18): login(), fake_names(), API and security (SRS FR-AD-01-03, FR-UI-01-03, NFR-12, NFR-16; SDD 7, 9.2) on…, test_data_manager_upload_validates_and_versions(), test_FR_AD_01_role_and_region_refusals(), test_FR_AD_03_threshold_change_applies_on_rerun(), test_FR_PS_07_suspects_reasons_add_up(), test_FR_UI_01_overview_zone_level_in_gap_order() (+10 more)

### Community 84 - "ollama"
Cohesion: 0.50
Nodes (4): image, restart, volumes, ollama

### Community 85 - "london.py"
Cohesion: 0.16
Nodes (23): test_datagovmy_adapter_month_factors(), _columns(), convert(), month_factors(), month_factors_from(), DataFrame, ndarray, data.gov.my monthly electricity consumption adapter (prompt 3.2). Source:… (+15 more)

### Community 86 - "routes_zones.py"
Cohesion: 0.09
Nodes (39): test_tariff_file_unset_by_default(), test_3_1_value_at_risk_is_an_estimate_from_the_gap_above_the_margin(), latest_run_date(), premise_view(), date, get, Zone and premise views (SDD 7; FR-UI-01-04, FR-PS-07, FR-UI-03 masking). No…, Ranked premises with scores, tags and top reasons (FR-PS-01, FR-PS-07).… (+31 more)

### Community 87 - "pathlib"
Cohesion: 0.18
Nodes (16): _bump(), daily_levels(), household_load_kw(), london_shapes(), _night_block(), ndarray, Path, Household load profiles for the simulator (SDD 10.2). Default: a built-in… (+8 more)

### Community 88 - "api.js"
Cohesion: 0.07
Nodes (51): ApiError, listeners, patch(), request(), setSession(), signIn(), signInDemo(), signOut() (+43 more)

### Community 89 - "secureStore.js"
Cohesion: 0.32
Nodes (13): cryptoKey(), enforceMaxAge(), get(), keys(), MAX_AGE_MS, openDb(), put(), rawDelete() (+5 more)

### Community 90 - "build_zone_inputs"
Cohesion: 0.11
Nodes (17): test_FR_DI_07_district_weather_loaded_and_used(), build_zone_inputs(), DataFrame, date, One ZoneInput per transformer, covering `days` days from `start`., FlowResult, LossParams, _phase_shares() (+9 more)

### Community 91 - "VoltGuard AI R0: review and end-to-end test report"
Cohesion: 0.18
Nodes (10): 1. Does the build meet the SRS and SDD?, 2. End-to-end test: every use case, every account, 3. Bugs found and fixed, 4. Remaining unfinished task: done, 5. Suggested improvements, 6. How to repeat the test, 7. Second round (after the review): what was added and rechecked, Features (+2 more)

### Community 92 - "ValidationReport"
Cohesion: 0.16
Nodes (18): Table, _check_duplicates(), _check_intervals(), _check_links(), _check_values(), coerce(), Issue, _parse_bool() (+10 more)

### Community 93 - "simulator.py"
Cohesion: 0.10
Nodes (41): _run(), test_FR_DI_01_readings_round_trip_match_generator(), test_FR_ZD_02_large_load_priority(), test_FR_ZD_05_many_conventional_meters_still_flag_mining(), test_FR_ML_03_missing_data_and_drift_raise_alerts(), cmd_simulate(), fake_address(), fake_name() (+33 more)

### Community 94 - "Zone.jsx"
Cohesion: 0.18
Nodes (20): BaseTiles(), providers(), startIndex(), numbered(), RouteMap(), zoneStatus(), COLOURS, dotRadius() (+12 more)

### Community 95 - "VoltGuard AI: UI and UX design requirements (R0 → R1 redesign)"
Cohesion: 0.18
Nodes (10): 1. Users and their first question, 2. Design principles, 3. Visual language and design tokens, 4. Components, 5. Screens, 6. Accessibility and language (must pass before release), 7. How to build it (suggested tools), 8. Prompts (+2 more)

### Community 96 - "Waterfall.jsx"
Cohesion: 0.17
Nodes (17): FeederSchematic(), nodeFill(), SHAP_KEY, Waterfall(), change(), layoutSchematic(), PHASES, riskMix() (+9 more)

### Community 97 - "sunshine_hours"
Cohesion: 0.11
Nodes (19): date, sunshine_hours, temperature_c, required, type, columns, description, key (+11 more)

### Community 98 - "How to run VoltGuard AI (and share it with a public link)"
Cohesion: 0.08
Nodes (22): 1. What you need (one time), 2. Set up Docker (one time), 3. Get the code (one time), 4. First start, 5. Everyday commands, 6. Make it a public, clickable link (instead of localhost), 7. When something goes wrong, 8. More documents (+14 more)

### Community 99 - "test_telegram.py"
Cohesion: 0.27
Nodes (11): message(), new_case(), parametrize, Telegram dispatch bot (SRS 5.1-5.2, FR-AG-02): buttons, refusals, linking, and…, A manual NOR case on this premise, or on the next one along the street when it…, The polling bot path, with Telegram's HTTP API replaced by a recorder., test_FR_AD_01_chat_is_for_supervisors_inspectors_and_managers(), test_FR_AG_02_cannot_attend_tells_the_supervisor() (+3 more)

### Community 100 - "3. New features"
Cohesion: 0.11
Nodes (17): 0. Ground rules, 1. Visual direction: "network control room", 2. Pages to redesign, 3.10 Today's route (Could), 3.11 Landlord alert concept (Could, mock only), 3.1 RM at risk (Must), 3.2 Feeder schematic (Must), 3.3 Reason waterfall (Must) (+9 more)

### Community 101 - "test_agents.py"
Cohesion: 0.12
Nodes (14): fixture, parametrize, Agent safety tests (SDD 10.1; FR-AG-01, 03-06, NFR-15): grounding, citations,…, A NOR case taken to Reporting with a confirmed-theft outcome whose notes plant…, The manager reviews evidence photos for the second approval, and not before the…, reporting_case(), test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act(), test_FR_AG_01_FR_UI_05_two_approvals_then_pdf_with_details() (+6 more)

### Community 104 - "i18n.js"
Cohesion: 0.15
Nodes (10): KEYS, LABELS, lang, LANGS, subscribers, DYNAMIC, files(), INDIRECT (+2 more)

### Community 105 - "command"
Cohesion: 0.16
Nodes (18): demo_passwords(), command(), cmd_activate(), cmd_convert(), cmd_sources(), migrate(), Apply sql/*.sql in order (each once) and set the application roles' passwords., _role_password() (+10 more)

### Community 106 - "rag.py"
Cohesion: 0.16
Nodes (20): test_NFR_15_planted_instruction_in_retrieved_text_is_data(), quote_retrieved(), Retrieved text as inert data: instruction-like lines are replaced, never…, case_summary_text(), collect_documents(), _front_matter(), index_case_summaries(), index_documents() (+12 more)

### Community 107 - "Manager dashboard in Power BI (R0)"
Cohesion: 0.25
Nodes (7): Connect Power BI Desktop, Manager dashboard in Power BI (R0), Page 1: Network overview, Page 2: Leaking zones, Page 3: Cases and hit rates, R1, Views

### Community 108 - "answer"
Cohesion: 0.19
Nodes (13): Not found" for a greeting is the online assistant refusing to guess, not a mock…, test_FR_AG_04_field_assistant_mode_says_who_answered(), asks_forbidden_action(), answer(), extractive_answer(), Passage, Connection, Top-k passages the caller may see (doc_chunk row-level security filters by role… (+5 more)

### Community 109 - "Upload area: bring your own datasets"
Cohesion: 0.33
Nodes (5): How to upload, Upload area: bring your own datasets, Versions, What to upload, What validation checks

### Community 110 - "llm.py"
Cohesion: 0.21
Nodes (13): Replies recorded from qwen2.5:7b-instruct: a list of params with 10% as 0.1, a…, test_FR_AG_03_live_model_choice_is_cleaned_and_labelled(), test_NFR_15_model_never_receives_personal_details(), test_NFR_15_model_output_with_personal_details_is_blocked(), available(), check_prompt(), complete(), Completion (+5 more)

### Community 111 - "test_ui_upgrade.py"
Cohesion: 0.15
Nodes (12): config_copy(), demo_on(), fixture, Endpoints added by the UI upgrade (VoltGuard_UI_Upgrade_Prompt.md): value at…, A writable copy of config/ so the tariff can be changed without touching the…, test_3_10_route_stops_show_straight_line_distance_from_base(), test_3_1_rpt_zone_latest_carries_value_at_risk_at_zone_level(), test_3_6_validation_summary_from_files_and_model_versions() (+4 more)

### Community 112 - "re"
Cohesion: 0.24
Nodes (7): collections, re, Create .env from .env.example and fill in generated secrets (used by `make…, expand(), main(), Generate TRACEABILITY.md: every SRS requirement mapped to the code and tests…, requirements()

### Community 113 - "documents"
Cohesion: 0.25
Nodes (7): documents, id, manual, owner, role_scope, title, url

### Community 114 - "voltguard_guide.md"
Cohesion: 0.29
Nodes (6): 1. What a flagged zone means, 2. Flat 24/7 gap, 3. Risk scores and reasons, 4. Voltage evidence, 5. Routine meter checks, 6. Recording outcomes

### Community 115 - "audit.py"
Cohesion: 0.20
Nodes (14): test_FR_AD_02_NFR_12_audit_logged_and_tampering_detected(), anchor_dir(), datetime, Path, Tamper-evident audit log (FR-AD-02, NFR-12). Rows are appended only by the…, Same canonical text as the SQL function vg_audit_text()., Copy the latest hash outside the database (daily job). Existing anchors are…, row_hash() (+6 more)

### Community 116 - "demo_guide.py"
Cohesion: 0.24
Nodes (12): accounts(), guide_config(), Any, Connection, datetime, Guided demo (UI brief 3.8): the 7 live steps of SDD 10.5, checked against the…, Reset rehearsal cases, rerun detection and reseed the demo kit (target: under…, Owner connection (reads the audit log and every table); returns booleans and… (+4 more)

### Community 117 - "field_evidence_checklist.md"
Cohesion: 0.50
Nodes (3): At the meter, Before the visit, Recording

### Community 119 - "routes_agents.py"
Cohesion: 0.23
Nodes (16): agent_status(), approve_content(), approve_export(), _call(), Chat, draft_report(), get_report(), BaseModel (+8 more)

### Community 121 - "Deviations from the SDD"
Cohesion: 0.29
Nodes (6): Additions after the R0 review (not in the SDD), Agents and RAG, Data, Deviations from the SDD, Library swaps, Lite-profile swaps (prompt 7.2)

### Community 122 - "json"
Cohesion: 0.25
Nodes (10): fallbacks(), health(), Any, Connection, Data health per table for the Data manager (UI brief 3.9): how the data was…, Issue counts by table and check from the active upload's validation report., SRS assumptions whose fallback the latest detection run used., Owner connection (counts every region's rows; returns counts only). (+2 more)

### Community 123 - "monitoring.py"
Cohesion: 0.25
Nodes (10): after_detection(), _alert(), check_unusual_access(), collect(), psi(), ndarray, Monitoring and alerts for the data team (FR-ML-03, SDD 9.2, NFR-11). After each…, What monitoring needs from a detection run, small enough to keep across zone… (+2 more)

### Community 124 - "pipeline"
Cohesion: 0.67
Nodes (3): pipeline, meter_batch, zone_batch

### Community 125 - "Traceability"
Cohesion: 0.50
Nodes (3): Requirements, Summary, Traceability

### Community 126 - "Hand-off: VoltGuard AI R0 build"
Cohesion: 0.15
Nodes (12): Auto-generated state (scripts/handoff.sh), Decisions to keep, Docker check (this session), File tree, Graph summary, Hand-off: VoltGuard AI R0 build, How to resume in a new session, Ideas for a next session (+4 more)

### Community 127 - "VoltGuard AI demo script (R0)"
Cohesion: 0.29
Nodes (6): Backup steps (for questions or a recorded clip), If something goes wrong, Live steps (5 minutes), Rehearsal checklist (prompt 7.5), The day before, VoltGuard AI demo script (R0)

### Community 130 - "handoff.py"
Cohesion: 0.36
Nodes (10): CompletedProcess, file_tree(), graphify_cmd(), main(), Path, Rebuild the hand-off material for the next session (run after every finished…, run(), test_count() (+2 more)

### Community 131 - "tunnel-token"
Cohesion: 0.25
Nodes (8): TUNNEL_TOKEN, tunnel-token, command, depends_on, environment, image, profiles, restart

### Community 132 - "psycopg"
Cohesion: 0.25
Nodes (6): Manager dashboard data (SRS FR-UI-01, NFR-07, SDD 9.2): zone-level…, test_NFR_07_rpt_views_hold_no_premise_ids_or_personal_details(), main(), Test accounts: one per role and region from config/demo.yaml, plus the pipeline…, psycopg, pytest

### Community 133 - "learning.py"
Cohesion: 0.28
Nodes (8): cmd_retrain(), hit_rates(), labels(), Model learning (SDD 5.4, FR-ML-01, FR-ML-02, FR-IW-04). Retrain on demand…, Training labels with the premise's features from the latest run on or before…, Hit rate (share confirmed) and precision (share confirmed among cases at or…, retrain(), psycopg_types_json

### Community 134 - "ui_screenshots.py"
Cohesion: 0.39
Nodes (7): argparse, chromium(), ids(), main(), Screenshots of every web page at desktop (1440x900) and phone (390x844) size.…, sign_in(), token()

### Community 135 - "test_digest.py"
Cohesion: 0.32
Nodes (7): fake_names(), Weekly manager summary: region-limited, zone-level, no personal details, PDF…, test_weekly_job_reaches_every_manager_and_supervisor(), test_weekly_report_page_explains_itself_in_both_languages(), test_weekly_summary_is_zone_level_and_region_limited(), test_weekly_summary_pdf_and_message(), test_SRS_5_2_dispatch_messages_hold_no_customer_details()

### Community 136 - "seed.py"
Cohesion: 0.32
Nodes (7): data_path(), predraft_demo_report(), Demo kit (SDD 10.5): closed cases with notes, RAG index and the pre-drafted…, Assessment for the demo premise, drafted ahead of the demo (prompt 7.3,…, Closed cases, RAG index and pre-drafted report. Needs the demo data loaded…, seed_closed_cases(), seed_demo_content()

### Community 137 - "digest.py"
Cohesion: 0.09
Nodes (30): acknowledge(), alerts(), models(), get, post, Model versions, retraining and monitoring alerts (FR-ML-01-03)., Each version with model-ranked and random-sample hit rates side by side (FR-…, Weekly summary of the caller's region: zone-level energy, cases, outcomes and… (+22 more)

### Community 138 - "demo.py"
Cohesion: 0.36
Nodes (7): cmd_demo(), prewarm(), print_script(), `make.ps1 demo`: fresh setup for the judges' demo (SDD 10.5, prompt 4.9 and…, Delete live cases, reports, messages and model versions from earlier rehearsals…, Load models before the demo so nothing is cold (prompt 7.5)., reset_rehearsal()

### Community 139 - "route"
Cohesion: 0.50
Nodes (4): route, road_factor, speed_kmh, visit_minutes

### Community 140 - "VoltGuard R0: finish the rooftop-solar handling (FR-PS-10) and show it"
Cohesion: 0.29
Nodes (6): 1. Close the loophole (Must), 2. Add the missing checks (Must unless marked), 3. Simulator and tests (Must), 4. Show it (Must), 5. Done means, VoltGuard R0: finish the rooftop-solar handling (FR-PS-10) and show it

### Community 141 - "VoltGuard R0: make the weekly summary report self-explanatory"
Cohesion: 0.33
Nodes (5): 1. What to add (in this order on the page), 2. Chart and writing rules, 3. Telegram delivery, 4. Tests and done, VoltGuard R0: make the weekly summary report self-explanatory

### Community 142 - "agents/__init__.py"
Cohesion: 0.40
Nodes (3): Route planner (supports FR-AG-02): visiting order, navigation links, and who…, test_FR_AG_02_team_route_with_navigation_and_limits(), AI agents and RAG (SDD 8). Agents act on VoltGuard's results; they never make…

### Community 143 - "Weekly summary report: before and after"
Cohesion: 0.40
Nodes (4): Fixed on the way, Tests, Weekly summary report: before and after, What changed

### Community 145 - "UI upgrade plan (`VoltGuard_UI_Upgrade_Prompt.md`)"
Cohesion: 0.50
Nodes (3): Order of work, Rules kept, UI upgrade plan (`VoltGuard_UI_Upgrade_Prompt.md`)

## Knowledge Gaps
- **637 isolated node(s):** `Template`, `handoff.sh script`, `name`, `private`, `version` (+632 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Caller` connect `Caller` to `test_digest.py`, `digest.py`, `cases.py`, `route.py`, `local_stack.py`, `routes_admin.py`, `settings.py`, `routes_ui.py`, `report.py`, `db.py`, `conftest.py`, `routes_cases.py`, `test_cases.py`, `chatbot.py`, `login`, `routes_zones.py`, `test_agents.py`, `rag.py`, `answer`, `routes_agents.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `login()` connect `login` to `conftest.py`, `test_telegram.py`, `test_agents.py`, `test_digest.py`, `Caller`, `timedelta`, `rag.py`, `guardrails.py`, `test_cases.py`, `agents/__init__.py`, `test_ui_upgrade.py`, `audit.py`, `routes_zones.py`, `simulator.py`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 101 inferred relationships involving `Caller` (e.g. with `LocalStack` and `ask()`) actually correct?**
  _`Caller` has 101 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Template`, `handoff.sh script`, `name` to the rest of the system?**
  _637 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `pg_server.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1380952380952381 - nodes in this community are weakly interconnected._
- **Should `get` be split into smaller, more focused modules?**
  _Cohesion score 0.11627906976744186 - nodes in this community are weakly interconnected._
- **Should `VoltGuard AI: Software Design Document (SDD)` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._