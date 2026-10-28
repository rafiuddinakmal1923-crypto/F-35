"""API and security (SRS FR-AD-01-03, FR-UI-01-03, NFR-12, NFR-16; SDD 7, 9.2) on a real PostgreSQL."""

from __future__ import annotations

import json

import psycopg
import pytest

from tests.conftest import login
from voltguard import audit, db
from voltguard.db import Caller


def fake_names(owner_url: str) -> list[str]:
    with psycopg.connect(owner_url) as conn:
        return [r[0].replace("FAKE ", "") for r in conn.execute("SELECT holder_name FROM customer_pii").fetchall()]


def test_FR_UI_01_overview_zone_level_in_gap_order(api):
    r = api.get("/zones", headers=login(api, "manager.cen"))
    assert r.status_code == 200
    zones = r.json()["zones"]
    assert {z["region"] for z in zones} == {"CEN"}
    flagged = [z for z in zones if z["flagged"]]
    assert [z["transformer_id"] for z in flagged] == sorted(
        [z["transformer_id"] for z in flagged], key=lambda t: -next(z["gap_pct_recent"] for z in flagged if z["transformer_id"] == t))
    assert {"TX-CEN-001", "TX-CEN-002"} <= {z["transformer_id"] for z in flagged}
    text = json.dumps(r.json())
    assert "premise_id" not in text and "holder_name" not in text


def test_FR_UI_04_district_filter(api):
    h = login(api, "analyst.cen")
    all_zones = api.get("/zones", headers=h).json()["zones"]
    klang = api.get("/zones", params={"district": "Klang"}, headers=h).json()["zones"]
    assert klang and len(klang) < len(all_zones) and {z["district"] for z in klang} == {"Klang"}


def test_FR_UI_02_zone_view_balance_and_profile(api):
    r = api.get("/zones/TX-CEN-002/balance", headers=login(api, "analyst.cen")).json()
    assert r["zone"]["flagged"] and r["zone"]["gap_start"] == "2026-08-31"
    assert len(r["hourly_gap_kwh"]) == 24 and len(r["days"]) == 61
    before = [d["gap_kwh"] for d in r["days"] if d["date"] < "2026-08-29"]
    after = [d["gap_kwh"] for d in r["days"] if d["date"] > "2026-09-02"]
    assert sum(after) / len(after) > 5 * max(sum(before) / len(before), 1)


def test_FR_AD_01_role_and_region_refusals(api):
    cen_tx = "TX-CEN-001"
    # Wrong region: the zone does not exist for a Northern analyst (row-level security).
    assert api.get(f"/zones/{cen_tx}/suspects", headers=login(api, "analyst.nor")).status_code == 404
    assert {z["region"] for z in api.get("/zones", headers=login(api, "analyst.nor")).json()["zones"]} == {"NOR"}
    # Wrong role.
    assert api.get(f"/zones/{cen_tx}/suspects", headers=login(api, "manager.cen")).status_code == 403
    for user in ("inspector.a", "auditor", "datasci"):
        assert api.get("/zones", headers=login(api, user)).status_code == 403, user
    assert api.get("/audit", headers=login(api, "analyst.cen")).status_code == 403
    assert api.post("/jobs/run-detection", headers=login(api, "analyst.cen")).status_code == 403
    assert api.get("/admin/datasets", headers=login(api, "manager.cen")).status_code == 403
    assert api.put("/settings/thresholds", json={"zone": {"share_of_supply": 0.1}}, headers=login(api, "analyst.cen")).status_code == 403
    # No token at all.
    assert api.get("/zones").status_code == 401


