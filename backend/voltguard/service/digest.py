"""Weekly manager summary (SDD 9.2 manager view, FR-ML-02 hit rates): one page per region and week.

Zone-level and case-level counts only, never premise IDs or personal details, so it is safe for the
manager's dashboard, the PDF and a Telegram message alike. Two windows, both stated on the page:
- energy: the last 7 days of meter data against the 7 days before (data arrive daily, not live);
- work: the last 7 calendar days of cases, visits, reports and alerts.
Runs on the caller's connection, so row-level security limits it to the caller's region.
"""

from __future__ import annotations

import html
import logging
from datetime import datetime, timedelta, timezone

import psycopg

from voltguard import db, pdf
from voltguard.db import Caller
from voltguard.service import settings

log = logging.getLogger("voltguard.digest")


def _change(now: float | None, before: float | None) -> float | None:
    if not before:
        return None
    return round((now or 0) / before * 100 - 100, 1)


def build(conn: psycopg.Connection, caller: Caller, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    last = conn.execute("SELECT max(date) AS d FROM zone_daily_balance").fetchone()["d"]
    if last is None:
        return {"region": caller.region, "empty": True, "message": "No detection results yet."}
    days = conn.execute(
        """SELECT date, round(sum(gap_kwh)::numeric, 0) AS gap_kwh, round(sum(supplied_kwh)::numeric, 0) AS supplied_kwh
           FROM zone_daily_balance WHERE balance_available AND date > %s::date - 14 GROUP BY date ORDER BY date""", (last,)).fetchall()
    this_week = [float(d["gap_kwh"]) for d in days if d["date"] > last - timedelta(days=7)]
    prev_week = [float(d["gap_kwh"]) for d in days if d["date"] <= last - timedelta(days=7)]
    avg_now = sum(this_week) / len(this_week) if this_week else None
    avg_before = sum(prev_week) / len(prev_week) if prev_week else None
    zones = conn.execute(
        """SELECT b.transformer_id, t.district, round(avg(b.gap_kwh)::numeric, 0) AS gap_kwh_per_day,
                  round(avg(b.gap_pct)::numeric * 100, 1) AS gap_pct, bool_or(b.flagged) AS flagged
           FROM zone_daily_balance b JOIN transformer t USING (transformer_id)
           WHERE b.balance_available AND b.date > %s::date - 7 GROUP BY b.transformer_id, t.district
           ORDER BY gap_kwh_per_day DESC LIMIT 5""", (last,)).fetchall()
    run = conn.execute("""SELECT count(*) FILTER (WHERE flagged) AS flagged, count(*) FILTER (WHERE NOT balance_available) AS no_balance
                          FROM zone_run WHERE run_date = (SELECT max(run_date) FROM zone_run)""").fetchone()
    cfg = settings.thresholds(conn)["dispatch"]
    status = conn.execute("SELECT status, count(*) AS n FROM inspection_case GROUP BY status ORDER BY status").fetchall()
    work = conn.execute(
        """SELECT count(*) FILTER (WHERE created_at >= %(since)s) AS opened,
                  count(*) FILTER (WHERE closed_at >= %(since)s) AS closed,
                  count(*) FILTER (WHERE status = 'assigned' AND assigned_at < %(overdue)s) AS overdue
           FROM inspection_case""", {"since": week_ago, "overdue": now - timedelta(hours=cfg["escalation_hours"])}).fetchone()
    outcomes = conn.execute("""SELECT outcome, count(*) AS n FROM inspection_outcome WHERE recorded_at >= %s
                               GROUP BY outcome ORDER BY n DESC""", (week_ago,)).fetchall()
    hit = conn.execute(
        """SELECT CASE WHEN origin = 'random_sample' THEN 'random_sample' ELSE 'model_ranked' END AS kind, count(*) AS inspections,
                  sum(is_theft::int) AS confirmed FROM training_label GROUP BY 1""").fetchall()
    reports = conn.execute("SELECT count(*) AS n FROM case_report WHERE export_approved_at >= %s", (week_ago,)).fetchone()["n"]
    alerts = conn.execute("SELECT count(*) AS n FROM alert WHERE acknowledged_by IS NULL AND region IN (%s, '*')",
                          (caller.region,)).fetchone()["n"]
    hit_rates = {h["kind"]: {"inspections": h["inspections"], "confirmed_theft": h["confirmed"],
                             "hit_rate_pct": round(h["confirmed"] / h["inspections"] * 100, 1) if h["inspections"] else None} for h in hit}
    return {
        "region": caller.region, "generated_at": now.isoformat(), "energy_window": {"from": (last - timedelta(days=6)).isoformat(), "to": last.isoformat()},
        "work_window": {"from": week_ago.date().isoformat(), "to": now.date().isoformat()},
        "kpis": {"flagged_zones": run["flagged"], "zones_without_balance": run["no_balance"],
                 "unexplained_kwh_per_day": round(avg_now) if avg_now is not None else None,
                 "unexplained_change_pct": _change(avg_now, avg_before),
                 "unexplained_kwh_per_month": round(avg_now * 30) if avg_now is not None else None,
                 "value_at_risk": "[TNB tariff: to be supplied]",
                 "cases_opened": work["opened"], "cases_closed": work["closed"], "cases_overdue": work["overdue"],
                 "reports_exported": reports, "open_alerts": alerts},
        "daily_gap": [{"date": d["date"].isoformat(), "gap_kwh": float(d["gap_kwh"])} for d in days],
        "top_zones": [{**z, "gap_kwh_per_day": float(z["gap_kwh_per_day"]), "gap_pct": float(z["gap_pct"])} for z in zones],
        "cases_by_status": {s["status"]: s["n"] for s in status},
        "outcomes_this_week": {o["outcome"]: o["n"] for o in outcomes},
        "hit_rates": hit_rates,
    }


def headline(d: dict) -> str:
    """One line for Telegram: counts only (passes the notifier's personal-details check)."""
    k = d["kpis"]
    change = k["unexplained_change_pct"]
    trend = "" if change is None else f" ({'+' if change >= 0 else ''}{change}% vs the week before)"
    hr = d["hit_rates"].get("model_ranked", {}).get("hit_rate_pct")
    return (f"{k['flagged_zones']} flagged zone(s), {k['unexplained_kwh_per_day']} kWh/day unexplained{trend}; "
            f"{k['cases_opened']} case(s) opened, {k['cases_closed']} closed, {k['cases_overdue']} overdue"
            + (f"; model-ranked hit rate {hr}%" if hr is not None else "") + ".")


def _bars(rows: list[tuple[str, float]], unit: str, width: int = 520) -> str:
    if not rows:
        return "<p class='muted'>None.</p>"
    hi = max(v for _, v in rows) or 1
    h = 26 * len(rows) + 6
    bars = "".join(
        f"<text x='150' y='{22 + 26 * i}' text-anchor='end' font-size='12'>{html.escape(str(label))}</text>"
        f"<rect x='158' y='{8 + 26 * i}' width='{max(v / hi * (width - 230), 1):.0f}' height='18' rx='3' fill='#c2410c'/>"
        f"<text x='{164 + v / hi * (width - 230):.0f}' y='{22 + 26 * i}' font-size='12' fill='#555'>{v:g} {unit}</text>"
        for i, (label, v) in enumerate(rows))
    return f"<svg width='{width}' height='{h}' xmlns='http://www.w3.org/2000/svg'>{bars}</svg>"


def _line(points: list[float], width: int = 520, height: int = 120) -> str:
    if len(points) < 2:
        return ""
    lo, hi = min(points + [0]), max(points) or 1
    xs = [20 + i * (width - 40) / (len(points) - 1) for i in range(len(points))]
    ys = [height - 15 - (p - lo) / (hi - lo or 1) * (height - 30) for p in points]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.0f},{y:.0f}" for i, (x, y) in enumerate(zip(xs, ys)))
    mid = xs[len(points) // 2]
    return (f"<svg width='{width}' height='{height}' xmlns='http://www.w3.org/2000/svg'>"
            f"<line x1='{mid:.0f}' x2='{mid:.0f}' y1='5' y2='{height - 10}' stroke='#f5b700' stroke-dasharray='4 3'/>"
            f"<path d='{path}' fill='none' stroke='#2563eb' stroke-width='2'/></svg>")


def render_html(d: dict) -> str:
    k = d["kpis"]
    esc = html.escape
    change = "" if k["unexplained_change_pct"] is None else f" ({'+' if k['unexplained_change_pct'] >= 0 else ''}{k['unexplained_change_pct']}%)"
    cards = "".join(f"<div class='kpi'><b>{esc(str(v))}</b><span>{esc(label)}</span></div>" for label, v in [
        ("Flagged zones", k["flagged_zones"]), ("Unexplained kWh/day" + change, k["unexplained_kwh_per_day"]),
        ("Cases opened / closed", f"{k['cases_opened']} / {k['cases_closed']}"), ("Overdue cases", k["cases_overdue"]),
        ("Reports exported", k["reports_exported"]), ("Open alerts", k["open_alerts"])])
    hr = "".join(f"<tr><td>{esc(name.replace('_', ' '))}</td><td>{v['inspections']}</td><td>{v['confirmed_theft']}</td><td>{v['hit_rate_pct']}%</td></tr>"
                 for name, v in d["hit_rates"].items())
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>VoltGuard weekly summary {esc(d['region'])}</title>
<style>body{{font-family:Helvetica,Arial,sans-serif;color:#17202a;margin:0}}h1{{font-size:20px;margin:0}}h2{{font-size:14px;margin:18px 0 6px}}
.muted{{color:#5b6673;font-size:11px}}.kpis{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}}
.kpi{{border:1px solid #d7dde4;border-radius:8px;padding:8px}}.kpi b{{display:block;font-size:20px}}.kpi span{{font-size:11px;color:#5b6673}}
table{{border-collapse:collapse;font-size:12px}}td,th{{border-bottom:1px solid #d7dde4;padding:4px 10px 4px 0;text-align:left}}</style></head><body>
<h1>VoltGuard weekly summary · region {esc(d['region'])}</h1>
<p class="muted">Meter data {d['energy_window']['from']} to {d['energy_window']['to']} · work {d['work_window']['from']} to {d['work_window']['to']} ·
generated {esc(d['generated_at'][:16].replace('T', ' '))} UTC. Zone-level figures only. Scores rank risk; people decide after inspection.</p>
<div class="kpis">{cards}</div>
<h2>Unexplained energy, last 14 days (kWh/day, whole region; dashed line = start of this week)</h2>{_line([p['gap_kwh'] for p in d['daily_gap']])}
<p class="muted">About {k['unexplained_kwh_per_month']} kWh a month at this week's level. Value at risk: {esc(k['value_at_risk'])}.</p>
<h2>Top zones by unexplained energy this week</h2>{_bars([(z['transformer_id'], z['gap_kwh_per_day']) for z in d['top_zones']], 'kWh/day')}
<h2>Inspection outcomes this week</h2>{_bars([(o.replace('_', ' '), n) for o, n in d['outcomes_this_week'].items()], '')}
<h2>Hit rate so far (random sample = unbiased reference)</h2><table><tr><th>Inspections</th><th>Labelled</th><th>Confirmed theft</th><th>Hit rate</th></tr>{hr}</table>
<h2>Cases by status now</h2><p>{esc(', '.join(f'{n} {s}' for s, n in d['cases_by_status'].items()) or 'none')}</p>
</body></html>"""


def pdf_bytes(d: dict) -> bytes:
    data, _engine = pdf.html_to_pdf(render_html(d))
    return data


def send_weekly() -> list[dict]:
    """Scheduler job (Monday morning): each region's summary line to its managers and supervisors."""
    from voltguard.service import notify

    sent = []
    with db.admin_connection() as conn:
        people = conn.execute("SELECT user_id, role, region, team FROM app_user WHERE role IN ('manager', 'supervisor') AND active "
                              "AND region <> '*'").fetchall()
    for p in people:
        caller = Caller(p["user_id"], p["role"], p["region"], p["team"])
        with db.app_connection(caller) as conn:
            d = build(conn, caller)
            if d.get("empty"):
                continue
            sent.append(notify.send(conn, "weekly", None, p["region"], p["user_id"], headline(d), buttons=[]))
            db.audit(conn, "agent:digest", "digest.weekly", f"user:{p['user_id']}", None)
    log.info("weekly summary sent to %d people", len(sent))
    return sent
