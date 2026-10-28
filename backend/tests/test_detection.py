"""Detection engine prototype tests (SRS 3.1-3.3, SDD 5) on simulated zones."""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import polars as pl
import pytest

from tests.conftest import case_premise, rank_of, top_k
from voltguard.data import simulator
from voltguard.data.simulator import Injected, Scenario, ZoneSpec
from voltguard.detection import engine
from voltguard.detection.features import FEATURE_NAMES

DEMO_ZONE = "TX-CEN-001"        # day-one mining tap + partial bypass + legitimate look-alikes
MINING_ZONE = "TX-CEN-002"      # mining tap starting on day 30
NO_DTM_ZONE = "TX-CEN-004"      # no transformer meter
CONV_ZONE = "TX-CEN-003"        # 40% monthly-read meters, home business, no theft
CLEAN_ZONE = "TX-NOR-003"


def _run(scn: Scenario, cfg, score_all=False):
    tables, truth = simulator.simulate(scn)
    return engine.run_tables(tables, scn.start_date, scn.days, cfg, score_all=score_all), truth, tables


# --------------------------------------------------------------------------- data ingestion

def test_FR_DI_01_readings_round_trip_match_generator(demo_sim, tmp_path, monkeypatch):
    scn, tables, truth = demo_sim
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    simulator.write_run(scn, tables, truth)
    loaded = simulator.load_run_tables(scn.name)
    for name, frame in tables.items():
        assert loaded[name].height == frame.height, name
    smart = tables["meter"].filter(pl.col("meter_type") == "smart").height
    expected = smart * scn.days * 48
    # The generator drops a small share of intervals on purpose (missing_rate 0.2%).
    assert 0.99 * expected <= tables["meter_reading"].height <= expected


def test_FR_DI_02_voltage_for_smart_meters_only(demo_sim):
    _, tables, _ = demo_sim
    meters = tables["meter"]
    with_readings = set(tables["meter_reading"]["meter_id"].unique().to_list())
    conventional = set(meters.filter(pl.col("meter_type") == "conventional")["meter_id"].to_list())
    assert conventional and not (conventional & with_readings)
    assert tables["meter_reading"]["voltage_v"].null_count() == 0


def test_FR_DI_03_supply_equals_homes_plus_loss_plus_taps(demo_sim):
    scn, tables, truth = demo_sim
    zt = truth["zones"][MINING_ZONE]
    days = scn.days
    supplied = tables["transformer_reading"].filter(pl.col("transformer_id") == MINING_ZONE)["kwh_supplied"].sum()
    meters = tables["meter"].join(tables["premise"], on="premise_id").filter(pl.col("transformer_id") == MINING_ZONE)
    smart_kwh = tables["meter_reading"].filter(pl.col("meter_id").is_in(meters["meter_id"].to_list()))["kwh"].sum()
    monthly_kwh = tables["meter_monthly_reading"].filter(pl.col("meter_id").is_in(meters["meter_id"].to_list()))["kwh"].sum()
    loss = sum(zt["tech_loss_kwh_daily"])
    stolen = sum(c["stolen_kwh_per_day"] * (days - c["start_day"]) for c in zt["cases"] if c["is_theft"])
    # Transformer meter class 0.5 and 0.2% missing smart intervals leave a small residual.
    assert supplied == pytest.approx(smart_kwh + monthly_kwh + loss + stolen, rel=0.01)


def test_FR_DI_04_every_meter_linked_to_one_transformer(demo_sim):
    _, tables, _ = demo_sim
    linked = tables["meter"].join(tables["premise"], on="premise_id", how="left")
    assert linked["transformer_id"].null_count() == 0
    assert linked.group_by("meter_id").agg(pl.col("transformer_id").n_unique())["transformer_id"].max() == 1
    assert tables["premise"]["street_seq"].null_count() == 0


