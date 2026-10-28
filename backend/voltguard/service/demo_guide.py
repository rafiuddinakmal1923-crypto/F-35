"""Guided demo (UI brief 3.8): the 7 live steps of SDD 10.5, checked against the database.

Only with DEMO_MODE on (config.demo_ui()). Each step is "done" when its pass criterion holds in the
data *and* the step was performed since the last demo reset, so a fresh reset shows no ticks. The
step targets (demo zone, injected taps, legitimate homes) come from config/demo.yaml.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import psycopg
from psycopg.types.json import Jsonb

from voltguard import config, db

EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)
# Who performs each step and where it starts (the web app adds the language-specific narration).
STEPS = [
    {"step": 1, "role": "data_scientist", "user": "datasci", "page": "/models"},
    {"step": 2, "role": "analyst", "user": "analyst.cen", "page": "/zones/{zone}"},
    {"step": 3, "role": "analyst", "user": "analyst.cen", "page": "/zones/{zone}?premise={premise}"},
    {"step": 4, "role": "supervisor", "user": "supervisor.cen", "page": "/cases"},
    {"step": 5, "role": "inspector", "user": "{inspector}", "page": "/field"},
    {"step": 6, "role": "analyst", "user": "analyst.cen", "page": "/cases/{case}"},
    {"step": 7, "role": "data_scientist", "user": "datasci", "page": "/models"},
]
PREMISE_ROLES = {"analyst", "supervisor", "inspector", "admin", "data_scientist"}


def guide_config() -> dict[str, Any]:
    cfg = config.demo_config()
    g = cfg.get("demo_guide") or {}
    return {"zone": cfg.get("demo_zone", "TX-CEN-001"), "taps": list(g.get("taps") or []),
            "legitimate": list(g.get("legitimate") or []), "inspector": g.get("inspector", "inspector.b")}


def reset_time(conn: psycopg.Connection) -> datetime:
    row = conn.execute("SELECT value FROM setting WHERE key = 'demo_reset_at'").fetchone()
    if row and row["value"].get("at"):
        return datetime.fromisoformat(row["value"]["at"])
    return EPOCH


def status(conn: psycopg.Connection, role: str) -> dict[str, Any]:
    """Owner connection (reads the audit log and every table); returns booleans and demo targets only."""
    g = guide_config()
    zone, since = g["zone"], reset_time(conn)
    run_date = conn.execute("SELECT max(run_date) AS d FROM zone_run").fetchone()["d"]
    z = conn.execute("SELECT flagged, gap_since_start, gap_start, n_premises FROM zone_run WHERE transformer_id = %s AND run_date = %s",
                     (zone, run_date)).fetchone()
    ranks = {r["premise_id"]: r["rank"] for r in conn.execute(
        "SELECT premise_id, rank FROM premise_score WHERE transformer_id = %s AND run_date = %s", (zone, run_date)).fetchall()}
    top = min(ranks, key=ranks.get) if ranks else None
    top_k = max(1, -(-(z["n_premises"] if z else 0) * 5 // 100))

    def audited(action: str, target: str) -> bool:
        return bool(conn.execute("SELECT 1 FROM audit_log WHERE action = %s AND object_ref = %s AND ts >= %s LIMIT 1",
                                 (action, target, since)).fetchone())

    detection_done = bool(conn.execute(
        "SELECT 1 FROM job_run WHERE kind = 'run_detection' AND status = 'done' AND finished_at >= %s LIMIT 1", (since,)).fetchone())
    case = conn.execute(
        """SELECT c.case_id, c.assigned_analyst, c.status, d.status AS dispatch FROM inspection_case c
           LEFT JOIN dispatch_suggestion d USING (case_id)
           WHERE c.premise_id = %s AND c.case_id NOT LIKE 'H-%%' AND c.created_at >= %s ORDER BY c.created_at DESC LIMIT 1""",
        (top, since)).fetchone() if top else None
    outcome = conn.execute("SELECT max(recorded_at) AS at FROM inspection_outcome WHERE case_id = %s",
                           (case["case_id"],)).fetchone()["at"] if case else None
    exported = bool(case and conn.execute("SELECT 1 FROM case_report WHERE case_id = %s AND status = 'export_approved'",
                                          (case["case_id"],)).fetchone())
    retrained = bool(outcome and conn.execute("SELECT 1 FROM model_version WHERE trained_at >= %s LIMIT 1", (outcome,)).fetchone())
    sums = conn.execute("SELECT s.score, coalesce(sum(r.contribution), 0) AS lines FROM premise_score s LEFT JOIN score_reason r "
                        "ON r.premise_id = s.premise_id AND r.run_date = s.run_date WHERE s.premise_id = %s AND s.run_date = %s "
                        "GROUP BY s.score", (top, run_date)).fetchone() if top else None

    checks: list[Callable[[], bool]] = [
        lambda: detection_done and bool(z and z["flagged"]),
        lambda: (bool(g["taps"]) and all(ranks.get(p, 999) <= 3 for p in g["taps"])
                 and all(ranks.get(p, 999) > top_k for p in g["legitimate"]) and audited("zone.suspects.view", f"zone:{zone}")),
        lambda: bool(sums and abs(float(sums["lines"]) - sums["score"]) < 0.6 and audited("premise.view", f"premise:{top}")),
        lambda: bool(case and case["assigned_analyst"] and case["dispatch"] == "approved"),
        lambda: outcome is not None,
        lambda: exported,
        lambda: retrained,
    ]
    show_ids = role in PREMISE_ROLES
    steps = []
    for spec, check in zip(STEPS, checks):
        user = spec["user"].format(inspector=g["inspector"])
        steps.append({"step": spec["step"], "role": spec["role"], "user": user, "page": spec["page"], "done": bool(check())})
    return {"zone": zone, "premise": top if show_ids else None, "case": case["case_id"] if case and show_ids else None,
            "since": since.isoformat() if since != EPOCH else None, "run_date": run_date, "steps": steps}


def accounts() -> list[dict[str, Any]]:
    """Test accounts for the role picker (no passwords)."""
    return [{k: u.get(k) for k in ("user_id", "role", "region", "team")} for u in config.demo_config().get("users", [])]


def reset(actor: str, progress: Callable[[str], None]) -> dict[str, Any]:
    """Reset rehearsal cases, rerun detection and reseed the demo kit (target: under 30 s)."""
    import time

    from voltguard.service import demo, pipeline, seed

    started = time.time()
    with db.admin_connection() as conn:     # this job's own row survives the reset
        row = conn.execute("SELECT max(job_id) AS id FROM job_run WHERE kind = 'demo_reset' AND status = 'running'").fetchone()
    job_id = row["id"] if row else None
    progress("Removing cases from earlier rehearsals...")
    counts = demo.reset_rehearsal(keep_job=job_id)
    progress("Running detection...")
    pipeline.run_detection(actor, progress=progress)
    progress("Seeding the demo kit...")
    seed.seed_demo_content(progress=lambda m: None)
    with db.admin_connection() as conn:
        with conn.transaction():
            conn.execute("INSERT INTO setting (key, value, changed_by) VALUES ('demo_reset_at', %s, %s) "
                         "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, changed_by = EXCLUDED.changed_by, changed_at = now()",
                         (Jsonb({"at": datetime.now(timezone.utc).isoformat()}), actor))
    return {"removed": counts, "seconds": round(time.time() - started, 1)}
