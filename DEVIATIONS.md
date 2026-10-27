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
