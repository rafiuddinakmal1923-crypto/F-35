"""Analyst chatbot (SDD 8.1, FR-AG-03) and the read-only query service behind POST /query.

The chatbot never writes SQL. A question is mapped to one of a fixed set of read-only query
templates over the results tables (zones, balances, cases, labels), run on the caller's own
connection, so row-level security limits every answer to the caller's region. The answer shows
the query and figures used. Questions about another region are refused. With LLM_MODE=ollama
the model only picks the template and its parameters (JSON); mock mode uses keyword rules.

Each template also names the chart that suits its rows (bar for categories, line for days), so the
web app draws the answer; "as a bar/line chart" in the question switches between the two. The
summary sentence is built from the rows themselves, never generated.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import psycopg

from voltguard import config, db
from voltguard.agents import guardrails, llm, scrubber
from voltguard.db import Caller


@dataclass(frozen=True)
class Template:
    description: str
    sql: str
    params: tuple[str, ...] = ()
    defaults: tuple = ()
    chart: dict | None = None      # {"type": "bar"|"line", "x": column, "y": [columns], "series": pivot column, "y_label": text}


TEMPLATES: dict[str, Template] = {
    "zones_gap_above": Template(
        "Zones whose average gap over the last N days is above a share of supply",
        """SELECT b.transformer_id, t.district, round(avg(b.gap_pct)::numeric * 100, 1) AS avg_gap_pct,
                  round(avg(b.gap_kwh)::numeric, 0) AS avg_gap_kwh_per_day
           FROM zone_daily_balance b JOIN transformer t USING (transformer_id)
           WHERE b.balance_available AND b.date > (SELECT max(date) FROM zone_daily_balance) - %(days)s::int
           GROUP BY b.transformer_id, t.district HAVING avg(b.gap_pct) > %(pct)s::float / 100 ORDER BY avg_gap_pct DESC""",
        ("pct", "days"), (20.0, 7), {"type": "bar", "x": "transformer_id", "y": ["avg_gap_pct"], "y_label": "Average gap, % of supply"}),
    "flagged_zones": Template(
        "Flagged zones in the latest detection run",
        """SELECT transformer_id, district, round(gap_pct_recent::numeric * 100, 1) AS gap_pct, round(gap_kwh_recent::numeric, 0) AS gap_kwh_per_day,
                  priority, gap_start FROM zone_run WHERE flagged AND run_date = (SELECT max(run_date) FROM zone_run) ORDER BY gap_pct_recent DESC""",
        chart={"type": "bar", "x": "transformer_id", "y": ["gap_kwh_per_day"], "y_label": "Unexplained energy, kWh/day"}),
    "top_zones": Template(
        "Top N zones by gap share in the latest run",
        """SELECT transformer_id, district, flagged, round(gap_pct_recent::numeric * 100, 1) AS gap_pct FROM zone_run
           WHERE balance_available AND run_date = (SELECT max(run_date) FROM zone_run) ORDER BY gap_pct_recent DESC LIMIT %(n)s""",
        ("n",), (5,), {"type": "bar", "x": "transformer_id", "y": ["gap_pct"], "y_label": "Gap, % of supply"}),
    "open_cases": Template(
        "Open cases by status",
        "SELECT status, count(*) AS cases FROM inspection_case WHERE status <> 'closed' GROUP BY status ORDER BY status",
        chart={"type": "bar", "x": "status", "y": ["cases"], "y_label": "Open cases"}),
    "hit_rates": Template(
        "Hit rate of inspections, model-ranked vs random sample",
        """SELECT CASE WHEN origin = 'random_sample' THEN 'random sample' ELSE 'model-ranked' END AS inspections, count(*) AS labelled,
                  sum(is_theft::int) AS confirmed_theft, round(avg(is_theft::int)::numeric * 100, 1) AS hit_rate_pct
           FROM training_label GROUP BY 1 ORDER BY 1""",
        chart={"type": "bar", "x": "inspections", "y": ["hit_rate_pct"], "y_label": "Hit rate, % of inspections"}),
    "zone_gap": Template(
        "Recent gap of one zone",
        """SELECT transformer_id, district, flagged, round(gap_pct_recent::numeric * 100, 1) AS gap_pct, round(gap_kwh_recent::numeric, 0) AS gap_kwh_per_day,
                  gap_start, round(flatness_cv::numeric, 2) AS flatness_cv
           FROM zone_run WHERE transformer_id = %(zone)s AND run_date = (SELECT max(run_date) FROM zone_run)""",
        ("zone",), ("",)),
    "zone_gap_trend": Template(
        "Daily energy gap of one zone over the last N days",
        """SELECT date, round(gap_kwh::numeric, 0) AS gap_kwh, round(uncertainty_kwh::numeric, 0) AS uncertainty_kwh,
                  round(gap_pct::numeric * 100, 1) AS gap_pct
           FROM zone_daily_balance WHERE transformer_id = %(zone)s AND balance_available
             AND date > (SELECT max(date) FROM zone_daily_balance) - %(days)s::int ORDER BY date""",
        ("zone", "days"), ("", 30), {"type": "line", "x": "date", "y": ["gap_kwh", "uncertainty_kwh"], "y_label": "kWh/day"}),
    "region_gap_trend": Template(
        "Daily energy gap of every zone with a balance over the last N days",
        """SELECT date, transformer_id, round(gap_kwh::numeric, 0) AS gap_kwh FROM zone_daily_balance
           WHERE balance_available AND date > (SELECT max(date) FROM zone_daily_balance) - %(days)s::int ORDER BY date, transformer_id""",
        ("days",), (30,), {"type": "line", "x": "date", "y": ["gap_kwh"], "series": "transformer_id", "y_label": "Unexplained energy, kWh/day"}),
    "gap_by_district": Template(
        "Unexplained energy and flagged zones by district in the latest run",
        """SELECT district, round(sum(CASE WHEN balance_available THEN gap_kwh_recent ELSE 0 END)::numeric, 0) AS gap_kwh_per_day,
                  sum(flagged::int) AS flagged_zones, count(*) AS zones
           FROM zone_run WHERE run_date = (SELECT max(run_date) FROM zone_run) GROUP BY district ORDER BY gap_kwh_per_day DESC""",
        chart={"type": "bar", "x": "district", "y": ["gap_kwh_per_day"], "y_label": "Unexplained energy, kWh/day"}),
    "outcomes_summary": Template(
        "Inspection outcomes recorded so far",
        """SELECT replace(outcome, '_', ' ') AS outcome, count(*) AS visits FROM inspection_outcome GROUP BY outcome ORDER BY visits DESC""",
        chart={"type": "bar", "x": "outcome", "y": ["visits"], "y_label": "Visits"}),
}
TREND = re.compile(r"\b(trend|over time|daily|per day|each day|history|graph|chart|plot|line)\b")
NUMBER = re.compile(r"(\d+(?:\.\d+)?)\s*(%|percent|peratus)")


class QueryError(Exception):
    pass


def run_query(conn: psycopg.Connection, caller: Caller, template: str, params: dict | None = None) -> dict:
    """POST /query: one whitelisted read-only template, on the caller's connection (region-limited)."""
    if caller.role not in ("manager", "analyst"):
        raise QueryError("The query service answers managers and analysts")
    t = TEMPLATES.get(template)
    if t is None:
        raise QueryError(f"Unknown query; available: {', '.join(TEMPLATES)}")
    values = dict(zip(t.params, t.defaults))
    for key, value in (params or {}).items():
        if key not in t.params:
            raise QueryError(f"Unknown parameter {key}")
        values[key] = value
    if "pct" in values:
        values["pct"] = float(values["pct"])
    if "days" in values:
        values["days"] = max(1, min(int(values["days"]), 90))
    if "n" in values:
        values["n"] = max(1, min(int(values["n"]), 50))
    rows = conn.execute(t.sql, values).fetchall()
    return {"template": template, "description": t.description, "sql": " ".join(t.sql.split()), "params": values, "rows": rows,
            "chart": dict(t.chart) if t.chart and rows else None}


