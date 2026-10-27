# Graph Report - F-35  (2026-10-27)

## Corpus Check
- 56 files · ~48,656 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: .csv 11, (none) 4, .example 1)

## Summary
- 1091 nodes · 1948 edges · 77 communities (73 shown, 4 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 115 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5e430be1`
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
- test_detection.py
- weights
- zone
- ingest.py
- Simulation report
- VoltGuard AI R0: build plan
- scrape_configs
- thresholds.yaml
- voltguard_nightly.py
- config.example.yml
- Hand-off: VoltGuard AI R0 build
- VoltGuard AI (R0 prototype)
- dispatch
- features
- Deviations from the SDD
- make.ps1
- cases
- penalties
- voltage
- handoff.sh
- tunnel.sh
- worker
- profiles.py
- db
- services
- keycloak
- minio
- airflow
- tunnel-named
- proxy
- tunnel
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
- meter_id
- month
- transformer_id
- distance_m
- dtm_accuracy_class
- kwh
- api
- environment
- capacity_kva
- kwh_supplied
- temperature_c
- voltage_v
- lat
- lon
- phase
- quality_flag
- docker-compose.yml
- has_dtm
- outcome
- premise_type
- street_seq
- tariff
- ts

## God Nodes (most connected - your core abstractions)
1. `simulate_zone()` - 28 edges
2. `ingest()` - 26 edges
3. `ZoneInput` - 26 edges
4. `Requirements` - 26 edges
5. `build_features()` - 24 edges
6. `Scenario` - 19 edges
7. `ValidationReport` - 19 edges
8. `locate()` - 19 edges
9. `simulation_report()` - 19 edges
10. `run_zones()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `3.1 Canonical schema (the only thing the pipeline reads)` --references--> `duty_roster()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/voltguard/data/simulator.py
- `Library swaps` --references--> `change_point()`  [INFERRED]
  DEVIATIONS.md → backend/voltguard/detection/balance.py
- `Requirements` --references--> `test_FR_DI_06_upload_with_missing_intervals_flags_meter()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_data_layer.py
- `Requirements` --references--> `test_FR_ZD_02_taps_flagged_clean_zones_not()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_detection.py
- `Requirements` --references--> `test_FR_ZD_03_gap_start_estimated_or_present_since_start()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_detection.py

## Import Cycles
- None detected.

## Communities (77 total, 4 thin omitted)

### Community 0 - "numpy"
Cohesion: 0.06
Nodes (39): recorded_params(), _timestamps(), balance_zone(), BalanceResult, change_point(), data_quality_flags(), _days_in(), estimate_conventional() (+31 more)

### Community 1 - "config.py"
Cohesion: 0.09
Nodes (27): admin_database_url(), config_dir(), data_path(), data_root(), data_sources(), database_url(), deep_merge(), demo_config() (+19 more)

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
Cohesion: 0.21
Nodes (11): test_sgcc_adapter_feeds_pattern_model(), auc(), load(), model_path(), PatternModel, reset_cache(), sgcc_training_set(), synthetic_training_set() (+3 more)

### Community 7 - "tables"
Cohesion: 0.08
Nodes (24): downloads, london, sgcc, london, households, region, zone_size, pattern_training (+16 more)

### Community 8 - "Build the VoltGuard AI prototype (R0)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "test_data_layer.py"
Cohesion: 0.06
Nodes (33): isolated(), small_scenario(), test_bad_upload_is_rejected_with_reasons(), test_column_map_units_and_timezone(), test_FR_DI_06_upload_with_missing_intervals_flags_meter(), test_london_adapter_profiles_and_canonical_tables(), test_missing_voltage_and_phase_use_fallbacks(), test_switch_to_uploaded_dataset_without_code_changes() (+25 more)

### Community 10 - "cli.py"
Cohesion: 0.10
Nodes (17): cmd_detect(), cmd_simreport(), cmd_train_models(), cmd_tune(), command(), main(), cmd_activate(), cmd_convert() (+9 more)

### Community 11 - "teams"
Cohesion: 0.12
Nodes (16): demo_seed, demo_zone, regions, code, name, teams, base_lat, base_lon (+8 more)

### Community 12 - "test_detection.py"
Cohesion: 0.06
Nodes (57): case_premise(), cfg(), demo_run(), demo_run_all(), demo_sim(), rank_of(), top_k(), _run() (+49 more)

### Community 13 - "weights"
Cohesion: 0.10
Nodes (20): _tuning, objective, seed, split, tuned_at, zones, weights, anomaly (+12 more)

### Community 14 - "zone"
Cohesion: 0.18
Nodes (11): zone, change_min_segment_days, change_min_shift_share, consecutive_days, conventional_daily_cv, flat_cv, large_load_share, loss_model_error_share (+3 more)

### Community 15 - "ingest.py"
Cohesion: 0.05
Nodes (46): test_datagovmy_adapter_month_factors(), _columns(), convert(), month_factors(), month_factors_from(), processed(), raw_dir(), _stamp() (+38 more)

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

### Community 21 - "config.example.yml"
Cohesion: 0.33
Nodes (5): credentials-file, ingress, hostname, service, tunnel

### Community 22 - "Hand-off: VoltGuard AI R0 build"
Cohesion: 0.29
Nodes (6): Auto-generated state (scripts/handoff.sh), Decisions to keep, File tree, Hand-off: VoltGuard AI R0 build, How to resume in a new session, Known issues (from the review at the start of this session)

### Community 23 - "VoltGuard AI (R0 prototype)"
Cohesion: 0.33
Nodes (5): Data modes, Development without Docker, Documents, Quick start (Windows laptop), VoltGuard AI (R0 prototype)

### Community 24 - "dispatch"
Cohesion: 0.40
Nodes (5): dispatch, demo_escalation_minutes, demo_reminder_minutes, escalation_hours, reminder_hours

### Community 25 - "features"
Cohesion: 0.40
Nodes (5): features, history_weeks, recent_days, timing_tau_days, zero_kwh

### Community 26 - "Deviations from the SDD"
Cohesion: 0.40
Nodes (4): Data, Deviations from the SDD, Library swaps, Lite-profile swaps (prompt 7.2)

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
Cohesion: 0.20
Nodes (11): build, context, dockerfile, worker, build, build, command, depends_on (+3 more)

### Community 34 - "profiles.py"
Cohesion: 0.12
Nodes (11): fake_address(), fake_name(), fake_phone(), _bump(), daily_levels(), household_load_kw(), london_shapes(), _night_block() (+3 more)

### Community 35 - "db"
Cohesion: 0.15
Nodes (13): environment, healthcheck, image, ports, restart, volumes, POSTGRES_DB, POSTGRES_PASSWORD (+5 more)

### Community 36 - "services"
Cohesion: 0.15
Nodes (13): image, profiles, image, restart, volumes, image, profiles, services (+5 more)

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

### Community 42 - "tunnel"
Cohesion: 0.33
Nodes (6): tunnel, command, depends_on, image, profiles, restart

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
Cohesion: 0.12
Nodes (17): required, type, case_id, notes, origin, reason_tag, recorded_at, columns (+9 more)

### Community 47 - "premise_id"
Cohesion: 0.12
Nodes (16): installed_on, meter_type, premise_id, read_frequency, required, type, columns, allowed (+8 more)

### Community 48 - "columns"
Cohesion: 0.13
Nodes (15): columns, description, key, event_date, event_id, event_type, required, type (+7 more)

### Community 49 - "tables"
Cohesion: 0.15
Nodes (12): description, key, description, key, description, key, tables, duty_roster (+4 more)

### Community 50 - "columns"
Cohesion: 0.15
Nodes (13): required, type, address, contact, holder_name, required, type, columns (+5 more)

### Community 51 - "sunshine_hours"
Cohesion: 0.15
Nodes (13): district, sunshine_hours, required, type, columns, description, key, max (+5 more)

### Community 52 - "columns"
Cohesion: 0.17
Nodes (12): loss_params, region, description, required, type, description, required, type (+4 more)

### Community 53 - "columns"
Cohesion: 0.25
Nodes (8): feeder_branch, description, required, type, columns, description, key, premise

### Community 54 - "meter_id"
Cohesion: 0.25
Nodes (8): meter_id, description, required, type, columns, description, key, meter_reading

### Community 55 - "month"
Cohesion: 0.25
Nodes (8): month, columns, description, key, description, required, type, meter_monthly_reading

### Community 56 - "transformer_id"
Cohesion: 0.25
Nodes (8): transformer_id, transformer_reading, description, required, type, columns, description, key

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

### Community 63 - "kwh_supplied"
Cohesion: 0.33
Nodes (6): kwh_supplied, max, min, required, type, unit

### Community 64 - "temperature_c"
Cohesion: 0.33
Nodes (6): temperature_c, max, min, required, type, unit

### Community 65 - "voltage_v"
Cohesion: 0.33
Nodes (6): voltage_v, max, min, required, type, unit

### Community 66 - "lat"
Cohesion: 0.40
Nodes (5): lat, max, min, required, type

### Community 67 - "lon"
Cohesion: 0.40
Nodes (5): lon, max, min, required, type

### Community 68 - "phase"
Cohesion: 0.40
Nodes (5): phase, allowed, description, required, type

### Community 69 - "quality_flag"
Cohesion: 0.40
Nodes (5): quality_flag, allowed, description, required, type

### Community 70 - "docker-compose.yml"
Cohesion: 0.40
Nodes (4): name, volumes, minio, pgdata

### Community 71 - "has_dtm"
Cohesion: 0.50
Nodes (4): has_dtm, description, required, type

### Community 72 - "outcome"
Cohesion: 0.50
Nodes (4): outcome, allowed, required, type

### Community 73 - "premise_type"
Cohesion: 0.50
Nodes (4): premise_type, allowed, required, type

### Community 74 - "street_seq"
Cohesion: 0.50
Nodes (4): street_seq, description, required, type

### Community 75 - "tariff"
Cohesion: 0.50
Nodes (4): tariff, allowed, required, type

### Community 76 - "ts"
Cohesion: 0.50
Nodes (4): ts, description, required, type

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `columns` connect `sunshine_hours` to `numpy`, `temperature_c`?**
  _High betweenness centrality (0.213) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `simulate_zone()` (e.g. with `.transformer_id()` and `ZoneNetwork`) actually correct?**
  _`simulate_zone()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `numpy` be split into smaller, more focused modules?**
  _Cohesion score 0.058672276764843385 - nodes in this community are weakly interconnected._
- **Why does `date` connect `numpy` to `test_data_layer.py`, `sunshine_hours`, `test_detection.py`?**
  _High betweenness centrality (0.211) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `ingest()` (e.g. with `.ok()` and `.to_html()`) actually correct?**
  _`ingest()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `config.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08973172987974098 - nodes in this community are weakly interconnected._
- **Why does `tables` connect `tables` to `columns`, `columns`, `sunshine_hours`, `columns`, `columns`, `meter_id`, `month`, `transformer_id`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._