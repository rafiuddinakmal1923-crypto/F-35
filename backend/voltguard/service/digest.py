"""Manager summary (FR-ML-02 hit rates; the manager's report): one report per region and period.

The manager picks the period: a day, a week (the default, also sent on a schedule), a month, a year, or
their own From-To dates. This module gathers the figures; `digest_render` turns them into rule-based
sentences, charts, HTML and the PDF (English or Bahasa Melayu). Zone-level and case-level counts only,
never premise IDs or personal details, so the report is safe for the dashboard, the PDF and a message alike.
Two windows, both stated on the page (`windows`):
- energy: the latest period of meter data (data arrive daily, not live), against the period before;
- work: the same period up to today, for cases, visits, reports and alerts.
Chosen dates use the same dates for both. Runs on the caller's connection, so row-level security limits
it to the caller's region.
"""

from __future__ import annotations

import calendar
import logging
import math
from datetime import date, datetime, time, timedelta, timezone

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


# --------------------------------------------------------------------------- periods

PERIODS = ("day", "week", "month", "year", "custom")
CODES = {"day": "DY", "week": "WK", "month": "MO", "year": "YR", "custom": "RG"}
MAX_DAYS = 731                       # chosen dates: up to two years


class PeriodError(ValueError):
    pass


def _back_months(d: date, months: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 - months, 12)
    return date(y, m + 1, min(d.day, calendar.monthrange(y, m + 1)[1]))


def span(period: str, anchor: date) -> tuple[date, date, date, date]:
    """(from, to, prev_from, prev_to) of a preset period ending on `anchor`.

    day: that day and the day before. week: the 7 days to `anchor` and the 7 before. month and year: the
    calendar month or year so far, against the same days of the month or year before (the whole of it when
    `anchor` is its last day), so a month to date is not compared with a full month.
    """
    if period == "day":
        return anchor, anchor, anchor - timedelta(days=1), anchor - timedelta(days=1)
    if period == "week":
        return anchor - timedelta(days=6), anchor, anchor - timedelta(days=13), anchor - timedelta(days=7)
    if period == "month":
        start = anchor.replace(day=1)
        prev_start = _back_months(start, 1)
        full = anchor.day == calendar.monthrange(anchor.year, anchor.month)[1]
        prev_end = start - timedelta(days=1) if full else _back_months(anchor, 1)
        return start, anchor, prev_start, prev_end
    if period == "year":
        start, prev_start = date(anchor.year, 1, 1), date(anchor.year - 1, 1, 1)
        prev_end = date(anchor.year - 1, 12, 31) if (anchor.month, anchor.day) == (12, 31) else _back_months(anchor, 12)
        return start, anchor, prev_start, prev_end
    raise PeriodError(f"unknown period {period!r}")


def windows(period: str, last: date, today: date, start: date | None = None, end: date | None = None) -> dict:
    """Energy and work windows. Presets: energy ends on the latest meter day, work on today. Chosen dates
    (period "custom") use the same dates for both, against the same number of days just before."""
    if period not in PERIODS:
        raise PeriodError(f"period must be one of {', '.join(PERIODS)}")
    if period == "custom":
        if start is None or end is None:
            raise PeriodError("chosen dates need both from and to")
        if start > end:
            raise PeriodError("from must be on or before to")
        days = (end - start).days + 1
        if days > MAX_DAYS:
            raise PeriodError(f"chosen dates may cover at most {MAX_DAYS} days")
        both = (start, end, start - timedelta(days=days), start - timedelta(days=1))
        energy = work = both
    else:
        energy, work = span(period, last), span(period, today)
    keys = ("from", "to", "prev_from", "prev_to")
    return {"energy": dict(zip(keys, energy)), "work": dict(zip(keys, work))}


def report_id(region: str, period: str, w: dict) -> str:
    """VG-WK-CEN-2026-W44 (the week of the work window's end), VG-DY-CEN-2026-10-28, VG-MO-CEN-2026-10,
    VG-YR-CEN-2026, VG-RG-CEN-20260801-20260831."""
    end = w["work"]["to"]
    label = {"day": end.isoformat(), "week": f"{end.isocalendar().year}-W{end.isocalendar().week:02d}",
             "month": f"{end:%Y-%m}", "year": f"{end:%Y}",
             "custom": f"{w['work']['from']:%Y%m%d}-{end:%Y%m%d}"}[period]
    return f"VG-{CODES[period]}-{region}-{label}"


def _blocks(first: date, last: date, size: int, prev_first: date) -> list[tuple[date, date]]:
    """Chart points: blocks of `size` days from the period's first day forward, and back from the day before
    it, so a block never straddles the start of the period."""
    out, d = [], first
    while d <= last:
        out.append((d, min(d + timedelta(days=size - 1), last)))
        d += timedelta(days=size)
    d = first - timedelta(days=1)
    while d >= prev_first:
        out.insert(0, (max(d - timedelta(days=size - 1), prev_first), d))
        d -= timedelta(days=size)
    return out


