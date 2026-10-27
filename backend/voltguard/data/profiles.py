"""Household load profiles for the simulator (SDD 10.2).

Default: a built-in synthetic generator with tropical, aircon-heavy daily shapes, so the
whole demo runs offline with no downloads. If the London smart-meter adapter has produced
`processed/london_profiles.parquet`, its half-hourly shapes are used instead, blended with
an aircon component to shift them towards Malaysian homes.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

SLOTS_PER_DAY = 48
HOURS = np.arange(SLOTS_PER_DAY) / 2.0  # slot start hour


def _bump(center: float, width: float) -> np.ndarray:
    """Smooth daily bump (wraps around midnight)."""
    delta = np.minimum(np.abs(HOURS - center), 24 - np.abs(HOURS - center))
    return np.exp(-0.5 * (delta / width) ** 2)


def _night_block(start: float, end: float) -> np.ndarray:
    """1 between start and end hour (end may be after midnight), with soft edges."""
    if end > start:
        inside = (HOURS >= start) & (HOURS < end)
    else:
        inside = (HOURS >= start) | (HOURS < end)
    block = inside.astype(float)
    return np.convolve(np.r_[block[-2:], block, block[:2]], np.ones(5) / 5, mode="valid")


def synthetic_shapes(rng: np.random.Generator, n_homes: int, family: str = "A") -> np.ndarray:
    """Normalised daily shapes (n_homes, 48), each summing to 1."""
    shapes = np.zeros((n_homes, SLOTS_PER_DAY))
    for i in range(n_homes):
        base = rng.uniform(0.6, 1.2)
        morning = rng.uniform(0.3, 1.0) * _bump(rng.uniform(6.0, 8.0), 0.8)
        evening = rng.uniform(1.0, 2.2) * _bump(rng.uniform(19.5, 21.5), 1.4)
        aircon_start = rng.uniform(21.0, 23.5) if family == "A" else rng.uniform(20.0, 22.0)
        aircon_end = rng.uniform(5.0, 7.0)
        aircon = rng.uniform(1.0, 3.0) * _night_block(aircon_start, aircon_end) * (rng.random() < 0.85)
        day_home = rng.random() < (0.35 if family == "A" else 0.5)
        daytime = day_home * rng.uniform(0.5, 1.5) * _bump(rng.uniform(13.0, 15.5), 2.0)
        shape = base + morning + evening + aircon + daytime
        shapes[i] = shape / shape.sum()
    return shapes


def london_shapes(path: Path, rng: np.random.Generator, n_homes: int) -> np.ndarray | None:
    """Average daily shapes from London households, blended with a tropical aircon block."""
    if not path.exists():
        return None
    import polars as pl

    frame = pl.read_parquet(path)
    households = frame["household"].unique().to_list()
    if not households:
        return None
    picks = rng.choice(households, size=n_homes, replace=len(households) < n_homes)
    shapes = np.zeros((n_homes, SLOTS_PER_DAY))
    for i, household in enumerate(picks):
        rows = frame.filter(pl.col("household") == household)
        slot_means = rows.group_by("slot").agg(pl.col("kwh").mean()).sort("slot")["kwh"].to_numpy()
        if len(slot_means) != SLOTS_PER_DAY or slot_means.sum() <= 0:
            slot_means = np.ones(SLOTS_PER_DAY)
        london = slot_means / slot_means.sum()
        aircon = _night_block(rng.uniform(21.0, 23.0), rng.uniform(5.0, 7.0))
        blended = 0.5 * london + 0.5 * aircon / aircon.sum()
        shapes[i] = blended / blended.sum()
    return shapes


def daily_levels(rng: np.random.Generator, n_homes: int, mean_kwh: float = 11.0) -> np.ndarray:
    """Mean daily consumption per home (kWh/day), lognormal around Malaysian domestic levels."""
    sigma = 0.45
    return rng.lognormal(np.log(mean_kwh) - sigma**2 / 2, sigma, size=n_homes)


def household_load_kw(
    rng: np.random.Generator,
    shapes: np.ndarray,
    levels: np.ndarray,
    days: int,
    start_weekday: int,
    weather: np.ndarray,
    noise: float = 0.25,
) -> np.ndarray:
    """Half-hourly average power (n_homes, days*48) in kW.

    weather: (days,) zone-wide daily multiplier (hot days use more aircon).
    """
    n_homes = shapes.shape[0]
    weekday = (start_weekday + np.arange(days)) % 7
    weekend = np.where(weekday >= 5, 1.08, 1.0)
    day_factor = weather[None, :] * weekend[None, :] * rng.normal(1.0, 0.07, size=(n_homes, days))
    kwh = levels[:, None, None] * shapes[:, None, :] * day_factor[:, :, None]
    kwh *= rng.gamma(1.0 / noise**2, noise**2, size=kwh.shape)
    return np.clip(kwh.reshape(n_homes, days * SLOTS_PER_DAY), 0.0, None) * 2.0  # kWh per half hour -> kW
