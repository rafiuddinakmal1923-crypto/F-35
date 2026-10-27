"""Nightly pipeline (SDD 6.1 steps 1-4; POST /jobs/run-detection, `make.ps1 pipeline`).

1. Ingest: load every canonical table from its active source (config/data_sources.yaml),
   validate it and write it into the database.
2-4. Read the canonical tables back from the database, run the detection engine (balance,
   locator, features, scoring) and write zone results, scores and reasons.
Creates no cases: the case job is separate (POST /jobs/create-cases).
"""

from __future__ import annotations

import hashlib
import io
import json
import math
from datetime import date, datetime
from typing import Callable

import numpy as np
import polars as pl
import psycopg
from psycopg.types.json import Jsonb

from voltguard import config, db
from voltguard.data import simulator, sources
from voltguard.data.canonical import TABLES, TIMEZONE
from voltguard.data.validation import ValidationReport, validate
from voltguard.detection import engine
from voltguard.service import settings

Progress = Callable[[str], None]


class PipelineError(RuntimeError):
    pass


# --------------------------------------------------------------------------- COPY helpers

def _csv(frame: pl.DataFrame) -> bytes:
    out = frame
    for col, dtype in frame.schema.items():
        if isinstance(dtype, pl.Datetime):
            out = out.with_columns(pl.col(col).dt.convert_time_zone("UTC").dt.strftime("%Y-%m-%dT%H:%M:%S%.6fZ"))
        elif isinstance(dtype, pl.List):
            out = out.with_columns(pl.col(col).map_elements(lambda v: "{" + ",".join(f'"{x}"' for x in v) + "}", return_dtype=pl.Utf8))
    return out.write_csv(include_header=False, null_value="").encode("utf-8")


def copy_in(conn: psycopg.Connection, table: str, frame: pl.DataFrame) -> int:
    if not frame.height:
        return 0
    cols = ", ".join(frame.columns)
    with conn.cursor().copy(f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT csv, NULL '')") as cp:
        data = _csv(frame)
        for start in range(0, len(data), 8 << 20):
            cp.write(data[start:start + (8 << 20)])
    return frame.height


