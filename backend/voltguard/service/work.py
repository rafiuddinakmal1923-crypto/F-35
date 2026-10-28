""""My work" (role home pages): what each role should act on next, in their region.

Counts and short lists only, each item linking to the page where the action happens; the actions
themselves stay in the case, report and dispatch services. Runs on the caller's connection.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import psycopg

from voltguard.db import Caller
from voltguard.service import settings


def _item(kind: str, title: str, link: str, detail: str = "", urgent: bool = False) -> dict:
    return {"kind": kind, "title": title, "link": link, "detail": detail, "urgent": urgent}


def for_caller(conn: psycopg.Connection, caller: Caller) -> dict:
    now = datetime.now(timezone.utc)
    cfg = settings.thresholds(conn)["dispatch"]
    sections: list[dict] = []
    if caller.role == "analyst":
        unclaimed = conn.execute("""SELECT case_id, premise_id, transformer_id, score_at_creation FROM inspection_case
                                    WHERE assigned_analyst IS NULL AND status <> 'closed' AND origin <> 'random_sample'
                                    ORDER BY score_at_creation DESC NULLS LAST, case_id LIMIT 8""").fetchall()
        mine = conn.execute("""SELECT case_id, premise_id, status FROM inspection_case WHERE assigned_analyst = %s AND status <> 'closed'
                               ORDER BY case_id""", (caller.user_id,)).fetchall()
        drafts = conn.execute("""SELECT r.report_id, r.case_id FROM case_report r JOIN inspection_case c USING (case_id)
                                 WHERE r.status = 'draft' AND c.assigned_analyst = %s ORDER BY r.created_at""", (caller.user_id,)).fetchall()
        sections = [
            {"key": "reports", "title": "Reports to approve", "items": [
                _item("report", f"Report {r['report_id']}", f"/cases/{r['case_id']}", f"case {r['case_id']}: approve the content", True) for r in drafts]},
            {"key": "unclaimed", "title": "Cases to claim", "items": [
                _item("case", c["case_id"], f"/cases/{c['case_id']}", f"{c['premise_id']} · {c['transformer_id']} · score {c['score_at_creation']}")
                for c in unclaimed]},
            {"key": "mine", "title": "My open cases", "items": [
                _item("case", c["case_id"], f"/cases/{c['case_id']}", f"{c['premise_id']} · {c['status']}") for c in mine]},
        ]
    elif caller.role == "supervisor":
        pending = conn.execute("""SELECT s.case_id, s.suggested_team, s.distance_km, s.joint_operation FROM dispatch_suggestion s
                                  JOIN inspection_case c USING (case_id) WHERE s.status = 'pending' AND c.status = 'new'
                                  ORDER BY s.case_id""").fetchall()
        unassigned = conn.execute("""SELECT c.case_id, c.premise_id FROM inspection_case c LEFT JOIN dispatch_suggestion s USING (case_id)
                                     WHERE c.status = 'new' AND (s.case_id IS NULL OR s.status = 'rejected') ORDER BY c.case_id""").fetchall()
        overdue = conn.execute("""SELECT case_id, assigned_team, assigned_at FROM inspection_case WHERE status = 'assigned'
                                  AND assigned_at < %s ORDER BY assigned_at""", (now - timedelta(hours=cfg["reminder_hours"]),)).fetchall()
        declined = conn.execute("""SELECT DISTINCT case_id FROM case_event WHERE event_type = 'declined'
                                   AND case_id IN (SELECT case_id FROM inspection_case WHERE status = 'assigned')""").fetchall()
        teams = conn.execute("""SELECT t.team_id, t.name, count(c.case_id) FILTER (WHERE c.status = 'assigned') AS open_visits
                                FROM team t LEFT JOIN inspection_case c ON c.assigned_team = t.team_id GROUP BY t.team_id, t.name
                                ORDER BY t.team_id""").fetchall()
        sections = [
            {"key": "suggestions", "title": "Dispatch suggestions to approve", "items": [
                _item("dispatch", p["case_id"], f"/cases/{p['case_id']}",
                      f"{p['suggested_team']}, {p['distance_km']} km" + (" · joint operation" if p["joint_operation"] else ""), True) for p in pending]},
            {"key": "declined", "title": "Teams that cannot attend", "items": [
                _item("case", d["case_id"], f"/cases/{d['case_id']}", "reassign", True) for d in declined]},
            {"key": "overdue", "title": "Overdue visits", "items": [
                _item("case", o["case_id"], f"/cases/{o['case_id']}", f"{o['assigned_team']} · assigned {o['assigned_at']:%d %b %H:%M}", True) for o in overdue]},
            {"key": "unassigned", "title": "New cases without a team", "items": [
                _item("case", u["case_id"], f"/cases/{u['case_id']}", u["premise_id"]) for u in unassigned]},
            {"key": "teams", "title": "Teams", "items": [
                _item("team", f"{t['name']} ({t['team_id']})", "/dispatch", f"{t['open_visits']} visit(s) waiting") for t in teams]},
        ]
    elif caller.role == "manager":
        exports = conn.execute("""SELECT report_id, case_id FROM case_report WHERE status = 'content_approved' ORDER BY content_approved_at""").fetchall()
        alerts = conn.execute("SELECT count(*) AS n FROM alert WHERE acknowledged_by IS NULL AND region IN (%s, '*')", (caller.region,)).fetchone()["n"]
        sections = [
            {"key": "exports", "title": "Reports waiting for your export approval", "items": [
                _item("report", f"Report {e['report_id']}", f"/cases/{e['case_id']}", f"case {e['case_id']}", True) for e in exports]},
            {"key": "alerts", "title": "Data and model alerts", "items": [
                _item("alert", f"{alerts} open alert(s)", "/models", "missing data or drift")] if alerts else []},
        ]
    counts = {s["key"]: len(s["items"]) for s in sections}
    urgent = sum(1 for s in sections for i in s["items"] if i["urgent"])
    return {"role": caller.role, "sections": sections, "counts": counts, "urgent": urgent}
