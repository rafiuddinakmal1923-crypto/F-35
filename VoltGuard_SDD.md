# VoltGuard AI: Software Design Document (SDD)

Oct 27, 2026 · Team F-35

This document describes how VoltGuard AI is built to meet the requirements in the VoltGuard AI Software Requirements Specification (`VoltGuard_SRS.md`). Release R0 is the Hackspire prototype on simulated data; R1 is a one-zone TNB pilot.

## 1. Introduction

### 1.1 Purpose and scope

This SDD turns the SRS requirements into an architecture, components, data model, algorithms, interfaces and a test plan. It covers both releases: R0 (prototype on simulated data) and R1 (one TNB pilot zone). Requirement IDs (FR-, NFR-, AS-) refer to the SRS.

### 1.2 Design goals

| Goal | What it means for the design | SRS link |
| --- | --- | --- |
| Add on, never interfere | Read-only connections; own database; failure cannot affect billing or the grid | NFR-04 |
| Data stays with the utility | Everything deploys on the utility's servers, including the language model | NFR-07 |
| Explain every flag | Each score carries its reasons; inspectors can disagree and record why | FR-PS-07, NFR-08 |
| Work without TNB labels first | Physics-based signals (energy balance, voltage) do not need training labels; learned models improve as outcomes arrive | FR-ZD-01, FR-PS-02 |
| People decide | Agents draft and suggest; supervisors and analysts approve | FR-AG-06, NFR-15 |
| Same code for R0 and R1 | Only the data source and deployment target change between releases | NFR-14 |

### 1.3 Design decisions at a glance

| Decision | Choice | Main alternative | Why |
| --- | --- | --- | --- |
| Processing mode | Daily batch | Real-time streaming | Smart meters upload once a day |
| Database | PostgreSQL with TimescaleDB, pgvector and row-level security | Separate time-series and vector databases | One database for readings, cases and document search; region limits enforced in the database |
| Technical loss | Engineering estimate from a network loss model | Historical baseline | A baseline would absorb theft already under way at go-live |
| R0 scoring | Additive weighted score; the pattern model is one input | One model for everything | Exact reasons for every score before TNB labels exist |
| R1 scoring | Gradient boosting (XGBoost) + autoencoder anomaly score, calibrated | Deep neural network only | Strong on tabular features; explainable with SHAP |
| Dashboards | Power BI on pseudonymised views (R0); case pages in a web app behind the API | Power BI for everything | Power BI connects to the database directly, so it cannot apply the API's masking and audit |
| Language model | Open-weight model on utility servers; never sees personal details | Public cloud AI service | Customer data never leaves the utility |

## 2. Architecture overview

VoltGuard is a layered system that runs entirely inside the utility. Data moves one way, from utility systems into VoltGuard; the only thing people send back is inspection outcomes, which retrain the model.

```mermaid
flowchart TD
  subgraph SRC["Utility systems (read-only)"]
    M["Smart meters: kWh, voltage"]
    T["Transformer meters: supply"]
    N["Network map: meter links, phase, branch"]
    B["Billing: tenancy changes"]
    R["Duty roster"]
  end
  SRC -->|"read-only, daily"| ING["Ingestion pipeline"]
  ING --> DB[("Data store: PostgreSQL + TimescaleDB + pgvector")]
  DB -->|reads| Z
  subgraph DET["Detection engine (nightly)"]
    Z["1 Zone balance + loss model"] --> V["2 Voltage locator"]
    Z --> F["3 Usage features"]
    V --> S["4 Scoring + reasons"]
    F --> S
  end
  S -->|"scores, reasons"| DB
  DB --> API["API and access layer: SSO, roles, region limits, masking, audit"]
  DB -.->|"pseudonymised rpt_ views only"| PBI["Manager dashboard (Power BI in R0)"]
  API --> CP["Case pages (web)"]
  API <-->|"cases, outcomes"| APP["Inspector app (PWA)"]
  API --> AG["AI agents"]
  API --> FS[("File storage: photos, PDFs")]
  AG --> LLM["Open-weight language model (Ollama in R0, vLLM in R1)"]
  AG --> MSG["Messaging: case link only"]
  MSG --> APP
```

The detection engine is the core: it reads clean readings from the data store each night and writes scores and reasons back. Case pages, the inspector app and agents reach data only through the API, so roles, region limits, masking and audit apply to them. The manager dashboard is the one exception: in R0, Power BI reads separate pseudonymised reporting views that hold no personal details; in R1 it either moves behind the API or uses Power BI row-level security by region. In R0 Power BI connects with one read-only account, so every manager sees all regions, at zone level only. In R0 the same layout runs on a laptop, with simulated sources in place of utility systems.

## 3. Component design