def test_FR_DI_05_tenancy_change_at_injected_thief(demo_sim):
    _, tables, truth = demo_sim
    thief = case_premise(truth, DEMO_ZONE, "partial_bypass")
    events = tables["account_event"].filter((pl.col("premise_id") == thief) & (pl.col("event_type") == "change_of_tenancy"))
    assert events.height == 1


def test_FR_DI_06_missing_day_flags_meter(demo_sim, cfg):
    scn, tables, _ = demo_sim
    meter = tables["meter_reading"]["meter_id"][0]
    day = scn.start_date + timedelta(days=10)
    readings = tables["meter_reading"].with_columns(pl.col("ts").dt.date().alias("_d"))
    cut = readings.filter(~((pl.col("meter_id") == meter) & (pl.col("_d") == day))).drop("_d")
    run = engine.run_tables({**tables, "meter_reading": cut}, scn.start_date, scn.days, cfg)
    flags = [f for zr in run.zones.values() for f in zr.quality_flags]
    assert any(f["meter_id"] == meter and f["date"] == day and f["completeness"] == 0 for f in flags)


# --------------------------------------------------------------------------- zone detection

def test_FR_ZD_01_gap_matches_injected_energy_including_day_one_tap(demo_run, demo_sim):
    _, _, truth = demo_sim
    for zone in (DEMO_ZONE, MINING_ZONE):
        b = demo_run.zones[zone].balance
        cases = [c for c in truth["zones"][zone]["cases"] if c["is_theft"]]
        recent_stolen = sum(c["stolen_kwh_per_day"] for c in cases if c["start_day"] <= b.dates.__len__() - 7)
        assert np.mean(b.gap_kwh[-7:]) == pytest.approx(recent_stolen, rel=0.2), zone
    # The demo zone's mining tap runs from day one: the gap is there on the first day.
    day_one_stolen = sum(c["stolen_kwh_per_day"] for c in truth["zones"][DEMO_ZONE]["cases"] if c["is_theft"] and c["start_day"] == 0)
    assert np.mean(demo_run.zones[DEMO_ZONE].balance.gap_kwh[:7]) == pytest.approx(day_one_stolen, rel=0.2)


def test_FR_ZD_02_taps_flagged_clean_zones_not(demo_run):
    assert demo_run.zones[DEMO_ZONE].balance.flagged
    assert demo_run.zones[MINING_ZONE].balance.flagged
    assert not demo_run.zones[CLEAN_ZONE].balance.flagged
    assert not demo_run.zones[CONV_ZONE].balance.flagged


def test_FR_ZD_02_large_load_priority(cfg):
    scn = Scenario("large", 77, [ZoneSpec(1, n_homes=50, cases=[Injected("full_bypass_mining", start_day=10, size=10.0)])], days=40)
    run, _, _ = _run(scn, cfg)
    b = run.zones["TX-CEN-001"].balance
    assert b.flagged and b.priority == "large_load"


def test_FR_ZD_03_gap_start_estimated_or_present_since_start(demo_run, demo_sim):
    scn, _, truth = demo_sim
    b = demo_run.zones[MINING_ZONE].balance
    start = [c for c in truth["zones"][MINING_ZONE]["cases"] if c["is_theft"]][0]["start_day"]
    assert b.gap_start is not None and abs((b.gap_start - scn.start_date).days - start) <= 3
    day_one = demo_run.zones[DEMO_ZONE].balance
    assert day_one.gap_since_start and day_one.gap_start is None


def test_FR_ZD_04_mining_gap_is_flat_partial_bypass_is_not(demo_run_all):
    assert demo_run_all.zones[MINING_ZONE].balance.flatness_cv < 0.2
    partial_only = demo_run_all.zones["TX-NOR-001"].balance
    assert partial_only.flatness_cv is None or partial_only.flatness_cv >= 0.2


