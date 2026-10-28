"""Weekly report rules and page (no database): summary, takeaways, Wilson intervals, next steps,
empty weeks, tariff set/unset, simulated vs uploaded data, schedule, and an HTML snapshot."""

from __future__ import annotations

import copy
from datetime import datetime, timezone

import pytest

from voltguard.service import digest, digest_render as r

HEADINGS = {"en": ["1 · Key figures", "Why two dates?", "2 · Is energy still going missing?", "3 · Where is it going missing?",
                   "Value at risk (estimate)", "4 · Are inspections finding theft?", "5 · Can these figures be trusted?",
                   "Assumptions and limits", "6 · Recommended next steps", "Glossary"],
            "ms": ["1 · Angka utama", "Mengapa dua tarikh?", "2 · Adakah tenaga masih hilang?", "3 · Di mana tenaga hilang?",
                   "Nilai berisiko (anggaran)", "4 · Adakah pemeriksaan menemui kecurian?", "5 · Bolehkah angka ini dipercayai?",
                   "Andaian dan had", "6 · Langkah seterusnya yang disyorkan", "Glosari"]}


def week(**over) -> dict:
    """Figures shaped like digest.build() for region CEN (the demo's current week)."""
    d = {
        "region": "CEN", "report_id": "VG-WK-CEN-2026-W44", "generated_at": "2026-10-28T02:13:00+00:00",
        "generated_myt": "2026-10-28T10:13+08:00", "empty": False,
        "energy_window": {"from": "2026-09-24", "to": "2026-09-30"}, "work_window": {"from": "2026-10-21", "to": "2026-10-28"},
        "window_gap_days": 28, "data_mode": {"simulated": True, "outcomes_simulated": True, "sources": {}},
        "kpis": {"flagged_zones": 2, "flagged_zones_prev": 2, "zones_with_balance": 3, "zones_without_balance": 1,
                 "unexplained_kwh_per_day": 285, "unexplained_kwh_per_day_prev": 292, "unexplained_change_pct": -2.5,
                 "unexplained_kwh_per_month": 8554, "value_at_risk": "[TNB tariff: to be supplied]", "cases_opened": 0,
                 "cases_closed": 0, "cases_opened_prev": 0, "cases_closed_prev": 0, "cases_closed_total": 10, "cases_overdue": 0,
                 "reports_exported": 0, "reports_exported_prev": 0, "open_alerts": 0, "alerts_this_week": 0},
        "region_margin_kwh": 58, "week_average": {"this": 285, "prev": 292},
        "daily_gap": [{"date": f"2026-09-{17 + i:02d}", "gap_kwh": 290 - i, "margin_kwh": 58} for i in range(14)],
        "zones": [
            {"transformer_id": "TX-CEN-002", "district": "Petaling", "gap_kwh_per_day": 156.0, "gap_pct": 16.2, "margin_kwh": 31.0,
             "threshold_kwh": 48.0, "supply_kwh_per_day": 960, "flagged": True, "priority": "large_load", "gap_start": "2026-08-31",
             "gap_since_start": False, "flatness_cv": 0.05, "open_cases": 0, "suspects_without_case": 1},
            {"transformer_id": "TX-CEN-001", "district": "Petaling", "gap_kwh_per_day": 128.0, "gap_pct": 9.1, "margin_kwh": 28.0,
             "threshold_kwh": 70.0, "supply_kwh_per_day": 1400, "flagged": True, "priority": "normal", "gap_start": None,
             "gap_since_start": True, "flatness_cv": 0.16, "open_cases": 0, "suspects_without_case": 2},
            {"transformer_id": "TX-CEN-003", "district": "Klang", "gap_kwh_per_day": 1.0, "gap_pct": 0.1, "margin_kwh": 25.0,
             "threshold_kwh": 50.0, "supply_kwh_per_day": 800, "flagged": False, "priority": "normal", "gap_start": None,
             "gap_since_start": False, "flatness_cv": None, "open_cases": 0, "suspects_without_case": 0}],
        "no_balance_zones": [{"transformer_id": "TX-CEN-004", "district": "Klang", "open_cases": 0}],
        "top_zones": [],
        "value": {"kwh_per_month": 8554, "kwh_per_month_above_threshold": 4980, "rm_per_kwh": None, "tariff_source": None},
        "cases_by_status": {"closed": 10},
        "outcomes_this_week": {}, "outcomes_all_time": {"confirmed_theft": 8, "false_alarm": 10, "inconclusive": 2, "no_access": 1},
        "hit_rates": {"model_ranked": {"inspections": 16, "confirmed_theft": 7, "hit_rate_pct": 43.8, "ci_low_pct": 23.1, "ci_high_pct": 66.8},
                      "random_sample": {"inspections": 4, "confirmed_theft": 1, "hit_rate_pct": 25.0, "ci_low_pct": 4.6, "ci_high_pct": 69.9}},
        "quality": {"meter_days_complete_pct": 100.0, "monthly_read_pct": 12.0, "zones_without_dtm": 1, "fallbacks": ["AS-2", "AS-3-simulated", "AS-9"]},
        "model": {"scoring": "r0-additive/pattern-v1", "retrained": None, "retrained_at": None, "labels": 20},
        "thresholds": {"share_of_supply": 0.05, "min_gap_kwh_per_day": 15.0, "consecutive_days": 7, "large_load_share": 0.15,
                       "flat_cv": 0.2, "min_random_checks": 10, "escalation_hours": 72},
    }
    for key, value in over.items():
        d[key] = value
    return d


