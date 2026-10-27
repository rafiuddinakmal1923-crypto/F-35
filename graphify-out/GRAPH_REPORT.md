# Graph Report - F-35  (2026-10-27)

## Corpus Check
- 141 files · ~95,343 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: .csv 17, (none) 8, .example 1)

## Summary
- 1888 nodes · 4360 edges · 130 communities (115 shown, 15 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 249 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `51c2e71e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- locate
- evaluation.py
- weights
- VoltGuard AI: Software Design Document (SDD)
- columns
- 3. Functional requirements
- config.py
- tables
- Build the VoltGuard AI prototype (R0)
- test_data_layer.py
- conftest.py
- teams
- polars
- weights
- zone
- validation.py
- Simulation report
- VoltGuard AI R0: build plan
- scrape_configs
- thresholds.yaml
- dispatch.py
- config.example.yml
- Hand-off: VoltGuard AI R0 build
- VoltGuard AI (R0 prototype)
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
- simulator.py
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
- sunshine_hours
- columns
- columns
- psycopg
- month
- voltage_v
- distance_m
- dtm_accuracy_class
- report.py
- api
- environment
- capacity_kva
- routes_admin.py
- App.jsx
- voltage_v
- lat
- lon
- phase
- numpy
- command
- cases.py
- json
- pattern.py
- street_seq
- Caller
- auth.py
- sources.py
- voltguard/__init__.py
- engine.py
- admin_connection
- .start
- re
- cli.py
- ollama
- london.py
- embed.py
- numpy
- shutil
- secureStore.js
- solve
- llm.py
- pipeline.py
- scoring.py
- login
- Upload area: bring your own datasets
- kwh_supplied
- temperature_c
- local_stack.py
- Deviations from the SDD
- learning.py
- Traceability
- sw.js
- ingest.py
- routes_agents.py
- rag.py
- Manager dashboard in Power BI (R0)
- anomaly.py
- answer
- scrubber.py
- seed.py
- test_demo_rehearsal.py
- documents
- voltguard_guide.md
- audit.py
- scheduler.py
- field_evidence_checklist.md
- Documents for the field assistant and the report agent (RAG)
- loss_params
- tariff
- test_detection_creates_no_cases
- os
- notify.py
- canonical.py
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
8. `ingest()` - 27 edges
9. `run_detection()` - 27 edges
10. `command()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `7.2 Compose profiles` --references--> `api()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/tests/conftest.py
- `Requirements` --references--> `test_NFR_15_every_planted_detail_scrubbed_from_seeded_notes()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_agents.py
- `3.1 Canonical schema (the only thing the pipeline reads)` --references--> `duty_roster()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/voltguard/data/simulator.py
- `Library swaps` --references--> `change_point()`  [INFERRED]
  DEVIATIONS.md → backend/voltguard/detection/balance.py
- `Quick start (Windows laptop)` --references--> `api()`  [INFERRED]
  README.md → backend/tests/conftest.py

## Import Cycles
- None detected.

## Communities (130 total, 15 thin omitted)

### Community 0 - "locate"
Cohesion: 0.24
Nodes (5): network_for(), _fit_group(), locate(), _relative_voltage(), VoltageResult

### Community 1 - "evaluation.py"
Cohesion: 0.16
Nodes (13): heldout_scenario(), tuning_scenario(), _varied_zones(), evaluate(), _fast_scores(), _fmt(), run_scenario(), simulation_report() (+5 more)

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
Cohesion: 0.14
Nodes (20): test_sgcc_adapter_feeds_pattern_model(), health(), cmd_detect(), admin_database_url(), config_dir(), data_path(), data_root(), data_sources() (+12 more)

### Community 7 - "tables"
Cohesion: 0.08
Nodes (24): downloads, london, sgcc, london, households, region, zone_size, pattern_training (+16 more)

### Community 8 - "Build the VoltGuard AI prototype (R0)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "test_data_layer.py"
Cohesion: 0.24
Nodes (12): small_scenario(), test_bad_upload_is_rejected_with_reasons(), test_column_map_units_and_timezone(), test_FR_DI_06_upload_with_missing_intervals_flags_meter(), test_london_adapter_profiles_and_canonical_tables(), test_missing_voltage_and_phase_use_fallbacks(), test_switch_to_uploaded_dataset_without_code_changes(), test_upload_templates_are_a_valid_dataset() (+4 more)

### Community 10 - "conftest.py"
Cohesion: 0.21
Nodes (8): api(), cfg(), demo_run(), demo_run_all(), demo_sim(), pg(), demo_users(), Quick start (Windows laptop)

### Community 11 - "teams"
Cohesion: 0.12
Nodes (16): demo_seed, demo_zone, regions, code, name, teams, base_lat, base_lon (+8 more)

### Community 12 - "polars"
Cohesion: 0.17
Nodes (26): case_premise(), rank_of(), top_k(), test_FR_DI_01_readings_round_trip_match_generator(), test_FR_DI_02_voltage_for_smart_meters_only(), test_FR_DI_03_supply_equals_homes_plus_loss_plus_taps(), test_FR_DI_04_every_meter_linked_to_one_transformer(), test_FR_DI_05_tenancy_change_at_injected_thief() (+18 more)

### Community 13 - "weights"
Cohesion: 0.10
Nodes (20): _tuning, objective, seed, split, tuned_at, zones, weights, anomaly (+12 more)

### Community 14 - "zone"
Cohesion: 0.18
Nodes (11): zone, change_min_segment_days, change_min_shift_share, consecutive_days, conventional_daily_cv, flat_cv, large_load_share, loss_model_error_share (+3 more)

### Community 15 - "validation.py"
Cohesion: 0.24
Nodes (10): _check_duplicates(), _check_intervals(), _check_links(), _check_values(), coerce(), Issue, _parse_bool(), _parse_timestamp() (+2 more)

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

### Community 20 - "dispatch.py"
Cohesion: 0.14
Nodes (11): haversine_km(), roster_date(), run_reminders(), suggest(), _timers(), get_thresholds(), demo_mode(), overrides() (+3 more)

### Community 21 - "config.example.yml"
Cohesion: 0.33
Nodes (5): credentials-file, ingress, hostname, service, tunnel

### Community 22 - "Hand-off: VoltGuard AI R0 build"
Cohesion: 0.25
Nodes (7): preview(), Decisions to keep, Hand-off: VoltGuard AI R0 build, How to resume in a new session, Ideas for a next session, Known issues, Status by milestone (PLAN.md)

### Community 23 - "VoltGuard AI (R0 prototype)"
Cohesion: 0.29
Nodes (6): Data modes, Development and tests, Documents, Public link for judges (Cloudflare Tunnel), Status: what works, what does not, what needs TNB, VoltGuard AI (R0 prototype)

### Community 24 - "dispatch"
Cohesion: 0.40
Nodes (5): dispatch, demo_escalation_minutes, demo_reminder_minutes, escalation_hours, reminder_hours

### Community 25 - "features"
Cohesion: 0.40
Nodes (5): features, history_weeks, recent_days, timing_tau_days, zero_kwh

### Community 26 - "routes_zones.py"
Cohesion: 0.17
Nodes (11): latest_run_date(), premise_view(), _usage(), _zone(), zone_balance(), zone_suspects(), zone_voltage(), zones() (+3 more)

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

### Community 34 - "simulator.py"
Cohesion: 0.12
Nodes (22): _run(), test_FR_ZD_02_large_load_priority(), test_FR_ZD_05_many_conventional_meters_still_flag_mining(), test_FR_ML_03_missing_data_and_drift_raise_alerts(), cmd_simulate(), fake_address(), fake_name(), fake_phone() (+14 more)

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
Cohesion: 0.10
Nodes (14): create_cases(), run(), admin_connection(), app_connection(), _pool(), cmd_snapshot(), _run(), running() (+6 more)

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
Cohesion: 0.13
Nodes (15): installed_on, meter_type, read_frequency, required, type, columns, description, key (+7 more)

### Community 48 - "columns"
Cohesion: 0.13
Nodes (15): columns, description, key, event_date, event_id, event_type, required, type (+7 more)

### Community 49 - "tables"
Cohesion: 0.15
Nodes (12): description, key, description, key, description, key, tables, district_weather (+4 more)

### Community 50 - "columns"
Cohesion: 0.12
Nodes (17): required, type, address, contact, holder_name, premise_id, required, type (+9 more)

### Community 51 - "sunshine_hours"
Cohesion: 0.33
Nodes (6): sunshine_hours, max, min, required, type, unit

### Community 52 - "columns"
Cohesion: 0.17
Nodes (12): has_dtm, region, description, required, type, description, required, type (+4 more)

### Community 53 - "columns"
Cohesion: 0.17
Nodes (12): feeder_branch, premise_type, description, required, type, columns, description, key (+4 more)

### Community 54 - "psycopg"
Cohesion: 0.14
Nodes (14): fake_names(), test_data_manager_upload_validates_and_versions(), test_FR_AD_01_database_enforces_region_and_pii_rules(), test_FR_AD_01_role_and_region_refusals(), test_FR_AD_02_NFR_12_audit_logged_and_tampering_detected(), test_FR_AD_03_threshold_change_applies_on_rerun(), test_FR_PS_07_suspects_reasons_add_up(), test_FR_UI_02_zone_view_balance_and_profile() (+6 more)

### Community 55 - "month"
Cohesion: 0.13
Nodes (15): kwh, month, description, max, min, required, type, unit (+7 more)

### Community 56 - "voltage_v"
Cohesion: 0.11
Nodes (18): transformer_id, ts, voltage_v, transformer_reading, description, required, type, columns (+10 more)

### Community 57 - "distance_m"
Cohesion: 0.29
Nodes (7): distance_m, description, max, min, required, type, unit

### Community 58 - "dtm_accuracy_class"
Cohesion: 0.29
Nodes (7): dtm_accuracy_class, description, max, min, required, type, unit

### Community 59 - "report.py"
Cohesion: 0.12
Nodes (19): approve_content(), approve_export(), _assessment(), _assessment_mock(), build_draft(), draft_for_case(), _facts(), get_pdf() (+11 more)

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
Nodes (14): bad_request(), not_found(), audit_log(), audit_verify(), dataset_activate(), dataset_preview(), dataset_report(), datasets() (+6 more)

### Community 64 - "App.jsx"
Cohesion: 0.05
Nodes (109): leaflet, react, react-dom, react-leaflet, react-router-dom, vite, @vitejs/plugin-react, dependencies (+101 more)

### Community 65 - "voltage_v"
Cohesion: 0.15
Nodes (13): meter_id, quality_flag, description, required, type, columns, description, key (+5 more)

### Community 66 - "lat"
Cohesion: 0.40
Nodes (5): lat, max, min, required, type

### Community 67 - "lon"
Cohesion: 0.40
Nodes (5): lon, max, min, required, type

### Community 68 - "phase"
Cohesion: 0.40
Nodes (5): phase, allowed, description, required, type

### Community 69 - "numpy"
Cohesion: 0.24
Nodes (9): balance_zone(), change_point(), data_quality_flags(), _days_in(), estimate_conventional(), fill_smart_readings(), similar_groups(), technical_loss() (+1 more)

### Community 70 - "command"
Cohesion: 0.11
Nodes (16): demo_passwords(), cmd_simreport(), cmd_tune(), command(), cmd_activate(), cmd_convert(), cmd_sources(), cmd_pipeline() (+8 more)

### Community 71 - "cases.py"
Cohesion: 0.17
Nodes (21): audit(), add_photo(), assign(), _assign(), _case(), case_detail(), CaseError, claim() (+13 more)

### Community 72 - "json"
Cohesion: 0.23
Nodes (11): test_FR_UI_01_overview_zone_level_in_gap_order(), fake_names(), find(), test_FR_AG_02_dispatch_suggestion_claim_and_approval(), test_FR_IW_01_case_job_creates_threshold_cases(), test_FR_IW_01_manual_cases_and_only_supervisor_assigns(), test_FR_IW_02_03_04_outcomes_status_and_labels(), test_FR_IW_05_random_sample_from_flagged_zones_only() (+3 more)

### Community 73 - "pattern.py"
Cohesion: 0.22
Nodes (10): cmd_train_models(), load(), model_path(), PatternModel, reset_cache(), sgcc_training_set(), synthetic_training_set(), train() (+2 more)

### Community 74 - "street_seq"
Cohesion: 0.50
Nodes (4): street_seq, description, required, type

### Community 75 - "Caller"
Cohesion: 0.17
Nodes (19): assign(), Assignment, _call(), case_version(), claim_case(), create_case(), decide(), Decision (+11 more)

### Community 76 - "auth.py"
Cohesion: 0.15
Nodes (14): AuthError, check_password(), decode_token(), generate_password(), hash_password(), issue_token(), record_failure(), throttled() (+6 more)

### Community 77 - "sources.py"
Cohesion: 0.19
Nodes (12): activate_dataset(), context_for(), active_sources(), dataset_versions(), datasets_root(), load_active_tables(), load_table(), resolve_upload() (+4 more)

### Community 78 - "voltguard/__init__.py"
Cohesion: 0.10
Nodes (5): acknowledge(), alerts(), models(), retrain(), versions()

### Community 79 - "engine.py"
Cohesion: 0.17
Nodes (9): BalanceResult, DetectionRun, PremiseResult, run_zones(), ZoneResult, build_features(), _clip01(), _drop_share() (+1 more)

### Community 80 - "admin_connection"
Cohesion: 0.19
Nodes (7): test_FR_IW_04_no_access_never_a_label(), test_FR_ML_01_FR_ML_02_retrain_records_version_with_both_hit_rates(), test_unusual_access_alert(), after_detection(), _alert(), check_unusual_access(), psi()

### Community 81 - ".start"
Cohesion: 0.29
Nodes (5): _bin(), TempPostgres, migrate(), _role_password(), cmd_migrate()

### Community 82 - "re"
Cohesion: 0.16
Nodes (13): ask(), _ask_model(), other_region_named(), parse(), parse_mock(), QueryError, _regions(), run_query() (+5 more)

### Community 83 - "cli.py"
Cohesion: 0.23
Nodes (6): test_NFR_07_rpt_views_hold_no_premise_ids_or_personal_details(), main(), cut(), known_cases_active(), known_cases_simulated(), main()

### Community 84 - "ollama"
Cohesion: 0.50
Nodes (4): image, restart, volumes, ollama

### Community 85 - "london.py"
Cohesion: 0.14
Nodes (16): test_datagovmy_adapter_month_factors(), _columns(), convert(), month_factors(), month_factors_from(), processed(), raw_dir(), _stamp() (+8 more)

### Community 86 - "embed.py"
Cohesion: 0.18
Nodes (10): cosine(), download(), embed(), _hash_embed(), keyword_overlap(), _model_dir(), model_name(), _onnx() (+2 more)

### Community 87 - "numpy"
Cohesion: 0.19
Nodes (6): _bump(), daily_levels(), household_load_kw(), london_shapes(), _night_block(), synthetic_shapes()

### Community 88 - "shutil"
Cohesion: 0.15
Nodes (8): isolated(), apply_overrides(), fetch_kaggle(), fetch_url(), main(), manual(), main(), main()

### Community 89 - "secureStore.js"
Cohesion: 0.32
Nodes (13): cryptoKey(), enforceMaxAge(), get(), keys(), MAX_AGE_MS, openDb(), put(), rawDelete() (+5 more)

### Community 90 - "solve"
Cohesion: 0.11
Nodes (7): recorded_params(), build_zone_inputs(), FlowResult, LossParams, _phase_shares(), solve(), ZoneNetwork

### Community 91 - "llm.py"
Cohesion: 0.21
Nodes (8): test_NFR_15_model_never_receives_personal_details(), test_NFR_15_model_output_with_personal_details_is_blocked(), available(), check_prompt(), complete(), Completion, mode(), PromptBlocked

### Community 92 - "pipeline.py"
Cohesion: 0.18
Nodes (13): copy_in(), copy_out(), _csv(), ensure_simulated(), _jsonable(), load_into_db(), _num(), PipelineError (+5 more)

### Community 93 - "scoring.py"
Cohesion: 0.36
Nodes (4): Reason, reason_text(), Score, score_premise()

### Community 94 - "login"
Cohesion: 0.17
Nodes (11): login(), reporting_case(), test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act(), test_FR_AG_01_FR_UI_05_two_approvals_then_pdf_with_details(), test_FR_AG_03_chatbot_answers_with_query_and_refuses_other_region(), test_FR_AG_04_field_assistant_cites_or_says_not_found(), test_FR_AG_05_three_similar_closed_cases(), test_NFR_15_every_planted_detail_scrubbed_from_seeded_notes() (+3 more)

### Community 95 - "Upload area: bring your own datasets"
Cohesion: 0.33
Nodes (5): How to upload, Upload area: bring your own datasets, Versions, What to upload, What validation checks

### Community 96 - "kwh_supplied"
Cohesion: 0.33
Nodes (6): kwh_supplied, max, min, required, type, unit

### Community 97 - "temperature_c"
Cohesion: 0.20
Nodes (10): district, temperature_c, required, type, columns, max, min, required (+2 more)

### Community 99 - "Deviations from the SDD"
Cohesion: 0.33
Nodes (5): Agents and RAG, Data, Deviations from the SDD, Library swaps, Lite-profile swaps (prompt 7.2)

### Community 100 - "learning.py"
Cohesion: 0.33
Nodes (5): auc(), hit_rates(), labels(), _log_mlflow(), retrain()

### Community 104 - "ingest.py"
Cohesion: 0.14
Nodes (14): schema_document(), build_tables(), _checksum(), cmd_ingest(), cmd_upload_kit(), ingest(), IngestResult, load_column_map() (+6 more)

### Community 105 - "routes_agents.py"
Cohesion: 0.08
Nodes (28): ApiError, caller(), conflict(), connection(), current_session(), forbidden(), require(), check() (+20 more)

### Community 106 - "rag.py"
Cohesion: 0.14
Nodes (16): case_summary_text(), collect_documents(), extractive_answer(), _front_matter(), index_case_summaries(), index_documents(), Passage, _pdf_text() (+8 more)

### Community 107 - "Manager dashboard in Power BI (R0)"
Cohesion: 0.25
Nodes (7): Connect Power BI Desktop, Manager dashboard in Power BI (R0), Page 1: Network overview, Page 2: Leaking zones, Page 3: Cases and hit rates, R1, Views

### Community 108 - "anomaly.py"
Cohesion: 0.24
Nodes (7): Autoencoder, load(), model_path(), save(), train(), train_from_simulation(), week_vector()

### Community 109 - "answer"
Cohesion: 0.18
Nodes (9): test_FR_AG_06_no_tools_to_act_and_requests_refused(), allow(), asks_forbidden_action(), check_output(), OutputBlocked, ToolNotAllowed, answer(), search() (+1 more)

### Community 110 - "scrubber.py"
Cohesion: 0.25
Nodes (5): engine(), _known_patterns(), _presidio_analyzer(), scrub(), ScrubResult

### Community 112 - "test_demo_rehearsal.py"
Cohesion: 0.18
Nodes (10): run_job_and_wait(), sign_in(), stack(), test_demo_live_steps_1_to_7(), api_login(), sign_in(), stack(), test_demo_steps_4_5_dispatch_claim_offline_outcome_and_wipe() (+2 more)

### Community 113 - "documents"
Cohesion: 0.25
Nodes (7): documents, id, manual, owner, role_scope, title, url

### Community 114 - "voltguard_guide.md"
Cohesion: 0.29
Nodes (6): 1. What a flagged zone means, 2. Flat 24/7 gap, 3. Risk scores and reasons, 4. Voltage evidence, 5. Routine meter checks, 6. Recording outcomes

### Community 115 - "audit.py"
Cohesion: 0.19
Nodes (8): anchor_dir(), row_hash(), row_text(), verify(), VerifyResult, write_anchor(), cmd_anchor(), cmd_verify_audit()

### Community 116 - "scheduler.py"
Cohesion: 0.18
Nodes (6): lifespan(), close_pools(), register(), _safe(), start(), stop()

### Community 117 - "field_evidence_checklist.md"
Cohesion: 0.50
Nodes (3): At the meter, Before the visit, Recording

### Community 121 - "loss_params"
Cohesion: 0.50
Nodes (4): loss_params, description, required, type

### Community 122 - "tariff"
Cohesion: 0.50
Nodes (4): tariff, allowed, required, type

### Community 125 - "notify.py"
Cohesion: 0.24
Nodes (6): BlockedMessage, case_link(), _chat_ids(), compose(), output_check(), send()

### Community 126 - "canonical.py"
Cohesion: 0.38
Nodes (3): Column, Table, _table()

### Community 127 - "VoltGuard AI demo script (R0)"
Cohesion: 0.29
Nodes (6): Backup steps (for questions or a recorded clip), If something goes wrong, Live steps (5 minutes), Rehearsal checklist (prompt 7.5), The day before, VoltGuard AI demo script (R0)

## Knowledge Gaps
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `date` connect `routes_zones.py` to `temperature_c`, `simulator.py`, `numpy`, `test_data_layer.py`, `dispatch.py`, `solve`?**
  _High betweenness centrality (0.193) - this node is a cross-community bridge._
- **Are the 78 inferred relationships involving `Caller` (e.g. with `LocalStack` and `ask()`) actually correct?**
  _`Caller` has 78 INFERRED edges - model-reasoned connections that need verification._
- **Should `VoltGuard AI: Software Design Document (SDD)` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Why does `columns` connect `temperature_c` to `tables`, `routes_zones.py`, `sunshine_hours`?**
  _High betweenness centrality (0.189) - this node is a cross-community bridge._
- **Are the 59 inferred relationships involving `Requirements` (e.g. with `test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act()` and `test_FR_AG_01_FR_UI_05_two_approvals_then_pdf_with_details()`) actually correct?**
  _`Requirements` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Should `columns` be split into smaller, more focused modules?**
  _Cohesion score 0.06896551724137931 - nodes in this community are weakly interconnected._
- **Why does `tables` connect `tables` to `voltage_v`, `premise_id`, `columns`, `columns`, `columns`, `columns`, `month`, `voltage_v`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._