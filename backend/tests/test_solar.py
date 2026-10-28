"""Rooftop solar told apart from theft, and theft hidden behind solar (SRS FR-PS-10, AS-9; Solar brief).

Solar can explain only a daytime drop. These tests check that the solar penalty is applied to plain solar
homes, dropped when the night-time evidence is strong or the drop is larger than the panels can produce,
and that the supporting checks (rainy-day rebound, timing, voltage signature, unregistered export,
home battery) behave as documented.
"""

from __future__ import annotations

import polars as pl
import pytest

from tests.conftest import case_premise, rank_of, top_k
from voltguard.data import simulator
from voltguard.data.simulator import Injected, Scenario, ZoneSpec
from voltguard.detection import engine
from voltguard.detection.scoring import score_premise
from voltguard.detection.features import FEATURE_NAMES

DEMO_ZONE = "TX-CEN-001"
ZONE = "TX-CEN-009"


def solar_scenario(seed: int = 781) -> Scenario:
    return Scenario("solar", seed, [ZoneSpec(9, "CEN", "Petaling", n_homes=70, cases=[
        Injected("partial_bypass", start_day=30, size=0.7),
        Injected("solar", start_day=28, size=1.5, export=False, registered=True),
        Injected("solar", start_day=30, size=3.0, export=True, registered=True),
        Injected("solar_with_theft", start_day=32, size=3.0, export=True, registered=False, theft="rig", theft_size=3.0),
        Injected("solar_with_theft", start_day=34, size=3.5, export=False, registered=True, theft="night_bypass", theft_size=0.6),
        Injected("solar_unregistered_export", start_day=30, size=4.0, export=True, registered=False),
        Injected("solar_with_battery", start_day=30, size=4.0, export=False, registered=True, battery=True),
    ])])


@pytest.fixture(scope="module")
def solar_sim():
    scn = solar_scenario()
    tables, truth = simulator.simulate(scn)
    return scn, tables, truth


@pytest.fixture(scope="module")
def solar_run(solar_sim, cfg):
    scn, tables, _ = solar_sim
    return engine.run_tables(tables, scn.start_date, scn.days, cfg, score_all=True)


def premise(run, zone: str, pid: str):
    return next(p for p in run.zones[zone].premises if p.premise_id == pid)


def test_FR_PS_10_solar_masking_theft_still_top(demo_run, demo_sim, solar_run, solar_sim):
    """Solar + theft lands in the top 5% and its reasons mention night-time evidence (demo zone and a test zone)."""
    _, _, truth = demo_sim
    pid = case_premise(truth, DEMO_ZONE, "solar_with_theft")
    p = premise(demo_run, DEMO_ZONE, pid)
    assert "solar" in p.tags and p.rank <= top_k(demo_run.zones[DEMO_ZONE].zone.n)
    assert any("night" in r["reason_text"].lower() for r in p.reasons)
    _, _, truth = solar_sim
    k = top_k(solar_run.zones[ZONE].zone.n)
    for nth in (0, 1):                                           # a flat rig and a night-time partial bypass
        p = premise(solar_run, ZONE, case_premise(truth, ZONE, "solar_with_theft", nth))
        assert p.rank <= k, p.details["solar"]
        assert any("night" in r["reason_text"].lower() for r in p.reasons)


def test_FR_PS_10_plain_solar_battery_and_unregistered_export_not_top(solar_run, solar_sim, demo_run, demo_sim):
    _, _, truth = solar_sim
    k = top_k(solar_run.zones[ZONE].zone.n)
    for kind, count in (("solar", 2), ("solar_with_battery", 1), ("solar_unregistered_export", 1)):
        for nth in range(count):
            p = premise(solar_run, ZONE, case_premise(truth, ZONE, kind, nth))
            assert "solar" in p.tags and p.rank > k, (kind, p.rank)
            assert any(r["feature"] == "tag:solar" and r["contribution"] < 0 for r in p.reasons), kind
    _, _, truth = demo_sim
    for nth in (0, 1):
        assert rank_of(demo_run, DEMO_ZONE, case_premise(truth, DEMO_ZONE, "solar", nth)) > top_k(demo_run.zones[DEMO_ZONE].zone.n)


def test_FR_PS_10_penalty_dropped_when_night_evidence_is_strong(solar_run, solar_sim):
    _, _, truth = solar_sim
    thief = premise(solar_run, ZONE, case_premise(truth, ZONE, "solar_with_theft", 1))
    s = thief.details["solar"]
    assert s["night"]["strong"] and s["penalty"] == {"applies": False, "verdict": "night_unexplained", "confidence": "normal"}
    assert not any(r["feature"] == "tag:solar" for r in thief.reasons)
    line = next(r for r in thief.reasons if r["feature"] == "solar_unexplained")
    assert line["contribution"] == 0 and "daytime drop only" in line["reason_text"] and "night-time use" in line["reason_text"]
    plain = premise(solar_run, ZONE, case_premise(truth, ZONE, "solar", 0))
    assert plain.details["solar"]["penalty"]["applies"] and not plain.details["solar"]["night"]["strong"]