def _regions() -> dict[str, list[str]]:
    """Region code -> words that name it (code, name, its districts), for the out-of-region check."""
    names: dict[str, list[str]] = {}
    for r in config.demo_config().get("regions", []):
        names[r["code"]] = [r["code"].lower(), r["name"].lower()]
    with db.admin_connection() as conn:
        for row in conn.execute("SELECT DISTINCT region, district FROM transformer"):
            names.setdefault(row["region"], [row["region"].lower()]).append(row["district"].lower())
    return names


def other_region_named(question: str, caller: Caller) -> str | None:
    if caller.region == "*":
        return None
    q = question.lower()
    regions = _regions()
    own = regions.get(caller.region, [])
    for code, words in regions.items():
        if code == caller.region:
            continue
        for w in words:
            if w and w not in own and re.search(rf"\b{re.escape(w)}\b", q):
                return code
    return None


def parse_mock(question: str) -> tuple[str, dict]:
    q = question.lower()
    zone = re.search(r"\btx-[a-z]{3}-\d{3}\b", q)
    days = re.search(r"(\d+)\s*(?:days|hari)", q)
    span = {"days": int(days.group(1))} if days else {"days": 7} if ("week" in q or "minggu" in q) else {}
    if zone and TREND.search(q):
        return "zone_gap_trend", {"zone": zone.group(0).upper(), **span}
    if zone:
        return "zone_gap", {"zone": zone.group(0).upper()}
    if "district" in q or "daerah" in q:
        return "gap_by_district", {}
    if "outcome" in q or "keputusan" in q or "visit" in q:
        return "outcomes_summary", {}
    if "hit rate" in q or "precision" in q or "random sample" in q:
        return "hit_rates", {}
    if "case" in q or "kes" in q:
        return "open_cases", {}
    pct = NUMBER.search(q)
    if pct and ("gap" in q or "loss" in q or "jurang" in q or "above" in q):
        days = 7 if ("week" in q or "minggu" in q) else 30 if "month" in q else 7
        return "zones_gap_above", {"pct": float(pct.group(1)), "days": days}
    top = re.search(r"top\s+(\d+)", q)
    if top:
        return "top_zones", {"n": int(top.group(1))}
    if TREND.search(q) and ("gap" in q or "loss" in q or "energy" in q or "zone" in q or "jurang" in q):
        return "region_gap_trend", span
    if "flag" in q or "leak" in q or "bocor" in q:
        return "flagged_zones", {}
    return "", {}


