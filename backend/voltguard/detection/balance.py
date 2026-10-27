"""Stage 1: zone energy balance (SDD 5.1, FR-ZD-01 to FR-ZD-06).

Gap G(z,d) = supply - smart-metered energy - estimate for monthly-read meters - technical loss.
Technical loss is an engineering estimate from the load-flow model, not a historical
baseline, so theft already running at go-live still shows as excess loss.
Flag rule: G > max(theta * supply, G_min) + u for k consecutive days, where
u = sqrt(u_conv^2 + u_meter^2 + u_loss^2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

from voltguard.detection.zone_input import SLOTS, ZoneInput
from voltguard.network import V_NOMINAL, LossParams, ZoneNetwork, solve

DEFAULT_LOSS_SHARE = 0.01  # fallback when no zone in the run has network parameters


@dataclass
class BalanceResult:
    transformer_id: str
    balance_available: bool
    dates: list[date]
    supplied_kwh: np.ndarray
    metered_kwh: np.ndarray
    estimated_kwh: np.ndarray            # monthly-read meters spread into days (FR-ZD-05)
    tech_loss_kwh: np.ndarray
    uncertainty_kwh: np.ndarray
    gap_kwh: np.ndarray
    gap_pct: np.ndarray
    over_threshold: np.ndarray           # day passes the flag rule
    flagged: bool = False
    priority: str = "normal"             # normal | large_load
    gap_start: date | None = None
    gap_since_start: bool = False        # no change point: present since data start (FR-ZD-03)
    flatness_cv: float | None = None
    hourly_gap_kwh: np.ndarray | None = None   # (24,) mean gap per hour of day (FR-ZD-04)
    slot_gap_kwh: np.ndarray | None = None     # (T,) half-hourly gap, used to weight voltage evidence
    loss_method: str = "load_flow"       # load_flow | similar_zones | none
    notes: list[str] = field(default_factory=list)

    @property
    def gap_start_index(self) -> int | None:
        if self.gap_start is None:
            return None
        return (self.gap_start - self.dates[0]).days


def fill_smart_readings(z: ZoneInput) -> tuple[np.ndarray, np.ndarray]:
    """Fill missing half-hours of smart meters with the premise's median for that slot of day.

    Returns filled kWh (n, T) with zeros for conventional premises, and completeness (n, days).
    """
    kwh = z.kwh.copy()
    present = np.isfinite(kwh)
    completeness = present.reshape(z.n, z.days, SLOTS).mean(axis=2)
    by_slot = kwh.reshape(z.n, z.days, SLOTS)
    slot_median = np.zeros((z.n, SLOTS))
    has_data = present.any(axis=1)
    if has_data.any():
        slot_median[has_data] = np.nanmedian(by_slot[has_data], axis=1)  # (n, 48); all-NaN slots stay NaN
    slot_median = np.nan_to_num(slot_median, nan=0.0)
    fill = np.tile(slot_median, (1, z.days))
    kwh = np.where(present, kwh, fill)
    kwh[~z.smart] = 0.0
    return kwh, completeness


def data_quality_flags(z: ZoneInput, completeness: np.ndarray, min_completeness: float) -> list[dict]:
    """Meter-days below the minimum share of intervals present (FR-DI-06, SRS 5.3)."""
    flags = []
    dates = z.day_dates()
    for i in np.where(z.smart)[0]:
        for d in np.where(completeness[i] < min_completeness)[0]:
            flags.append({"meter_id": z.meter_ids[i], "premise_id": z.premise_ids[i], "date": dates[d],
                          "completeness": round(float(completeness[i, d]), 3)})
    return flags


def similar_groups(z: ZoneInput) -> dict[str, np.ndarray]:
    types = np.array(z.premises["premise_type"].to_list())
    return {t: np.where(types == t)[0] for t in set(types)}


def estimate_conventional(z: ZoneInput, filled: np.ndarray, daily_cv: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Spread monthly readings across days with similar smart homes' profiles (FR-ZD-05).

    Returns half-hourly estimate (n, T), daily estimate (n, days) and the zone's daily
    uncertainty u_conv (days,).
    """
    est = np.zeros((z.n, z.T))
    daily_est = np.zeros((z.n, z.days))
    u_conv = np.zeros(z.days)
    conventional = np.where(~z.smart)[0]
    if not len(conventional):
        return est, daily_est, u_conv
    groups = similar_groups(z)
    types = np.array(z.premises["premise_type"].to_list())
    smart_idx = np.where(z.smart)[0]
    dates = z.day_dates()
    months = np.array([d.replace(day=1) for d in dates])
    for i in conventional:
        peers = np.intersect1d(groups.get(types[i], smart_idx), smart_idx)
        peers = peers if len(peers) else smart_idx
        if not len(peers):
            continue
        peer_slots = filled[peers].mean(axis=0)                 # (T,) average smart peer
        peer_daily = peer_slots.reshape(z.days, SLOTS).sum(axis=1)
        readings = z.monthly.get(int(i), {})
        variance_scale = np.ones(z.days)
        daily = np.zeros(z.days)
        for month in sorted(set(months)):
            mask = months == month
            share = peer_daily[mask] / max(peer_daily[mask].sum(), 1e-9)
            if month in readings:
                daily[mask] = readings[month] * share
            else:
                # Reading not in yet: carry the last month's daily level forward, with a wider margin.
                prior = [readings[m] / _days_in(m) for m in sorted(readings) if m < month]
                level = prior[-1] if prior else float(np.median(peer_daily))
                daily[mask] = level * share * mask.sum()
                variance_scale[mask] = 2.0
        shape = peer_slots.reshape(z.days, SLOTS) / np.maximum(peer_daily[:, None], 1e-9)
        est[i] = (shape * daily[:, None]).ravel()
        daily_est[i] = daily
        u_conv += (daily_cv * daily * variance_scale) ** 2
    return est, daily_est, np.sqrt(u_conv)