def test_wilson_intervals():
    lo, hi = digest.wilson(7, 16)
    assert round(lo, 3) == 0.231 and round(hi, 3) == 0.668
    lo, hi = digest.wilson(1, 4)
    assert round(lo, 3) == 0.046 and round(hi, 3) == 0.699
    assert digest.wilson(0, 0) is None
    assert digest.wilson(0, 5)[0] == 0.0 and digest.wilson(5, 5)[1] == 1.0


def test_summary_rules_steady_week_with_flat_priority_zone():
    sentences, actions = r.summary(week())
    assert sentences[0] == ("Unexplained energy in region CEN averaged 285 kWh a day, 2.5% lower than the week before, "
                            "so the leak is steady, not growing.")
    assert sentences[1] == ("2 of 3 zones are flagged; TX-CEN-002 alone accounts for 55% of the unexplained energy "
                            "and draws a flat 24/7 load typical of mining rigs.")
    assert sentences[2] == "No cases were opened or closed this week and no inspections were recorded."
    assert len(actions) == 2 and "TX-CEN-002 and TX-CEN-001" in actions[0] and "joint operation" in actions[0]
    busy = week()
    busy["kpis"]["cases_opened"] = 5
    assert r.summary(busy)[0][2] == "5 case(s) were opened and 0 closed this week; no inspections were recorded yet."
    busy["outcomes_this_week"] = {"confirmed_theft": 1, "false_alarm": 2}
    assert r.summary(busy)[0][2] == "5 case(s) were opened and 0 closed this week; 3 inspection(s) were recorded."


@pytest.mark.parametrize("change, avg, margin, expected", [
    (-2.5, 285, 58, ("steady", True)), (25.0, 285, 58, ("rising", True)), (-30.0, 285, 58, ("falling", True)),
    (-2.5, 40, 58, ("steady", False)), (None, 285, 58, ("steady", True)), (None, None, 58, ("none", False))])
def test_trend_rule(change, avg, margin, expected):
    d = week(region_margin_kwh=margin, week_average={"this": avg, "prev": 292})
    d["kpis"]["unexplained_change_pct"] = change
    assert r.trend(d) == expected


def test_energy_takeaways():
    assert r.energy_takeaway(week()).startswith("About 285 kWh a day goes unrecorded, well above the margin of error (±58 kWh) and steady")
    assert "continuous load" in r.energy_takeaway(week())
    rising = week()
    rising["kpis"]["unexplained_change_pct"] = 20.0
    assert "rising: +20% on the week before" in r.energy_takeaway(rising)
    inside = week(region_margin_kwh=400)
    assert "inside the margin of error" in r.energy_takeaway(inside)


def test_zone_takeaway_names_priority_and_explains_unflagged_zone():
    text = r.zones_takeaway(week())
    assert text.startswith("TX-CEN-002 is the priority: the largest flagged leak, above 15% of its supply, flat around the clock.")
    assert "TX-CEN-003's 1 kWh a day sits inside its margin of error, so it is not flagged." in text
    quiet = week()
    for z in quiet["zones"]:
        z["flagged"] = False
    assert r.zones_takeaway(quiet).startswith("No zone is flagged")


def test_hit_rate_takeaway_overlap_apart_and_synthetic():
    text = r.hits_takeaway(week())
    assert "look better (44% vs 25%), but the ranges overlap: 4 random check(s) are too few" in text
    assert "No inspections were recorded this week." in text and "simulated cases" in text
    apart = week()
    apart["hit_rates"]["random_sample"].update(hit_rate_pct=5.0, ci_low_pct=1.0, ci_high_pct=15.0, inspections=40)
    assert r.hit_comparison(apart) == "apart" and "unlikely to be chance" in r.hits_takeaway(apart)
    real = week(data_mode={"simulated": False, "outcomes_simulated": False, "sources": {}}, hit_rates={})
    assert r.hits_takeaway(real).startswith("No inspection has been labelled yet") and "simulated" not in r.hits_takeaway(real)


