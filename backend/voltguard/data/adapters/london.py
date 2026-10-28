"""London smart-meter adapter (prompt 3.2): household half-hourly kWh -> profiles and canonical tables.

Accepted raw files anywhere under DATA_ROOT/raw/london/ (CSV), in this order of preference:
* Kaggle "Smart meters in London" hhblock files (hhblock_dataset/block_N.csv): LCLid, day, hh_0 ... hh_47
  (the most compact form of the half-hourly data)
* Kaggle half-hourly blocks (halfhourly_dataset/block_N.csv): LCLid, tstp, energy(kWh/hh)
* London Datastore LCL file: LCLid, stdorToU, DateTime, KWH/hh (per half hour), Acorn, ...
Other files in the folder (daily totals, weather, household information, bank holidays) are not
half-hourly and are skipped. Blocks are read in order only until `london.households` households are
covered, so the 9 GB Kaggle download is never read in full for the default subset.

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
from pathlib import Path

import polars as pl

from voltguard import config
from voltguard.data import adapters
from voltguard.data.canonical import TIMEZONE

ID_COLUMNS = ("LCLid", "lclid", "household_id")
TIME_COLUMNS = ("tstp", "DateTime", "datetime", "timestamp")
KWH_COLUMNS = ("energy(kWh/hh)", "KWH/hh (per half hour) ", "KWH/hh (per half hour)", "kwh", "energy")
HH_COLUMNS = [f"hh_{i}" for i in range(48)]


def _pick(columns: list[str], options: tuple[str, ...]) -> str | None:
    stripped = {c.strip(): c for c in columns}
    for option in options:
        if option in columns:
            return option
        if option.strip() in stripped:
            return stripped[option.strip()]
    return None


def _natural(path: Path) -> tuple:
    return tuple(int(t) if t.isdigit() else t for t in re.split(r"(\d+)", path.as_posix()))


def _kind(header: list[str]) -> str | None:
    """'wide' (hhblock: day + hh_0..hh_47), 'long' (one row per half hour) or None (not half-hourly)."""
    if _pick(header, ID_COLUMNS) and "day" in header and all(c in header for c in HH_COLUMNS):
        return "wide"
    if _pick(header, ID_COLUMNS) and _pick(header, TIME_COLUMNS) and _pick(header, KWH_COLUMNS):
        return "long"
    return None


def source_files() -> tuple[str | None, list[Path]]:
    """The half-hourly files to read: every file of the preferred format, in natural order (block_2 before block_10)."""
    found: dict[str, list[Path]] = {"wide": [], "long": []}
    for path in sorted(adapters.raw_dir("london").rglob("*.csv"), key=_natural):
        # Side files (ACORN details, weather) can be in another encoding; only the header decides.
        kind = _kind(pl.read_csv(path, n_rows=0, encoding="utf8-lossy").columns)
        if kind:
            found[kind].append(path)
    for kind in ("wide", "long"):
        if found[kind]:
            return kind, found[kind]
    return None, []


def _scan(path: Path, kind: str) -> pl.LazyFrame:
    header = pl.read_csv(path, n_rows=0).columns
    hid = _pick(header, ID_COLUMNS)
    if kind == "wide":
        return (pl.scan_csv(path, infer_schema=False)
                .select(pl.col(hid).str.strip_chars().alias("household"), pl.col("day").str.slice(0, 10).str.to_date(strict=False).alias("day"),
                        *[pl.col(c) for c in HH_COLUMNS])
                .unpivot(index=["household", "day"], on=HH_COLUMNS, variable_name="hh", value_name="kwh_text")
                .select("household",
                        (pl.col("day").cast(pl.Datetime("us"))
                         + pl.duration(minutes=pl.col("hh").str.slice(3).cast(pl.Int64) * 30)).alias("ts"),
                        pl.col("kwh_text").str.strip_chars().cast(pl.Float64, strict=False).alias("kwh")))
    tcol, kcol = _pick(header, TIME_COLUMNS), _pick(header, KWH_COLUMNS)
    return pl.scan_csv(path, infer_schema=False).select(
        pl.col(hid).str.strip_chars().alias("household"),
        pl.col(tcol).str.slice(0, 19).str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False).alias("ts"),
        pl.col(kcol).str.strip_chars().cast(pl.Float64, strict=False).alias("kwh"),
    )


def read_raw(households: int, files: list[Path] | None = None, kind: str | None = None) -> tuple[pl.DataFrame | None, list[Path]]:
    """Half-hourly rows for the first `households` households (0 = all), and the files actually read."""
    if files is None:
        kind, files = source_files()
    if not files:
        return None, []
    frames, used, chosen = [], [], set()
    for path in files:
        frame = _scan(path, kind).drop_nulls().collect()
        if households:
            # Households in file order, sorted by ID, until the subset is full (Kaggle blocks do not overlap).
            new = sorted(set(frame["household"].unique().to_list()) - chosen)[: households - len(chosen)]
            chosen |= set(new)
            frame = frame.filter(pl.col("household").is_in(sorted(chosen)))
        frames.append(frame)
        used.append(path)
        if households and len(chosen) >= households:
            break
    return pl.concat(frames), used


def _stamp_ok(stamp_path: Path, files: list[Path], households: int) -> bool:
    """The files read last time are unchanged and the subset size is the same."""
    import json

    if not stamp_path.exists():
        return False
    saved = json.loads(stamp_path.read_text(encoding="utf-8"))
    if saved.get("households") != households:
        return False
    current = {p.as_posix(): [p.stat().st_size, int(p.stat().st_mtime)] for p in files}
    return bool(saved.get("files")) and all(current.get(name) == value for name, value in saved["files"].items())


def convert(force: bool = False) -> dict | None:
    cfg = config.data_sources().get("london", {}) or {}
    households = int(cfg.get("households", 300))
    kind, files = source_files()
    profiles_path = adapters.processed("london_profiles.parquet")
    canon = config.data_root() / "processed" / "london_canonical"
    outputs = [profiles_path, canon / "meter_reading.parquet"]
    if not files:
        return None
    stamp_path = profiles_path.with_suffix(".stamp.json")
    if not force and all(p.exists() for p in outputs) and _stamp_ok(stamp_path, files, households):
        return {"status": "up to date", "path": str(profiles_path)}
    raw, used = read_raw(households, files, kind)
    raw = raw.with_columns(
        pl.col("ts").dt.date().alias("date"),
        (pl.col("ts").dt.hour() * 2 + pl.col("ts").dt.minute() // 30).alias("slot"),
    ).unique(subset=["household", "ts"])
    raw.select("household", "date", "slot", "kwh").write_parquet(profiles_path)
    tables = canonical_tables(raw, int(cfg.get("zone_size", 60)), str(cfg.get("region", "CEN")))
    canon.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.write_parquet(canon / f"{name}.parquet")
    import json

    stamp_path.write_text(json.dumps({"households": households, "format": kind,
                                      "files": {p.as_posix(): [p.stat().st_size, int(p.stat().st_mtime)] for p in used}}),
                          encoding="utf-8")
    return {"status": "converted", "format": kind, "files_read": len(used), "households": raw["household"].n_unique(),
            "rows": raw.height, "path": str(profiles_path)}


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
