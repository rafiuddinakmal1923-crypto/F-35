"""R0 score and reasons (SDD 5.4; FR-PS-01, FR-PS-05, FR-PS-07 to 09).

s(i) = 100 * clip(sum_k w_k * x(i,k) - sum_t p_t * tag(i,t), 0, 1)

Each input's contribution is exactly its weighted value and each tag's penalty is a negative
contribution, so the lines add up to the score: the page shows the top three plus "other",
and a "capped" line whenever clipping applies. Wording describes risk only and never labels
a premise or person as a thief (FR-PS-08).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from voltguard.detection.features import FEATURE_NAMES

TAG_TEXT = {
    "ev_charging": "Regular night-time block that matches EV charging (legitimate use)",
    "solar": "Drop in daytime use explained by rooftop solar (legitimate use)",
    "vacancy": "Near-zero use with no sign of occupancy, consistent with an empty premise (legitimate use)",
}


# When fewer than three inputs contribute, the remaining lines (to show at least three, NFR-08) say plainly
# that an aspect added nothing. True whether the data was missing or simply showed nothing unusual.
ZERO_TEXT = {
    "gap_from_similar": "No evidence from comparison with similar homes (adds 0)",
    "change_from_history": "No evidence from a drop against its own history (adds 0)",
    "night_to_day": "No evidence from night-time use (adds 0)",
    "zero_streaks": "No evidence from runs of near-zero readings (adds 0)",
    "flatness": "No evidence from a constant 24/7 load (adds 0)",
    "voltage_residual": "No evidence from this meter's voltage (adds 0)",
    "anomaly": "No evidence from the weekly profile (adds 0)",
}


@dataclass
class Reason:
    feature: str
    points: float
    text: str

    def as_dict(self) -> dict:
        return {"feature": self.feature, "contribution": round(self.points, 1), "reason_text": self.text}


@dataclass
class Score:
    score: int
    lines: list[Reason]            # top three, then "other" and "capped" when needed; they add up to score
    all_contributions: list[Reason]


def reason_text(feature: str, d: dict, sub_reasons: list[str]) -> str:
    if feature == "gap_from_similar":
        basis = " at night (daytime use is explained by solar)" if d.get("night_basis") else ""
        return f"Use is {d.get('below_similar_share', 0) * 100:.0f}% below similar {d.get('peer_type', '')} homes on this transformer{basis}"
    if feature == "change_from_history":
        when = f" from {d['own_change_day']}" if d.get("own_change_day") else " over the last two weeks"
        basis = " at night" if d.get("night_basis") else ""
        return f"Metered use{basis} fell {d.get('drop_share', 0) * 100:.0f}% compared with its own history{when}"
    if feature == "voltage_proximity":
        distance = d.get("tap_distance", 0)
        where = ("at or right next to this premise" if distance < 15
                 else f"about {distance:.0f} m from this premise")
        return (f"Neighbours on the same phase and branch show an unexplained voltage drop of {d.get('group_drop_v', 0):.1f} V; "
                f"the estimated hidden load is {where}")
    if feature == "voltage_residual":
        return f"This meter's voltage is {d.get('voltage_drop_v', 0):.1f} V lower than its metered use explains"
    if feature == "timing_match":
        return f"Its use changed {d.get('timing_days', 0)} day(s) from when the zone's energy gap opened"
    if feature == "zero_streaks":
        return f"{d.get('zero_share', 0) * 100:.0f}% of recent half-hours read almost zero, more than before"
    if feature == "night_to_day":
        return f"Night-time share of use is {d.get('night_share', 0) * 100:.0f}% against {d.get('peer_night_share', 0) * 100:.0f}% for similar homes"
    if feature == "flatness":
        return "Metered load is unusually constant across the day"
    if feature == "pattern_model":
        extra = f": {', '.join(sub_reasons)}" if sub_reasons else ""
        return f"Daily-use pattern resembles labelled theft cases in public training data{extra}"
    if feature == "anomaly":
        return f"Weekly profile is {d.get('anomaly_ratio', 1):.1f}x harder to reconstruct than a typical home's"
    if feature == "tenancy_change":
        return f"Tenancy changed on {d.get('tenancy_date', '?')}, near the gap start (supporting evidence only)"
    return TAG_TEXT.get(feature, feature)


def solar_unexplained_text(s: dict) -> str:
    verdict = (s.get("penalty") or {}).get("verdict")
    if verdict == "over_budget":
        b = s.get("budget") or {}
        kwp = s.get("capacity_kwp") or 0
        return (f"Solar penalty not applied: daytime use fell {b.get('drop_kwh', 0):.1f} kWh/day, more than a {kwp:g} kWp "
                f"system can produce (about {b.get('expected_kwh', 0):.1f} kWh/day)")
    n = s.get("night") or {}
    parts = []
    if n.get("drop_share") is not None and n["drop_share"] > 0:
        parts.append(f"night-time use still fell {n['drop_share'] * 100:.0f}% from its own history")
    if n.get("below_peers_share") is not None and n["below_peers_share"] > 0:
        parts.append(f"is {n['below_peers_share'] * 100:.0f}% below similar homes")
    if n.get("dip_v") is not None and n["dip_v"] >= 0.1:
        parts.append(f"its night-time voltage fell {n['dip_v']:.1f} V")
    detail = " and ".join(parts) if parts else "night-time evidence is strong"
    battery = " (low confidence: home battery)" if s.get("has_battery") else ""
    return f"Solar penalty not applied: solar explains the daytime drop only; {detail}{battery}"


def solar_timing_text(t: dict) -> str:
    if t.get("kind") == "before_registration":
        return f"Use dropped {t.get('days', 0)} days before the solar registration date (supporting evidence only)"
    return (f"Use dropped {t.get('days', 0)} day(s) from when the zone's energy gap opened, with no solar registration "
            f"(supporting evidence only)")


def score_premise(x: np.ndarray, tags: list[str], details: dict, sub_reasons: list[str], cfg: dict) -> Score:
    weights = cfg["weights"]
    contributions: list[Reason] = []
    other_evidence = 0.0
    for k, name in enumerate(FEATURE_NAMES):
        if name == "tenancy_change":
            continue
        value = float(weights.get(name, 0.0)) * float(x[k])
        other_evidence += value
        if value > 1e-6:
            contributions.append(Reason(name, 100 * value, reason_text(name, details, sub_reasons)))
    tenancy = 0.0
    t_idx = FEATURE_NAMES.index("tenancy_change")
    if x[t_idx] > 0 and other_evidence >= cfg["tenancy"]["gate_other_evidence"]:
        tenancy = min(float(weights.get("tenancy_change", 0.0)) * float(x[t_idx]), cfg["tenancy"]["max_contribution"])
        contributions.append(Reason("tenancy_change", 100 * tenancy, reason_text("tenancy_change", details, sub_reasons)))
    solar = details.get("solar") or {}
    pinned: list[Reason] = []
    if "solar" in tags:
        timing = solar.get("timing")
        points = float((cfg.get("solar") or {}).get("timing_points", 0.03))
        if timing and points and other_evidence >= cfg["tenancy"]["gate_other_evidence"]:
            # Supporting evidence only: counts when other evidence already reaches the gate (like tenancy).
            other_evidence += points
            contributions.append(Reason("solar_timing", 100 * points, solar_timing_text(timing)))
    penalty = 0.0
    for tag in tags:
        p = float(cfg["penalties"].get(tag, 0.0))
        if tag == "solar" and not (solar.get("penalty") or {"applies": True})["applies"]:
            # Solar explains a daytime drop only (FR-PS-10): with strong night-time evidence, or a drop larger
            # than the panels can produce, the penalty is not applied and the reason says why.
            line = Reason("solar_unexplained", 0.0, solar_unexplained_text(solar))
            contributions.append(line)
            pinned.append(line)
            continue
        if p:
            penalty += p
            contributions.append(Reason(f"tag:{tag}", -100 * p, TAG_TEXT[tag]))

    total = other_evidence + tenancy - penalty
    exact = 100 * float(np.clip(total, 0.0, 1.0))
    score = int(round(exact))
    contributions.sort(key=lambda r: -abs(r.points))
    top_raw = contributions[:3]
    for line in pinned:
        # The reason a legitimate-use penalty was not applied is always shown (it explains the score).
        if line not in top_raw:
            top_raw = top_raw[:2] + [line]
    rest_raw = [r for r in contributions if r not in top_raw]
    contributions = top_raw + rest_raw
    top = [Reason(r.feature, round(r.points, 1), r.text) for r in top_raw]
    for feature, text in ZERO_TEXT.items():
        if len(top) >= 3:
            break
        if all(r.feature != feature for r in contributions):
            top.append(Reason(feature, 0.0, text))
    rest = sum(r.points for r in contributions[3:])
    lines = list(top)
    capped = exact - 100 * total
    if abs(capped) >= 0.05:
        lines.append(Reason("capped", round(capped, 1), "Score capped at 0 or 100" if capped else ""))
    other = score - sum(r.points for r in lines)
    if contributions[3:] or abs(other) >= 0.05:
        lines.insert(len(top), Reason("other", round(other, 1), "Other evidence" if contributions[3:] else "Rounding"))
    return Score(score, lines, contributions)
