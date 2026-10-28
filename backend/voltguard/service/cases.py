"""Case service (SDD 6.2, FR-IW-01-05): cases, claims, assignment, outcomes and status history.

Statuses: new -> assigned -> visited -> reporting -> closed. False alarm or Inconclusive close
the case; Confirmed theft moves it to Reporting until the report is exported; No access returns
it to Assigned for a revisit and is not a training label. Only a supervisor assigns. Every
change writes a case_event and an audit row. Runs on the caller's connection, so region limits
apply in the database too.
"""

from __future__ import annotations

import random
from datetime import datetime

from psycopg.types.json import Jsonb

from voltguard import db, storage
from voltguard.agents import scrubber
from voltguard.db import Caller
from voltguard.service import notify, settings

OPEN = ("new", "assigned", "visited", "reporting")
OUTCOMES = ("confirmed_theft", "false_alarm", "inconclusive", "no_access")
ROUTINE_LABEL = "Routine meter check"
SAFETY_CHECKLIST = [
    "Check the meter board for exposed or heated cables before touching anything.",
    "Do not cut, move or disconnect cables yourself; record and photograph them.",
    "For a suspected mining site or large hidden load, wait for the police and the joint-operation team.",
    "[TNB procedure: to be supplied] Follow the utility's evidence-handling procedure for seals and photos.",
]


class CaseError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def _forbidden(message: str) -> CaseError:
    return CaseError(403, "forbidden", message)


def _event(conn, case: dict, actor: str, kind: str, detail: dict | None = None) -> None:
    conn.execute("INSERT INTO case_event (case_id, region, actor, event_type, detail) VALUES (%s, %s, %s, %s, %s)",
                 (case["case_id"], case["region"], actor, kind, Jsonb(detail) if detail else None))


def _case(conn, case_id: str, lock: bool = False) -> dict:
    row = conn.execute("SELECT * FROM inspection_case WHERE case_id = %s" + (" FOR UPDATE" if lock else ""), (case_id,)).fetchone()
    if not row:
        raise CaseError(404, "not_found", "Case not found in your region")
    return row


def _new_case_id(conn) -> str:
    n = conn.execute("SELECT nextval('case_seq') AS n").fetchone()["n"]
    return f"C-{datetime.now().year}-{n:04d}"


def _open_case_premises(conn) -> set[str]:
    return {r["premise_id"] for r in conn.execute("SELECT premise_id FROM inspection_case WHERE status <> 'closed'")}


def _insert_case(conn, caller: Caller, premise: dict, origin: str, score: int | None) -> dict:
    case_id = _new_case_id(conn)
    analyst = caller.user_id if caller.role == "analyst" else None
    case = conn.execute(
        """INSERT INTO inspection_case (case_id, premise_id, transformer_id, region, origin, status, score_at_creation,
                                        assigned_analyst, created_by)
           VALUES (%s, %s, %s, %s, %s, 'new', %s, %s, %s) RETURNING *""",
        (case_id, premise["premise_id"], premise["transformer_id"], premise["region"], origin, score, analyst, caller.user_id)).fetchone()
    _event(conn, case, caller.user_id, "created", {"origin": origin, "score": score})
    db.audit(conn, caller.user_id, "case.create", f"case:{case_id}", {"origin": origin, "premise_id": premise["premise_id"]})
    from voltguard.agents import dispatch

    suggestion = dispatch.suggest(conn, case_id)
    if suggestion:
        _event(conn, case, "agent:dispatch", "dispatch_suggested", suggestion)
        # The supervisor approves or rejects from the message (Telegram or the in-app chat).
        joint = "; joint operation with police" if suggestion["joint_operation"] else ""
        for sup in conn.execute("SELECT user_id FROM app_user WHERE role = 'supervisor' AND region = %s AND active",
                                (case["region"],)).fetchall():
            notify.send(conn, "suggestion", case_id, case["region"], sup["user_id"],
                        f"Nearest on-duty team {suggestion['suggested_team']}, {suggestion['distance_km']} km{joint}.")
    return case