def _days_in(month: date) -> int:
    nxt = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
    return (nxt - month).days


def network_for(z: ZoneInput, params: LossParams | None = None) -> ZoneNetwork | None:
    if not z.has_topology:
        return None
    prem = z.premises
    return ZoneNetwork.from_premises(
        prem["feeder_branch"].to_list(), prem["distance_m"].to_list(), z.phase_index(), params or z.loss_params or LossParams()
    )


def technical_loss(z: ZoneInput, load_kwh: np.ndarray, fallback_share: float) -> tuple[np.ndarray, str]:
    """Half-hourly technical loss (T,) from the load-flow model, or from similar zones (AS-8)."""
    if z.loss_params is not None and z.has_topology:
        net = network_for(z)
        v_tx = z.tx_voltage if z.tx_voltage is not None else V_NOMINAL + 6.0
        v_tx = np.where(np.isfinite(v_tx), v_tx, np.nanmedian(v_tx)) if np.ndim(v_tx) else v_tx
        flow = solve(net, load_kwh * 2.0, v_tx)
        return flow.loss_kw * 0.5, "load_flow"
    supply = z.supply_kwh if z.supply_kwh is not None else load_kwh.sum(axis=0)
    return np.nan_to_num(supply) * fallback_share, "similar_zones"


def change_point(series: np.ndarray, min_segment: int) -> tuple[int | None, float, float]:
    """Single mean-shift change point by least squares. Returns (index, shift, t-statistic)."""
    x = np.asarray(series, dtype=float)
    n = len(x)
    best = (None, 0.0, 0.0)
    best_sse = np.inf
    for t in range(min_segment, n - min_segment + 1):
        a, b = x[:t], x[t:]
        sse = ((a - a.mean()) ** 2).sum() + ((b - b.mean()) ** 2).sum()
        if sse < best_sse:
            pooled = np.sqrt(sse / max(n - 2, 1))
            tstat = (b.mean() - a.mean()) / max(pooled * np.sqrt(1 / len(a) + 1 / len(b)), 1e-9)
            best_sse, best = sse, (t, float(b.mean() - a.mean()), float(tstat))
    return best