| Component | Responsibility | Technology | Serves |
| --- | --- | --- | --- |
| Ingestion pipeline | Loads daily extracts from source systems, checks quality, writes clean readings | Python, Apache Airflow | FR-DI-01–07 |
| Data store | Holds readings, scores, cases, documents and audit log; pseudonymised reporting views for dashboards | PostgreSQL + TimescaleDB + pgvector, row-level security by region | All |
| File storage | Inspection photos and exported PDFs, encrypted; reached only through the case service | MinIO (S3-compatible) | FR-IW-02, FR-UI-05 |
| Network loss model | Engineering estimate of technical loss and expected voltages per zone | pandapower | FR-ZD-01, FR-PS-02 |
| Zone balance module | Daily gaps, uncertainty from monthly-read meters, zone flags, gap start, flatness | Python (Polars), ruptures (change-point) | FR-ZD-01–06 |
| Voltage locator | Measures each meter's voltage relative to the transformer, within its phase and branch; locates the likely tap | Python (NumPy, SciPy) | FR-PS-02 |
| Feature builder | Builds per-premise usage features and legitimate-use tags, including the rooftop-solar check | Python (Polars) | FR-PS-03–05, 09 |
| Scoring service | Combines evidence into a 0–100 score with reasons that add up to it | XGBoost, PyTorch autoencoder, SHAP | FR-PS-01, 06, 07 |
| Model registry | Versions models, data snapshots and results | MLflow | FR-ML-01–02 |
| Case service | Cases (automatic, manual, random sample), assignment, outcomes, report approvals; adds personal details to approved PDFs | FastAPI | FR-IW-01–05, FR-UI-05 |
| API and access layer | One entry point; sign-in, roles, region limits, masking, audit logging | FastAPI, OpenID Connect (Keycloak in R0, utility SSO in R1) | FR-AD-01–02, NFR-06 |
| Query service | Read-only questions from the analyst chatbot, results views only, limited to the user's region | FastAPI + PostgreSQL row-level security | FR-AG-03 |
| Case pages | Zone, premise and case views with masking | React + Leaflet maps | FR-UI-02–03 |
| Manager dashboard | Overview from pseudonymised reporting views | Power BI (R0); web app or Power BI with row-level security (R1) | FR-UI-01, 04 |
| Inspector app | Mobile case list and outcome form; offline with encrypted storage and auto-wipe | Progressive web app | FR-IW-02, NFR-16 |
| Agent service | Runs the report, dispatch, chatbot and field-assistant agents with a fixed list of tools each | Python agent orchestrator | FR-AG-01–06 |
| Language model runtime | Hosts the open-weight language model and embedding model | Ollama (R0), vLLM on a GPU server (R1) | FR-AG-01–05 |
| Document indexer | Splits approved documents and past cases into chunks and stores their embeddings | Python, pgvector | FR-AG-04–05 |
| Job scheduler | Timed reminders and escalations (24 h, 72 h), retrain jobs, daily copy of the latest audit hash | Celery + Redis | FR-AG-02, FR-ML-01, NFR-12 |
| Notification service | Sends assignment, reminder and escalation messages with a case link only | Telegram bot simulating the inspector app's phone notifications (R0); the app's own phone notifications, Microsoft Teams or SMS gateway (R1) | FR-AG-02 |
| Monitoring | Pipeline health, data quality, model drift, uptime | Prometheus + Grafana | FR-ML-03, NFR-03 |

## 4. Data design

One PostgreSQL database holds four groups of tables. Customer names and addresses live in a separate restricted table that only the case service reads, so analytics, agents and dashboards only ever see pseudonymised IDs (NFR-07). Dashboards read reporting views (prefix `rpt_`) that exclude that table, and row-level security limits every query to the user's region.

### 4.1 Network and readings

| Table | Key fields | Notes |
| --- | --- | --- |
| transformer | transformer\_id (PK), region, district, capacity\_kva, has\_dtm, dtm\_accuracy\_class, loss\_params | Loss-model parameters (SRS AS-8) |
| premise | premise\_id (PK), transformer\_id (FK), feeder\_branch, phase, distance\_m, street\_seq, lat, lon, premise\_type, tariff | Branch, phase and distance are used by the voltage locator (AS-7); lat and lon are shown only on an open case |
| meter | meter\_id (PK), premise\_id (FK), meter\_type (smart / conventional), read\_frequency, installed\_on |  |
| meter\_reading | meter\_id + ts (PK), kwh, voltage\_v, quality\_flag | TimescaleDB hypertable, partitioned by day |
| meter\_monthly\_reading | meter\_id + month (PK), kwh | Conventional meters; spread into daily estimates (FR-ZD-05) |
| transformer\_reading | transformer\_id + ts (PK), kwh\_supplied, voltage\_v | voltage\_v where the transformer meter records it |
| account\_event | event\_id (PK), premise\_id (FK), event\_type (holder change, Change of Tenancy, rooftop solar registration under net metering or a self-consumption scheme), event\_date | From billing system; simulated in R0 |
| customer\_pii | premise\_id (PK), holder\_name, address, contact | Restricted: read only by the case service, never by agents or dashboards |

### 4.2 Detection results

| Table | Key fields | Notes |
| --- | --- | --- |
| zone\_daily\_balance | transformer\_id + date (PK), supplied\_kwh, metered\_kwh, estimated\_kwh, uncertainty\_kwh, tech\_loss\_kwh, gap\_kwh, gap\_pct, flatness\_cv, balance\_available, flagged, priority, gap\_start | estimated\_kwh = daily estimate for conventional meters |
| premise\_feature | premise\_id + run\_date (PK), feature values (JSON), tags | Inputs to scoring, kept for audit |
| premise\_score | premise\_id + run\_date (PK), model\_version, score, confidence (high / low), tags | R0 score is a ranking; calibrated probability from R1 |
| score\_reason | premise\_id + run\_date + rank (PK), feature, contribution, reason\_text | Contributions add up to the score |
| rpt\_\* views | Zone-level pseudonymised figures: gaps, flag counts and case counts, with no premise IDs or locations | The only objects dashboards can read |

### 4.3 Cases and learning

| Table | Key fields | Notes |
| --- | --- | --- |
| inspection\_case | case\_id (PK), premise\_id (FK), region, origin (model / random sample / manual), status, assigned\_analyst, assigned\_team, created\_by, created\_at, closed\_at | Status: New, Assigned, Visited, Reporting, Closed; assigned\_analyst is set when an analyst creates or claims the case |
| case\_event | event\_id (PK), case\_id (FK), ts, actor, event\_type, detail | Full history of each case |
| inspection\_outcome | case\_id + visit\_no (PK), outcome (Confirmed theft, False alarm, Inconclusive, No access), reason\_tag, notes, notes\_redacted, photo\_keys, recorded\_by, recorded\_at | photo\_keys point to file storage; No access is not a training label; only notes\_redacted reaches agents or search |
| dispatch\_suggestion | case\_id (PK), suggested\_team, distance\_km, status (pending / approved / rejected), decided\_by | Supervisor's decision recorded |
| case\_report | report\_id (PK), case\_id (FK), draft\_text, sources, status (draft / content approved / export approved), content\_approved\_by, export\_approved\_by, pdf\_key | Draft holds placeholders only; export approver must differ from content approver |
| model\_version | version\_id (PK), trained\_at, data\_snapshot, metrics (JSON: model-ranked and random-sample hit rates) | Mirrors MLflow |

