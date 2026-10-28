# Graph Report - wt-int  (2026-10-28)

## Corpus Check
- 168 files · ~1,248,475 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2731 nodes · 6024 edges · 153 communities (143 shown, 10 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 188 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `739a27ac`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Test Postgres server
- Web data loading (cases, dispatch)
- Score weights
- SDD: software design document
- Upload column map example
- SRS: requirements
- Configuration loader
- Data source selection
- Build brief (R0 prompt)
- Data layer tests
- End-to-end use-case script
- Demo accounts, teams, regions
- Detection and solar tests
- Tuned weights
- Zone flag rule settings
- Dataset adapters: SGCC theft labels and data.gov.my months
- Simulation report
- R0 build plan
- Prometheus scrape config
- Penalties, tenancy, monitoring settings
- Case workflow and notifications
- Cloudflare tunnel config
- Dataset ingest
- Local test stack and browser tests
- Dispatch timer settings
- Feature window settings
- Tuning and simulation report code
- make.ps1 tasks
- Case job settings
- Inspection route planner
- Voltage locator settings
- handoff.sh wrapper
- Tunnel script
- Compose: worker and web build
- Rooftop solar checks (FR-PS-10)
- Compose: database
- Compose: full-profile services
- Compose: Keycloak
- Compose: MinIO
- Compose: Airflow
- Compose: named tunnel
- Compose: Caddy proxy
- Embeddings, document search and similar cases
- Compose: MLflow
- Schema: duty roster
- Compose: Prometheus
- Schema: inspection outcome
- Schema: meter
- Schema: account event (solar registration)
- Schema: table list
- Schema: customer personal details
- Admin API (datasets, sources, audit)
- Schema: transformer
- Schema: premise
- Network loss model and zone inputs
- Schema: monthly readings
- Schema: transformer readings
- Schema: distance column
- Nightly pipeline (batched load and detection)
- Case report agent and approvals
- Compose: API service
- Compose: API environment
- Weekly summary report
- Web app shell and theme
- Agent API routes
- Schema: meter readings
- Detection engine (balance, features, zone input)
- Notes scrubber (personal details)
- Web dependencies
- Data manager and job buttons
- Shared UI components and labels
- Telegram dispatch bot
- Dataset adapter: London smart meters
- Back-test script
- Threshold settings (admin overrides)
- Case API routes and My work
- Audit chain and daily anchor
- Active sources and dataset versions
- UI upgrade API (meta, demo, back-test)
- Case workflow tests
- Pattern model and autoencoder
- Power BI build guide
- Analyst chatbot (query templates)
- API security and UI upgrade tests
- Compose: Ollama
- Canonical schema and upload validation
- Zone API routes
- Household load profiles
- Inspector app and API client
- Inspector encrypted offline store
- Autoencoder and model training
- Review and test report
- Test fixtures and seeded users
- Zone simulator
- Overview and Validation pages
- UI/UX design requirements
- Reason waterfall
- Schema: district weather
- How to run and README
- Telegram bot tests
- UI upgrade brief
- Dataset and document download scripts
- Service worker
- Labels (EN/BM) and solar wording
- Database tables and reporting views
- RAG indexing
- Power BI dashboard layout
- Sign-in, sessions and file storage
- Upload area guide
- Language model, seed and demo command
- Agent safety tests and PDF export
- Graph naming and traceability scripts
- Public RAG document list
- Field assistant guide
- CLI commands and audit chain
- Screenshot scripts
- Field evidence checklist
- RAG documents README
- Hand-off script
- Deviations from the SDD
- Data health
- Demo-mode test config
- Pipeline batch settings
- Traceability matrix
- Hand-off notes
- Demo script
- Models and licences
- Back-test report
- Retraining and weekly endpoints
- Compose: token tunnel
- Encrypted file storage
- Scoring and reasons
- CLI entry and reporting tests
- Route planner tests
- Demo guide and reset
- Monitoring and alerts
- Feeder schematic
- Route planner settings
- Solar brief
- Weekly report brief
- Traceability and setup scripts
- UI and weekly report change log
- Rooftop solar schemes explainer (RAG)
- UI upgrade plan
- Vite dev proxy
- Learning and monitoring tests
- Row-level security
- Telegram tables
- doc_chunk table
- notification table

## God Nodes (most connected - your core abstractions)
1. `Caller` - 142 edges
2. `t()` - 105 edges
3. `login()` - 70 edges
4. `audit()` - 46 edges
5. `get()` - 42 edges
6. `admin_connection()` - 42 edges
7. `useLoad()` - 33 edges
8. `shot()` - 32 edges
9. `request()` - 30 edges
10. `run_detection()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `require()` --indirect_call--> `check()`  [INFERRED]
  backend/voltguard/api/deps.py → scripts/e2e_use_cases.py
- `status()` --calls--> `check()`  [INFERRED]
  backend/voltguard/service/demo_guide.py → scripts/e2e_use_cases.py
- `create_cases()` --indirect_call--> `run()`  [INFERRED]
  backend/voltguard/api/routes_cases.py → scripts/handoff.py
- `_safe()` --indirect_call--> `run()`  [INFERRED]
  backend/voltguard/service/scheduler.py → scripts/handoff.py
- `pg()` --uses--> `TempPostgres`  [INFERRED]
  backend/tests/conftest.py → backend/tests/pg_server.py

## Import Cycles
- None detected.

## Communities (153 total, 10 thin omitted)

### Community 0 - "Test Postgres server"
Cohesion: 0.14
Nodes (11): ExternalPostgres, TempPostgres, _bin(), _free_port(), make_postgres(), A throwaway PostgreSQL for database tests. Uses TEST_DATABASE_URL (owner…, Throwaway database: on TEST_DATABASE_URL's server when set, else a local…, A fresh database on the server named by TEST_DATABASE_URL (Windows: a throwaway… (+3 more)

### Community 1 - "Web data loading (cases, dispatch)"
Cohesion: 0.09
Nodes (39): get(), put(), session(), ErrorBox(), useLoad(), DemoGuide(), go(), fill() (+31 more)

### Community 2 - "Score weights"
Cohesion: 0.17
Nodes (12): weights, anomaly, change_from_history, flatness, gap_from_similar, night_to_day, pattern_model, tenancy_change (+4 more)

### Community 3 - "SDD: software design document"
Cohesion: 0.05
Nodes (39): 10.1 Test levels, 10.2 Simulated zone, 10.3 Stress tests, 10.4 Acceptance criteria, 10.5 Prototype demo for judges, 10. Testing and validation plan, 11.1 Requirements to design, 11.2 Open issues (+31 more)

### Community 4 - "Upload column map example"
Cohesion: 0.07
Nodes (28): CABLE_M, ENERGY_KWH, INTERVAL_START, KWH_IMPORT, LV_BRANCH, METER_NO, PHASE, PREMISE_REF (+20 more)

### Community 5 - "SRS: requirements"
Cohesion: 0.06
Nodes (31): 1.1 Purpose, 1.2 Scope, 1.3 Releases, 1.4 Definitions, 1.5 References, 1. Introduction, 2.1 Product perspective, 2.2 User classes (+23 more)

### Community 6 - "Configuration loader"
Cohesion: 0.13
Nodes (29): _timers(), agent_status(), cmd_detect(), admin_database_url(), config_dir(), data_path(), data_root(), data_sources() (+21 more)

### Community 7 - "Data source selection"
Cohesion: 0.08
Nodes (24): downloads, london, sgcc, london, households, region, zone_size, pattern_training (+16 more)

### Community 8 - "Build brief (R0 prompt)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "Data layer tests"
Cohesion: 0.17
Nodes (20): isolated(), small_scenario(), test_bad_upload_is_rejected_with_reasons(), test_column_map_units_and_timezone(), test_FR_DI_06_upload_with_missing_intervals_flags_meter(), test_london_adapter_profiles_and_canonical_tables(), test_missing_voltage_and_phase_use_fallbacks(), test_switch_to_uploaded_dataset_without_code_changes() (+12 more)

### Community 10 - "End-to-end use-case script"
Cohesion: 0.08
Nodes (51): adm_data(), adm_settings(), adm_upload(), api(), ask(), bm(), check(), desk() (+43 more)

### Community 11 - "Demo accounts, teams, regions"
Cohesion: 0.12
Nodes (16): demo_seed, demo_zone, regions, code, name, teams, base_lat, base_lon (+8 more)

### Community 12 - "Detection and solar tests"
Cohesion: 0.08
Nodes (30): case_premise(), rank_of(), top_k(), test_detection_creates_no_cases(), test_FR_DI_05_tenancy_change_at_injected_thief(), test_FR_PS_02_voltage_locates_tap_on_its_phase(), test_FR_PS_04_timing_match_and_day_one_tap_in_top(), test_FR_PS_05_legitimate_patterns_tagged_not_top() (+22 more)

### Community 13 - "Tuned weights"
Cohesion: 0.10
Nodes (20): _tuning, objective, seed, split, tuned_at, zones, weights, anomaly (+12 more)

### Community 14 - "Zone flag rule settings"
Cohesion: 0.18
Nodes (11): zone, change_min_segment_days, change_min_shift_share, consecutive_days, conventional_daily_cv, flat_cv, large_load_share, loss_model_error_share (+3 more)

### Community 15 - "Dataset adapters: SGCC theft labels and data.gov.my months"
Cohesion: 0.15
Nodes (23): test_datagovmy_adapter_month_factors(), test_sgcc_adapter_feeds_pattern_model(), _columns(), convert(), month_factors(), month_factors_from(), processed(), raw_dir() (+15 more)

### Community 16 - "Simulation report"
Cohesion: 0.22
Nodes (8): Demo zone TX-CEN-001, Flag threshold sweep (held-out settings, for OI-7), Held-out thefts, one by one, How to read this, Simulation report, Stress tests (SDD 10.3): where detection breaks, Summary (copy into the pitch deck), Where it breaks: noise and monthly-read meters

### Community 17 - "R0 build plan"
Cohesion: 0.33
Nodes (5): File tree, Key decisions (details in DEVIATIONS.md), Milestones, Open questions (do not block Must requirements), VoltGuard AI R0: build plan

### Community 18 - "Prometheus scrape config"
Cohesion: 0.25
Nodes (7): global, scrape_interval, scrape_configs, job_name, metrics_path, static_configs, targets

### Community 19 - "Penalties, tenancy, monitoring settings"
Cohesion: 0.18
Nodes (10): monitoring, drift_psi_alert, min_interval_completeness, penalties, ev_charging, solar, vacancy, tenancy (+2 more)

### Community 20 - "Case workflow and notifications"
Cohesion: 0.14
Nodes (36): CaseError, suggest(), audit(), add_photo(), _assign(), _case(), case_detail(), claim() (+28 more)

### Community 21 - "Cloudflare tunnel config"
Cohesion: 0.33
Nodes (5): credentials-file, ingress, hostname, service, tunnel

### Community 22 - "Dataset ingest"
Cohesion: 0.17
Nodes (22): IngestResult, schema_document(), build_tables(), _checksum(), cmd_ingest(), cmd_upload_kit(), context_for(), ingest() (+14 more)

### Community 23 - "Local test stack and browser tests"
Cohesion: 0.12
Nodes (22): LocalStack, run_job_and_wait(), sign_in(), stack(), test_demo_live_steps_1_to_7(), test_NFR_02_NFR_13_pages_load_fast_and_phone_view_in_bahasa_melayu(), api_login(), sign_in() (+14 more)

### Community 24 - "Dispatch timer settings"
Cohesion: 0.40
Nodes (5): dispatch, demo_escalation_minutes, demo_reminder_minutes, escalation_hours, reminder_hours

### Community 25 - "Feature window settings"
Cohesion: 0.40
Nodes (5): features, history_weeks, recent_days, timing_tau_days, zero_kwh

### Community 26 - "Tuning and simulation report code"
Cohesion: 0.13
Nodes (22): cmd_simreport(), cmd_tune(), evaluate(), _fast_scores(), _fmt(), _num(), penalised_tags(), run_scenario() (+14 more)

### Community 27 - "make.ps1 tasks"
Cohesion: 0.38
Nodes (4): Invoke-Setup(), Invoke-Tunnel(), New-Secret(), Test-PublicLink()

### Community 28 - "Case job settings"
Cohesion: 0.50
Nodes (4): cases, case_threshold, max_cases_per_zone, random_sample_per_zone

### Community 29 - "Inspection route planner"
Cohesion: 0.20
Nodes (17): test_route_order_beats_nearest_neighbour_and_is_close_to_the_best(), haversine_km(), roster_date(), _base(), _leg(), maps_links(), nearest_neighbour(), order_stops() (+9 more)

### Community 30 - "Voltage locator settings"
Cohesion: 0.50
Nodes (4): voltage, min_drop_v, proximity_scale_m, window_days

### Community 33 - "Compose: worker and web build"
Cohesion: 0.17
Nodes (13): build, context, dockerfile, web, worker, build, restart, build (+5 more)

### Community 34 - "Rooftop solar checks (FR-PS-10)"
Cohesion: 0.19
Nodes (19): FeatureSet, test_FR_PS_10_energy_budget_without_weather_uses_labelled_default(), change_point(), build_features(), _clip01(), _drop_share(), _mean(), peak_sun_hours() (+11 more)

### Community 35 - "Compose: database"
Cohesion: 0.15
Nodes (13): environment, healthcheck, image, ports, restart, volumes, POSTGRES_DB, POSTGRES_PASSWORD (+5 more)

### Community 36 - "Compose: full-profile services"
Cohesion: 0.11
Nodes (17): image, profiles, name, image, profiles, services, grafana, redis (+9 more)

### Community 37 - "Compose: Keycloak"
Cohesion: 0.25
Nodes (8): KC_BOOTSTRAP_ADMIN_PASSWORD, KC_BOOTSTRAP_ADMIN_USERNAME, command, environment, image, profiles, volumes, keycloak

### Community 38 - "Compose: MinIO"
Cohesion: 0.25
Nodes (8): MINIO_ROOT_PASSWORD, MINIO_ROOT_USER, command, environment, image, profiles, volumes, minio

### Community 39 - "Compose: Airflow"
Cohesion: 0.29
Nodes (7): command, environment, image, profiles, volumes, AIRFLOW__CORE__LOAD_EXAMPLES, airflow

### Community 40 - "Compose: named tunnel"
Cohesion: 0.29
Nodes (7): tunnel-named, command, depends_on, image, profiles, restart, volumes

### Community 41 - "Compose: Caddy proxy"
Cohesion: 0.33
Nodes (6): depends_on, image, ports, restart, volumes, proxy

### Community 42 - "Embeddings, document search and similar cases"
Cohesion: 0.19
Nodes (15): cosine(), download(), embed(), _hash_embed(), _model_dir(), model_name(), _onnx(), words() (+7 more)

### Community 43 - "Compose: MLflow"
Cohesion: 0.40
Nodes (5): command, image, profiles, volumes, mlflow

### Community 44 - "Schema: duty roster"
Cohesion: 0.10
Nodes (20): max, min, required, type, max, min, required, type (+12 more)

### Community 45 - "Compose: Prometheus"
Cohesion: 0.50
Nodes (4): image, profiles, volumes, prometheus

### Community 46 - "Schema: inspection outcome"
Cohesion: 0.10
Nodes (21): required, type, case_id, notes, origin, outcome, reason_tag, recorded_at (+13 more)

### Community 47 - "Schema: meter"
Cohesion: 0.11
Nodes (19): installed_on, meter_id, meter_type, read_frequency, required, type, columns, description (+11 more)

### Community 48 - "Schema: account event (solar registration)"
Cohesion: 0.13
Nodes (15): columns, description, key, event_date, event_id, event_type, required, type (+7 more)

### Community 49 - "Schema: table list"
Cohesion: 0.15
Nodes (12): description, key, description, key, tables, duty_roster, inspection_outcome, transformer (+4 more)

### Community 50 - "Schema: customer personal details"
Cohesion: 0.12
Nodes (17): required, type, address, contact, holder_name, premise_id, required, type (+9 more)

### Community 51 - "Admin API (datasets, sources, audit)"
Cohesion: 0.07
Nodes (58): ApiError, DemoSignIn, Tariff, bad_request(), caller(), conflict(), connection(), forbidden() (+50 more)

### Community 52 - "Schema: transformer"
Cohesion: 0.06
Nodes (34): max, min, required, type, unit, capacity_kva, district, dtm_accuracy_class (+26 more)

### Community 53 - "Schema: premise"
Cohesion: 0.07
Nodes (30): feeder_branch, lat, phase, premise_type, street_seq, tariff, description, required (+22 more)

### Community 54 - "Network loss model and zone inputs"
Cohesion: 0.20
Nodes (11): FlowResult, ZoneNetwork, _phase_shares(), solve(), ndarray, Radial low-voltage network model: per-phase load flow, technical losses and…, Phase resistance from the transformer to each node (ohm)., (n_premises, 3) share of each premise's current carried on each phase. (+3 more)

### Community 55 - "Schema: monthly readings"
Cohesion: 0.13
Nodes (15): kwh, month, description, max, min, required, type, unit (+7 more)

### Community 56 - "Schema: transformer readings"
Cohesion: 0.11
Nodes (18): kwh_supplied, transformer_id, ts, max, min, required, type, unit (+10 more)

### Community 57 - "Schema: distance column"
Cohesion: 0.29
Nodes (7): distance_m, description, max, min, required, type, unit

### Community 58 - "Nightly pipeline (batched load and detection)"
Cohesion: 0.12
Nodes (34): PipelineError, _scores(), test_NFR_01_small_batches_give_the_same_results(), _chunks(), copy_in(), copy_out(), _csv(), detect_in_batches() (+26 more)

### Community 59 - "Case report agent and approvals"
Cohesion: 0.15
Nodes (25): ReportError, test_FR_AG_01_live_model_gets_figures_with_units(), approve_content(), approve_export(), _assessment(), _assessment_mock(), build_draft(), draft_for_case() (+17 more)

### Community 60 - "Compose: API service"
Cohesion: 0.29
Nodes (7): depends_on, env_file, restart, volumes, condition, db, api

### Community 61 - "Compose: API environment"
Cohesion: 0.38
Nodes (7): environment, ADMIN_DATABASE_URL, DATA_ROOT, DATABASE_URL, HF_HOME, OLLAMA_URL, environment

### Community 62 - "Weekly summary report"
Cohesion: 0.05
Nodes (91): test_FR_UI_05_pdf_fallback_without_a_browser(), test_empty_week(), test_energy_takeaways(), test_headline_counts_only(), test_hit_rate_takeaway_overlap_apart_and_synthetic(), test_html_snapshot_has_every_section_and_no_personal_details(), test_malay_rule_sentences(), test_next_step_rules_and_limit() (+83 more)

### Community 63 - "Web app shell and theme"
Cohesion: 0.12
Nodes (16): onSessionChange(), App(), Guarded(), SearchBox(), Shell(), useBadges(), useMeta(), useSession() (+8 more)

### Community 64 - "Agent API routes"
Cohesion: 0.24
Nodes (15): Chat, Query, approve_content(), approve_export(), _call(), draft_report(), get_report(), query_templates() (+7 more)

### Community 65 - "Schema: meter readings"
Cohesion: 0.13
Nodes (15): quality_flag, voltage_v, columns, description, key, allowed, description, required (+7 more)

### Community 66 - "Detection engine (balance, features, zone input)"
Cohesion: 0.09
Nodes (37): BalanceResult, DetectionRun, PremiseResult, ZoneResult, VoltageResult, ZoneInput, balance_zone(), data_quality_flags() (+29 more)

### Community 67 - "Notes scrubber (personal details)"
Cohesion: 0.15
Nodes (16): OutputBlocked, ToolNotAllowed, ScrubResult, asks_forbidden_action(), check_output(), engine(), _known_patterns(), _presidio_analyzer() (+8 more)

### Community 68 - "Web dependencies"
Cohesion: 0.06
Nodes (31): dependencies, @fontsource/ibm-plex-sans, @fontsource/space-grotesk, leaflet, lucide-react, react, react-dom, react-leaflet (+23 more)

### Community 69 - "Data manager and job buttons"
Cohesion: 0.10
Nodes (26): pollJob(), post(), QueryChart(), JobButton(), start(), reset(), openCase(), int() (+18 more)

### Community 70 - "Shared UI components and labels"
Cohesion: 0.09
Nodes (43): bandPath(), BarChart(), CategoryBars(), LineChart(), niceTicks(), scale(), VoltageStrip(), Confidence() (+35 more)

### Community 71 - "Telegram dispatch bot"
Cohesion: 0.06
Nodes (52): Press, BlockedMessage, ActionRefused, chats(), link_code(), status(), unlink(), public_base_url() (+44 more)

### Community 72 - "Dataset adapter: London smart meters"
Cohesion: 0.21
Nodes (17): canonical_tables(), convert(), _kind(), _natural(), _pick(), read_raw(), _scan(), source_files() (+9 more)

### Community 73 - "Back-test script"
Cohesion: 0.29
Nodes (11): test_FR_DI_06_missing_day_flags_meter(), cut(), known_cases_active(), known_cases_simulated(), main(), replay_frame(), write_replay(), timedelta (+3 more)

### Community 74 - "Threshold settings (admin overrides)"
Cohesion: 0.22
Nodes (14): test_FR_AG_02_reminder_then_escalation_on_demo_timers(), run_reminders(), get_thresholds(), overrides(), save(), thresholds(), validate_change(), datetime (+6 more)

### Community 75 - "Case API routes and My work"
Cohesion: 0.11
Nodes (37): Assignment, Decision, NewCase, Outcome, Caller, me(), users(), assign() (+29 more)

### Community 76 - "Audit chain and daily anchor"
Cohesion: 0.20
Nodes (14): VerifyResult, test_FR_AD_02_NFR_12_audit_logged_and_tampering_detected(), anchor_dir(), row_hash(), row_text(), verify(), write_anchor(), datetime (+6 more)

### Community 77 - "Active sources and dataset versions"
Cohesion: 0.16
Nodes (24): SourceError, datasets(), activate_dataset(), active_sources(), dataset_versions(), datasets_root(), load_active_tables(), load_table() (+16 more)

### Community 78 - "UI upgrade API (meta, demo, back-test)"
Cohesion: 0.09
Nodes (23): alerts(), models(), weekly(), weekly_html(), weekly_pdf(), demo_accounts(), _demo_only(), demo_status() (+15 more)

### Community 79 - "Case workflow tests"
Cohesion: 0.23
Nodes (10): find(), test_FR_AG_02_dispatch_suggestion_claim_and_approval(), test_FR_IW_01_case_job_creates_threshold_cases(), test_FR_IW_01_manual_cases_and_only_supervisor_assigns(), test_FR_IW_02_FR_IW_03_FR_IW_04_outcomes_status_and_labels(), test_FR_IW_05_random_sample_presented_as_routine_check(), test_FR_UI_03_details_only_for_case_roles(), test_FR_UI_03_unclaimed_case_masked_for_every_analyst() (+2 more)

### Community 80 - "Pattern model and autoencoder"
Cohesion: 0.17
Nodes (18): PatternModel, feature_text(), load(), model_path(), reset_cache(), sgcc_training_set(), synthetic_training_set(), train() (+10 more)

### Community 81 - "Power BI build guide"
Cohesion: 0.33
Nodes (5): Before you start (5 minutes), Build the Power BI dashboard with Claude on your laptop, Check the result, If Claude cannot open Power BI, Prompt to paste into Claude (Cowork / Desktop on the laptop)

### Community 82 - "Analyst chatbot (query templates)"
Cohesion: 0.13
Nodes (22): QueryError, Template, ask(), _ask_model(), _chart_choice(), _model_params(), _num(), other_region_named() (+14 more)

### Community 83 - "API security and UI upgrade tests"
Cohesion: 0.15
Nodes (18): login(), fake_names(), test_data_manager_upload_validates_and_versions(), test_FR_AD_01_role_and_region_refusals(), test_FR_AD_03_threshold_change_applies_on_rerun(), test_FR_PS_07_suspects_reasons_add_up(), test_FR_UI_01_overview_zone_level_in_gap_order(), test_FR_UI_02_zone_view_balance_and_profile() (+10 more)

### Community 84 - "Compose: Ollama"
Cohesion: 0.50
Nodes (4): image, restart, volumes, ollama

### Community 85 - "Canonical schema and upload validation"
Cohesion: 0.15
Nodes (20): Column, Table, Issue, ValidationReport, _check_duplicates(), _check_intervals(), _check_links(), _check_values() (+12 more)

### Community 86 - "Zone API routes"
Cohesion: 0.08
Nodes (44): test_tariff_file_unset_by_default(), test_3_1_value_at_risk_is_an_estimate_from_the_gap_above_the_margin(), latest_run_date(), premise_view(), _usage(), _zone(), zone_balance(), zone_cleared() (+36 more)

### Community 87 - "Household load profiles"
Cohesion: 0.19
Nodes (15): _bump(), daily_levels(), household_load_kw(), london_shapes(), _night_block(), synthetic_shapes(), ndarray, Path (+7 more)

### Community 88 - "Inspector app and API client"
Cohesion: 0.09
Nodes (39): ApiError, patch(), request(), setSession(), signIn(), signInDemo(), signOut(), AskBox() (+31 more)

### Community 89 - "Inspector encrypted offline store"
Cohesion: 0.32
Nodes (13): cryptoKey(), enforceMaxAge(), get(), keys(), openDb(), put(), rawDelete(), rawGet() (+5 more)

### Community 90 - "Autoencoder and model training"
Cohesion: 0.14
Nodes (18): Autoencoder, test_FR_DI_07_district_weather_loaded_and_used(), cmd_train_models(), load(), model_path(), save(), train(), train_from_simulation() (+10 more)

### Community 91 - "Review and test report"
Cohesion: 0.18
Nodes (10): 1. Does the build meet the SRS and SDD?, 2. End-to-end test: every use case, every account, 3. Bugs found and fixed, 4. Remaining unfinished task: done, 5. Suggested improvements, 6. How to repeat the test, 7. Second round (after the review): what was added and rechecked, Features (+2 more)

### Community 92 - "Test fixtures and seeded users"
Cohesion: 0.13
Nodes (21): api(), cfg(), demo_run(), demo_run_all(), demo_sim(), models(), pg(), test_NFR_03_no_endpoint_blocks_the_event_loop() (+13 more)

### Community 93 - "Zone simulator"
Cohesion: 0.08
Nodes (47): Injected, Scenario, ZoneSim, ZoneSpec, LossParams, _run(), test_FR_DI_01_readings_round_trip_match_generator(), test_FR_ZD_02_large_load_priority() (+39 more)

### Community 94 - "Overview and Validation pages"
Cohesion: 0.13
Nodes (24): BaseTiles(), providers(), startIndex(), numbered(), RouteMap(), zoneStatus(), dotRadius(), ZoneMap() (+16 more)

### Community 95 - "UI/UX design requirements"
Cohesion: 0.18
Nodes (10): 1. Users and their first question, 2. Design principles, 3. Visual language and design tokens, 4. Components, 5. Screens, 6. Accessibility and language (must pass before release), 7. How to build it (suggested tools), 8. Prompts (+2 more)

### Community 96 - "Reason waterfall"
Cohesion: 0.40
Nodes (7): Waterfall(), at(), barStyle(), shapRows(), waterfall(), SHAP_KEY, ADJUST

### Community 97 - "Schema: district weather"
Cohesion: 0.11
Nodes (19): date, sunshine_hours, temperature_c, required, type, columns, description, key (+11 more)

### Community 98 - "How to run and README"
Cohesion: 0.08
Nodes (22): 1. What you need (one time), 2. Set up Docker (one time), 3. Get the code (one time), 4. First start, 5. Everyday commands, 6. Make it a public, clickable link (instead of localhost), 7. When something goes wrong, 8. More documents (+14 more)

### Community 99 - "Telegram bot tests"
Cohesion: 0.15
Nodes (18): fake_names(), test_weekly_job_reaches_every_manager_and_supervisor(), test_weekly_report_page_explains_itself_in_both_languages(), test_weekly_summary_is_zone_level_and_region_limited(), test_weekly_summary_pdf_and_message(), message(), new_case(), test_FR_AD_01_chat_is_for_supervisors_inspectors_and_managers() (+10 more)

### Community 100 - "UI upgrade brief"
Cohesion: 0.11
Nodes (17): 0. Ground rules, 1. Visual direction: "network control room", 2. Pages to redesign, 3.10 Today's route (Could), 3.11 Landlord alert concept (Could, mock only), 3.1 RM at risk (Must), 3.2 Feeder schematic (Must), 3.3 Reason waterfall (Must) (+9 more)

### Community 101 - "Dataset and document download scripts"
Cohesion: 0.15
Nodes (14): apply_overrides(), fetch_kaggle(), fetch_url(), main(), manual(), Full profile only: the nightly pipeline as an Airflow DAG (SDD 6.1). In the…, Try to download the public datasets (prompt 3.2). Never blocks: on failure it…, `downloads: {london: <kaggle slug>, sgcc: <kaggle slug>}` in… (+6 more)

### Community 104 - "Labels (EN/BM) and solar wording"
Cohesion: 0.12
Nodes (21): SolarCheck(), checkValue(), pc(), share(), stillSuspect(), verdictText(), files(), usedKeys() (+13 more)

### Community 105 - "Database tables and reporting views"
Cohesion: 0.08
Nodes (29): account_event, customer_pii, detection_run, district_weather, duty_roster, historic_outcome, meter, meter_monthly_reading (+21 more)

### Community 106 - "RAG indexing"
Cohesion: 0.09
Nodes (39): Passage, test_FR_AG_04_field_assistant_mode_says_who_answered(), test_FR_AG_04_legal_sections_by_number_and_no_index(), keyword_overlap(), allow(), quote_retrieved(), answer(), case_summary_text() (+31 more)

### Community 107 - "Power BI dashboard layout"
Cohesion: 0.25
Nodes (7): Connect Power BI Desktop, Manager dashboard in Power BI (R0), Page 1: Network overview, Page 2: Leaking zones, Page 3: Cases and hit rates, R1, Views

### Community 108 - "Sign-in, sessions and file storage"
Cohesion: 0.08
Nodes (31): SignIn, AuthError, Session, test_FR_AD_01_database_enforces_region_and_pii_rules(), test_FR_AD_01_training_labels_and_hit_rates_are_region_limited(), current_session(), sign_in(), sign_out() (+23 more)

### Community 109 - "Upload area guide"
Cohesion: 0.33
Nodes (5): How to upload, Upload area: bring your own datasets, Versions, What to upload, What validation checks

### Community 110 - "Language model, seed and demo command"
Cohesion: 0.21
Nodes (13): Completion, PromptBlocked, test_FR_AG_03_live_model_choice_is_cleaned_and_labelled(), test_NFR_15_model_never_receives_personal_details(), test_NFR_15_model_output_with_personal_details_is_blocked(), available(), check_prompt(), complete() (+5 more)

### Community 111 - "Agent safety tests and PDF export"
Cohesion: 0.11
Nodes (16): reporting_case(), test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act(), test_FR_AG_01_FR_UI_05_two_approvals_then_pdf_with_details(), test_FR_AG_01_manager_sees_evidence_photos_only_for_export_approval(), test_FR_AG_03_answers_carry_a_chart_and_a_sentence_from_the_rows(), test_FR_AG_03_chatbot_answers_with_query_and_refuses_other_region(), test_FR_AG_04_field_assistant_cites_or_says_not_found(), test_FR_AG_05_three_similar_closed_cases() (+8 more)

### Community 112 - "Graph naming and traceability scripts"
Cohesion: 0.23
Nodes (8): community_index(), describe(), main(), match(), Apply curated community names to the graphify graph without re-clustering.…, Per community: its main files (most nodes; ties all count) and node labels, for…, First rule whose `file` is one of the community's main files and whose `has`…, collections

### Community 113 - "Public RAG document list"
Cohesion: 0.25
Nodes (7): documents, id, manual, owner, role_scope, title, url

### Community 114 - "Field assistant guide"
Cohesion: 0.29
Nodes (6): 1. What a flagged zone means, 2. Flat 24/7 gap, 3. Risk scores and reasons, 4. Voltage evidence, 5. Routine meter checks, 6. Recording outcomes

### Community 115 - "CLI commands and audit chain"
Cohesion: 0.17
Nodes (18): command(), cmd_activate(), cmd_convert(), cmd_sources(), migrate(), _role_password(), cmd_anchor(), cmd_fetch_models() (+10 more)

### Community 116 - "Screenshot scripts"
Cohesion: 0.32
Nodes (10): main(), chromium(), ids(), main(), sign_in(), token(), Ad-hoc screenshots of a few routes, for checking a page during development.…, Screenshots of every web page at desktop (1440x900) and phone (390x844) size.… (+2 more)

### Community 117 - "Field evidence checklist"
Cohesion: 0.50
Nodes (3): At the meter, Before the visit, Recording

### Community 119 - "Hand-off script"
Cohesion: 0.38
Nodes (10): file_tree(), graphify_cmd(), main(), run(), test_count(), update_graph(), update_handoff(), CompletedProcess (+2 more)

### Community 121 - "Deviations from the SDD"
Cohesion: 0.20
Nodes (9): Additions after the R0 review (not in the SDD), Agents and RAG, Data, Data (current public datasets), Deviations from the SDD, Library swaps, Lite-profile swaps (prompt 7.2), Rooftop solar (`VoltGuard_Solar_Prompt.md`, FR-PS-10) (+1 more)

### Community 122 - "Data health"
Cohesion: 0.25
Nodes (9): fallbacks(), health(), _upload_checks(), Any, Connection, Data health per table for the Data manager (UI brief 3.9): how the data was…, Issue counts by table and check from the active upload's validation report., SRS assumptions whose fallback the latest detection run used. (+1 more)

### Community 123 - "Demo-mode test config"
Cohesion: 0.15
Nodes (12): config_copy(), demo_on(), test_3_10_route_stops_show_straight_line_distance_from_base(), test_3_1_rpt_zone_latest_carries_value_at_risk_at_zone_level(), test_3_6_validation_summary_from_files_and_model_versions(), test_3_7_backtest_replay_by_role_and_region(), test_3_8_demo_guide_status_and_reset(), test_3_9_data_health_for_admins() (+4 more)

### Community 124 - "Pipeline batch settings"
Cohesion: 0.67
Nodes (3): pipeline, meter_batch, zone_batch

### Community 125 - "Traceability matrix"
Cohesion: 0.50
Nodes (3): Requirements, Summary, Traceability

### Community 126 - "Hand-off notes"
Cohesion: 0.14
Nodes (13): Auto-generated state (scripts/handoff.py), Decisions to keep, Docker check (this session), File tree, Graph summary, Hand-off: VoltGuard AI R0 build, How to resume in a new session, Ideas for a next session (+5 more)

### Community 127 - "Demo script"
Cohesion: 0.25
Nodes (7): Backup steps (for questions or a recorded clip), Driving the demo from the screen (`DEMO_MODE=true`), If something goes wrong, Live steps (5 minutes), Rehearsal checklist (prompt 7.5), The day before, VoltGuard AI demo script (R0)

### Community 130 - "Retraining and weekly endpoints"
Cohesion: 0.33
Nodes (8): auc(), hit_rates(), labels(), _log_mlflow(), retrain(), Model learning (SDD 5.4, FR-ML-01, FR-ML-02, FR-IW-04). Retrain on demand…, Training labels with the premise's features from the latest run on or before…, Hit rate (share confirmed) and precision (share confirmed among cases at or…

### Community 131 - "Compose: token tunnel"
Cohesion: 0.25
Nodes (8): TUNNEL_TOKEN, tunnel-token, command, depends_on, environment, image, profiles, restart

### Community 132 - "Encrypted file storage"
Cohesion: 0.43
Nodes (7): exists(), _fernet(), get(), _path(), put(), Encrypted file storage for inspection photos and exported PDFs (lite profile…, cryptography_fernet

### Community 133 - "Scoring and reasons"
Cohesion: 0.22
Nodes (11): Reason, Score, test_FR_PS_07_voltage_reason_at_the_premise_reads_naturally(), test_FR_PS_10_penalty_rule_follows_settings(), reason_text(), score_premise(), solar_timing_text(), solar_unexplained_text() (+3 more)

### Community 134 - "CLI entry and reporting tests"
Cohesion: 0.40
Nodes (4): test_NFR_07_rpt_views_hold_no_premise_ids_or_personal_details(), main(), Manager dashboard data (SRS FR-UI-01, NFR-07, SDD 9.2): zone-level…, pytest

### Community 135 - "Route planner tests"
Cohesion: 0.40
Nodes (3): test_FR_AG_02_team_route_with_navigation_and_limits(), Route planner (supports FR-AG-02): visiting order, navigation links, and who…, AI agents and RAG (SDD 8). Agents act on VoltGuard's results; they never make…

### Community 136 - "Demo guide and reset"
Cohesion: 0.11
Nodes (25): cmd_demo(), accounts(), guide_config(), reset(), reset_time(), status(), prewarm(), print_script() (+17 more)

### Community 137 - "Monitoring and alerts"
Cohesion: 0.06
Nodes (47): test_unusual_access_alert(), lifespan(), create_cases(), demo_reset(), admin_connection(), _pool(), _run(), running() (+39 more)

### Community 138 - "Feeder schematic"
Cohesion: 0.46
Nodes (6): FeederSchematic(), nodeFill(), layoutSchematic(), riskMix(), schematicSummary(), PHASES

### Community 139 - "Route planner settings"
Cohesion: 0.50
Nodes (4): route, road_factor, speed_kmh, visit_minutes

### Community 140 - "Solar brief"
Cohesion: 0.29
Nodes (6): 1. Close the loophole (Must), 2. Add the missing checks (Must unless marked), 3. Simulator and tests (Must), 4. Show it (Must), 5. Done means, VoltGuard R0: finish the rooftop-solar handling (FR-PS-10) and show it

### Community 141 - "Weekly report brief"
Cohesion: 0.33
Nodes (5): 1. What to add (in this order on the page), 2. Chart and writing rules, 3. Telegram delivery, 4. Tests and done, VoltGuard R0: make the weekly summary report self-explanatory

### Community 142 - "Traceability and setup scripts"
Cohesion: 0.21
Nodes (8): expand(), main(), requirements(), Create .env from .env.example and fill in generated secrets (used by `make…, Generate TRACEABILITY.md: every SRS requirement mapped to the code and tests…, re, secrets, sys

### Community 143 - "UI and weekly report change log"
Cohesion: 0.20
Nodes (9): Checks, Design system (section 1), Fixed on the way, New features (section 3), Pages (section 2), Tests, UI upgrade: before and after, Weekly summary report: before and after (+1 more)

### Community 144 - "Rooftop solar schemes explainer (RAG)"
Cohesion: 0.29
Nodes (6): NEM (Net Energy Metering), SelCo (self-consumption), Solar ATAP, Sources, What to check on site, Why it matters for an inspection

### Community 145 - "UI upgrade plan"
Cohesion: 0.50
Nodes (3): Order of work, Rules kept, UI upgrade plan (`VoltGuard_UI_Upgrade_Prompt.md`)

### Community 151 - "Learning and monitoring tests"
Cohesion: 0.25
Nodes (4): test_FR_ML_01_FR_ML_02_retrain_records_version_with_both_hit_rates(), Learning and monitoring (SRS FR-ML-01-03, FR-IW-04)., Test accounts: one per role and region from config/demo.yaml, plus the pipeline…, psycopg

### Community 154 - "Telegram tables"
Cohesion: 0.50
Nodes (3): app_user, telegram_link_code, telegram_state

## Knowledge Gaps
- **664 isolated node(s):** `Template`, `DONE`, `TITLES`, `FILTER_LABEL`, `FILTERS` (+659 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Caller` connect `Case API routes and My work` to `Configuration loader`, `Monitoring and alerts`, `Case workflow and notifications`, `Local test stack and browser tests`, `Inspection route planner`, `Admin API (datasets, sources, audit)`, `Case report agent and approvals`, `Weekly summary report`, `Agent API routes`, `Telegram dispatch bot`, `Threshold settings (admin overrides)`, `Active sources and dataset versions`, `UI upgrade API (meta, demo, back-test)`, `Case workflow tests`, `Analyst chatbot (query templates)`, `API security and UI upgrade tests`, `Zone API routes`, `Test fixtures and seeded users`, `Telegram bot tests`, `RAG indexing`, `Sign-in, sessions and file storage`, `Agent safety tests and PDF export`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `login()` connect `API security and UI upgrade tests` to `Telegram bot tests`, `Route planner tests`, `Monitoring and alerts`, `Audit chain and daily anchor`, `Sign-in, sessions and file storage`, `Detection and solar tests`, `Case workflow tests`, `Agent safety tests and PDF export`, `Zone API routes`, `Learning and monitoring tests`, `Demo-mode test config`, `Test fixtures and seeded users`, `Zone simulator`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Why does `run_zones()` connect `Detection engine (balance, features, zone input)` to `Pattern model and autoencoder`, `Data layer tests`, `Rooftop solar checks (FR-PS-10)`, `Scoring and reasons`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Are the 102 inferred relationships involving `Caller` (e.g. with `LocalStack` and `ask()`) actually correct?**
  _`Caller` has 102 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Template`, `DONE`, `TITLES` to the rest of the system?**
  _664 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Test Postgres server` be split into smaller, more focused modules?**
  _Cohesion score 0.1380952380952381 - nodes in this community are weakly interconnected._
- **Should `Web data loading (cases, dispatch)` be split into smaller, more focused modules?**
  _Cohesion score 0.08748114630467571 - nodes in this community are weakly interconnected._