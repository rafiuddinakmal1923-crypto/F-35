"""Monitoring and alerts for the data team (FR-ML-03, SDD 9.2, NFR-11).

After each detection run:
* data quality: meter-days under 90% of intervals, zones whose transformer meter stopped reporting;
* drift: population stability index (PSI) of premises' daily use and of the score distribution
  against the previous run;
Periodically (scheduler): unusual access, e.g. one user opening many cases or premises in an hour.
Alerts go to the `alert` table, the API logs and /alerts; fairness flag rates are in rpt_ views.
"""

from __future__ import annotations

import json
import logging

import numpy as np
from psycopg.types.json import Jsonb

from voltguard import config, db

log = logging.getLogger("voltguard.monitoring")
STATE = "monitoring_state.json"
UNUSUAL_VIEWS_PER_HOUR = 40


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected, actual = np.asarray(expected, float), np.asarray(actual, float)
    expected, actual = expected[np.isfinite(expected)], actual[np.isfinite(actual)]
    if len(expected) < 10 or len(actual) < 10:
        return 0.0
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    e = np.histogram(np.clip(expected, edges[0], edges[-1]), edges)[0] / len(expected)
    a = np.histogram(np.clip(actual, edges[0], edges[-1]), edges)[0] / len(actual)
    e, a = np.clip(e, 1e-4, None), np.clip(a, 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))


def _alert(conn, kind: str, message: str, detail: dict, region: str = "*", severity: str = "warning") -> None:
    conn.execute("INSERT INTO alert (kind, severity, region, message, detail) VALUES (%s, %s, %s, %s, %s)",
                 (kind, severity, region, message, Jsonb(detail)))
    log.warning("[alert:%s] %s", kind, message)


def collect(run, into: dict | None = None) -> dict:
    """What monitoring needs from a detection run, small enough to keep across zone batches."""
    into = into if into is not None else {"daily_use": [], "scores": [], "flags": {}, "silent_meters": [], "region": {}}
    for tx, z in run.zones.items():
        into["region"][tx] = z.zone.region
        if z.zone.smart.any():
            into["daily_use"].append(np.nansum(z.zone.kwh.reshape(z.zone.n, z.zone.days, 48), axis=2)[z.zone.smart, -7:].ravel())
        into["scores"].extend(p.score for p in z.premises)
        if z.quality_flags:
            into["flags"][tx] = list(z.quality_flags)
        if z.zone.supply_kwh is not None and np.isnan(z.zone.supply_kwh[-48:]).all():
            into["silent_meters"].append(tx)
    return into


def after_detection(run_or_inputs, summary: dict) -> list[str]:
    """Called by the pipeline after each run (a DetectionRun, or inputs from collect()). Returns the alert kinds raised."""
    inputs = run_or_inputs if isinstance(run_or_inputs, dict) else collect(run_or_inputs)
    raised = []
    cfg = config.thresholds()["monitoring"]
    state_path = config.data_root() / STATE
    previous = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    daily_use = np.concatenate(inputs["daily_use"] or [np.array([])])
    scores = np.array(inputs["scores"], dtype=float)
    with db.admin_connection() as conn:
        with conn.transaction():
            for tx, flags in inputs["flags"].items():
                _alert(conn, "data_quality", f"{tx}: {len(flags)} meter-day(s) below {cfg['min_interval_completeness']:.0%} of intervals",
                       {"zone": tx, "meters": sorted({f['meter_id'] for f in flags})[:20], "days": sorted({str(f['date']) for f in flags})[:10]},
                       inputs["region"][tx])
                raised.append("data_quality")
            for tx in inputs["silent_meters"]:
                _alert(conn, "data_quality", f"{tx}: transformer meter sent no data on the last day", {"zone": tx}, inputs["region"][tx])
                raised.append("data_quality")
            for name, current in (("daily_use", daily_use), ("scores", scores)):
                if name in previous and len(current):
                    value = psi(np.array(previous[name]), current)
                    if value > cfg["drift_psi_alert"]:
                        _alert(conn, "drift", f"Distribution of {name.replace('_', ' ')} shifted (PSI {value:.2f} > {cfg['drift_psi_alert']})",
                               {"metric": name, "psi": round(value, 3), "run_date": summary.get("run_date")})
                        raised.append("drift")
    rng = np.random.default_rng(0)
    keep = {"daily_use": rng.choice(daily_use, min(len(daily_use), 5000), replace=False).round(3).tolist() if len(daily_use) else [],
            "scores": scores.tolist()}
    state_path.write_text(json.dumps(keep), encoding="utf-8")
    return raised


def check_unusual_access() -> int:
    """Scheduler job: one user opening many cases or premises within an hour (SDD 9.2)."""
    with db.admin_connection() as conn:
        with conn.transaction():
            rows = conn.execute(
                """SELECT user_id, count(DISTINCT object_ref) AS n FROM audit_log WHERE action IN ('case.view', 'premise.view', 'pii.view')
                   AND ts > now() - interval '1 hour' GROUP BY user_id HAVING count(DISTINCT object_ref) > %s""",
                (UNUSUAL_VIEWS_PER_HOUR,)).fetchall()
            for r in rows:
                recent = conn.execute("SELECT 1 FROM alert WHERE kind = 'unusual_access' AND detail->>'user_id' = %s AND ts > now() - interval '1 hour'",
                                      (r["user_id"],)).fetchone()
                if not recent:
                    _alert(conn, "unusual_access", f"{r['user_id']} opened {r['n']} cases or premises in the last hour",
                           {"user_id": r["user_id"], "views": r["n"]}, severity="high")
    return len(rows)