# --------------------------------------------------------------------------- creation

def create_cases_job(conn, caller: Caller, rng: random.Random | None = None) -> dict:
    """POST /jobs/create-cases: threshold cases plus a random sample (FR-IW-01, FR-IW-05). Runs after scoring."""
    if caller.role not in ("pipeline", "supervisor"):
        raise _forbidden("Only the pipeline service account or a supervisor runs the case job")
    cfg = settings.thresholds(conn)["cases"]
    rng = rng or random.SystemRandom()
    run_date = conn.execute("SELECT max(run_date) AS d FROM zone_run").fetchone()["d"]
    if run_date is None:
        raise CaseError(409, "no_detection", "Run detection first")
    open_premises = _open_case_premises(conn)
    created: list[dict] = []
    zones = conn.execute("SELECT transformer_id, flagged, balance_available FROM zone_run WHERE run_date = %s AND scored ORDER BY transformer_id",
                         (run_date,)).fetchall()
    for z in zones:
        rows = conn.execute(
            """SELECT s.premise_id, s.score, p.transformer_id, p.region FROM premise_score s JOIN premise p USING (premise_id)
               WHERE s.transformer_id = %s AND s.run_date = %s AND s.score >= %s ORDER BY s.rank""",
            (z["transformer_id"], run_date, cfg["case_threshold"])).fetchall()
        picked = 0
        for r in rows:
            if picked >= cfg["max_cases_per_zone"]:
                break
            if r["premise_id"] in open_premises:
                continue
            case = _insert_case(conn, caller, r, "model", r["score"])
            open_premises.add(r["premise_id"])
            created.append({"case_id": case["case_id"], "premise_id": r["premise_id"], "origin": "model", "zone": z["transformer_id"]})
            picked += 1
    # Random sample: uniform over ALL premises in flagged zones, regardless of score, excluding open cases.
    flagged = [z["transformer_id"] for z in zones if z["flagged"]]
    per_zone = int(cfg["random_sample_per_zone"])
    sample = []
    for tx in flagged:
        pool = [r for r in conn.execute("SELECT premise_id, transformer_id, region FROM premise WHERE transformer_id = %s ORDER BY premise_id",
                                        (tx,)).fetchall() if r["premise_id"] not in open_premises]
        for r in rng.sample(pool, min(per_zone, len(pool))):
            case = _insert_case(conn, caller, r, "random_sample", None)
            open_premises.add(r["premise_id"])
            sample.append({"case_id": case["case_id"], "premise_id": r["premise_id"], "origin": "random_sample", "zone": tx})
    db.audit(conn, caller.user_id, "job.create_cases", f"run_date:{run_date}", {"model": len(created), "random_sample": len(sample)})
    return {"run_date": run_date, "model_cases": created, "random_sample_cases": sample}


def create_manual(conn, caller: Caller, premise_id: str, reason: str | None = None) -> dict:
    if caller.role not in ("analyst", "supervisor"):
        raise _forbidden("Only an analyst or a supervisor creates a case manually")
    premise = conn.execute("SELECT premise_id, transformer_id, region FROM premise WHERE premise_id = %s", (premise_id,)).fetchone()
    if not premise:
        raise CaseError(404, "not_found", "Premise not found in your region")
    if premise["premise_id"] in _open_case_premises(conn):
        raise CaseError(409, "conflict", "This premise already has an open case")
    score = conn.execute("SELECT score FROM premise_score WHERE premise_id = %s ORDER BY run_date DESC LIMIT 1", (premise_id,)).fetchone()
    case = _insert_case(conn, caller, premise, "manual", score["score"] if score else None)
    if reason:
        _event(conn, case, caller.user_id, "note", {"reason": scrubber.scrub(reason).text})
    return case


