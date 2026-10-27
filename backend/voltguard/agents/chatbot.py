"""Analyst chatbot (SDD 8.1, FR-AG-03) and the read-only query service behind POST /query.

The chatbot never writes SQL. A question is mapped to one of a fixed set of read-only query
templates over the results tables (zones, balances, cases, labels), run on the caller's own
connection, so row-level security limits every answer to the caller's region. The answer shows
the query and figures used. Questions about another region are refused. With LLM_MODE=ollama
the model only picks the template and its parameters (JSON); mock mode uses keyword rules.
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


TEMPLATES: dict[str, Template] = {
    "zones_gap_above": Template(
        "Zones whose average gap over the last N days is above a share of supply",
        """SELECT b.transformer_id, t.district, round(avg(b.gap_pct)::numeric * 100, 1) AS avg_gap_pct,
                  round(avg(b.gap_kwh)::numeric, 0) AS avg_gap_kwh_per_day
           FROM zone_daily_balance b JOIN transformer t USING (transformer_id)
           WHERE b.balance_available AND b.date > (SELECT max(date) FROM zone_daily_balance) - %(days)s::int
           GROUP BY b.transformer_id, t.district HAVING avg(b.gap_pct) > %(pct)s::float / 100 ORDER BY avg_gap_pct DESC""",
        ("pct", "days"), (20.0, 7)),
    "flagged_zones": Template(
        "Flagged zones in the latest detection run",
        """SELECT transformer_id, district, round(gap_pct_recent::numeric * 100, 1) AS gap_pct, round(gap_kwh_recent::numeric, 0) AS gap_kwh_per_day,
                  priority, gap_start FROM zone_run WHERE flagged AND run_date = (SELECT max(run_date) FROM zone_run) ORDER BY gap_pct_recent DESC"""),
    "top_zones": Template(
        "Top N zones by gap share in the latest run",
        """SELECT transformer_id, district, flagged, round(gap_pct_recent::numeric * 100, 1) AS gap_pct FROM zone_run
           WHERE balance_available AND run_date = (SELECT max(run_date) FROM zone_run) ORDER BY gap_pct_recent DESC LIMIT %(n)s""",
        ("n",), (5,)),
    "open_cases": Template(
        "Open cases by status",
        "SELECT status, count(*) AS cases FROM inspection_case WHERE status <> 'closed' GROUP BY status ORDER BY status"),
    "hit_rates": Template(
        "Hit rate of inspections, model-ranked vs random sample",
        """SELECT CASE WHEN origin = 'random_sample' THEN 'random sample' ELSE 'model-ranked' END AS inspections, count(*) AS labelled,
                  sum(is_theft::int) AS confirmed_theft, round(avg(is_theft::int)::numeric * 100, 1) AS hit_rate_pct
           FROM training_label GROUP BY 1 ORDER BY 1"""),
    "zone_gap": Template(
        "Recent gap of one zone",
        """SELECT transformer_id, district, flagged, round(gap_pct_recent::numeric * 100, 1) AS gap_pct, round(gap_kwh_recent::numeric, 0) AS gap_kwh_per_day,
                  gap_start, round(flatness_cv::numeric, 2) AS flatness_cv
           FROM zone_run WHERE transformer_id = %(zone)s AND run_date = (SELECT max(run_date) FROM zone_run)""",
        ("zone",), ("",)),
}
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
    return {"template": template, "description": t.description, "sql": " ".join(t.sql.split()), "params": values, "rows": rows}


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
    if zone:
        return "zone_gap", {"zone": zone.group(0).upper()}
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
                n = len(q["rows"])
                summary = f"{q['description']}: {n} row(s)." if n else f"{q['description']}: no matching rows in your region."
                result = {"answer": guardrails.check_output(summary), "refused": False, "mode": mode, "query": q}
    db.audit(conn, caller.user_id, "agent.chatbot.answer", None,
             {"question": scrubber.scrub(question).text[:300], "template": (result.get("query") or {}).get("template"), "refused": result["refused"]})
    return result
