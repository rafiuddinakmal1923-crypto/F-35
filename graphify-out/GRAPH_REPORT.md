# Graph Report - F-35  (2026-10-27)

## Corpus Check
- 44 files · ~40,336 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .example 1, .ini 1)

## Summary
- 679 nodes · 1201 edges · 46 communities (42 shown, 4 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 90 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8b0000af`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- numpy
- config.py
- weights
- VoltGuard AI: Software Design Document (SDD)
- simulator.py
- 3. Functional requirements
- cli.py
- tables
- Build the VoltGuard AI prototype (R0)
- traceability.py
- anomaly.py
- teams
- test_detection.py
- weights
- zone
- canonical.py
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
- ollama
- prometheus

## God Nodes (most connected - your core abstractions)
1. `simulate_zone()` - 27 edges
2. `ZoneInput` - 26 edges
3. `Requirements` - 25 edges
4. `build_features()` - 24 edges
5. `locate()` - 19 edges
6. `simulation_report()` - 19 edges
7. `run_zones()` - 18 edges
8. `Scenario` - 17 edges
9. `services` - 16 edges
10. `simulate()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `3.1 Canonical schema (the only thing the pipeline reads)` --references--> `duty_roster()`  [INFERRED]
  VoltGuard_ClaudeCode_Prompt.md → backend/voltguard/data/simulator.py
- `Library swaps` --references--> `change_point()`  [INFERRED]
  DEVIATIONS.md → backend/voltguard/detection/balance.py
- `Requirements` --references--> `test_FR_ZD_02_taps_flagged_clean_zones_not()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_detection.py
- `Requirements` --references--> `test_FR_ZD_02_large_load_priority()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_detection.py
- `Requirements` --references--> `test_FR_ZD_03_gap_start_estimated_or_present_since_start()`  [INFERRED]
  TRACEABILITY.md → backend/tests/test_detection.py

## Import Cycles
- None detected.

## Communities (46 total, 4 thin omitted)

### Community 0 - "numpy"
Cohesion: 0.06
Nodes (35): recorded_params(), balance_zone(), BalanceResult, change_point(), data_quality_flags(), _days_in(), estimate_conventional(), fill_smart_readings() (+27 more)

### Community 1 - "config.py"
Cohesion: 0.08
Nodes (28): admin_database_url(), config_dir(), data_path(), data_root(), data_sources(), database_url(), deep_merge(), demo_config() (+20 more)

### Community 2 - "weights"
Cohesion: 0.17
Nodes (12): weights, anomaly, change_from_history, flatness, gap_from_similar, night_to_day, pattern_model, tenancy_change (+4 more)

### Community 3 - "VoltGuard AI: Software Design Document (SDD)"
Cohesion: 0.05
Nodes (39): 10.1 Test levels, 10.2 Simulated zone, 10.3 Stress tests, 10.4 Acceptance criteria, 10.5 Prototype demo for judges, 10. Testing and validation plan, 11.1 Requirements to design, 11.2 Open issues (+31 more)

### Community 4 - "simulator.py"
Cohesion: 0.11
Nodes (24): _run(), test_FR_ZD_02_large_load_priority(), test_FR_ZD_05_many_conventional_meters_still_flag_mining(), cmd_simulate(), fake_address(), fake_name(), fake_phone(), config_tz() (+16 more)

### Community 5 - "3. Functional requirements"
Cohesion: 0.06
Nodes (31): 1.1 Purpose, 1.2 Scope, 1.3 Releases, 1.4 Definitions, 1.5 References, 1. Introduction, 2.1 Product perspective, 2.2 User classes (+23 more)

### Community 6 - "cli.py"
Cohesion: 0.11
Nodes (17): cmd_detect(), cmd_simreport(), cmd_train_models(), cmd_tune(), command(), main(), load_truth(), auc() (+9 more)

### Community 7 - "tables"
Cohesion: 0.11
Nodes (18): london, households, pattern_training, profiles, rescale, simulation, run, tables (+10 more)

### Community 8 - "Build the VoltGuard AI prototype (R0)"
Cohesion: 0.11
Nodes (17): 1. What "done" means, 2. Working rules, 3.1 Canonical schema (the only thing the pipeline reads), 3.2 Current datasets (adapters), 3.3 Simulator (SDD 10.2), 3.4 Upload area for future datasets, 3. Data sources: use current datasets now, swappable later, 4. Build order (milestones) (+9 more)

### Community 9 - "traceability.py"
Cohesion: 0.29
Nodes (4): main(), expand(), main(), requirements()

### Community 10 - "anomaly.py"
Cohesion: 0.24
Nodes (7): Autoencoder, load(), model_path(), save(), train(), train_from_simulation(), week_vector()

### Community 11 - "teams"
Cohesion: 0.12
Nodes (16): demo_seed, demo_zone, regions, code, name, teams, base_lat, base_lon (+8 more)

### Community 12 - "test_detection.py"
Cohesion: 0.10
Nodes (34): case_premise(), cfg(), demo_run(), demo_run_all(), demo_sim(), rank_of(), top_k(), test_detection_creates_no_cases() (+26 more)

### Community 13 - "weights"
Cohesion: 0.10
Nodes (20): _tuning, objective, seed, split, tuned_at, zones, weights, anomaly (+12 more)

### Community 14 - "zone"
Cohesion: 0.18
Nodes (11): zone, change_min_segment_days, change_min_shift_share, consecutive_days, conventional_daily_cv, flat_cv, large_load_share, loss_model_error_share (+3 more)

### Community 15 - "canonical.py"
Cohesion: 0.28
Nodes (4): Column, schema_document(), Table, _table()

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
Cohesion: 0.09
Nodes (27): build, depends_on, env_file, environment, restart, volumes, context, dockerfile (+19 more)

### Community 34 - "profiles.py"
Cohesion: 0.19
Nodes (6): _bump(), daily_levels(), household_load_kw(), london_shapes(), _night_block(), synthetic_shapes()

### Community 35 - "db"
Cohesion: 0.15
Nodes (13): environment, healthcheck, image, ports, restart, volumes, POSTGRES_DB, POSTGRES_PASSWORD (+5 more)

### Community 36 - "services"
Cohesion: 0.17
Nodes (11): image, profiles, name, image, profiles, services, grafana, redis (+3 more)

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

### Community 44 - "ollama"
Cohesion: 0.50
Nodes (4): image, restart, volumes, ollama

### Community 45 - "prometheus"
Cohesion: 0.50
Nodes (4): image, profiles, volumes, prometheus

## Knowledge Gaps
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `duty_roster()` connect `simulator.py` to `Build the VoltGuard AI prototype (R0)`, `config.py`, `test_detection.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `simulate_zone()` (e.g. with `.transformer_id()` and `ZoneNetwork`) actually correct?**
  _`simulate_zone()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `numpy` be split into smaller, more focused modules?**
  _Cohesion score 0.06092384519350812 - nodes in this community are weakly interconnected._
- **Why does `3.1 Canonical schema (the only thing the pipeline reads)` connect `Build the VoltGuard AI prototype (R0)` to `simulator.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `ZoneInput` (e.g. with `balance_zone()` and `data_quality_flags()`) actually correct?**
  _`ZoneInput` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Should `config.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Are the 24 inferred relationships involving `Requirements` (e.g. with `test_FR_DI_01_readings_round_trip_match_generator()` and `test_FR_DI_02_voltage_for_smart_meters_only()`) actually correct?**
  _`Requirements` has 24 INFERRED edges - model-reasoned connections that need verification._