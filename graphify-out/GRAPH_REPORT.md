# Graph Report - F-35  (2026-10-27)

## Corpus Check
- 162 files · ~119,467 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 31 file(s) not represented in the graph (top: .csv 17, (none) 8, .example 1)

## Summary
- 2192 nodes · 5181 edges · 126 communities (113 shown, 13 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 285 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f1de3c30`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .start
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
- os
- Simulation report
- VoltGuard AI R0: build plan
- scrape_configs
- thresholds.yaml
- cases.py
- config.example.yml
- config.py
- local_stack.py
- dispatch
- features
- routes_admin.py
- make.ps1
- cases
- db.py
- voltage
- handoff.sh
- tunnel.sh
- worker
- re
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
- voltguard/__init__.py
- App.jsx
- voltage_v
- guardrails.py
- conftest.py
- package.json
- pattern.py
- request
- admin_connection
- Premise.jsx
- notify.py
- engine.py
- voltguard/__init__.py
- anomaly.py
- sources.py
- answer
- create_app
- login
- Build the Power BI dashboard with Claude on your laptop
- re
- scripts
- ollama
- london.py
- date
- profiles.py
- api.js
- secureStore.js
- balance.py
- VoltGuard AI R0: review and end-to-end test report
- pipeline.py
- simulator.py
- VoltGuard AI: UI and UX design requirements (R0 → R1 redesign)
- learning.py
- sunshine_hours
- VoltGuard AI (R0 prototype)
- scoring.py
- sw.js
- cli.py
- seed.py
- rag.py
- Manager dashboard in Power BI (R0)
- Upload area: bring your own datasets
- llm.py
- Hand-off: VoltGuard AI R0 build
- Cases.jsx
- documents
- voltguard_guide.md
- audit.py
- field_evidence_checklist.md
- Documents for the field assistant and the report agent (RAG)
- Deviations from the SDD
- pipeline
- Traceability
- VoltGuard AI demo script (R0)
- MODELS.md
- backtest_report.md
- Weekly.jsx
- digest.py
- route

## God Nodes (most connected - your core abstractions)
1. `Caller` - 127 edges
2. `Requirements` - 72 edges
3. `login()` - 56 edges
4. `audit()` - 43 edges
5. `t()` - 42 edges
6. `admin_connection()` - 38 edges
7. `get()` - 34 edges
8. `shot()` - 33 edges
9. `run_detection()` - 30 edges
10. `request()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Requirements` --references--> `test_NFR_15_every_planted_detail_scrubbed_from_seeded_notes()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_agents.py
- `3.1 Canonical schema (the only thing the pipeline reads)` --references--> `duty_roster()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/voltguard/data/simulator.py
- `Library swaps` --references--> `change_point()`  [INFERRED]
  DEVIATIONS.md → backend/voltguard/detection/balance.py
- `Review round (after the team's laptop test, 2026-10-27)` --references--> `QueryChart()`  [INFERRED]
  HANDOFF.md → web/src/components/Charts.jsx
- `2. Design principles` --references--> `t()`  [INFERRED]
  docs/UI_UX_DESIGN_REQUIREMENTS.md → web/src/i18n.js

## Import Cycles
- None detected.

## Communities (126 total, 13 thin omitted)

### Community 0 - ".start"
Cohesion: 0.16
Nodes (7): _bin(), _free_port(), TempPostgres, close_pools(), migrate(), _role_password(), cmd_migrate()

### Community 1 - "get"
Cohesion: 0.17
Nodes (25): get(), put(), session(), useBadges(), ErrorBox(), useLoad(), body_(), DONE (+17 more)

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
Cohesion: 0.18
Nodes (11): cmd_tune(), evaluate(), _fast_scores(), _fmt(), run_scenario(), simulation_report(), stress_scenarios(), summarise() (+3 more)

### Community 7 - "tables"
Cohesion: 0.08
Nodes (24): downloads, london, sgcc, london, households, region, zone_size, pattern_training (+16 more)

### Community 8 - "Build the VoltGuard AI prototype (R0)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "test_data_layer.py"
Cohesion: 0.20
Nodes (14): isolated(), small_scenario(), test_bad_upload_is_rejected_with_reasons(), test_column_map_units_and_timezone(), test_FR_DI_06_upload_with_missing_intervals_flags_meter(), test_london_adapter_profiles_and_canonical_tables(), test_missing_voltage_and_phase_use_fallbacks(), test_switch_to_uploaded_dataset_without_code_changes() (+6 more)

### Community 10 - "e2e_use_cases.py"
Cohesion: 0.08
Nodes (48): adm_data(), adm_settings(), adm_upload(), api(), ask(), bm(), check(), desk() (+40 more)

### Community 11 - "teams"
Cohesion: 0.12
Nodes (16): demo_seed, demo_zone, regions, code, name, teams, base_lat, base_lon (+8 more)

### Community 12 - "Requirements"
Cohesion: 0.13
Nodes (32): case_premise(), rank_of(), top_k(), test_FR_AD_01_database_enforces_region_and_pii_rules(), test_datagovmy_adapter_month_factors(), test_detection_creates_no_cases(), test_FR_DI_01_readings_round_trip_match_generator(), test_FR_DI_02_voltage_for_smart_meters_only() (+24 more)

### Community 13 - "weights"
Cohesion: 0.10
Nodes (20): _tuning, objective, seed, split, tuned_at, zones, weights, anomaly (+12 more)

### Community 14 - "zone"
Cohesion: 0.18
Nodes (11): zone, change_min_segment_days, change_min_shift_share, consecutive_days, conventional_daily_cv, flat_cv, large_load_share, loss_model_error_share (+3 more)

### Community 15 - "os"
Cohesion: 0.15
Nodes (7): _call(), apply_overrides(), fetch_kaggle(), fetch_url(), main(), manual(), main()

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
Cohesion: 0.18
Nodes (10): monitoring, drift_psi_alert, min_interval_completeness, penalties, ev_charging, solar, vacancy, tenancy (+2 more)

### Community 20 - "cases.py"
Cohesion: 0.15
Nodes (23): audit(), add_photo(), assign(), _assign(), _case(), case_detail(), CaseError, claim() (+15 more)

### Community 21 - "config.example.yml"
Cohesion: 0.33
Nodes (5): credentials-file, ingress, hostname, service, tunnel

### Community 22 - "config.py"
Cohesion: 0.05
Nodes (40): test_sgcc_adapter_feeds_pattern_model(), test_FR_AG_02_team_route_with_navigation_and_limits(), test_route_order_beats_nearest_neighbour_and_is_close_to_the_best(), haversine_km(), roster_date(), run_reminders(), suggest(), _timers() (+32 more)

### Community 23 - "local_stack.py"
Cohesion: 0.13
Nodes (11): run_job_and_wait(), sign_in(), stack(), test_demo_live_steps_1_to_7(), test_NFR_02_NFR_13_pages_load_fast_and_phone_view_in_bahasa_melayu(), api_login(), sign_in(), stack() (+3 more)

### Community 24 - "dispatch"
Cohesion: 0.40
Nodes (5): dispatch, demo_escalation_minutes, demo_reminder_minutes, escalation_hours, reminder_hours

### Community 25 - "features"
Cohesion: 0.40
Nodes (5): features, history_weeks, recent_days, timing_tau_days, zero_kwh

### Community 26 - "routes_admin.py"
Cohesion: 0.10
Nodes (18): audit_log(), audit_verify(), dataset_activate(), dataset_preview(), dataset_report(), get_thresholds(), job_status(), jobs_running() (+10 more)

### Community 28 - "cases"
Cohesion: 0.50
Nodes (4): cases, case_threshold, max_cases_per_zone, random_sample_per_zone

### Community 29 - "db.py"
Cohesion: 0.10
Nodes (6): lifespan(), register(), _safe(), start(), stop(), stop_polling()

### Community 30 - "voltage"
Cohesion: 0.50
Nodes (4): voltage, min_drop_v, proximity_scale_m, window_days

### Community 33 - "worker"
Cohesion: 0.17
Nodes (13): build, context, dockerfile, web, worker, build, restart, build (+5 more)

### Community 34 - "re"
Cohesion: 0.27
Nodes (6): _sentences(), database_name(), main(), expand(), main(), requirements()

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
Cohesion: 0.15
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

### Community 51 - "auth.py"
Cohesion: 0.14
Nodes (14): sign_in(), SignIn, AuthError, check_password(), generate_password(), hash_password(), issue_token(), record_failure() (+6 more)

### Community 52 - "columns"
Cohesion: 0.07
Nodes (28): dtm_accuracy_class, has_dtm, lat, loss_params, region, description, max, min (+20 more)

### Community 53 - "columns"
Cohesion: 0.07
Nodes (30): feeder_branch, lon, phase, premise_type, street_seq, tariff, description, required (+22 more)

### Community 54 - "embed.py"
Cohesion: 0.19
Nodes (9): cosine(), download(), embed(), _hash_embed(), _model_dir(), model_name(), _onnx(), words() (+1 more)

### Community 55 - "month"
Cohesion: 0.13
Nodes (15): kwh, month, description, max, min, required, type, unit (+7 more)

### Community 56 - "voltage_v"
Cohesion: 0.11
Nodes (18): kwh_supplied, transformer_id, ts, max, min, required, type, unit (+10 more)

### Community 57 - "distance_m"
Cohesion: 0.29
Nodes (7): distance_m, description, max, min, required, type, unit

### Community 58 - "ingest.py"
Cohesion: 0.14
Nodes (13): command(), schema_document(), _checksum(), cmd_convert(), cmd_ingest(), cmd_sources(), cmd_upload_kit(), IngestResult (+5 more)

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

### Community 63 - "voltguard/__init__.py"
Cohesion: 0.07
Nodes (32): ApiError, bad_request(), caller(), conflict(), connection(), current_session(), forbidden(), not_found() (+24 more)

### Community 64 - "App.jsx"
Cohesion: 0.14
Nodes (30): onSessionChange(), App(), Guarded(), ICONS, ID_ROUTES, NAV, SearchBox(), Shell() (+22 more)

### Community 65 - "voltage_v"
Cohesion: 0.13
Nodes (15): quality_flag, voltage_v, columns, description, key, allowed, description, required (+7 more)

### Community 66 - "guardrails.py"
Cohesion: 0.31
Nodes (5): test_FR_AG_06_no_tools_to_act_and_requests_refused(), allow(), check_output(), OutputBlocked, ToolNotAllowed

### Community 67 - "conftest.py"
Cohesion: 0.15
Nodes (9): api(), cfg(), demo_run(), demo_run_all(), demo_sim(), models(), pg(), demo_users() (+1 more)

### Community 68 - "package.json"
Cohesion: 0.09
Nodes (27): @fontsource-variable/inter, leaflet, lucide-react, react, react-dom, react-leaflet, react-router-dom, vite (+19 more)

### Community 69 - "pattern.py"
Cohesion: 0.24
Nodes (9): auc(), load(), model_path(), PatternModel, sgcc_training_set(), synthetic_training_set(), train(), train_default() (+1 more)

### Community 70 - "request"
Cohesion: 0.14
Nodes (25): 8. Prompts, patch(), post(), request(), Masked(), press(), submit(), ago() (+17 more)

### Community 71 - "admin_connection"
Cohesion: 0.07
Nodes (27): test_unusual_access_alert(), chats(), link_code(), press(), Press, status(), unlink(), admin_connection() (+19 more)

### Community 72 - "Premise.jsx"
Cohesion: 0.23
Nodes (20): pollJob(), VoltageStrip(), Confidence(), fmt(), Help(), JobButton(), start(), Kpi() (+12 more)

### Community 73 - "notify.py"
Cohesion: 0.15
Nodes (12): public_base_url(), BlockedMessage, case_link(), _chat_ids(), compose(), keyboard(), output_check(), recipient_chats() (+4 more)

### Community 74 - "engine.py"
Cohesion: 0.12
Nodes (14): balance_zone(), BalanceResult, data_quality_flags(), estimate_conventional(), fill_smart_readings(), DetectionRun, PremiseResult, run_zones() (+6 more)

### Community 75 - "voltguard/__init__.py"
Cohesion: 0.10
Nodes (26): me(), users(), assign(), Assignment, _call(), case_version(), claim_case(), create_case() (+18 more)

### Community 76 - "anomaly.py"
Cohesion: 0.14
Nodes (11): cmd_train_models(), data_path(), Autoencoder, load(), model_path(), save(), train(), train_from_simulation() (+3 more)

### Community 77 - "sources.py"
Cohesion: 0.13
Nodes (17): datasets(), activate_dataset(), cmd_activate(), context_for(), next_version(), active_sources(), dataset_versions(), datasets_root() (+9 more)

### Community 78 - "answer"
Cohesion: 0.27
Nodes (6): keyword_overlap(), answer(), extractive_answer(), Passage, search(), similar_cases()

### Community 80 - "login"
Cohesion: 0.05
Nodes (50): login(), reporting_case(), test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act(), test_FR_AG_01_FR_UI_05_two_approvals_then_pdf_with_details(), test_FR_AG_01_manager_sees_evidence_photos_only_for_export_approval(), test_FR_AG_03_answers_carry_a_chart_and_a_sentence_from_the_rows(), test_FR_AG_03_chatbot_answers_with_query_and_refuses_other_region(), test_FR_AG_04_field_assistant_cites_or_says_not_found() (+42 more)

### Community 81 - "Build the Power BI dashboard with Claude on your laptop"
Cohesion: 0.33
Nodes (5): Before you start (5 minutes), Build the Power BI dashboard with Claude on your laptop, Check the result, If Claude cannot open Power BI, Prompt to paste into Claude (Cowork / Desktop on the laptop)

### Community 82 - "re"
Cohesion: 0.15
Nodes (13): ask(), _ask_model(), _chart_choice(), _num(), other_region_named(), parse(), parse_mock(), QueryError (+5 more)

### Community 83 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, preview, test

### Community 84 - "ollama"
Cohesion: 0.50
Nodes (4): image, restart, volumes, ollama

### Community 85 - "london.py"
Cohesion: 0.13
Nodes (16): data_root(), _columns(), convert(), month_factors(), month_factors_from(), processed(), raw_dir(), _stamp() (+8 more)

### Community 86 - "date"
Cohesion: 0.23
Nodes (9): latest_run_date(), _zone(), zone_balance(), zone_suspects(), zone_voltage(), zones(), date, required (+1 more)

### Community 87 - "profiles.py"
Cohesion: 0.14
Nodes (12): _bump(), daily_levels(), household_load_kw(), london_shapes(), _night_block(), synthetic_shapes(), change_point(), similar_groups() (+4 more)

### Community 88 - "api.js"
Cohesion: 0.22
Nodes (10): ApiError, listeners, setSession(), signIn(), signOut(), token, user, HOME (+2 more)

### Community 89 - "secureStore.js"
Cohesion: 0.32
Nodes (13): cryptoKey(), enforceMaxAge(), get(), keys(), MAX_AGE_MS, openDb(), put(), rawDelete() (+5 more)

### Community 90 - "balance.py"
Cohesion: 0.12
Nodes (9): recorded_params(), _days_in(), network_for(), technical_loss(), FlowResult, LossParams, _phase_shares(), solve() (+1 more)

### Community 91 - "VoltGuard AI R0: review and end-to-end test report"
Cohesion: 0.18
Nodes (10): 1. Does the build meet the SRS and SDD?, 2. End-to-end test: every use case, every account, 3. Bugs found and fixed, 4. Remaining unfinished task: done, 5. Suggested improvements, 6. How to repeat the test, 7. Second round (after the review): what was added and rechecked, Features (+2 more)

### Community 92 - "pipeline.py"
Cohesion: 0.06
Nodes (35): _scores(), test_NFR_01_small_batches_give_the_same_results(), sizes(), Column, Table, _table(), build_tables(), map_files() (+27 more)

### Community 93 - "simulator.py"
Cohesion: 0.11
Nodes (27): _run(), test_FR_ZD_02_large_load_priority(), test_FR_ZD_05_many_conventional_meters_still_flag_mining(), test_FR_ML_03_missing_data_and_drift_raise_alerts(), cmd_simulate(), fake_address(), fake_name(), fake_phone() (+19 more)

### Community 95 - "VoltGuard AI: UI and UX design requirements (R0 → R1 redesign)"
Cohesion: 0.20
Nodes (9): 1. Users and their first question, 2. Design principles, 3. Visual language and design tokens, 4. Components, 5. Screens, 6. Accessibility and language (must pass before release), 7. How to build it (suggested tools), 9. Acceptance checks for the redesign (+1 more)

### Community 96 - "learning.py"
Cohesion: 0.31
Nodes (5): cmd_retrain(), hit_rates(), labels(), _log_mlflow(), retrain()

### Community 97 - "sunshine_hours"
Cohesion: 0.11
Nodes (19): district, sunshine_hours, temperature_c, required, type, columns, description, key (+11 more)

### Community 98 - "VoltGuard AI (R0 prototype)"
Cohesion: 0.22
Nodes (8): Data modes, Development and tests, Documents, Public link for judges (Cloudflare Tunnel), Quick start (Windows laptop), Status: what works, what does not, what needs TNB, Telegram dispatch bot, VoltGuard AI (R0 prototype)

### Community 101 - "scoring.py"
Cohesion: 0.36
Nodes (4): Reason, reason_text(), Score, score_premise()

### Community 104 - "cli.py"
Cohesion: 0.18
Nodes (9): test_NFR_07_rpt_views_hold_no_premise_ids_or_personal_details(), cmd_detect(), cmd_simreport(), main(), load_truth(), cut(), known_cases_active(), known_cases_simulated() (+1 more)

### Community 105 - "seed.py"
Cohesion: 0.36
Nodes (4): cmd_demo(), prewarm(), print_script(), reset_rehearsal()

### Community 106 - "rag.py"
Cohesion: 0.15
Nodes (15): test_NFR_15_planted_instruction_in_retrieved_text_is_data(), quote_retrieved(), case_summary_text(), collect_documents(), _front_matter(), index_case_summaries(), index_documents(), _pdf_text() (+7 more)

### Community 107 - "Manager dashboard in Power BI (R0)"
Cohesion: 0.25
Nodes (7): Connect Power BI Desktop, Manager dashboard in Power BI (R0), Page 1: Network overview, Page 2: Leaking zones, Page 3: Cases and hit rates, R1, Views

### Community 109 - "Upload area: bring your own datasets"
Cohesion: 0.40
Nodes (4): How to upload, Upload area: bring your own datasets, Versions, What validation checks

### Community 110 - "llm.py"
Cohesion: 0.26
Nodes (8): test_NFR_15_model_never_receives_personal_details(), test_NFR_15_model_output_with_personal_details_is_blocked(), available(), check_prompt(), complete(), Completion, mode(), PromptBlocked

### Community 111 - "Hand-off: VoltGuard AI R0 build"
Cohesion: 0.18
Nodes (10): Auto-generated state (scripts/handoff.sh), Decisions to keep, Docker check (this session), File tree, Hand-off: VoltGuard AI R0 build, How to resume in a new session, Ideas for a next session, Known issues (+2 more)

### Community 112 - "Cases.jsx"
Cohesion: 0.33
Nodes (5): Board(), Cases(), FILTER_LABEL, FILTERS, STATUSES

### Community 113 - "documents"
Cohesion: 0.25
Nodes (7): documents, id, manual, owner, role_scope, title, url

### Community 114 - "voltguard_guide.md"
Cohesion: 0.29
Nodes (6): 1. What a flagged zone means, 2. Flat 24/7 gap, 3. Risk scores and reasons, 4. Voltage evidence, 5. Routine meter checks, 6. Recording outcomes

### Community 115 - "audit.py"
Cohesion: 0.13
Nodes (13): anchor_dir(), row_hash(), row_text(), verify(), VerifyResult, write_anchor(), demo_passwords(), cmd_anchor() (+5 more)

### Community 117 - "field_evidence_checklist.md"
Cohesion: 0.50
Nodes (3): At the meter, Before the visit, Recording

### Community 121 - "Deviations from the SDD"
Cohesion: 0.29
Nodes (6): Additions after the R0 review (not in the SDD), Agents and RAG, Data, Deviations from the SDD, Library swaps, Lite-profile swaps (prompt 7.2)

### Community 124 - "pipeline"
Cohesion: 0.67
Nodes (3): pipeline, meter_batch, zone_batch

### Community 127 - "VoltGuard AI demo script (R0)"
Cohesion: 0.29
Nodes (6): Backup steps (for questions or a recorded clip), If something goes wrong, Live steps (5 minutes), Rehearsal checklist (prompt 7.5), The day before, VoltGuard AI demo script (R0)

### Community 134 - "Weekly.jsx"
Cohesion: 0.18
Nodes (17): BarChart(), CategoryBars(), LineChart(), niceTicks(), PALETTE, QueryChart(), scale(), Answer() (+9 more)

### Community 137 - "digest.py"
Cohesion: 0.09
Nodes (17): test_FR_UI_05_pdf_fallback_without_a_browser(), alerts(), models(), weekly(), weekly_pdf(), weekly_send(), _chromium(), _fpdf() (+9 more)

### Community 139 - "route"
Cohesion: 0.50
Nodes (4): route, road_factor, speed_kmh, visit_minutes

## Knowledge Gaps
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Caller` connect `voltguard/__init__.py` to `.start`, `admin_connection`, `digest.py`, `rag.py`, `Requirements`, `sources.py`, `answer`, `login`, `re`, `auth.py`, `cases.py`, `config.py`, `local_stack.py`, `date`, `routes_admin.py`, `report.py`, `db.py`, `voltguard/__init__.py`?**
  _High betweenness centrality (0.173) - this node is a cross-community bridge._
- **Are the 95 inferred relationships involving `Caller` (e.g. with `LocalStack` and `ask()`) actually correct?**
  _`Caller` has 95 INFERRED edges - model-reasoned connections that need verification._
- **Should `VoltGuard AI: Software Design Document (SDD)` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Why does `date` connect `date` to `sunshine_hours`, `test_data_layer.py`, `engine.py`, `anomaly.py`, `sources.py`, `config.py`, `balance.py`, `pipeline.py`, `simulator.py`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Are the 71 inferred relationships involving `Requirements` (e.g. with `test_NFR_02_NFR_13_pages_load_fast_and_phone_view_in_bahasa_melayu()` and `test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act()`) actually correct?**
  _`Requirements` has 71 INFERRED edges - model-reasoned connections that need verification._
- **Should `columns` be split into smaller, more focused modules?**
  _Cohesion score 0.06896551724137931 - nodes in this community are weakly interconnected._
- **Why does `columns` connect `sunshine_hours` to `date`?**
  _High betweenness centrality (0.158) - this node is a cross-community bridge._