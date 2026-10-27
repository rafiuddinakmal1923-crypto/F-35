"""Active data source per canonical table (prompt 3.4): `config/data_sources.yaml`.

Per-table values:
  simulated              the simulation run named in `simulation.run` (DATA_ROOT/simulated/<run>)
  london                 London smart-meter households converted by the London adapter
                         (meter, premise, transformer, meter_reading; no voltage, phase or
                         transformer meter, so the AS-2/AS-3/AS-7 fallbacks apply)
  upload:<name>          latest accepted version of an uploaded dataset
  upload:<name>@v<N>     a specific version
SGCC and data.gov.my cannot fill canonical tables (no meter-to-transformer links; national
monthly totals), so they are chosen by `pattern_training: sgcc` and `rescale: datagovmy`.

Switching a source is a config change plus `make.ps1 pipeline`; no code changes.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import polars as pl

from voltguard import config
from voltguard.data.canonical import TABLES, TIMEZONE


class SourceError(RuntimeError):
    pass


def active_sources() -> dict[str, str]:
    config.load_yaml.cache_clear()
    tables = config.data_sources().get("tables", {})
    return {name: str(tables.get(name, "simulated")) for name in TABLES}


def simulation_run() -> str:
    return str(config.data_sources().get("simulation", {}).get("run", "demo"))


def datasets_root() -> Path:
    return config.data_root() / "datasets"


def dataset_versions(name: str) -> list[dict]:
    folder = datasets_root() / name
    out = []
    for manifest in sorted(folder.glob("v*/manifest.json"), key=lambda p: int(p.parent.name[1:])):
        out.append(json.loads(manifest.read_text(encoding="utf-8")))
    return out


def resolve_upload(source: str) -> Path:
    match = re.fullmatch(r"upload:([A-Za-z0-9_.-]+)(?:@(v\d+))?", source)
    if not match:
        raise SourceError(f"Bad source '{source}': use upload:<dataset_name> or upload:<dataset_name>@v<N>")
    name, version = match.groups()
    accepted = [v for v in dataset_versions(name) if v.get("status") == "accepted"]
    if not accepted:
        raise SourceError(f"Dataset '{name}' has no accepted version; run make.ps1 ingest -Dataset {name}")
    chosen = next((v for v in accepted if v["version"] == version), None) if version else accepted[-1]
    if chosen is None:
        raise SourceError(f"Dataset '{name}' has no accepted version {version}")
    return datasets_root() / name / chosen["version"]


def table_path(name: str, source: str) -> Path:
    if source == "simulated":
        return config.data_root() / "simulated" / simulation_run() / "tables" / f"{name}.parquet"
    if source == "london":
        return config.data_root() / "processed" / "london_canonical" / f"{name}.parquet"
    if source.startswith("upload:"):
        return resolve_upload(source) / f"{name}.parquet"
    raise SourceError(f"Unknown source '{source}' for table {name}")


def load_table(name: str, source: str) -> pl.DataFrame | None:
    path = table_path(name, source)
    if not path.exists():
        optional = name in ("transformer_reading", "meter_monthly_reading", "account_event", "customer_pii",
                            "inspection_outcome", "district_weather", "duty_roster")
        if optional:
            return None
        raise SourceError(f"Table {name} not found for source '{source}' ({path})")
    return pl.read_parquet(path)


def load_active_tables(sources: dict[str, str] | None = None, skip: tuple[str, ...] = ()) -> dict[str, pl.DataFrame]:
    """Every canonical table from its active source (missing optional tables are left out).

    `skip` leaves big tables (the interval readings) to be streamed in batches by the pipeline.
    """
    sources = sources or active_sources()
    tables = {}
    for name in TABLES:
        if name in skip:
            continue
        source = sources.get(name, "simulated")
        frame = load_table(name, source)
        if frame is not None:
            tables[name] = frame
    # The weather series follows the simulation when the readings are simulated.
    if "district_weather" not in tables and sources.get("meter_reading") == "simulated":
        frame = load_table("district_weather", "simulated")
        if frame is not None:
            tables["district_weather"] = frame
    return tables


def period(tables: dict[str, pl.DataFrame]) -> tuple[date, int]:
    """First full day and number of days covered by the interval readings."""
    ts = tables["meter_reading"]["ts"].dt.convert_time_zone(TIMEZONE)
    first, last = ts.min().date(), ts.max().date()
    return first, (last - first).days + 1


def scan_readings(source: str) -> pl.LazyFrame:
    """The interval readings as a lazy scan: the pipeline reads them in meter batches, never all at once."""
    path = table_path("meter_reading", source)
    if not path.exists():
        raise SourceError(f"Table meter_reading not found for source '{source}' ({path})")
    return pl.scan_parquet(path)


def scan_period(scan: pl.LazyFrame) -> tuple[date, int]:
    bounds = scan.select(pl.col("ts").min().alias("lo"), pl.col("ts").max().alias("hi")).collect()
    first = bounds["lo"].dt.convert_time_zone(TIMEZONE)[0].date()
    last = bounds["hi"].dt.convert_time_zone(TIMEZONE)[0].date()
    return first, (last - first).days + 1


def set_source(table: str, source: str) -> None:
    """Change one table's source in data_sources.yaml, keeping the file's comments."""
    if table not in TABLES:
        raise SourceError(f"Unknown table {table}")
    path = config.config_dir() / "data_sources.yaml"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^(  {table}:\s*)(\S+)(.*)$", re.MULTILINE)
    if pattern.search(text):
        text = pattern.sub(lambda m: f"{m.group(1)}{source}{m.group(3)}", text, count=1)
    else:
        text = text.replace("tables:\n", f"tables:\n  {table}: {source}\n", 1)
    path.write_text(text, encoding="utf-8")
    config.load_yaml.cache_clear()
