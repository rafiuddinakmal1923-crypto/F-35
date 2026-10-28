"""Pattern model (SDD 5.4): XGBoost on daily-consumption windows, one input of the R0 score.

Training data is the labelled SGCC dataset when its adapter has produced
`processed/sgcc_windows.parquet`; otherwise a synthetic set built from the published SGCC
theft patterns (scaling, random daily scaling, a drop from a start day, flattening, zero
days), so the pipeline works offline. The README and model metadata say which was used.

Sub-reasons come from XGBoost's exact TreeSHAP contributions (`pred_contribs=True`), so no
separate SHAP package is needed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np

from voltguard import config

WINDOW_DAYS = 28
FEATURES = [
    "cv", "min_ratio", "max_ratio", "zero_day_share", "trend", "half_ratio",
    "max_drop", "weekly_autocorr", "low_day_share", "last_first_week_ratio", "level_vs_peers",
]
FEATURE_TEXT = {
    "cv": "how much daily use varies",
    "min_ratio": "unusually low days",
    "max_ratio": "unusually high days",
    "zero_day_share": "days with almost no use",
    "trend": "a steady fall in use",
    "half_ratio": "lower use in the second half of the month",
    "max_drop": "a sudden drop between consecutive weeks",
    "weekly_autocorr": "a weekly pattern that has broken down",
    "low_day_share": "many days well below its usual level",
    "last_first_week_ratio": "the last week compared with the first",
    "level_vs_peers": "use far below similar homes",
}


def window_features(daily: np.ndarray, peer_median: float | None = None) -> np.ndarray:
    """Features of one premise's last WINDOW_DAYS daily totals (kWh)."""
    x = np.asarray(daily[-WINDOW_DAYS:], dtype=float)
    x = np.nan_to_num(x, nan=np.nanmean(x) if np.isfinite(x).any() else 0.0)
    mean = max(x.mean(), 1e-6)
    med = max(float(np.median(x)), 1e-6)
    weeks = x[: len(x) // 7 * 7].reshape(-1, 7).mean(axis=1) if len(x) >= 14 else np.array([mean, mean])
    slope = np.polyfit(np.arange(len(x)), x / mean, 1)[0] * len(x) if len(x) > 2 else 0.0
    half = len(x) // 2
    if len(x) > 14 and x[:-7].std() > 0 and x[7:].std() > 0:
        auto = float(np.corrcoef(x[:-7], x[7:])[0, 1])
    else:
        auto = 0.0
    return np.array([
        x.std() / mean,
        x.min() / mean,
        x.max() / mean,
        float((x < 0.05 * med).mean()),
        slope,
        x[half:].mean() / max(x[:half].mean(), 1e-6),
        float(np.max(np.clip(weeks[:-1] - weeks[1:], 0, None)) / mean) if len(weeks) > 1 else 0.0,
        auto,
        float((x < 0.5 * med).mean()),
        weeks[-1] / max(weeks[0], 1e-6),
        mean / max(peer_median, 1e-6) if peer_median else 1.0,
    ])


def synthetic_training_set(seed: int = 7, n: int = 4000) -> tuple[np.ndarray, np.ndarray]:
    """Labelled windows following the SGCC theft types; used when the SGCC data is not loaded."""
    rng = np.random.default_rng(seed)
    X, y = [], []
    for _ in range(n):
        level = rng.lognormal(np.log(11), 0.45)
        weekly = 1 + 0.08 * np.sin(np.arange(WINDOW_DAYS) * 2 * np.pi / 7 + rng.uniform(0, 6))
        x = level * weekly * rng.normal(1, 0.12, WINDOW_DAYS).clip(0.3)
        peer = level * rng.lognormal(0, 0.35)
        label = int(rng.random() < 0.3)
        if label:
            kind = rng.integers(0, 5)
            if kind == 0:
                x = x * rng.uniform(0.2, 0.7)
            elif kind == 1:
                x = x * rng.uniform(0.1, 0.9, WINDOW_DAYS)
            elif kind == 2:
                start = rng.integers(5, WINDOW_DAYS - 5)
                x[start:] *= rng.uniform(0.15, 0.6)
            elif kind == 3:
                x = np.full(WINDOW_DAYS, x.mean() * rng.uniform(0.3, 0.8)) * rng.normal(1, 0.02, WINDOW_DAYS)
            else:
                x[rng.random(WINDOW_DAYS) < rng.uniform(0.2, 0.6)] = 0.0
        X.append(window_features(x, peer))
        y.append(label)
    return np.array(X), np.array(y)


def sgcc_training_set() -> tuple[np.ndarray, np.ndarray] | None:
    path = config.data_root() / "processed" / "sgcc_windows.parquet"
    if not path.exists():
        return None
    import polars as pl

    frame = pl.read_parquet(path)
    days = [c for c in frame.columns if c.startswith("d")]
    values = frame.select(days).to_numpy()
    X = np.array([window_features(row) for row in values])
    return X, frame["flag"].to_numpy().astype(int)


@dataclass
class PatternModel:
    booster: object
    source: str
    version: str = "pattern-v1"

    def predict(self, X: np.ndarray) -> np.ndarray:
        import xgboost as xgb

        return self.booster.predict(xgb.DMatrix(X, feature_names=FEATURES))

    def contributions(self, X: np.ndarray) -> np.ndarray:
        import xgboost as xgb

        return self.booster.predict(xgb.DMatrix(X, feature_names=FEATURES), pred_contribs=True)[:, :-1]

    def sub_reasons(self, x_row: np.ndarray, top: int = 2) -> list[str]:
        contrib = self.contributions(x_row[None, :])[0]
        order = np.argsort(-contrib)
        return [FEATURE_TEXT[FEATURES[i]] for i in order[:top] if contrib[i] > 0]

    def sub_reason_values(self, x_row: np.ndarray, top: int = 4) -> list[dict]:
        """SHAP contributions (log-odds) of the strongest inputs, for the premise page's expandable bar."""
        contrib = self.contributions(x_row[None, :])[0]
        order = np.argsort(-np.abs(contrib))
        return [{"feature": FEATURES[i], "text": FEATURE_TEXT[FEATURES[i]], "shap": round(float(contrib[i]), 3)}
                for i in order[:top] if abs(contrib[i]) >= 1e-3]


def train(X: np.ndarray, y: np.ndarray, sample_weight: np.ndarray | None = None, seed: int = 7):
    import xgboost as xgb

    dtrain = xgb.DMatrix(X, label=y, weight=sample_weight, feature_names=FEATURES)
    params = {"objective": "binary:logistic", "max_depth": 4, "eta": 0.1, "subsample": 0.9,
              "colsample_bytree": 0.9, "eval_metric": "auc", "seed": seed, "nthread": 2}
    return xgb.train(params, dtrain, num_boost_round=150)


def auc(y: np.ndarray, p: np.ndarray) -> float:
    order = np.argsort(p)
    ranks = np.empty(len(p))
    ranks[order] = np.arange(1, len(p) + 1)
    pos = y == 1
    n_pos, n_neg = pos.sum(), (~pos).sum()
    if not n_pos or not n_neg:
        return float("nan")
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def model_path():
    return config.data_path("models", "pattern_xgb.json")


def train_default(save: bool = True) -> tuple[PatternModel, dict]:
    """Train on SGCC if loaded, else the synthetic set; hold out 20% to report AUC."""
    wanted = config.data_sources().get("pattern_training", "synthetic")
    data = sgcc_training_set() if wanted == "sgcc" else None
    source = "sgcc"
    if data is None:
        data, source = synthetic_training_set(), "synthetic_sgcc_patterns"
    X, y = data
    rng = np.random.default_rng(11)
    test = rng.random(len(y)) < 0.2
    booster = train(X[~test], y[~test])
    model = PatternModel(booster, source)
    metrics = {"source": source, "train_rows": int((~test).sum()), "holdout_rows": int(test.sum()),
               "holdout_auc": round(auc(y[test], model.predict(X[test])), 4)}
    if save:
        booster.save_model(str(model_path()))
        model_path().with_suffix(".meta.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return model, metrics


_cached: PatternModel | None = None


def load() -> PatternModel:
    global _cached
    if _cached is not None:
        return _cached
    import xgboost as xgb

    path = model_path()
    if path.exists():
        booster = xgb.Booster()
        booster.load_model(str(path))
        meta_path = path.with_suffix(".meta.json")
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        _cached = PatternModel(booster, meta.get("source", "unknown"), meta.get("version", "pattern-v1"))
    else:
        _cached, _ = train_default(save=True)
    return _cached


def reset_cache() -> None:
    global _cached
    _cached = None
