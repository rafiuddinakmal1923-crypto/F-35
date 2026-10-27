"""Case endpoints (SDD 7; FR-IW-01-05, FR-AG-02). The case service holds every rule; this maps HTTP to it."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from voltguard import db, storage
from voltguard.api.deps import ApiError, connection, forbidden, not_found, require
from voltguard.db import Caller
from voltguard.service import cases, jobs

router = APIRouter(tags=["cases"])


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except cases.CaseError as exc:
        raise ApiError(exc.status, exc.code, exc.message) from exc


class NewCase(BaseModel):
    premise_id: str
    reason: str | None = Field(None, max_length=1000)


class Decision(BaseModel):
    approve: bool
    team: str | None = None


class Assignment(BaseModel):
    team: str


class Outcome(BaseModel):
    outcome: Literal["confirmed_theft", "false_alarm", "inconclusive", "no_access"]
    notes: str | None = Field(None, max_length=4000)
    reason_tag: str | None = Field(None, max_length=60)
    photo_keys: list[str] = []
    client_ref: str | None = Field(None, max_length=64)


@router.post("/jobs/create-cases", tags=["jobs"])
def create_cases(wait: bool = True, c: Caller = Depends(require("pipeline", "supervisor"))):
    """The case job (runs after scoring): threshold cases plus the random sample."""
    def run(progress):
        with db.app_connection(c) as conn:
            result = _call(cases.create_cases_job, conn, c)
        return {"run_date": str(result["run_date"]), "model_cases": result["model_cases"], "random_sample_cases": result["random_sample_cases"]}
    job_id = jobs.submit("create_cases", c.user_id, run, wait=wait)
    with db.app_connection(c) as conn:
        return {"job_id": job_id, **(jobs.status(conn, job_id) or {})}


@router.post("/cases")
def create_case(body: NewCase, c: Caller = Depends(require("analyst", "supervisor")), conn=Depends(connection)):
    return _call(cases.create_manual, conn, c, body.premise_id, body.reason)


@router.get("/cases")
def list_cases(status: str | None = None, team: str | None = None, limit: int = Query(100, le=500), cursor: str | None = None,
               c: Caller = Depends(require("supervisor", "analyst", "inspector", "manager")), conn=Depends(connection)):
    rows = _call(cases.list_cases, conn, c, status, team, limit, cursor)
    return {"cases": rows, "next_cursor": rows[-1]["case_id"] if len(rows) == limit else None}


@router.get("/cases/{case_id}")
def get_case(case_id: str, c: Caller = Depends(require("supervisor", "analyst", "inspector", "manager")), conn=Depends(connection)):
    return _call(cases.case_detail, conn, c, case_id)


@router.post("/cases/{case_id}/claim")
def claim_case(case_id: str, c: Caller = Depends(require("analyst")), conn=Depends(connection)):
    return _call(cases.claim, conn, c, case_id)


@router.get("/cases/{case_id}/dispatch-suggestion")
def dispatch_suggestion(case_id: str, c: Caller = Depends(require("supervisor")), conn=Depends(connection)):
    row = conn.execute("SELECT * FROM dispatch_suggestion WHERE case_id = %s", (case_id,)).fetchone()
    if not row:
        raise not_found("No dispatch suggestion for this case")
    return row


@router.post("/cases/{case_id}/dispatch-suggestion/approve")
def decide(case_id: str, body: Decision, c: Caller = Depends(require("supervisor")), conn=Depends(connection)):
    return _call(cases.decide_suggestion, conn, c, case_id, body.approve, body.team)


@router.patch("/cases/{case_id}/assign")
def assign(case_id: str, body: Assignment, c: Caller = Depends(require("supervisor")), conn=Depends(connection)):
    return _call(cases.assign, conn, c, case_id, body.team)


@router.post("/cases/{case_id}/photos")
def upload_photo(case_id: str, file: UploadFile = File(...), c: Caller = Depends(require("inspector")), conn=Depends(connection)):
    # A plain def runs in the worker threads: an async endpoint that touches the database blocks the event
    # loop, and while it waits for the audit lock no other request can commit and release it (deadlock).
    data = file.file.read()
    key = _call(cases.add_photo, conn, c, case_id, data, file.content_type or "")
    return {"photo_key": key}


@router.get("/cases/{case_id}/photos/{key}")
def get_photo(case_id: str, key: str, c: Caller = Depends(require("supervisor", "analyst", "inspector", "manager")), conn=Depends(connection)):
    detail = _call(cases.case_detail, conn, c, case_id)
    # A manager sees the evidence only to give the second (export) approval of a report.
    if c.role == "manager" and not any(r["status"] in ("content_approved", "export_approved") for r in detail["reports"]):
        raise forbidden("Managers see evidence photos when a report waits for their export approval")
    if not any(key in (o["photo_keys"] or []) for o in detail["outcomes"]) and not any(
            (e["detail"] or {}).get("photo_key") == key for e in detail["events"]):
        raise not_found("No such photo on this case")
    media = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(key.rsplit(".", 1)[-1], "application/octet-stream")
    return Response(storage.get("photos", key), media_type=media, headers={"Cache-Control": "no-store"})


@router.post("/cases/{case_id}/outcome")
def record_outcome(case_id: str, body: Outcome, c: Caller = Depends(require("inspector")), conn=Depends(connection)):
    return _call(cases.record_outcome, conn, c, case_id, body.outcome, body.notes, body.reason_tag, body.photo_keys, body.client_ref)


@router.get("/notifications")
def notifications(limit: int = Query(50, le=200), c: Caller = Depends(require("supervisor", "admin")), conn=Depends(connection)):
    """Messages sent (or logged by the console notifier), for the demo: they hold a case link only."""
    return conn.execute("SELECT notification_id, ts, case_id, recipient, kind, channel, text, status FROM notification "
                        "ORDER BY notification_id DESC LIMIT %s", (limit,)).fetchall()


@router.get("/teams")
def teams(c: Caller = Depends(require("supervisor", "manager", "analyst")), conn=Depends(connection)):
    return conn.execute("SELECT team_id, name, region FROM team ORDER BY team_id").fetchall()


@router.get("/cases/{case_id}/version")
def case_version(case_id: str, c: Caller = Depends(require("supervisor", "analyst", "inspector", "manager")), conn=Depends(connection)):
    """Cheap change marker for pages that poll (no personal details, so no audit row per poll)."""
    row = conn.execute("""SELECT c.status, (SELECT max(event_id) FROM case_event e WHERE e.case_id = c.case_id) AS last_event,
                                 (SELECT string_agg(status, ',' ORDER BY report_id) FROM case_report r WHERE r.case_id = c.case_id) AS reports
                          FROM inspection_case c WHERE c.case_id = %s""", (case_id,)).fetchone()
    if not row:
        raise ApiError(404, "not_found", "Case not found in your region")
    return row


@router.get("/route")
def my_route(team: str | None = None, c: Caller = Depends(require("inspector", "supervisor")), conn=Depends(connection)):
    """Today's visiting order: an inspector gets their own team's route; a supervisor names a team in their region."""
    from voltguard.agents import route

    if c.role == "inspector":
        if team and team != c.team:
            raise forbidden("Inspectors see their own team's route")
        team = c.team
    if not team:
        raise ApiError(400, "bad_request", "Name a team")
    try:
        result = route.plan(conn, c, team)
    except LookupError as exc:
        raise not_found(str(exc)) from exc
    db.audit(conn, c.user_id, "route.plan", f"team:{team}", {"stops": len(result["stops"])})
    return result