def test_FR_PS_10_penalty_rule_follows_settings(cfg):
    """The strong-night rule reads config (solar.strong_night_*); a premise below it keeps the penalty."""
    x = [0.0] * len(FEATURE_NAMES)
    x[FEATURE_NAMES.index("change_from_history")] = 1.0
    keep = {"solar": {"penalty": {"applies": True, "verdict": "explained"}}}
    drop = {"solar": {"penalty": {"applies": False, "verdict": "night_unexplained"},
                      "night": {"drop_share": 0.4, "below_peers_share": 0.35}}}
    with_penalty = score_premise(x, ["solar"], keep, [], cfg)
    without = score_premise(x, ["solar"], drop, [], cfg)
    assert without.score - with_penalty.score == round(100 * cfg["penalties"]["solar"])
    assert "fell 40% from its own history and is 35% below similar homes" in next(
        r.text for r in without.lines if r.feature == "solar_unexplained")
    assert sum(r.points for r in without.lines) == pytest.approx(without.score, abs=0.2)


def test_FR_PS_10_energy_budget_excess_is_flagged(demo_sim, cfg):
    """A registration of 0.2 kWp cannot explain the drop seen: the excess counts and the penalty is dropped."""
    scn, tables, truth = demo_sim
    pid = case_premise(truth, DEMO_ZONE, "solar", 0)               # registered self-consumption home
    events = tables["account_event"].with_columns(
        pl.when((pl.col("premise_id") == pid) & (pl.col("event_type") == "solar_registration"))
        .then(pl.lit(0.2)).otherwise(pl.col("capacity_kwp")).alias("capacity_kwp"))
    run = engine.run_tables({**tables, "account_event": events}, scn.start_date, scn.days, cfg, score_all=True)
    s = premise(run, DEMO_ZONE, pid).details["solar"]
    assert s["over_budget"] and s["budget"]["excess_kwh"] > 0 and s["budget"]["psh_source"] == "weather"
    assert s["penalty"]["verdict"] == "over_budget" and not s["penalty"]["applies"]
    line = next(r for r in premise(run, DEMO_ZONE, pid).reasons if r["feature"] == "solar_unexplained")
    assert "more than a 0.2 kWp system can produce" in line["reason_text"]
    # The real 3 kWp registration explains the same drop.
    real = next(p for p in engine.run_tables(tables, scn.start_date, scn.days, cfg, score_all=True).zones[DEMO_ZONE].premises
                if p.premise_id == pid).details["solar"]
    assert not real["over_budget"] and real["budget"]["expected_kwh"] > real["budget"]["drop_kwh"]


def test_FR_PS_10_energy_budget_without_weather_uses_labelled_default(cfg):
    from voltguard.detection.features import peak_sun_hours
    psh, source = peak_sun_hours(None, slice(0, 10), {**cfg["solar"]})
    assert source == "assumed" and psh == max(cfg["solar"]["psh_default"])


def test_FR_PS_10_rainy_day_rebound_separates_solar_from_bypass(solar_run, solar_sim, cfg):
    _, _, truth = solar_sim
    rebound = lambda kind, nth=0: premise(solar_run, ZONE, case_premise(truth, ZONE, kind, nth)).details["solar"]["rain_rebound"]
    # Exporting solar homes give daytime use back on cloudy days; a bypass stays low whatever the weather.
    # (A self-consumption system large enough to cover all daytime use on cloudy days too shows no
    # rebound: then the sun-shaped drop and the zeroed midday carry the solar check instead.)
    assert rebound("solar", 1) >= cfg["solar"]["rebound_min"]
    assert rebound("solar_unregistered_export") >= cfg["solar"]["rebound_min"]
    assert rebound("partial_bypass") < cfg["solar"]["rebound_min"]
    assert rebound("solar_with_theft", 1) < cfg["solar"]["rebound_min"]


def test_FR_PS_10_voltage_signature_and_timing_are_supporting_only(solar_run, solar_sim):
    _, _, truth = solar_sim
    exporter = premise(solar_run, ZONE, case_premise(truth, ZONE, "solar", 1)).details["solar"]["voltage"]
    assert exporter["supports_solar"] and exporter["midday_rise_v"] > 0         # reverse power flow at midday
    rig = premise(solar_run, ZONE, case_premise(truth, ZONE, "solar_with_theft", 0))
    assert rig.details["solar"]["voltage"]["supports_hidden_load"]               # night dip beside the hidden rig
    # Timing on its own never lifts a premise: it needs other evidence above the tenancy gate.
    for p in solar_run.zones[ZONE].premises:
        if any(r["feature"] == "solar_timing" for r in p.reasons):
            assert p.score >= 25


def test_FR_PS_10_unregistered_export_gets_follow_up_not_theft(solar_run, solar_sim):
    _, _, truth = solar_sim
    p = premise(solar_run, ZONE, case_premise(truth, ZONE, "solar_unregistered_export"))
    assert p.details["solar"]["export"] and not p.details["solar"]["registered"]
    assert p.details["solar"]["follow_up"] == "unregistered_export"
    assert p.rank > top_k(solar_run.zones[ZONE].zone.n)


