"""Why a home with a legitimate explanation was not ranked high (UI brief 3.5, FR-PS-10).

Returns facts, not sentences: the web app words them in English or Bahasa Melayu. Every fact comes
from the scoring run's own evidence (`premise_feature.details`) and the account events, so the box
shows exactly what the scorer saw.
"""

from __future__ import annotations

from typing import Any

LEGIT_TAGS = ("solar", "ev_charging", "vacancy")


def _round(v, digits=2):
    return None if v is None else round(float(v), digits)


def why_cleared(tags: list[str] | None, details: dict | None, events: list[dict], flat_cv: float) -> list[dict[str, Any]]:
    tags, d = list(tags or []), dict(details or {})
    out: list[dict[str, Any]] = []
    solar = d.get("solar") or {}
    if "solar" in tags:
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