def test_FR_ZD_05_many_conventional_meters_still_flag_mining(cfg):
    scn = Scenario("conv", 31, [ZoneSpec(1, n_homes=70, conventional_share=0.5,
                                         cases=[Injected("full_bypass_mining", start_day=15, size=5.0)])], days=61)
    run, _, _ = _run(scn, cfg)
    b = run.zones["TX-CEN-001"].balance
    assert b.flagged
    assert np.all(b.estimated_kwh > 0) and np.all(b.uncertainty_kwh > 0)


def test_FR_ZD_06_no_transformer_meter_ranked_low_confidence(demo_run):
    zr = demo_run.zones[NO_DTM_ZONE]
    assert not zr.balance.balance_available
    assert zr.premises and all(p.confidence == "low" for p in zr.premises)
    assert any("no balance available" in n for n in zr.balance.notes)


# --------------------------------------------------------------------------- premise scoring

def test_FR_PS_01_every_premise_in_flagged_zone_scored(demo_run):
    for zr in demo_run.zones.values():
        if zr.balance.flagged:
            assert len(zr.premises) == zr.zone.n
            assert all(0 <= p.score <= 100 for p in zr.premises)


def test_FR_PS_02_voltage_locates_tap_on_its_phase(demo_run, demo_sim):
    _, tables, truth = demo_sim
    thief = case_premise(truth, MINING_ZONE, "full_bypass_mining")
    zr = demo_run.zones[MINING_ZONE]
    v = zr.voltage
    assert v.available and v.method == "residual"
    i = zr.zone.premise_ids.index(thief)
    phases = zr.zone.phase_index()
    branches = np.array(zr.zone.premises["feeder_branch"].to_list())
    same = (phases == phases[i]) & (branches == branches[i])
    other = (phases != phases[i]) & (branches == branches[i])
    # Deepest unexplained drop on the tap's own phase and branch; other phases barely move.
    assert v.signal_v[i] <= np.nanmin(v.signal_v[same]) + 0.3
    assert np.nanmean(np.abs(v.signal_v[other])) < 0.25 * abs(v.signal_v[i])
    assert v.tap_distance_m[i] <= 40
    assert rank_of(demo_run, MINING_ZONE, thief) <= 3


def test_FR_PS_03_all_usage_features_present(demo_run):
    for p in demo_run.zones[DEMO_ZONE].premises:
        assert set(FEATURE_NAMES) == set(p.features)


def test_FR_PS_04_timing_match_and_day_one_tap_in_top(demo_run, demo_sim):
    _, _, truth = demo_sim
    n = demo_run.zones[MINING_ZONE].zone.n
    thief = next(p for p in demo_run.zones[MINING_ZONE].premises if p.premise_id == case_premise(truth, MINING_ZONE, "full_bypass_mining"))
    assert thief.details.get("timing_days") is not None and abs(thief.details["timing_days"]) <= 2
    day_one = case_premise(truth, DEMO_ZONE, "full_bypass_mining")
    assert rank_of(demo_run, DEMO_ZONE, day_one) <= top_k(demo_run.zones[DEMO_ZONE].zone.n)
    assert n > 0


def test_FR_PS_05_legitimate_patterns_tagged_not_top(demo_run, demo_sim):
    _, _, truth = demo_sim
    k = top_k(demo_run.zones[DEMO_ZONE].zone.n)
    ev = case_premise(truth, DEMO_ZONE, "ev_charging")
    assert "ev_charging" in next(p.tags for p in demo_run.zones[DEMO_ZONE].premises if p.premise_id == ev)
    for kind in ("ev_charging", "metered_mining"):
        assert rank_of(demo_run, DEMO_ZONE, case_premise(truth, DEMO_ZONE, kind)) > k, kind
    negative = [r for p in demo_run.zones[DEMO_ZONE].premises if "ev_charging" in p.tags for r in p.reasons if r["contribution"] < 0]
    assert negative, "a legitimate-use tag shows as a negative reason"


