"""Nightly run in batches (NFR-01): small meter and zone batches give the same results as one batch."""

from __future__ import annotations

import psycopg

from voltguard import config
from voltguard.service import pipeline


def _scores(owner_url: str) -> dict:
    with psycopg.connect(owner_url) as conn:
        rows = conn.execute("SELECT premise_id, score, rank FROM premise_score WHERE run_date = (SELECT max(run_date) FROM premise_score)").fetchall()
        zones = conn.execute("SELECT transformer_id, flagged, round(gap_kwh_recent::numeric, 3) FROM zone_run "
                             "WHERE run_date = (SELECT max(run_date) FROM zone_run) ORDER BY 1").fetchall()
        readings = conn.execute("SELECT count(*), round(sum(kwh)::numeric, 3) FROM meter_reading").fetchone()
    return {"scores": sorted(rows), "zones": zones, "readings": readings}


def test_NFR_01_small_batches_give_the_same_results(api, pg, monkeypatch):
    original = config.thresholds

    def sizes(meter_batch, zone_batch):
        return lambda overrides=None: {**original(overrides), "pipeline": {"meter_batch": meter_batch, "zone_batch": zone_batch}}

    monkeypatch.setattr(config, "thresholds", sizes(10**9, 10**9))
    one = pipeline.run_detection("pipeline", progress=lambda m: None)
    reference = _scores(pg[0])
    monkeypatch.setattr(config, "thresholds", sizes(37, 2))
    steps = []
    batched = pipeline.run_detection("pipeline", progress=steps.append)
    assert sum("Detection: zones" in s for s in steps) >= 3 and sum("Loaded" in s for s in steps) >= 10
    assert _scores(pg[0]) == reference
    assert sorted(batched["flagged_zones"]) == sorted(one["flagged_zones"]) and batched["premises_scored"] == one["premises_scored"]
    assert batched["loaded"]["meter_reading"] == one["loaded"]["meter_reading"]
