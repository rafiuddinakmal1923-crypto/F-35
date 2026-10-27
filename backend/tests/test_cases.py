"""Inspection workflow (SRS FR-IW-01-05, FR-UI-03, FR-AG-02; SDD 6.2) end to end through the API."""

from __future__ import annotations

import json
from datetime import timedelta

import psycopg
import pytest

from tests.conftest import login
from voltguard.agents import dispatch

TOP_CEN = "P-CEN-001-054"


@pytest.fixture(scope="module")
def case_job(api):
    r = api.post("/jobs/create-cases", headers=login(api, "pipeline"))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "done", r.json().get("error")
    return r.json()["result"]


def fake_names(owner_url: str) -> list[str]:
    with psycopg.connect(owner_url) as conn:
        return [r[0].replace("FAKE ", "") for r in conn.execute("SELECT holder_name FROM customer_pii").fetchall()]


def find(api, user: str, premise_id: str) -> dict:
    cases = api.get("/cases", headers=login(api, user)).json()["cases"]
    return next(c for c in cases if c["premise_id"] == premise_id)


def test_FR_IW_01_case_job_creates_threshold_cases(api, case_job):
    model = case_job["model_cases"]
    assert TOP_CEN in {c["premise_id"] for c in model}
    assert {c["zone"] for c in model} >= {"TX-CEN-001", "TX-CEN-002", "TX-NOR-002"}
    assert api.post("/jobs/create-cases", headers=login(api, "analyst.cen")).status_code == 403


def test_FR_UI_03_unclaimed_case_masked_for_every_analyst(api, case_job, pg):
    """Regression: a new case with no assigned analyst must not show details to any analyst."""
    names = fake_names(pg[0])
    case = find(api, "supervisor.cen", TOP_CEN)
    assert case["assigned_analyst"] is None
    for user in ("analyst.cen", "analyst2.cen"):
        body = api.get(f"/premises/{TOP_CEN}", headers=login(api, user)).json()
        assert body["contact"] is None and not any(n in json.dumps(body) for n in names), user
    from voltguard import db
    from voltguard.db import Caller

    for caller in (Caller("analyst.cen", "analyst", "CEN"), Caller("x", "analyst", ""), Caller("x", "", "CEN"),
                   Caller("inspector.a", "inspector", "CEN", None)):
        with db.app_connection(caller) as conn:
            assert conn.execute("SELECT * FROM vg_case_contact(%s)", (case["case_id"],)).fetchone() is None, caller


def test_FR_IW_05_random_sample_from_flagged_zones_only(api, case_job, pg):
    sample = case_job["random_sample_cases"]
    assert sample and all(c["origin"] == "random_sample" for c in sample)
    with psycopg.connect(pg[0]) as conn:
        flagged = {r[0] for r in conn.execute("SELECT transformer_id FROM zone_run WHERE flagged AND run_date = (SELECT max(run_date) FROM zone_run)")}
        open_model = {c["premise_id"] for c in case_job["model_cases"]}
    assert {c["zone"] for c in sample} <= flagged
    assert not ({c["premise_id"] for c in sample} & open_model)   # excludes premises that already had an open case


def test_FR_IW_01_manual_cases_and_only_supervisor_assigns(api, case_job):
    r = api.post("/cases", json={"premise_id": "P-CEN-001-010", "reason": "Neighbour complaint about cables"},
                 headers=login(api, "analyst.cen"))
    assert r.status_code == 200 and r.json()["assigned_analyst"] == "analyst.cen" and r.json()["origin"] == "manual"
    dup = api.post("/cases", json={"premise_id": "P-CEN-001-010"}, headers=login(api, "supervisor.cen"))
    assert dup.status_code == 409
    case_id = r.json()["case_id"]
    for user in ("analyst.cen", "inspector.a", "manager.cen"):
        assert api.patch(f"/cases/{case_id}/assign", json={"team": "T-CEN-A"}, headers=login(api, user)).status_code == 403, user
    ok = api.patch(f"/cases/{case_id}/assign", json={"team": "T-CEN-A"}, headers=login(api, "supervisor.cen"))
    assert ok.status_code == 200 and ok.json()["status"] == "assigned"
    assert api.post("/cases", json={"premise_id": "P-NOR-001-001"}, headers=login(api, "analyst.cen")).status_code == 404