def upsert(conn: psycopg.Connection, table: str, frame: pl.DataFrame, key: list[str]) -> int:
    if not frame.height:
        return 0
    tmp = f"tmp_{table}"
    conn.execute(f"CREATE TEMP TABLE {tmp} (LIKE {table} INCLUDING DEFAULTS) ON COMMIT DROP")
    copy_in(conn, tmp, frame)
    cols = ", ".join(frame.columns)
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in frame.columns if c not in key) or f"{key[0]} = EXCLUDED.{key[0]}"
    conn.execute(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM {tmp} ON CONFLICT ({', '.join(key)}) DO UPDATE SET {updates}")
    conn.execute(f"DROP TABLE {tmp}")
    return frame.height


def copy_out(conn: psycopg.Connection, query: str, schema: dict) -> pl.DataFrame:
    buf = io.BytesIO()
    with conn.cursor().copy(f"COPY ({query}) TO STDOUT WITH (FORMAT csv, HEADER true)") as cp:
        for block in cp:
            buf.write(block)
    buf.seek(0)
    if not buf.getbuffer().nbytes:
        return pl.DataFrame(schema=schema)
    return pl.read_csv(buf, schema_overrides=schema, infer_schema_length=0 if not schema else 100)


# --------------------------------------------------------------------------- 1. ingest into the database

def load_into_db(conn: psycopg.Connection, tables: dict[str, pl.DataFrame], progress: Progress = print) -> dict[str, int]:
    """Write canonical tables into the database (owner connection). Readings are replaced."""
    from voltguard.agents import scrubber

    counts: dict[str, int] = {}
    demo = config.demo_config()
    teams = pl.DataFrame(demo.get("teams", []) or [{"team_id": "T-0", "name": "Team", "region": "CEN"}]).select("team_id", "name", "region")
    upsert(conn, "team", teams, ["team_id"])

    tx = tables["transformer"].with_columns(pl.col("loss_params").cast(pl.Utf8))
    counts["transformer"] = upsert(conn, "transformer", tx, ["transformer_id"])
    region_of_tx = tx.select("transformer_id", "region")
    premise = tables["premise"].join(region_of_tx, on="transformer_id", how="left")
    counts["premise"] = upsert(conn, "premise", premise.select(
        "premise_id", "transformer_id", "region", "feeder_branch", "phase", "distance_m", "street_seq", "lat", "lon", "premise_type", "tariff"),
        ["premise_id"])
    meter = tables["meter"].join(premise.select("premise_id", "region"), on="premise_id", how="left")
    counts["meter"] = upsert(conn, "meter", meter.select("meter_id", "premise_id", "region", "meter_type", "read_frequency", "installed_on"),
                             ["meter_id"])

    conn.execute("TRUNCATE meter_reading, meter_monthly_reading, transformer_reading, account_event, district_weather, duty_roster")
    progress(f"Loading {tables['meter_reading'].height:,} meter readings...")
    counts["meter_reading"] = copy_in(conn, "meter_reading", tables["meter_reading"].with_columns(
        pl.col("quality_flag").fill_null(0)).select("meter_id", "ts", "kwh", "voltage_v", "quality_flag"))
    for name in ("meter_monthly_reading", "transformer_reading", "account_event", "district_weather"):
        if name in tables:
            counts[name] = copy_in(conn, name, tables[name].select(TABLES[name].names))
    if "duty_roster" in tables:
        roster = tables["duty_roster"].join(teams.select("team_id", "region"), on="team_id", how="left").with_columns(
            pl.col("region").fill_null("*"))
        counts["duty_roster"] = copy_in(conn, "duty_roster", roster.select(
            "team_id", "shift_date", "region", "base_lat", "base_lon", "on_duty"))
    if "customer_pii" in tables:
        counts["customer_pii"] = upsert(conn, "customer_pii", tables["customer_pii"].select(TABLES["customer_pii"].names), ["premise_id"])
    if "inspection_outcome" in tables and tables["inspection_outcome"].height:
        # Historic labels: notes are scrubbed before they are stored; the raw notes are not kept.
        hist = tables["inspection_outcome"]
        redacted = [scrubber.scrub(n).text if n else None for n in hist["notes"].to_list()]
        hist = hist.with_columns(pl.Series("notes_redacted", redacted, dtype=pl.Utf8)).select(
            "case_id", "premise_id", "outcome", "reason_tag", "notes_redacted", "recorded_at", "origin")
        counts["historic_outcome"] = upsert(conn, "historic_outcome", hist, ["case_id"])
    return counts


# --------------------------------------------------------------------------- 2-4. detection from the database

def read_canonical(conn: psycopg.Connection, transformer_ids: list[str]) -> dict[str, pl.DataFrame]:
    """Canonical tables for the given zones, read back from the data store (the engine never reads files)."""
    ids = "ARRAY[" + ",".join("'" + t.replace("'", "''") + "'" for t in transformer_ids) + "]::text[]"
    epoch = "(extract(epoch FROM ts) * 1000000)::bigint AS ts_us"
    tx = copy_out(conn, f"SELECT transformer_id, region, district, capacity_kva, has_dtm::text AS has_dtm, dtm_accuracy_class, loss_params::text AS loss_params, "
                        f"lat, lon FROM transformer WHERE transformer_id = ANY({ids})",
                  {"capacity_kva": pl.Float64, "dtm_accuracy_class": pl.Float64, "lat": pl.Float64, "lon": pl.Float64, "has_dtm": pl.Boolean})
    premise = copy_out(conn, f"SELECT premise_id, transformer_id, feeder_branch, phase, distance_m, street_seq, lat, lon, premise_type, tariff "
                             f"FROM premise WHERE transformer_id = ANY({ids})",
                       {"distance_m": pl.Float64, "street_seq": pl.Int64, "lat": pl.Float64, "lon": pl.Float64,
                        "feeder_branch": pl.Utf8, "phase": pl.Utf8})
    pids = f"(SELECT premise_id FROM premise WHERE transformer_id = ANY({ids}))"
    meter = copy_out(conn, f"SELECT meter_id, premise_id, meter_type, read_frequency, installed_on FROM meter WHERE premise_id IN {pids}",
                     {"installed_on": pl.Date})
    mids = f"(SELECT meter_id FROM meter WHERE premise_id IN {pids})"

    def with_ts(frame: pl.DataFrame) -> pl.DataFrame:
        return frame.with_columns(pl.from_epoch(pl.col("ts_us"), time_unit="us").dt.replace_time_zone("UTC")
                                  .dt.convert_time_zone(TIMEZONE).alias("ts")).drop("ts_us")

    readings = with_ts(copy_out(conn, f"SELECT meter_id, {epoch}, kwh, voltage_v, quality_flag FROM meter_reading WHERE meter_id IN {mids}",
                                {"ts_us": pl.Int64, "kwh": pl.Float64, "voltage_v": pl.Float64, "quality_flag": pl.Int64}))
    monthly = copy_out(conn, f"SELECT meter_id, month, kwh FROM meter_monthly_reading WHERE meter_id IN {mids}",
                       {"month": pl.Date, "kwh": pl.Float64})
    tx_read = with_ts(copy_out(conn, f"SELECT transformer_id, {epoch}, kwh_supplied, voltage_v FROM transformer_reading "
                                     f"WHERE transformer_id = ANY({ids})",
                               {"ts_us": pl.Int64, "kwh_supplied": pl.Float64, "voltage_v": pl.Float64}))
    events = copy_out(conn, f"SELECT event_id, premise_id, event_type, event_date FROM account_event WHERE premise_id IN {pids}",
                      {"event_date": pl.Date})
    weather = copy_out(conn, "SELECT district, date, temperature_c, sunshine_hours FROM district_weather",
                       {"date": pl.Date, "temperature_c": pl.Float64, "sunshine_hours": pl.Float64})
    return {"transformer": tx, "premise": premise, "meter": meter, "meter_reading": readings, "meter_monthly_reading": monthly,
            "transformer_reading": tx_read, "account_event": events, "district_weather": weather}


def _num(x) -> float | None:
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) or math.isinf(x) else round(x, 4)


