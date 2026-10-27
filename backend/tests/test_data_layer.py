"""Data layer: upload area, validation, versions, source switching and adapters (prompt 3, FR-DI-*)."""

from __future__ import annotations

import shutil
from datetime import date, datetime, timedelta

import numpy as np
import polars as pl
import pytest
import yaml

from voltguard import config
from voltguard.data import ingest, simulator, sources
from voltguard.data.simulator import Injected, Scenario, ZoneSpec
from voltguard.detection import engine


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    """Own DATA_ROOT and a copy of config/, so activation never touches the repository."""
    cfg_dir = tmp_path / "config"
    shutil.copytree(config.REPO_ROOT / "config", cfg_dir)
    monkeypatch.setenv("DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("VG_CONFIG_DIR", str(cfg_dir))
    config.load_yaml.cache_clear()
    yield tmp_path
    config.load_yaml.cache_clear()


def upload_folder(root, name: str):
    folder = root / "data" / "uploads" / name
    folder.mkdir(parents=True)
    return folder


def small_scenario() -> Scenario:
    return Scenario("small", 4242, [
        ZoneSpec(1, n_homes=40, cases=[Injected("full_bypass_mining", start_day=5, size=5.0)]),
        ZoneSpec(2, n_homes=36, has_dtm=False),
    ], days=21)


def write_csvs(tables: dict[str, pl.DataFrame], folder) -> None:
    for name, frame in tables.items():
        out = frame
        for col, dtype in frame.schema.items():
            if isinstance(dtype, pl.Datetime):
                out = out.with_columns(pl.col(col).dt.strftime("%Y-%m-%dT%H:%M:%S%:z"))
        out.write_csv(folder / f"{name}.csv")


def test_upload_templates_are_a_valid_dataset(isolated):
    folder = upload_folder(isolated, "templates")
    for path in (config.REPO_ROOT / "data" / "uploads" / "templates").glob("*.csv"):
        shutil.copy(path, folder)
    result = ingest.ingest("templates", folder)
    assert result.ok, result.report.to_json()
    assert set(result.report.rows) == set(sources.TABLES)


def test_bad_upload_is_rejected_with_reasons(isolated):
    folder = upload_folder(isolated, "bad")
    (folder / "transformer.csv").write_text(
        "transformer_id,region,district,capacity_kva,has_dtm\nTX-1,CEN,Petaling,500,maybe\n", encoding="utf-8")
    (folder / "premise.csv").write_text(
        "premise_id,transformer_id,street_seq,premise_type,tariff\nP-1,TX-1,1,terrace,domestic\nP-2,TX-9,2,castle,domestic\n", encoding="utf-8")
    (folder / "meter.csv").write_text(
        "meter_id,premise_id,meter_type,read_frequency,installed_on\nM-1,P-1,smart,30min,2024-01-01\nM-1,P-2,smart,30min,2024-01-01\n",
        encoding="utf-8")
    (folder / "meter_reading.csv").write_text(
        "meter_id,ts,kwh\nM-1,2026-08-01T00:00:00+08:00,0.4\nM-1,2026-08-01T00:10:00+08:00,999\nM-2,2026-08-01T00:30:00+08:00,abc\n",
        encoding="utf-8")
    result = ingest.ingest("bad", folder)
    assert not result.ok
    checks = {(i.table, i.check) for i in result.report.issues if i.level == "error"}
    assert ("transformer", "type") in checks                 # has_dtm "maybe"
    assert ("premise", "allowed_values") in checks           # premise_type "castle"
    assert ("premise", "link") in checks                     # TX-9 unknown
    assert ("meter", "duplicates") in checks                 # M-1 twice with different premises
    assert ("meter_reading", "range") in checks              # 999 kWh in half an hour
    assert ("meter_reading", "interval") in checks           # 00:10 is not a 30-minute boundary
    assert ("meter_reading", "type") in checks               # "abc"
    assert ("meter_reading", "link") in checks               # M-2 not in meter table
    manifest = sources.dataset_versions("bad")[-1]
    assert manifest["status"] == "rejected"
    assert (result.folder / "validation.html").exists() and (folder / "_reports" / "v1" / "validation.json").exists()
    assert not list(result.folder.glob("*.parquet"))


def test_FR_DI_06_upload_with_missing_intervals_flags_meter(isolated):
    scn = small_scenario()
    tables, _ = simulator.simulate(scn)
    meter = tables["meter_reading"]["meter_id"][0]
    day = scn.start_date + timedelta(days=7)
    tables["meter_reading"] = tables["meter_reading"].filter(
        ~((pl.col("meter_id") == meter) & (pl.col("ts").dt.date() == day) & (pl.col("ts").dt.hour() < 6)))
    folder = upload_folder(isolated, "gappy")
    write_csvs({k: tables[k] for k in ("transformer", "premise", "meter", "meter_reading")}, folder)
    result = ingest.ingest("gappy", folder)
    assert result.ok
    flagged = [f for f in result.report.flagged_meters if f["meter_id"] == meter and f["date"] == day.isoformat()]
    assert flagged and flagged[0]["completeness"] <= 0.75


def test_column_map_units_and_timezone(isolated):
    folder = upload_folder(isolated, "mapped")
    shutil.copy(config.REPO_ROOT / "data" / "uploads" / "templates" / "transformer.csv", folder)
    shutil.copy(config.REPO_ROOT / "data" / "uploads" / "templates" / "premise.csv", folder)
    shutil.copy(config.REPO_ROOT / "data" / "uploads" / "templates" / "meter.csv", folder)
    (folder / "mdms.csv").write_text("METER_NO,READ_START,KWH_WH\nMTR-001001,2026-08-01 00:00:00,412\n"
                                     "MTR-001001,2026-07-31T16:30:00Z,398\n", encoding="utf-8")
    (folder / "column_map.yaml").write_text(yaml.safe_dump({"files": {"mdms.csv": {
        "table": "meter_reading", "columns": {"METER_NO": "meter_id", "READ_START": "ts", "KWH_WH": "kwh"},
        "units": {"kwh": "Wh"}}}}), encoding="utf-8")
    result = ingest.ingest("mapped", folder)
    assert result.ok, result.report.to_json()
    readings = result.tables["meter_reading"].sort("ts")
    assert readings["kwh"].to_list() == pytest.approx([0.412, 0.398])
    local = [t.replace(tzinfo=None) for t in readings["ts"].to_list()]
    assert local == [datetime(2026, 8, 1, 0, 0), datetime(2026, 8, 1, 0, 30)]   # 16:30Z = 00:30 +08:00
    assert any(i.check == "timezone" for i in result.report.issues)
    assert "voltage_v" in result.report.missing_optional["meter_reading"]


def test_switch_to_uploaded_dataset_without_code_changes(isolated):
    """Same simulated data as an upload: activation is a config change and detection gives the same result."""
    scn = small_scenario()
    tables, truth = simulator.simulate(scn)
    folder = upload_folder(isolated, "sim_upload")
    write_csvs(tables, folder)
    result = ingest.ingest("sim_upload", folder, activate=True)
    assert result.ok, result.report.to_json()
    active = sources.active_sources()
    assert active["meter_reading"] == "upload:sim_upload@v1" and active["transformer"] == "upload:sim_upload@v1"
    loaded = sources.load_active_tables()
    start, days = sources.period(loaded)
    assert (start, days) == (scn.start_date, scn.days)
    cfg = config.thresholds()
    via_upload = engine.run_tables(loaded, start, days, cfg)
    direct = engine.run_tables(tables, scn.start_date, scn.days, cfg)
    for tx in direct.zones:
        assert via_upload.zones[tx].balance.flagged == direct.zones[tx].balance.flagged
        assert [p.premise_id for p in via_upload.zones[tx].premises[:3]] == [p.premise_id for p in direct.zones[tx].premises[:3]]
    # A second ingest is a new version; the earlier one stays usable.
    again = ingest.ingest("sim_upload", folder)
    assert again.version == "v2"
    assert sources.resolve_upload("upload:sim_upload@v1").name == "v1"
    assert sources.resolve_upload("upload:sim_upload").name == "v2"
    text = (config.config_dir() / "data_sources.yaml").read_text(encoding="utf-8")
    assert "# Active source per canonical table" in text   # comments kept


def test_missing_voltage_and_phase_use_fallbacks(isolated):
    scn = small_scenario()
    tables, _ = simulator.simulate(scn)
    tables["meter_reading"] = tables["meter_reading"].drop("voltage_v")
    tables["premise"] = tables["premise"].drop("phase", "feeder_branch", "distance_m")
    tables["transformer"] = tables["transformer"].drop("loss_params")
    folder = upload_folder(isolated, "bare")
    write_csvs(tables, folder)
    result = ingest.ingest("bare", folder, activate=True)
    assert result.ok
    assert set(result.report.missing_optional["premise"]) >= {"phase", "feeder_branch", "distance_m"}
    loaded = sources.load_active_tables()
    run = engine.run_tables(loaded, *sources.period(loaded), config.thresholds())
    zr = run.zones["TX-CEN-001"]
    assert zr.balance.flagged
    assert zr.voltage is not None and not zr.voltage.available
    assert any("AS-8" in note for note in zr.balance.notes)


# --------------------------------------------------------------------------- adapters

def test_london_adapter_profiles_and_canonical_tables(isolated):
    from voltguard.data.adapters import london

    raw = isolated / "data" / "raw" / "london"
    raw.mkdir(parents=True)
    rng = np.random.default_rng(1)
    lines = ["LCLid,tstp,energy(kWh/hh)"]
    start = datetime(2013, 1, 1)
    for h in range(5):
        for i in range(48 * 10):
            value = "Null" if (h == 0 and i == 5) else f"{abs(rng.normal(0.2, 0.1)):.3f}"
            lines.append(f"MAC{h:06d},{(start + timedelta(minutes=30 * i)).strftime('%Y-%m-%d %H:%M:%S')}.0000000,{value}")
    (raw / "block_0.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = london.convert()
    assert out["status"] == "converted" and out["households"] == 5
    assert london.convert()["status"] == "up to date"          # converted once, then Parquet only
    profiles = pl.read_parquet(config.data_root() / "processed" / "london_profiles.parquet")
    assert set(profiles.columns) == {"household", "date", "slot", "kwh"} and profiles["slot"].max() == 47
    for table in ("transformer", "premise", "meter", "meter_reading"):
        sources.set_source(table, "london")
    loaded = sources.load_active_tables()
    run = engine.run_tables(loaded, *sources.period(loaded), config.thresholds())
    zr = run.zones["TX-LDN-001"]
    assert not zr.balance.balance_available and all(p.confidence == "low" for p in zr.premises)


def test_sgcc_adapter_feeds_pattern_model(isolated):
    from voltguard.data.adapters import sgcc
    from voltguard.detection import pattern

    raw = isolated / "data" / "raw" / "sgcc"
    raw.mkdir(parents=True)
    rng = np.random.default_rng(2)
    days = [(date(2014, 1, 1) + timedelta(days=d)) for d in range(70)]
    header = "CONS_NO,FLAG," + ",".join(f"{d.year}/{d.month}/{d.day}" for d in days)
    rows = [header]
    for c in range(200):
        flag = int(c % 4 == 0)
        level = rng.uniform(5, 15)
        values = level * rng.normal(1, 0.1, len(days))
        if flag:  # zero-reading days, one of the SGCC theft patterns, visible in every window
            values[rng.random(len(days)) < 0.4] = 0.0
        cells = ["" if rng.random() < 0.05 else f"{v:.2f}" for v in values]
        rows.append(f"C{c:05d},{flag}," + ",".join(cells))
    (raw / "data set.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    out = sgcc.convert()
    assert out["customers"] == 200 and out["theft_share"] == pytest.approx(0.25)
    text = (config.config_dir() / "data_sources.yaml").read_text(encoding="utf-8").replace(
        "pattern_training: synthetic", "pattern_training: sgcc")
    (config.config_dir() / "data_sources.yaml").write_text(text, encoding="utf-8")
    config.load_yaml.cache_clear()
    _, metrics = pattern.train_default(save=False)
    assert metrics["source"] == "sgcc" and metrics["holdout_auc"] > 0.7


def test_datagovmy_adapter_month_factors(isolated):
    from voltguard.data.adapters import datagovmy

    raw = isolated / "data" / "raw" / "datagovmy"
    raw.mkdir(parents=True)
    rows = []
    for year in range(2019, 2025):
        for month in range(1, 13):
            for sector, base in (("total", 12000.0), ("local_domestic", 2500.0)):
                bump = 1.15 if month in (4, 5) else 1.0
                rows.append({"date": date(year, month, 1), "sector": sector, "consumption": base * bump})
    pl.DataFrame(rows).write_parquet(raw / "electricity_consumption.parquet")
    out = datagovmy.convert()
    assert out["sector"] == "domestic"
    factors = datagovmy.month_factors()
    assert factors[5] > 1.05 > factors[11]
    assert np.mean(factors[1:]) == pytest.approx(1.0, abs=0.02)
