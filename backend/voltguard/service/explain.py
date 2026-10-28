"""Why a home with a legitimate explanation was not ranked high (UI brief 3.5, FR-PS-10), and the
rooftop-solar check shown on the premise page (Solar brief 4).

Returns facts, not sentences: the web app words them in English or Bahasa Melayu. Every fact comes
from the scoring run's own evidence (`premise_feature.details`) and the account events, so the box
shows exactly what the scorer saw.
"""

from __future__ import annotations

from typing import Any

LEGIT_TAGS = ("solar", "ev_charging", "vacancy")


def _round(v, digits=2):
    return None if v is None else round(float(v), digits)


def penalty_dropped(details: dict | None) -> bool:
    """The solar tag is present but solar does not explain the drop (strong night evidence or over budget)."""
    s = (details or {}).get("solar") or {}
    return bool(s.get("penalty")) and not s["penalty"].get("applies", True)


def why_cleared(tags: list[str] | None, details: dict | None, events: list[dict], flat_cv: float) -> list[dict[str, Any]]:
    tags, d = list(tags or []), dict(details or {})
    out: list[dict[str, Any]] = []
    solar = d.get("solar") or {}
    if "solar" in tags and not penalty_dropped(d):
        registered = next((str(e["event_date"]) for e in events if e["event_type"] == "solar_registration"), None)
        out.append({"kind": "solar", "facts": {
            "day_drop": _round(solar.get("day_drop")), "night_drop": _round(solar.get("night_drop")),
            "sun_corr": _round(solar.get("sun_corr")), "shape_corr": _round(solar.get("shape_corr")),
            "export": bool(solar.get("export")), "registered_on": registered,
            "night_basis": bool(d.get("night_basis"))}})
    if "ev_charging" in tags:
        out.append({"kind": "ev_charging", "facts": {"ev_night_share": _round(d.get("ev_night_share"))}})
    if "vacancy" in tags:
        out.append({"kind": "vacancy", "facts": {"intraday_cv": _round(d.get("intraday_cv"))}})
    # Metered mining: a constant 24/7 load that the meter does record. No tag (it is not a penalty):
    # it simply earns no theft evidence, because use did not drop and is not below similar homes.
    cv = d.get("intraday_cv")
    below = d.get("below_similar_share")
    drop = d.get("drop_share")
    if cv is not None and cv < flat_cv and (below is None or below <= 0) and (drop is None or drop < 0.1):
        out.append({"kind": "metered_mining", "facts": {"intraday_cv": _round(cv), "above_similar_share": _round(-(below or 0)),
                                                        "drop_share": _round(drop)}})
    return out


def solar_check(tags: list[str] | None, details: dict | None, smart: bool | None, cfg: dict) -> dict[str, Any] | None:
    """One line per solar check with its number and a mark (Solar brief 4): "pass" supports solar,
    "against" points to a hidden load, "not_seen" was checked and not found, "no_data" could not be checked.
    None when the home shows no sign of solar at all (no tag, no registration, no export)."""
    d = dict(details or {})
    s = d.get("solar") or {}
    tagged = "solar" in (tags or [])
    if not (tagged or s.get("registered") or s.get("export")):
        return None
    sc = cfg.get("solar") or {}
    interval = bool(smart) and "day_drop" in s
    checks: list[dict[str, Any]] = []

    checks.append({"check": "registration", "status": "pass" if s.get("registered") else "not_seen",
                   "values": {"date": s.get("registered_on"), "capacity_kwp": s.get("capacity_kwp"),
                              "has_battery": s.get("has_battery")}})
    checks.append({"check": "export", "status": ("pass" if s.get("export") else "not_seen") if interval else "no_data", "values": {}})

    night = s.get("night") or {}
    if interval:
        day_vs_night = "against" if night.get("strong") else ("pass" if (s.get("day_drop") or 0) >= 0.15 else "not_seen")
    else:
        day_vs_night = "no_data"
    checks.append({"check": "day_vs_night", "status": day_vs_night,
                   "values": {"day_drop": _round(s.get("day_drop")), "night_drop": _round(s.get("night_drop")),
                              "night_below_peers": _round(night.get("below_peers_share")), "window": night.get("window"),
                              "confidence": s.get("night_confidence", "normal")}})

    shape, sun, midday = s.get("shape_corr"), s.get("sun_corr"), s.get("midday_zero_share")
    if not interval or (shape is None and sun is None):
        sun_status = "no_data"
    else:
        sun_status = "pass" if ((shape or 0) >= 0.7 or (sun is not None and sun <= -0.2) or (midday or 0) >= 0.8) else "not_seen"
    checks.append({"check": "sun_shape", "status": sun_status,
                   "values": {"shape_corr": _round(shape), "sun_corr": _round(sun), "midday_zero_share": _round(midday)}})

    rebound = s.get("rain_rebound")
    checks.append({"check": "rain_rebound",
                   "status": "no_data" if rebound is None else ("pass" if rebound >= sc.get("rebound_min", 0.1) else "not_seen"),
                   "values": {"rebound": _round(rebound)}})

    budget = s.get("budget")
    checks.append({"check": "energy_budget",
                   "status": "no_data" if not budget else ("against" if s.get("over_budget") else "pass"),
                   "values": dict(budget or {}) | {"capacity_kwp": s.get("capacity_kwp")}})

    v = s.get("voltage")
    if not v:
        v_status = "no_data"
    elif v.get("supports_hidden_load"):
        v_status = "against"
    elif v.get("supports_solar"):
        v_status = "pass"
    else:
        v_status = "not_seen"
    checks.append({"check": "voltage", "status": v_status, "values": dict(v or {})})

    if s.get("timing"):
        checks.append({"check": "timing", "status": "against", "values": dict(s["timing"])})

    verdict = (s.get("penalty") or {}).get("verdict") if tagged else "not_tagged"
    return {"tagged": tagged, "verdict": verdict or "not_tagged", "checks": checks,
            "follow_up": s.get("follow_up"), "night_confidence": s.get("night_confidence", "normal"),
            "night_drop": _round(night.get("drop_share")), "night_below_peers": _round(night.get("below_peers_share")),
            "night_by": night.get("by")}