def claim(conn, caller: Caller, case_id: str) -> dict:
    """An analyst claims a pipeline-created case and becomes its assigned analyst (runs alongside dispatch)."""
    if caller.role != "analyst":
        raise _forbidden("Only an analyst claims a case")
    case = _case(conn, case_id, lock=True)
    if case["status"] not in OPEN:
        raise CaseError(409, "conflict", "The case is closed")
    if case["assigned_analyst"] and case["assigned_analyst"] != caller.user_id:
        raise CaseError(409, "conflict", f"Already claimed by {case['assigned_analyst']}")
    case = conn.execute("UPDATE inspection_case SET assigned_analyst = %s WHERE case_id = %s RETURNING *", (caller.user_id, case_id)).fetchone()
    _event(conn, case, caller.user_id, "claimed", None)
    db.audit(conn, caller.user_id, "case.claim", f"case:{case_id}", None)
    return case


# --------------------------------------------------------------------------- assignment (supervisor only)

def _close_buttons(conn, case_id: str, kinds: tuple[str, ...], actor: str, action: str) -> None:
    """A decision taken anywhere (case page, phone, Telegram) closes the matching chat messages' buttons."""
    conn.execute("UPDATE notification SET answered_by = %s, answered_action = %s, answered_at = now() "
                 "WHERE case_id = %s AND kind = ANY(%s) AND answered_by IS NULL AND buttons IS NOT NULL",
                 (actor, action, case_id, list(kinds)))


def _assign(conn, caller: Caller, case: dict, team: str, via: str) -> dict:
    team_row = conn.execute("SELECT team_id, region FROM team WHERE team_id = %s", (team,)).fetchone()
    if not team_row or team_row["region"] != case["region"]:
        raise CaseError(400, "bad_request", "Unknown team for this region")
    if case["status"] not in ("new", "assigned"):
        raise CaseError(409, "conflict", f"A case in status '{case['status']}' cannot be (re)assigned")
    joint = conn.execute("SELECT joint_operation FROM dispatch_suggestion WHERE case_id = %s", (case["case_id"],)).fetchone()
    case = conn.execute("""UPDATE inspection_case SET assigned_team = %s, status = 'assigned', assigned_at = now(), reminded_at = NULL,
                           escalated_at = NULL, joint_operation = %s WHERE case_id = %s RETURNING *""",
                        (team, bool(joint and joint["joint_operation"]), case["case_id"])).fetchone()
    _event(conn, case, caller.user_id, "assigned", {"team": team, "via": via})
    if via == "direct":   # a direct assignment settles a pending suggestion's message too
        _close_buttons(conn, case["case_id"], ("suggestion",), caller.user_id, "assigned")
    db.audit(conn, caller.user_id, "case.assign", f"case:{case['case_id']}", {"team": team, "via": via})
    notify.send(conn, "assignment", case["case_id"], case["region"], team,
                "Joint operation with police." if case["joint_operation"] else "")
    return case


def decide_suggestion(conn, caller: Caller, case_id: str, approve: bool, team: str | None = None) -> dict:
    if caller.role != "supervisor":
        raise _forbidden("Only a supervisor approves dispatch suggestions")
    case = _case(conn, case_id, lock=True)
    suggestion = conn.execute("SELECT * FROM dispatch_suggestion WHERE case_id = %s", (case_id,)).fetchone()
    if not suggestion:
        raise CaseError(404, "not_found", "No dispatch suggestion for this case")
    if suggestion["status"] != "pending":
        raise CaseError(409, "conflict", f"Suggestion already {suggestion['status']}")
    conn.execute("UPDATE dispatch_suggestion SET status = %s, decided_by = %s, decided_at = now() WHERE case_id = %s",
                 ("approved" if approve else "rejected", caller.user_id, case_id))
    db.audit(conn, caller.user_id, "dispatch.approve" if approve else "dispatch.reject", f"case:{case_id}",
             {"suggested_team": suggestion["suggested_team"], "assigned_team": team})
    _close_buttons(conn, case_id, ("suggestion",), caller.user_id, "approve" if approve else "reject")
    if approve:
        return _assign(conn, caller, case, team or suggestion["suggested_team"], "dispatch_suggestion")
    _event(conn, case, caller.user_id, "dispatch_rejected", None)
    return case


