"""Transformer-zone simulator (SDD 10.2, prompt 3.3).

Produces the canonical tables for a set of zones plus a separate ground-truth file.
The ground truth is written next to the tables and is never loaded into any table the
model reads; only the simulation report and model-evaluation metrics open it.

Each zone has 50-100 homes on branching LV feeders across three phases. True loads
(metered + hidden) go through the load-flow model to give the transformer meter's
supply, the technical loss and every meter's voltage. Injected cases with known answers:

* full_bypass_mining  - flat 24/7 rig load wired around the meter (theft)
* partial_bypass      - a share of one home's load wired around the meter (theft)
* metered_mining      - flat high load that is billed (must not be scored as theft)
* ev_charging, home_business, vacancy - legitimate patterns
* solar               - rooftop solar installed partway through, self-consumption (export=False)
                        or with export; registered in account_event for some (FR-PS-10, AS-9)
* tenancy_only        - a tenancy change with no theft

Voltages come from the load-flow model because the open datasets hold kWh only: R0
results show the voltage locator works on physics-consistent data, not on TNB meters (AS-3).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from voltguard import config
from voltguard.data import fakes, profiles
from voltguard.network import LossParams, ZoneNetwork, solve

SLOTS = profiles.SLOTS_PER_DAY
THEFT_KINDS = {"full_bypass_mining", "partial_bypass"}
PHASES = np.array(["A", "B", "C"])


@dataclass
class Injected:
    kind: str
    start_day: int = 0          # 0 = present from the first day of data
    size: float = 0.0           # kW for mining/EV/business/solar; share of load for partial_bypass
    tenancy_change: bool = False
    premise_type: str | None = None
    conventional: bool = False
    export: bool = True         # solar: False = self-consumption meter that never goes negative
    registered: bool = False    # solar: registration event in account_event


@dataclass
class ZoneSpec:
    number: int
    region: str = "CEN"
    district: str = "Petaling"
    n_homes: int = 75
    n_branches: int = 3
    has_dtm: bool = True
    conventional_share: float = 0.08
    voltage: bool = True
    phase_data: bool = True
    params_data: bool = True
    noise: float = 0.25
    meter_noise_v: float = 0.3
    tx_voltage_swing: float = 1.5
    missing_rate: float = 0.002
    profile_family: str = "A"
    mean_kwh: float = 11.0
    background_tenancy: int = 1
    cases: list[Injected] = field(default_factory=list)

    @property
    def transformer_id(self) -> str:
        return f"TX-{self.region}-{self.number:03d}"


@dataclass
class Scenario:
    name: str
    seed: int
    zones: list[ZoneSpec]
    start_date: date = date(2026, 8, 1)
    days: int = 61
    split: str = "demo"


# --------------------------------------------------------------------------- scenarios

def demo_scenario(seed: int | None = None) -> Scenario:
    seed = seed if seed is not None else int(config.demo_config().get("demo_seed", 20261027))
    return Scenario("demo", seed, [
        ZoneSpec(1, "CEN", "Petaling", n_homes=72, cases=[
            Injected("full_bypass_mining", start_day=0, size=4.5),
            Injected("partial_bypass", start_day=38, size=0.65, tenancy_change=True, premise_type="semi_d"),
            Injected("ev_charging", size=7.0),
            Injected("metered_mining", size=3.0),
            Injected("tenancy_only", start_day=30),
            Injected("solar", start_day=33, size=3.0, export=False, registered=True),
            Injected("solar", start_day=41, size=4.0, export=True, registered=False),
        ]),
        ZoneSpec(2, "CEN", "Petaling", n_homes=80, cases=[Injected("full_bypass_mining", start_day=30, size=6.0)]),
        ZoneSpec(3, "CEN", "Klang", n_homes=60, conventional_share=0.4, cases=[Injected("home_business", size=2.0)]),
        ZoneSpec(4, "CEN", "Klang", n_homes=55, has_dtm=False, cases=[Injected("partial_bypass", start_day=20, size=0.7, premise_type="bungalow")]),
        ZoneSpec(1, "NOR", "Timur Laut", n_homes=50, cases=[
            Injected("partial_bypass", start_day=25, size=0.75, premise_type="bungalow"),
            Injected("vacancy"),
        ]),
        ZoneSpec(2, "NOR", "Seberang Perai", n_homes=65, cases=[Injected("full_bypass_mining", start_day=20, size=3.5)]),
        ZoneSpec(3, "NOR", "Seberang Perai", n_homes=58),
    ], split="demo")


def _varied_zones(rng: np.random.Generator, count: int, sizes, mining_kw, bypass_share, noise, family, region) -> list[ZoneSpec]:
    zones = []
    for i in range(count):
        kind = ("full_bypass_mining", "partial_bypass", "both", "clean")[i % 4]
        cases: list[Injected] = []
        day_one = rng.random() < 0.35
        if kind in ("full_bypass_mining", "both"):
            cases.append(Injected("full_bypass_mining", start_day=0 if day_one else int(rng.integers(20, 45)), size=float(rng.uniform(*mining_kw))))
        if kind in ("partial_bypass", "both"):
            cases.append(Injected("partial_bypass", start_day=int(rng.integers(15, 45)), size=float(rng.uniform(*bypass_share)),
                                  premise_type=str(rng.choice(["semi_d", "bungalow"])), tenancy_change=rng.random() < 0.3))
        cases += [Injected("ev_charging", size=7.0)] * int(rng.random() < 0.6)
        cases += [Injected("metered_mining", size=float(rng.uniform(2, 4)))] * int(rng.random() < 0.4)
        cases += [Injected("tenancy_only", start_day=int(rng.integers(10, 50)))] * int(rng.random() < 0.5)
        if rng.random() < 0.5:
            cases.append(Injected("solar", start_day=int(rng.integers(15, 45)), size=float(rng.uniform(2.5, 5.0)),
                                  export=bool(rng.random() < 0.5), registered=bool(rng.random() < 0.5)))
        zones.append(ZoneSpec(
            100 + i, region, "Sim", n_homes=int(rng.integers(*sizes)), n_branches=int(rng.integers(2, 5)),
            noise=float(rng.uniform(*noise)), profile_family=family,
            conventional_share=float(rng.uniform(0.0, 0.2)), cases=cases,
        ))
    return zones


def tuning_scenario(seed: int = 1000, count: int = 24) -> Scenario:
    rng = np.random.default_rng(seed)
    zones = _varied_zones(rng, count, (50, 90), (3.0, 7.0), (0.5, 0.8), (0.2, 0.28), "A", "CEN")
    return Scenario("tuning", seed, zones, split="tuning")


def heldout_scenario(seed: int = 5000, count: int = 24) -> Scenario:
    """Held-out settings: different zone sizes, tap sizes, noise and household profile family."""
    rng = np.random.default_rng(seed)
    zones = _varied_zones(rng, count, (55, 101), (2.5, 8.0), (0.45, 0.85), (0.26, 0.34), "B", "NOR")
    return Scenario("heldout", seed, zones, split="heldout")


# --------------------------------------------------------------------------- simulation

@dataclass
class ZoneSim:
    tables: dict[str, pl.DataFrame]
    truth: dict


def _timestamps(start: date, days: int) -> list[datetime]:
    base = datetime(start.year, start.month, start.day)
    return [base + timedelta(minutes=30 * i) for i in range(days * SLOTS)]


def _ts_series(name: str, stamps: list[datetime], repeat: int = 1, tile: bool = True) -> pl.Series:
    values = np.array(stamps, dtype="datetime64[us]")
    values = np.tile(values, repeat) if tile else np.repeat(values, repeat)
    return pl.Series(name, values).dt.replace_time_zone(config_tz())


def config_tz() -> str:
    from voltguard.data.canonical import TIMEZONE

    return TIMEZONE


def simulate_zone(scn: Scenario, zone: ZoneSpec) -> ZoneSim:
    rng = np.random.default_rng(scn.seed * 31 + zone.number * 1009 + (0 if zone.region == "CEN" else 7))
    n, days, T = zone.n_homes, scn.days, scn.days * SLOTS
    tx_id = zone.transformer_id
    ids = [f"P-{zone.region}-{zone.number:03d}-{i + 1:03d}" for i in range(n)]
    meter_ids = [f"MTR-{(0 if zone.region == 'CEN' else 5) * 1000 + zone.number:04d}{i + 1:03d}" for i in range(n)]

    # Network: branches are chains of poles; 1-3 homes per pole; phases rotate with shuffling.
    branch_of = np.array([f"B{1 + (i * zone.n_branches) // n}" for i in range(n)])
    distance = np.zeros(n)
    for b in sorted(set(branch_of)):
        idx = np.where(branch_of == b)[0]
        pole, homes_on_pole, d = 0, 0, rng.uniform(15, 30)
        for j in idx:
            if homes_on_pole >= rng.integers(1, 4):
                pole, homes_on_pole, d = pole + 1, 0, d + rng.uniform(28, 40)
            distance[j] = round(d, 1)
            homes_on_pole += 1
    phase_idx = np.array([rng.permutation(3) for _ in range(n // 3 + 1)]).ravel()[:n]
    types = rng.choice(["terrace", "semi_d", "bungalow"], size=n, p=[0.7, 0.2, 0.1])
    type_scale = {"terrace": 1.0, "semi_d": 1.35, "bungalow": 1.9}

    # Choose premises for injected cases (deterministic for a given seed).
    free = list(rng.permutation(n))
    assignments: list[tuple[int, Injected]] = []
    for case in zone.cases:
        pick = next((i for i in free if case.premise_type is None or types[i] == case.premise_type), free[0])
        free.remove(pick)
        assignments.append((int(pick), case))
    case_idx = {i for i, _ in assignments}
    conventional = np.zeros(n, dtype=bool)
    for i, case in assignments:
        conventional[i] = case.conventional
    candidates = [i for i in range(n) if i not in case_idx]
    n_conv = int(round(zone.conventional_share * n))
    if n_conv:
        conventional[rng.choice(candidates, size=min(n_conv, len(candidates)), replace=False)] = True

    # Household load.
    shapes = None
    if config.data_sources().get("profiles") == "london":
        shapes = profiles.london_shapes(config.data_root() / "processed" / "london_profiles.parquet", rng, n)
    if shapes is None:
        shapes = profiles.synthetic_shapes(rng, n, zone.profile_family)
    levels = profiles.daily_levels(rng, n, zone.mean_kwh) * np.array([type_scale[t] for t in types])
    weather = district_weather(scn, zone.district)
    heat = 1.0 + 0.04 * (weather["temperature_c"] - 31.0)
    if config.data_sources().get("rescale") == "datagovmy":
        from voltguard.data.adapters import datagovmy

        factors = datagovmy.month_factors()
        if factors is not None:
            months = np.array([(scn.start_date + timedelta(days=d)).month for d in range(days)])
            heat = heat * factors[months]
    base_kw = profiles.household_load_kw(rng, shapes, levels, days, scn.start_date.weekday(), heat, zone.noise)

    true_kw = base_kw.copy()
    metered_kw = base_kw.copy()
    hours = np.tile(profiles.HOURS, days)
    day_of = np.repeat(np.arange(days), SLOTS)
    truth_cases = []
    for i, case in assignments:
        active = day_of >= case.start_day
        stolen_kw = np.zeros(T)
        if case.kind == "full_bypass_mining":
            rig = case.size * (1 + rng.normal(0, 0.02, T))
            true_kw[i] = base_kw[i] + rig * active
            metered_kw[i] = np.where(active, base_kw[i] * 0.35, base_kw[i])
            stolen_kw = true_kw[i] - metered_kw[i]
        elif case.kind == "partial_bypass":
            metered_kw[i] = np.where(active, base_kw[i] * (1 - case.size), base_kw[i])
            stolen_kw = true_kw[i] - metered_kw[i]
        elif case.kind == "metered_mining":
            rig = case.size * (1 + rng.normal(0, 0.02, T))
            true_kw[i] = metered_kw[i] = base_kw[i] + rig
        elif case.kind == "ev_charging":
            nights = rng.random(days) < 0.8
            start = rng.uniform(22.0, 24.0, days)
            dur = rng.uniform(2.5, 4.0, days)
            rel = (hours - start[day_of]) % 24
            block = (rel < dur[day_of]) & nights[day_of]
            true_kw[i] = metered_kw[i] = base_kw[i] + case.size * block
        elif case.kind == "home_business":
            weekday = ((scn.start_date.weekday() + day_of) % 7) < 5
            block = (hours >= 9) & (hours < 18) & weekday
            true_kw[i] = metered_kw[i] = base_kw[i] + case.size * block
        elif case.kind == "solar":
            # Generation follows the time of day and the day's sunshine; self-consumed solar lowers
            # the premise meter and the transformer meter equally, so no zone gap opens.
            daylight = np.clip(np.sin((hours - 7) / 12 * np.pi), 0, None)
            sun = daylight * (weather["sunshine_hours"] / 8.0)[day_of] * active
            net = base_kw[i] - case.size * sun
            true_kw[i] = metered_kw[i] = net if case.export else np.maximum(net, 0.0)
        elif case.kind == "vacancy":
            true_kw[i] = metered_kw[i] = base_kw[i] * 0.02 + 0.01
        truth_cases.append({
            "premise_id": ids[i], "kind": case.kind, "is_theft": case.kind in THEFT_KINDS,
            "start_day": case.start_day,
            "start_date": (scn.start_date + timedelta(days=case.start_day)).isoformat(),
            "stolen_kwh_per_day": round(float(stolen_kw[day_of >= case.start_day].sum() * 0.5 / max(days - case.start_day, 1)), 2),
            "tenancy_change": case.tenancy_change or case.kind == "tenancy_only",
            "conventional": bool(conventional[i]),
            **({"export": case.export, "registered": case.registered} if case.kind == "solar" else {}),
        })

    # Load flow with the true loads gives supply, technical loss and meter voltages.
    params = LossParams(kva=float(rng.choice([300.0, 500.0])))
    net = ZoneNetwork.from_premises(branch_of, distance, phase_idx, params)
    v_tx = 236.0 + zone.tx_voltage_swing * np.sin((hours - 4) / 24 * 2 * np.pi) + np.repeat(rng.normal(0, 0.6, days), SLOTS)
    flow = solve(net, true_kw, v_tx)

    stamps = _timestamps(scn.start_date, days)
    smart = ~conventional
    n_smart = int(smart.sum())
    kwh = metered_kw[smart] * 0.5 + rng.normal(0, 0.002, (n_smart, T))
    volts = flow.prem_voltage[smart] + rng.normal(0, zone.meter_noise_v, (n_smart, T))
    keep = rng.random((n_smart, T)) >= zone.missing_rate
    readings = pl.DataFrame({
        "meter_id": np.repeat(np.array(meter_ids)[smart], T),
        "ts": _ts_series("ts", stamps, repeat=n_smart, tile=True),
        "kwh": np.round(kwh.ravel(), 3),
        "voltage_v": np.round(volts.ravel(), 1) if zone.voltage else np.full(n_smart * T, None, dtype=object),
        "quality_flag": np.zeros(n_smart * T, dtype=np.int64),
    }).filter(pl.Series(keep.ravel()))
    if not zone.voltage:
        readings = readings.with_columns(pl.lit(None, dtype=pl.Float64).alias("voltage_v"))

    month_of = np.array([(scn.start_date + timedelta(days=int(d))).replace(day=1) for d in range(days)])
    monthly_rows = []
    for i in np.where(conventional)[0]:
        daily = metered_kw[i].reshape(days, SLOTS).sum(axis=1) * 0.5
        for month in sorted(set(month_of)):
            monthly_rows.append({"meter_id": meter_ids[i], "month": month, "kwh": round(float(daily[month_of == month].sum()), 1)})

    accuracy = 0.5
    bias = rng.uniform(-accuracy, accuracy) / 100.0 * 0.6
    supplied = flow.supply_kw * 0.5 * (1 + bias) * (1 + rng.normal(0, 0.002, T))
    tx_rows = pl.DataFrame({
        "transformer_id": [tx_id] * T,
        "ts": _ts_series("ts", stamps),
        "kwh_supplied": np.round(supplied, 3),
        "voltage_v": np.round(v_tx + rng.normal(0, 0.2, T), 1),
    }) if zone.has_dtm else None

    # Geography: branches fan out from the transformer.
    base_lat = {"CEN": 3.10, "NOR": 5.38}[zone.region] + zone.number * 0.011
    base_lon = {"CEN": 101.60, "NOR": 100.30}[zone.region] + zone.number * 0.013
    bearing = {b: k * 2 * np.pi / zone.n_branches for k, b in enumerate(sorted(set(branch_of)))}
    lat = np.array([base_lat + distance[i] * np.cos(bearing[branch_of[i]]) / 111_000 for i in range(n)])
    lon = np.array([base_lon + distance[i] * np.sin(bearing[branch_of[i]]) / 111_000 for i in range(n)])
    order = np.lexsort((distance, branch_of))
    street_seq = np.empty(n, dtype=int)
    street_seq[order] = np.arange(1, n + 1)

    tables: dict[str, pl.DataFrame] = {
        "transformer": pl.DataFrame([{
            "transformer_id": tx_id, "region": zone.region, "district": zone.district,
            "capacity_kva": params.kva, "has_dtm": zone.has_dtm,
            "dtm_accuracy_class": accuracy if zone.has_dtm else None,
            # The utility's network model never matches the real cables exactly: record the
            # parameters with a realistic error so the loss model's own error is measurable.
            "loss_params": json.dumps(recorded_params(params, rng)) if zone.params_data else None,
            "lat": round(base_lat, 5), "lon": round(base_lon, 5),
        }]),
        "premise": pl.DataFrame({
            "premise_id": ids, "transformer_id": [tx_id] * n,
            "feeder_branch": branch_of.tolist() if zone.phase_data else [None] * n,
            "phase": PHASES[phase_idx].tolist() if zone.phase_data else [None] * n,
            "distance_m": distance.tolist() if zone.phase_data else [None] * n,
            "street_seq": street_seq.tolist(),
            "lat": np.round(lat, 6).tolist(), "lon": np.round(lon, 6).tolist(),
            "premise_type": types.tolist(), "tariff": ["domestic"] * n,
        }),
        "meter": pl.DataFrame({
            "meter_id": meter_ids, "premise_id": ids,
            "meter_type": np.where(conventional, "conventional", "smart").tolist(),
            "read_frequency": np.where(conventional, "monthly", "30min").tolist(),
            "installed_on": [date(2024, 3, 1) if not c else date(2015, 6, 1) for c in conventional],
        }),
        "meter_reading": readings,
        "meter_monthly_reading": pl.DataFrame(monthly_rows, schema={"meter_id": pl.Utf8, "month": pl.Date, "kwh": pl.Float64}),
    }
    if tx_rows is not None:
        tables["transformer_reading"] = tx_rows

    events = []
    for i, case in assignments:
        if case.tenancy_change or case.kind == "tenancy_only":
            day = max(case.start_day + int(rng.integers(-2, 3)), 1)
            events.append({"premise_id": ids[i], "event_type": "change_of_tenancy", "event_date": scn.start_date + timedelta(days=day)})
        if case.kind == "solar" and case.registered:
            events.append({"premise_id": ids[i], "event_type": "solar_registration", "event_date": scn.start_date + timedelta(days=max(case.start_day - 3, 0))})
    for i in rng.choice(candidates, size=min(zone.background_tenancy, len(candidates)), replace=False):
        events.append({"premise_id": ids[int(i)], "event_type": "holder_change", "event_date": scn.start_date + timedelta(days=int(rng.integers(1, days)))})
    tables["account_event"] = pl.DataFrame(
        [{"event_id": f"AE-{tx_id}-{k + 1:03d}", **e} for k, e in enumerate(events)],
        schema={"event_id": pl.Utf8, "premise_id": pl.Utf8, "event_type": pl.Utf8, "event_date": pl.Date},
    )
    tables["customer_pii"] = pl.DataFrame({
        "premise_id": ids,
        "holder_name": [fakes.fake_name(rng) for _ in range(n)],
        "address": [fakes.fake_address(rng, zone.region, int(street_seq[i]) * 2, zone.number) for i in range(n)],
        "contact": [fakes.fake_phone(rng) for _ in range(n)],
    })

    supply_kwh_day = flow.supply_kw.reshape(days, SLOTS).sum(axis=1) * 0.5
    loss_kwh_day = flow.loss_kw.reshape(days, SLOTS).sum(axis=1) * 0.5
    truth = {
        "transformer_id": tx_id, "region": zone.region, "has_dtm": zone.has_dtm, "n_homes": n,
        "spec": {k: v for k, v in asdict(zone).items() if k != "cases"},
        "cases": truth_cases,
        "mean_supply_kwh_per_day": round(float(supply_kwh_day.mean()), 1),
        "mean_tech_loss_kwh_per_day": round(float(loss_kwh_day.mean()), 2),
        "tech_loss_share": round(float(loss_kwh_day.sum() / max(supply_kwh_day.sum(), 1e-9)), 4),
        "tech_loss_kwh_daily": np.round(loss_kwh_day, 2).tolist(),
    }
    return ZoneSim(tables, truth)


def recorded_params(true: LossParams, rng: np.random.Generator, error: float = 0.12) -> dict:
    recorded = true.to_dict()
    for key in ("r_phase_ohm_per_m", "x_phase_ohm_per_m", "r_neutral_ohm_per_m", "r_service_ohm"):
        recorded[key] = round(recorded[key] * float(np.clip(rng.normal(1.0, error), 0.7, 1.3)), 7)
    return recorded


def district_weather(scn: Scenario, district: str) -> dict[str, np.ndarray]:
    """Daily temperature and sunshine for a district (shared by its zones, stable per seed)."""
    import zlib

    rng = np.random.default_rng(scn.seed * 7 + zlib.crc32(district.encode()))
    days = np.arange(scn.days)
    temperature = 31.0 + 1.2 * np.sin(days / 6.0) + rng.normal(0, 0.8, scn.days)
    sunshine = np.clip(6.5 + 1.5 * np.sin(days / 4.0 + 1) + rng.normal(0, 1.8, scn.days), 0.5, 11.0)
    return {"temperature_c": temperature, "sunshine_hours": sunshine}


def weather_table(scn: Scenario) -> pl.DataFrame:
    rows = []
    for district in sorted({z.district for z in scn.zones}):
        w = district_weather(scn, district)
        for d in range(scn.days):
            rows.append({"district": district, "date": scn.start_date + timedelta(days=d),
                         "temperature_c": round(float(w["temperature_c"][d]), 1),
                         "sunshine_hours": round(float(w["sunshine_hours"][d]), 1)})
    return pl.DataFrame(rows)


def duty_roster(start: date, days: int) -> pl.DataFrame:
    rows = []
    for team in config.demo_config().get("teams", []):
        for d in range(days + 14):
            day = start + timedelta(days=d)
            rows.append({"team_id": team["team_id"], "shift_date": day, "base_lat": team["base_lat"],
                         "base_lon": team["base_lon"], "on_duty": not (team["team_id"] == "T-CEN-B" and day.weekday() == 6)})
    return pl.DataFrame(rows, schema={"team_id": pl.Utf8, "shift_date": pl.Date, "base_lat": pl.Float64, "base_lon": pl.Float64, "on_duty": pl.Boolean})


def simulate(scn: Scenario) -> tuple[dict[str, pl.DataFrame], dict]:
    parts: dict[str, list[pl.DataFrame]] = {}
    truth = {"run": scn.name, "seed": scn.seed, "split": scn.split, "start_date": scn.start_date.isoformat(), "days": scn.days, "zones": {}}
    for zone in scn.zones:
        sim = simulate_zone(scn, zone)
        for name, frame in sim.tables.items():
            parts.setdefault(name, []).append(frame)
        truth["zones"][zone.transformer_id] = sim.truth
    tables = {name: pl.concat(frames, how="vertical_relaxed") for name, frames in parts.items()}
    tables["duty_roster"] = duty_roster(scn.start_date, scn.days)
    tables["district_weather"] = weather_table(scn)
    return tables, truth


def write_run(scn: Scenario, tables: dict[str, pl.DataFrame], truth: dict) -> Path:
    folder = config.data_root() / "simulated" / scn.name
    (folder / "tables").mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.write_parquet(folder / "tables" / f"{name}.parquet")
    (folder / "ground_truth.json").write_text(json.dumps(truth, indent=2, default=str), encoding="utf-8")
    (folder / "scenario.json").write_text(json.dumps(asdict(scn), indent=2, default=str), encoding="utf-8")
    return folder


def load_run_tables(run: str) -> dict[str, pl.DataFrame]:
    folder = config.data_root() / "simulated" / run / "tables"
    return {p.stem: pl.read_parquet(p) for p in sorted(folder.glob("*.parquet"))}


def load_truth(run: str) -> dict:
    return json.loads((config.data_root() / "simulated" / run / "ground_truth.json").read_text(encoding="utf-8"))