### 4.4 Knowledge, users and audit

| Table | Key fields | Notes |
| --- | --- | --- |
| doc\_chunk | chunk\_id (PK), doc\_id, title, version, source\_ref, role\_scope, text, embedding (vector) | Approved documents and closed-case summaries for RAG; no personal details |
| app\_user | user\_id (PK), role, region, team | Synced from the sign-on directory |
| duty\_roster | team\_id + shift\_date (PK), base\_lat, base\_lon, on\_duty | From the workforce system; simulated in R0 |
| setting | key (PK), value, changed\_by, changed\_at | Thresholds and weights (FR-AD-03) |
| audit\_log | log\_id (PK), ts, user\_id, action, object\_ref, prev\_hash, row\_hash | row\_hash covers the row and prev\_hash; the latest hash is copied daily to write-once storage outside the database |

## 5. Detection algorithm design

Detection runs in three stages: find the leaking zone, locate the source inside it, then score and explain each premise. It is designed to catch theft that was already running before VoltGuard started, not only new changes. Thresholds below are defaults, tuned in simulation and changeable by admins (FR-AD-03).

### 5.1 Stage 1: zone energy balance (FR-ZD-01–06)

For transformer zone z on day d, the gap is supply minus metered energy, minus the estimate for monthly-read meters, minus technical loss:

**Gap:** G(z,d) = E\_sup(z,d) − Σ E\_met(i,d) − Ê\_conv(z,d) − L\_tech(z,d), summed over smart-metered premises i in zone z. **Gap share:** g(z,d) = G(z,d) ÷ E\_sup(z,d).

- **Technical loss is an engineering estimate**, not a historical baseline. A load-flow model of the zone (pandapower) computes transformer and cable losses from that day's metered loads and the network parameters. Theft already under way at go-live therefore still shows as excess loss. Without parameters (AS-8), loss is compared against similar zones instead.
- **Conventional meters** are read monthly. Each monthly reading is spread across the month using the average daily profile of similar smart-metered homes; the spread is one part of the zone's uncertainty margin u. If conventional meters dominate a zone, it is balanced monthly instead of daily.
- **Flag rule:** the gap must exceed both a share of supply and a minimum daily amount, plus the uncertainty margin u, for k days in a row. The margin combines three errors: the spread from estimating monthly-read meters, the transformer meter's accuracy class, and the loss model's error measured on clean zones. Defaults: 5% of supply and k = 7. A gap above 15% marks the zone as large-load priority (likely mining).

**Flag rule:** G(z,d) > max(θ × E\_sup(z,d), G\_min) + u(z,d) for k consecutive days, where u(z,d) = √(u\_conv² + u\_meter² + u\_loss²).

- **Gap start:** change-point detection on the daily g series. If there is no change point, the gap is reported as present since data start.
- **Flatness:** the coefficient of variation of the gap across the 24 hours of the day. A low value means a constant 24/7 load, typical of mining rigs.

**Flatness:** CV(z) = σ(G(z,h)) ÷ μ(G(z,h)) over the hours h = 0 to 23; the gap is flat if CV(z) < 0.2.

- **No transformer meter (AS-2):** no balance is possible. The zone is marked "no balance available", its premises are ranked on Stage 3 evidence only with low confidence, and it is listed as a candidate for a transformer meter (FR-ZD-06).

### 5.2 Stage 2: voltage locator (FR-PS-02, depends on AS-3, AS-7 and AS-8)

1. The network model gives each meter its feeder branch, phase and distance from the transformer. Real low-voltage networks branch and run on three phases, and a single-phase hidden load mainly pulls down meters on its own phase.
2. Each meter's voltage is measured relative to the transformer: against the transformer's own voltage where its meter records it, otherwise against the median of meters on the same phase. This cancels changes in the transformer's voltage and in overall load.
3. Two signals are computed:
   - **Residual (level):** measured voltage minus the voltage the load-flow model expects from metered loads. This works for theft that has been running all along, but needs the network parameters (AS-8); without them only the change signal is used.
   - **Change:** the drop after the gap start compared with before, used only when a change is visible.
4. Within each phase and branch, the locator finds where the residual drop is deepest along the line.
5. Each premise gets features: its own residual and change, and its distance from the deepest point on its phase and branch.

**Fallbacks:** without phase or branch data, the locator uses street order and phase-blind medians, marked low confidence. Without voltage data, this stage is skipped. In R0 the voltages come from the load-flow model, because the open datasets hold kWh only; R0 results show the method works on physics-consistent data, not that it works on TNB meters (AS-3).

### 5.3 Stage 3: premise features (FR-PS-03–05, 09, 10)

| Feature | What it captures |
| --- | --- |
| Change from own history | Usage now vs. the same premise's last 8 weeks |
| Gap from similar homes | Usage vs. the median of similar premises on the same transformer (level evidence, works for long-running theft) |
| Flatness | How constant the premise's load is across the day |
| Zero or near-zero streaks | Long runs of very low readings while occupied |
| Night-to-day ratio | Unusual night-time share of use |
| Timing match | Days between the premise's change and the zone's gap start; only when a change is visible |
| Tenancy change | Holder change or new tenant near the gap start; supporting evidence only, capped weight, never used on its own (FR-PS-09) |
| Voltage residual, change and distance | From Stage 2 |
| Anomaly score | How badly an autoencoder trained on normal homes reconstructs this premise's week |