def balance_zone(z: ZoneInput, cfg: dict, filled: np.ndarray, conv_est: np.ndarray, u_conv: np.ndarray,
                 fallback_loss_share: float = DEFAULT_LOSS_SHARE) -> BalanceResult:
    zc = cfg["zone"]
    dates = z.day_dates()
    load = filled + conv_est
    metered_daily = filled.reshape(z.n, z.days, SLOTS).sum(axis=(0, 2))
    estimated_daily = conv_est.reshape(z.n, z.days, SLOTS).sum(axis=(0, 2))
    loss_slots, method = technical_loss(z, load, fallback_loss_share)
    loss_daily = loss_slots.reshape(z.days, SLOTS).sum(axis=1)

    if not z.has_dtm:
        nan = np.full(z.days, np.nan)
        return BalanceResult(
            z.transformer_id, False, dates, nan, metered_daily, estimated_daily, loss_daily, nan, nan, nan,
            np.zeros(z.days, dtype=bool), loss_method="none",
            notes=["No transformer meter (AS-2): no balance available; candidate for a transformer meter (FR-ZD-06)."],
        )

    supply_slots = z.supply_kwh.copy()
    missing = ~np.isfinite(supply_slots)
    if missing.any():
        supply_slots[missing] = (load.sum(axis=0) + loss_slots)[missing]
    supplied_daily = supply_slots.reshape(z.days, SLOTS).sum(axis=1)
    slot_gap = supply_slots - load.sum(axis=0) - loss_slots
    gap = supplied_daily - metered_daily - estimated_daily - loss_daily
    gap_pct = gap / np.maximum(supplied_daily, 1e-9)

    accuracy = (z.accuracy_class if z.accuracy_class else zc["meter_accuracy_share"] * 100) / 100.0
    u_meter = accuracy * supplied_daily
    u_loss = zc["loss_model_error_share"] * loss_daily * (1.0 if method == "load_flow" else 2.0)
    u = np.sqrt(u_conv**2 + u_meter**2 + u_loss**2)
    threshold = np.maximum(zc["share_of_supply"] * supplied_daily, zc["min_gap_kwh_per_day"]) + u
    over = gap > threshold

    k = int(zc["consecutive_days"])
    flagged = bool(len(over) >= k and over[-k:].all())
    result = BalanceResult(
        z.transformer_id, True, dates, supplied_daily, metered_daily, estimated_daily, loss_daily, u, gap, gap_pct,
        over, flagged=flagged, slot_gap_kwh=slot_gap, loss_method=method,
    )
    if method != "load_flow":
        result.notes.append("Network parameters or topology missing (AS-7/AS-8): technical loss compared with similar zones.")

    recent = gap_pct[-k:] if len(gap_pct) >= k else gap_pct
    if flagged and float(np.mean(recent)) > zc["large_load_share"]:
        result.priority = "large_load"

    # Gap start (FR-ZD-03): a visible change point, or present since data start.
    t, shift, tstat = change_point(gap_pct, int(zc["change_min_segment_days"]))
    if t is not None and shift >= zc["change_min_shift_share"] and tstat >= 6.0:
        result.gap_start = dates[t]
    elif flagged:
        result.gap_since_start = True

    # Hourly profile and flatness (FR-ZD-04), over the days the gap is open.
    start_idx = result.gap_start_index or 0
    window = slot_gap.reshape(z.days, SLOTS)[start_idx:]
    hourly = window.reshape(-1, 24, 2).sum(axis=2).mean(axis=0)
    result.hourly_gap_kwh = hourly
    mean = hourly.mean()
    result.flatness_cv = float(hourly.std() / mean) if mean > 0 else None
    return result
