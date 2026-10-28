"""Weekly manager summary (SDD 9.2 manager view, FR-ML-02 hit rates): one report per region and week.

This module gathers the figures; `digest_render` turns them into rule-based sentences, charts, HTML
and the PDF (English or Bahasa Melayu). Zone-level and case-level counts only, never premise IDs or
personal details, so the report is safe for the dashboard, the PDF and a Telegram message alike.
Two windows, both stated on the page:
- energy: the last 7 days of meter data against the 7 days before (data arrive daily, not live);
- work: the last 7 calendar days of cases, visits, reports and alerts.
Runs on the caller's connection, so row-level security limits it to the caller's region.
"""

from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta, timezone

import psycopg
from psycopg.types.json import Jsonb

from voltguard import config, db
from voltguard.db import Caller
from voltguard.service import settings

log = logging.getLogger("voltguard.digest")
MYT = timezone(timedelta(hours=8), "MYT")          # Malaysia has no daylight saving
OUTCOMES = ("confirmed_theft", "false_alarm", "inconclusive", "no_access")
STATUSES = ("new", "assigned", "visited", "reporting", "closed")


def _change(now: float | None, before: float | None) -> float | None:
    if not before:
        return None
    return round((now or 0) / before * 100 - 100, 1)


def _avg(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """95% Wilson score interval for a proportion, as fractions; None without observations."""
    if not n:
        return None
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def tariff() -> dict:
    t = config.load_yaml("tariffs.yaml") or {}
    rate = t.get("rm_per_kwh")
    try:
        rate = float(rate) if rate not in (None, "") else None
    except (TypeError, ValueError):
        rate = None
    return {"rm_per_kwh": rate if rate and rate > 0 else None, "source": t.get("source") or None}


def _flagged_at(rows: list[dict], k: int) -> bool:
    """Flag rule on stored daily results: over the threshold for the last k days in a row."""
    over = [bool(r["over_threshold"]) for r in rows]
    return len(over) >= k and all(over[-k:])


def build(conn: psycopg.Connection, caller: Caller, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    week_ago, two_weeks_ago = now - timedelta(days=7), now - timedelta(days=14)
    cfg = settings.thresholds(conn)
    zc, cc = cfg["zone"], cfg["cases"]
    k = int(zc["consecutive_days"])
    myt = now.astimezone(MYT)
    iso = myt.isocalendar()
    base = {"region": caller.region, "generated_at": now.isoformat(), "generated_myt": myt.isoformat(timespec="minutes"),
            "report_id": f"VG-WK-{caller.region}-{iso.year}-W{iso.week:02d}"}
    last = conn.execute("SELECT max(date) AS d FROM zone_daily_balance").fetchone()["d"]
    if last is None:
        return {**base, "empty": True, "message": "No detection results yet."}

    run = conn.execute("SELECT run_date, model_version, data_sources FROM detection_run WHERE status = 'done' "
                       "ORDER BY run_id DESC LIMIT 1").fetchone() or {}
    sources = (run.get("data_sources") or {}) if run else {}
    simulated = sources.get("meter_reading", "simulated") == "simulated"

    # Energy: daily rows per zone for the two meter weeks (plus k days so last week's flag state is known).
    rows = conn.execute(
        """SELECT b.transformer_id, t.district, b.date, b.gap_kwh, b.gap_pct, b.uncertainty_kwh, b.supplied_kwh,
                  b.over_threshold, b.balance_available
           FROM zone_daily_balance b JOIN transformer t USING (transformer_id)
           WHERE b.date > %s::date - %s ORDER BY b.transformer_id, b.date""", (last, 14 + k)).fetchall()
    by_zone: dict[str, list[dict]] = {}
    for r in rows:
        by_zone.setdefault(r["transformer_id"], []).append(r)
    week_start = last - timedelta(days=6)
    prev_start, prev_end = last - timedelta(days=13), last - timedelta(days=7)

    daily: dict[date, dict] = {}
    for r in rows:
        if not r["balance_available"] or r["date"] < prev_start:
            continue
        d = daily.setdefault(r["date"], {"gap": 0.0, "u2": 0.0})
        d["gap"] += float(r["gap_kwh"] or 0)
        d["u2"] += float(r["uncertainty_kwh"] or 0) ** 2
    daily_gap = [{"date": d.isoformat(), "gap_kwh": round(v["gap"]), "margin_kwh": round(math.sqrt(v["u2"]))}
                 for d, v in sorted(daily.items())]
    this_week = [p["gap_kwh"] for p in daily_gap if p["date"] >= week_start.isoformat()]
    prev_week = [p["gap_kwh"] for p in daily_gap if p["date"] <= prev_end.isoformat()]
    avg_now, avg_before = _avg(this_week), _avg(prev_week)
    margin_now = _avg([p["margin_kwh"] for p in daily_gap if p["date"] >= week_start.isoformat()])

    latest = {z["transformer_id"]: z for z in conn.execute(
        """SELECT transformer_id, district, balance_available, flagged, priority, gap_start, gap_since_start, flatness_cv
           FROM zone_run WHERE run_date = (SELECT max(run_date) FROM zone_run)""").fetchall()}
    open_cases = {r["transformer_id"]: r["n"] for r in conn.execute(
        "SELECT transformer_id, count(*) AS n FROM inspection_case WHERE status <> 'closed' GROUP BY transformer_id").fetchall()}
    waiting = {r["transformer_id"]: r["n"] for r in conn.execute(
        """SELECT p.transformer_id, count(*) AS n FROM premise_score s JOIN premise p USING (premise_id)
           WHERE s.run_date = (SELECT max(run_date) FROM premise_score) AND s.rank <= %s AND s.score >= %s
             AND NOT EXISTS (SELECT 1 FROM inspection_case c WHERE c.premise_id = s.premise_id AND c.status <> 'closed')
           GROUP BY p.transformer_id""", (cc["max_cases_per_zone"], cc["case_threshold"])).fetchall()}

    zones, no_balance, flagged_prev = [], [], 0
    for tx, zrows in sorted(by_zone.items()):
        info = latest.get(tx, {})
        if not info.get("balance_available", zrows[-1]["balance_available"]):
            no_balance.append({"transformer_id": tx, "district": zrows[0]["district"], "open_cases": open_cases.get(tx, 0)})
            continue
        week = [r for r in zrows if r["date"] >= week_start]
        supply = _avg([float(r["supplied_kwh"] or 0) for r in week]) or 0.0
        threshold = max(zc["share_of_supply"] * supply, zc["min_gap_kwh_per_day"])
        flagged_prev += _flagged_at([r for r in zrows if r["date"] <= prev_end], k)
        zones.append({
            "transformer_id": tx, "district": info.get("district") or zrows[0]["district"],
            "gap_kwh_per_day": round(_avg([float(r["gap_kwh"] or 0) for r in week]) or 0, 1),
            "gap_pct": round((_avg([float(r["gap_pct"] or 0) for r in week]) or 0) * 100, 2),
            "margin_kwh": round(_avg([float(r["uncertainty_kwh"] or 0) for r in week]) or 0, 1),
            "threshold_kwh": round(threshold, 1), "supply_kwh_per_day": round(supply),
            "flagged": bool(info.get("flagged", _flagged_at(zrows, k))), "priority": info.get("priority") or "normal",
            "gap_start": info["gap_start"].isoformat() if info.get("gap_start") else None,
            "gap_since_start": bool(info.get("gap_since_start")), "flatness_cv": info.get("flatness_cv"),
            "open_cases": open_cases.get(tx, 0), "suspects_without_case": waiting.get(tx, 0),
        })
    zones.sort(key=lambda z: -z["gap_kwh_per_day"])
    flagged_now = sum(z["flagged"] for z in zones)
    above = sum(max(0.0, z["gap_kwh_per_day"] - z["threshold_kwh"]) for z in zones)

    # Work: cases, visits, reports and alerts in the last 7 calendar days (and the 7 before).
    work = conn.execute(
        """SELECT count(*) FILTER (WHERE created_at >= %(w)s) AS opened,
                  count(*) FILTER (WHERE created_at >= %(w2)s AND created_at < %(w)s) AS opened_prev,
                  count(*) FILTER (WHERE closed_at >= %(w)s) AS closed,
                  count(*) FILTER (WHERE closed_at >= %(w2)s AND closed_at < %(w)s) AS closed_prev,
                  count(*) FILTER (WHERE status = 'closed') AS closed_total,
                  count(*) FILTER (WHERE status = 'assigned' AND assigned_at < %(overdue)s) AS overdue
           FROM inspection_case""",
        {"w": week_ago, "w2": two_weeks_ago, "overdue": now - timedelta(hours=cfg["dispatch"]["escalation_hours"])}).fetchone()
    status = {s["status"]: s["n"] for s in conn.execute("SELECT status, count(*) AS n FROM inspection_case GROUP BY status").fetchall()}
    outcomes_week = {o["outcome"]: o["n"] for o in conn.execute(
        "SELECT outcome, count(*) AS n FROM inspection_outcome WHERE recorded_at >= %s GROUP BY outcome", (week_ago,)).fetchall()}
    # All time = the same outcomes the hit rates learn from (training_label): live visits plus historic ones.
    outcomes_all = {o["outcome"]: o["n"] for o in conn.execute(
        """SELECT outcome, count(*) AS n FROM (SELECT outcome FROM inspection_outcome UNION ALL SELECT outcome FROM historic_outcome) o
           GROUP BY outcome""").fetchall()}
    hit = conn.execute(
        """SELECT CASE WHEN origin = 'random_sample' THEN 'random_sample' ELSE 'model_ranked' END AS kind, count(*) AS inspections,
                  sum(is_theft::int) AS confirmed FROM training_label GROUP BY 1""").fetchall()
    hit_rates = {}
    for h in hit:
        ci = wilson(h["confirmed"], h["inspections"])
        hit_rates[h["kind"]] = {"inspections": h["inspections"], "confirmed_theft": h["confirmed"],
                                "hit_rate_pct": round(h["confirmed"] / h["inspections"] * 100, 1) if h["inspections"] else None,
                                "ci_low_pct": round(ci[0] * 100, 1) if ci else None, "ci_high_pct": round(ci[1] * 100, 1) if ci else None}
    reports = conn.execute(
        """SELECT count(*) FILTER (WHERE export_approved_at >= %s) AS n, count(*) FILTER (WHERE export_approved_at >= %s
           AND export_approved_at < %s) AS prev FROM case_report""", (week_ago, two_weeks_ago, week_ago)).fetchone()
    alerts = conn.execute(
        """SELECT count(*) FILTER (WHERE acknowledged_by IS NULL) AS open, count(*) FILTER (WHERE ts >= %s) AS week
           FROM alert WHERE region IN (%s, '*')""", (week_ago, caller.region)).fetchone()

    # Data quality for the meter week, fallbacks in use, and the model.
    meters = conn.execute("SELECT count(*) FILTER (WHERE meter_type = 'smart') AS smart, count(*) AS total FROM meter").fetchone()
    short_days = conn.execute(
        "SELECT count(*) AS n FROM data_quality_flag WHERE date BETWEEN %s AND %s AND run_date = (SELECT max(run_date) FROM data_quality_flag)",
        (week_start, last)).fetchone()["n"]
    notes = conn.execute("SELECT loss_method, voltage->>'method' AS vmethod, voltage->>'confidence' AS vconf FROM zone_run "
                         "WHERE run_date = (SELECT max(run_date) FROM zone_run)").fetchall()
    solar_registrations = conn.execute("SELECT count(*) AS n FROM account_event WHERE event_type = 'solar_registration'").fetchone()["n"]
    fallbacks = []
    if no_balance:
        fallbacks.append("AS-2")
    if simulated:
        fallbacks.append("AS-3-simulated")
    elif any(n["vmethod"] in (None, "none") for n in notes):
        fallbacks.append("AS-3")
    if any(n["vconf"] == "low" for n in notes):
        fallbacks.append("AS-7")
    if any(n["loss_method"] == "similar_zones" for n in notes):
        fallbacks.append("AS-8")
    if not solar_registrations:
        fallbacks.append("AS-9")
    model = conn.execute("SELECT version_id, trained_at FROM model_version ORDER BY trained_at DESC LIMIT 1").fetchone()
    labels = conn.execute("SELECT count(*) AS n FROM training_label").fetchone()["n"]
    # Rooftop solar in the ranked zones of the latest run (FR-PS-10): tagged, still suspected, unregistered export.
    solar = conn.execute(
        """SELECT count(*) FILTER (WHERE 'solar' = ANY(f.tags)) AS tagged,
                  count(*) FILTER (WHERE 'solar' = ANY(f.tags) AND (f.details->'solar'->'penalty'->>'applies') = 'false') AS suspected,
                  count(*) FILTER (WHERE f.details->'solar'->>'follow_up' = 'unregistered_export') AS unregistered_export
           FROM premise_feature f WHERE f.run_date = (SELECT max(run_date) FROM premise_feature)""").fetchone()

    rate = tariff()
    kwh_month = round(avg_now * 30) if avg_now is not None else None
    return {
        **base, "empty": False,
        "energy_window": {"from": week_start.isoformat(), "to": last.isoformat()},
        "work_window": {"from": week_ago.astimezone(MYT).date().isoformat(), "to": myt.date().isoformat()},
        "window_gap_days": (myt.date() - last).days,
        "data_mode": {"simulated": simulated, "outcomes_simulated": sources.get("inspection_outcome", "simulated") == "simulated",
                      "sources": sources},
        "kpis": {"flagged_zones": flagged_now, "flagged_zones_prev": flagged_prev, "zones_with_balance": len(zones),
                 "zones_without_balance": len(no_balance),
                 "unexplained_kwh_per_day": round(avg_now) if avg_now is not None else None,
                 "unexplained_kwh_per_day_prev": round(avg_before) if avg_before is not None else None,
                 "unexplained_change_pct": _change(avg_now, avg_before),
                 "unexplained_kwh_per_month": kwh_month,
                 "value_at_risk": (f"RM {kwh_month * rate['rm_per_kwh']:,.0f} a month (estimate)" if rate["rm_per_kwh"] and kwh_month
                                   else "[TNB tariff: to be supplied]"),
                 "cases_opened": work["opened"], "cases_closed": work["closed"], "cases_opened_prev": work["opened_prev"],
                 "cases_closed_prev": work["closed_prev"], "cases_closed_total": work["closed_total"], "cases_overdue": work["overdue"],
                 "reports_exported": reports["n"], "reports_exported_prev": reports["prev"], "open_alerts": alerts["open"],
                 "alerts_this_week": alerts["week"]},
        "region_margin_kwh": round(margin_now) if margin_now is not None else None,
        "week_average": {"this": round(avg_now) if avg_now is not None else None, "prev": round(avg_before) if avg_before is not None else None},
        "daily_gap": daily_gap,
        "zones": zones,
        "no_balance_zones": no_balance,
        "top_zones": [{k2: z[k2] for k2 in ("transformer_id", "district", "gap_kwh_per_day", "gap_pct", "flagged")} for z in zones[:5]],
        "value": {"kwh_per_month": kwh_month, "kwh_per_month_above_threshold": round(above * 30),
                  "rm_per_kwh": rate["rm_per_kwh"], "tariff_source": rate["source"]},
        "cases_by_status": status,
        "outcomes_this_week": outcomes_week,
        "outcomes_all_time": outcomes_all,
        "hit_rates": hit_rates,
        "quality": {"meter_days_complete_pct": round(100 - short_days / max(meters["smart"] * 7, 1) * 100, 1) if meters["smart"] else None,
                    "monthly_read_pct": round((meters["total"] - meters["smart"]) / meters["total"] * 100, 1) if meters["total"] else None,
                    "zones_without_dtm": len(no_balance), "fallbacks": fallbacks},
        "solar": {"tagged": solar["tagged"], "suspected": solar["suspected"],
                  "unregistered_export": solar["unregistered_export"], "registrations": solar_registrations},
        "model": {"scoring": run.get("model_version") if run else None,
                  "retrained": model["version_id"] if model else None,
                  "retrained_at": model["trained_at"].astimezone(MYT).isoformat(timespec="minutes") if model else None,
                  "labels": labels},
        "thresholds": {"share_of_supply": zc["share_of_supply"], "min_gap_kwh_per_day": zc["min_gap_kwh_per_day"],
                       "consecutive_days": k, "large_load_share": zc["large_load_share"], "flat_cv": zc["flat_cv"],
                       "min_random_checks": int(cfg.get("weekly", {}).get("min_random_checks", 10)),
                       "escalation_hours": cfg["dispatch"]["escalation_hours"]},
    }


def headline(d: dict, lang: str = "en") -> str:
    from voltguard.service import digest_render

    return digest_render.headline(d, lang)


def render_html(d: dict, lang: str = "en") -> str:
    from voltguard.service import digest_render

    return digest_render.render_html(d, lang)


def pdf_bytes(d: dict, lang: str = "en") -> bytes:
    from voltguard.service import digest_render

    return digest_render.pdf_bytes(d, lang)


def due(now: datetime, cfg: dict, last_sent: str | None) -> str | None:
    """The send slot now due, as its ISO week ("2026-W44"), or None (Settings: weekly.day_of_week,
    hour and minute, Malaysia time). The slot's own week is stored as sent, so a Sunday slot checked
    on Monday is not sent again."""
    w = cfg.get("weekly", {})
    local = now.astimezone(MYT)
    slot = local.replace(hour=int(w.get("hour", 8)), minute=int(w.get("minute", 0)), second=0, microsecond=0)
    slot -= timedelta(days=(local.weekday() - int(w.get("day_of_week", 0))) % 7)
    if slot > local:
        slot -= timedelta(days=7)
    week = f"{slot.isocalendar().year}-W{slot.isocalendar().week:02d}"
    return week if last_sent != week else None


def send_weekly(now: datetime | None = None, force: bool = True) -> list[dict]:
    """Each region's summary to its managers (and supervisors, if set) in-app and on Telegram.

    The scheduler calls `weekly_tick` every 15 minutes, which sends once per week at the time set in
    Settings; `send_weekly()` sends now. Both pass the text and the PDF through the output check first.
    """
    from voltguard.service import digest_render, notify

    now = now or datetime.now(timezone.utc)
    with db.admin_connection() as conn:
        cfg = settings.thresholds(conn)
        roles = ("manager", "supervisor") if int(cfg.get("weekly", {}).get("include_supervisors", 1)) else ("manager",)
        people = conn.execute("SELECT user_id, role, region, team FROM app_user WHERE role = ANY(%s) AND active "
                              "AND region <> '*' ORDER BY user_id", (list(roles),)).fetchall()
    send_pdf = bool(int(cfg.get("weekly", {}).get("send_pdf", 1)))
    sent = []
    for p in people:
        caller = Caller(p["user_id"], p["role"], p["region"], p["team"])
        with db.app_connection(caller) as conn:
            d = build(conn, caller, now)
            if d.get("empty"):
                continue
            document = None
            if send_pdf:
                data = digest_render.pdf_bytes(d)
                digest_render.check_document(data)
                document = (f"{d['report_id']}.pdf", data)
            sent.append(notify.send(conn, "weekly", None, p["region"], p["user_id"], digest_render.headline(d), buttons=[],
                                    document=document))
            db.audit(conn, "agent:digest", "digest.weekly", f"user:{p['user_id']}", {"report_id": d["report_id"]})
    log.info("weekly summary sent to %d people", len(sent))
    return sent


def weekly_tick() -> None:
    """Scheduler job (every 15 minutes): send the weekly summary once, at the time set in Settings."""
    now = datetime.now(timezone.utc)
    with db.admin_connection() as conn:
        cfg = settings.thresholds(conn)
        row = conn.execute("SELECT value FROM setting WHERE key = 'weekly_last_sent'").fetchone()
        last_sent = row["value"].get("week") if row else None
        week = due(now, cfg, last_sent)
        if week is None:
            return
        conn.execute("INSERT INTO setting (key, value, changed_by) VALUES ('weekly_last_sent', %s, 'agent:digest') "
                     "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, changed_at = now()", (Jsonb({"week": week}),))
    send_weekly(now)
