"""Zone and premise views (SDD 7; FR-UI-01-04, FR-PS-07, FR-UI-03 masking).

No endpoint here returns customer names, addresses or premise coordinates, except the premise
view's `contact` block, which comes only from vg_case_contact(): an open case, for its assigned
analyst, a supervisor of its region and its assigned team's inspectors.
"""

from __future__ import annotations

from datetime import date
from statistics import median

from fastapi import APIRouter, Depends, Query

from voltguard import db
from voltguard.service import explain, settings, value
from voltguard.api.deps import connection, forbidden, not_found, require
from voltguard.db import Caller

router = APIRouter(tags=["zones"])


def latest_run_date(conn, on: date | None = None) -> date | None:
    row = conn.execute("SELECT max(run_date) AS d FROM zone_run" + (" WHERE run_date <= %s" if on else ""),
                       (on,) if on else ()).fetchone()
    return row["d"] if row else None


@router.get("/zones")
def zones(date_: date | None = Query(None, alias="date"), district: str | None = None, flagged_only: bool = False,
          c: Caller = Depends(require("manager", "analyst", "supervisor")), conn=Depends(connection)):
    """Ranked leaking zones for the caller's region (FR-UI-01, FR-UI-04): zone-level figures only."""
    run_date = latest_run_date(conn, date_)
    if run_date is None:
        return {"run_date": None, "zones": [], "districts": []}
    rows = conn.execute(
        """SELECT z.transformer_id, z.region, z.district, z.flagged, z.priority, z.balance_available, z.gap_kwh_recent,
                  z.gap_pct_recent, z.uncertainty_kwh_recent, z.flatness_cv, z.gap_start, z.gap_since_start, z.n_premises,
                  z.scored, t.lat, t.lon,
                  (SELECT count(*) FROM inspection_case ic WHERE ic.transformer_id = z.transformer_id AND ic.status <> 'closed') AS open_cases
           FROM zone_run z JOIN transformer t USING (transformer_id)
           WHERE z.run_date = %s AND (%s::text IS NULL OR z.district = %s) AND (NOT %s OR z.flagged)
           ORDER BY z.flagged DESC, z.balance_available, z.gap_pct_recent DESC NULLS LAST""",
        (run_date, district, district, flagged_only)).fetchall()
    districts = [r["district"] for r in conn.execute("SELECT DISTINCT district FROM zone_run WHERE run_date = %s ORDER BY 1", (run_date,))]
    totals = {"zones": len(rows), "flagged": sum(r["flagged"] for r in rows),
              "no_balance": sum(not r["balance_available"] for r in rows),
              "gap_kwh_per_day": round(sum(r["gap_kwh_recent"] or 0 for r in rows if r["flagged"]), 1)}
    # 14-day trend of the region's unexplained energy (flagged zones) for the overview's sparklines.
    trend = conn.execute(
        """SELECT b.date, round(sum(b.gap_kwh)::numeric, 1) AS gap_kwh, count(*) FILTER (WHERE b.flagged) AS flagged
           FROM zone_daily_balance b JOIN transformer t USING (transformer_id)
           WHERE b.balance_available AND b.date > %s::date - 14 AND b.date <= %s AND (%s::text IS NULL OR t.district = %s)
           GROUP BY b.date ORDER BY b.date""", (run_date, run_date, district, district)).fetchall()
    # Per-zone 14-day gap line for the leaderboard sparklines (zone level only).
    spark: dict[str, list[float | None]] = {}
    for r in conn.execute(
            """SELECT transformer_id, date, gap_kwh FROM zone_daily_balance
               WHERE balance_available AND date > %s::date - 14 AND date <= %s AND transformer_id = ANY(%s) ORDER BY date""",
            (run_date, run_date, [r["transformer_id"] for r in rows])).fetchall():
        spark.setdefault(r["transformer_id"], []).append(round(r["gap_kwh"], 1) if r["gap_kwh"] is not None else None)
    rate = value.tariff_info()
    for r in rows:
        r["spark"] = spark.get(r["transformer_id"], [])
        r["value"] = value.zone_value(r, rate["rm_per_kwh"])
    totals["value"] = value.totals([r["value"] for r in rows], rate["rm_per_kwh"])
    # Model-ranked vs random-sample hit rate on the caller's region's outcomes (training_label runs as the caller).
    hits = {h["kind"]: h for h in conn.execute(
        """SELECT CASE WHEN origin = 'random_sample' THEN 'random_sample' ELSE 'model_ranked' END AS kind,
                  count(*) AS inspections, sum(is_theft::int) AS confirmed FROM training_label GROUP BY 1""").fetchall()}
    totals["hit_rates"] = {k: {"inspections": h["inspections"], "confirmed_theft": h["confirmed"],
                               "hit_rate": round(h["confirmed"] / h["inspections"], 3) if h["inspections"] else None}
                           for k, h in hits.items()}
    totals["open_cases"] = sum(int(r["open_cases"] or 0) for r in rows)
    return {"run_date": run_date, "zones": rows, "districts": districts, "totals": totals, "tariff": rate,
            "trend": [{"date": r["date"], "gap_kwh": float(r["gap_kwh"]), "flagged": r["flagged"]} for r in trend]}


