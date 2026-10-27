# Graph Report - F-35  (2026-10-27)

## Corpus Check
- 141 files · ~95,759 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: .csv 17, (none) 8, .example 1)

## Summary
- 1894 nodes · 4379 edges · 120 communities (109 shown, 11 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 250 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0363865d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- deps.py
- simulator.py
- weights
- VoltGuard AI: Software Design Document (SDD)
- columns
- 3. Functional requirements
- json
- tables
- Build the VoltGuard AI prototype (R0)
- test_data_layer.py
- engine.py
- teams
- conftest.py
- weights
- zone
- validation.py
- Simulation report
- VoltGuard AI R0: build plan
- scrape_configs
- thresholds.yaml
- config.py
- config.example.yml
- run_detection
- test_demo_rehearsal.py
- dispatch
- features
- routes_zones.py
- make.ps1
- cases
- penalties
- voltage
- handoff.sh
- tunnel.sh
- worker
- config.py
- db
- services
- keycloak
- minio
- airflow
- tunnel-named
- proxy
- db.py
- mlflow
- columns
- prometheus
- columns
- premise_id
- columns
- tables
- columns
- .start
- columns
- columns
- answer
- month
- voltage_v
- distance_m
- local_stack.py
- report.py
- api
- environment
- capacity_kva
- routes_admin.py
- App.jsx
- voltage_v
- lat
- datetime
- seed.py
- numpy
- command
- pdf.py
- dtm_accuracy_class
- pattern.py
- VoltGuard AI (R0 prototype)
- Caller
- auth.py
- sources.py
- temperature_c
- voltage_v
- lon
- phase
- re
- cli.py
- ollama
- london.py
- embed.py
- numpy
- loss_params
- secureStore.js
- solve
- llm.py
- pipeline.py
- scoring.py
- Requirements
- street_seq
- tariff
- sunshine_hours
- Deviations from the SDD
- sw.js
- ingest.py
- routes_agents.py
- rag.py
- Manager dashboard in Power BI (R0)
- anomaly.py
- answer
- scrubber.py
- pathlib
- documents
- voltguard_guide.md
- audit.py
- admin_connection
- field_evidence_checklist.md
- Documents for the field assistant and the report agent (RAG)
- VoltGuard AI demo script (R0)
- MODELS.md
- backtest_report.md

## God Nodes (most connected - your core abstractions)
1. `Caller` - 102 edges
2. `Requirements` - 60 edges
3. `login()` - 37 edges
4. `audit()` - 35 edges
5. `t()` - 33 edges
6. `admin_connection()` - 30 edges
7. `simulate_zone()` - 28 edges
8. `run_detection()` - 28 edges
9. `command()` - 27 edges
10. `ingest()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `Docker check (this session)` --references--> `api()`  [INFERRED]
  HANDOFF.md → backend/tests/conftest.py
- `7.2 Compose profiles` --references--> `api()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/tests/conftest.py
- `3.1 Canonical schema (the only thing the pipeline reads)` --references--> `duty_roster()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/voltguard/data/simulator.py
- `Library swaps` --references--> `change_point()`  [INFERRED]
  DEVIATIONS.md → backend/voltguard/detection/balance.py
- `Quick start (Windows laptop)` --references--> `api()`  [INFERRED]
  README.md → backend/tests/conftest.py

## Import Cycles
- None detected.

## Communities (120 total, 11 thin omitted)

### Community 0 - "deps.py"
Cohesion: 0.13
Nodes (12): ApiError, caller(), conflict(), connection(), current_session(), me(), remote_sign_out(), sign_out() (+4 more)

### Community 1 - "simulator.py"
Cohesion: 0.06
Nodes (49): _run(), test_FR_DI_01_readings_round_trip_match_generator(), test_FR_ZD_02_large_load_priority(), test_FR_ZD_05_many_conventional_meters_still_flag_mining(), test_FR_ML_03_missing_data_and_drift_raise_alerts(), cmd_detect(), cmd_simulate(), data_sources() (+41 more)

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

### Community 6 - "json"
Cohesion: 0.14
Nodes (17): test_NFR_07_rpt_views_hold_no_premise_ids_or_personal_details(), cmd_simreport(), cmd_tune(), command(), main(), cmd_activate(), cmd_convert(), cmd_anchor() (+9 more)

### Community 7 - "tables"
Cohesion: 0.08
Nodes (24): downloads, london, sgcc, london, households, region, zone_size, pattern_training (+16 more)

### Community 8 - "Build the VoltGuard AI prototype (R0)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "test_data_layer.py"
Cohesion: 0.31
Nodes (9): small_scenario(), test_bad_upload_is_rejected_with_reasons(), test_column_map_units_and_timezone(), test_FR_DI_06_upload_with_missing_intervals_flags_meter(), test_missing_voltage_and_phase_use_fallbacks(), test_switch_to_uploaded_dataset_without_code_changes(), test_upload_templates_are_a_valid_dataset(), upload_folder() (+1 more)

### Community 10 - "engine.py"
Cohesion: 0.17
Nodes (10): BalanceResult, network_for(), DetectionRun, PremiseResult, run_zones(), ZoneResult, _fit_group(), locate() (+2 more)

### Community 11 - "teams"
Cohesion: 0.12
Nodes (16): demo_seed, demo_zone, regions, code, name, teams, base_lat, base_lon (+8 more)

### Community 12 - "conftest.py"
Cohesion: 0.15
Nodes (10): api(), cfg(), demo_run(), demo_run_all(), demo_sim(), models(), pg(), run_tables() (+2 more)

### Community 13 - "weights"
Cohesion: 0.10
Nodes (20): _tuning, objective, seed, split, tuned_at, zones, weights, anomaly (+12 more)

### Community 14 - "zone"
Cohesion: 0.18
Nodes (11): zone, change_min_segment_days, change_min_shift_share, consecutive_days, conventional_daily_cv, flat_cv, large_load_share, loss_model_error_share (+3 more)

### Community 15 - "validation.py"
Cohesion: 0.14
Nodes (13): Column, Table, _table(), _check_duplicates(), _check_intervals(), _check_links(), _check_values(), coerce() (+5 more)

### Community 16 - "Simulation report"
Cohesion: 0.25
Nodes (7): Demo zone TX-CEN-001, Flag threshold sweep (held-out settings, for OI-7), Held-out thefts, one by one, How to read this, Simulation report, Stress tests (SDD 10.3): where detection breaks, Summary (copy into the pitch deck)

### Community 17 - "VoltGuard AI R0: build plan"
Cohesion: 0.33
Nodes (5): File tree, Key decisions (details in DEVIATIONS.md), Milestones, Open questions (do not block Must requirements), VoltGuard AI R0: build plan

### Community 18 - "scrape_configs"
Cohesion: 0.25
Nodes (7): global, scrape_interval, scrape_configs, job_name, metrics_path, static_configs, targets

### Community 19 - "thresholds.yaml"
Cohesion: 0.29
Nodes (6): monitoring, drift_psi_alert, min_interval_completeness, tenancy, gate_other_evidence, max_contribution

### Community 20 - "config.py"
Cohesion: 0.07
Nodes (36): haversine_km(), roster_date(), run_reminders(), suggest(), _timers(), audit(), add_photo(), assign() (+28 more)

### Community 21 - "config.example.yml"
Cohesion: 0.33
Nodes (5): credentials-file, ingress, hostname, service, tunnel

### Community 22 - "run_detection"
Cohesion: 0.25
Nodes (6): cmd_sources(), active_sources(), ensure_models(), ensure_simulated(), PipelineError, run_detection()

### Community 23 - "test_demo_rehearsal.py"
Cohesion: 0.21
Nodes (9): run_job_and_wait(), sign_in(), stack(), test_demo_live_steps_1_to_7(), api_login(), sign_in(), stack(), test_demo_steps_4_5_dispatch_claim_offline_outcome_and_wipe() (+1 more)

### Community 24 - "dispatch"
Cohesion: 0.40
Nodes (5): dispatch, demo_escalation_minutes, demo_reminder_minutes, escalation_hours, reminder_hours

### Community 25 - "features"
Cohesion: 0.40
Nodes (5): features, history_weeks, recent_days, timing_tau_days, zero_kwh

### Community 26 - "routes_zones.py"
Cohesion: 0.14
Nodes (14): forbidden(), require(), check(), latest_run_date(), premise_view(), _usage(), _zone(), zone_balance() (+6 more)

### Community 28 - "cases"
Cohesion: 0.50
Nodes (4): cases, case_threshold, max_cases_per_zone, random_sample_per_zone

### Community 29 - "penalties"
Cohesion: 0.50
Nodes (4): penalties, ev_charging, solar, vacancy

### Community 30 - "voltage"
Cohesion: 0.50
Nodes (4): voltage, min_drop_v, proximity_scale_m, window_days

### Community 33 - "worker"
Cohesion: 0.17
Nodes (13): build, context, dockerfile, web, worker, build, restart, build (+5 more)

### Community 34 - "config.py"
Cohesion: 0.20
Nodes (10): health(), admin_database_url(), config_dir(), database_url(), demo_mode(), _env(), llm_mode(), public_base_url() (+2 more)

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

### Community 42 - "db.py"
Cohesion: 0.07
Nodes (10): acknowledge(), alerts(), models(), retrain(), _pool(), _run(), running(), submit() (+2 more)

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

### Community 47 - "premise_id"
Cohesion: 0.12
Nodes (16): installed_on, meter_type, premise_id, read_frequency, required, type, columns, allowed (+8 more)

### Community 48 - "columns"
Cohesion: 0.13
Nodes (15): columns, description, key, event_date, event_id, event_type, required, type (+7 more)

### Community 49 - "tables"
Cohesion: 0.12
Nodes (15): description, key, description, key, description, key, tables, duty_roster (+7 more)

### Community 50 - "columns"
Cohesion: 0.15
Nodes (13): required, type, address, contact, holder_name, required, type, columns (+5 more)

### Community 51 - ".start"
Cohesion: 0.21
Nodes (6): LocalStack, _bin(), TempPostgres, close_pools(), migrate(), _role_password()

### Community 52 - "columns"
Cohesion: 0.17
Nodes (12): district, has_dtm, region, required, type, description, required, type (+4 more)

### Community 53 - "columns"
Cohesion: 0.17
Nodes (12): feeder_branch, premise_type, description, required, type, columns, description, key (+4 more)

### Community 54 - "answer"
Cohesion: 0.24
Nodes (7): keyword_overlap(), answer(), extractive_answer(), Passage, search(), _sentences(), similar_cases()

### Community 55 - "month"
Cohesion: 0.13
Nodes (15): kwh, month, description, max, min, required, type, unit (+7 more)

### Community 56 - "voltage_v"
Cohesion: 0.11
Nodes (18): kwh_supplied, transformer_id, ts, max, min, required, type, unit (+10 more)

### Community 57 - "distance_m"
Cohesion: 0.29
Nodes (7): distance_m, description, max, min, required, type, unit

### Community 59 - "report.py"
Cohesion: 0.18
Nodes (15): approve_content(), approve_export(), _assessment(), _assessment_mock(), build_draft(), draft_for_case(), _facts(), get_pdf() (+7 more)

### Community 60 - "api"
Cohesion: 0.29
Nodes (7): depends_on, env_file, restart, volumes, condition, db, api

### Community 61 - "environment"
Cohesion: 0.38
Nodes (7): environment, ADMIN_DATABASE_URL, DATA_ROOT, DATABASE_URL, HF_HOME, OLLAMA_URL, environment

### Community 62 - "capacity_kva"
Cohesion: 0.33
Nodes (6): max, min, required, type, unit, capacity_kva

### Community 63 - "routes_admin.py"
Cohesion: 0.15
Nodes (15): bad_request(), not_found(), audit_log(), audit_verify(), dataset_activate(), dataset_preview(), dataset_report(), datasets() (+7 more)

### Community 64 - "App.jsx"
Cohesion: 0.05
Nodes (109): leaflet, react, react-dom, react-leaflet, react-router-dom, vite, @vitejs/plugin-react, dependencies (+101 more)

### Community 65 - "voltage_v"
Cohesion: 0.15
Nodes (13): meter_id, quality_flag, description, required, type, columns, description, key (+5 more)

### Community 66 - "lat"
Cohesion: 0.40
Nodes (5): lat, max, min, required, type

### Community 67 - "datetime"
Cohesion: 0.27
Nodes (5): data_path(), hit_rates(), labels(), _log_mlflow(), retrain()

### Community 68 - "seed.py"
Cohesion: 0.28
Nodes (3): predraft_demo_report(), seed_closed_cases(), seed_demo_content()

### Community 69 - "numpy"
Cohesion: 0.17
Nodes (13): balance_zone(), change_point(), data_quality_flags(), _days_in(), estimate_conventional(), fill_smart_readings(), similar_groups(), technical_loss() (+5 more)

### Community 70 - "command"
Cohesion: 0.20
Nodes (6): demo_passwords(), cmd_demo(), prewarm(), print_script(), reset_rehearsal(), seed_users()

### Community 71 - "pdf.py"
Cohesion: 0.43
Nodes (3): _chromium(), _fpdf(), html_to_pdf()

### Community 72 - "dtm_accuracy_class"
Cohesion: 0.29
Nodes (7): dtm_accuracy_class, description, max, min, required, type, unit

### Community 73 - "pattern.py"
Cohesion: 0.22
Nodes (10): test_sgcc_adapter_feeds_pattern_model(), auc(), load(), model_path(), PatternModel, sgcc_training_set(), synthetic_training_set(), train() (+2 more)

### Community 74 - "VoltGuard AI (R0 prototype)"
Cohesion: 0.29
Nodes (6): Data modes, Development and tests, Documents, Public link for judges (Cloudflare Tunnel), Status: what works, what does not, what needs TNB, VoltGuard AI (R0 prototype)

### Community 75 - "Caller"
Cohesion: 0.14
Nodes (22): assign(), Assignment, _call(), case_version(), claim_case(), create_case(), create_cases(), run() (+14 more)

### Community 76 - "auth.py"
Cohesion: 0.11
Nodes (17): sign_in(), SignIn, AuthError, check_password(), generate_password(), hash_password(), issue_token(), record_failure() (+9 more)

### Community 77 - "sources.py"
Cohesion: 0.17
Nodes (14): test_london_adapter_profiles_and_canonical_tables(), activate_dataset(), preview(), dataset_versions(), datasets_root(), load_active_tables(), load_table(), period() (+6 more)

### Community 78 - "temperature_c"
Cohesion: 0.33
Nodes (6): temperature_c, max, min, required, type, unit

### Community 79 - "voltage_v"
Cohesion: 0.33
Nodes (6): voltage_v, max, min, required, type, unit

### Community 80 - "lon"
Cohesion: 0.40
Nodes (5): lon, max, min, required, type

### Community 81 - "phase"
Cohesion: 0.40
Nodes (5): phase, allowed, description, required, type

### Community 82 - "re"
Cohesion: 0.20
Nodes (11): test_FR_IW_05_random_sample_presented_as_routine_check(), _ask_model(), other_region_named(), parse(), parse_mock(), _regions(), Template, database_name() (+3 more)

### Community 83 - "cli.py"
Cohesion: 0.48
Nodes (4): cut(), known_cases_active(), known_cases_simulated(), main()

### Community 84 - "ollama"
Cohesion: 0.50
Nodes (4): image, restart, volumes, ollama

### Community 85 - "london.py"
Cohesion: 0.14
Nodes (17): test_datagovmy_adapter_month_factors(), data_root(), _columns(), convert(), month_factors(), month_factors_from(), processed(), raw_dir() (+9 more)

### Community 86 - "embed.py"
Cohesion: 0.23
Nodes (8): cosine(), download(), embed(), _hash_embed(), _model_dir(), model_name(), _onnx(), words()

### Community 87 - "numpy"
Cohesion: 0.19
Nodes (6): _bump(), daily_levels(), household_load_kw(), london_shapes(), _night_block(), synthetic_shapes()

### Community 88 - "loss_params"
Cohesion: 0.50
Nodes (4): loss_params, description, required, type

### Community 89 - "secureStore.js"
Cohesion: 0.32
Nodes (13): cryptoKey(), enforceMaxAge(), get(), keys(), MAX_AGE_MS, openDb(), put(), rawDelete() (+5 more)

### Community 90 - "solve"
Cohesion: 0.12
Nodes (7): recorded_params(), build_zone_inputs(), FlowResult, LossParams, _phase_shares(), solve(), ZoneNetwork

### Community 91 - "llm.py"
Cohesion: 0.26
Nodes (8): test_NFR_15_model_never_receives_personal_details(), test_NFR_15_model_output_with_personal_details_is_blocked(), available(), check_prompt(), complete(), Completion, mode(), PromptBlocked

### Community 92 - "pipeline.py"
Cohesion: 0.27
Nodes (9): copy_in(), copy_out(), _csv(), _jsonable(), load_into_db(), _num(), read_canonical(), upsert() (+1 more)

### Community 93 - "scoring.py"
Cohesion: 0.36
Nodes (4): Reason, reason_text(), Score, score_premise()

### Community 94 - "Requirements"
Cohesion: 0.06
Nodes (64): case_premise(), login(), rank_of(), top_k(), reporting_case(), test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act(), test_FR_AG_01_FR_UI_05_two_approvals_then_pdf_with_details(), test_FR_AG_03_chatbot_answers_with_query_and_refuses_other_region() (+56 more)

### Community 95 - "street_seq"
Cohesion: 0.50
Nodes (4): street_seq, description, required, type

### Community 96 - "tariff"
Cohesion: 0.50
Nodes (4): tariff, allowed, required, type

### Community 97 - "sunshine_hours"
Cohesion: 0.20
Nodes (10): sunshine_hours, columns, description, key, max, min, required, type (+2 more)

### Community 99 - "Deviations from the SDD"
Cohesion: 0.33
Nodes (5): Agents and RAG, Data, Deviations from the SDD, Library swaps, Lite-profile swaps (prompt 7.2)

### Community 104 - "ingest.py"
Cohesion: 0.16
Nodes (15): schema_document(), build_tables(), _checksum(), cmd_ingest(), cmd_upload_kit(), context_for(), ingest(), IngestResult (+7 more)

### Community 105 - "routes_agents.py"
Cohesion: 0.19
Nodes (13): agent_status(), approve_content(), approve_export(), _call(), Chat, chat(), draft_report(), get_report() (+5 more)

### Community 106 - "rag.py"
Cohesion: 0.19
Nodes (12): case_summary_text(), collect_documents(), _front_matter(), index_case_summaries(), index_documents(), _pdf_text(), _sections_legal(), _sections_markdown() (+4 more)

### Community 107 - "Manager dashboard in Power BI (R0)"
Cohesion: 0.25
Nodes (7): Connect Power BI Desktop, Manager dashboard in Power BI (R0), Page 1: Network overview, Page 2: Leaking zones, Page 3: Cases and hit rates, R1, Views

### Community 108 - "anomaly.py"
Cohesion: 0.21
Nodes (9): cmd_train_models(), Autoencoder, load(), model_path(), save(), train(), train_from_simulation(), week_vector() (+1 more)

### Community 109 - "answer"
Cohesion: 0.17
Nodes (9): test_FR_AG_06_no_tools_to_act_and_requests_refused(), ask(), QueryError, run_query(), allow(), asks_forbidden_action(), check_output(), OutputBlocked (+1 more)

### Community 110 - "scrubber.py"
Cohesion: 0.25
Nodes (5): engine(), _known_patterns(), _presidio_analyzer(), scrub(), ScrubResult

### Community 112 - "pathlib"
Cohesion: 0.13
Nodes (8): _free_port(), isolated(), apply_overrides(), fetch_kaggle(), fetch_url(), main(), manual(), main()

### Community 113 - "documents"
Cohesion: 0.25
Nodes (7): documents, id, manual, owner, role_scope, title, url

### Community 114 - "voltguard_guide.md"
Cohesion: 0.29
Nodes (6): 1. What a flagged zone means, 2. Flat 24/7 gap, 3. Risk scores and reasons, 4. Voltage evidence, 5. Routine meter checks, 6. Recording outcomes

### Community 115 - "audit.py"
Cohesion: 0.15
Nodes (8): test_FR_AD_02_NFR_12_audit_logged_and_tampering_detected(), anchor_dir(), row_hash(), row_text(), verify(), VerifyResult, write_anchor(), _call()

### Community 116 - "admin_connection"
Cohesion: 0.07
Nodes (20): test_unusual_access_alert(), lifespan(), admin_connection(), after_detection(), _alert(), check_unusual_access(), psi(), register() (+12 more)

### Community 117 - "field_evidence_checklist.md"
Cohesion: 0.50
Nodes (3): At the meter, Before the visit, Recording

### Community 127 - "VoltGuard AI demo script (R0)"
Cohesion: 0.29
Nodes (6): Backup steps (for questions or a recorded clip), If something goes wrong, Live steps (5 minutes), Rehearsal checklist (prompt 7.5), The day before, VoltGuard AI demo script (R0)

## Knowledge Gaps
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `date` connect `routes_zones.py` to `simulator.py`, `sunshine_hours`, `numpy`, `conftest.py`, `sources.py`, `config.py`, `solve`?**
  _High betweenness centrality (0.188) - this node is a cross-community bridge._
- **Are the 78 inferred relationships involving `Caller` (e.g. with `LocalStack` and `ask()`) actually correct?**
  _`Caller` has 78 INFERRED edges - model-reasoned connections that need verification._
- **Should `deps.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13043478260869565 - nodes in this community are weakly interconnected._
- **Why does `columns` connect `sunshine_hours` to `routes_zones.py`, `columns`, `temperature_c`?**
  _High betweenness centrality (0.188) - this node is a cross-community bridge._
- **Are the 59 inferred relationships involving `Requirements` (e.g. with `test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act()` and `test_FR_AG_01_FR_UI_05_two_approvals_then_pdf_with_details()`) actually correct?**
  _`Requirements` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Should `simulator.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05898021308980213 - nodes in this community are weakly interconnected._
- **Why does `tables` connect `tables` to `sunshine_hours`, `voltage_v`, `columns`, `columns`, `columns`, `month`, `voltage_v`?**
  _High betweenness centrality (0.135) - this node is a cross-community bridge._