def test_FR_AG_02_dispatch_suggestion_claim_and_approval(api, case_job, pg):
    case = find(api, "supervisor.cen", TOP_CEN)
    suggestion = api.get(f"/cases/{case['case_id']}/dispatch-suggestion", headers=login(api, "supervisor.cen")).json()
    assert suggestion["suggested_team"] == "T-CEN-B" and suggestion["status"] == "pending"   # nearest on-duty team
    assert suggestion["joint_operation"]                                                      # flat 24/7 mining gap
    # The analyst claims the case while the suggestion waits for the supervisor (claim runs alongside dispatch).
    assert api.post(f"/cases/{case['case_id']}/claim", headers=login(api, "analyst.cen")).status_code == 200
    assert api.post(f"/cases/{case['case_id']}/claim", headers=login(api, "analyst2.cen")).status_code == 409
    assert api.post(f"/cases/{case['case_id']}/dispatch-suggestion/approve", json={"approve": True},
                    headers=login(api, "analyst.cen")).status_code == 403
    r = api.post(f"/cases/{case['case_id']}/dispatch-suggestion/approve", json={"approve": True}, headers=login(api, "supervisor.cen"))
    assert r.status_code == 200 and r.json()["assigned_team"] == "T-CEN-B" and r.json()["status"] == "assigned"
    messages = api.get("/notifications", headers=login(api, "supervisor.cen")).json()
    sent = next(m for m in messages if m["case_id"] == case["case_id"] and m["kind"] == "assignment")
    assert f"/#/cases/{case['case_id']}" in sent["text"]
    assert not any(name in sent["text"] for name in fake_names(pg[0]))
    assert "Jalan" not in sent["text"] and "Taman" not in sent["text"]


def test_FR_UI_03_details_only_for_case_roles(api, case_job, pg):
    case = find(api, "supervisor.cen", TOP_CEN)
    cid = case["case_id"]
    with psycopg.connect(pg[0]) as conn:
        holder = conn.execute("SELECT holder_name FROM customer_pii WHERE premise_id = %s", (TOP_CEN,)).fetchone()[0]
    for user in ("analyst.cen", "supervisor.cen", "inspector.b"):
        body = api.get(f"/cases/{cid}", headers=login(api, user)).json()
        assert body["contact"]["holder_name"] == holder and body["contact"]["lat"] is not None, user
    premise = api.get(f"/premises/{TOP_CEN}", headers=login(api, "analyst.cen")).json()
    assert premise["contact"]["holder_name"] == holder
    # Not the assigned analyst, another team's inspector, a manager or another region: no details.
    assert api.get(f"/cases/{cid}", headers=login(api, "analyst2.cen")).status_code == 403
    assert api.get(f"/premises/{TOP_CEN}", headers=login(api, "analyst2.cen")).json()["contact"] is None
    assert api.get(f"/cases/{cid}", headers=login(api, "inspector.a")).status_code in (403, 404)
    manager = api.get(f"/cases/{cid}", headers=login(api, "manager.cen")).json()
    assert manager["contact"] is None and holder not in json.dumps(manager)
    assert api.get(f"/cases/{cid}", headers=login(api, "supervisor.nor")).status_code == 404
    inspector_list = api.get("/cases", headers=login(api, "inspector.b")).json()["cases"]
    item = next(c for c in inspector_list if c["case_id"] == cid)
    assert item["contact"]["address"] and item["reasons"] and item["label"] == "Inspection"


