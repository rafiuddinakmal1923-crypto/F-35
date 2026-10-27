"""Dispatch and reminder agent (SDD 8.1, FR-AG-02).

Tools allowed: read the case summary, the duty roster and team locations; send a message.
It suggests the nearest on-duty team to the case's transformer (zone-level location; the
premise's exact location is not needed), recommends a joint operation with police when the
hidden load is large or flat 24/7, and the supervisor approves or changes the suggestion.
Overdue cases get a reminder to the team and then an escalation to the region's supervisors,
on shortened timers in demo mode. It has no tool to contact customers, disconnect supply or
contact external agencies (FR-AG-06).
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone

import psycopg

from voltguard import config, db
from voltguard.service import notify, settings

TOOLS = ("read_case_summary", "read_duty_roster", "read_team_locations", "send_message")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def roster_date(conn: psycopg.Connection, region: str, today: date | None = None) -> date | None:
    """Today's shift if the roster covers it, else the latest shift on record (simulated roster)."""
    today = today or date.today()
    row = conn.execute("SELECT max(shift_date) AS d FROM duty_roster WHERE region = %s AND shift_date <= %s", (region, today)).fetchone()
    return row["d"] if row else None


def suggest(conn: psycopg.Connection, case_id: str) -> dict | None:
    """Create the dispatch suggestion for a new case (owner connection; called by the case service)."""
    case = conn.execute(
        """SELECT c.case_id, c.region, c.transformer_id, t.lat, t.lon, z.priority, z.flatness_cv, z.gap_kwh_recent
           FROM inspection_case c JOIN transformer t USING (transformer_id)
           LEFT JOIN LATERAL (SELECT priority, flatness_cv, gap_kwh_recent FROM zone_run zr WHERE zr.transformer_id = c.transformer_id
                              ORDER BY run_date DESC LIMIT 1) z ON true
           WHERE c.case_id = %s""", (case_id,)).fetchone()
    if not case or case["lat"] is None:
        return None
    shift = roster_date(conn, case["region"])
    teams = conn.execute("SELECT team_id, base_lat, base_lon FROM duty_roster WHERE region = %s AND shift_date = %s AND on_duty",
                         (case["region"], shift)).fetchall() if shift else []
    if not teams:
        return None
    ranked = sorted(((haversine_km(case["lat"], case["lon"], t["base_lat"], t["base_lon"]), t["team_id"]) for t in teams))
    distance, team = ranked[0]
    flat_cv = settings.thresholds(conn)["zone"]["flat_cv"]
    joint = case["priority"] == "large_load" or (case["flatness_cv"] is not None and case["flatness_cv"] < flat_cv)
    rationale = f"Nearest on-duty team to the transformer ({distance:.1f} km; roster of {shift})."
    if joint:
        rationale += " The hidden load is large or flat 24/7 (likely mining rigs): plan a joint operation with police, not a lone inspector."
    conn.execute("""INSERT INTO dispatch_suggestion (case_id, region, suggested_team, distance_km, joint_operation, rationale)
                    VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (case_id) DO NOTHING""",
                 (case_id, case["region"], team, round(distance, 2), joint, rationale))
    db.audit(conn, "agent:dispatch", "agent.dispatch.suggest", f"case:{case_id}", {"team": team, "joint_operation": joint})
    return {"case_id": case_id, "suggested_team": team, "distance_km": round(distance, 2), "joint_operation": joint, "rationale": rationale}


def _timers(cfg: dict) -> tuple[timedelta, timedelta]:
    d = cfg["dispatch"]
    if config.demo_mode():
        return timedelta(minutes=d["demo_reminder_minutes"]), timedelta(minutes=d["demo_escalation_minutes"])
    return timedelta(hours=d["reminder_hours"]), timedelta(hours=d["escalation_hours"])


def run_reminders(now: datetime | None = None) -> list[dict]:
    """Scheduler job: remind the team about overdue assigned cases, then escalate to the supervisors."""
    now = now or datetime.now(timezone.utc)
    sent = []
    with db.admin_connection() as conn:
        with conn.transaction():
            reminder, escalation = _timers(settings.thresholds(conn))
            overdue = conn.execute(
                """SELECT case_id, region, assigned_team, assigned_at, reminded_at, escalated_at FROM inspection_case
                   WHERE status = 'assigned' AND assigned_at IS NOT NULL AND (reminded_at IS NULL OR escalated_at IS NULL)
                   ORDER BY assigned_at""").fetchall()
            for c in overdue:
                age = now - c["assigned_at"]
                if age >= escalation and c["escalated_at"] is None:
                    for sup in conn.execute("SELECT user_id FROM app_user WHERE role = 'supervisor' AND region = %s AND active",
                                            (c["region"],)).fetchall():
                        sent.append(notify.send(conn, "escalation", c["case_id"], c["region"], sup["user_id"],
                                                f"Not visited {int(age.total_seconds() // 60)} minutes after assignment."))
                    conn.execute("UPDATE inspection_case SET escalated_at = %s, reminded_at = coalesce(reminded_at, %s) WHERE case_id = %s",
                                 (now, now, c["case_id"]))
                    conn.execute("INSERT INTO case_event (case_id, region, actor, event_type, detail) VALUES (%s, %s, 'agent:dispatch', 'escalated', NULL)",
                                 (c["case_id"], c["region"]))
                    db.audit(conn, "agent:dispatch", "agent.dispatch.escalate", f"case:{c['case_id']}", None)
                elif age >= reminder and c["reminded_at"] is None:
                    sent.append(notify.send(conn, "reminder", c["case_id"], c["region"], c["assigned_team"]))
                    conn.execute("UPDATE inspection_case SET reminded_at = %s WHERE case_id = %s", (now, c["case_id"]))
                    conn.execute("INSERT INTO case_event (case_id, region, actor, event_type, detail) VALUES (%s, %s, 'agent:dispatch', 'reminded', NULL)",
                                 (c["case_id"], c["region"]))
                    db.audit(conn, "agent:dispatch", "agent.dispatch.remind", f"case:{c['case_id']}", None)
    return sent
