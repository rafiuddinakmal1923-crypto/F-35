# Graph Report - F-35  (2026-10-27)

## Corpus Check
- 79 files · ~60,992 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: .csv 11, (none) 4, .example 1)

## Summary
- 1351 nodes · 2683 edges · 86 communities (80 shown, 6 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 151 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `eca82133`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- numpy
- config.py
- weights
- VoltGuard AI: Software Design Document (SDD)
- columns
- 3. Functional requirements
- cli.py
- tables
- Build the VoltGuard AI prototype (R0)
- test_data_layer.py
- cli.py
- teams
- polars
- weights
- zone
- ValidationReport
- Simulation report
- VoltGuard AI R0: build plan
- scrape_configs
- thresholds.yaml
- auth.py
- config.example.yml
- Hand-off: VoltGuard AI R0 build
- VoltGuard AI (R0 prototype)
- dispatch
- features
- routes_auth.py
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
- pipeline.py
- month
- kwh_supplied
- distance_m
- dtm_accuracy_class
- kwh
- api
- environment
- capacity_kva
- routes_admin.py
- ingest.py
- voltage_v
- lat
- lon
- phase
- routes_zones.py
- conftest.py
- has_dtm
- test_api_security.py
- premise_type
- street_seq
- tariff
- audit.py
- sources.py
- scheduler.py
- run_detection
- commands.py
- re
- create_app
- ollama

## God Nodes (most connected - your core abstractions)
1. `Caller` - 37 edges
2. `simulate_zone()` - 28 edges
3. `ingest()` - 27 edges
4. `ZoneInput` - 26 edges
5. `Requirements` - 26 edges
6. `build_features()` - 24 edges
7. `run_detection()` - 22 edges
8. `ValidationReport` - 21 edges
9. `command()` - 19 edges
10. `data_root()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `7.2 Compose profiles` --references--> `api()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/tests/conftest.py
- `3.1 Canonical schema (the only thing the pipeline reads)` --references--> `duty_roster()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/voltguard/data/simulator.py
- `Requirements` --references--> `test_FR_DI_06_upload_with_missing_intervals_flags_meter()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_data_layer.py
- `Requirements` --references--> `test_FR_ZD_02_taps_flagged_clean_zones_not()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_detection.py
- `Requirements` --references--> `test_FR_ZD_02_large_load_priority()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_detection.py

## Import Cycles
- None detected.

## Communities (86 total, 6 thin omitted)

### Community 0 - "numpy"
Cohesion: 0.06
Nodes (39): recorded_params(), balance_zone(), BalanceResult, change_point(), data_quality_flags(), _days_in(), estimate_conventional(), fill_smart_readings() (+31 more)

### Community 1 - "config.py"
Cohesion: 0.07
Nodes (33): health(), admin_database_url(), config_dir(), data_path(), data_root(), data_sources(), database_url(), deep_merge() (+25 more)

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

### Community 6 - "cli.py"
Cohesion: 0.11
Nodes (19): test_sgcc_adapter_feeds_pattern_model(), cmd_train_models(), Autoencoder, load(), model_path(), save(), train(), train_from_simulation() (+11 more)

### Community 7 - "tables"
Cohesion: 0.08
Nodes (24): downloads, london, sgcc, london, households, region, zone_size, pattern_training (+16 more)

### Community 8 - "Build the VoltGuard AI prototype (R0)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "test_data_layer.py"
Cohesion: 0.15
Nodes (14): isolated(), test_bad_upload_is_rejected_with_reasons(), test_column_map_units_and_timezone(), test_FR_DI_06_upload_with_missing_intervals_flags_meter(), test_london_adapter_profiles_and_canonical_tables(), test_missing_voltage_and_phase_use_fallbacks(), test_switch_to_uploaded_dataset_without_code_changes(), test_upload_templates_are_a_valid_dataset() (+6 more)

### Community 10 - "cli.py"
Cohesion: 0.21
Nodes (8): cmd_detect(), cmd_simreport(), cmd_tune(), command(), main(), cmd_activate(), cmd_convert(), load_truth()

### Community 11 - "teams"
Cohesion: 0.12
Nodes (16): demo_seed, demo_zone, regions, code, name, teams, base_lat, base_lon (+8 more)

### Community 12 - "polars"
Cohesion: 0.07
Nodes (46): case_premise(), rank_of(), top_k(), test_datagovmy_adapter_month_factors(), test_detection_creates_no_cases(), test_FR_DI_01_readings_round_trip_match_generator(), test_FR_DI_02_voltage_for_smart_meters_only(), test_FR_DI_03_supply_equals_homes_plus_loss_plus_taps() (+38 more)

### Community 13 - "weights"
Cohesion: 0.10
Nodes (20): _tuning, objective, seed, split, tuned_at, zones, weights, anomaly (+12 more)

### Community 14 - "zone"
Cohesion: 0.18
Nodes (11): zone, change_min_segment_days, change_min_shift_share, consecutive_days, conventional_daily_cv, flat_cv, large_load_share, loss_model_error_share (+3 more)

### Community 15 - "ValidationReport"
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

### Community 20 - "auth.py"
Cohesion: 0.06
Nodes (24): _bin(), _free_port(), TempPostgres, AuthError, check_password(), generate_password(), hash_password(), issue_token() (+16 more)

### Community 21 - "config.example.yml"
Cohesion: 0.33
Nodes (5): credentials-file, ingress, hostname, service, tunnel

### Community 22 - "Hand-off: VoltGuard AI R0 build"
Cohesion: 0.25
Nodes (7): Auto-generated state (scripts/handoff.sh), Decisions to keep, File tree, Hand-off: VoltGuard AI R0 build, How to resume in a new session, Known issues (from the review at the start of this session), Status by milestone (PLAN.md)

### Community 23 - "VoltGuard AI (R0 prototype)"
Cohesion: 0.33
Nodes (5): Data modes, Development without Docker, Documents, Quick start (Windows laptop), VoltGuard AI (R0 prototype)

### Community 24 - "dispatch"
Cohesion: 0.40
Nodes (5): dispatch, demo_escalation_minutes, demo_reminder_minutes, escalation_hours, reminder_hours

### Community 25 - "features"
Cohesion: 0.40
Nodes (5): features, history_weeks, recent_days, timing_tau_days, zero_kwh

### Community 26 - "routes_auth.py"
Cohesion: 0.12
Nodes (17): ApiError, caller(), conflict(), connection(), current_session(), forbidden(), not_found(), require() (+9 more)

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
Cohesion: 0.07
Nodes (35): small_scenario(), _run(), test_FR_ZD_02_large_load_priority(), test_FR_ZD_05_many_conventional_meters_still_flag_mining(), cmd_simulate(), fake_address(), fake_name(), fake_phone() (+27 more)

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
Cohesion: 0.11
Nodes (11): test_FR_AD_01_database_enforces_region_and_pii_rules(), run_detection(), admin_connection(), app_connection(), database_name(), _pool(), _run(), running() (+3 more)

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
Cohesion: 0.12
Nodes (16): district, sunshine_hours, temperature_c, required, type, columns, max, min (+8 more)

### Community 52 - "columns"
Cohesion: 0.17
Nodes (12): loss_params, region, description, required, type, description, required, type (+4 more)

### Community 53 - "columns"
Cohesion: 0.25
Nodes (8): feeder_branch, description, required, type, columns, description, key, premise

### Community 54 - "pipeline.py"
Cohesion: 0.15
Nodes (13): _known_patterns(), _presidio_analyzer(), scrub(), ScrubResult, copy_in(), copy_out(), _csv(), _jsonable() (+5 more)

### Community 55 - "month"
Cohesion: 0.17
Nodes (12): meter_id, month, description, required, type, columns, description, key (+4 more)

### Community 56 - "kwh_supplied"
Cohesion: 0.11
Nodes (18): kwh_supplied, transformer_id, ts, max, min, required, type, unit (+10 more)

### Community 57 - "distance_m"
Cohesion: 0.29
Nodes (7): distance_m, description, max, min, required, type, unit

### Community 58 - "dtm_accuracy_class"
Cohesion: 0.29
Nodes (7): dtm_accuracy_class, description, max, min, required, type, unit

### Community 59 - "kwh"
Cohesion: 0.29
Nodes (7): kwh, description, max, min, required, type, unit

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
Cohesion: 0.17
Nodes (16): bad_request(), audit_log(), audit_verify(), dataset_activate(), dataset_preview(), dataset_report(), datasets(), get_thresholds() (+8 more)

### Community 64 - "ingest.py"
Cohesion: 0.14
Nodes (13): schema_document(), build_tables(), _checksum(), cmd_ingest(), cmd_upload_kit(), context_for(), IngestResult, load_column_map() (+5 more)

### Community 65 - "voltage_v"
Cohesion: 0.13
Nodes (15): quality_flag, voltage_v, columns, description, key, allowed, description, required (+7 more)

### Community 66 - "lat"
Cohesion: 0.40
Nodes (5): lat, max, min, required, type

### Community 67 - "lon"
Cohesion: 0.40
Nodes (5): lon, max, min, required, type

### Community 68 - "phase"
Cohesion: 0.40
Nodes (5): phase, allowed, description, required, type

### Community 69 - "routes_zones.py"
Cohesion: 0.17
Nodes (11): latest_run_date(), premise_view(), _usage(), _zone(), zone_balance(), zone_suspects(), zone_voltage(), zones() (+3 more)

### Community 70 - "conftest.py"
Cohesion: 0.15
Nodes (10): api(), cfg(), demo_run(), demo_run_all(), demo_sim(), pg(), demo_passwords(), cmd_seed_users() (+2 more)

### Community 71 - "has_dtm"
Cohesion: 0.50
Nodes (4): has_dtm, description, required, type

### Community 72 - "test_api_security.py"
Cohesion: 0.22
Nodes (13): login(), fake_names(), test_data_manager_upload_validates_and_versions(), test_FR_AD_01_role_and_region_refusals(), test_FR_AD_02_NFR_12_audit_logged_and_tampering_detected(), test_FR_AD_03_threshold_change_applies_on_rerun(), test_FR_PS_07_suspects_reasons_add_up(), test_FR_UI_01_overview_zone_level_in_gap_order() (+5 more)

### Community 73 - "premise_type"
Cohesion: 0.50
Nodes (4): premise_type, allowed, required, type

### Community 74 - "street_seq"
Cohesion: 0.50
Nodes (4): street_seq, description, required, type

### Community 75 - "tariff"
Cohesion: 0.50
Nodes (4): tariff, allowed, required, type

### Community 76 - "audit.py"
Cohesion: 0.19
Nodes (8): anchor_dir(), row_hash(), row_text(), verify(), VerifyResult, write_anchor(), cmd_anchor(), cmd_verify_audit()

### Community 77 - "sources.py"
Cohesion: 0.28
Nodes (9): activate_dataset(), dataset_versions(), datasets_root(), load_table(), resolve_upload(), set_source(), simulation_run(), SourceError (+1 more)

### Community 78 - "scheduler.py"
Cohesion: 0.18
Nodes (6): lifespan(), close_pools(), register(), _safe(), start(), stop()

### Community 80 - "run_detection"
Cohesion: 0.31
Nodes (5): cmd_sources(), active_sources(), ensure_simulated(), PipelineError, run_detection()

### Community 81 - "commands.py"
Cohesion: 0.29
Nodes (4): migrate(), _role_password(), cmd_migrate(), cmd_pipeline()

### Community 82 - "re"
Cohesion: 0.67
Nodes (3): expand(), main(), requirements()

### Community 84 - "ollama"
Cohesion: 0.50
Nodes (4): image, restart, volumes, ollama

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `date` connect `routes_zones.py` to `numpy`, `test_data_layer.py`, `simulator.py`, `sunshine_hours`?**
  _High betweenness centrality (0.189) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Caller` (e.g. with `caller()` and `connection()`) actually correct?**
  _`Caller` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `numpy` be split into smaller, more focused modules?**
  _Cohesion score 0.05696636925188744 - nodes in this community are weakly interconnected._
- **Why does `columns` connect `sunshine_hours` to `tables`, `routes_zones.py`?**
  _High betweenness centrality (0.186) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `simulate_zone()` (e.g. with `.transformer_id()` and `ZoneNetwork`) actually correct?**
  _`simulate_zone()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `config.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07393483709273183 - nodes in this community are weakly interconnected._
- **Why does `district_weather` connect `tables` to `sunshine_hours`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._