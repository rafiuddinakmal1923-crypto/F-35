"""Endpoints added by the UI upgrade (VoltGuard_UI_Upgrade_Prompt.md): value at risk, validation summary,
back-test replay, data health and the demo-only role cards, guide and reset. Privacy and role rules unchanged."""

from __future__ import annotations

import shutil
import time

import psycopg
import pytest

from tests.conftest import login
from voltguard import config


@pytest.fixture
def demo_on(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")


@pytest.fixture
def config_copy(tmp_path, monkeypatch):
    """A writable copy of config/ so the tariff can be changed without touching the repository."""
    target = tmp_path / "config"
    shutil.copytree(config.REPO_ROOT / "config", target)
    monkeypatch.setenv("VG_CONFIG_DIR", str(target))
    config.load_yaml.cache_clear()
    yield target
    monkeypatch.delenv("VG_CONFIG_DIR")
    config.load_yaml.cache_clear()


def test_3_1_value_at_risk_is_an_estimate_from_the_gap_above_the_margin(api, config_copy):
    (config_copy / "tariffs.yaml").write_text("rm_per_kwh:\nsource:\n", encoding="utf-8")
    config.load_yaml.cache_clear()
    data = api.get("/zones", headers=login(api, "manager.cen")).json()
    assert data["tariff"]["rm_per_kwh"] is None and data["tariff"]["placeholder"] == "[TNB domestic tariff: to confirm]"
    flagged = [z for z in data["zones"] if z["flagged"] and z["balance_available"]]
    assert flagged
    for z in data["zones"]:
        if z in flagged:
            excess = max(z["gap_kwh_recent"] - z["uncertainty_kwh_recent"], 0)
            assert z["value"]["estimate"] is True and z["value"]["rm_per_month"] is None       # no tariff: never a guessed RM
            assert z["value"]["kwh_per_month"] == round(excess * 30)
        else:
            assert z["value"] is None                                                          # flagged zones only
        assert len(z["spark"]) <= 14 and "lat" in z                                            # zone level: transformer position
    assert data["totals"]["value"]["kwh_per_month"] == sum(z["value"]["kwh_per_month"] for z in flagged)
    assert "model_ranked" in data["totals"]["hit_rates"] or data["totals"]["hit_rates"] == {}

    admin = login(api, "admin")
    assert api.put("/settings/tariff", json={"rm_per_kwh": 0.5}, headers=login(api, "manager.cen")).status_code == 403
    assert api.put("/settings/tariff", json={"rm_per_kwh": 50}, headers=admin).status_code == 400
    r = api.put("/settings/tariff", json={"rm_per_kwh": 0.5, "source": "test value"}, headers=admin)
    assert r.status_code == 200 and r.json()["rm_per_kwh"] == 0.5
    assert "rm_per_kwh: 0.5" in (config_copy / "tariffs.yaml").read_text(encoding="utf-8")
    zone = api.get(f"/zones/{flagged[0]['transformer_id']}/balance", headers=login(api, "analyst.cen")).json()
    assert zone["value"]["rm_per_month"] == round(zone["value"]["kwh_per_month"] * 0.5)
    from voltguard.service import digest

    assert digest.tariff()["rm_per_kwh"] == 0.5                                                # the weekly report reads the same file
    api.put("/settings/tariff", json={"rm_per_kwh": None}, headers=admin)


def test_3_1_rpt_zone_latest_carries_value_at_risk_at_zone_level(api, pg, config_copy):
    api.put("/settings/tariff", json={"rm_per_kwh": 0.4}, headers=login(api, "admin"))
    with psycopg.connect(pg[0]) as conn:
        rows = conn.execute("SELECT zone, flagged, excess_kwh_per_day, excess_kwh_per_month_estimate, rm_at_risk_per_month_estimate "
                            "FROM rpt_zone_latest").fetchall()
    for zone, flagged, excess, month, rm in rows:
        if flagged and excess is not None:
            assert float(month) == round(float(excess) * 30) and float(rm) == round(float(excess) * 30 * 0.4)
        else:
            assert rm is None
    api.put("/settings/tariff", json={"rm_per_kwh": None}, headers=login(api, "admin"))


def test_3_6_validation_summary_from_files_and_model_versions(api, monkeypatch, tmp_path):
    from voltguard.api import routes_ui

    for user in ("manager.cen", "analyst.cen", "datasci"):
        r = api.get("/validation/summary", headers=login(api, user))
        assert r.status_code == 200
    body = r.json()
    assert body["simulation"]["heldout"]["thefts_in_top5"] <= body["simulation"]["heldout"]["thefts"]
    assert {"noise_sweep", "monthly_read_sweep"} <= set(body["simulation"])
    assert isinstance(body["model_versions"], list)
    for user in ("supervisor.cen", "inspector.a", "auditor"):
        assert api.get("/validation/summary", headers=login(api, user)).status_code == 403
    monkeypatch.setattr(routes_ui, "REPORTS", tmp_path)                                       # not run yet: null, not a number
    assert api.get("/validation/summary", headers=login(api, "manager.cen")).json()["simulation"] is None


def test_3_7_backtest_replay_by_role_and_region(api):
    zones = api.get("/backtest", headers=login(api, "analyst.cen")).json()["zones"]
    assert zones and all(z["region"] == "CEN" for z in zones)
    full = api.get("/backtest/TX-CEN-001", headers=login(api, "analyst.cen")).json()
    assert full["frames"] and full["frames"][0]["top"] and full["known_cases"][0]["premise_id"].startswith("P-CEN-001")
    assert all(k["first_top5_day"] is None or k["days_to_detection"] is not None for k in full["known_cases"])
    manager = api.get("/backtest/TX-CEN-001", headers=login(api, "manager.cen")).json()
    assert manager["premise_ids_hidden"] and "P-CEN" not in str(manager)                      # managers: zone level only
    assert api.get("/backtest/TX-CEN-001", headers=login(api, "analyst.nor")).status_code == 404
    assert api.get("/backtest/TX-CEN-001", headers=login(api, "inspector.a")).status_code == 403


def test_3_9_data_health_for_admins(api):
    r = api.get("/admin/data-health", headers=login(api, "admin"))
    assert r.status_code == 200
    body = r.json()
    readings = next(t for t in body["tables"] if t["table"] == "meter_reading")
    assert readings["rows"] > 0 and readings["source"] == "simulated" and readings["duplicates_removed"] is None
    assert 0 <= body["completeness"]["complete_share"] <= 1
    assert {f["code"] for f in body["fallbacks"]} >= {"AS-2", "AS-3"}                          # TX-CEN-004 has no meter; voltage simulated
    assert api.get("/admin/data-health", headers=login(api, "analyst.cen")).status_code == 403


def test_3_10_route_stops_show_straight_line_distance_from_base(api):
    r = api.get("/route", params={"team": "T-CEN-B"}, headers=login(api, "supervisor.cen"))
    if r.status_code == 200:
        assert all(s["base_km"] >= 0 for s in r.json()["stops"])


def test_demo_features_are_off_without_demo_mode(api, monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    assert api.get("/demo/accounts").status_code == 404
    assert api.post("/auth/demo-token", json={"username": "analyst.cen"}).status_code == 404
    assert api.get("/demo/status", headers=login(api, "analyst.cen")).status_code == 404
    assert api.get("/meta", headers=login(api, "analyst.cen")).json()["demo"] is False


def test_2_6_role_cards_sign_in_test_accounts_only(api, demo_on):
    accounts = api.get("/demo/accounts").json()["accounts"]
    assert {"manager.cen", "inspector.b", "admin"} <= {a["user_id"] for a in accounts}
    assert all("password" not in a for a in accounts)
    r = api.post("/auth/demo-token", json={"username": "analyst.cen"})
    assert r.status_code == 200 and r.json()["user"]["role"] == "analyst"
    me = api.get("/meta", headers={"Authorization": f"Bearer {r.json()['access_token']}"}).json()
    assert me["demo"] is True and me["data_mode"] == "simulated" and me["region"] == "CEN" and me["run_date"]
    assert api.post("/auth/demo-token", json={"username": "pipeline"}).status_code == 403   # service account is not a card


def test_3_8_demo_guide_status_and_reset(api, demo_on, monkeypatch):
    analyst = api.get("/demo/status", headers=login(api, "analyst.cen")).json()
    assert [s["step"] for s in analyst["steps"]] == [1, 2, 3, 4, 5, 6, 7]
    assert analyst["zone"] == "TX-CEN-001" and analyst["premise"]
    manager = api.get("/demo/status", headers=login(api, "manager.cen")).json()
    assert manager["premise"] is None and manager["case"] is None                             # no premise IDs for managers

    from voltguard.service import demo

    kept = {}
    monkeypatch.setattr(demo, "reset_rehearsal", lambda keep_job=None: kept.setdefault("job", keep_job) and {})
    assert api.post("/admin/demo/reset", headers=login(api, "analyst.cen")).status_code == 403
    started = time.time()
    job = api.post("/admin/demo/reset", params={"wait": True}, headers=login(api, "admin")).json()["job_id"]
    status = api.get(f"/jobs/{job}", headers=login(api, "admin")).json()
    assert status["status"] == "done", status.get("error")
    assert kept["job"] == job and time.time() - started < 60
    after = api.get("/demo/status", headers=login(api, "analyst.cen")).json()
    assert after["since"] and not any(s["done"] for s in after["steps"])                     # nothing ticked right after a reset
