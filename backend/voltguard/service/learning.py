"""Model learning (SDD 5.4, FR-ML-01, FR-ML-02, FR-IW-04).

Retrain on demand (weekly in R1) on the inspection labels: every outcome except No access, live
and historic. The label model is XGBoost over the same premise features the R0 score uses,
weighted by how each case was chosen (random-sample cases stand for many unselected premises,
so they weigh more), which corrects for feedback-loop bias. Each version is recorded in
`model_version` and in the MLflow file store (DATA_ROOT/mlruns), with hit rate and precision
reported separately for model-ranked and random-sample inspections.

In R0 the score stays the additive, explainable sum; the label model is recorded and evaluated
for R1. On synthetic outcomes this shows the mechanics of learning, not real improvement.
"""

from __future__ import annotations

import json
from datetime import datetime

import numpy as np
from psycopg.types.json import Jsonb

from voltguard import config, db
from voltguard.detection.features import FEATURE_NAMES

RANDOM_SAMPLE_WEIGHT = 5.0     # inverse of the (small) share of inspections that are random samples (OI-10)


def labels(conn) -> list[dict]:
    """Training labels with the premise's features from the latest run on or before the outcome."""
    return conn.execute(
        """SELECT l.case_id, l.premise_id, l.origin, l.outcome, l.is_theft, l.source, l.recorded_at,
                  (SELECT c.score_at_creation FROM inspection_case c WHERE c.case_id = l.case_id) AS score_at_creation,
                  f.features
           FROM training_label l
           LEFT JOIN LATERAL (SELECT features FROM premise_feature pf WHERE pf.premise_id = l.premise_id
                              ORDER BY (pf.run_date <= l.recorded_at::date) DESC, pf.run_date DESC LIMIT 1) f ON true""").fetchall()


def hit_rates(rows: list[dict], case_threshold: float) -> dict:
    """Hit rate (share confirmed) and precision (share confirmed among cases at or above the case threshold),
    separately for model-ranked (model + manual) and random-sample inspections (FR-ML-02)."""
    out = {}
    for group, members in (("model_ranked", [r for r in rows if r["origin"] != "random_sample"]),
                           ("random_sample", [r for r in rows if r["origin"] == "random_sample"])):
        n = len(members)
        hits = sum(1 for r in members if r["is_theft"])
        above = [r for r in members if r["score_at_creation"] is not None and r["score_at_creation"] >= case_threshold]
        out[group] = {"inspections": n, "confirmed_theft": hits, "hit_rate": round(hits / n, 3) if n else None,
                      "precision_at_threshold": round(sum(r["is_theft"] for r in above) / len(above), 3) if above else None,
                      "scored_at_or_above_threshold": len(above)}
    return out


def _log_mlflow(version: str, params: dict, metrics: dict, model_path) -> str | None:
    try:
        import mlflow

        mlflow.set_tracking_uri((config.data_root() / "mlruns").as_uri())
        mlflow.set_experiment("voltguard-label-model")
        with mlflow.start_run(run_name=version) as run:
            mlflow.log_params(params)
            flat = {f"{g}_{k}": v for g, d in metrics.get("hit_rates", {}).items() for k, v in d.items() if isinstance(v, (int, float))}
            flat.update({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
            mlflow.log_metrics(flat)
            if model_path:
                mlflow.log_artifact(str(model_path))
            return run.info.run_id
    except Exception:  # MLflow is a record-keeping mirror; the model_version table is the source of truth
        return None


def retrain(actor: str = "data_scientist", progress=print) -> dict:
    with db.admin_connection() as conn:
        with conn.transaction():
            cfg_cases = config.thresholds()["cases"]
            rows = labels(conn)
            usable = [r for r in rows if r["features"]]
            n = conn.execute("SELECT count(*) AS n FROM model_version").fetchone()["n"]
            version = f"label-v{n + 1}"
            metrics = {"labels": len(rows), "labels_with_features": len(usable),
                       "confirmed_theft": sum(r["is_theft"] for r in rows), "hit_rates": hit_rates(rows, cfg_cases["case_threshold"]),
                       "note": "Synthetic outcomes in R0: this shows the mechanics of learning, not real-world improvement."}
            model_path = None
            classes = {bool(r["is_theft"]) for r in usable}
            progress(f"Training {version} on {len(usable)} labelled premises...")
            if len(usable) >= 6 and len(classes) == 2:
                import xgboost as xgb

                X = np.array([[float(r["features"].get(f, 0.0)) for f in FEATURE_NAMES] for r in usable])
                y = np.array([int(r["is_theft"]) for r in usable])
                w = np.array([RANDOM_SAMPLE_WEIGHT if r["origin"] == "random_sample" else 1.0 for r in usable])
                booster = xgb.train({"objective": "binary:logistic", "max_depth": 2, "eta": 0.2, "seed": 3, "nthread": 2},
                                    xgb.DMatrix(X, label=y, weight=w, feature_names=FEATURE_NAMES), num_boost_round=40)
                pred = booster.predict(xgb.DMatrix(X, feature_names=FEATURE_NAMES))
                from voltguard.detection.pattern import auc

                metrics["training_auc"] = round(auc(y, pred), 3)
                importance = booster.get_score(importance_type="gain")
                metrics["top_features"] = sorted(importance, key=importance.get, reverse=True)[:5]
                model_path = config.data_path("models", f"{version}.json")
                booster.save_model(str(model_path))
            else:
                metrics["skipped"] = "Need at least 6 labelled premises with both outcomes to fit the label model"
            snapshot = conn.execute("SELECT data_snapshot FROM detection_run WHERE status = 'done' ORDER BY run_id DESC LIMIT 1").fetchone()
            run_id = _log_mlflow(version, {"labels": len(usable), "random_sample_weight": RANDOM_SAMPLE_WEIGHT,
                                           "features": ",".join(FEATURE_NAMES)}, metrics, model_path)
            metrics["mlflow_run_id"] = run_id
            conn.execute("UPDATE model_version SET active = false WHERE active")
            conn.execute("""INSERT INTO model_version (version_id, data_snapshot, metrics, active, notes) VALUES (%s, %s, %s, true, %s)""",
                         (version, snapshot["data_snapshot"] if snapshot else None, Jsonb(metrics),
                          "R0 score stays additive; label model recorded for R1"))
            db.audit(conn, actor, "model.retrain", f"model:{version}", {"labels": len(rows)})
    progress(f"Recorded {version}")
    return {"version_id": version, "trained_at": datetime.now().isoformat(timespec="seconds"), "metrics": metrics}


def versions(conn) -> list[dict]:
    rows = conn.execute("SELECT version_id, trained_at, data_snapshot, metrics, active, notes FROM model_version ORDER BY trained_at DESC").fetchall()
    for r in rows:
        r["metrics"] = r["metrics"] if isinstance(r["metrics"], dict) else json.loads(r["metrics"] or "{}")
    return rows