def test_next_step_rules_and_limit():
    keys = [k for k, _ in r.next_steps(week())]
    assert keys == ["n_case_job_joint", "n_random", "n_tariff"]
    busy = week()
    busy["kpis"].update(cases_overdue=3, open_alerts=2)
    assert [k for k, _ in r.next_steps(busy)] == ["n_case_job_joint", "n_overdue", "n_alerts"]
    calm = week(value={**week()["value"], "rm_per_kwh": 0.5})
    for z in calm["zones"]:
        z["suspects_without_case"] = 0
        z["priority"] = "normal"
    calm["hit_rates"]["random_sample"]["inspections"] = 12
    assert r.next_steps(calm) == []
    assert "No action stands out" in r.render_html(calm)


def test_tariff_unset_then_set():
    unset = r.value_text(week())
    assert "[TNB tariff per kWh: to be supplied]" in unset and "RM " not in unset.replace("[TNB", "")
    set_ = r.value_text(week(value={**week()["value"], "rm_per_kwh": 0.5, "tariff_source": "test"}))
    assert "about RM 4,277 a month (estimate, tariff RM 0.5/kWh; test)" in set_ and "(about RM 2,490)" in set_
    assert "Tariff not yet supplied" not in " ".join(r.assumptions(week(value={**week()["value"], "rm_per_kwh": 0.5})))


def test_simulated_versus_uploaded_data():
    sim = r.render_html(week())
    assert "Simulated data (R0): not TNB data" in sim and "simulated meter data end on 30 Sep 2026" in sim
    real = week(data_mode={"simulated": False, "outcomes_simulated": False, "sources": {"meter_reading": "upload:tnb_w44"}})
    page = r.render_html(real)
    assert "Simulated data (R0)" not in page and "Meter data have not arrived since 30 Sep 2026" in page
    assert not any("Simulated data." in a for a in r.assumptions(real))


def test_empty_week():
    assert "No detection results yet." in r.render_html({"region": "CEN", "empty": True})
    quiet = week(week_average={"this": None, "prev": None}, daily_gap=[])
    quiet["kpis"]["unexplained_change_pct"] = None
    assert r.summary(quiet)[0][0] == "There are no meter data for this week, so unexplained energy cannot be measured."
    assert r.energy_takeaway(quiet) == "No meter data for this week, so there is nothing to compare."
    assert "No meter data" in r.chart_energy(quiet)


@pytest.mark.parametrize("lang", ["en", "ms"])
def test_html_snapshot_has_every_section_and_no_personal_details(lang):
    page = r.render_html(week(), lang)
    for heading in HEADINGS[lang]:
        assert heading in page, heading
    assert not r.PREMISE_ID.search(page) and "FAKE" not in page and "binti" not in page
    assert page.count("<svg") == 3 and f'lang="{lang}"' in page


def test_malay_rule_sentences():
    sentences, _ = r.summary(week(), "ms")
    assert sentences[0].startswith("Tenaga yang tidak dapat dijelaskan di wilayah CEN purata 285 kWh sehari, 2.5% lebih rendah")
    assert "dan " in r.step_text(*r.next_steps(week())[0], week(), "ms")


def test_headline_counts_only():
    text = r.headline(week())
    assert text.startswith("2 flagged zone(s), 285 kWh/day unexplained (−2.5% vs the week before)")
    assert "model-ranked hit rate 44%" in text and "Next: Supervisor: run the case job" in text
    assert not r.PREMISE_ID.search(text)


def test_weekly_schedule_due_once_per_week():
    cfg = {"weekly": {"day_of_week": 0, "hour": 8, "minute": 0}}
    tuesday_7am = datetime(2026, 10, 26, 23, 0, tzinfo=timezone.utc)      # Tue 27 Oct, 07:00 MYT
    assert digest.due(datetime(2026, 10, 26, 0, 30, tzinfo=timezone.utc), cfg, None) == "2026-W44"     # Mon 08:30 MYT
    assert digest.due(datetime(2026, 10, 25, 23, 30, tzinfo=timezone.utc), cfg, "2026-W43") is None    # Mon 07:30 MYT: W43 slot sent
    assert digest.due(datetime(2026, 10, 26, 0, 30, tzinfo=timezone.utc), cfg, "2026-W44") is None
    assert digest.due(tuesday_7am, cfg, "2026-W44") is None
    sunday = {"weekly": {"day_of_week": 6, "hour": 20, "minute": 0}}
    # Monday morning after a Sunday 20:00 slot: the slot's own week counts, so it is not sent twice.
    assert digest.due(datetime(2026, 10, 26, 1, 0, tzinfo=timezone.utc), sunday, "2026-W43") is None
    assert digest.due(datetime(2026, 10, 26, 1, 0, tzinfo=timezone.utc), sunday, "2026-W42") == "2026-W43"


def test_tariff_file_unset_by_default():
    assert digest.tariff() == {"rm_per_kwh": None, "source": None}


def test_week_fixture_is_not_mutated():
    d = week()
    snapshot = copy.deepcopy(d)
    r.render_html(d, "ms")
    assert d == snapshot