def test_FR_PS_10_battery_marks_night_comparison_low_confidence(solar_run, solar_sim):
    _, _, truth = solar_sim
    s = premise(solar_run, ZONE, case_premise(truth, ZONE, "solar_with_battery")).details["solar"]
    assert s["has_battery"] and s["night_confidence"] == "low"
    assert s["night"]["window"] == "00:00-07:00" and s["penalty"]["confidence"] == "low"


def test_FR_PS_10_registration_carries_capacity_and_battery(solar_sim):
    _, tables, truth = solar_sim
    regs = tables["account_event"].filter(pl.col("event_type") == "solar_registration")
    assert regs["capacity_kwp"].null_count() == 0
    battery = case_premise(truth, ZONE, "solar_with_battery")
    assert regs.filter(pl.col("premise_id") == battery)["has_battery"].to_list() == [True]
    from voltguard.data.canonical import TABLES
    assert {"capacity_kwp", "has_battery"} <= set(TABLES["account_event"].names)
    assert not TABLES["account_event"].column("capacity_kwp").required


# --------------------------------------------------------------------------- shown in the API and the report

SOLAR_THIEF = "P-CEN-001-069"        # demo zone: registered solar home that also bypasses part of its night load


def _demo_case(truth_kind: str, nth: int = 0) -> str:
    scn = simulator.demo_scenario()
    _, truth = simulator.simulate(scn)
    return case_premise(truth, DEMO_ZONE, truth_kind, nth)


def test_FR_PS_10_api_marks_solar_with_unexplained_night_use(api):
    from tests.conftest import login

    analyst = login(api, "analyst.cen")
    suspects = {s["premise_id"]: s for s in api.get(f"/zones/{DEMO_ZONE}/suspects?limit=500", headers=analyst).json()["suspects"]}
    assert suspects[SOLAR_THIEF]["solar_unexplained"] and "solar" in suspects[SOLAR_THIEF]["tags"]
    assert not any(s["solar_unexplained"] for pid, s in suspects.items() if pid != SOLAR_THIEF and "solar" not in s["tags"])
    check = api.get(f"/premises/{SOLAR_THIEF}", headers=analyst).json()["solar_check"]
    assert check["verdict"] == "night_unexplained" and check["night_by"] in ("drop", "peers")
    names = [c["check"] for c in check["checks"]]
    assert names[:7] == ["registration", "export", "day_vs_night", "sun_shape", "rain_rebound", "energy_budget", "voltage"]
    assert next(c for c in check["checks"] if c["check"] == "day_vs_night")["status"] == "against"
    assert {c["status"] for c in check["checks"]} <= {"pass", "against", "not_seen", "no_data"}


def test_FR_PS_10_cleared_list_shows_plain_solar_with_reasons(api):
    from tests.conftest import login

    body = api.get(f"/zones/{DEMO_ZONE}/cleared", headers=login(api, "analyst.cen")).json()
    cleared = {c["premise_id"]: c for c in body["cleared"]}
    for nth in (0, 1):
        pid = _demo_case("solar", nth)
        assert pid in cleared and any(i["kind"] == "solar" for i in cleared[pid]["items"])
    assert SOLAR_THIEF not in cleared or not any(i["kind"] == "solar" for i in cleared[SOLAR_THIEF]["items"])
    ev = _demo_case("ev_charging")
    assert ev in cleared and cleared[ev]["items"][0]["kind"] == "ev_charging"
    plain = api.get(f"/premises/{_demo_case('solar', 0)}", headers=login(api, "analyst.cen")).json()["solar_check"]
    assert plain["verdict"] == "explained"
    # Zone-level users never get premise lists (FR-UI-01); other regions are refused by row-level security.
    assert api.get(f"/zones/{DEMO_ZONE}/cleared", headers=login(api, "manager.cen")).status_code == 403
    assert api.get(f"/zones/{DEMO_ZONE}/cleared", headers=login(api, "analyst.nor")).status_code in (403, 404)


def test_FR_PS_10_inspector_gets_solar_checklist(api):
    from voltguard import db
    from voltguard.service import cases

    with db.admin_connection() as conn:
        visit = cases._solar_visit(conn, SOLAR_THIEF)
        assert visit["checklist"] == list(cases.SOLAR_CHECKLIST) and visit["registered"]
        assert visit["capacity_kwp"] and visit["expected_kwh_per_day"] > 0
        assert visit["reason_tags"] == {"false_alarm": "solar_confirmed_no_theft", "confirmed_theft": "solar_plus_bypass"}
        assert cases._solar_visit(conn, _demo_case("full_bypass_mining")) is None


def test_FR_PS_10_weekly_report_counts_solar(api):
    from tests.conftest import login

    manager = login(api, "manager.cen")
    s = api.get("/weekly", headers=manager).json()["solar"]
    assert s["tagged"] >= 3 and s["suspected"] >= 1 and s["registrations"] >= 2
    for lang, heading in (("en", "Rooftop solar in ranked zones"), ("ms", "Solar bumbung dalam zon yang disenaraikan")):
        html = api.get(f"/weekly/html?lang={lang}", headers=manager).text
        assert heading in html and SOLAR_THIEF not in html          # counts only: zone-level report
