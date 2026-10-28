"""Stage 3: premise features and legitimate-use tags (SDD 5.3; FR-PS-03 to 06, 09, 10).

Every feature is normalised to [0, 1] so the R0 score can add them with weights and every
contribution can be shown as a reason. `details` keeps the raw numbers for the reason text.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import date

import numpy as np

from voltguard.detection import anomaly, pattern
from voltguard.detection.balance import BalanceResult, change_point, similar_groups
from voltguard.detection.voltage import VoltageResult
from voltguard.detection.zone_input import SLOTS, ZoneInput

FEATURE_NAMES = [
    "gap_from_similar", "change_from_history", "voltage_proximity", "voltage_residual", "timing_match",
    "zero_streaks", "night_to_day", "flatness", "pattern_model", "anomaly", "tenancy_change",
]
DAY_SLOTS = np.arange(16, 34)                      # 08:00-17:00: when rooftop solar generates
NIGHT_SLOTS = np.r_[np.arange(38, 48), np.arange(0, 14)]  # 19:00-07:00: solar cannot explain a drop here
EARLY_NIGHT = np.arange(0, 12)                     # 00:00-06:00 for the night-to-day ratio
MIDDAY_SLOTS = np.arange(22, 28)                   # 11:00-14:00: reverse power flow lifts the voltage here
LATE_NIGHT = np.arange(0, 14)                      # 00:00-07:00: night window for homes with a battery, which
                                                   # covers the evening from stored solar energy


@dataclass
class FeatureSet:
    X: np.ndarray                                   # (n, len(FEATURE_NAMES))
    tags: list[list[str]]
    details: list[dict]
    confidence: list[str]
    sub_reasons: list[list[str]] = field(default_factory=list)


def _clip01(x):
    return float(np.clip(x, 0.0, 1.0))


def _drop_share(before: float, after: float) -> float:
    return float(1.0 - after / before) if before > 1e-6 else 0.0


# ----------------------------------------------------------------------------- rooftop solar (FR-PS-10, AS-9)

SOLAR_DEFAULTS = {
    "strong_night_drop": 0.25, "strong_night_below_peers": 0.30, "strong_night_dip_v": 1.0,
    "budget_factor": 1.2, "psh_per_sunshine_hour": 0.95, "psh_default": [3.5, 6.5], "rebound_min": 0.10,
    "timing_before_registration_days": 14, "timing_near_gap_days": 3, "midday_rise_v": 0.4,
}


def _phase_voltage_residual(z: ZoneInput) -> np.ndarray | None:
    """Each meter's voltage minus the median of meters on its phase (phase-blind without phase data)."""
    if not z.has_voltage:
        return None
    ph = z.phase_index()
    out = np.full_like(z.voltage, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        everyone = np.nanmedian(z.voltage, axis=0)
        for p in set(ph.tolist()):
            members = ph == p
            ref = np.nanmedian(z.voltage[members], axis=0) if (p >= 0 and members.sum() >= 3) else everyone
            out[members] = z.voltage[members] - ref
    return out


def _mean(block: np.ndarray) -> float | None:
    v = block[np.isfinite(block)]
    return float(v.mean()) if v.size else None


def peak_sun_hours(sunshine: np.ndarray | None, window: slice, sc: dict) -> tuple[float, str]:
    """Mean daily peak-sun-hours over the window: from district sunshine when loaded, otherwise the
    top of the configured default range (labelled "[peak sun hours: to confirm]")."""
    if sunshine is not None:
        s = sunshine[window]
        if s.size and np.isfinite(s).all():
            return float(s.mean() * sc["psh_per_sunshine_hour"]), "weather"
    return float(max(sc["psh_default"])), "assumed"


def _solar_checks(solar: dict, i: int, slots: np.ndarray, before: slice, after: slice, own_change: int | None,
                  zone_start: int | None, dates: list, z: ZoneInput, vres: np.ndarray | None, sc: dict, levels,
                  night: np.ndarray = NIGHT_SLOTS) -> None:
    """Energy budget, rainy-day rebound, timing vs. registration and voltage signature (Solar brief 2.1-2.4)."""
    day_before, day_after, night_before, night_after = (float(v) for v in levels)
    solar["day_drop_kwh"] = round(day_before - day_after, 2)
    solar["night_drop_kwh"] = round(night_before - night_after, 2)

    # Rainy-day rebound: daytime use on the cloudiest third of days against the sunniest third.
    # Solar homes use more from the grid on cloudy days; a bypass stays low whatever the weather.
    solar["rain_rebound"] = None
    n_after = after.stop - after.start
    if z.sunshine is not None and n_after >= 9:
        s = z.sunshine[after]
        if np.isfinite(s).all() and s.std() > 0:
            use = slots[i, after][:, DAY_SLOTS].sum(axis=1)
            order, third = np.argsort(s), max(n_after // 3, 1)
            cloudy, sunny = float(use[order[:third]].mean()), float(use[order[-third:]].mean())
            solar["rain_rebound"] = round((cloudy - sunny) / max(day_before, 1e-6), 2)

    # Energy budget: the drop cannot exceed what the registered panels can produce.
    kwp = solar.get("capacity_kwp")
    if kwp:
        psh, source = peak_sun_hours(z.sunshine, after, sc)
        expected = float(kwp) * psh
        drop = max(day_before - day_after, 0.0)
        if solar.get("has_battery"):
            drop += max(night_before - night_after, 0.0)      # a battery spends solar energy at night too
        solar["budget"] = {"expected_kwh": round(expected, 1), "drop_kwh": round(drop, 1), "psh": round(psh, 2),
                           "psh_source": source, "factor": sc["budget_factor"],
                           "excess_kwh": round(max(drop - sc["budget_factor"] * expected, 0.0), 1)}
        solar["over_budget"] = bool(drop > sc["budget_factor"] * expected)

    # Timing against the registration (supporting evidence only, never used on its own).
    if own_change is not None:
        if solar["registered"]:
            lead = (date.fromisoformat(solar["registered_on"]) - dates[own_change]).days
            if lead > sc["timing_before_registration_days"]:
                solar["timing"] = {"kind": "before_registration", "days": int(lead)}
        elif zone_start is not None and abs(own_change - zone_start) <= sc["timing_near_gap_days"]:
            solar["timing"] = {"kind": "near_gap_start", "days": int(abs(own_change - zone_start))}

    # Voltage signature: a midday rise (reverse power flow) supports solar; a night dip supports a hidden load.
    solar["voltage"] = None
    if vres is not None and np.isfinite(vres[i]).any():
        r = vres[i].reshape(z.days, SLOTS)
        mid_a, mid_b = _mean(r[after][:, MIDDAY_SLOTS]), _mean(r[before][:, MIDDAY_SLOTS])
        night_a, night_b = _mean(r[after][:, night]), _mean(r[before][:, night])
        rise = round(mid_a - mid_b, 2) if mid_a is not None and mid_b is not None else None
        dip = round(night_b - night_a, 2) if night_a is not None and night_b is not None else None
        solar["voltage"] = {"midday_rise_v": rise, "night_dip_v": dip,
                            "supports_solar": bool(rise is not None and rise >= sc["midday_rise_v"]),
                            "supports_hidden_load": bool(dip is not None and dip >= sc["strong_night_dip_v"])}


def _solar_decision(solar: dict, i: int, slots: np.ndarray, recent: slice, before: slice, peers: list[int], sc: dict,
                    night: np.ndarray = NIGHT_SLOTS) -> dict:
    """Whether the solar penalty applies (Solar brief 1). Solar can only explain a daytime drop: when the
    night-time evidence is strong, or the drop is larger than the panels can produce, it is dropped."""
    def below_peers(window: slice) -> float | None:
        if not peers or window.stop <= window.start:
            return None
        own = float(slots[i, window][:, night].sum(axis=1).mean())
        peer = float(np.median([slots[j, window][:, night].sum(axis=1).mean() for j in peers]))
        return round(1.0 - own / peer, 3) if peer > 0 else None

    below, below_before = below_peers(recent), below_peers(before)
    drop = solar.get("night_drop")
    dip = (solar.get("voltage") or {}).get("night_dip_v")
    by_drop = drop is not None and drop >= sc["strong_night_drop"]
    # Low night use against similar homes counts when it is new: a household that already used little at
    # night before the drop is frugal, and solar did not change that.
    by_peers = (below is not None and below >= sc["strong_night_below_peers"]
                and (below_before is None or below_before < sc["strong_night_below_peers"]))
    # A night-time voltage dip can come from a neighbour's tap on the same phase, so it strengthens the
    # night-time evidence but never decides on its own.
    by_dip = dip is not None and dip >= sc["strong_night_dip_v"]
    strong = bool(by_drop or by_peers)
    if solar.get("over_budget"):
        verdict = "over_budget"
    elif strong:
        # With a home battery the night window starts at midnight (the battery covers the evening) and the
        # comparison is marked low confidence rather than skipped (Solar brief 2.6).
        verdict = "night_unexplained"
    else:
        verdict = "explained"
    solar["night"] = {"drop_share": None if drop is None else round(float(drop), 3), "below_peers_share": below,
                      "below_peers_before_share": below_before,
                      "dip_v": dip, "dip_supports": bool(by_dip), "strong": strong,
                      "by": "drop" if by_drop else ("peers" if by_peers else None),
                      "window": "00:00-07:00" if night is LATE_NIGHT else "19:00-07:00"}
    return {"applies": verdict == "explained", "verdict": verdict,
            "confidence": "low" if solar.get("has_battery") else "normal"}


# ----------------------------------------------------------------------------- features

def build_features(z: ZoneInput, bal: BalanceResult, volt: VoltageResult, filled: np.ndarray,
                   daily_est: np.ndarray, cfg: dict) -> FeatureSet:
    fc, vc = cfg["features"], cfg["voltage"]
    n, days = z.n, z.days
    slots = filled.reshape(n, days, SLOTS)
    daily = np.where(z.smart[:, None], slots.sum(axis=2), daily_est)
    recent_days = int(fc["recent_days"])
    history_days = int(fc["history_weeks"]) * 7
    recent = slice(days - recent_days, days)
    base = slice(max(0, days - recent_days - history_days), days - recent_days)
    zone_start = bal.gap_start_index
    groups = similar_groups(z)
    types = np.array(z.premises["premise_type"].to_list())
    dates = z.day_dates()
    run_date = dates[-1]

    pm = pattern.load()
    ae = anomaly.load()
    errors = np.full(n, np.nan)
    if ae is not None:
        vectors, idx = [], []
        for i in np.where(z.smart)[0]:
            v = anomaly.week_vector(filled[i])
            if v is not None:
                vectors.append(v)
                idx.append(i)
        if vectors:
            errors[idx] = ae.error(np.array(vectors))
    median_error = float(np.nanmedian(errors)) if np.isfinite(errors).any() else np.nan

    signal = volt.signal_v if volt.available else np.full(n, np.nan)
    drops = np.clip(-np.nan_to_num(signal, nan=0.0), 0, None)
    zone_max_drop = max(float(drops.max()) if n else 0.0, 2 * vc["min_drop_v"])
    max_group_drop = max(float(np.max(volt.group_drop_v)) if n else 0.0, 1e-9)

    peer_recent = dict(groups)
    sc = {**SOLAR_DEFAULTS, **(cfg.get("solar") or {})}
    vres = _phase_voltage_residual(z)

    X = np.zeros((n, len(FEATURE_NAMES)))
    tags, details, confidence, subs = [], [], [], []
    for i in range(n):
        d: dict = {}
        tag: list[str] = []
        row_daily = daily[i]
        peers = [j for j in peer_recent.get(types[i], []) if j != i]

        # Legitimate-use checks first: the solar check changes how a drop is measured (FR-PS-10).
        own_t, own_shift, own_tstat = change_point(row_daily, 3) if z.smart[i] else (None, 0.0, 0.0)
        own_change = own_t if (own_t is not None and own_shift < 0 and own_tstat <= -6.0) else None
        before = slice(max(0, (own_change or days - recent_days) - history_days), own_change or days - recent_days)
        after = slice(own_change or days - recent_days, days)
        reg = z.solar_registrations.get(i)
        solar = {"registered": reg is not None and reg["date"] <= run_date}
        if solar["registered"]:
            solar["registered_on"] = reg["date"].isoformat()
            solar["capacity_kwp"] = reg.get("capacity_kwp")
            solar["has_battery"] = bool(reg.get("has_battery"))
        night = LATE_NIGHT if solar.get("has_battery") else NIGHT_SLOTS
        if z.smart[i]:
            day_before = slots[i, before][:, DAY_SLOTS].sum(axis=1).mean()
            day_after = slots[i, after][:, DAY_SLOTS].sum(axis=1).mean()
            night_before = slots[i, before][:, night].sum(axis=1).mean()
            night_after = slots[i, after][:, night].sum(axis=1).mean()
            solar["day_drop"] = _drop_share(day_before, day_after)
            solar["night_drop"] = _drop_share(night_before, night_after)
            raw = z.kwh[i]
            solar["export"] = bool((np.nan_to_num(raw) < -0.01).reshape(days, SLOTS).any(axis=1)[recent].mean() >= 0.2)
            solar["sun_corr"] = None
            if z.sunshine is not None and (after.stop - after.start) >= 7:
                s = z.sunshine[after]
                u = slots[i, after][:, DAY_SLOTS].sum(axis=1)
                if np.isfinite(s).all() and s.std() > 0 and u.std() > 0:
                    solar["sun_corr"] = round(float(np.corrcoef(s, u)[0, 1]), 2)
            # Shape of the drop through the day: solar follows the sun's bell; a bypassed appliance does not.
            drop_profile = slots[i, before].mean(axis=0) - slots[i, after].mean(axis=0)
            daylight = np.clip(np.sin((np.arange(SLOTS) / 2.0 - 7) / 12 * np.pi), 0, None)
            solar["shape_corr"] = (round(float(np.corrcoef(drop_profile, daylight)[0, 1]), 2)
                                   if drop_profile.std() > 0 else None)
            # Midday hours (10:00-15:00) reading almost zero after the change: a system large enough
            # to cover all daytime use.
            core = slots[i, after][:, 20:30]
            solar["midday_zero_share"] = round(float((core < fc["zero_kwh"]).mean()), 2) if core.size else 0.0
            daytime_only = solar["day_drop"] >= 0.25 and solar["night_drop"] <= 0.12
            # Sunshine correlation needs an unsaturated drop; a system that zeroes daytime use every
            # day leaves no day-to-day variation, so a sun-shaped drop or a zeroed midday also counts.
            sunny = ((solar["sun_corr"] is not None and solar["sun_corr"] <= -0.2)
                     or (solar["shape_corr"] or 0) >= 0.7 or solar["midday_zero_share"] >= 0.8)
            _solar_checks(solar, i, slots, before, after, own_change, zone_start, dates, z, vres, sc,
                          (day_before, day_after, night_before, night_after), night)
            # Cloudy days giving back daytime use is solar's own signature (a bypass stays low whatever the weather).
            sunny = sunny or (solar["rain_rebound"] is not None and solar["rain_rebound"] >= sc["rebound_min"])
            if solar["export"] or (solar["registered"] and solar["day_drop"] >= 0.15) or (daytime_only and sunny):
                tag.append("solar")
            if solar["export"] and not solar["registered"]:
                solar["follow_up"] = "unregistered_export"     # admin note, never scored as theft
            if solar.get("has_battery"):
                solar["night_confidence"] = "low"              # a battery can move solar energy into the evening
        d["solar"] = solar
        # A drop larger than the system can produce is not explained by solar: judge the whole day.
        night_only = "solar" in tag and not solar.get("over_budget")
        d["night_basis"] = night_only

        # 1. Change from own history (night-time only when the drop is explained by solar).
        if z.smart[i]:
            cols = night if night_only else slice(None)
            b = slots[i, before][:, cols].sum(axis=1).mean()
            a = slots[i, after][:, cols].sum(axis=1).mean()
            drop = _drop_share(b, a)
        else:
            months = sorted(z.monthly.get(i, {}))
            drop = _drop_share(z.monthly[i][months[-2]], z.monthly[i][months[-1]]) if len(months) >= 2 else 0.0
        d["drop_share"] = round(drop, 3)
        d["own_change_day"] = dates[own_change].isoformat() if own_change is not None else None
        X[i, 1] = _clip01((drop - 0.10) / 0.5)

        # 2. Gap from similar homes (level evidence, works for long-running theft).
        if peers:
            if night_only:
                own = slots[i, recent][:, night].sum(axis=1).mean()
                peer_level = float(np.median([slots[j, recent][:, night].sum(axis=1).mean() for j in peers]))
            else:
                own = row_daily[recent].mean()
                peer_level = float(np.median(daily[peers][:, recent].mean(axis=1)))
            low = 1.0 - own / peer_level if peer_level > 0 else 0.0
            d["below_similar_share"] = round(float(low), 3)
            d["peer_type"] = types[i]
            X[i, 0] = _clip01((low - 0.20) / 0.5)

        if "solar" in tag:
            solar["penalty"] = _solar_decision(solar, i, slots, recent, before, peers, sc, night)

        if z.smart[i]:
            recent_slots = slots[i, recent]
            hourly = recent_slots.reshape(-1, 24, 2).sum(axis=2).mean(axis=0)
            cv = float(hourly.std() / hourly.mean()) if hourly.mean() > 0 else 1.0
            d["intraday_cv"] = round(cv, 3)
            X[i, 7] = _clip01((0.5 - cv) / 0.4)

            # With solar, daytime zeros and a shifted day/night split are expected: judge night-time use only.
            cols = night if night_only else slice(None)
            zero_now = float((recent_slots[:, cols] < fc["zero_kwh"]).mean())
            zero_before = float((slots[i, base][:, cols] < fc["zero_kwh"]).mean()) if base.stop > base.start else 0.0
            d["zero_share"] = round(zero_now, 3)
            X[i, 5] = _clip01((zero_now - zero_before) * 3)

            night_share = recent_slots[:, EARLY_NIGHT].sum() / max(recent_slots.sum(), 1e-9)
            peer_night = [slots[j, recent][:, EARLY_NIGHT].sum() / max(slots[j, recent].sum(), 1e-9) for j in peers if z.smart[j]]
            if peer_night and not night_only:
                med = float(np.median(peer_night))
                dev = abs(night_share - med) / max(med, 1e-6)
                d["night_share"], d["peer_night_share"] = round(float(night_share), 3), round(med, 3)
                X[i, 6] = _clip01((dev - 0.2) / 0.6)

            # Pattern model and anomaly score (night-time totals for solar homes).
            series = slots[i][:, night].sum(axis=1) if night_only else row_daily
            if night_only:
                peer_level_all = float(np.median([slots[j, recent][:, night].sum(axis=1).mean() for j in peers])) if peers else None
            else:
                peer_level_all = float(np.median(daily[peers][:, recent].mean(axis=1))) if peers else None
            fx = pattern.window_features(series, peer_level_all)
            X[i, 8] = float(pm.predict(fx[None, :])[0])
            subs.append(pm.sub_reasons(fx) if X[i, 8] >= 0.5 else [])
            if X[i, 8] >= 0.5:
                d["pattern_shap"] = pm.sub_reason_values(fx)
            if night_only:
                pass  # the weekly-shape autoencoder would flag the new solar shape itself
            elif np.isfinite(errors[i]) and np.isfinite(median_error) and median_error > 0:
                d["anomaly_ratio"] = round(float(errors[i] / median_error), 2)
                X[i, 9] = _clip01((errors[i] / median_error - 1.0) / 3.0)
        else:
            subs.append([])

        # 5. Timing match: only when a change is visible in both the zone and the premise. For a solar home
        # judged at night the installation date is not evidence: only a night-time change counts.
        timing_change = own_change
        if night_only:
            nt, nshift, ntstat = change_point(slots[i][:, night].sum(axis=1), 3)
            timing_change = nt if (nt is not None and nshift < 0 and ntstat <= -6.0) else None
            d["night_change_day"] = dates[timing_change].isoformat() if timing_change is not None else None
        if zone_start is not None and timing_change is not None:
            gap_days = abs(timing_change - zone_start)
            d["timing_days"] = int(gap_days)
            X[i, 4] = float(np.exp(-gap_days / fc["timing_tau_days"]))

        # Tenancy change near the gap start (supporting evidence only; capped in scoring, FR-PS-09).
        anchor = zone_start if zone_start is not None else own_change
        for idx, kind, when in z.events:
            if idx != i or kind not in ("change_of_tenancy", "holder_change"):
                continue
            offset = (when - dates[0]).days
            if anchor is None or abs(offset - anchor) <= 14:
                X[i, 10] = 1.0
                d["tenancy_date"] = when.isoformat()

        # Voltage evidence (Stage 2).
        if volt.available and np.isfinite(signal[i]) and drops[i] >= vc["min_drop_v"]:
            d["voltage_drop_v"] = round(float(drops[i]), 2)
            X[i, 3] = _clip01(drops[i] / zone_max_drop)
        if volt.available and np.isfinite(volt.tap_distance_m[i]) and volt.group_drop_v[i] >= vc["min_drop_v"]:
            d["tap_distance"] = round(float(volt.tap_distance_m[i]), 1)
            d["group_drop_v"] = round(float(volt.group_drop_v[i]), 2)
            X[i, 2] = float(np.exp(-volt.tap_distance_m[i] / vc["proximity_scale_m"]) * volt.group_drop_v[i] / max_group_drop)

        # Remaining legitimate-use tags.
        if z.smart[i]:
            # 20:00-06:00 in kW; an EV is a regular high block of 2 hours or more on most nights.
            night_kw = np.concatenate([slots[i, recent][:, 40:], slots[i, recent][:, :12]], axis=1) * 2.0
            baseline_kw = np.median(night_kw)
            rolling = np.lib.stride_tricks.sliding_window_view(night_kw, 4, axis=1).mean(axis=2)
            ev_nights = float(((rolling - baseline_kw).max(axis=1) >= 2.5).mean())
            d["ev_night_share"] = round(ev_nights, 2)
            if ev_nights >= 0.4:
                tag.append("ev_charging")
            if row_daily[recent].mean() < 0.8 and (base.stop <= base.start or row_daily[base].mean() < 1.2) and d.get("intraday_cv", 1) < 0.6:
                tag.append("vacancy")

        if not z.smart[i] or not bal.balance_available or (volt.available and volt.confidence == "low") or not volt.available:
            confidence.append("low")
        else:
            confidence.append("high")
        tags.append(tag)
        details.append(d)
    return FeatureSet(X, tags, details, confidence, subs)