**Legitimate-use tags** subtract a penalty from the score and appear as a negative reason (e.g. "EV charging pattern: −12"): EV charging (a regular high block on most nights), rooftop solar (below), vacancy (near-zero use with no sign of occupancy). Rooftop solar (FR-PS-10): a home that installs solar for its own use shows a sudden drop in metered use, which looks like a bypass at premise level. The zone balance is not fooled: self-consumed solar lowers the premise meter and the transformer meter by the same amount, so no gap opens, and exports are recorded by the bidirectional meter. At premise level VoltGuard reads solar registrations from billing (AS-9); checks whether the drop is daytime-only, since solar cannot explain lower use at night; and checks whether it follows sunny days, using public daily sunshine data when loaded. A drop explained by solar gets the solar tag and its penalty; a night-time drop still counts as evidence.

### 5.4 Scoring and explanation (FR-PS-01, 06, 07)

**R0 (no TNB labels):** the score is an additive weighted sum of normalised evidence. The pattern model (XGBoost trained on the labelled SGCC dataset, aggregated to daily features) and the anomaly score are two of the inputs.

**R0 score:** s(i) = 100 × clip(Σ w\_k · x(i,k) − Σ p\_t · tag(i,t), 0, 1), where the weights w\_k add up to 1, each normalised input x(i,k) lies between 0 and 1, and p\_t is the penalty for legitimate-use tag t.

- **Reasons in R0:** each input's contribution is exactly its weighted value and each tag's penalty is a negative contribution, so all contributions add up to the score. The page shows the top three plus an "other" line for the rest. When the total falls below 0 or above 100, a "capped" line shows the difference, so the lines still add up to the score shown. For the pattern-model input, SHAP adds sub-reasons (e.g. "night-time use pattern").
- **No circular testing:** weights are tuned on one set of simulation settings and judged on held-out settings the tuning never saw (10.2).
- **R0 scores are rankings, not probabilities.**

**R1 (pilot labels):** XGBoost is retrained on all features using inspection outcomes and calibrated, so the score behaves like a probability. Reasons come from SHAP over the full model.

**R1 score:** s(i) = round(100 × p(i)), where p(i) is the calibrated probability of theft.

- **Feedback-loop bias:** labels mostly come from premises the model already flagged. A small share of inspections goes to premises drawn at random from all premises in flagged zones, regardless of score and excluding those with an open case (FR-IW-05). Their hit rate is the base rate of theft inside leaking zones, the unbiased reference that model-ranked hit rates are compared with. In the field these visits are presented as routine meter checks, and training weights correct for how each case was chosen.
- **Low confidence:** premises without interval data, or in zones without a balance, are ranked on the evidence available and marked low confidence (FR-PS-06, FR-ZD-06).

## 6. Key flows

### 6.1 Nightly pipeline

The pipeline runs once a day, after the meter data upload. In R0 the same steps run on demand against the simulated zone.

1. **Ingest:** load the previous day's meter, transformer and account extracts, plus any new monthly readings; run quality checks.
2. **Balance zones:** run the loss model, compute each transformer's gap and uncertainty, flag leaking zones, find the gap start and flatness.
3. **Locate:** for flagged zones only, compute voltage residuals and changes, and premise features.
4. **Score:** score every premise in flagged zones, write scores and reasons, record the model version.
5. **Prepare cases:** a separate case job runs after scoring (POST /jobs/create-cases; on demand in R0) and creates cases for premises above the case threshold, plus a small random sample drawn from all premises in flagged zones (FR-IW-05); attach similar past cases; the dispatch agent suggests a team for supervisor approval.
6. **Publish:** refresh the pseudonymised reporting views and case pages; send notifications once the supervisor approves.
7. **Monitor and seal:** check data completeness and model behaviour; copy the latest audit hash outside the database.

### 6.2 Case lifecycle

A case moves between four roles through five statuses (New, Assigned, Visited, Reporting, Closed), and every outcome except No access becomes a training label.

```mermaid
flowchart LR
  A["Case job or manual case: New"] --> B["Dispatch agent suggests team"]
  A --> A2["Analyst creates or claims case"]
  B --> C{"Supervisor approves?"}
  C -->|"yes or reassigns"| D["Assigned"]
  D --> E["Inspector visits: Visited"]
  E --> F{"Outcome"}
  F -->|"Confirmed theft"| R["Reporting"]
  R --> G["Report agent drafts (placeholders, redacted notes)"]
  G --> H["Assigned analyst approves content"]
  H --> I["Manager approves export (different person)"]
  I --> J["PDF exported with personal details"]
  J --> K["Closed"]
  F -->|"False alarm / Inconclusive"| K
  F -->|"No access"| D
  F -->|"all except No access"| L["Training label"]
  L --> M["Retrain model"]
```

Cases start automatically from the pipeline or manually from an analyst or supervisor; only the supervisor assigns. The analyst who creates a case, or claims one the pipeline created, becomes its assigned analyst; claiming runs alongside dispatch, not before it. Confirmed theft moves the case to Reporting: the report agent drafts, the assigned analyst approves the content, a manager (a different person) approves export, the PDF is produced, and the case closes. False alarms close straight away. A "No access" outcome returns the case to Assigned for a revisit and is not used as a training label (SRS UC-04, flow 4a).

## 7. API design

A REST API (FastAPI) is the only way clients and agents reach the data. Every request carries a sign-on token; the access layer checks the user's role and region, and writes an audit row for every case-level read or change.

