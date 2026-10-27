# Graph Report - F-35  (2026-10-27)

## Corpus Check
- 156 files · ~113,956 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: .csv 17, (none) 8, .example 1)

## Summary
- 2126 nodes · 5011 edges · 135 communities (121 shown, 14 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 280 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `93671eb6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- db.py
- get
- weights
- VoltGuard AI: Software Design Document (SDD)
- columns
- 3. Functional requirements
- evaluation.py
- tables
- Build the VoltGuard AI prototype (R0)
- test_data_layer.py
- e2e_use_cases.py
- teams
- Requirements
- weights
- zone
- validation.py
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
- routes_zones.py
- make.ps1
- cases
- penalties
- voltage
- handoff.sh
- tunnel.sh
- worker
- thresholds
- db
- services
- keycloak
- minio
- airflow
- tunnel-named
- proxy
- seed.py
- mlflow
- columns
- prometheus
- columns
- premise_id
- columns
- tables
- columns
- auth.py
- columns
- columns
- embed.py
- month
- voltage_v
- distance_m
- ingest.py
- report.py
- api
- environment
- capacity_kva
- Caller
- App.jsx
- voltage_v
- anomaly.py
- conftest.py
- package.json
- guardrails.py
- request
- admin_connection
- Premise.jsx
- pattern.py
- numpy
- Caller
- notify.py
- sources.py
- json
- learning.py
- test_api_security.py
- os
- re
- voltguard/__init__.py
- ollama
- london.py
- build_zone_inputs
- numpy
- api.js
- secureStore.js
- solve
- VoltGuard AI R0: review and end-to-end test report
- pipeline.py
- simulator.py
- login
- VoltGuard AI: UI and UX design requirements (R0 → R1 redesign)
- scoring.py
- sunshine_hours
- VoltGuard AI (R0 prototype)
- Deviations from the SDD
- config.py
- engine.py
- sw.js
- command
- demo.py
- rag.py
- Manager dashboard in Power BI (R0)
- test_telegram.py
- Upload area: bring your own datasets
- llm.py
- Hand-off: VoltGuard AI R0 build
- pg_server.py
- documents
- voltguard_guide.md
- audit.py
- storage.py
- field_evidence_checklist.md
- Documents for the field assistant and the report agent (RAG)
- fetch_datasets.py
- Traceability
- session
- lat
- canonical.py
- test_FR_UI_05_pdf_fallback_without_a_browser
- VoltGuard AI demo script (R0)
- MODELS.md
- backtest_report.md
- jobs.py
- Assistant.jsx
- digest.py
- route

## God Nodes (most connected - your core abstractions)
1. `Caller` - 124 edges
2. `Requirements` - 70 edges
3. `login()` - 53 edges
4. `audit()` - 43 edges
5. `t()` - 39 edges
6. `admin_connection()` - 38 edges
7. `shot()` - 33 edges
8. `get()` - 31 edges
9. `run_detection()` - 29 edges
10. `request()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `Requirements` --references--> `test_NFR_15_every_planted_detail_scrubbed_from_seeded_notes()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_agents.py
- `3.1 Canonical schema (the only thing the pipeline reads)` --references--> `duty_roster()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/voltguard/data/simulator.py
- `Review round (after the team's laptop test, 2026-10-27)` --references--> `QueryChart()`  [INFERRED]
  HANDOFF.md → web/src/components/Charts.jsx
- `2. Design principles` --references--> `t()`  [INFERRED]
  docs/UI_UX_DESIGN_REQUIREMENTS.md → web/src/i18n.js
- `Graph summary` --references--> `login()`  [INFERRED]
  HANDOFF.md → backend/tests/conftest.py

## Import Cycles
- None detected.

## Communities (135 total, 14 thin omitted)

### Community 0 - "db.py"
Cohesion: 0.09
Nodes (7): caller(), connection(), forbidden(), require(), check(), audit_log(), remote_sign_out()

### Community 1 - "get"
Cohesion: 0.19
Nodes (19): get(), put(), CategoryBars(), ErrorBox(), useLoad(), Audit(), runVerify(), Cases() (+11 more)

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

### Community 6 - "evaluation.py"
Cohesion: 0.16
Nodes (12): test_FR_DI_06_missing_day_flags_meter(), DetectionRun, run_tables(), evaluate(), _fast_scores(), _fmt(), run_scenario(), simulation_report() (+4 more)

### Community 7 - "tables"
Cohesion: 0.08
Nodes (24): downloads, london, sgcc, london, households, region, zone_size, pattern_training (+16 more)

### Community 8 - "Build the VoltGuard AI prototype (R0)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "test_data_layer.py"
Cohesion: 0.20
Nodes (11): isolated(), small_scenario(), test_bad_upload_is_rejected_with_reasons(), test_column_map_units_and_timezone(), test_FR_DI_06_upload_with_missing_intervals_flags_meter(), test_missing_voltage_and_phase_use_fallbacks(), test_switch_to_uploaded_dataset_without_code_changes(), test_upload_templates_are_a_valid_dataset() (+3 more)

### Community 10 - "e2e_use_cases.py"
Cohesion: 0.08
Nodes (48): adm_data(), adm_settings(), adm_upload(), api(), ask(), bm(), check(), desk() (+40 more)

### Community 11 - "teams"
Cohesion: 0.12
Nodes (16): demo_seed, demo_zone, regions, code, name, teams, base_lat, base_lon (+8 more)

### Community 12 - "Requirements"
Cohesion: 0.15
Nodes (27): case_premise(), rank_of(), top_k(), test_detection_creates_no_cases(), test_FR_DI_02_voltage_for_smart_meters_only(), test_FR_DI_03_supply_equals_homes_plus_loss_plus_taps(), test_FR_DI_04_every_meter_linked_to_one_transformer(), test_FR_DI_05_tenancy_change_at_injected_thief() (+19 more)

### Community 13 - "weights"
Cohesion: 0.10
Nodes (20): _tuning, objective, seed, split, tuned_at, zones, weights, anomaly (+12 more)

### Community 14 - "zone"
Cohesion: 0.18
Nodes (11): zone, change_min_segment_days, change_min_shift_share, consecutive_days, conventional_daily_cv, flat_cv, large_load_share, loss_model_error_share (+3 more)

### Community 15 - "validation.py"
Cohesion: 0.19
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

### Community 20 - "cases.py"
Cohesion: 0.15
Nodes (24): sign_out(), audit(), add_photo(), assign(), _assign(), _case(), case_detail(), CaseError (+16 more)

### Community 21 - "config.example.yml"
Cohesion: 0.33
Nodes (5): credentials-file, ingress, hostname, service, tunnel

### Community 22 - "route.py"
Cohesion: 0.09
Nodes (19): test_route_order_beats_nearest_neighbour_and_is_close_to_the_best(), haversine_km(), roster_date(), suggest(), _base(), _leg(), maps_links(), nearest_neighbour() (+11 more)

### Community 23 - "local_stack.py"
Cohesion: 0.13
Nodes (11): run_job_and_wait(), sign_in(), stack(), test_demo_live_steps_1_to_7(), test_NFR_02_NFR_13_pages_load_fast_and_phone_view_in_bahasa_melayu(), api_login(), sign_in(), stack() (+3 more)

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

### Community 34 - "thresholds"
Cohesion: 0.29
Nodes (6): run_reminders(), get_thresholds(), overrides(), save(), thresholds(), validate_change()

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

### Community 42 - "seed.py"
Cohesion: 0.16
Nodes (8): engine(), _known_patterns(), _presidio_analyzer(), scrub(), ScrubResult, predraft_demo_report(), seed_closed_cases(), seed_demo_content()

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

### Community 51 - "auth.py"
Cohesion: 0.16
Nodes (12): current_session(), sign_in(), SignIn, AuthError, check_password(), decode_token(), hash_password(), issue_token() (+4 more)

### Community 52 - "columns"
Cohesion: 0.07
Nodes (28): dtm_accuracy_class, has_dtm, lon, loss_params, region, description, max, min (+20 more)

### Community 53 - "columns"
Cohesion: 0.08
Nodes (25): feeder_branch, phase, premise_type, street_seq, tariff, description, required, type (+17 more)

### Community 54 - "embed.py"
Cohesion: 0.19
Nodes (9): cosine(), download(), embed(), _hash_embed(), _model_dir(), model_name(), _onnx(), words() (+1 more)

### Community 55 - "month"
Cohesion: 0.13
Nodes (15): kwh, month, description, max, min, required, type, unit (+7 more)

### Community 56 - "voltage_v"
Cohesion: 0.10
Nodes (20): kwh_supplied, transformer_id, voltage_v, max, min, required, type, unit (+12 more)

### Community 57 - "distance_m"
Cohesion: 0.29
Nodes (7): distance_m, description, max, min, required, type, unit

### Community 58 - "ingest.py"
Cohesion: 0.16
Nodes (15): schema_document(), build_tables(), _checksum(), cmd_ingest(), cmd_upload_kit(), context_for(), ingest(), IngestResult (+7 more)

### Community 59 - "report.py"
Cohesion: 0.17
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

### Community 63 - "Caller"
Cohesion: 0.09
Nodes (27): bad_request(), dataset_activate(), dataset_preview(), datasets(), put_thresholds(), run_detection(), set_source(), upload_dataset() (+19 more)

### Community 64 - "App.jsx"
Cohesion: 0.16
Nodes (27): onSessionChange(), App(), Guarded(), NAV, Shell(), useSession(), AskBox(), ask() (+19 more)

### Community 65 - "voltage_v"
Cohesion: 0.12
Nodes (17): meter_id, quality_flag, ts, description, required, type, columns, description (+9 more)

### Community 66 - "anomaly.py"
Cohesion: 0.24
Nodes (6): Autoencoder, load(), model_path(), save(), train(), week_vector()

### Community 67 - "conftest.py"
Cohesion: 0.11
Nodes (10): api(), cfg(), demo_run(), demo_run_all(), demo_sim(), models(), pg(), test_NFR_03_no_endpoint_blocks_the_event_loop() (+2 more)

### Community 68 - "package.json"
Cohesion: 0.09
Nodes (25): leaflet, react, react-dom, react-leaflet, vite, @vitejs/plugin-react, dependencies, leaflet@1.9.4 (+17 more)

### Community 69 - "guardrails.py"
Cohesion: 0.16
Nodes (11): keyword_overlap(), allow(), asks_forbidden_action(), check_output(), OutputBlocked, ToolNotAllowed, answer(), extractive_answer() (+3 more)

### Community 70 - "request"
Cohesion: 0.18
Nodes (21): 8. Prompts, patch(), pollJob(), post(), request(), JobButton(), start(), Masked() (+13 more)

### Community 71 - "admin_connection"
Cohesion: 0.07
Nodes (31): test_unusual_access_alert(), create_cases(), run(), chats(), link_code(), status(), unlink(), admin_connection() (+23 more)

### Community 72 - "Premise.jsx"
Cohesion: 0.26
Nodes (16): react-router-dom, BarChart(), LineChart(), niceTicks(), PALETTE, scale(), VoltageStrip(), Confidence() (+8 more)

### Community 73 - "pattern.py"
Cohesion: 0.23
Nodes (9): test_sgcc_adapter_feeds_pattern_model(), load(), model_path(), PatternModel, sgcc_training_set(), synthetic_training_set(), train(), train_default() (+1 more)

### Community 74 - "numpy"
Cohesion: 0.15
Nodes (14): balance_zone(), data_quality_flags(), _days_in(), estimate_conventional(), fill_smart_readings(), network_for(), similar_groups(), technical_loss() (+6 more)

### Community 75 - "Caller"
Cohesion: 0.12
Nodes (22): ApiError, conflict(), not_found(), assign(), Assignment, _call(), case_version(), claim_case() (+14 more)

### Community 76 - "notify.py"
Cohesion: 0.19
Nodes (10): public_base_url(), BlockedMessage, case_link(), _chat_ids(), compose(), keyboard(), output_check(), recipient_chats() (+2 more)

### Community 77 - "sources.py"
Cohesion: 0.22
Nodes (10): activate_dataset(), dataset_versions(), datasets_root(), load_active_tables(), load_table(), resolve_upload(), set_source(), simulation_run() (+2 more)

### Community 78 - "json"
Cohesion: 0.16
Nodes (14): test_FR_UI_01_overview_zone_level_in_gap_order(), case_job(), fake_names(), find(), test_FR_AG_02_dispatch_suggestion_claim_and_approval(), test_FR_AG_02_reminder_then_escalation_on_demo_timers(), test_FR_IW_01_case_job_creates_threshold_cases(), test_FR_IW_01_manual_cases_and_only_supervisor_assigns() (+6 more)

### Community 79 - "learning.py"
Cohesion: 0.33
Nodes (5): auc(), hit_rates(), labels(), _log_mlflow(), retrain()

### Community 80 - "test_api_security.py"
Cohesion: 0.13
Nodes (15): fake_names(), test_data_manager_upload_validates_and_versions(), test_FR_AD_01_database_enforces_region_and_pii_rules(), test_FR_AD_01_role_and_region_refusals(), test_FR_AD_02_NFR_12_audit_logged_and_tampering_detected(), test_FR_AD_03_threshold_change_applies_on_rerun(), test_FR_PS_07_suspects_reasons_add_up(), test_FR_UI_02_zone_view_balance_and_profile() (+7 more)

### Community 82 - "re"
Cohesion: 0.12
Nodes (17): ask(), _ask_model(), _chart_choice(), _num(), other_region_named(), parse(), parse_mock(), QueryError (+9 more)

### Community 83 - "voltguard/__init__.py"
Cohesion: 0.25
Nodes (5): cut(), known_cases_active(), known_cases_simulated(), main(), main()

### Community 84 - "ollama"
Cohesion: 0.50
Nodes (4): image, restart, volumes, ollama

### Community 85 - "london.py"
Cohesion: 0.14
Nodes (17): test_datagovmy_adapter_month_factors(), test_london_adapter_profiles_and_canonical_tables(), _columns(), convert(), month_factors(), month_factors_from(), processed(), raw_dir() (+9 more)

### Community 86 - "build_zone_inputs"
Cohesion: 0.24
Nodes (4): test_FR_DI_07_district_weather_loaded_and_used(), recorded_params(), build_zone_inputs(), LossParams

### Community 87 - "numpy"
Cohesion: 0.19
Nodes (6): _bump(), daily_levels(), household_load_kw(), london_shapes(), _night_block(), synthetic_shapes()

### Community 88 - "api.js"
Cohesion: 0.22
Nodes (10): ApiError, listeners, setSession(), signIn(), signOut(), token, user, HOME (+2 more)

### Community 89 - "secureStore.js"
Cohesion: 0.32
Nodes (13): cryptoKey(), enforceMaxAge(), get(), keys(), MAX_AGE_MS, openDb(), put(), rawDelete() (+5 more)

### Community 90 - "solve"
Cohesion: 0.17
Nodes (4): FlowResult, _phase_shares(), solve(), ZoneNetwork

### Community 91 - "VoltGuard AI R0: review and end-to-end test report"
Cohesion: 0.20
Nodes (9): 1. Does the build meet the SRS and SDD?, 2. End-to-end test: every use case, every account, 3. Bugs found and fixed, 4. Remaining unfinished task: done, 5. Suggested improvements, 6. How to repeat the test, Features, Usability (high value, low effort first) (+1 more)

### Community 92 - "pipeline.py"
Cohesion: 0.16
Nodes (14): copy_in(), copy_out(), _csv(), ensure_models(), ensure_simulated(), _jsonable(), load_into_db(), _num() (+6 more)

### Community 93 - "simulator.py"
Cohesion: 0.09
Nodes (30): _run(), test_FR_DI_01_readings_round_trip_match_generator(), test_FR_ZD_02_large_load_priority(), test_FR_ZD_05_many_conventional_meters_still_flag_mining(), test_FR_ML_03_missing_data_and_drift_raise_alerts(), cmd_simulate(), fake_address(), fake_name() (+22 more)

### Community 94 - "login"
Cohesion: 0.09
Nodes (19): login(), reporting_case(), test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act(), test_FR_AG_01_FR_UI_05_two_approvals_then_pdf_with_details(), test_FR_AG_01_manager_sees_evidence_photos_only_for_export_approval(), test_FR_AG_03_answers_carry_a_chart_and_a_sentence_from_the_rows(), test_FR_AG_03_chatbot_answers_with_query_and_refuses_other_region(), test_FR_AG_04_field_assistant_cites_or_says_not_found() (+11 more)

### Community 95 - "VoltGuard AI: UI and UX design requirements (R0 → R1 redesign)"
Cohesion: 0.20
Nodes (9): 1. Users and their first question, 2. Design principles, 3. Visual language and design tokens, 4. Components, 5. Screens, 6. Accessibility and language (must pass before release), 7. How to build it (suggested tools), 9. Acceptance checks for the redesign (+1 more)

### Community 96 - "scoring.py"
Cohesion: 0.38
Nodes (3): Reason, Score, score_premise()

### Community 97 - "sunshine_hours"
Cohesion: 0.12
Nodes (16): district, sunshine_hours, temperature_c, required, type, columns, max, min (+8 more)

### Community 98 - "VoltGuard AI (R0 prototype)"
Cohesion: 0.22
Nodes (8): Data modes, Development and tests, Documents, Public link for judges (Cloudflare Tunnel), Quick start (Windows laptop), Status: what works, what does not, what needs TNB, Telegram dispatch bot, VoltGuard AI (R0 prototype)

### Community 99 - "Deviations from the SDD"
Cohesion: 0.25
Nodes (6): change_point(), Agents and RAG, Data, Deviations from the SDD, Library swaps, Lite-profile swaps (prompt 7.2)

### Community 100 - "config.py"
Cohesion: 0.13
Nodes (17): _timers(), cmd_detect(), admin_database_url(), config_dir(), data_path(), data_root(), data_sources(), database_url() (+9 more)

### Community 101 - "engine.py"
Cohesion: 0.21
Nodes (8): BalanceResult, PremiseResult, ZoneResult, build_features(), _clip01(), _drop_share(), FeatureSet, VoltageResult

### Community 104 - "command"
Cohesion: 0.12
Nodes (18): demo_passwords(), cmd_simreport(), cmd_train_models(), cmd_tune(), command(), main(), cmd_activate(), cmd_convert() (+10 more)

### Community 105 - "demo.py"
Cohesion: 0.21
Nodes (6): generate_password(), cmd_demo(), prewarm(), print_script(), reset_rehearsal(), seed_users()

### Community 106 - "rag.py"
Cohesion: 0.16
Nodes (14): quote_retrieved(), case_summary_text(), collect_documents(), _front_matter(), index_case_summaries(), index_documents(), _pdf_text(), _sections_legal() (+6 more)

### Community 107 - "Manager dashboard in Power BI (R0)"
Cohesion: 0.25
Nodes (7): Connect Power BI Desktop, Manager dashboard in Power BI (R0), Page 1: Network overview, Page 2: Leaking zones, Page 3: Cases and hit rates, R1, Views

### Community 108 - "test_telegram.py"
Cohesion: 0.27
Nodes (7): message(), new_case(), test_FR_AD_01_chat_is_for_supervisors_and_inspectors(), test_FR_AG_02_cannot_attend_tells_the_supervisor(), test_FR_AG_02_decision_on_the_case_page_closes_the_chat_buttons(), test_FR_AG_02_real_bot_links_a_chat_and_answers_a_button(), test_FR_AG_02_supervisor_approves_and_team_answers_from_the_chat()

### Community 109 - "Upload area: bring your own datasets"
Cohesion: 0.40
Nodes (4): How to upload, Upload area: bring your own datasets, Versions, What validation checks

### Community 110 - "llm.py"
Cohesion: 0.22
Nodes (10): available(), check_prompt(), complete(), Completion, mode(), PromptBlocked, health(), agent_status() (+2 more)

### Community 111 - "Hand-off: VoltGuard AI R0 build"
Cohesion: 0.20
Nodes (9): Auto-generated state (scripts/handoff.sh), Decisions to keep, Docker check (this session), File tree, Hand-off: VoltGuard AI R0 build, How to resume in a new session, Known issues, Review round (after the team's laptop test, 2026-10-27) (+1 more)

### Community 112 - "pg_server.py"
Cohesion: 0.27
Nodes (3): _bin(), _free_port(), TempPostgres

### Community 113 - "documents"
Cohesion: 0.25
Nodes (7): documents, id, manual, owner, role_scope, title, url

### Community 114 - "voltguard_guide.md"
Cohesion: 0.29
Nodes (6): 1. What a flagged zone means, 2. Flat 24/7 gap, 3. Risk scores and reasons, 4. Voltage evidence, 5. Routine meter checks, 6. Recording outcomes

### Community 115 - "audit.py"
Cohesion: 0.16
Nodes (10): audit_verify(), anchor_dir(), row_hash(), row_text(), verify(), VerifyResult, write_anchor(), cmd_anchor() (+2 more)

### Community 116 - "storage.py"
Cohesion: 0.27
Nodes (6): exists(), _fernet(), get(), _path(), put(), main()

### Community 117 - "field_evidence_checklist.md"
Cohesion: 0.50
Nodes (3): At the meter, Before the visit, Recording

### Community 121 - "fetch_datasets.py"
Cohesion: 0.33
Nodes (5): apply_overrides(), fetch_kaggle(), fetch_url(), main(), manual()

### Community 123 - "session"
Cohesion: 0.22
Nodes (14): session(), numbered(), RouteMap(), body_(), DONE, linkify(), TelegramChat(), press() (+6 more)

### Community 124 - "lat"
Cohesion: 0.40
Nodes (5): lat, max, min, required, type

### Community 125 - "canonical.py"
Cohesion: 0.38
Nodes (3): Column, Table, _table()

### Community 127 - "VoltGuard AI demo script (R0)"
Cohesion: 0.29
Nodes (6): Backup steps (for questions or a recorded clip), If something goes wrong, Live steps (5 minutes), Rehearsal checklist (prompt 7.5), The day before, VoltGuard AI demo script (R0)

### Community 130 - "jobs.py"
Cohesion: 0.16
Nodes (10): dataset_report(), job_status(), jobs_running(), acknowledge(), retrain(), _run(), running(), status() (+2 more)

### Community 134 - "Assistant.jsx"
Cohesion: 0.29
Nodes (8): QueryChart(), Answer(), download(), Assistant(), ask(), csv(), EXAMPLES, EXTRA_PAGES

### Community 137 - "digest.py"
Cohesion: 0.10
Nodes (16): alerts(), models(), weekly(), weekly_pdf(), weekly_send(), _chromium(), html_to_pdf(), _bars() (+8 more)

### Community 139 - "route"
Cohesion: 0.50
Nodes (4): route, road_factor, speed_kmh, visit_minutes

## Knowledge Gaps
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Caller` connect `Caller` to `db.py`, `jobs.py`, `digest.py`, `cases.py`, `route.py`, `local_stack.py`, `routes_zones.py`, `thresholds`, `auth.py`, `report.py`, `guardrails.py`, `admin_connection`, `Caller`, `notify.py`, `json`, `test_api_security.py`, `re`, `rag.py`, `llm.py`, `audit.py`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Are the 93 inferred relationships involving `Caller` (e.g. with `LocalStack` and `ask()`) actually correct?**
  _`Caller` has 93 INFERRED edges - model-reasoned connections that need verification._
- **Should `db.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08571428571428572 - nodes in this community are weakly interconnected._
- **Why does `date` connect `routes_zones.py` to `sunshine_hours`, `evaluation.py`, `test_data_layer.py`, `numpy`, `route.py`, `build_zone_inputs`, `simulator.py`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Are the 69 inferred relationships involving `Requirements` (e.g. with `test_NFR_02_NFR_13_pages_load_fast_and_phone_view_in_bahasa_melayu()` and `test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act()`) actually correct?**
  _`Requirements` has 69 INFERRED edges - model-reasoned connections that need verification._
- **Should `VoltGuard AI: Software Design Document (SDD)` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Why does `columns` connect `sunshine_hours` to `tables`, `routes_zones.py`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._