def test_FR_IW_02_FR_IW_03_FR_IW_04_outcomes_status_and_labels(api, case_job, pg):
    insp = login(api, "inspector.b")
    cid = find(api, "supervisor.cen", TOP_CEN)["case_id"]
    photo = api.post(f"/cases/{cid}/photos", files={"file": ("meter.jpg", b"\xff\xd8\xff fake jpeg", "image/jpeg")}, headers=insp)
    assert photo.status_code == 200
    key = photo.json()["photo_key"]
    # Wrong team cannot record.
    assert api.post(f"/cases/{cid}/outcome", json={"outcome": "false_alarm"}, headers=login(api, "inspector.a")).status_code in (403, 404)
    r = api.post(f"/cases/{cid}/outcome", json={"outcome": "no_access", "notes": "Gate locked, nobody home.", "client_ref": "dev1-0001"},
                 headers=insp)
    assert r.status_code == 200 and r.json()["case"]["status"] == "assigned"
    again = api.post(f"/cases/{cid}/outcome", json={"outcome": "no_access", "client_ref": "dev1-0001"}, headers=insp)
    assert again.json()["duplicate"] is True          # an offline submission synced twice is recorded once
    planted = ("Met Encik Ahmad bin Ali at No. 12, Jalan Mawar 3, Taman Seri. IC 850312-10-5523, phone 012-345 6789. "
               "Bypass cable behind the meter board feeding a container of mining rigs.")
    r = api.post(f"/cases/{cid}/outcome", json={"outcome": "confirmed_theft", "notes": planted, "photo_keys": [key],
                                                "reason_tag": "meter_bypass"}, headers=insp)
    assert r.status_code == 200 and r.json()["case"]["status"] == "reporting" and r.json()["visit_no"] == 2
    detail = api.get(f"/cases/{cid}", headers=login(api, "analyst.cen")).json()
    statuses = [e["event_type"] for e in detail["events"]]
    assert statuses[:1] == ["created"] and "assigned" in statuses and "visited" in statuses
    assert "outcome:no_access" in statuses and "outcome:confirmed_theft" in statuses
    redacted = detail["outcomes"][1]["notes_redacted"]
    for secret in ("Ahmad", "Jalan Mawar", "850312", "012-345"):
        assert secret not in redacted and secret not in json.dumps(detail)
    assert "mining rigs" in redacted
    assert api.get(f"/cases/{cid}/photos/{key}", headers=login(api, "analyst.cen")).content.startswith(b"\xff\xd8")
    with psycopg.connect(pg[0]) as conn:
        labels = conn.execute("SELECT outcome FROM training_label WHERE case_id = %s", (cid,)).fetchall()
    assert labels == [("confirmed_theft",)]           # No access is not a training label

    # Other outcomes close the case.
    for premise, outcome in (("P-CEN-002-029", "false_alarm"), ("P-NOR-002-035", "inconclusive")):
        sup = "supervisor.cen" if "CEN" in premise else "supervisor.nor"
        team = "T-CEN-A" if "CEN" in premise else "T-NOR-C"
        inspector = "inspector.a" if "CEN" in premise else "inspector.c"
        case = find(api, sup, premise)
        api.patch(f"/cases/{case['case_id']}/assign", json={"team": team}, headers=login(api, sup))
        r = api.post(f"/cases/{case['case_id']}/outcome", json={"outcome": outcome}, headers=login(api, inspector))
        assert r.json()["case"]["status"] == "closed", (premise, r.text)


def test_FR_IW_05_random_sample_presented_as_routine_check(api, case_job):
    sample = next(c for c in case_job["random_sample_cases"] if c["zone"].startswith("TX-CEN"))
    api.patch(f"/cases/{sample['case_id']}/assign", json={"team": "T-CEN-A"}, headers=login(api, "supervisor.cen"))
    item = next(c for c in api.get("/cases", headers=login(api, "inspector.a")).json()["cases"] if c["case_id"] == sample["case_id"])
    assert item["label"] == "Routine meter check" and item["reasons"] == [] and "score" not in json.dumps(item)


def test_FR_AG_02_reminder_then_escalation_on_demo_timers(api, case_job, pg):
    with psycopg.connect(pg[0]) as conn:
        case_id, assigned_at = conn.execute("SELECT case_id, assigned_at FROM inspection_case WHERE status = 'assigned' "
                                            "AND reminded_at IS NULL ORDER BY assigned_at LIMIT 1").fetchone()
    first = [m for m in dispatch.run_reminders(assigned_at + timedelta(minutes=3)) if f"case {case_id}" in m["text"]]
    assert [m["text"].split(":")[0] for m in first] == ["VoltGuard Reminder"]
    second = [m for m in dispatch.run_reminders(assigned_at + timedelta(minutes=5)) if f"case {case_id}" in m["text"]]
    assert second and all(m["text"].startswith("VoltGuard Escalation") for m in second)
    assert not [m for m in dispatch.run_reminders(assigned_at + timedelta(minutes=6)) if f"case {case_id}" in m["text"]]