def assign(conn, caller: Caller, case_id: str, team: str) -> dict:
    if caller.role != "supervisor":
        raise _forbidden("Only a supervisor assigns a case")
    return _assign(conn, caller, _case(conn, case_id, lock=True), team, "direct")


# --------------------------------------------------------------------------- field work (assigned inspector)

def _require_assigned_inspector(caller: Caller, case: dict) -> None:
    if caller.role != "inspector" or not case["assigned_team"] or case["assigned_team"] != caller.team:
        raise _forbidden("Only an inspector of the assigned team records this")


def add_photo(conn, caller: Caller, case_id: str, data: bytes, content_type: str) -> str:
    case = _case(conn, case_id)
    _require_assigned_inspector(caller, case)
    if content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise CaseError(400, "bad_request", "Photos must be JPEG, PNG or WebP")
    key = storage.put("photos", data, {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[content_type])
    _event(conn, case, caller.user_id, "photo_added", {"photo_key": key})
    db.audit(conn, caller.user_id, "case.photo", f"case:{case_id}", {"photo_key": key})
    return key


def _known_details(premise_id: str) -> list[str]:
    """The case's own holder name and address, so the scrubber removes them even when no pattern matches."""
    with db.admin_connection() as conn:
        row = conn.execute("SELECT holder_name, address FROM customer_pii WHERE premise_id = %s", (premise_id,)).fetchone()
    return [row["holder_name"], row["address"]] if row else []


def record_outcome(conn, caller: Caller, case_id: str, outcome: str, notes: str | None = None, reason_tag: str | None = None,
                   photo_keys: list[str] | None = None, client_ref: str | None = None) -> dict:
    """Record a visit (FR-IW-02-04). Notes are scrubbed into notes_redacted; only that ever reaches agents."""
    if outcome not in OUTCOMES:
        raise CaseError(400, "bad_request", f"Outcome must be one of {', '.join(OUTCOMES)}")
    if client_ref:
        existing = conn.execute("SELECT case_id, visit_no FROM inspection_outcome WHERE client_ref = %s", (client_ref,)).fetchone()
        if existing:   # an offline submission synced twice
            return {"case": _case(conn, existing["case_id"]), "visit_no": existing["visit_no"], "duplicate": True}
    case = _case(conn, case_id, lock=True)
    _require_assigned_inspector(caller, case)
    if case["status"] != "assigned":
        raise CaseError(409, "conflict", f"Outcomes are recorded on assigned cases; this one is '{case['status']}'")
    keys = list(photo_keys or [])
    if any(not storage.exists("photos", k) for k in keys):
        raise CaseError(400, "bad_request", "Unknown photo key")
    redacted = scrubber.scrub(notes, known=_known_details(case["premise_id"])) if notes else None
    visit = conn.execute("SELECT coalesce(max(visit_no), 0) + 1 AS n FROM inspection_outcome WHERE case_id = %s", (case_id,)).fetchone()["n"]
    conn.execute("""INSERT INTO inspection_outcome (case_id, visit_no, region, outcome, reason_tag, notes, notes_redacted, photo_keys,
                                                    recorded_by, client_ref) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                 (case_id, visit, case["region"], outcome, reason_tag, notes, redacted.text if redacted else None, keys, caller.user_id, client_ref))
    conn.execute("UPDATE inspection_case SET status = 'visited' WHERE case_id = %s", (case_id,))
    _close_buttons(conn, case_id, ("assignment", "reminder"), caller.user_id, "visited")
    _event(conn, case, caller.user_id, "visited", {"visit_no": visit})
    new_status = {"confirmed_theft": "reporting", "false_alarm": "closed", "inconclusive": "closed", "no_access": "assigned"}[outcome]
    case = conn.execute("UPDATE inspection_case SET status = %s, closed_at = CASE WHEN %s = 'closed' THEN now() END, "
                        "assigned_at = CASE WHEN %s = 'assigned' THEN now() ELSE assigned_at END, "
                        "reminded_at = CASE WHEN %s = 'assigned' THEN NULL ELSE reminded_at END, "
                        "escalated_at = CASE WHEN %s = 'assigned' THEN NULL ELSE escalated_at END "
                        "WHERE case_id = %s RETURNING *", (new_status, new_status, new_status, new_status, new_status, case_id)).fetchone()
    _event(conn, case, caller.user_id, f"outcome:{outcome}", {"visit_no": visit, "status": new_status,
                                                              "training_label": outcome != "no_access",
                                                              "redactions": redacted.found if redacted else {}})
    db.audit(conn, caller.user_id, "case.outcome", f"case:{case_id}", {"outcome": outcome, "visit_no": visit, "status": new_status})
    if outcome == "no_access":
        for sup in conn.execute("SELECT user_id FROM app_user WHERE role = 'supervisor' AND region = %s AND active", (case["region"],)).fetchall():
            notify.send(conn, "no_access", case_id, case["region"], sup["user_id"])
    report = None
    if outcome == "confirmed_theft":
        try:
            from voltguard.agents import report as report_agent
        except ImportError:
            report_agent = None
        if report_agent is not None:
            report = report_agent.draft_for_case(conn, Caller("agent:report", "analyst", case["region"]), case_id, trigger="confirmed_theft")
    return {"case": case, "visit_no": visit, "duplicate": False, "report_id": report["report_id"] if report else None}


# --------------------------------------------------------------------------- reading

def list_cases(conn, caller: Caller, status: str | None = None, team: str | None = None, limit: int = 100,
               cursor: str | None = None) -> list[dict]:
    where, params = ["(%s::text IS NULL OR c.status = %s)", "(%s::text IS NULL OR c.assigned_team = %s)",
                     "(%s::text IS NULL OR c.case_id > %s)"], [status, status, team, team, cursor, cursor]
    if caller.role == "analyst":
        where.append("(c.assigned_analyst = %s OR (c.assigned_analyst IS NULL AND c.status <> 'closed'))")
        params.append(caller.user_id)
    elif caller.role == "inspector":
        where.append("c.status IN ('assigned', 'visited') AND c.assigned_team = %s")
        params.append(caller.team)
    elif caller.role not in ("supervisor", "manager"):
        raise _forbidden("Your role has no case list")
    rows = conn.execute(
        f"""SELECT c.case_id, c.premise_id, c.transformer_id, c.region, c.origin, c.status, c.score_at_creation, c.assigned_analyst,
                   c.assigned_team, c.created_by, c.created_at, c.assigned_at, c.closed_at, c.joint_operation,
                   d.suggested_team, d.status AS suggestion_status, d.joint_operation AS suggested_joint
            FROM inspection_case c LEFT JOIN dispatch_suggestion d USING (case_id)
            WHERE {' AND '.join(where)} ORDER BY c.case_id LIMIT %s""", (*params, limit)).fetchall()
    if caller.role == "inspector":
        rows = [inspector_view(conn, caller, r) for r in rows]
    return rows


SOLAR_CHECKLIST = ("panels_inverter_seen", "inverter_total_vs_expected", "registration_seen", "wiring_before_meter")
SOLAR_REASON_TAGS = {"false_alarm": "solar_confirmed_no_theft", "confirmed_theft": "solar_plus_bypass"}


def _solar_visit(conn, premise_id: str) -> dict | None:
    """Rooftop-solar items for the visit (Solar brief 4): the checklist keys (worded on the phone in English or
    Bahasa Melayu), the registered capacity and the daily generation the scorer expected, for comparison with
    the inverter's own reading. None when the home shows no sign of solar."""
    row = conn.execute(
        """SELECT f.tags, f.details->'solar' AS solar FROM premise_feature f
           WHERE f.premise_id = %s ORDER BY f.run_date DESC LIMIT 1""", (premise_id,)).fetchone()
    s = (row or {}).get("solar") or {}
    if not row or not ("solar" in (row["tags"] or []) or s.get("registered") or s.get("export")):
        return None
    budget = s.get("budget") or {}
    return {"checklist": list(SOLAR_CHECKLIST), "registered": bool(s.get("registered")),
            "capacity_kwp": s.get("capacity_kwp"), "has_battery": bool(s.get("has_battery")),
            "expected_kwh_per_day": budget.get("expected_kwh"), "psh_source": budget.get("psh_source"),
            "reason_tags": SOLAR_REASON_TAGS}


def inspector_view(conn, caller: Caller, case: dict) -> dict:
    """What the phone keeps offline: address, top reasons (model cases) and the safety checklist.

    Random-sample visits are presented as routine meter checks without scores or reasons.
    """
    contact = conn.execute("SELECT * FROM vg_case_contact(%s)", (case["case_id"],)).fetchone()
    view = {"case_id": case["case_id"], "premise_id": case["premise_id"], "status": case["status"],
            "joint_operation": case["joint_operation"], "contact": dict(contact) if contact else None,
            "safety_checklist": SAFETY_CHECKLIST}
    view["solar"] = _solar_visit(conn, case["premise_id"])
    if case["origin"] == "random_sample":
        view.update({"label": ROUTINE_LABEL, "reasons": []})
    else:
        reasons = conn.execute(
            """SELECT feature, contribution, reason_text FROM score_reason WHERE premise_id = %s
               AND run_date = (SELECT max(run_date) FROM score_reason WHERE premise_id = %s)
               AND feature NOT IN ('other', 'capped') ORDER BY rank LIMIT 3""", (case["premise_id"], case["premise_id"])).fetchall()
        view.update({"label": "Inspection", "reasons": reasons})
    return view


def case_detail(conn, caller: Caller, case_id: str) -> dict:
    case = _case(conn, case_id)
    if caller.role == "analyst" and case["assigned_analyst"] not in (None, caller.user_id):
        raise _forbidden("Analysts see their own cases")
    if caller.role == "inspector":
        _require_assigned_inspector(caller, case)
    if caller.role not in ("analyst", "supervisor", "inspector", "manager"):
        raise _forbidden("Your role cannot open cases")
    events = conn.execute("SELECT ts, actor, event_type, detail FROM case_event WHERE case_id = %s ORDER BY event_id", (case_id,)).fetchall()
    outcomes = conn.execute("SELECT visit_no, outcome, reason_tag, notes_redacted, photo_keys, recorded_by, recorded_at "
                            "FROM inspection_outcome WHERE case_id = %s ORDER BY visit_no", (case_id,)).fetchall()
    suggestion = conn.execute("SELECT suggested_team, distance_km, joint_operation, rationale, status, decided_by FROM dispatch_suggestion "
                              "WHERE case_id = %s", (case_id,)).fetchone()
    reports = conn.execute("SELECT report_id, status, created_at, content_approved_by, content_approved_at, export_approved_by, export_approved_at, pdf_key IS NOT NULL AS has_pdf "
                           "FROM case_report WHERE case_id = %s ORDER BY created_at", (case_id,)).fetchall()
    contact = None
    if caller.role in ("analyst", "supervisor", "inspector"):
        row = conn.execute("SELECT * FROM vg_case_contact(%s)", (case_id,)).fetchone()
        contact = dict(row) if row else None
    db.audit(conn, caller.user_id, "case.view", f"case:{case_id}", {"personal_details_shown": contact is not None})
    detail = {"case": case, "events": events, "outcomes": outcomes, "dispatch_suggestion": suggestion, "reports": reports,
              "contact": contact, "masked": contact is None}
    if caller.role == "inspector":
        detail["field"] = inspector_view(conn, caller, case)
    return detail
