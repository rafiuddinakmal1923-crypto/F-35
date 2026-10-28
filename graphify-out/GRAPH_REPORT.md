# Graph Report - wt-ui  (2026-10-28)

## Corpus Check
- 168 files · ~1,247,494 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2725 nodes · 6010 edges · 154 communities (143 shown, 11 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 188 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `aefd2c21`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Test Postgres server (pg_server.py)
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
- Public dataset adapters (London, SGCC, data.gov.my)
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
- Background job runner (one heavy job at a time)
- make.ps1 tasks
- Case job settings
- Inspection route planner
- Voltage locator settings
- handoff.sh wrapper
- Tunnel script
- Compose: worker and web build
- Telegram API routes
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
- UI upgrade API (meta, demo, back-test)
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
- Database connections and Telegram dispatch bot
- RAG indexing (rag.py)
- Back-test script
- PDF export
- Case API routes and My work
- Audit chain and daily anchor
- Active sources and dataset versions
- Model API and retraining
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
- RAG indexing (rag.py)
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
- Monitoring and alerts
- Pipeline batch settings
- Traceability matrix
- Hand-off notes
- Demo script
- Models and licences
- Back-test report
- Airflow nightly DAG
- Compose: token tunnel
- Test Postgres server (pg_server.py)
- Scoring and reasons
- Assistant page and query charts
- Weekly report and message tests
- Demo guide and reset
- API app, scheduler and lifespan
- Feeder schematic
- Route planner settings
- Solar brief
- Weekly report brief
- Traceability and setup scripts
- UI and weekly report change log
- Rooftop solar schemes explainer (RAG)
- UI upgrade plan
- Vite dev proxy
- Agent guardrails
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

## Communities (154 total, 11 thin omitted)

### Community 0 - "Test Postgres server (pg_server.py)"
Cohesion: 0.19
Nodes (9): TempPostgres, _bin(), _free_port(), make_postgres(), A throwaway PostgreSQL for database tests. Uses TEST_DATABASE_URL (owner…, Throwaway database: on TEST_DATABASE_URL's server when set, else a local…, socket, subprocess (+1 more)

### Community 1 - "Web data loading (cases, dispatch)"
Cohesion: 0.09
Nodes (37): get(), put(), session(), ErrorBox(), useLoad(), DemoGuide(), go(), fill() (+29 more)

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
Nodes (26): test_sgcc_adapter_feeds_pattern_model(), meta(), admin_database_url(), config_dir(), data_sources(), database_url(), deep_merge(), demo_config() (+18 more)

### Community 7 - "Data source selection"
Cohesion: 0.08
Nodes (24): downloads, london, sgcc, london, households, region, zone_size, pattern_training (+16 more)

### Community 8 - "Build brief (R0 prompt)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "Data layer tests"
Cohesion: 0.17
Nodes (22): isolated(), small_scenario(), test_bad_upload_is_rejected_with_reasons(), test_column_map_units_and_timezone(), test_FR_DI_06_upload_with_missing_intervals_flags_meter(), test_london_adapter_profiles_and_canonical_tables(), test_missing_voltage_and_phase_use_fallbacks(), test_switch_to_uploaded_dataset_without_code_changes() (+14 more)

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

### Community 15 - "Public dataset adapters (London, SGCC, data.gov.my)"
Cohesion: 0.09
Nodes (38): test_datagovmy_adapter_month_factors(), _columns(), convert(), month_factors(), month_factors_from(), processed(), raw_dir(), _stamp() (+30 more)

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
Cohesion: 0.06
Nodes (64): CaseError, BlockedMessage, data_path(), public_base_url(), add_photo(), _assign(), _case(), case_detail() (+56 more)

### Community 21 - "Cloudflare tunnel config"
Cohesion: 0.33
Nodes (5): credentials-file, ingress, hostname, service, tunnel

### Community 22 - "Dataset ingest"
Cohesion: 0.10
Nodes (28): IngestResult, upload_dataset(), schema_document(), build_tables(), _checksum(), cmd_activate(), cmd_convert(), cmd_ingest() (+20 more)

### Community 23 - "Local test stack and browser tests"
Cohesion: 0.11
Nodes (23): LocalStack, run_job_and_wait(), sign_in(), stack(), test_demo_live_steps_1_to_7(), test_NFR_02_NFR_13_pages_load_fast_and_phone_view_in_bahasa_melayu(), api_login(), sign_in() (+15 more)

### Community 24 - "Dispatch timer settings"
Cohesion: 0.40
Nodes (5): dispatch, demo_escalation_minutes, demo_reminder_minutes, escalation_hours, reminder_hours

### Community 25 - "Feature window settings"
Cohesion: 0.40
Nodes (5): features, history_weeks, recent_days, timing_tau_days, zero_kwh

### Community 26 - "Background job runner (one heavy job at a time)"
Cohesion: 0.19
Nodes (12): run_detection(), create_cases(), _run(), running(), status(), submit(), _update(), Ingest, zone balance, locator and scoring. Creates no cases. (+4 more)

### Community 27 - "make.ps1 tasks"
Cohesion: 0.38
Nodes (4): Invoke-Setup(), Invoke-Tunnel(), New-Secret(), Test-PublicLink()

### Community 28 - "Case job settings"
Cohesion: 0.50
Nodes (4): cases, case_threshold, max_cases_per_zone, random_sample_per_zone

### Community 29 - "Inspection route planner"
Cohesion: 0.11
Nodes (33): test_route_order_beats_nearest_neighbour_and_is_close_to_the_best(), haversine_km(), roster_date(), run_reminders(), suggest(), _timers(), _base(), _leg() (+25 more)

### Community 30 - "Voltage locator settings"
Cohesion: 0.50
Nodes (4): voltage, min_drop_v, proximity_scale_m, window_days

### Community 33 - "Compose: worker and web build"
Cohesion: 0.17
Nodes (13): build, context, dockerfile, web, worker, build, restart, build (+5 more)

### Community 34 - "Telegram API routes"
Cohesion: 0.13
Nodes (16): Press, require(), chats(), link_code(), status(), unlink(), BaseModel, get (+8 more)

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
Cohesion: 0.17
Nodes (17): cosine(), download(), embed(), _hash_embed(), _model_dir(), model_name(), _onnx(), words() (+9 more)

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
Cohesion: 0.12
Nodes (16): columns, event_date, event_id, event_type, premise_id, required, type, required (+8 more)

### Community 49 - "Schema: table list"
Cohesion: 0.12
Nodes (15): description, key, description, key, description, key, tables, account_event (+7 more)

### Community 50 - "Schema: customer personal details"
Cohesion: 0.15
Nodes (13): required, type, address, contact, holder_name, required, type, columns (+5 more)

### Community 51 - "UI upgrade API (meta, demo, back-test)"
Cohesion: 0.11
Nodes (34): ApiError, DemoSignIn, Tariff, bad_request(), caller(), conflict(), connection(), forbidden() (+26 more)

### Community 52 - "Schema: transformer"
Cohesion: 0.06
Nodes (34): max, min, required, type, unit, capacity_kva, district, dtm_accuracy_class (+26 more)

### Community 53 - "Schema: premise"
Cohesion: 0.07
Nodes (30): feeder_branch, lat, phase, premise_type, street_seq, tariff, description, required (+22 more)

### Community 54 - "Network loss model and zone inputs"
Cohesion: 0.16
Nodes (13): FlowResult, LossParams, ZoneNetwork, network_for(), _phase_shares(), solve(), ndarray, Radial low-voltage network model: per-phase load flow, technical losses and… (+5 more)

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
Cohesion: 0.13
Nodes (32): PipelineError, _scores(), test_NFR_01_small_batches_give_the_same_results(), _chunks(), copy_in(), copy_out(), _csv(), detect_in_batches() (+24 more)

### Community 59 - "Case report agent and approvals"
Cohesion: 0.16
Nodes (24): ReportError, test_FR_AG_01_live_model_gets_figures_with_units(), approve_content(), approve_export(), _assessment(), _assessment_mock(), build_draft(), draft_for_case() (+16 more)

### Community 60 - "Compose: API service"
Cohesion: 0.29
Nodes (7): depends_on, env_file, restart, volumes, condition, db, api

### Community 61 - "Compose: API environment"
Cohesion: 0.38
Nodes (7): environment, ADMIN_DATABASE_URL, DATA_ROOT, DATABASE_URL, HF_HOME, OLLAMA_URL, environment

### Community 62 - "Weekly summary report"
Cohesion: 0.06
Nodes (84): test_empty_week(), test_energy_takeaways(), test_headline_counts_only(), test_hit_rate_takeaway_overlap_apart_and_synthetic(), test_html_snapshot_has_every_section_and_no_personal_details(), test_malay_rule_sentences(), test_next_step_rules_and_limit(), test_simulated_versus_uploaded_data() (+76 more)

### Community 63 - "Web app shell and theme"
Cohesion: 0.12
Nodes (16): onSessionChange(), App(), Guarded(), SearchBox(), Shell(), useBadges(), useMeta(), useSession() (+8 more)

### Community 64 - "Agent API routes"
Cohesion: 0.23
Nodes (16): Chat, Query, agent_status(), approve_content(), approve_export(), _call(), draft_report(), get_report() (+8 more)

### Community 65 - "Schema: meter readings"
Cohesion: 0.13
Nodes (15): quality_flag, voltage_v, columns, description, key, allowed, description, required (+7 more)

### Community 66 - "Detection engine (balance, features, zone input)"
Cohesion: 0.07
Nodes (57): BalanceResult, DetectionRun, PremiseResult, ZoneResult, FeatureSet, VoltageResult, ZoneInput, test_FR_PS_10_energy_budget_without_weather_uses_labelled_default() (+49 more)

### Community 67 - "Notes scrubber (personal details)"
Cohesion: 0.25
Nodes (9): ScrubResult, engine(), _known_patterns(), _presidio_analyzer(), scrub(), Pattern, Notes scrubber (SDD 8.4, NFR-15): inspector notes -> notes_redacted before any…, presidio=False runs only the Malaysian recognisers (for templated text whose… (+1 more)

### Community 68 - "Web dependencies"
Cohesion: 0.06
Nodes (31): dependencies, @fontsource/ibm-plex-sans, @fontsource/space-grotesk, leaflet, lucide-react, react, react-dom, react-leaflet (+23 more)

### Community 69 - "Data manager and job buttons"
Cohesion: 0.14
Nodes (21): pollJob(), post(), JobButton(), start(), reset(), openCase(), int(), act() (+13 more)

### Community 70 - "Shared UI components and labels"
Cohesion: 0.09
Nodes (43): bandPath(), BarChart(), CategoryBars(), LineChart(), niceTicks(), scale(), VoltageStrip(), Confidence() (+35 more)

### Community 71 - "Database connections and Telegram dispatch bot"
Cohesion: 0.11
Nodes (32): ActionRefused, test_FR_AD_01_database_enforces_region_and_pii_rules(), test_FR_UI_03_unclaimed_case_masked_for_every_analyst(), test_FR_AD_01_training_labels_and_hit_rates_are_region_limited(), admin_connection(), app_connection(), audit(), _pool() (+24 more)

### Community 72 - "RAG indexing (rag.py)"
Cohesion: 0.20
Nodes (14): Passage, test_FR_AG_04_field_assistant_mode_says_who_answered(), test_FR_AG_06_no_tools_to_act_and_requests_refused(), keyword_overlap(), allow(), answer(), extractive_answer(), search() (+6 more)

### Community 73 - "Back-test script"
Cohesion: 0.23
Nodes (11): cut(), known_cases_active(), known_cases_simulated(), main(), replay_frame(), write_replay(), date, timedelta (+3 more)

### Community 74 - "PDF export"
Cohesion: 0.28
Nodes (8): test_FR_UI_05_pdf_fallback_without_a_browser(), _chromium(), _fpdf(), html_to_pdf(), Without Chromium (e.g. a minimal image) the export still produces a PDF with…, HTML -> PDF for approved case reports (FR-UI-05): Playwright (Chromium) with an…, Returns (pdf bytes, engine). Playwright first; fpdf2 text rendering if no…, html

### Community 75 - "Case API routes and My work"
Cohesion: 0.08
Nodes (52): Assignment, Decision, NewCase, Outcome, Caller, not_found(), audit_log(), dataset_activate() (+44 more)

### Community 76 - "Audit chain and daily anchor"
Cohesion: 0.16
Nodes (17): VerifyResult, test_FR_AD_02_NFR_12_audit_logged_and_tampering_detected(), audit_verify(), anchor_dir(), row_hash(), row_text(), verify(), write_anchor() (+9 more)

### Community 77 - "Active sources and dataset versions"
Cohesion: 0.17
Nodes (22): SourceError, datasets(), data_root(), activate_dataset(), dataset_versions(), datasets_root(), load_table(), resolve_upload() (+14 more)

### Community 78 - "Model API and retraining"
Cohesion: 0.12
Nodes (22): acknowledge(), alerts(), models(), retrain(), weekly(), weekly_html(), weekly_pdf(), hit_rates() (+14 more)

### Community 79 - "Case workflow tests"
Cohesion: 0.15
Nodes (14): case_job(), find(), test_FR_AG_02_dispatch_suggestion_claim_and_approval(), test_FR_AG_02_reminder_then_escalation_on_demo_timers(), test_FR_IW_01_case_job_creates_threshold_cases(), test_FR_IW_01_manual_cases_and_only_supervisor_assigns(), test_FR_IW_02_FR_IW_03_FR_IW_04_outcomes_status_and_labels(), test_FR_IW_05_random_sample_presented_as_routine_check() (+6 more)

### Community 80 - "Pattern model and autoencoder"
Cohesion: 0.21
Nodes (15): PatternModel, auc(), load(), model_path(), sgcc_training_set(), synthetic_training_set(), train(), train_default() (+7 more)

### Community 81 - "Power BI build guide"
Cohesion: 0.33
Nodes (5): Before you start (5 minutes), Build the Power BI dashboard with Claude on your laptop, Check the result, If Claude cannot open Power BI, Prompt to paste into Claude (Cowork / Desktop on the laptop)

### Community 82 - "Analyst chatbot (query templates)"
Cohesion: 0.13
Nodes (22): QueryError, Template, ask(), _ask_model(), _chart_choice(), _model_params(), _num(), other_region_named() (+14 more)

### Community 83 - "API security and UI upgrade tests"
Cohesion: 0.11
Nodes (25): login(), fake_names(), test_data_manager_upload_validates_and_versions(), test_FR_AD_01_role_and_region_refusals(), test_FR_AD_03_threshold_change_applies_on_rerun(), test_FR_PS_07_suspects_reasons_add_up(), test_FR_UI_01_overview_zone_level_in_gap_order(), test_FR_UI_02_zone_view_balance_and_profile() (+17 more)

### Community 84 - "Compose: Ollama"
Cohesion: 0.50
Nodes (4): image, restart, volumes, ollama

### Community 85 - "Canonical schema and upload validation"
Cohesion: 0.15
Nodes (19): Column, Table, Issue, ValidationReport, _check_duplicates(), _check_intervals(), _check_links(), _check_values() (+11 more)

### Community 86 - "Zone API routes"
Cohesion: 0.09
Nodes (41): latest_run_date(), premise_view(), _usage(), _zone(), zone_balance(), zone_cleared(), zone_suspects(), zone_voltage() (+33 more)

### Community 87 - "Household load profiles"
Cohesion: 0.10
Nodes (28): ZoneSim, fake_address(), fake_name(), fake_phone(), _bump(), daily_levels(), household_load_kw(), london_shapes() (+20 more)

### Community 88 - "Inspector app and API client"
Cohesion: 0.09
Nodes (39): ApiError, patch(), request(), setSession(), signIn(), signInDemo(), signOut(), AskBox() (+31 more)

### Community 89 - "Inspector encrypted offline store"
Cohesion: 0.32
Nodes (13): cryptoKey(), enforceMaxAge(), get(), keys(), openDb(), put(), rawDelete(), rawGet() (+5 more)

### Community 90 - "Autoencoder and model training"
Cohesion: 0.16
Nodes (16): Autoencoder, test_FR_DI_07_district_weather_loaded_and_used(), load(), model_path(), save(), train(), train_from_simulation(), week_vector() (+8 more)

### Community 91 - "Review and test report"
Cohesion: 0.18
Nodes (10): 1. Does the build meet the SRS and SDD?, 2. End-to-end test: every use case, every account, 3. Bugs found and fixed, 4. Remaining unfinished task: done, 5. Suggested improvements, 6. How to repeat the test, 7. Second round (after the review): what was added and rechecked, Features (+2 more)

### Community 92 - "Test fixtures and seeded users"
Cohesion: 0.11
Nodes (25): api(), cfg(), demo_run(), demo_run_all(), demo_sim(), models(), pg(), test_NFR_03_no_endpoint_blocks_the_event_loop() (+17 more)

### Community 93 - "Zone simulator"
Cohesion: 0.07
Nodes (56): Injected, Scenario, ZoneSpec, _run(), test_FR_DI_01_readings_round_trip_match_generator(), test_FR_DI_06_missing_day_flags_meter(), test_FR_ZD_02_large_load_priority(), test_FR_ZD_05_many_conventional_meters_still_flag_mining() (+48 more)

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
Cohesion: 0.27
Nodes (11): message(), new_case(), test_FR_AD_01_chat_is_for_supervisors_inspectors_and_managers(), test_FR_AG_02_cannot_attend_tells_the_supervisor(), test_FR_AG_02_decision_on_the_case_page_closes_the_chat_buttons(), test_FR_AG_02_real_bot_links_a_chat_and_answers_a_button(), test_FR_AG_02_supervisor_approves_and_team_answers_from_the_chat(), parametrize (+3 more)

### Community 100 - "UI upgrade brief"
Cohesion: 0.11
Nodes (17): 0. Ground rules, 1. Visual direction: "network control room", 2. Pages to redesign, 3.10 Today's route (Could), 3.11 Landlord alert concept (Could, mock only), 3.1 RM at risk (Must), 3.2 Feeder schematic (Must), 3.3 Reason waterfall (Must) (+9 more)

### Community 101 - "Dataset and document download scripts"
Cohesion: 0.23
Nodes (10): apply_overrides(), fetch_kaggle(), fetch_url(), main(), manual(), Try to download the public datasets (prompt 3.2). Never blocks: on failure it…, `downloads: {london: <kaggle slug>, sgcc: <kaggle slug>}` in…, Download the public documents for RAG (data/docs_rag/sources.yaml) into… (+2 more)

### Community 104 - "Labels (EN/BM) and solar wording"
Cohesion: 0.12
Nodes (21): SolarCheck(), checkValue(), pc(), share(), stillSuspect(), verdictText(), files(), usedKeys() (+13 more)

### Community 105 - "Database tables and reporting views"
Cohesion: 0.08
Nodes (29): account_event, customer_pii, detection_run, district_weather, duty_roster, historic_outcome, meter, meter_monthly_reading (+21 more)

### Community 106 - "RAG indexing (rag.py)"
Cohesion: 0.13
Nodes (24): test_NFR_15_planted_instruction_in_retrieved_text_is_data(), quote_retrieved(), case_summary_text(), collect_documents(), _front_matter(), index_case_summaries(), index_documents(), _pdf_text() (+16 more)

### Community 107 - "Power BI dashboard layout"
Cohesion: 0.25
Nodes (7): Connect Power BI Desktop, Manager dashboard in Power BI (R0), Page 1: Network overview, Page 2: Leaking zones, Page 3: Cases and hit rates, R1, Views

### Community 108 - "Sign-in, sessions and file storage"
Cohesion: 0.11
Nodes (24): SignIn, AuthError, Session, current_session(), me(), remote_sign_out(), sign_in(), sign_out() (+16 more)

### Community 109 - "Upload area guide"
Cohesion: 0.33
Nodes (5): How to upload, Upload area: bring your own datasets, Versions, What to upload, What validation checks

### Community 110 - "Language model, seed and demo command"
Cohesion: 0.19
Nodes (14): Completion, PromptBlocked, test_FR_AG_03_live_model_choice_is_cleaned_and_labelled(), test_NFR_15_model_never_receives_personal_details(), test_NFR_15_model_output_with_personal_details_is_blocked(), available(), check_prompt(), complete() (+6 more)

### Community 111 - "Agent safety tests and PDF export"
Cohesion: 0.10
Nodes (17): reporting_case(), test_FR_AG_01_draft_has_placeholders_only_and_cites_the_act(), test_FR_AG_01_FR_UI_05_two_approvals_then_pdf_with_details(), test_FR_AG_01_manager_sees_evidence_photos_only_for_export_approval(), test_FR_AG_03_answers_carry_a_chart_and_a_sentence_from_the_rows(), test_FR_AG_03_chatbot_answers_with_query_and_refuses_other_region(), test_FR_AG_04_field_assistant_cites_or_says_not_found(), test_FR_AG_05_three_similar_closed_cases() (+9 more)

### Community 112 - "Graph naming and traceability scripts"
Cohesion: 0.36
Nodes (7): community_index(), describe(), main(), match(), Apply curated community names to the graphify graph without re-clustering.…, Per community: its main files (most nodes; ties all count) and node labels, for…, First rule whose `file` is one of the community's main files and whose `has`…

### Community 113 - "Public RAG document list"
Cohesion: 0.25
Nodes (7): documents, id, manual, owner, role_scope, title, url

### Community 114 - "Field assistant guide"
Cohesion: 0.29
Nodes (6): 1. What a flagged zone means, 2. Flat 24/7 gap, 3. Risk scores and reasons, 4. Voltage evidence, 5. Routine meter checks, 6. Recording outcomes

### Community 115 - "CLI commands and audit chain"
Cohesion: 0.13
Nodes (21): test_NFR_07_rpt_views_hold_no_premise_ids_or_personal_details(), demo_passwords(), cmd_simreport(), cmd_train_models(), cmd_tune(), command(), main(), migrate() (+13 more)

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
Cohesion: 0.23
Nodes (11): cmd_sources(), active_sources(), fallbacks(), health(), _upload_checks(), Any, Connection, Data health per table for the Data manager (UI brief 3.9): how the data was… (+3 more)

### Community 123 - "Monitoring and alerts"
Cohesion: 0.25
Nodes (10): after_detection(), _alert(), check_unusual_access(), collect(), psi(), ndarray, Monitoring and alerts for the data team (FR-ML-03, SDD 9.2, NFR-11). After each…, What monitoring needs from a detection run, small enough to keep across zone… (+2 more)

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

### Community 130 - "Airflow nightly DAG"
Cohesion: 0.40
Nodes (3): Full profile only: the nightly pipeline as an Airflow DAG (SDD 6.1). In the…, airflow_operators_python, requests

### Community 131 - "Compose: token tunnel"
Cohesion: 0.25
Nodes (8): TUNNEL_TOKEN, tunnel-token, command, depends_on, environment, image, profiles, restart

### Community 133 - "Scoring and reasons"
Cohesion: 0.22
Nodes (11): Reason, Score, test_FR_PS_07_voltage_reason_at_the_premise_reads_naturally(), test_FR_PS_10_penalty_rule_follows_settings(), reason_text(), score_premise(), solar_timing_text(), solar_unexplained_text() (+3 more)

### Community 134 - "Assistant page and query charts"
Cohesion: 0.29
Nodes (7): QueryChart(), Answer(), download(), Assistant(), ask(), csv(), EXAMPLES

### Community 135 - "Weekly report and message tests"
Cohesion: 0.32
Nodes (7): fake_names(), test_weekly_job_reaches_every_manager_and_supervisor(), test_weekly_report_page_explains_itself_in_both_languages(), test_weekly_summary_is_zone_level_and_region_limited(), test_weekly_summary_pdf_and_message(), test_SRS_5_2_dispatch_messages_hold_no_customer_details(), Weekly manager summary: region-limited, zone-level, no personal details, PDF…

### Community 136 - "Demo guide and reset"
Cohesion: 0.13
Nodes (21): cmd_demo(), accounts(), guide_config(), reset(), reset_time(), status(), reset_rehearsal(), predraft_demo_report() (+13 more)

### Community 137 - "API app, scheduler and lifespan"
Cohesion: 0.08
Nodes (27): lifespan(), close_pools(), register(), _safe(), start(), stop(), start_polling(), stop_polling() (+19 more)

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
Cohesion: 0.47
Nodes (5): expand(), main(), requirements(), Generate TRACEABILITY.md: every SRS requirement mapped to the code and tests…, collections

### Community 143 - "UI and weekly report change log"
Cohesion: 0.20
Nodes (9): Checks, Design system (section 1), Fixed on the way, New features (section 3), Pages (section 2), Tests, UI upgrade: before and after, Weekly summary report: before and after (+1 more)

### Community 144 - "Rooftop solar schemes explainer (RAG)"
Cohesion: 0.29
Nodes (6): NEM (Net Energy Metering), SelCo (self-consumption), Solar ATAP, Sources, What to check on site, Why it matters for an inspection

### Community 145 - "UI upgrade plan"
Cohesion: 0.50
Nodes (3): Order of work, Rules kept, UI upgrade plan (`VoltGuard_UI_Upgrade_Prompt.md`)

### Community 149 - "Agent guardrails"
Cohesion: 0.18
Nodes (11): OutputBlocked, ToolNotAllowed, asks_forbidden_action(), check_output(), check_document(), Exception, Agent guardrails (SDD 8.4, FR-AG-06, NFR-15). * Fixed tool list per agent. No…, Block personal details in anything an agent returns (placeholders such as… (+3 more)

### Community 151 - "Learning and monitoring tests"
Cohesion: 0.25
Nodes (5): test_FR_ML_01_FR_ML_02_retrain_records_version_with_both_hit_rates(), test_unusual_access_alert(), Learning and monitoring (SRS FR-ML-01-03, FR-IW-04)., Test accounts: one per role and region from config/demo.yaml, plus the pipeline…, psycopg

### Community 154 - "Telegram tables"
Cohesion: 0.50
Nodes (3): app_user, telegram_link_code, telegram_state

## Knowledge Gaps
- **664 isolated node(s):** `Template`, `DONE`, `TITLES`, `FILTER_LABEL`, `FILTERS` (+659 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Caller` connect `Case API routes and My work` to `Configuration loader`, `Weekly report and message tests`, `API app, scheduler and lifespan`, `Case workflow and notifications`, `Dataset ingest`, `Local test stack and browser tests`, `Background job runner (one heavy job at a time)`, `Inspection route planner`, `Telegram API routes`, `UI upgrade API (meta, demo, back-test)`, `Case report agent and approvals`, `Weekly summary report`, `Agent API routes`, `Database connections and Telegram dispatch bot`, `RAG indexing (rag.py)`, `Audit chain and daily anchor`, `Active sources and dataset versions`, `Model API and retraining`, `Case workflow tests`, `Analyst chatbot (query templates)`, `API security and UI upgrade tests`, `Zone API routes`, `Test fixtures and seeded users`, `RAG indexing (rag.py)`, `Sign-in, sessions and file storage`, `Agent safety tests and PDF export`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `login()` connect `API security and UI upgrade tests` to `Telegram bot tests`, `Database connections and Telegram dispatch bot`, `RAG indexing (rag.py)`, `Weekly report and message tests`, `RAG indexing (rag.py)`, `Audit chain and daily anchor`, `Detection and solar tests`, `Agent safety tests and PDF export`, `Case workflow tests`, `Learning and monitoring tests`, `Test fixtures and seeded users`, `Zone simulator`, `Weekly summary report`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Why does `ZoneInput` connect `Detection engine (balance, features, zone input)` to `Back-test script`, `Autoencoder and model training`, `Network loss model and zone inputs`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 102 inferred relationships involving `Caller` (e.g. with `LocalStack` and `ask()`) actually correct?**
  _`Caller` has 102 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Template`, `DONE`, `TITLES` to the rest of the system?**
  _664 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Web data loading (cases, dispatch)` be split into smaller, more focused modules?**
  _Cohesion score 0.09061224489795919 - nodes in this community are weakly interconnected._
- **Should `SDD: software design document` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._