def test_FR_AD_01_database_enforces_region_and_pii_rules(api):
    with db.app_connection(Caller("analyst.nor", "analyst", "NOR")) as conn:
        assert conn.execute("SELECT count(*) AS n FROM premise WHERE region = 'CEN'").fetchone()["n"] == 0
        assert conn.execute("SELECT count(*) AS n FROM premise_score WHERE transformer_id = 'TX-CEN-001'").fetchone()["n"] == 0
        assert conn.execute("SELECT count(*) AS n FROM meter_reading r JOIN meter m USING (meter_id) WHERE m.region = 'CEN'").fetchone()["n"] == 0
    for query in ("SELECT * FROM customer_pii LIMIT 1", "SELECT lat FROM premise LIMIT 1", "SELECT notes FROM inspection_outcome LIMIT 1",
                  "SELECT password_hash FROM app_user LIMIT 1", "DELETE FROM audit_log", "UPDATE audit_log SET action = 'x'"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with db.app_connection(Caller("admin", "admin", "*")) as conn:
                conn.execute(query)


def test_FR_UI_03_details_masked_before_a_case_opens(api, pg):
    names = fake_names(pg[0])
    for user in ("analyst.cen", "supervisor.cen"):
        top = api.get("/zones/TX-CEN-001/suspects", headers=login(api, user)).json()["suspects"][0]
        assert top["open_case_id"] is None
        r = api.get(f"/premises/{top['premise_id']}", headers=login(api, user))
        assert r.status_code == 200
        body = r.json()
        assert body["masked"] and body["contact"] is None
        text = json.dumps(body)
        assert '"lat"' not in text and '"lon"' not in text
        assert not any(name in text for name in names)
    assert api.get(f"/premises/{top['premise_id']}", headers=login(api, "inspector.a")).status_code == 403


def test_FR_PS_07_suspects_reasons_add_up(api):
    body = api.get("/zones/TX-CEN-001/suspects", headers=login(api, "analyst.cen")).json()
    for s in body["suspects"][:10]:
        assert sum(r["contribution"] for r in s["reasons"]) == pytest.approx(s["score"], abs=0.051 * len(s["reasons"]))
    # SDD 10.5 step 2: the injected thefts lead the ranking (mining tap from day one, partial bypass, and the
    # solar home that also bypasses its night load); their order among themselves is not a requirement.
    top3 = {s["premise_id"] for s in body["suspects"][:3]}
    assert top3 == {"P-CEN-001-054", "P-CEN-001-049", "P-CEN-001-069"}


def test_NFR_16_remote_sign_out(api):
    h = login(api, "inspector.b")
    assert api.get("/me", headers=h).status_code == 200
    # Another region: row-level security hides the user, so the refusal is a 404.
    assert api.post("/users/inspector.b/sign-out", headers=login(api, "supervisor.nor")).status_code in (403, 404)
    assert api.post("/users/inspector.b/sign-out", headers=login(api, "supervisor.cen")).status_code == 200
    r = api.get("/me", headers=h)
    assert r.status_code == 401 and r.json()["code"] == "signed_out"
    assert api.get("/me", headers=login(api, "inspector.b")).status_code == 200   # signing in again works


def test_jobs_run_detection_creates_no_cases(api, pg):
    r = api.post("/jobs/run-detection", params={"wait": True}, headers=login(api, "datasci"))
    assert r.status_code == 200
    job = api.get(f"/jobs/{r.json()['job_id']}", headers=login(api, "datasci")).json()
    assert job["status"] == "done", job.get("error")
    assert "TX-CEN-001" in job["result"]["flagged_zones"]
    with psycopg.connect(pg[0]) as conn:
        assert conn.execute("SELECT count(*) FROM inspection_case WHERE origin <> 'manual' AND created_by <> 'seed'").fetchone()[0] == 0


def test_FR_AD_03_threshold_change_applies_on_rerun(api, pg):
    admin = login(api, "admin")
    assert api.put("/settings/thresholds", json={"zone": {"bogus": 1}}, headers=admin).status_code == 400
    assert api.put("/settings/thresholds", json={"zone": {"share_of_supply": 0.5}}, headers=admin).status_code == 200
    try:
        job = api.post("/jobs/run-detection", params={"wait": True}, headers=login(api, "datasci")).json()
        result = api.get(f"/jobs/{job['job_id']}", headers=admin).json()["result"]
        assert result["flagged_zones"] == []
    finally:
        with psycopg.connect(pg[0]) as conn:
            conn.execute("DELETE FROM setting WHERE key = 'thresholds'")
        api.post("/jobs/run-detection", params={"wait": True}, headers=login(api, "datasci"))


def test_data_manager_upload_validates_and_versions(api):
    from voltguard import config

    admin = login(api, "admin")
    # A transformer file alone would orphan the active premises (link check), so use a standalone table.
    template = (config.REPO_ROOT / "data" / "uploads" / "templates" / "district_weather.csv").read_bytes()
    r = api.post("/admin/datasets", data={"dataset": "dm_test", "table": "district_weather"},
                 files={"file": ("weather.csv", template, "text/csv")}, headers=admin)
    assert r.status_code == 200 and r.json()["report"]["status"] == "accepted", r.json()["report"]["issues"]
    assert r.json()["preview"]["district_weather"][0]["district"] == "Petaling"
    orphan = (config.REPO_ROOT / "data" / "uploads" / "templates" / "transformer.csv").read_bytes()
    bad = api.post("/admin/datasets", data={"dataset": "dm_test", "table": "transformer"},
                   files={"file": ("tx.csv", orphan, "text/csv")}, headers=admin)
    assert bad.json()["version"] == "v2" and bad.json()["report"]["status"] == "rejected"
    assert any(i["check"] == "link" for i in bad.json()["report"]["issues"])
    report = api.get("/admin/datasets/dm_test/versions/v2/report", headers=admin)
    assert report.status_code == 200 and "Rejected" in report.text
    assert api.post("/admin/datasets/dm_test/versions/v2/activate", headers=admin).status_code == 400
    assert api.post("/admin/datasets", data={"dataset": "../x", "table": "transformer"},
                    files={"file": ("tx.csv", orphan, "text/csv")}, headers=admin).status_code == 400


def test_FR_AD_02_NFR_12_audit_logged_and_tampering_detected(api, pg):
    owner = pg[0]
    api.get("/zones/TX-CEN-001/suspects", headers=login(api, "analyst.cen"))
    rows = api.get("/audit", params={"action": "zone.suspects"}, headers=login(api, "auditor")).json()["rows"]
    assert rows and rows[0]["user_id"] == "analyst.cen"
    assert audit.verify().ok
    anchor = audit.write_anchor("2026-10-27")
    assert anchor and audit.verify().anchors_checked == 1

    with psycopg.connect(owner) as conn:
        target = conn.execute("SELECT log_id, action FROM audit_log WHERE action = 'zone.suspects.view' ORDER BY log_id LIMIT 1").fetchone()
        conn.execute("UPDATE audit_log SET action = 'nothing.to.see' WHERE log_id = %s", (target[0],))
    result = audit.verify()
    assert not result.ok and any(p["log_id"] == target[0] and "edited" in p["problem"] for p in result.problems)

    # Rewrite the whole chain consistently: row hashes check out, but the anchor outside the database does not.
    with psycopg.connect(owner) as conn:
        prev = audit.GENESIS
        for r in conn.execute("SELECT log_id, ts, user_id, action, object_ref, detail::text FROM audit_log ORDER BY log_id").fetchall():
            h = audit.row_hash(prev, r[0], r[1], r[2], r[3], r[4], r[5])
            conn.execute("UPDATE audit_log SET prev_hash = %s, row_hash = %s WHERE log_id = %s", (prev, h, r[0]))
            prev = h
    result = audit.verify()
    assert not result.ok and any("anchor" in p["problem"] for p in result.problems)
    assert not any("edited" in p["problem"] for p in result.problems)

    with psycopg.connect(owner) as conn:   # restore for later tests
        conn.execute("UPDATE audit_log SET action = %s WHERE log_id = %s", (target[1], target[0]))
        prev = audit.GENESIS
        for r in conn.execute("SELECT log_id, ts, user_id, action, object_ref, detail::text FROM audit_log ORDER BY log_id").fetchall():
            h = audit.row_hash(prev, r[0], r[1], r[2], r[3], r[4], r[5])
            conn.execute("UPDATE audit_log SET prev_hash = %s, row_hash = %s WHERE log_id = %s", (prev, h, r[0]))
            prev = h
    anchor.chmod(0o644)
    anchor.unlink()
    assert audit.verify().ok


def test_sign_in_rejects_wrong_password_and_throttles(api):
    for _ in range(5):
        assert api.post("/auth/token", json={"username": "manager.nor", "password": "wrong"}).status_code == 401
    assert api.post("/auth/token", json={"username": "manager.nor", "password": "wrong"}).status_code == 429
    from voltguard import auth

    auth._failures.pop("manager.nor", None)       # the throttle lasts five minutes; later tests sign in as this user


def test_health_and_metrics(api):
    assert api.get("/health").json()["status"] == "ok"
    assert "voltguard_requests_total" in api.get("/metrics").text


def test_NFR_03_no_endpoint_blocks_the_event_loop():
    """Endpoints that touch the database must be plain functions (run in worker threads). An async endpoint
    waiting for the audit lock blocked the event loop, so the request holding that lock could never commit."""
    import inspect

    from fastapi.routing import APIRoute

    from voltguard.api.main import create_app

    async_routes = [r.path for r in create_app().routes if isinstance(r, APIRoute) and inspect.iscoroutinefunction(r.endpoint)]
    assert not async_routes, async_routes
