# VoltGuard AI R0: build plan

Source of truth: `VoltGuard_SRS.md` (what), `VoltGuard_SDD.md` (how), `VoltGuard_ClaudeCode_Prompt.md` (build brief; its sections 3 and 7 override the documents).

## Milestones

| # | Milestone | Covers | Done when |
| --- | --- | --- | --- |
| 1 | Scaffold: git, layout, lite Compose profile, `make.ps1` + `Makefile`, `.env.example`, `make test` | NFR-14 | `make.ps1 test` runs |
| 2 | Data layer: canonical schema, simulator, adapters (London, SGCC, data.gov.my), upload area, validation report, Data manager endpoint | FR-DI-01–07, SRS 5.3 | Simulator writes canonical Parquet + ground truth; validation rejects bad files |
| 3 | Detection engine: loss model, zone balance with uncertainty, change point, flatness, voltage locator, features, legitimate-use tags, additive score with exact reasons, SGCC-style pattern model, autoencoder | FR-ZD-01–06, FR-PS-01–09, NFR-08, NFR-09 | Unit tests pass; held-out simulation report written |
| 4 | API and security: sign-in per role and region, row-level security, masking, hash-chained audit with daily anchor, file storage | FR-AD-01–02, FR-UI-03, NFR-06, NFR-12 | Role and region refusals tested; audit tamper detected |
| 5 | Cases and apps: case job, random sample, claim, supervisor assignment, outcomes incl. No access, Reporting status, case pages, inspector PWA (offline, encrypted, auto-wipe, remote sign-out) | FR-IW-01–05, FR-UI-01–05, NFR-13, NFR-16 | Demo steps 4–5 work in the browser |
| 6 | Agents and RAG: report generator (placeholders, two approvals, PDF), dispatch + reminders, region-limited chatbot, field assistant, similar cases, notes scrubber, guardrails | FR-AG-01–06, NFR-15 | Agent safety tests pass |
| 7 | Learning and monitoring: retrain with versions, model-ranked vs random-sample hit rates, data-quality and drift alerts, threshold settings | FR-ML-01–03, FR-AD-03 | Retrain adds a version with both hit rates |
| 8 | Dashboards: zone-level `rpt_` views, Power BI role, `POWERBI.md`, CSV snapshot | FR-UI-01 (Power BI part) | Snapshot exported |
| 9 | Tests, deployment and demo: `make demo`, tunnel, `DEMO.md`, simulation report | SDD 10 | 7 live steps rehearsed end to end |

## File tree

```
F-35/
  VoltGuard_*.md / *.pdf        source documents
  PLAN.md TRACEABILITY.md DEVIATIONS.md DEMO.md README.md MODELS.md
  .env.example  docker-compose.yml  Makefile  make.ps1
  config/        thresholds.yaml  data_sources.yaml  demo.yaml
  backend/       Dockerfile  requirements.txt  voltguard/ (package)  tests/
    voltguard/
      config.py  cli.py  db/  data/  detection/  cases/  agents/  api/
      audit.py  auth.py  storage.py  scheduler.py  notify.py  monitoring.py  pdf.py
  web/           React + Vite: case pages, inspector PWA, Data manager
  data/          uploads/ (README, templates, schema.yaml)  docs_rag/
  deploy/        caddy/  cloudflared/  keycloak/  prometheus/
  powerbi/       POWERBI.md
  reports/       simulation_report.md
  scripts/       fetch_datasets.py  fetch_docs.py
```

Runtime data lives outside the repository under `DATA_ROOT` (`D:/VoltGuard`).

## Key decisions (details in DEVIATIONS.md)

- One Python package (`voltguard`) holds the engine, the service layer and the API; the CLI (`python -m voltguard ...`) and API jobs call the same functions.
- Agents call the service layer with the acting user's identity, so the same role, region, masking and audit checks apply as for HTTP clients.
- The lite profile is the default; heavier full-profile services are defined but optional.

## Open questions (do not block Must requirements)

- SDD 11.2 OI-1 to OI-10 need TNB input (voltage data, baseline hit rate, phase data, loss-model parameters, random-sample share).
- Default flag threshold θ = 5% (SRS FR-ZD-02) is a placeholder: the simulation report measures the smallest tap it can flag and states it honestly.
- Public legal texts (Electricity Supply Act 1990, Penal Code) are not copied into the repository; `scripts/fetch_docs.py` downloads them at setup, and RAG answers "not found" until they are loaded.