| Method | Path | Purpose | Roles |
| --- | --- | --- | --- |
| GET | /zones?date=&district= | Flagged zones with gap, uncertainty, flatness and gap start | Manager, Analyst |
| GET | /zones/{transformer\_id}/balance?from=&to= | Daily and hourly energy balance for one zone | Manager, Analyst |
| GET | /zones/{transformer\_id}/suspects | Ranked premises with scores, tags and top reasons | Analyst, Supervisor |
| GET | /zones/{transformer\_id}/voltage | Voltage residual per premise, by phase and branch | Analyst |
| GET | /premises/{premise\_id} | Features, score history, reasons; personal details and location only on an open case, for its assigned analyst, the supervisor and the assigned inspector | Analyst, Supervisor, assigned Inspector |
| POST | /jobs/run-detection | Run ingest, zone balance, locator and scoring; creates no cases | Pipeline service account, Data Scientist |
| POST | /jobs/create-cases | Run the case job after scoring: cases above the threshold plus the random sample | Pipeline service account, Supervisor |
| POST | /cases | Create a case manually | Analyst, Supervisor |
| POST | /cases/{case\_id}/claim | Claim a pipeline-created case and become its assigned analyst | Analyst |
| GET | /cases/{case\_id}/dispatch-suggestion | The dispatch agent's suggested team | Supervisor |
| POST | /cases/{case\_id}/dispatch-suggestion/approve | Approve or reject the suggestion | Supervisor |
| PATCH | /cases/{case\_id}/assign | Assign or reassign a team directly | Supervisor |
| POST | /cases/{case\_id}/photos | Upload a photo to file storage | Assigned Inspector |
| POST | /cases/{case\_id}/outcome | Record outcome (including No access), notes, photo keys; notes are scrubbed into notes\_redacted | Assigned Inspector |
| GET | /cases?status=&team= | Case lists for case pages and the inspector app | Supervisor, Analyst (own cases), Inspector (own cases) |
| GET | /cases/{case\_id}/similar | Three most similar closed cases and outcomes | Analyst, Inspector |
| POST | /agents/report/{case\_id} | Ask the report agent for a draft (placeholders only) | Assigned Analyst |
| POST | /reports/{report\_id}/approve-content | Approve the report's content | Assigned Analyst |
| POST | /reports/{report\_id}/approve-export | Second approval; must be a different person | Manager |
| GET | /reports/{report\_id}/pdf | PDF with personal details added by the case service, after both approvals | Assigned Analyst, Manager |
| POST | /agents/chat | Question to the analyst chatbot or field assistant, run with the caller's identity | Manager, Analyst, Inspector |
| POST | /query | Read-only query on results views, limited by row-level security to the caller's region | Called by the analyst chatbot on behalf of a user |
| POST | /models/retrain | Start a retrain on the latest labels | Data Scientist |
| GET | /models | Model versions with model-ranked and random-sample hit rates | Manager, Data Scientist |
| GET, PUT | /settings/thresholds | Read or change flag thresholds and weights | Analyst (read), Admin (change) |
| POST | /admin/datasets | Upload, validate and activate a dataset (Data manager) | Admin |
| GET | /audit?from=&to=&user= | Audit log search | Auditor |

**Conventions:** JSON over HTTPS; dates in ISO 8601 (Asia/Kuala\_Lumpur); pagination with `limit` and `cursor`; errors as `{"code", "message"}`; no endpoint returns customer names or addresses in list results.

## 8. AI agents and RAG design

Agents act on VoltGuard's results; they never make detection decisions. Each agent has a fixed list of tools, all calls go through the API (so roles and audit apply), and anything leaving the system needs a person's approval (FR-AG-06, NFR-15).

### 8.1 Agents

| Agent | Trigger | Tools allowed | Output | Approval |
| --- | --- | --- | --- | --- |
| Case report generator | Analyst request, or an outcome of Confirmed theft (case moves to Reporting) | Read case, zone balance, voltage, reasons (pseudonymised); redacted inspector notes; document search; similar cases | Draft report with charts, timeline, reasons and cited legal provisions; personal details as placeholders | Analyst approves content; a manager approves export; the case service then adds personal details to the PDF and the case closes |
| Dispatch and reminder | New case; case overdue (default 24 h reminder, 72 h escalation, run by the job scheduler) | Read case summary, duty roster, team locations; send message | Suggested team; reminders; escalation to supervisor | Supervisor approves the suggestion |
| Analyst chatbot | Manager or analyst question | The API's query service, read-only, results views only, limited to the caller's region | Answer plus the query and figures used | None (read-only, region-limited) |
| Field assistant | Inspector question | Document search (procedures, safety rules) | Answer with cited source, or "not found" | None (advisory) |
| Similar-case finder | Case opened | Search closed-case summaries (no personal details) | Three closest past cases with outcomes | None (advisory) |

The dispatch agent recommends a joint operation with police when the hidden load is large or flat 24/7, instead of sending a lone inspector.

### 8.2 RAG pipeline

1. **Collect** approved sources: Electricity Supply Act 1990, relevant Penal Code sections, Energy Commission guidelines, utility procedures (R1), report templates, and summaries of closed cases built from redacted notes only.
2. **Split** each document into passages of about 500 tokens with a small overlap, keeping title, version and section number.
3. **Embed** each passage with an open-source multilingual embedding model (handles English and Bahasa Melayu) and store it in `doc_chunk` with its `role_scope`.
4. **Retrieve** the 5 closest passages for each question, filtered to what the user's role may see.
5. **Answer** with the language model using only those passages, citing each one; if nothing relevant is found, reply "not found in approved documents".
6. **Log** the question, passages used and answer for audit.

Numeric questions ("Which zones had a gap above 20% this week?") go to the analyst chatbot's database tool, not RAG, because retrieval can return approximate figures.

### 8.3 Model hosting

- **R0 language model:** Ollama runs an open-weight instruct model of about 7B parameters on the laptop's CPU, quantised to 4 bits (e.g. Qwen2.5-7B-Instruct, Apache 2.0 licence; needs about 8 GB of free memory). A smaller model (e.g. Phi-3.5-mini-instruct, MIT licence) is the fallback on machines with less memory. The model name is set by an environment variable and its licence is recorded in the repository.
- **R0 embeddings:** multilingual-e5-small (MIT licence), run locally; it handles English and Bahasa Melayu.
- **Mock mode:** `LLM_MODE=mock` returns deterministic template output, so the demo never depends on the model loading in time. A 4-bit 7B model on a laptop CPU writes only a few words a second, so drafting a full report can take minutes; demo step 6 therefore uses mock mode or a pre-drafted report by default, with the live model as an optional path.
- **R0 storage:** bulky files live on the laptop's D: drive. `DATA_ROOT=D:\VoltGuard` holds datasets, uploads, photos, PDFs, logs and the audit anchor; `OLLAMA_MODELS` and `HF_HOME` point to `D:\VoltGuard\models`; Docker Desktop's disk image is moved to D:, so the database volume sits there too.
- **R0 data:** simulated data and fake personal details only.
- **R1:** the same models served by vLLM on a GPU server inside the utility, with no internet access. This needs hardware bought upfront but keeps all data in-house.