def _zone(conn, tx: str, run_date: date | None) -> dict:
    zone = conn.execute("SELECT * FROM zone_run WHERE transformer_id = %s AND run_date = %s", (tx, run_date)).fetchone()
    if not zone:
        raise not_found("Zone not found in your region")
    return zone


@router.get("/zones/{transformer_id}/balance")
def zone_balance(transformer_id: str, from_: date | None = Query(None, alias="from"), to: date | None = None,
                 c: Caller = Depends(require("manager", "analyst", "supervisor")), conn=Depends(connection)):
    """Daily energy balance and hourly gap profile (FR-ZD-01-05, FR-UI-02)."""
    zone = _zone(conn, transformer_id, latest_run_date(conn))
    days = conn.execute(
        """SELECT date, supplied_kwh, metered_kwh, estimated_kwh, tech_loss_kwh, uncertainty_kwh, gap_kwh, gap_pct, over_threshold
           FROM zone_daily_balance WHERE transformer_id = %s AND (%s::date IS NULL OR date >= %s) AND (%s::date IS NULL OR date <= %s)
           ORDER BY date""", (transformer_id, from_, from_, to, to)).fetchall()
    rate = value.tariff_info()
    return {"zone": {k: zone[k] for k in ("transformer_id", "district", "region", "flagged", "priority", "balance_available", "gap_start",
                                          "gap_since_start", "flatness_cv", "loss_method", "notes", "gap_pct_recent", "gap_kwh_recent",
                                          "uncertainty_kwh_recent", "n_premises")},
            "hourly_gap_kwh": zone["hourly_gap_kwh"], "days": days, "value": value.zone_value(zone, rate["rm_per_kwh"]), "tariff": rate,
            "flat_cv": settings.thresholds(conn)["zone"]["flat_cv"]}


