"""London smart-meter adapter (prompt 3.2): household half-hourly kWh -> profiles and canonical tables.

Accepted raw files in DATA_ROOT/raw/london/ (CSV):
* Kaggle "Smart meters in London" half-hourly blocks: LCLid, tstp, energy(kWh/hh)
* London Datastore LCL file: LCLid, stdorToU, DateTime, KWH/hh (per half hour), Acorn, ...

Outputs:
* processed/london_profiles.parquet: household, date, slot, kwh - load shapes for the simulator
* processed/london_canonical/*.parquet: transformer, premise, meter, meter_reading, so
  `meter_reading: london` in data_sources.yaml runs the pipeline on real household load.
  The London data has no transformer links, voltage, phase or transformer meter: households
  are grouped into pseudo zones of `london.zone_size` (AS-1 stated, not real), every zone is
  "no balance available" (AS-2) and the voltage locator is skipped (AS-3). Timestamps are kept
  as local wall-clock time and labelled Asia/Kuala_Lumpur so the daily shape is preserved.
"""

from __future__ import annotations

import re
from datetime import date

import polars as pl

from voltguard import config
from voltguard.data import adapters
from voltguard.data.canonical import TIMEZONE

ID_COLUMNS = ("LCLid", "lclid", "household_id")
TIME_COLUMNS = ("tstp", "DateTime", "datetime", "timestamp")
KWH_COLUMNS = ("energy(kWh/hh)", "KWH/hh (per half hour) ", "KWH/hh (per half hour)", "kwh", "energy")


def _pick(columns: list[str], options: tuple[str, ...]) -> str | None:
    stripped = {c.strip(): c for c in columns}
    for option in options:
        if option in columns:
            return option
        if option.strip() in stripped:
            return stripped[option.strip()]
    return None


def _natural(path) -> list:
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(path))]


def half_hourly_files() -> list:
    """Every CSV under raw/london (subfolders too) that holds half-hourly readings: the full Kaggle extract
    also has daily, weather and household-information CSVs, which are skipped."""
    found = []
    for path in sorted(adapters.raw_dir("london").rglob("*.csv"), key=_natural):
        header = pl.read_csv(path, n_rows=0, encoding="utf8-lossy").columns   # some extract files are not UTF-8
        if _pick(header, ID_COLUMNS) and _pick(header, TIME_COLUMNS) and _pick(header, KWH_COLUMNS):
            found.append(path)
    return found


def read_raw(households: int) -> pl.DataFrame | None:
    files = half_hourly_files()
    if not files:
        return None
    frames, seen = [], set()
    for path in files:
        header = pl.read_csv(path, n_rows=0).columns
        hid, tcol, kcol = _pick(header, ID_COLUMNS), _pick(header, TIME_COLUMNS), _pick(header, KWH_COLUMNS)
        frame = pl.scan_csv(path, infer_schema=False).select(
            pl.col(hid).str.strip_chars().alias("household"),
            pl.col(tcol).str.slice(0, 19).str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False).alias("ts"),
            pl.col(kcol).str.strip_chars().cast(pl.Float64, strict=False).alias("kwh"),
        ).drop_nulls().collect()
        frames.append(frame)
        seen.update(frame["household"].unique().to_list())
        if households and len(seen) >= households:
            break           # the 112 Kaggle blocks hold ~5,500 homes: read only as many blocks as the subset needs
    raw = pl.concat(frames)
    if households:
        chosen = sorted(seen)[:households]
        raw = raw.filter(pl.col("household").is_in(chosen))
    return raw


def convert(force: bool = False) -> dict | None:
    cfg = config.data_sources().get("london", {}) or {}
    households = int(cfg.get("households", 300))
    files = half_hourly_files()
    profiles_path = adapters.processed("london_profiles.parquet")
    canon = config.data_root() / "processed" / "london_canonical"
    outputs = [profiles_path, canon / "meter_reading.parquet"]
    if not files:
        return None
    if not force and adapters.up_to_date(files, outputs):
        return {"status": "up to date", "path": str(profiles_path)}
    raw = read_raw(households)
    raw = raw.with_columns(
        pl.col("ts").dt.date().alias("date"),
        (pl.col("ts").dt.hour() * 2 + pl.col("ts").dt.minute() // 30).alias("slot"),
    ).unique(subset=["household", "ts"])
    raw.select("household", "date", "slot", "kwh").write_parquet(profiles_path)
    tables = canonical_tables(raw, int(cfg.get("zone_size", 60)), str(cfg.get("region", "CEN")))
    canon.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.write_parquet(canon / f"{name}.parquet")
    adapters.write_stamp(files, outputs)
    return {"status": "converted", "households": raw["household"].n_unique(), "rows": raw.height, "path": str(profiles_path)}


def canonical_tables(raw: pl.DataFrame, zone_size: int, region: str) -> dict[str, pl.DataFrame]:
    households = sorted(raw["household"].unique().to_list())
    zone_of = {h: i // zone_size + 1 for i, h in enumerate(households)}
    zones = sorted(set(zone_of.values()))
    transformer = pl.DataFrame({
        "transformer_id": [f"TX-LDN-{z:03d}" for z in zones], "region": [region] * len(zones),
        "district": ["London (public data)"] * len(zones), "capacity_kva": [500.0] * len(zones),
        "has_dtm": [False] * len(zones), "dtm_accuracy_class": [None] * len(zones), "loss_params": [None] * len(zones),
        "lat": [None] * len(zones), "lon": [None] * len(zones),
    }, schema_overrides={"dtm_accuracy_class": pl.Float64, "loss_params": pl.Utf8, "lat": pl.Float64, "lon": pl.Float64})
    pid = {h: f"P-LDN-{zone_of[h]:03d}-{i % zone_size + 1:03d}" for i, h in enumerate(households)}
    mid = {h: f"MTR-L{i + 1:06d}" for i, h in enumerate(households)}
    premise = pl.DataFrame({
        "premise_id": [pid[h] for h in households], "transformer_id": [f"TX-LDN-{zone_of[h]:03d}" for h in households],
        "feeder_branch": [None] * len(households), "phase": [None] * len(households), "distance_m": [None] * len(households),
        "street_seq": [i % zone_size + 1 for i in range(len(households))], "lat": [None] * len(households), "lon": [None] * len(households),
        "premise_type": ["terrace"] * len(households), "tariff": ["domestic"] * len(households),
    }, schema_overrides={"feeder_branch": pl.Utf8, "phase": pl.Utf8, "distance_m": pl.Float64, "lat": pl.Float64, "lon": pl.Float64})
    first = raw["ts"].min().date()
    meter = pl.DataFrame({"meter_id": [mid[h] for h in households], "premise_id": [pid[h] for h in households],
                          "meter_type": ["smart"] * len(households), "read_frequency": ["30min"] * len(households),
                          "installed_on": [min(first, date(2012, 1, 1))] * len(households)})
    readings = raw.select(
        pl.col("household").replace_strict(mid).alias("meter_id"),
        pl.col("ts").dt.replace_time_zone(TIMEZONE, ambiguous="earliest", non_existent="null").alias("ts"),
        pl.col("kwh").round(3), pl.lit(None, dtype=pl.Float64).alias("voltage_v"), pl.lit(0, dtype=pl.Int64).alias("quality_flag"),
    ).drop_nulls("ts")
    return {"transformer": transformer, "premise": premise, "meter": meter, "meter_reading": readings}
