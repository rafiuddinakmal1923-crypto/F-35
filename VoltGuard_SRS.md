# VoltGuard AI: Software Requirements Specification (SRS)

Oct 27, 2026 · Team F-35

VoltGuard AI helps utility revenue-protection teams find which premises inside a leaking transformer zone is most likely stealing electricity. This SRS specifies what the system must do; the VoltGuard AI Software Design Document (`VoltGuard_SDD.md`) describes how it is built. Release R0 is the Hackspire prototype on simulated data; R1 is a one-zone TNB pilot.

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements of VoltGuard AI (the design is in the companion SDD), a decision-support system for utility revenue-protection teams. It is written for Team F-35, Hackspire judges and mentors, and a future pilot partner (TNB).

### 1.2 Scope

VoltGuard turns a transformer energy-gap alert into a ranked, explained list of the premises most likely responsible, then supports inspection, reporting and model learning.

**In scope**

- Ingesting smart-meter, transformer-meter, network and account data (read-only)
- Detecting leaking transformer zones and ranking premises inside them
- Explaining each risk score
- Dashboards, inspection workflow and outcome feedback
- AI agents: case report generator, dispatch reminders, analyst chatbot, field assistant, similar-case retrieval (RAG)

**Out of scope**

- Disconnecting supply or changing bills
- Contacting customers, police or regulators automatically
- A customer or landlord portal (possible later, opt-in only)
- Replacing the utility's metering, billing or workforce systems

### 1.3 Releases

| Release | Purpose | Data | Users |
| --- | --- | --- | --- |
| R0 Prototype | Hackspire demo | Simulated transformer zone, SGCC, London profiles, data.gov.my | Team F-35, judges |
| R1 Pilot | Prove hit rate on real data: a back-test on past confirmed cases, then a shadow-mode pilot | One TNB transformer zone, anonymised, on TNB servers | TNB revenue-protection staff |

All functional requirements are built and testable in R0 using simulated or public data (section 7). R1 adds real data, real system connections and the real hit rate.

### 1.4 Definitions

| Term | Meaning |
| --- | --- |
| AMI | Advanced Metering Infrastructure: smart meters and their data network |
| MDMS | Meter Data Management System that stores meter readings |
| DTM | Distribution Transformer Meter: measures energy leaving a transformer |
| Zone | All premises supplied by one distribution transformer |
| Metered energy | Energy recorded by customers' meters. Billing is monthly; analysis uses the daily meter readings |
| Technical loss | Energy lost in the transformer and cables, estimated from an engineering model of the network |
| Energy gap | Energy supplied by a transformer minus metered energy, after technical loss |
| NTL | Non-technical loss: theft, tampering, unmetered or unbilled use |
| Risk score | 0–100 ranking of how strongly a premise's evidence matches theft; calibrated as a probability only from R1 |
| Hit rate | Share of inspected premises confirmed as theft |
| Random-sample inspection | Inspection of a premise chosen at random from all premises in flagged zones, not by the model, used to measure hit rates without bias |
| SHAP | Method that shows which inputs drove a model's score |
| RAG | Retrieval-augmented generation: the AI looks up documents before answering |
| PDPA | Personal Data Protection Act 2010 (Malaysia), amended in 2024 |

### 1.5 References

