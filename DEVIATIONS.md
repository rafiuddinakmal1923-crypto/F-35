# Deviations from the SDD

Every swap below sits behind the same interface as the SDD component, so the full component
can replace it without changing callers. No privacy, audit or approval rule was dropped.

## Lite-profile swaps (prompt 7.2)

| SDD component | R0 lite profile | Reason | Where |
| --- | --- | --- | --- |
| Apache Airflow (ingestion) and Celery + Redis (jobs) | APScheduler inside the API plus the CLI runner (`python -m voltguard`) | One laptop; fewer containers and less memory | `backend/voltguard/cli.py`, scheduler module |
| MinIO file storage | Encrypted files under `${DATA_ROOT}` reached only through the case service | No extra service; same "case service only" access rule | storage module |
| Keycloak (OpenID Connect) | Built-in sign-in with the same roles, regions and teams; signed JWTs | Keycloak needs ~1 GB RAM | auth module |
| MLflow server | MLflow file store under `${DATA_ROOT}/mlruns` plus the `model_version` table | No server process | learning module |
| Prometheus + Grafana | `/metrics` endpoint plus structured logs | Laptop memory | API |

The full profile (`docker compose --profile full up -d`) starts the heavier services so the
R1 architecture can be shown; the application still uses the lite implementations unless a
later change wires them in.

## Library swaps

| SDD | Used | Reason |
| --- | --- | --- |
| pandapower load flow | Own backward/forward-sweep solver for radial LV feeders, vectorised over time (`network.py`) | pandapower's balanced solver cannot model one phase of a three-phase LV network, which the voltage locator needs (a single-phase tap mainly pulls down its own phase); the sweep runs 61 days x 48 intervals in seconds |
| ruptures (change point) | Own single change-point search on the daily gap share with a t-statistic (`balance.change_point`) | One change point per zone is enough; avoids a dependency |
| PyTorch autoencoder | scikit-learn `MLPRegressor` bottleneck autoencoder (`anomaly.py`) | Avoids a ~2 GB PyTorch install on the laptop |
| SHAP package | XGBoost's exact TreeSHAP contributions (`pred_contribs=True`) for pattern-model sub-reasons | Same values, no extra dependency |

## Data

| Prompt | R0 | Reason |
| --- | --- | --- |
| SGCC dataset trains the pattern model | Trained on SGCC when `processed/sgcc_windows.parquet` exists, otherwise on synthetic windows that follow the published SGCC theft patterns | Kaggle needs an API key; the demo must run offline. The model metadata and the simulation report say which source was used |
| London profiles feed the simulator | Built-in synthetic tropical (aircon-heavy) profiles by default; London shapes when processed | Same reason |
| Per-table sources `simulated`, `london`, `sgcc`, `datagovmy`, `upload:<name>` | Per-table values `simulated`, `london`, `upload:<name>[@vN]`; SGCC is chosen by `pattern_training: sgcc` and data.gov.my by `rescale: datagovmy` | SGCC has no meter-to-transformer links and data.gov.my holds national monthly totals, so neither can fill a canonical table on its own |
| data.gov.my rescales profiles to Malaysian consumption levels | Monthly seasonality factors from domestic consumption; the household level stays the configurable `mean_kwh` placeholder | The dataset has no household count, so a per-household level would be an invented figure |
| London data feeds the simulator | Also converted to canonical tables (pseudo zones of 60 homes, no voltage, phase or transformer meter) | Exercises the AS-1/AS-2/AS-3/AS-7 fallbacks on real household load |

## Agents and RAG

| Prompt / SDD | R0 | Reason |
| --- | --- | --- |
| Presidio for notes scrubbing | Malaysian regex recognisers always; Presidio with spaCy `en_core_web_sm` adds PERSON, e-mail and phone (LOCATION left to the address patterns; one-word and lower-case "names" ignored) | Presidio's LOCATION and one-word PERSON hits flagged zone IDs and ordinary words; Presidio would otherwise download a 560 MB model at runtime |
| multilingual-e5-small embeddings | Used through ONNX Runtime when `fetch-models` has downloaded it; otherwise a deterministic 384-dim hashing embedder plus keyword overlap | The demo must work offline; the index records which embedder built it |
| Language model drafts the report | Facts, reasons, notes and citations are filled from the database by template; the model writes only the assessment paragraph (`REPORT_MODE=live`), pre-drafted at setup (`predrafted`) or from a template (`mock`) | A 4-bit 7B model on a laptop CPU is slow, and facts must never depend on generation |
| Chatbot query service | Fixed, whitelisted read-only query templates; the model (if any) only picks a template and its parameters | No model-written SQL reaches the database |
| Public legal texts for RAG | Not copied into the repository; `scripts/fetch_docs.py` downloads them when a verified URL is set, otherwise prints manual steps. Until loaded, legal questions return "not found" and reports cite Section 37 by name only | No invented or unverified legal text |

## Additions after the R0 review (not in the SDD)

| Addition | What it does | Rule kept |
| --- | --- | --- |
| Telegram dispatch bot with buttons (`service/telegram.py`) | Supervisor approves or rejects suggestions; team accepts, says it is on the way, or cannot attend; works without a token as an in-app chat | Messages carry a case ID and link only; each press runs as the linked person with their role and region, is audited and answers a message once |
| Route planner (`agents/route.py`) | Visiting order of a team's cases with distances and arrival estimates | Locations only through `vg_case_contact`; no routing service is called. The Google Maps / Waze buttons send the destination coordinates (never a name or address) to that app when the inspector taps them. TNB may prefer its own navigation app (open issue for R1) |
| Weekly summary (`service/digest.py`) | Region page, PDF and a Monday message to managers and supervisors | Zone-level figures and case counts only; value at risk stays a `[TNB tariff: to be supplied]` placeholder |
| "My work" home and badges (`service/work.py`) | Next actions per role | Reads through the caller's own connection, so role and region rules apply |
| Batched nightly run (`service/pipeline.py`) | Readings in meter batches, detection in zone batches | Same results as one batch (tested); validation still stops the run on errors |
| Map background (`components/BaseTiles.jsx`) | CARTO basemap first, then OpenStreetMap, then Esri, switching when a provider's tiles fail; a note when none load | OpenStreetMap's tile servers block many apps on localhost with an "Access blocked" image. CARTO's free basemap is for light, non-commercial use with attribution (shown); R1 should use the utility's own map server. Tile requests carry only map coordinates, never case data |