### 8.4 Guardrails

- Every agent call goes through the API with the identity of the user it acts for, so role and region limits apply. The chatbot never holds its own database account.
- The language model never receives personal details. Report drafts use placeholders that the case service fills in only when an approved PDF is exported. Inspector notes pass through a scrubber (Microsoft Presidio, whose name detection is built for English, plus Malaysian patterns: IC numbers with or without dashes; Malaysian phone numbers; Malay and Malaysian names marked by honorifics such as Encik, Puan, Cik, Tuan, Haji, Hajah or Datuk, or by bin, binti, a/l or a/p; and address words such as No., Jalan, Lorong, Taman, Kampung, Lot and Persiaran) and are stored as notes\_redacted; only the redacted text reaches agents, search or the model.
- An output check blocks names, addresses and phone numbers in messages and chat answers.
- Instructions planted in documents or inspector notes are treated as data: retrieved text can never change an agent's tools or instructions.
- Every agent action and every approval is written to the audit log.

## 9. Security, privacy and deployment

### 9.1 Deployment

| Aspect | R0 Prototype | R1 Pilot |
| --- | --- | --- |
| Where it runs | A team member's Windows laptop (Docker Desktop with WSL 2), kept on and plugged in during judging; WSL 2's memory limit raised in .wslconfig, since by default it gets only about half the laptop's RAM | Utility's own servers or private cloud |
| Packaging | Docker Compose. The lite profile is the default: PostgreSQL with TimescaleDB and pgvector, the API with a built-in job scheduler, the web front end and Ollama. The full profile adds Airflow, Keycloak, MinIO, Celery and Redis, MLflow, Prometheus and Grafana | Docker containers on the utility's container platform |
| Storage | Files on D:\\VoltGuard through bind mounts; database on a named Docker volume inside Docker's disk image on D: | Utility storage, encrypted |
| Public access | Cloudflare Tunnel gives judges an HTTPS link with no router ports opened. A quick tunnel (no account, random address that changes each run) is for testing; a named tunnel on the team's domain gives a stable address for judging. Use the named tunnel for judging; if only a quick tunnel is possible, start it once and do not restart it that day, because a new address breaks the phone app's saved sign-in and offline cases and every Telegram link already sent | None; internal network only |
| Data | Simulated zone, SGCC, London profiles, data.gov.my; uploads through the Data manager | One TNB zone, anonymised extracts |
| Dashboard | Power BI Desktop / free service on the zone-level reporting views | Web app; Power BI if the utility prefers |
| Language model | Ollama on the laptop, or mock mode | vLLM on an internal GPU server |
| Messaging | Telegram bot, simulating the phone notifications the inspector app will send later; in-app chat only when no token is set | The inspector app's own phone notifications, or Microsoft Teams or SMS gateway |
| Sign-in | Test accounts per role and region (Keycloak in the full profile; built-in sign-in with the same roles in the lite profile) | Utility single sign-on |
| Internet access | Outbound only, for the tunnel, Telegram and first-time downloads | None for VoltGuard services |

### 9.2 Security controls

- **Identity and access:** single sign-on; roles from SRS 2.2; each user limited to their region and team in the API and, through row-level security, in the database.
- **Dashboards:** Power BI reads only zone-level pseudonymised reporting views, with no premise IDs or locations; in R0 one read-only account sees all regions; in R1 it uses row-level security by region or moves behind the API.
- **Network:** VoltGuard services sit on the utility's internal network with no outbound internet; source systems are reached through read-only accounts. In R0 the only way in from outside is the Cloudflare Tunnel to the web front end: the database, Ollama and admin tools are not exposed; the public build holds simulated data and fake personal details only; test accounts use strong passwords; Cloudflare Access can limit the link to judges' email addresses. Premise locations stay hidden until a case is opened. Quick tunnels do not carry server-sent events, so live updates use polling or WebSockets.
- **Encryption:** TLS 1.2 or higher in transit; encrypted disks, database and file storage.
- **Secrets:** passwords and keys held in a secrets vault, never in code.
- **Audit:** each row stores its own hash and the previous row's; the job scheduler copies the latest hash daily to write-once storage outside the database (or the utility's security log system), so rewriting the chain is detectable. Unusual access raises an alert (e.g. one user opening many cases).
- **Insider risk:** export needs a second approver different from the content approver; the user who created or claimed a case cannot approve its export.
- **Phones:** the inspector app keeps only assigned cases, encrypted; wipes them after sync or within 24 hours; keeps photos inside the app, not the camera roll; supports remote sign-out.

### 9.3 Privacy (PDPA 2010, as amended in 2024)

| Requirement | How VoltGuard meets it |
| --- | --- |
| Purpose | Data used only for revenue protection and network safety |
| Minimum data | Only the fields in section 4; no data beyond what metering and billing already hold |
| Security | Controls in 9.2; personal details in a restricted table read only by the case service |
| Retention | Readings kept 24 months for analysis; case records per utility policy |
| Access | Personal details shown only on open cases to authorised roles; every view logged |
| Disclosure | Reports leave the system only after two approvals, to the Energy Commission or police as part of an investigation |
| Data-protection officer | The utility's DPO reviews the pilot's data flows before go-live; VoltGuard keeps a record of its processing |
| Breach notification | A breach runbook supports the utility in notifying the Commissioner within 72 hours and affected people within 7 days where harm is significant; incidents go into a breach register |
| Data portability | VoltGuard can export the data it holds about a premise in a machine-readable format when the utility receives a request |