def series(daily: dict[date, dict], first: date, last: date, prev_first: date) -> tuple[list[dict], int]:
    """Region gap per point (kWh/day) with its margin: daily for periods up to a month, then weekly (or 30-day
    for chosen dates over 400 days) averages so a year stays readable. The margin of an n-day average is √Σu² / n."""
    days = (last - first).days + 1
    size = 1 if days <= 31 else 7 if days <= 400 else 30
    out = []
    for a, b in _blocks(first, last, size, prev_first):
        pts = [v for d, v in daily.items() if a <= d <= b]
        if pts:
            out.append({"date": a.isoformat(), "to": b.isoformat(), "days": len(pts),
                        "gap_kwh": round(sum(p["gap"] for p in pts) / len(pts)),
                        "margin_kwh": round(math.sqrt(sum(p["u2"] for p in pts)) / len(pts))})
    return out, size


def _start_of(d: date) -> datetime:
    return datetime.combine(d, time.min, MYT)


def build(conn: psycopg.Connection, caller: Caller, now: datetime | None = None, period: str = "week",
          start: date | None = None, end: date | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    cfg = settings.thresholds(conn)
    zc, cc = cfg["zone"], cfg["cases"]
    k = int(zc["consecutive_days"])
    myt = now.astimezone(MYT)
    last = conn.execute("SELECT max(date) AS d FROM zone_daily_balance").fetchone()["d"]
    w = windows(period, last or myt.date(), myt.date(), start, end)
    ew, ww = w["energy"], w["work"]
    base = {"region": caller.region, "generated_at": now.isoformat(), "generated_myt": myt.isoformat(timespec="minutes"),
            "report_id": report_id(caller.region, period, w),
            "period": {"kind": period, "days": (ww["to"] - ww["from"]).days + 1}}
    if last is None:
        return {**base, "empty": True, "message": "No detection results yet."}
    # Work window as times: from the first day's midnight (MYT) up to, not including, the day after the last.
    w_from, w_to = _start_of(ww["from"]), _start_of(ww["to"] + timedelta(days=1))
    p_from, p_to = _start_of(ww["prev_from"]), _start_of(ww["prev_to"] + timedelta(days=1))

    run = conn.execute("SELECT run_date, model_version, data_sources FROM detection_run WHERE status = 'done' "
                       "ORDER BY run_id DESC LIMIT 1").fetchone() or {}
    sources = (run.get("data_sources") or {}) if run else {}
    simulated = sources.get("meter_reading", "simulated") == "simulated"

    # Energy: daily rows per zone for both meter periods (plus k days so the earlier period's flag state is known).
    rows = conn.execute(
        """SELECT b.transformer_id, t.district, b.date, b.gap_kwh, b.gap_pct, b.uncertainty_kwh, b.supplied_kwh,
                  b.over_threshold, b.balance_available
           FROM zone_daily_balance b JOIN transformer t USING (transformer_id)
           WHERE b.date BETWEEN %s AND %s ORDER BY b.transformer_id, b.date""",
        (ew["prev_from"] - timedelta(days=k), ew["to"])).fetchall()
    by_zone: dict[str, list[dict]] = {}
    for r in rows:
        by_zone.setdefault(r["transformer_id"], []).append(r)
    in_now = lambda d: ew["from"] <= d <= ew["to"]                # noqa: E731
    in_prev = lambda d: ew["prev_from"] <= d <= ew["prev_to"]     # noqa: E731

    daily: dict[date, dict] = {}
    for r in rows:
        if not r["balance_available"] or not (in_now(r["date"]) or in_prev(r["date"])):
            continue
        d = daily.setdefault(r["date"], {"gap": 0.0, "u2": 0.0})
        d["gap"] += float(r["gap_kwh"] or 0)
        d["u2"] += float(r["uncertainty_kwh"] or 0) ** 2
    gap_series, bucket = series(daily, ew["from"], ew["to"], ew["prev_from"])
    now_days = sorted(d for d in daily if in_now(d))
    avg_now = _avg([v["gap"] for d, v in daily.items() if in_now(d)])
    avg_before = _avg([v["gap"] for d, v in daily.items() if in_prev(d)])
    margin_now = _avg([math.sqrt(v["u2"]) for d, v in daily.items() if in_now(d)])

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
        period_rows = [r for r in zrows if in_now(r["date"])]
        flagged_prev += _flagged_at([r for r in zrows if r["date"] <= ew["prev_to"]], k)
        if not period_rows:
            continue           # no meter data for this zone in the period: nothing to show for it
        supply = _avg([float(r["supplied_kwh"] or 0) for r in period_rows]) or 0.0
        threshold = max(zc["share_of_supply"] * supply, zc["min_gap_kwh_per_day"])
        # The latest run's flag describes the latest meter day; a period ending earlier uses the flag rule on its own last day.
        flagged = info.get("flagged") if ew["to"] >= last and "flagged" in info else _flagged_at([r for r in zrows if r["date"] <= ew["to"]], k)
        zones.append({
            "transformer_id": tx, "district": info.get("district") or zrows[0]["district"],
            "gap_kwh_per_day": round(_avg([float(r["gap_kwh"] or 0) for r in period_rows]) or 0, 1),
            "gap_pct": round((_avg([float(r["gap_pct"] or 0) for r in period_rows]) or 0) * 100, 2),
            "margin_kwh": round(_avg([float(r["uncertainty_kwh"] or 0) for r in period_rows]) or 0, 1),
            "threshold_kwh": round(threshold, 1), "supply_kwh_per_day": round(supply),
            "flagged": bool(flagged), "priority": info.get("priority") or "normal",
            "gap_start": info["gap_start"].isoformat() if info.get("gap_start") else None,
            "gap_since_start": bool(info.get("gap_since_start")), "flatness_cv": info.get("flatness_cv"),
            "open_cases": open_cases.get(tx, 0), "suspects_without_case": waiting.get(tx, 0),
        })
    zones.sort(key=lambda z: -z["gap_kwh_per_day"])
    flagged_now = sum(z["flagged"] for z in zones)
    above = sum(max(0.0, z["gap_kwh_per_day"] - z["threshold_kwh"]) for z in zones)

    # Work: cases, visits, reports and alerts in the work window (and the period before).
    work = conn.execute(
        """SELECT count(*) FILTER (WHERE created_at >= %(w)s AND created_at < %(we)s) AS opened,
                  count(*) FILTER (WHERE created_at >= %(p)s AND created_at < %(pe)s) AS opened_prev,
                  count(*) FILTER (WHERE closed_at >= %(w)s AND closed_at < %(we)s) AS closed,
                  count(*) FILTER (WHERE closed_at >= %(p)s AND closed_at < %(pe)s) AS closed_prev,
                  count(*) FILTER (WHERE status = 'closed') AS closed_total,
                  count(*) FILTER (WHERE status = 'assigned' AND assigned_at < %(overdue)s) AS overdue
           FROM inspection_case""",
        {"w": w_from, "we": w_to, "p": p_from, "pe": p_to,
         "overdue": now - timedelta(hours=cfg["dispatch"]["escalation_hours"])}).fetchone()
    status = {s["status"]: s["n"] for s in conn.execute("SELECT status, count(*) AS n FROM inspection_case GROUP BY status").fetchall()}
    outcomes_period = {o["outcome"]: o["n"] for o in conn.execute(
        "SELECT outcome, count(*) AS n FROM inspection_outcome WHERE recorded_at >= %s AND recorded_at < %s GROUP BY outcome",
        (w_from, w_to)).fetchall()}
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
        """SELECT count(*) FILTER (WHERE export_approved_at >= %s AND export_approved_at < %s) AS n,
                  count(*) FILTER (WHERE export_approved_at >= %s AND export_approved_at < %s) AS prev FROM case_report""",
        (w_from, w_to, p_from, p_to)).fetchone()
    alerts = conn.execute(
        """SELECT count(*) FILTER (WHERE acknowledged_by IS NULL) AS open, count(*) FILTER (WHERE ts >= %s AND ts < %s) AS period
           FROM alert WHERE region IN (%s, '*')""", (w_from, w_to, caller.region)).fetchone()

    # Data quality for the meter period, fallbacks in use, and the model.
    meters = conn.execute("SELECT count(*) FILTER (WHERE meter_type = 'smart') AS smart, count(*) AS total FROM meter").fetchone()
    short_days = conn.execute(
        "SELECT count(*) AS n FROM data_quality_flag WHERE date BETWEEN %s AND %s AND run_date = (SELECT max(run_date) FROM data_quality_flag)",
        (ew["from"], ew["to"])).fetchone()["n"]
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
    iso = lambda win: {key: v.isoformat() for key, v in win.items()}    # noqa: E731
    return {
        **base, "empty": False,
        "period": {**base["period"], "bucket_days": bucket},
        "energy_window": iso(ew),
        "work_window": iso(ww),
        # Meter days with data inside the energy window (a year of a two-month dataset has 61 of 365).
        "energy_data": {"from": now_days[0].isoformat() if now_days else None, "to": now_days[-1].isoformat() if now_days else None,
                        "days": len(now_days), "of": (ew["to"] - ew["from"]).days + 1},
        "window_gap_days": (ww["to"] - ew["to"]).days,
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
                 "alerts_in_period": alerts["period"]},
        "region_margin_kwh": round(margin_now) if margin_now is not None else None,
        "period_average": {"this": round(avg_now) if avg_now is not None else None, "prev": round(avg_before) if avg_before is not None else None},
        "gap_series": gap_series,
        "zones": zones,
        "no_balance_zones": no_balance,
        "top_zones": [{k2: z[k2] for k2 in ("transformer_id", "district", "gap_kwh_per_day", "gap_pct", "flagged")} for z in zones[:5]],
        "value": {"kwh_per_month": kwh_month, "kwh_per_month_above_threshold": round(above * 30),
                  "rm_per_kwh": rate["rm_per_kwh"], "tariff_source": rate["source"]},
        "cases_by_status": status,
        "outcomes_in_period": outcomes_period,
        "outcomes_all_time": outcomes_all,
        "hit_rates": hit_rates,
        "quality": {"meter_days_complete_pct": (round(100 - short_days / max(meters["smart"] * len(now_days), 1) * 100, 1)
                                                if meters["smart"] and now_days else None),
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
