"""Anomaly score (SDD 5.3): how badly an autoencoder trained on normal homes rebuilds a premise's week.

The SDD names a PyTorch autoencoder; the lite profile uses scikit-learn's MLPRegressor as a
small bottleneck autoencoder behind the same role (see DEVIATIONS.md), which avoids a large
PyTorch install on the laptop.
"""

from __future__ import annotations

import pickle

import numpy as np

from voltguard import config

HOURS_PER_WEEK = 7 * 24


def week_vector(kwh_slots: np.ndarray) -> np.ndarray | None:
    """Last 7 days of half-hourly kWh -> 168 hourly values scaled by their mean."""
    x = np.asarray(kwh_slots[-7 * 48:], dtype=float)
    if len(x) < 7 * 48 or not np.isfinite(x).all():
        return None
    hourly = x.reshape(HOURS_PER_WEEK, 2).sum(axis=1)
    mean = hourly.mean()
    if mean <= 0:
        return None
    return hourly / mean


class Autoencoder:
    def __init__(self, model):
        self.model = model

    def error(self, vectors: np.ndarray) -> np.ndarray:
        recon = self.model.predict(vectors)
        return ((recon - vectors) ** 2).mean(axis=1)


def train(vectors: np.ndarray, seed: int = 3) -> Autoencoder:
    from sklearn.neural_network import MLPRegressor

    model = MLPRegressor(hidden_layer_sizes=(48, 12, 48), activation="relu", max_iter=400,
                         early_stopping=True, random_state=seed)
    model.fit(vectors, vectors)
    return Autoencoder(model)


def model_path():
    return config.data_path("models", "autoencoder.pkl")


def save(ae: Autoencoder) -> None:
    with model_path().open("wb") as handle:
        pickle.dump(ae.model, handle)


_cached: Autoencoder | None = None


def load() -> Autoencoder | None:
    global _cached
    if _cached is None and model_path().exists():
        with model_path().open("rb") as handle:
            _cached = Autoencoder(pickle.load(handle))
    return _cached


def train_from_simulation(seed: int = 1000) -> Autoencoder:
    """Train on normal homes from the tuning simulation (never the held-out settings)."""
    from voltguard.data import simulator
    from voltguard.detection.zone_input import build_zone_inputs

    scn = simulator.tuning_scenario(seed=seed, count=8)
    tables, truth = simulator.simulate(scn)
    zones = build_zone_inputs(tables, scn.start_date, scn.days)
    injected = {c["premise_id"] for z in truth["zones"].values() for c in z["cases"]}
    vectors = []
    for z in zones.values():
        for i, pid in enumerate(z.premise_ids):
            if pid in injected or not z.smart[i]:
                continue
            row = np.nan_to_num(z.kwh[i], nan=np.nanmean(z.kwh[i]))
            for end in range(7 * 48, z.T + 1, 7 * 48):
                v = week_vector(row[:end])
                if v is not None:
                    vectors.append(v)
    ae = train(np.array(vectors))
    save(ae)
    global _cached
    _cached = ae
    return ae