def parse(question: str) -> tuple[str, dict, str]:
    template, params = parse_mock(question)
    try:
        completion = _ask_model(question)
    except llm.PromptBlocked:
        completion = None
    if completion:
        try:
            choice = json.loads(re.search(r"\{.*\}", completion.text, re.S).group(0))
            if choice.get("template") in TEMPLATES:
                return choice["template"], choice.get("params") or {}, "ollama"
        except (AttributeError, ValueError):
            pass
    return template, params, "mock"


def _ask_model(question: str):
    return llm.complete(
        "Map the manager's question to ONE query template. Reply with JSON only: {\"template\": name, \"params\": {...}}. "
        "Templates: " + json.dumps({k: {"description": t.description, "params": list(t.params)} for k, t in TEMPLATES.items()})
        + ". If none fits, use {\"template\": \"\"}.", question, timeout=60, max_tokens=120)


def _num(v) -> str:
    return f"{float(v):,.1f}".rstrip("0").rstrip(".") if v is not None else "?"


def summarise(template: str, rows: list[dict], params: dict) -> str:
    """One plain sentence built from the rows (no generation), so the figures always match the table."""
    if not rows:
        return {"zones_gap_above": f"No zone in your region averaged a gap above {_num(params.get('pct'))}% over the last {params.get('days')} days.",
                "flagged_zones": "No zone in your region is flagged in the latest run.",
                "open_cases": "There are no open cases in your region.",
                "outcomes_summary": "No inspection outcome has been recorded yet.",
                "hit_rates": "No inspection outcome is a training label yet, so there is no hit rate."}.get(
            template, f"{TEMPLATES[template].description}: no matching rows in your region.")
    r0, n = rows[0], len(rows)
    if template == "zones_gap_above":
        listed = ", ".join(f"{r['transformer_id']} ({_num(r['avg_gap_pct'])}%)" for r in rows[:5])
        return f"{n} zone(s) averaged a gap above {_num(params['pct'])}% of supply over the last {params['days']} days: {listed}."
    if template == "flagged_zones":
        return (f"{n} zone(s) are flagged in the latest run. The largest gap is {r0['transformer_id']} in {r0['district']}: "
                f"{_num(r0['gap_pct'])}% of supply, about {_num(r0['gap_kwh_per_day'])} kWh/day.")
    if template == "top_zones":
        return f"Top {n} zone(s) by gap share: " + ", ".join(f"{r['transformer_id']} ({_num(r['gap_pct'])}%)" for r in rows) + "."
    if template == "open_cases":
        total = sum(r["cases"] for r in rows)
        return f"{total} open case(s): " + ", ".join(f"{r['cases']} {r['status']}" for r in rows) + "."
    if template == "hit_rates":
        return " ".join(f"{r['inspections'].capitalize()} inspections found theft in {_num(r['hit_rate_pct'])}% of {r['labelled']} labelled visit(s)."
                        for r in rows)
    if template == "zone_gap":
        since = f"since {r0['gap_start']}" if r0["gap_start"] else "since data start"
        flat = " (flat 24/7)" if r0["flatness_cv"] is not None and r0["flatness_cv"] < 0.2 else ""
        state = "is flagged" if r0["flagged"] else "is not flagged"
        return (f"{r0['transformer_id']} ({r0['district']}) {state}: gap {_num(r0['gap_pct'])}% of supply, about "
                f"{_num(r0['gap_kwh_per_day'])} kWh/day, {since}; flatness {float(r0['flatness_cv'] or 0):.2f}{flat}.")
    if template == "zone_gap_trend":
        gaps = [float(r["gap_kwh"]) for r in rows if r["gap_kwh"] is not None]
        last = rows[-1]
        return (f"Over the last {n} day(s) the gap of {params['zone']} averaged {_num(sum(gaps) / len(gaps))} kWh/day "
                f"(lowest {_num(min(gaps))}, highest {_num(max(gaps))}); on {last['date']} it was {_num(last['gap_kwh'])} kWh "
                f"with an uncertainty of ±{_num(last['uncertainty_kwh'])} kWh.")
    if template == "region_gap_trend":
        totals: dict[str, list[float]] = {}
        for r in rows:
            totals.setdefault(r["transformer_id"], []).append(float(r["gap_kwh"] or 0))
        top = max(totals.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
        return (f"Daily gap of {len(totals)} zone(s) over the last {params['days']} days. "
                f"Highest on average: {top[0]}, {_num(sum(top[1]) / len(top[1]))} kWh/day.")
    if template == "gap_by_district":
        return (f"{r0['district']} carries the most unexplained energy: {_num(r0['gap_kwh_per_day'])} kWh/day, "
                f"with {r0['flagged_zones']} flagged zone(s) of {r0['zones']}.")
    if template == "outcomes_summary":
        return f"{sum(r['visits'] for r in rows)} visit(s) recorded: " + ", ".join(f"{r['visits']} {r['outcome']}" for r in rows) + "."
    return f"{TEMPLATES[template].description}: {n} row(s)."


def _chart_choice(question: str, chart: dict | None) -> dict | None:
    """'as a bar chart' / 'as a line chart' switches a single-series chart between the two forms."""
    if not chart or chart.get("series"):
        return chart
    q = question.lower()
    if re.search(r"\bbar\b", q):
        return {**chart, "type": "bar"}
    if re.search(r"\bline\b", q):
        return {**chart, "type": "line"}
    return chart


def ask(conn: psycopg.Connection, caller: Caller, question: str) -> dict:
    guardrails.allow("chatbot", "query_results_views")
    if guardrails.asks_forbidden_action(question):
        result = {"answer": guardrails.REFUSAL, "refused": True}
    elif (other := other_region_named(question, caller)) is not None:
        result = {"answer": f"I can only answer about your own region ({caller.region}); that question is about region {other}.",
                  "refused": True}
    else:
        template, params, mode = parse(question)
        if not template:
            result = {"answer": "I answer numeric questions about zones, gaps, cases and hit rates in your region, for example "
                                "'Which zones had a gap above 20% this week?'. I could not match this question to a query.",
                      "refused": False, "mode": mode}
        else:
            try:
                q = run_query(conn, caller, template, params)
            except (QueryError, ValueError, TypeError) as exc:
                result = {"answer": f"I could not run that query: {exc}", "refused": False}
            else:
                q["chart"] = _chart_choice(question, q["chart"])
                summary = summarise(template, q["rows"], q["params"])
                # Built only from zone, case and label columns: the pattern check is enough (Presidio reads
                # two-word district names such as "Seberang Perai" as a person's name).
                result = {"answer": guardrails.check_output(summary, presidio=False), "refused": False, "mode": mode, "query": q}
    db.audit(conn, caller.user_id, "agent.chatbot.answer", None,
             {"question": scrubber.scrub(question).text[:300], "template": (result.get("query") or {}).get("template"), "refused": result["refused"]})
    return result
