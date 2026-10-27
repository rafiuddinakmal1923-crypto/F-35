# Graph Report - F-35  (2026-10-27)

## Corpus Check
- 141 files · ~96,000 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: .csv 17, (none) 8, .example 1)

## Summary
- 1899 nodes · 4394 edges · 126 communities (114 shown, 12 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 252 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `98abea42`
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
- dispatch.py
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
- storage.py
- columns
- columns
- embed.py
- month
- voltage_v
- distance_m
- evaluation.py
- report.py
- api
- environment
- capacity_kva
- routes_admin.py
- App.jsx
- voltage_v
- anomaly.py
- conftest.py
- routes_models.py
- guardrails.py
- command
- notify.py
- .start
- pattern.py
- numpy
- Caller
- auth.py
- sources.py
- json
- seed.py
- test_api_security.py
- monitoring.py
- re
- voltguard/__init__.py
- ollama
- london.py
- Graph summary
- numpy
- case_premise
- secureStore.js
- solve
- llm.py
- pipeline.py
- engine.py
- login
- pdf.py
- scoring.py
- sunshine_hours
- VoltGuard AI (R0 prototype)
- Deviations from the SDD
- data_root
- re
- sw.js
- ingest.py
- routes_agents.py
- rag.py
- Manager dashboard in Power BI (R0)
- thresholds
- Upload area: bring your own datasets
- scrubber.py
- create_app
- pathlib
- documents
- voltguard_guide.md
- audit.py
- admin_connection
- field_evidence_checklist.md
- Documents for the field assistant and the report agent (RAG)
- psycopg
- Traceability
- VoltGuard AI demo script (R0)
- MODELS.md
- backtest_report.md

## God Nodes (most connected - your core abstractions)
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

## Surprising Connections (you probably didn't know these)
- `Docker check (this session)` --references--> `api()`  [INFERRED]
  HANDOFF.md → backend/tests/conftest.py
- `Quick start (Windows laptop)` --references--> `api()`  [INFERRED]
  README.md → backend/tests/conftest.py
- `7.2 Compose profiles` --references--> `api()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/tests/conftest.py
- `3.1 Canonical schema (the only thing the pipeline reads)` --references--> `duty_roster()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/voltguard/data/simulator.py
- `Library swaps` --references--> `change_point()`  [INFERRED]
  DEVIATIONS.md → backend/voltguard/detection/balance.py

## Import Cycles
- None detected.

## Communities (126 total, 12 thin omitted)

### Community 0 - "deps.py"
Cohesion: 0.15
Nodes (11): ApiError, caller(), conflict(), connection(), forbidden(), require(), check(), me() (+3 more)

### Community 1 - "simulator.py"
Cohesion: 0.11
Nodes (29): _run(), test_detection_creates_no_cases(), test_FR_DI_01_readings_round_trip_match_generator(), test_FR_DI_02_voltage_for_smart_meters_only(), test_FR_DI_04_every_meter_linked_to_one_transformer(), test_FR_DI_06_missing_day_flags_meter(), test_FR_ZD_02_large_load_priority(), test_FR_ZD_05_many_conventional_meters_still_flag_mining() (+21 more)

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
Cohesion: 0.28
Nodes (10): command(), cmd_anchor(), cmd_fetch_models(), cmd_index_docs(), cmd_migrate(), cmd_pipeline(), cmd_retrain(), cmd_seed() (+2 more)

### Community 7 - "tables"
Cohesion: 0.08
Nodes (24): downloads, london, sgcc, london, households, region, zone_size, pattern_training (+16 more)

### Community 8 - "Build the VoltGuard AI prototype (R0)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "test_data_layer.py"
Cohesion: 0.19
Nodes (13): isolated(), small_scenario(), test_bad_upload_is_rejected_with_reasons(), test_column_map_units_and_timezone(), test_FR_DI_06_upload_with_missing_intervals_flags_meter(), test_missing_voltage_and_phase_use_fallbacks(), test_switch_to_uploaded_dataset_without_code_changes(), test_upload_templates_are_a_valid_dataset() (+5 more)

### Community 10 - "engine.py"
Cohesion: 0.22
Nodes (7): network_for(), technical_loss(), _fit_group(), locate(), _relative_voltage(), VoltageResult, ZoneInput

### Community 11 - "teams"
Cohesion: 0.12
Nodes (16): demo_seed, demo_zone, regions, code, name, teams, base_lat, base_lon (+8 more)

### Community 12 - "Requirements"
Cohesion: 0.11
Nodes (20): test_NFR_15_every_planted_detail_scrubbed_from_seeded_notes(), test_NFR_15_model_output_with_personal_details_is_blocked(), test_FR_AD_01_database_enforces_region_and_pii_rules(), test_FR_PS_07_suspects_reasons_add_up(), test_FR_IW_01_case_job_creates_threshold_cases(), test_FR_IW_01_manual_cases_and_only_supervisor_assigns(), test_FR_DI_03_supply_equals_homes_plus_loss_plus_taps(), test_FR_PS_01_every_premise_in_flagged_zone_scored() (+12 more)

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

### Community 20 - "cases.py"
Cohesion: 0.17
Nodes (21): audit(), add_photo(), assign(), _assign(), _case(), case_detail(), CaseError, claim() (+13 more)

### Community 21 - "config.example.yml"
Cohesion: 0.33
Nodes (5): credentials-file, ingress, hostname, service, tunnel

### Community 22 - "dispatch.py"
Cohesion: 0.22
Nodes (5): haversine_km(), roster_date(), run_reminders(), suggest(), _timers()

### Community 23 - "test_demo_rehearsal.py"
Cohesion: 0.16
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

### Community 34 - "config.py"
Cohesion: 0.27
Nodes (9): health(), admin_database_url(), database_url(), demo_mode(), _env(), jwt_secret(), llm_mode(), public_base_url() (+1 more)

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
Cohesion: 0.09
Nodes (8): lifespan(), close_pools(), migrate(), _role_password(), register(), _safe(), start(), stop()

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
Cohesion: 0.11
Nodes (19): installed_on, meter_id, meter_type, read_frequency, required, type, columns, description (+11 more)

### Community 48 - "columns"
Cohesion: 0.12
Nodes (16): columns, event_date, event_id, event_type, premise_id, required, type, required (+8 more)

### Community 49 - "tables"
Cohesion: 0.15
Nodes (12): description, key, description, key, description, key, tables, account_event (+4 more)

### Community 50 - "columns"
Cohesion: 0.15
Nodes (13): required, type, address, contact, holder_name, required, type, columns (+5 more)

### Community 51 - "storage.py"
Cohesion: 0.22
Nodes (7): generate_password(), exists(), _fernet(), get(), _path(), put(), main()

### Community 52 - "columns"
Cohesion: 0.07
Nodes (28): dtm_accuracy_class, has_dtm, lat, loss_params, region, description, max, min (+20 more)

### Community 53 - "columns"
Cohesion: 0.07
Nodes (30): feeder_branch, lon, phase, premise_type, street_seq, tariff, description, required (+22 more)

### Community 54 - "embed.py"
Cohesion: 0.20
Nodes (9): cosine(), download(), embed(), _hash_embed(), keyword_overlap(), _model_dir(), model_name(), _onnx() (+1 more)

### Community 55 - "month"
Cohesion: 0.13
Nodes (15): kwh, month, description, max, min, required, type, unit (+7 more)

### Community 56 - "voltage_v"
Cohesion: 0.11
Nodes (18): kwh_supplied, transformer_id, ts, max, min, required, type, unit (+10 more)

### Community 57 - "distance_m"
Cohesion: 0.29
Nodes (7): distance_m, description, max, min, required, type, unit

### Community 58 - "evaluation.py"
Cohesion: 0.14
Nodes (14): cmd_simreport(), cmd_tune(), deep_merge(), heldout_scenario(), evaluate(), _fast_scores(), _fmt(), run_scenario() (+6 more)

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

### Community 63 - "routes_admin.py"
Cohesion: 0.19
Nodes (11): bad_request(), not_found(), audit_log(), dataset_activate(), dataset_preview(), dataset_report(), job_status(), jobs_running() (+3 more)

### Community 64 - "App.jsx"
Cohesion: 0.05
Nodes (109): leaflet, react, react-dom, react-leaflet, react-router-dom, vite, @vitejs/plugin-react, dependencies (+101 more)

### Community 65 - "voltage_v"
Cohesion: 0.13
Nodes (15): quality_flag, voltage_v, columns, description, key, allowed, description, required (+7 more)

### Community 66 - "anomaly.py"
Cohesion: 0.19
Nodes (10): cmd_train_models(), Autoencoder, load(), model_path(), save(), train(), train_from_simulation(), week_vector() (+2 more)

### Community 67 - "conftest.py"
Cohesion: 0.19
Nodes (9): api(), cfg(), demo_run(), demo_run_all(), demo_sim(), models(), pg(), run_tables() (+1 more)

### Community 68 - "routes_models.py"
Cohesion: 0.20
Nodes (5): acknowledge(), alerts(), models(), retrain(), versions()

### Community 69 - "guardrails.py"
Cohesion: 0.19
Nodes (8): allow(), asks_forbidden_action(), check_output(), OutputBlocked, ToolNotAllowed, answer(), search(), similar_cases()

### Community 70 - "command"
Cohesion: 0.20
Nodes (6): demo_passwords(), cmd_demo(), prewarm(), print_script(), reset_rehearsal(), seed_users()

### Community 71 - "notify.py"
Cohesion: 0.24
Nodes (6): BlockedMessage, case_link(), _chat_ids(), compose(), output_check(), send()

### Community 72 - ".start"
Cohesion: 0.27
Nodes (3): _bin(), _free_port(), TempPostgres

### Community 73 - "pattern.py"
Cohesion: 0.15
Nodes (13): auc(), load(), model_path(), PatternModel, sgcc_training_set(), synthetic_training_set(), train(), train_default() (+5 more)

### Community 74 - "numpy"
Cohesion: 0.20
Nodes (11): balance_zone(), BalanceResult, change_point(), data_quality_flags(), _days_in(), estimate_conventional(), similar_groups(), build_features() (+3 more)

### Community 75 - "Caller"
Cohesion: 0.17
Nodes (19): assign(), Assignment, _call(), case_version(), claim_case(), create_case(), decide(), Decision (+11 more)

### Community 76 - "auth.py"
Cohesion: 0.19
Nodes (11): current_session(), sign_in(), SignIn, AuthError, check_password(), decode_token(), hash_password(), issue_token() (+3 more)

### Community 77 - "sources.py"
Cohesion: 0.15
Nodes (16): datasets(), activate_dataset(), cmd_activate(), next_version(), preview(), dataset_versions(), datasets_root(), load_active_tables() (+8 more)

### Community 78 - "json"
Cohesion: 0.28
Nodes (7): fake_names(), find(), test_FR_AG_02_dispatch_suggestion_claim_and_approval(), test_FR_IW_02_FR_IW_03_FR_IW_04_outcomes_status_and_labels(), test_FR_IW_05_random_sample_presented_as_routine_check(), test_FR_UI_03_details_only_for_case_roles(), test_FR_UI_03_unclaimed_case_masked_for_every_analyst()

### Community 79 - "seed.py"
Cohesion: 0.18
Nodes (6): quote_retrieved(), case_summary_text(), index_case_summaries(), predraft_demo_report(), seed_closed_cases(), seed_demo_content()

### Community 80 - "test_api_security.py"
Cohesion: 0.18
Nodes (8): fake_names(), test_data_manager_upload_validates_and_versions(), test_FR_AD_01_role_and_region_refusals(), test_FR_UI_01_overview_zone_level_in_gap_order(), test_FR_UI_02_zone_view_balance_and_profile(), test_FR_UI_03_details_masked_before_a_case_opens(), test_FR_UI_04_district_filter(), test_NFR_16_remote_sign_out()

### Community 81 - "monitoring.py"
Cohesion: 0.24
Nodes (5): test_unusual_access_alert(), after_detection(), _alert(), check_unusual_access(), psi()

### Community 82 - "re"
Cohesion: 0.21
Nodes (9): ask(), _ask_model(), other_region_named(), parse(), parse_mock(), QueryError, _regions(), run_query() (+1 more)

### Community 83 - "voltguard/__init__.py"
Cohesion: 0.24
Nodes (4): cut(), known_cases_active(), known_cases_simulated(), main()

### Community 84 - "ollama"
Cohesion: 0.50
Nodes (4): image, restart, volumes, ollama

### Community 85 - "london.py"
Cohesion: 0.14
Nodes (16): test_datagovmy_adapter_month_factors(), _columns(), convert(), month_factors(), month_factors_from(), processed(), raw_dir(), _stamp() (+8 more)

### Community 86 - "Graph summary"
Cohesion: 0.20
Nodes (9): Auto-generated state (scripts/handoff.sh), Decisions to keep, Docker check (this session), File tree, Graph summary, Hand-off: VoltGuard AI R0 build, How to resume in a new session, Ideas for a next session (+1 more)

### Community 87 - "numpy"
Cohesion: 0.19
Nodes (6): _bump(), daily_levels(), household_load_kw(), london_shapes(), _night_block(), synthetic_shapes()

### Community 88 - "case_premise"
Cohesion: 0.42
Nodes (9): case_premise(), rank_of(), top_k(), test_FR_DI_05_tenancy_change_at_injected_thief(), test_FR_PS_02_voltage_locates_tap_on_its_phase(), test_FR_PS_04_timing_match_and_day_one_tap_in_top(), test_FR_PS_05_legitimate_patterns_tagged_not_top(), test_FR_PS_09_tenancy_change_alone_not_top_and_capped() (+1 more)

### Community 89 - "secureStore.js"
Cohesion: 0.32
Nodes (13): cryptoKey(), enforceMaxAge(), get(), keys(), MAX_AGE_MS, openDb(), put(), rawDelete() (+5 more)

### Community 90 - "solve"
Cohesion: 0.12
Nodes (8): test_FR_DI_07_district_weather_loaded_and_used(), recorded_params(), build_zone_inputs(), FlowResult, LossParams, _phase_shares(), solve(), ZoneNetwork

### Community 91 - "llm.py"
Cohesion: 0.29
Nodes (7): test_NFR_15_model_never_receives_personal_details(), available(), check_prompt(), complete(), Completion, mode(), PromptBlocked

### Community 92 - "pipeline.py"
Cohesion: 0.18
Nodes (13): active_sources(), copy_in(), copy_out(), _csv(), ensure_simulated(), _jsonable(), load_into_db(), _num() (+5 more)

### Community 93 - "engine.py"
Cohesion: 0.17
Nodes (5): fill_smart_readings(), DetectionRun, PremiseResult, run_zones(), ZoneResult

### Community 94 - "login"
Cohesion: 0.21
Nodes (10): login(), reporting_case(), test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act(), test_FR_AG_01_FR_UI_05_two_approvals_then_pdf_with_details(), test_FR_AG_03_chatbot_answers_with_query_and_refuses_other_region(), test_FR_AG_04_field_assistant_cites_or_says_not_found(), test_FR_AG_05_three_similar_closed_cases(), test_FR_AG_06_no_tools_to_act_and_requests_refused() (+2 more)

### Community 95 - "pdf.py"
Cohesion: 0.28
Nodes (4): test_FR_UI_05_pdf_fallback_without_a_browser(), _chromium(), _fpdf(), html_to_pdf()

### Community 96 - "scoring.py"
Cohesion: 0.36
Nodes (4): Reason, reason_text(), Score, score_premise()

### Community 97 - "sunshine_hours"
Cohesion: 0.11
Nodes (19): district, sunshine_hours, temperature_c, required, type, columns, description, key (+11 more)

### Community 98 - "VoltGuard AI (R0 prototype)"
Cohesion: 0.25
Nodes (7): Data modes, Development and tests, Documents, Public link for judges (Cloudflare Tunnel), Quick start (Windows laptop), Status: what works, what does not, what needs TNB, VoltGuard AI (R0 prototype)

### Community 99 - "Deviations from the SDD"
Cohesion: 0.33
Nodes (5): Agents and RAG, Data, Deviations from the SDD, Library swaps, Lite-profile swaps (prompt 7.2)

### Community 100 - "data_root"
Cohesion: 0.18
Nodes (12): test_london_adapter_profiles_and_canonical_tables(), test_sgcc_adapter_feeds_pattern_model(), cmd_detect(), config_dir(), data_path(), data_root(), data_sources(), demo_config() (+4 more)

### Community 101 - "re"
Cohesion: 0.52
Nodes (4): database_name(), expand(), main(), requirements()

### Community 104 - "ingest.py"
Cohesion: 0.13
Nodes (14): schema_document(), build_tables(), _checksum(), cmd_convert(), cmd_ingest(), cmd_sources(), cmd_upload_kit(), context_for() (+6 more)

### Community 105 - "routes_agents.py"
Cohesion: 0.19
Nodes (13): agent_status(), approve_content(), approve_export(), _call(), Chat, chat(), draft_report(), get_report() (+5 more)

### Community 106 - "rag.py"
Cohesion: 0.19
Nodes (13): collect_documents(), extractive_answer(), _front_matter(), index_documents(), Passage, _pdf_text(), _sections_legal(), _sections_markdown() (+5 more)

### Community 107 - "Manager dashboard in Power BI (R0)"
Cohesion: 0.29
Nodes (6): Connect Power BI Desktop, Manager dashboard in Power BI (R0), Page 1: Network overview, Page 2: Leaking zones, R1, Views

### Community 108 - "thresholds"
Cohesion: 0.40
Nodes (5): get_thresholds(), overrides(), save(), thresholds(), validate_change()

### Community 109 - "Upload area: bring your own datasets"
Cohesion: 0.22
Nodes (6): district_weather(), How to upload, Upload area: bring your own datasets, Versions, What to upload, What validation checks

### Community 110 - "scrubber.py"
Cohesion: 0.25
Nodes (5): engine(), _known_patterns(), _presidio_analyzer(), scrub(), ScrubResult

### Community 112 - "pathlib"
Cohesion: 0.11
Nodes (7): _call(), apply_overrides(), fetch_kaggle(), fetch_url(), main(), manual(), main()

### Community 113 - "documents"
Cohesion: 0.25
Nodes (7): documents, id, manual, owner, role_scope, title, url

### Community 114 - "voltguard_guide.md"
Cohesion: 0.29
Nodes (6): 1. What a flagged zone means, 2. Flat 24/7 gap, 3. Risk scores and reasons, 4. Voltage evidence, 5. Routine meter checks, 6. Recording outcomes

### Community 115 - "audit.py"
Cohesion: 0.18
Nodes (10): test_FR_AD_02_NFR_12_audit_logged_and_tampering_detected(), audit_verify(), anchor_dir(), row_hash(), row_text(), verify(), VerifyResult, write_anchor() (+2 more)

### Community 116 - "admin_connection"
Cohesion: 0.15
Nodes (11): create_cases(), run(), admin_connection(), app_connection(), _pool(), _run(), running(), status() (+3 more)

### Community 117 - "field_evidence_checklist.md"
Cohesion: 0.50
Nodes (3): At the meter, Before the visit, Recording

### Community 121 - "psycopg"
Cohesion: 0.24
Nodes (8): test_FR_AD_03_threshold_change_applies_on_rerun(), test_jobs_run_detection_creates_no_cases(), test_FR_AG_02_reminder_then_escalation_on_demo_timers(), test_FR_IW_05_random_sample_from_flagged_zones_only(), test_FR_IW_04_no_access_never_a_label(), test_FR_UI_01_powerbi_role_reads_rpt_views_only(), test_NFR_07_rpt_views_hold_no_premise_ids_or_personal_details(), main()

### Community 127 - "VoltGuard AI demo script (R0)"
Cohesion: 0.29
Nodes (6): Backup steps (for questions or a recorded clip), If something goes wrong, Live steps (5 minutes), Rehearsal checklist (prompt 7.5), The day before, VoltGuard AI demo script (R0)

## Knowledge Gaps
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `date` connect `routes_zones.py` to `simulator.py`, `sunshine_hours`, `conftest.py`, `numpy`, `sources.py`, `dispatch.py`, `solve`?**
  _High betweenness centrality (0.181) - this node is a cross-community bridge._
- **Are the 78 inferred relationships involving `Caller` (e.g. with `LocalStack` and `ask()`) actually correct?**
  _`Caller` has 78 INFERRED edges - model-reasoned connections that need verification._
- **Should `deps.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1471861471861472 - nodes in this community are weakly interconnected._
- **Why does `columns` connect `sunshine_hours` to `routes_zones.py`?**
  _High betweenness centrality (0.181) - this node is a cross-community bridge._
- **Are the 61 inferred relationships involving `Requirements` (e.g. with `test_NFR_02_NFR_13_pages_load_fast_and_phone_view_in_bahasa_melayu()` and `test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act()`) actually correct?**
  _`Requirements` has 61 INFERRED edges - model-reasoned connections that need verification._
- **Should `simulator.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11184939091915837 - nodes in this community are weakly interconnected._
- **Why does `Caller` connect `Caller` to `deps.py`, `test_data_layer.py`, `Requirements`, `cases.py`, `test_demo_rehearsal.py`, `routes_zones.py`, `db.py`, `report.py`, `routes_admin.py`, `routes_models.py`, `guardrails.py`, `.start`, `auth.py`, `sources.py`, `json`, `test_api_security.py`, `re`, `Graph summary`, `routes_agents.py`, `rag.py`, `thresholds`, `pathlib`, `audit.py`, `admin_connection`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._