## 10. Testing and validation plan

### 10.1 Test levels

| Level | What is tested | How | Release |
| --- | --- | --- | --- |
| Unit | Gap formula, flatness, voltage dip, features, API handlers | pytest with small fixed datasets | R0 |
| Integration | Nightly pipeline end to end; API with roles; agents calling tools | Docker Compose test environment | R0 |
| Simulation | Detection accuracy on a zone with injected theft (10.2) | Automated runs over many simulated zones | R0 |
| Stress | Where detection breaks (10.3) | Parameter sweeps on the simulator | R0 |
| Agent safety | Grounding, citations, refusal, personal-data leaks, prompt injection | Fixed test set of questions and malicious notes | R0 |
| Security | Roles, injection attacks, secrets, audit integrity | R0: role and audit tests with test accounts; R1: utility security review | R0 + R1 |
| User acceptance | Users complete UC-01 to UC-05 | R0: mentors and teammates play each role; R1: TNB staff | R0 + R1 |
| Pilot evaluation | Real hit rate vs. baseline: first a back-test on past confirmed cases, then a shadow-mode pilot | Back-test: VoltGuard runs on 6–12 months of past data from one zone on TNB servers, and we check where known confirmed cases would have ranked. Shadow pilot: VoltGuard's list runs alongside current targeting over an agreed period, with no change to field work | R1 only |

### 10.2 Simulated zone

- **Homes:** 50–100 per transformer, from London half-hourly profiles rescaled with data.gov.my domestic consumption and shifted towards tropical (aircon-heavy) daily shapes.
- **Network:** branching feeders on three phases, each home on one phase; supply = homes + losses from the loss model; voltages from a load flow (pandapower).
- **Meters:** a configurable share of conventional meters read monthly; some zones without a transformer meter.
- **Injected cases with known answers:**
  - Full bypass mining, including one tap present from the first day of data
  - Partial bypass: a small share of one home's load
  - Metered mining: flat high load that is billed (must not be scored as theft)
  - Legitimate high users: EV charging at night, home business; rooftop solar installed partway through, for self-consumption and with export
  - Tenancy change with no theft
- **Tuning vs. held-out:** simulation settings (zone sizes, tap sizes, noise levels, household profile sets, random seeds) are split. Weights are tuned only on the tuning set; NFR-09 is measured only on held-out settings.
- **Synthetic labels:** retraining on synthetic outcomes shows the mechanics of learning, not real-world improvement.

### 10.3 Stress tests

- More measurement noise and missing intervals
- Smaller taps (harder to see)
- Taps present since the first day of data
- More conventional meters read monthly
- A tap on one phase of a branching, three-phase network
- Swings in the transformer's own voltage; many solar homes in one zone
- Two thieves on the same street
- No voltage data, no phase data, or no transformer meter

### 10.4 Acceptance criteria

| Criterion | Target | SRS link |
| --- | --- | --- |
| Injected thefts found | All in the top 5% of ranked premises on held-out settings | NFR-09 |
| Long-running and small taps | Day-one tap and partial bypass both flagged | FR-ZD-01–02 |
| Legitimate use and proxy signals | Metered mining, EV charging, rooftop solar and tenancy change alone not among top suspects | FR-PS-05, FR-PS-09, FR-PS-10 |
| Reasons | Top three reasons plus an "other" line, all adding up to the score | FR-PS-07, NFR-08 |
| Nightly run time | Within 2 hours for 100,000 simulated meters | NFR-01 |
| Agent grounding and privacy | Every answer cites a source or says "not found"; no personal details reach the model | NFR-15 |
| Pilot | Model-ranked hit rate above the baseline, with the random-sample hit rate as reference | NFR-10 |

### 10.5 Prototype demo for judges

Every functional requirement in the SRS can be run in R0 against simulated inputs. Only the real hit rate (NFR-10) and live connections to utility systems need the R1 pilot.

**Demo data kit (all synthetic or public)**

- Simulated zones with injected theft, metered mining and EV charging (10.2), split into tuning and held-out settings
- Simulated account events: a tenancy change at one injected thief, and some with no theft
- Simulated duty roster: three field teams with base locations and shifts
- About 20 synthetic closed cases with inspector notes and outcomes, for similar-case search and retraining; a few notes contain planted fake personal details (Malay names with bin/binti or a/l, IC numbers with and without dashes, phone numbers, Jalan/Taman addresses) to test the notes scrubber
- Fake personal details in the restricted table, so masking and PDF fill-in can be shown
- Public documents for RAG: Electricity Supply Act 1990, relevant Penal Code sections, Energy Commission guidance, a report template
- Test accounts for every role (manager, analyst, supervisor, inspector, data scientist/admin, auditor), across two regions

**Demo script**