def test_FR_PS_06_premises_without_interval_data_ranked_low_confidence(demo_run_all):
    zr = demo_run_all.zones[CONV_ZONE]
    conventional = [p for p in zr.premises if not p.smart]
    assert conventional and all(p.confidence == "low" for p in conventional)


def test_FR_PS_07_reasons_add_up_to_score(demo_run_all):
    for zr in demo_run_all.zones.values():
        for p in zr.premises:
            total = sum(r["contribution"] for r in p.reasons)
            assert total == pytest.approx(p.score, abs=0.051 * len(p.reasons)), p.premise_id
            named = [r for r in p.reasons if r["feature"] not in ("other", "capped")]
            assert len(named) <= 3


def test_NFR_08_flagged_premises_show_three_reasons(demo_run):
    for zr in demo_run.zones.values():
        for p in zr.premises[:5]:
            named = [r for r in p.reasons if r["feature"] not in ("other", "capped")]
            assert len(named) == 3 and all(r["reason_text"] for r in named), p.premise_id


def test_FR_PS_08_wording_describes_risk_only(demo_run_all):
    banned = ("thief", "stealing", "steals", "criminal", "guilty", "fraudster")
    for zr in demo_run_all.zones.values():
        for p in zr.premises:
            for r in p.reasons:
                assert not any(word in r["reason_text"].lower() for word in banned), r["reason_text"]


def test_FR_PS_09_tenancy_change_alone_not_top_and_capped(demo_run, demo_sim, cfg):
    _, _, truth = demo_sim
    k = top_k(demo_run.zones[DEMO_ZONE].zone.n)
    assert rank_of(demo_run, DEMO_ZONE, case_premise(truth, DEMO_ZONE, "tenancy_only")) > k
    for p in demo_run.zones[DEMO_ZONE].premises:
        for r in p.reasons:
            if r["feature"] == "tenancy_change":
                assert r["contribution"] <= 100 * cfg["tenancy"]["max_contribution"] + 0.05


def test_FR_PS_10_solar_homes_not_top_thief_still_is(demo_run, demo_sim):
    _, _, truth = demo_sim
    zr = demo_run.zones[DEMO_ZONE]
    k = top_k(zr.zone.n)
    for nth in (0, 1):
        pid = case_premise(truth, DEMO_ZONE, "solar", nth)
        assert rank_of(demo_run, DEMO_ZONE, pid) > k
        assert "solar" in next(p.tags for p in zr.premises if p.premise_id == pid)
    assert rank_of(demo_run, DEMO_ZONE, case_premise(truth, DEMO_ZONE, "partial_bypass")) <= k


def test_detection_creates_no_cases(demo_run):
    """POST /jobs/run-detection creates no cases: the engine returns scores only."""
    assert not hasattr(demo_run, "cases")


def test_FR_DI_07_district_weather_loaded_and_used(demo_sim):
    scn, tables, _ = demo_sim
    weather = tables["district_weather"]
    assert set(weather["district"].unique().to_list()) == {z.district for z in scn.zones}
    assert weather.height == len({z.district for z in scn.zones}) * scn.days
    from voltguard.detection.zone_input import build_zone_inputs

    zone = build_zone_inputs(tables, scn.start_date, scn.days)["TX-CEN-001"]
    assert zone.sunshine is not None and np.isfinite(zone.sunshine).all()    # the rooftop-solar check reads it (FR-PS-10)


def test_FR_PS_07_voltage_reason_at_the_premise_reads_naturally():
    from voltguard.detection.scoring import reason_text

    at = reason_text("voltage_proximity", {"group_drop_v": 1.1, "tap_distance": 0.0}, [])
    near = reason_text("voltage_proximity", {"group_drop_v": 1.1, "tap_distance": 63.6}, [])
    assert "at or right next to this premise" in at and "0 m" not in at
    assert "about 64 m from this premise" in near