@router.get("/zones/{transformer_id}/suspects")
def zone_suspects(transformer_id: str, limit: int = Query(50, le=500), c: Caller = Depends(require("analyst", "supervisor")),
                  conn=Depends(connection)):
    """Ranked premises with scores, tags and top reasons (FR-PS-01, FR-PS-07). Pseudonymised IDs only."""
    run_date = latest_run_date(conn)
    zone = _zone(conn, transformer_id, run_date)
    rows = conn.execute(
        """SELECT s.premise_id, s.score, s.rank, s.confidence, s.tags, s.smart, p.premise_type, p.phase, p.feeder_branch, p.street_seq,
                  ic.case_id AS open_case_id, ic.status AS open_case_status
           FROM premise_score s JOIN premise p USING (premise_id)
           LEFT JOIN inspection_case ic ON ic.premise_id = s.premise_id AND ic.status <> 'closed'
           WHERE s.transformer_id = %s AND s.run_date = %s ORDER BY s.rank LIMIT %s""",
        (transformer_id, run_date, limit)).fetchall()
    reasons = conn.execute("SELECT premise_id, rank, feature, contribution, reason_text FROM score_reason "
                           "WHERE run_date = %s AND premise_id = ANY(%s) ORDER BY premise_id, rank",
                           (run_date, [r["premise_id"] for r in rows])).fetchall()
    by_premise: dict[str, list] = {}
    for r in reasons:
        by_premise.setdefault(r["premise_id"], []).append({k: r[k] for k in ("feature", "contribution", "reason_text")})
    for r in rows:
        r["reasons"] = by_premise.get(r["premise_id"], [])
        # "Solar with unexplained night use": the solar tag is there but its penalty was not applied (FR-PS-10).
        r["solar_unexplained"] = any(x["feature"] == "solar_unexplained" for x in r["reasons"])
    db.audit(conn, c.user_id, "zone.suspects.view", f"zone:{transformer_id}", {"run_date": str(run_date)})
    top_k = max(1, -(-zone["n_premises"] * 5 // 100))
    return {"transformer_id": transformer_id, "run_date": run_date, "flagged": zone["flagged"], "balance_available": zone["balance_available"],
            "top_k": top_k, "suspects": rows}


@router.get("/zones/{transformer_id}/cleared")
def zone_cleared(transformer_id: str, c: Caller = Depends(require("analyst", "supervisor")), conn=Depends(connection)):
    """'Cleared as legitimate': homes whose drop or high use has a legitimate explanation (rooftop solar,
    EV charging, metered mining, vacancy), each with the facts behind it (FR-PS-05, FR-PS-10).
    Pseudonymised IDs only, like the suspect list."""
    run_date = latest_run_date(conn)
    _zone(conn, transformer_id, run_date)
    cfg = settings.thresholds(conn)
    rows = conn.execute(
        """SELECT s.premise_id, s.score, s.rank, s.tags, s.smart, f.details
           FROM premise_score s JOIN premise_feature f ON f.premise_id = s.premise_id AND f.run_date = s.run_date
           WHERE s.transformer_id = %s AND s.run_date = %s ORDER BY s.rank""", (transformer_id, run_date)).fetchall()
    regs = {r["premise_id"]: r for r in conn.execute(
        """SELECT e.premise_id, e.event_type, e.event_date FROM account_event e JOIN premise p USING (premise_id)
           WHERE p.transformer_id = %s AND e.event_type = 'solar_registration'""", (transformer_id,)).fetchall()}
    out = []
    for r in rows:
        events = [regs[r["premise_id"]]] if r["premise_id"] in regs else []
        items = explain.why_cleared(r["tags"], r["details"], events, cfg["zone"]["flat_cv"])
        if items:
            check = explain.solar_check(r["tags"], r["details"], r["smart"], cfg) if "solar" in (r["tags"] or []) else None
            out.append({"premise_id": r["premise_id"], "rank": r["rank"], "score": r["score"], "items": items,
                        "follow_up": (check or {}).get("follow_up")})
    db.audit(conn, c.user_id, "zone.cleared.view", f"zone:{transformer_id}", {"run_date": str(run_date)})
    return {"transformer_id": transformer_id, "run_date": run_date, "cleared": out}


@router.get("/zones/{transformer_id}/voltage")
def zone_voltage(transformer_id: str, c: Caller = Depends(require("analyst", "supervisor")), conn=Depends(connection)):
    """Voltage residual per premise by phase and branch: the neighbour voltage strip (FR-PS-02)."""
    zone = _zone(conn, transformer_id, latest_run_date(conn))
    voltage = zone["voltage"] or {"available": False, "method": "none", "groups": [], "notes": ["No voltage result for this zone"]}
    # Groups whose fitted drop is below this are noise: the UI marks a tap position only above it.
    min_drop_v = settings.thresholds(conn)["voltage"]["min_drop_v"]
    return {"transformer_id": transformer_id, "min_drop_v": min_drop_v, **voltage}


def _usage(conn, premise: dict, days: int = 60) -> dict:
    """Daily kWh of this premise against the median of similar homes on the same transformer."""
    rows = conn.execute(
        """SELECT m.premise_id, (r.ts AT TIME ZONE 'Asia/Kuala_Lumpur')::date AS day, sum(r.kwh) AS kwh
           FROM meter_reading r JOIN meter m USING (meter_id) JOIN premise p ON p.premise_id = m.premise_id
           WHERE p.transformer_id = %s AND p.premise_type = %s
             AND r.ts >= date_trunc('day', (SELECT max(ts) FROM meter_reading) AT TIME ZONE 'Asia/Kuala_Lumpur'
                                         - make_interval(days => %s)) AT TIME ZONE 'Asia/Kuala_Lumpur'
           GROUP BY 1, 2""", (premise["transformer_id"], premise["premise_type"], days)).fetchall()
    own: dict[date, float] = {}
    peers: dict[date, list[float]] = {}
    for r in rows:
        if r["premise_id"] == premise["premise_id"]:
            own[r["day"]] = round(r["kwh"], 2)
        else:
            peers.setdefault(r["day"], []).append(r["kwh"])
    series = [{"date": d, "kwh": own.get(d), "similar_median_kwh": round(median(v), 2)} for d, v in sorted(peers.items())]
    # Monthly-read (conventional) meters have no daily readings: the UI says so instead of an empty line.
    return {"premise_type": premise["premise_type"], "days": series, "interval_data": bool(own)}


@router.get("/premises/{premise_id}")
def premise_view(premise_id: str, c: Caller = Depends(require("analyst", "supervisor", "inspector")), conn=Depends(connection)):
    """Reasons, usage vs similar homes, neighbour voltage and account context (FR-UI-03)."""
    premise = conn.execute("SELECT premise_id, transformer_id, region, feeder_branch, phase, distance_m, street_seq, premise_type, tariff "
                           "FROM premise WHERE premise_id = %s", (premise_id,)).fetchone()
    if not premise:
        raise not_found("Premise not found in your region")
    case = conn.execute("SELECT case_id, status, origin, assigned_analyst, assigned_team FROM inspection_case "
                        "WHERE premise_id = %s AND status <> 'closed'", (premise_id,)).fetchone()
    if c.role == "inspector" and not case:
        raise forbidden("Inspectors see only premises with a case assigned to their team")
    run_date = latest_run_date(conn)
    score = conn.execute("SELECT score, rank, confidence, tags, model_version, smart FROM premise_score WHERE premise_id = %s AND run_date = %s",
                         (premise_id, run_date)).fetchone()
    reasons = conn.execute("SELECT feature, contribution, reason_text FROM score_reason WHERE premise_id = %s AND run_date = %s ORDER BY rank",
                           (premise_id, run_date)).fetchall()
    features = conn.execute("SELECT features, details, tags FROM premise_feature WHERE premise_id = %s AND run_date = %s",
                            (premise_id, run_date)).fetchone()
    history = conn.execute("SELECT run_date, score, rank FROM premise_score WHERE premise_id = %s ORDER BY run_date", (premise_id,)).fetchall()
    events = conn.execute("SELECT event_type, event_date FROM account_event WHERE premise_id = %s ORDER BY event_date", (premise_id,)).fetchall()
    zone = conn.execute("SELECT voltage, flagged, gap_start, gap_since_start FROM zone_run WHERE transformer_id = %s AND run_date = %s",
                        (premise["transformer_id"], run_date)).fetchone()
    neighbours = None
    if zone and zone["voltage"] and zone["voltage"].get("groups"):
        neighbours = next((g for g in zone["voltage"]["groups"] if premise_id in g.get("premises", [])), None)
    contact = None
    case_events = []
    if case:
        row = conn.execute("SELECT * FROM vg_case_contact(%s)", (case["case_id"],)).fetchone()
        contact = dict(row) if row else None
        # For the evidence timeline: what happened and when (no actors, no notes).
        case_events = conn.execute("SELECT event_type, ts FROM case_event WHERE case_id = %s ORDER BY ts", (case["case_id"],)).fetchall()
    cfg = settings.thresholds(conn)
    db.audit(conn, c.user_id, "premise.view", f"premise:{premise_id}", {"case_id": case["case_id"] if case else None,
                                                                        "personal_details_shown": contact is not None})
    return {
        "premise": premise, "score": score, "reasons": reasons,
        "features": features["features"] if features else None, "details": features["details"] if features else None,
        "score_history": history, "account_events": events, "usage": _usage(conn, premise),
        "neighbour_voltage": neighbours, "voltage_min_drop_v": cfg["voltage"]["min_drop_v"], "zone": {"flagged": zone["flagged"], "gap_start": zone["gap_start"],
                                                  "gap_since_start": zone["gap_since_start"]} if zone else None,
        "case": case, "contact": contact, "case_events": case_events,
        "why_cleared": explain.why_cleared(score["tags"] if score else (features["tags"] if features else []),
                                           features["details"] if features else None, events, cfg["zone"]["flat_cv"]),
        "solar_check": explain.solar_check(score["tags"] if score else (features["tags"] if features else []),
                                           features["details"] if features else None, score["smart"] if score else None, cfg),
        "masked": contact is None,
        "masking_note": None if contact else "Personal details and exact location appear only on an open case, for its assigned analyst, "
                                              "the supervisor and the assigned inspector.",
    }
