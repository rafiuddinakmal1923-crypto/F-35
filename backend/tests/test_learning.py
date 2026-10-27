"""Learning and monitoring (SRS FR-ML-01-03, FR-IW-04)."""

from __future__ import annotations

import polars as pl
import psycopg

from tests.conftest import login
from voltguard import db
from voltguard.data import simulator
from voltguard.detection import engine
from voltguard.service import monitoring


def test_FR_ML_01_FR_ML_02_retrain_records_version_with_both_hit_rates(api):
    ds = login(api, "datasci")
    first = api.post("/models/retrain", params={"wait": True}, headers=ds).json()
    job = api.get(f"/jobs/{first['job_id']}", headers=ds).json()
    assert job["status"] == "done", job.get("error")
    api.post("/models/retrain", params={"wait": True}, headers=ds)
    versions = api.get("/models", headers=login(api, "manager.cen")).json()["versions"]
    assert len(versions) >= 2 and versions[0]["active"] and not versions[1]["active"]
    hr = versions[0]["metrics"]["hit_rates"]
    assert set(hr) == {"model_ranked", "random_sample"}
    assert hr["random_sample"]["inspections"] > 0 and hr["model_ranked"]["inspections"] > 0
    assert 0 <= hr["model_ranked"]["hit_rate"] <= 1 and 0 <= hr["random_sample"]["hit_rate"] <= 1
    assert versions[0]["metrics"]["labels"] >= 20          # the demo kit's closed cases plus live outcomes
    assert api.get("/models", headers=login(api, "analyst.cen")).status_code == 403
    assert api.post("/models/retrain", headers=login(api, "manager.cen")).status_code == 403


def test_FR_IW_04_no_access_never_a_label(api, pg):
    with psycopg.connect(pg[0]) as conn:
        assert conn.execute("SELECT count(*) FROM training_label WHERE outcome = 'no_access'").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM training_label").fetchone()[0] >= 20


def test_FR_ML_03_missing_data_and_drift_raise_alerts(api, pg, cfg):
    scn = simulator.Scenario("mon", 77, [simulator.ZoneSpec(1, n_homes=40)], days=21)
    tables, _ = simulator.simulate(scn)
    baseline = engine.run_tables(tables, scn.start_date, scn.days, cfg, score_all=True)
    monitoring.after_detection(baseline, {"run_date": "baseline"})
    day = scn.start_date + __import__("datetime").timedelta(days=15)
    shifted = tables["meter_reading"].filter(pl.col("ts").dt.date() != day).with_columns(pl.col("kwh") * 2.5)
    changed = engine.run_tables({**tables, "meter_reading": shifted}, scn.start_date, scn.days, cfg, score_all=True)
    raised = monitoring.after_detection(changed, {"run_date": "changed"})
    assert "data_quality" in raised and "drift" in raised
    kinds = {a["kind"] for a in api.get("/alerts", headers=login(api, "datasci")).json()}
    assert {"data_quality", "drift"} <= kinds


def test_unusual_access_alert(api, pg):
    with db.admin_connection() as conn:
        with conn.transaction():
            for i in range(monitoring.UNUSUAL_VIEWS_PER_HOUR + 1):
                db.audit(conn, "analyst2.cen", "case.view", f"case:X-{i}", None)
    assert monitoring.check_unusual_access() >= 1
    alerts = api.get("/alerts", headers=login(api, "admin")).json()
    assert any(a["kind"] == "unusual_access" and a["detail"]["user_id"] == "analyst2.cen" for a in alerts)
