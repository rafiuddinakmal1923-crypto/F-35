"""Turn canonical tables into per-zone arrays for the detection engine.

The engine never reads raw files or the database directly: the pipeline loads the
canonical tables (from the database, or from a simulation run in tests) and this module
reshapes them into half-hourly matrices per transformer zone.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import numpy as np
import polars as pl

from voltguard.data.canonical import TIMEZONE
from voltguard.network import LossParams

SLOTS = 48


@dataclass
class ZoneInput:
    transformer_id: str
    region: str
    district: str
    has_dtm: bool
    accuracy_class: float | None
    loss_params: LossParams | None          # None when parameters are unavailable (AS-8)
    start: date
    days: int
    premise_ids: list[str]
    premises: pl.DataFrame                  # canonical premise rows, in premise_ids order
    smart: np.ndarray                       # (n,) premise has a smart (interval) meter
    meter_ids: list[str]
    kwh: np.ndarray                         # (n, T) interval kWh, NaN when missing or not a smart meter
    voltage: np.ndarray                     # (n, T) volts, NaN when missing
    monthly: dict[int, dict[date, float]]   # premise index -> month -> kWh (conventional meters)
    supply_kwh: np.ndarray | None           # (T,) transformer meter, None without a DTM (AS-2)
    tx_voltage: np.ndarray | None           # (T,)
    events: list[tuple[int, str, date]] = field(default_factory=list)
    sunshine: np.ndarray | None = None      # (days,) district sunshine hours, when loaded (FR-DI-07)

    @property
    def n(self) -> int:
        return len(self.premise_ids)

    @property
    def T(self) -> int:
        return self.days * SLOTS

    @property
    def has_topology(self) -> bool:
        """Branch, phase and distance recorded for every premise (AS-7)."""
        cols = self.premises.select(["feeder_branch", "phase", "distance_m"])
        return cols.null_count().sum_horizontal().item() == 0

    @property
    def has_voltage(self) -> bool:
        return bool(np.isfinite(self.voltage).any())

    def day_dates(self) -> list[date]:
        return [self.start + timedelta(days=d) for d in range(self.days)]

    def phase_index(self) -> np.ndarray:
        mapping = {"A": 0, "B": 1, "C": 2}
        return np.array([mapping.get(p, -1) for p in self.premises["phase"].fill_null("").to_list()])


def build_zone_inputs(tables: dict[str, pl.DataFrame], start: date, days: int) -> dict[str, ZoneInput]:
    """One ZoneInput per transformer, covering `days` days from `start`."""
    transformers = tables["transformer"]
    premises_all = tables["premise"].sort("premise_id")
    meters = tables["meter"]
    readings = tables.get("meter_reading", pl.DataFrame())
    monthly_all = tables.get("meter_monthly_reading", pl.DataFrame())
    tx_readings = tables.get("transformer_reading", pl.DataFrame())
    events = tables.get("account_event", pl.DataFrame())
    weather = tables.get("district_weather", pl.DataFrame())
    T = days * SLOTS
    origin_us = np.datetime64(datetime(start.year, start.month, start.day), "us").astype(np.int64)

    def slots(ts: pl.Series) -> np.ndarray:
        local = ts.dt.convert_time_zone(TIMEZONE).dt.replace_time_zone(None).cast(pl.Int64).to_numpy()
        return (local - origin_us) // (30 * 60 * 1_000_000)

    zones: dict[str, ZoneInput] = {}
    for tx in transformers.iter_rows(named=True):
        tx_id = tx["transformer_id"]
        prem = premises_all.filter(pl.col("transformer_id") == tx_id)
        ids = prem["premise_id"].to_list()
        index = {pid: i for i, pid in enumerate(ids)}
        zone_meters = meters.filter(pl.col("premise_id").is_in(ids))
        meter_to_prem = {m: index[p] for m, p in zip(zone_meters["meter_id"], zone_meters["premise_id"])}
        smart = np.zeros(len(ids), dtype=bool)
        meter_ids = [""] * len(ids)
        for row in zone_meters.iter_rows(named=True):
            i = index[row["premise_id"]]
            meter_ids[i] = row["meter_id"]
            smart[i] = row["meter_type"] == "smart"

        kwh = np.full((len(ids), T), np.nan)
        volts = np.full((len(ids), T), np.nan)
        if readings.height:
            zr = readings.filter(pl.col("meter_id").is_in(list(meter_to_prem)))
            if zr.height:
                rows = np.array([meter_to_prem[m] for m in zr["meter_id"].to_list()])
                cols = slots(zr["ts"])
                ok = (cols >= 0) & (cols < T)
                kwh[rows[ok], cols[ok]] = zr["kwh"].to_numpy()[ok]
                if "voltage_v" in zr.columns:
                    v = zr["voltage_v"].cast(pl.Float64).to_numpy()
                    volts[rows[ok], cols[ok]] = v[ok]

        monthly: dict[int, dict[date, float]] = {}
        if monthly_all.height:
            for row in monthly_all.filter(pl.col("meter_id").is_in(list(meter_to_prem))).iter_rows(named=True):
                monthly.setdefault(meter_to_prem[row["meter_id"]], {})[row["month"]] = float(row["kwh"])

        supply = tx_v = None
        if tx.get("has_dtm") and tx_readings.height:
            zt = tx_readings.filter(pl.col("transformer_id") == tx_id)
            if zt.height:
                supply = np.full(T, np.nan)
                tx_v = np.full(T, np.nan)
                cols = slots(zt["ts"])
                ok = (cols >= 0) & (cols < T)
                supply[cols[ok]] = zt["kwh_supplied"].to_numpy()[ok]
                if "voltage_v" in zt.columns:
                    tx_v[cols[ok]] = zt["voltage_v"].cast(pl.Float64).to_numpy()[ok]
                if not np.isfinite(tx_v).any():
                    tx_v = None

        zone_events = []
        if events.height:
            for row in events.filter(pl.col("premise_id").is_in(ids)).iter_rows(named=True):
                zone_events.append((index[row["premise_id"]], row["event_type"], row["event_date"]))

        sunshine = None
        if weather.height and "sunshine_hours" in weather.columns:
            zw = weather.filter(pl.col("district") == (tx.get("district") or ""))
            if zw.height:
                sunshine = np.full(days, np.nan)
                for row in zw.iter_rows(named=True):
                    d = (row["date"] - start).days
                    if 0 <= d < days and row["sunshine_hours"] is not None:
                        sunshine[d] = float(row["sunshine_hours"])
                if not np.isfinite(sunshine).any():
                    sunshine = None

        raw_params = tx.get("loss_params")
        params = None
        if raw_params:
            params = LossParams.from_dict(json.loads(raw_params) if isinstance(raw_params, str) else raw_params)

        zones[tx_id] = ZoneInput(
            transformer_id=tx_id, region=tx["region"], district=tx.get("district") or "",
            has_dtm=bool(tx.get("has_dtm")) and supply is not None,
            accuracy_class=tx.get("dtm_accuracy_class"), loss_params=params,
            start=start, days=days, premise_ids=ids, premises=prem, smart=smart, meter_ids=meter_ids,
            kwh=kwh, voltage=volts, monthly=monthly, supply_kwh=supply, tx_voltage=tx_v, events=zone_events,
            sunshine=sunshine,
        )
    return zones