def _jsonable(value):
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (np.floating, float)):
        return _num(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def write_results(conn: psycopg.Connection, run: engine.DetectionRun, run_id: int) -> dict:
    run_date = run.run_date
    tx_ids = list(run.zones)
    region = {tx: zr.zone.region for tx, zr in run.zones.items()}
    first = min(zr.balance.dates[0] for zr in run.zones.values())
    conn.execute("DELETE FROM zone_daily_balance WHERE transformer_id = ANY(%s) AND date >= %s", (tx_ids, first))
    for table in ("zone_run", "premise_feature", "premise_score", "score_reason", "data_quality_flag"):
        key = "transformer_id" if table in ("zone_run", "premise_feature", "premise_score", "data_quality_flag") else None
        if key:
            conn.execute(f"DELETE FROM {table} WHERE run_date = %s AND {key} = ANY(%s)", (run_date, tx_ids))
    conn.execute("DELETE FROM score_reason WHERE run_date = %s AND premise_id IN (SELECT premise_id FROM premise WHERE transformer_id = ANY(%s))",
                 (run_date, tx_ids))

    balance_rows, zone_rows, feat_rows, score_rows, reason_rows, flag_rows = [], [], [], [], [], []
    for tx, zr in run.zones.items():
        b = zr.balance
        for d, day in enumerate(b.dates):
            balance_rows.append({
                "transformer_id": tx, "date": day, "region": region[tx], "run_id": run_id,
                "supplied_kwh": _num(b.supplied_kwh[d]), "metered_kwh": _num(b.metered_kwh[d]), "estimated_kwh": _num(b.estimated_kwh[d]),
                "uncertainty_kwh": _num(b.uncertainty_kwh[d]), "tech_loss_kwh": _num(b.tech_loss_kwh[d]), "gap_kwh": _num(b.gap_kwh[d]),
                "gap_pct": _num(b.gap_pct[d]), "over_threshold": bool(b.over_threshold[d]) if b.balance_available else None,
                "balance_available": b.balance_available, "flagged": b.flagged, "priority": b.priority, "gap_start": b.gap_start,
            })
        recent = slice(-7, None)
        v = zr.voltage
        voltage = None
        if v is not None:
            voltage = {"available": v.available, "method": v.method, "confidence": v.confidence, "notes": v.notes,
                       "groups": _jsonable(v.groups),
                       "premises": {pid: {"signal_v": _num(v.signal_v[i]), "residual_v": _num(v.residual_v[i]), "change_v": _num(v.change_v[i]),
                                          "tap_distance_m": _num(v.tap_distance_m[i])} for i, pid in enumerate(zr.zone.premise_ids)}}
        zone_rows.append({
            "transformer_id": tx, "run_date": run_date, "run_id": run_id, "region": region[tx], "district": zr.zone.district,
            "balance_available": b.balance_available, "flagged": b.flagged, "priority": b.priority, "gap_start": b.gap_start,
            "gap_since_start": b.gap_since_start,
            "gap_kwh_recent": _num(np.nanmean(b.gap_kwh[recent])) if b.balance_available else None,
            "gap_pct_recent": _num(np.nanmean(b.gap_pct[recent])) if b.balance_available else None,
            "uncertainty_kwh_recent": _num(np.nanmean(b.uncertainty_kwh[recent])) if b.balance_available else None,
            "flatness_cv": _num(b.flatness_cv), "hourly_gap_kwh": json.dumps(_jsonable(b.hourly_gap_kwh)) if b.hourly_gap_kwh is not None else None,
            "loss_method": b.loss_method, "voltage": json.dumps(_jsonable(voltage)) if voltage else None,
            "notes": json.dumps(b.notes + (v.notes if v is not None else [])), "n_premises": zr.zone.n, "scored": zr.scored,
        })
        for p in zr.premises:
            feat_rows.append({"premise_id": p.premise_id, "run_date": run_date, "transformer_id": tx, "region": region[tx],
                              "features": json.dumps(_jsonable(p.features)), "details": json.dumps(_jsonable(p.details)), "tags": p.tags})
            score_rows.append({"premise_id": p.premise_id, "run_date": run_date, "transformer_id": tx, "region": region[tx], "run_id": run_id,
                               "model_version": run.model_version, "score": p.score, "rank": p.rank, "confidence": p.confidence,
                               "tags": p.tags, "smart": p.smart})
            for k, r in enumerate(p.reasons, start=1):
                reason_rows.append({"premise_id": p.premise_id, "run_date": run_date, "rank": k, "region": region[tx],
                                    "feature": r["feature"], "contribution": r["contribution"], "reason_text": r["reason_text"]})
        for f in zr.quality_flags:
            flag_rows.append({"meter_id": f["meter_id"], "date": f["date"], "run_date": run_date, "premise_id": f["premise_id"],
                              "transformer_id": tx, "region": region[tx], "completeness": f["completeness"]})

    copy_in(conn, "zone_daily_balance", pl.DataFrame(balance_rows, infer_schema_length=None))
    upsert(conn, "zone_run", pl.DataFrame(zone_rows, infer_schema_length=None), ["transformer_id", "run_date"])
    if feat_rows:
        copy_in(conn, "premise_feature", pl.DataFrame(feat_rows, schema_overrides={"tags": pl.List(pl.Utf8)}, infer_schema_length=None))
        copy_in(conn, "premise_score", pl.DataFrame(score_rows, schema_overrides={"tags": pl.List(pl.Utf8)}, infer_schema_length=None))
        copy_in(conn, "score_reason", pl.DataFrame(reason_rows, infer_schema_length=None))
    if flag_rows:
        copy_in(conn, "data_quality_flag", pl.DataFrame(flag_rows, infer_schema_length=None).unique(subset=["meter_id", "date", "run_date"]))
    flagged = [tx for tx, zr in run.zones.items() if zr.balance.flagged]
    return {"run_date": run_date.isoformat(), "zones": len(run.zones), "flagged_zones": flagged,
            "no_balance_zones": [tx for tx, zr in run.zones.items() if not zr.balance.balance_available],
            "premises_scored": len(score_rows), "data_quality_flags": len(flag_rows), "model_version": run.model_version}


def snapshot_id(sources_map: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(sources_map, sort_keys=True).encode()).hexdigest()[:12]


def ensure_simulated(progress: Progress = print) -> None:
    """When a table's source is `simulated` and the run is missing, simulate it (offline demo needs no downloads)."""
    if "simulated" not in sources.active_sources().values():
        return
    run = sources.simulation_run()
    folder = config.data_root() / "simulated" / run / "tables"
    if folder.exists():
        return
    builders = {"demo": simulator.demo_scenario, "tuning": simulator.tuning_scenario, "heldout": simulator.heldout_scenario}
    if run not in builders:
        raise PipelineError(f"Simulation run '{run}' not found under {folder.parent}")
    progress(f"Simulating '{run}' (first run)...")
    scn = builders[run]()
    tables, truth = simulator.simulate(scn)
    simulator.write_run(scn, tables, truth)


def run_detection(actor: str = "pipeline", progress: Progress = print) -> dict:
    """Steps 1-4 of the nightly pipeline. Creates no cases."""
    ensure_simulated(progress)
    active = sources.active_sources()
    progress("Loading active sources...")
    tables = sources.load_active_tables(active)
    report = ValidationReport("pipeline", datetime.now().strftime("%Y%m%d-%H%M%S"))
    tables = validate(tables, report)
    if not report.ok:
        errors = [f"{i.table}.{i.column or '-'} {i.check}: {i.message}" for i in report.issues if i.level == "error"]
        raise PipelineError("Active sources failed validation: " + "; ".join(errors[:5]))
    tx_ids = tables["transformer"]["transformer_id"].to_list()
    start, days = sources.period(tables)
    with db.admin_connection() as conn:
        with conn.transaction():
            counts = load_into_db(conn, tables, progress)
            run_id = conn.execute("INSERT INTO detection_run (run_date, data_sources, data_snapshot) VALUES (%s, %s, %s) RETURNING run_id",
                                  (start, Jsonb(active), snapshot_id(active))).fetchone()["run_id"]
        progress("Reading canonical tables from the data store...")
        canonical = read_canonical(conn, tx_ids)
        cfg = settings.thresholds(conn)
        progress("Running detection (zone balance, voltage locator, features, scoring)...")
        run = engine.run_tables(canonical, start, days, cfg)
        with conn.transaction():
            summary = write_results(conn, run, run_id)
            summary.update({"run_id": run_id, "loaded": counts, "warnings": sum(i.level == "warning" for i in report.issues)})
            conn.execute("UPDATE detection_run SET run_date = %s, finished_at = now(), status = 'done', model_version = %s, summary = %s "
                         "WHERE run_id = %s", (run.run_date, run.model_version, Jsonb(summary), run_id))
            db.audit(conn, actor, "job.run_detection", f"run:{run_id}", {"flagged_zones": summary["flagged_zones"]})
    try:
        from voltguard.service import monitoring

        monitoring.after_detection(run, summary)
    except ImportError:
        pass
    progress(f"Done: {len(summary['flagged_zones'])} flagged zone(s), {summary['premises_scored']} premises scored.")
    return summary