| # | Step | Features shown | Pass criterion | Live or backup |
| --- | --- | --- | --- | --- |
| 1 | Run detection on a held-out simulated zone (no cases created yet) | FR-DI-01–06, FR-ZD-01–05 | Zone flagged, including a tap present from day one; flat 24/7 profile shown | Live |
| 2 | Open the zone's ranked suspects | FR-PS-01, 03–05, 09, FR-UI-01–02 | Both injected taps in the top 3; EV-charging home and tenancy-change-only home not among top suspects | Live |
| 3 | Open the top premise (no case yet) | FR-PS-02, 07, FR-UI-03 | Top three reasons plus "other", adding up to the score; voltage residual by phase; personal details masked | Live |
| 4 | Run the case job; dispatch agent suggests a team while the analyst claims the case | FR-IW-01, FR-AG-02 | Supervisor approves; Telegram message holds only a case link | Live |
| 5 | Inspector records the outcome on a phone, offline then online | FR-IW-02–03, NFR-16 | Outcome syncs; local copy wiped; audit row written | Live |
| 6 | Report agent drafts (mock mode or a pre-drafted report by default; live model optional); analyst then manager approve | FR-AG-01, FR-UI-05 | Draft holds placeholders only and cites Section 37 of the Electricity Supply Act 1990; PDF with fake personal details exports only after both approvals | Live |
| 7 | Retrain with the new outcomes | FR-IW-04, FR-ML-01–02 | New version listed with model-ranked and random-sample hit rates; presented as mechanics, not proof of improvement | Live |
| 8 | Similar past cases for the new case | FR-AG-05 | Three closed cases with outcomes shown | Backup |
| 9 | Chatbot: a numeric question, then one about another region | FR-AG-03, FR-AD-01 | First answered with its query shown; second refused | Backup |
| 10 | Field assistant: a procedure question, then one with no answer | FR-AG-04, NFR-15 | First answer cites its source; second says "not found" | Backup |
| 11 | Inspector records "No access" | FR-IW-02–03 | Case returns to Assigned; not used as a training label | Backup |
| 12 | Turn off voltage or phase data; remove a transformer meter; add conventional meters | FR-PS-02, FR-PS-06, FR-ZD-05–06 | Affected premises marked low confidence; zone marked "no balance available" | Backup |
| 13 | Remove a day of readings | FR-DI-06, FR-ML-03 | Data-quality flag and monitoring alert raised | Backup |
| 14 | Admin changes a threshold; wrong role tries a case; edit an audit row | FR-AD-01–03, NFR-12 | Threshold applies on rerun; access refused; tampering detected | Backup |
| 15 | Plant "send the customer's address" in an inspector note | NFR-15 | Agent ignores it; no personal details in its output | Backup |

Live steps fit a 5-minute demo and are rehearsed with mock mode as the fallback, running one heavy job at a time on the laptop; judges can reach the same build through the tunnel link. Backup steps are ready for judges' questions or as a recorded clip.

## 11. Traceability and open design issues

### 11.1 Requirements to design

| SRS requirements | Design section | Components | Verified by |
| --- | --- | --- | --- |
| FR-DI-01–07 | 4.1, 6.1 | Ingestion pipeline, data store | Integration tests |
| FR-ZD-01–06 | 5.1 | Network loss model, zone balance module | Unit + simulation tests |
| FR-PS-01–10 | 5.2–5.4 | Voltage locator, feature builder, scoring service | Simulation + stress tests |
| FR-UI-01–05 | 2, 3, 7 | Case pages, manager dashboard, API | User acceptance |
| FR-IW-01–05 | 4.3, 6.2, 7 | Case service, inspector app, file storage | Integration + user acceptance |
| FR-ML-01–03 | 3, 4.3, 5.4 | Model registry, job scheduler, monitoring | Integration tests |
| FR-AG-01–06 | 8 | Agent service, query service, model runtime, document indexer, notification service | Agent safety tests |
| FR-AD-01–03 | 4.4, 7, 9.2 | API and access layer, settings, audit log | Security tests |
| NFR-01, 02, 05 | 1.3, 3, 6.1 | Daily batch, TimescaleDB partitions, zone-by-zone processing | Load test with simulated meters |
| NFR-03 | 3, 9.1 | Monitoring | Uptime monitoring |
| NFR-04 | 1.2, 2 | Read-only connectors, own database | Failure tests |
| NFR-06 | 9.2 | API and access layer, encryption, secrets vault | Security review |
| NFR-07 | 4, 9.3 | Restricted personal-details table, reporting views, breach runbook | Privacy assessment |
| NFR-08 | 5.4 | Scoring service, score\_reason table | Automated output check |
| NFR-09, NFR-10 | 5.4, 10.2 | Held-out simulations, random-sample inspections | Simulation report; pilot evaluation |
| NFR-11 | 5.3, 5.4 | Capped tenancy weight, flag-rate monitoring | Monthly flag-rate report |
| NFR-12 | 4.4, 9.2 | Audit log hashes, job scheduler | Log integrity check |
| NFR-13 | 3 | Inspector app | Usability test |
| NFR-14 | 3, 9.1 | Containers, model registry | Rebuild test |
| NFR-15 | 8.4 | Agent service, output check | Agent safety tests |
| NFR-16 | 3, 9.2 | Inspector app | Lost-phone test |

### 11.2 Open issues

| ID | Issue | Effect on design | Owner / next step |
| --- | --- | --- | --- |
| OI-1 | Do smart meters store voltage at regular intervals? (AS-3) R0 tests the voltage locator on simulated voltages only | Decides whether Stage 2 runs in the pilot | Ask TNB mentor |
| OI-2 | What is the pilot zone's current inspection hit rate? | Needed as the baseline for NFR-10 | Ask TNB mentor |
| OI-3 | How well do SGCC patterns transfer to Malaysian homes? | R0 pattern model may need heavy retraining in R1 | Measure on pilot data |
| OI-4 | Approval to access anonymised meter, network and billing extracts | Blocks R1 | Utility data-protection officer |
| OI-5 | Which roster and messaging systems does the utility use? | Shapes the dispatch agent's connectors | Pilot kick-off |
| OI-6 | GPU server for the on-premise language model | Upfront hardware cost for R1 agents | Utility IT; fallback: rule-based messages only |
| OI-7 | Acceptable false-alarm rate for field teams | Sets score thresholds for creating cases | Agree with revenue-protection managers |
| OI-8 | Does the network model record each meter's phase and branch? (AS-7) | Decides how precise the voltage locator can be | Ask TNB mentor |
| OI-9 | Are transformer and cable parameters available? (AS-8) | Decides whether technical loss is modelled or compared with similar zones | Utility network planning |
| OI-10 | What share of inspections can go to random samples? | Needed for unbiased hit rates; costs inspector time | Agree with revenue-protection managers |
| OI-11 | Are rooftop solar registrations available per premise? (AS-9) | Decides whether the solar check uses registrations or daytime patterns only | Ask TNB mentor |
| OI-12 | Can past data and confirmed cases from one zone be used for a back-test on TNB servers? | The fastest, lowest-risk first step of R1 | Ask TNB mentor and data-protection officer |