- Hackspire Lumina canvas, Team F-35 (VoltGuard AI)
- TNB Distribution Transformer Meter pilot, as described in [NST, Aug 2025](https://www.nst.com.my/amp/news/nation/2025/08/1262003/tnb-deploys-smart-tech-combat-electricity-theft)
- Electricity Supply Act 1990; Penal Code Section 427; Personal Data Protection Act 2010, as amended by the Personal Data Protection (Amendment) Act 2024
- Datasets: SGCC electricity theft (Kaggle), [London smart meters](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d), [data.gov.my electricity consumption](https://open.dosm.gov.my/data-catalogue/electricity_consumption)

## 2. Overall description

### 2.1 Product perspective

VoltGuard is an add-on to the utility's existing systems, not a replacement. It reads meter, transformer, network and account data once a day, writes only to its own database, and sends people to its own dashboard. If it fails, billing, metering and the grid are unaffected.

### 2.2 User classes

| User | Main tasks | Access |
| --- | --- | --- |
| Revenue Protection Manager | Reviews leaking zones, sets priorities, gives the second approval before a report is exported | All zones in their region on pseudonymised dashboards; personal details only when approving an export |
| Analyst | Investigates zones, reviews scores, approves report content | Assigned regions; personal details only on open cases they handle |
| Supervisor | Assigns cases, approves dispatch suggestions | Their teams' cases, with personal details on those cases |
| Field Inspector | Visits premises, records outcomes and evidence | Only cases assigned to them, including the address |
| Data Scientist / Admin | Runs pipelines, retrains models, sets thresholds | Pseudonymised data and settings; no personal details |
| Auditor | Reviews access and action logs | Read-only audit log |

The Energy Commission and police receive approved case reports but are not system users.

### 2.3 Operating environment

- **R0:** the team's Windows laptop, with all data and model files on drive D:; simulated data only; web case pages and inspector app, plus manager dashboards in Power BI
- **R1:** the utility's own servers or private cloud, Docker containers on Linux
- **Clients:** current desktop browsers (Chrome, Edge); a mobile browser view for inspectors
- **Language:** English and Bahasa Melayu interface labels

### 2.4 Constraints

- Customer data must stay on utility infrastructure and be handled under PDPA 2010 as amended in 2024.
- Access to source systems is read-only.
- Smart meters upload once a day, so analysis is daily, not real time.
- R0 uses only public and simulated data; no TNB household data is available to the team.
- The system recommends; people decide. No automatic enforcement action.

### 2.5 Assumptions and dependencies

| ID | Assumption | Impact if false |
| --- | --- | --- |
| AS-1 | Each meter can be mapped to its transformer | Zone balance cannot run |
| AS-2 | The pilot zone has a transformer meter recording at regular intervals | No balance for that zone; premises ranked on usage patterns only (FR-ZD-06) |
| AS-3 | Smart meters store voltage readings at regular intervals (to be confirmed with TNB). In R0 the voltage locator is tested only on voltages generated by a load-flow model, because open datasets hold kWh only | Voltage-dip feature (FR-PS-02) is dropped |
| AS-4 | Inspection outcomes can be recorded and shared with the system | The model cannot learn from results |
| AS-5 | A duty roster with team locations is available | Dispatch agent (FR-AG-02) becomes manual assignment only |
| AS-6 | Account holder and tenancy changes are available from billing records | Tenancy-change signal is dropped |
| AS-7 | The network model records each meter's feeder branch and phase | Voltage locator uses street order only, with lower confidence |
| AS-8 | Transformer and cable parameters are available for the loss model | Technical loss is estimated by comparison with similar zones, and the voltage locator uses change signals only (FR-PS-02) |
| AS-9 | Rooftop solar registrations (net metering or self-consumption schemes) are available per premise from billing records | Solar homes are recognised only from their daytime pattern, with lower confidence (FR-PS-10) |

## 3. Functional requirements

Priority sets what is cut first if time runs short, not what appears in the demo: **Must** = the prototype is not acceptable without it; **Should** = planned for R0 and shown in the demo when ready, simplified or cut first if time runs short; **Could** = built if time allows. Each requirement has a prototype test on simulated or public data; R1 repeats the tests on real pilot data.

### 3.1 Data ingestion (DI)

| ID | The system shall… | Priority | Prototype test |
| --- | --- | --- | --- |
| FR-DI-01 | Import half-hourly energy (kWh) per smart meter once a day | Must | Load 30 days of simulated readings; row counts match the generator |
| FR-DI-02 | Import voltage readings per smart meter where available | Should | Simulated voltage present for smart meters, absent for conventional meters |
| FR-DI-03 | Import energy readings from each transformer meter | Must | Simulated supply equals homes + stated loss + injected taps |
| FR-DI-04 | Import the network map: meter to transformer, and each premise's street position | Must | Every simulated meter linked to one transformer with a street position |
| FR-DI-05 | Import account events: account holder change and Change of Tenancy | Should | Simulated tenancy change at one injected thief shows in its premise view |
| FR-DI-06 | Check data quality (missing intervals, duplicates, clock errors) and flag affected meters | Must | Delete a day of readings; affected meters are flagged |
| FR-DI-07 | Import daily temperature per district | Could | Load a public or simulated daily temperature series |

### 3.2 Zone detection (ZD)

| ID | The system shall… | Priority | Prototype test |
| --- | --- | --- | --- |
| FR-ZD-01 | Compute each transformer's daily energy gap: supplied minus metered minus technical loss, with technical loss from an engineering estimate, not a historical baseline | Must | Computed gap matches the injected stolen energy, including a tap present from day one |
| FR-ZD-02 | Flag a zone when its excess loss exceeds both a set share of supply (default 5%) and a minimum daily amount, plus an uncertainty margin covering meter, estimation and loss-model error, for a set number of days (default 7); mark zones above 15% as large-load priority | Must | Small partial-bypass and large mining taps both flagged; clean zones not flagged |
| FR-ZD-03 | Estimate the date the gap started when a change is visible; otherwise report it as present since data start | Should | Estimate within 3 days of an injected start; a day-one tap reported as present since data start |
| FR-ZD-04 | Compute the gap's hourly profile and a flatness index (constant 24/7 load) | Should | Mining scenario shows a flat profile; partial-bypass scenario does not |
| FR-ZD-05 | Estimate daily usage of conventional (monthly-read) meters from their monthly reading and similar homes' profiles, with an uncertainty range | Should | Zone with many conventional meters still flags a mining tap; uncertainty shown |
| FR-ZD-06 | For zones without a transformer meter, rank premises on usage patterns only and mark the zone "no balance available" | Should | Remove the transformer meter from a simulated zone; premises ranked and marked low confidence |

### 3.3 Premise scoring (PS)

| ID | The system shall… | Priority | Prototype test |
| --- | --- | --- | --- |
| FR-PS-01 | Give every premise in a flagged zone a risk score from 0 to 100 | Must | Every premise in a flagged simulated zone has a score |
| FR-PS-02 | Locate a hidden load from neighbours' voltage, measured relative to the transformer and compared within the same phase and feeder branch (depends on AS-3, AS-7, AS-8) | Should | Deepest drops on the tap's phase sit beside it; it ranks in the top 3; meters on other phases are unaffected |
| FR-PS-03 | Use usage patterns: change from own history, gap from similar homes, flatness, zero streaks, night-to-day ratio | Must | All features visible for any premise |
| FR-PS-04 | When a change is visible, score whether a premise's usage change starts near the zone's gap start; for long-running gaps, rely on level-based evidence instead | Must | Injected thief's timing match within a day or two; a day-one tap still ranks in the top 5% |
| FR-PS-05 | Tag likely-legitimate patterns (EV charging, solar export, vacancy) and lower their score through a penalty shown as a negative reason | Should | EV-charging and metered-mining homes tagged, not among top suspects |
| FR-PS-06 | Rank premises without interval data by location and account signals, marked "low confidence" | Should | Add homes without smart meters; they are ranked and marked low confidence |
| FR-PS-07 | Show the top three reasons behind each score in plain language, plus an "other" line, so that all contributions add up to the score | Must | Top three reasons plus "other" add up exactly to the top premise's score |
| FR-PS-08 | Describe scores as risk only; never label a premise or person as a thief | Must | Review every screen and report draft for wording |
| FR-PS-09 | Use a tenancy change only as supporting evidence inside a flagged zone, with a capped weight, never on its own | Must | A tenancy change without other evidence does not lift a premise into the top suspects |
| FR-PS-10 | Tell rooftop solar apart from theft: use solar registrations (AS-9), check whether a drop in use is daytime-only, and whether it follows sunny days; a drop explained by solar is tagged and penalised, while a night-time drop still counts as evidence | Should | Simulated homes that install solar, for self-consumption or with export, are not among the top suspects; an injected thief in the same zone still is |

### 3.4 Dashboard (UI)

| ID | The system shall… | Priority | Prototype test |
| --- | --- | --- | --- |
| FR-UI-01 | Provide a network overview from pseudonymised, zone-level data only: key figures, a map of zones by gap (no premise locations), ranked leaking zones | Must | Overview shows the flagged simulated zones in gap order, with no personal details |
| FR-UI-02 | Provide a zone view: energy balance over time, hourly gap profile, ranked suspects, neighbour voltage strip | Must | Zone view shows the gap opening on the injected date |
| FR-UI-03 | Provide a premise view: reasons, usage vs. similar homes, neighbour voltage, account context; personal details and exact location only on an open case, for that case's assigned analyst, supervisor and assigned inspector; an automatic case gets its analyst when one claims it | Must | Before a case opens, details are masked for every role; on an open case, the case's analyst, the supervisor and the assigned inspector see them |
| FR-UI-04 | Filter all views by district and date range | Should | Filters change the results shown |
| FR-UI-05 | Export an approved case report as PDF, with personal details added by the system at export | Should | Export blocked until both approvals (FR-AG-01); exported PDF contains the details |

### 3.5 Inspection workflow (IW)

| ID | The system shall… | Priority | Prototype test |
| --- | --- | --- | --- |
| FR-IW-01 | Create cases automatically for premises above the case threshold (a separate job that runs after scoring), or manually by an analyst or supervisor; only a supervisor assigns a case | Must | Pipeline creates cases for top premises; analyst creates one manually; only the supervisor account can assign |
| FR-IW-02 | Let an inspector record the outcome (Confirmed theft, False alarm, Inconclusive, No access), notes and photos | Must | Inspector test account records each outcome type with a photo on a phone |
| FR-IW-03 | Track case status: New, Assigned, Visited, Reporting, Closed. False alarm or Inconclusive closes the case; Confirmed theft moves it to Reporting until the report is exported; No access returns it to Assigned for a revisit | Must | Status history shows each step; a No-access case goes back to Assigned |
| FR-IW-04 | Store each outcome (except No access) as a training label for the next model update | Must | Outcome appears in the training labels |
| FR-IW-05 | Create a small random sample of inspection cases, drawn from all premises in flagged zones regardless of score and presented in the field as routine meter checks, so hit rates can be measured without bias | Must | Random-sample cases are drawn only from flagged zones and reported separately |

### 3.6 Model management (ML)

| ID | The system shall… | Priority | Prototype test |
| --- | --- | --- | --- |
| FR-ML-01 | Retrain the scoring model on new labels at least weekly, with each version recorded | Should | Retrain on demand after new outcomes; new version recorded. On synthetic cases this shows the mechanics, not real improvement |
| FR-ML-02 | Report hit rate and precision for each model version, separately for model-ranked and random-sample inspections | Must | Version list shows both figures side by side |
| FR-ML-03 | Alert the data team to missing data or changes in model behaviour (drift) | Could | Remove data or shift the simulated profiles; alert raised |

### 3.7 AI agents (AG)

| ID | The system shall… | Priority | Prototype test |
| --- | --- | --- | --- |
| FR-AG-01 | Draft a case report with evidence charts, reasons and relevant legal provisions, using placeholders for personal details; the analyst approves the content and a manager gives a second approval before export | Must | Draft holds no personal details and cites the Electricity Supply Act from public text; export blocked until both approvals |
| FR-AG-02 | Suggest the nearest on-duty team for a new case, send reminders when overdue, and escalate to the supervisor; the supervisor approves the suggestion | Must | Simulated roster: nearest team suggested; reminder and escalation fire on shortened demo timers |
| FR-AG-03 | Answer managers' numeric questions through the API's read-only query service, limited to the user's region, showing the query used | Could | Numeric question answered with its query shown; a question about another region is refused |
| FR-AG-04 | Answer inspectors' procedure questions from approved documents, with the source cited | Could | Answer cites its source; an unanswerable question returns "not found" |
| FR-AG-05 | Show the three most similar past cases and their outcomes for each new case | Should | Synthetic closed cases: three similar cases with outcomes shown |
| FR-AG-06 | Never disconnect supply, contact customers, or contact external agencies on its own | Must | Agents have no such tools; test prompts asking for it fail |

### 3.8 Administration and audit (AD)

| ID | The system shall… | Priority | Prototype test |
| --- | --- | --- | --- |
| FR-AD-01 | Restrict every view and action by role and region (see 2.2), enforced in the API; dashboards outside the API show pseudonymised data only | Must | Each test account is refused outside its role and region |
| FR-AD-02 | Log every case view, assignment, outcome, export and agent action with user and time, in a tamper-evident log | Must | Every demo action appears in the audit log; editing a log row is detected |
| FR-AD-03 | Let admins change thresholds and weights without code changes | Should | Change the flag threshold; the rerun uses it |

## 4. Non-functional requirements

Figures below are design targets set by the team, to be confirmed with the pilot partner.

| ID | Category | Requirement | How it is measured |
| --- | --- | --- | --- |
| NFR-01 | Performance | The nightly run finishes within 2 hours of meter data arriving, for the pilot zone and for 100,000 meters | Pipeline run time in logs |
| NFR-02 | Performance | A zone or premise page loads within 3 seconds | Page load time at the 95th percentile |
| NFR-03 | Availability | Dashboard available 99% of business hours during the pilot | Uptime monitoring |
| NFR-04 | Isolation | A VoltGuard failure never affects metering, billing or the grid | Read-only access; failure tests |
| NFR-05 | Scalability | The design scales out by transformer zone towards national coverage | Load test with simulated meters |
| NFR-06 | Security | Encrypted traffic (TLS 1.2 or higher) and encrypted storage; sign-in through the utility's single sign-on | Security review |
| NFR-07 | Privacy | Complies with PDPA 2010 as amended in 2024, including support for the utility's data-protection officer, breach notification to the Commissioner within 72 hours, and data portability requests; analytics use pseudonymised IDs; data never leaves utility infrastructure | Privacy impact assessment |
| NFR-08 | Explainability | Every score shows at least three plain-language reasons | Automated check on outputs |
| NFR-09 | Effectiveness (R0) | In simulated zones held out from tuning (different zone sizes, tap sizes, noise and household profiles), every injected theft appears in the top 5% of ranked premises | Simulation test report on held-out settings |
| NFR-10 | Effectiveness (R1) | Hit rate of model-ranked inspections exceeds the pilot zone's current hit rate, with random-sample inspections as the unbiased reference | Back-test on past confirmed cases, then shadow-pilot results vs. baseline |
| NFR-11 | Fairness | Flag rates are monitored by area and by housing tenure (owner or renter); no proxy signal such as tenancy change may drive a flag on its own (FR-PS-09) | Monthly flag-rate report |
| NFR-12 | Auditability | Each audit row stores its own hash and the previous row's; the latest hash is copied outside the database daily, so a rewritten chain is detectable | Log integrity check |
| NFR-13 | Usability | The inspector view works on a phone screen; labels in English and Bahasa Melayu | Usability test with inspectors |
| NFR-14 | Maintainability | All services run in containers; models and data versions are recorded | Rebuild from scratch in a test environment |
| NFR-15 | AI safety | Agent answers come only from retrieved documents or database results, cite their source, say "not found" otherwise, and need human approval before anything leaves the system; the language model never receives personal details, including any typed into inspector notes | Red-team test set of questions |
| NFR-16 | Device security | The inspector app keeps only assigned cases on the phone, encrypted; wipes them after sync or within 24 hours; keeps photos out of the camera roll; supports remote sign-out | Device test on a lost-phone scenario |

## 5. External interfaces and data requirements

### 5.1 User interfaces

- **Case pages (web app):** zone, premise and case views served through the API, with role-based masking of personal details
- **Manager dashboard:** network overview built only on zone-level, pseudonymised reporting views (Power BI in R0, where every manager sees all regions; web app or Power BI with row-level security by region in R1)
- **Inspector view:** case list, case details, outcome form with photo upload, usable on a phone
- **Chat panel:** questions to the analyst chatbot and field assistant
- **Notifications:** case assignments and reminders through the utility's chosen channel (e.g. Microsoft Teams, SMS); a Telegram bot in R0

### 5.2 Software interfaces

| External system | Data | Direction | Frequency | In the prototype (R0) |
| --- | --- | --- | --- | --- |
| Meter Data Management System (AMI) | Half-hourly kWh and voltage per meter | In | Daily | Simulated extract files |
| Transformer meter system | Energy supplied per transformer | In | Daily | Simulated extract files |
| Network / GIS model | Meter-to-transformer links, feeder branch, phase, street positions | In | Weekly | Simulated network file |
| Billing / customer system | Account holder, tenancy changes, tariff | In | Daily | Simulated account events |
| Workforce / roster system | On-duty teams and base locations | In | Each shift | Simulated roster of three teams |
| Messaging service | Assignments, reminders, escalations | Out | On event | Telegram bot |
| Single sign-on directory | User identity and roles | In | On sign-in | Keycloak with one test account per role |

All inbound connections are read-only. Messages carry a case ID and secure link, never customer names or addresses.

### 5.3 Data requirements

| Data | Minimum quality | Retention |
| --- | --- | --- |
| Meter readings | 30-minute intervals; at least 90% of intervals present per day | Rolling 24 months for analysis |
| Transformer readings | 30-minute or finer intervals | Rolling 24 months |
| Network map | Every meter linked to one transformer | Current version plus history of changes |
| Cases and outcomes | Outcome recorded for every closed case | Per utility retention policy |
| Documents for RAG | Approved versions only, with owner and date | Until replaced |
| Audit log | Every action recorded | Per utility retention policy |

Retention periods are proposals to agree with the utility's data-protection officer.

## 6. Use cases

### 6.1 Summary

| ID | Use case | Primary actor | Requirements |
| --- | --- | --- | --- |
| UC-01 | Review leaking zones | Revenue Protection Manager | FR-ZD-01–02, FR-UI-01 |
| UC-02 | Investigate a zone and its suspects | Analyst | FR-ZD-03–06, FR-PS-01–10, FR-UI-02–03 |
| UC-03 | Assign an inspection | Supervisor | FR-IW-01, FR-AG-02 |
| UC-04 | Inspect a premise and record the outcome | Field Inspector | FR-IW-02–04, FR-AG-04 |
| UC-05 | Generate a case report | Analyst (manager approves export) | FR-AG-01, FR-AG-05 |
| UC-06 | Ask the analyst chatbot | Revenue Protection Manager | FR-AG-03 |
| UC-07 | Retrain and compare models | Data Scientist | FR-ML-01–03 |
| UC-08 | Review access and actions | Auditor | FR-AD-02 |

### 6.2 Detailed use case: UC-04 Inspect a premise and record the outcome

- **Primary actor:** Field Inspector
- **Goal:** confirm or rule out theft at a flagged premise, and feed the result back to the model
- **Preconditions:** the case is assigned to the inspector's team (UC-03); the inspector is signed in on a phone
- **Postconditions:** the outcome is recorded; the case is Closed, in Reporting, or back in Assigned; every outcome except No access is stored as a training label; the action is logged

**Main flow**

1. The inspector opens the assigned case from the notification link.
2. The system shows the address, the top three reasons for the score, and a safety checklist.
3. The inspector visits the premise with the required partners (e.g. police for a suspected mining site).
4. The inspector checks the meter, cabling and load.
5. The inspector selects an outcome: Confirmed theft, False alarm, Inconclusive or No access.
6. The inspector adds notes and photos, then submits.
7. The system records the outcome: False alarm or Inconclusive closes the case; Confirmed theft moves it to Reporting (UC-05); No access returns it to Assigned. It stores the label (except for No access), logs the action and updates the zone view.

**Alternative flows**

- **4a. Premise inaccessible:** the inspector records "No access"; the case returns to Assigned for a revisit and the supervisor is alerted.
- **4b. Inspector unsure what evidence to collect:** the inspector asks the field assistant, which answers from approved procedures with sources (FR-AG-04).
- **5a. Theft confirmed:** the analyst starts UC-05 to draft the case report.
- **5b. Legitimate high use found (e.g. EV charger):** the inspector selects False alarm and tags the reason, so similar patterns score lower in future.

**Exceptions**

- **No mobile signal:** the outcome is saved encrypted on the phone and sent when the connection returns (NFR-16).

## 7. Prototype acceptance

The prototype is accepted when judges can watch each core capability work end to end on simulated data. The step-by-step demo script, data kit and backup tests are in SDD section 10.5.

| Core capability | Requirements | Acceptance criterion in R0 |
| --- | --- | --- |
| Find the leaking zone | FR-DI-01–06, FR-ZD-01–06 | Small and large taps flagged, including one present from day one; clean zones not flagged; zones without a transformer meter marked "no balance" |
| Pinpoint the premises | FR-PS-01–06, FR-PS-09–10 | Every injected theft in the top 5% on held-out simulations (NFR-09); EV charging, rooftop solar, metered mining and tenancy change alone do not reach the top suspects |
| Explain every flag | FR-PS-07–08, FR-UI-03 | Top three plain-language reasons plus "other", adding up to the score, on every flagged premise |
| Inspect and learn | FR-IW-01–05, FR-ML-01–02 | Case assigned, outcome recorded on a phone (including No access), model retrained with a new version; presented as mechanics, not proof of improvement |
| AI agents | FR-AG-01–06 | Report drafted without personal details, cited and held for two approvals; nearest team suggested; chatbot limited to the user's region; field assistant cites sources or says "not found" |
| Safe and accountable | FR-AD-01–03, NFR-07, NFR-12, NFR-15, NFR-16 | Wrong roles and regions refused, personal details masked until a case opens, tampering with the audit log detected, planted instructions ignored, phone data encrypted |

Only two things cannot be shown in R0: the real-world hit rate against TNB's baseline (NFR-10), and live connections to utility systems. Both are the purpose of R1, which starts with a back-test on past confirmed cases and continues as a shadow-mode pilot. The voltage locator is shown working on simulated voltages only; whether it works on TNB meters depends on AS-3.
