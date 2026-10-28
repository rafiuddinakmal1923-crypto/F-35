"""Canonical tables (SDD 4.1): the only thing the detection pipeline reads.

One definition drives the simulator output, the upload templates, `schema.yaml`,
upload validation and the database load, so they cannot drift apart.
Times are ISO 8601 in Asia/Kuala_Lumpur; energy is kWh per interval; voltage is volts.
"""

from __future__ import annotations

from dataclasses import dataclass, field

TIMEZONE = "Asia/Kuala_Lumpur"


@dataclass(frozen=True)
class Column:
    name: str
    type: str                 # string | float | int | bool | date | timestamp | json
    required: bool = True
    unit: str = ""
    allowed: tuple = ()
    min: float | None = None
    max: float | None = None
    description: str = ""


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[Column, ...]
    key: tuple[str, ...]
    description: str = ""
    examples: list = field(default_factory=list)

    def column(self, name: str) -> Column:
        return next(c for c in self.columns if c.name == name)

    @property
    def names(self) -> list[str]:
        return [c.name for c in self.columns]


TABLES: dict[str, Table] = {}


def _table(table: Table) -> Table:
    TABLES[table.name] = table
    return table


_table(Table(
    "transformer",
    (
        Column("transformer_id", "string", description="Distribution transformer ID"),
        Column("region", "string", description="Region code used for access limits"),
        Column("district", "string"),
        Column("capacity_kva", "float", unit="kVA", min=10, max=5000),
        Column("has_dtm", "bool", description="Has a distribution transformer meter (AS-2)"),
        Column("dtm_accuracy_class", "float", required=False, unit="%", min=0.1, max=5,
               description="Transformer meter accuracy class, e.g. 0.5"),
        Column("loss_params", "json", required=False, description="Cable and transformer parameters for the loss model (AS-8)"),
        Column("lat", "float", required=False, min=-90, max=90),
        Column("lon", "float", required=False, min=-180, max=180),
    ),
    key=("transformer_id",),
    examples=[
        ["TX-CEN-001", "CEN", "Petaling", 500, True, 0.5, '{"kva": 500}', 3.1073, 101.6067],
        ["TX-CEN-002", "CEN", "Petaling", 300, False, "", "", 3.1201, 101.6402],
    ],
))

_table(Table(
    "premise",
    (
        Column("premise_id", "string", description="Pseudonymised premise ID"),
        Column("transformer_id", "string"),
        Column("feeder_branch", "string", required=False, description="LV branch from the transformer (AS-7)"),
        Column("phase", "string", required=False, allowed=("A", "B", "C"), description="Phase the premise is connected to (AS-7)"),
        Column("distance_m", "float", required=False, unit="m", min=0, max=3000, description="Cable distance from the transformer"),
        Column("street_seq", "int", description="Order along the street"),
        Column("lat", "float", required=False, min=-90, max=90),
        Column("lon", "float", required=False, min=-180, max=180),
        Column("premise_type", "string", allowed=("terrace", "semi_d", "bungalow", "apartment", "shop")),
        Column("tariff", "string", allowed=("domestic", "commercial")),
    ),
    key=("premise_id",),
    examples=[
        ["P-CEN-001-001", "TX-CEN-001", "B1", "A", 35.0, 1, 3.1075, 101.6069, "terrace", "domestic"],
        ["P-CEN-001-002", "TX-CEN-001", "B1", "B", 35.0, 2, 3.1076, 101.6070, "terrace", "domestic"],
    ],
))

_table(Table(
    "meter",
    (
        Column("meter_id", "string", description="Meter ID (format MTR- plus digits)"),
        Column("premise_id", "string"),
        Column("meter_type", "string", allowed=("smart", "conventional")),
        Column("read_frequency", "string", allowed=("30min", "monthly")),
        Column("installed_on", "date"),
    ),
    key=("meter_id",),
    examples=[
        ["MTR-001001", "P-CEN-001-001", "smart", "30min", "2024-03-01"],
        ["MTR-001002", "P-CEN-001-002", "conventional", "monthly", "2015-07-12"],
    ],
))

_table(Table(
    "meter_reading",
    (
        Column("meter_id", "string"),
        Column("ts", "timestamp", description="Start of the 30-minute interval, ISO 8601 with +08:00"),
        Column("kwh", "float", unit="kWh", min=-10, max=50, description="Energy in the interval (negative = export)"),
        Column("voltage_v", "float", required=False, unit="V", min=150, max=280),
        Column("quality_flag", "int", required=False, allowed=(0, 1, 2), description="0 ok, 1 estimated, 2 suspect"),
    ),
    key=("meter_id", "ts"),
    examples=[
        ["MTR-001001", "2026-08-01T00:00:00+08:00", 0.412, 233.8, 0],
        ["MTR-001001", "2026-08-01T00:30:00+08:00", 0.398, 234.1, 0],
    ],
))

_table(Table(
    "meter_monthly_reading",
    (
        Column("meter_id", "string"),
        Column("month", "date", description="First day of the month"),
        Column("kwh", "float", unit="kWh", min=0, max=50000),
    ),
    key=("meter_id", "month"),
    examples=[["MTR-001002", "2026-08-01", 312.0], ["MTR-001002", "2026-09-01", 298.5]],
))

_table(Table(
    "transformer_reading",
    (
        Column("transformer_id", "string"),
        Column("ts", "timestamp", description="Start of the 30-minute interval"),
        Column("kwh_supplied", "float", unit="kWh", min=0, max=5000),
        Column("voltage_v", "float", required=False, unit="V", min=180, max=270),
    ),
    key=("transformer_id", "ts"),
    examples=[
        ["TX-CEN-001", "2026-08-01T00:00:00+08:00", 21.4, 236.2],
        ["TX-CEN-001", "2026-08-01T00:30:00+08:00", 20.9, 236.4],
    ],
))

_table(Table(
    "account_event",
    (
        Column("event_id", "string"),
        Column("premise_id", "string"),
        Column("event_type", "string", allowed=("holder_change", "change_of_tenancy", "solar_registration"),
               description="solar_registration = rooftop solar under net metering or a self-consumption scheme (AS-9)"),
        Column("event_date", "date"),
        Column("capacity_kwp", "float", required=False, unit="kWp", min=0.1, max=100,
               description="solar_registration only: installed panel capacity, for the energy-budget check (FR-PS-10)"),
        Column("has_battery", "bool", required=False,
               description="solar_registration only: a home battery can move solar energy into the evening (FR-PS-10)"),
    ),
    key=("event_id",),
    examples=[["EV-0001", "P-CEN-001-014", "change_of_tenancy", "2026-09-05", None, None],
              ["EV-0002", "P-CEN-001-020", "solar_registration", "2026-08-20", 4.0, False]],
))

_table(Table(
    "district_weather",
    (
        Column("district", "string"),
        Column("date", "date"),
        Column("temperature_c", "float", required=False, unit="°C", min=10, max=45),
        Column("sunshine_hours", "float", required=False, unit="h", min=0, max=14),
    ),
    key=("district", "date"),
    description="Optional daily weather per district (FR-DI-07); sunshine helps tell rooftop solar from theft (FR-PS-10).",
    examples=[["Petaling", "2026-08-01", 31.5, 6.2]],
))

_table(Table(
    "duty_roster",
    (
        Column("team_id", "string"),
        Column("shift_date", "date"),
        Column("base_lat", "float", min=-90, max=90),
        Column("base_lon", "float", min=-180, max=180),
        Column("on_duty", "bool"),
    ),
    key=("team_id", "shift_date"),
    examples=[["T-CEN-A", "2026-09-30", 3.0738, 101.5183, True]],
))

_table(Table(
    "customer_pii",
    (
        Column("premise_id", "string"),
        Column("holder_name", "string"),
        Column("address", "string"),
        Column("contact", "string", required=False),
    ),
    key=("premise_id",),
    description="Restricted. Fake data only in R0.",
    examples=[["P-CEN-001-001", "FAKE Siti binti Rahman", "No. 1, Jalan Contoh 1, Taman Demo, 47000 Sungai Buloh, Selangor", "012-000 0001"]],
))

_table(Table(
    "inspection_outcome",
    (
        Column("case_id", "string"),
        Column("premise_id", "string"),
        Column("outcome", "string", allowed=("confirmed_theft", "false_alarm", "inconclusive", "no_access")),
        Column("reason_tag", "string", required=False),
        Column("notes", "string", required=False),
        Column("recorded_at", "timestamp"),
        Column("origin", "string", required=False, allowed=("model", "random_sample", "manual")),
    ),
    key=("case_id",),
    description="Optional historic outcomes (labels).",
    examples=[["H-0001", "P-CEN-002-010", "confirmed_theft", "meter_bypass", "Bypass cable behind meter board.", "2026-06-12T10:30:00+08:00", "model"]],
))


def schema_document() -> dict:
    """Content of data/uploads/schema.yaml."""
    doc = {"timezone": TIMEZONE, "timestamp_format": "ISO 8601, e.g. 2026-08-01T00:30:00+08:00", "tables": {}}
    for table in TABLES.values():
        doc["tables"][table.name] = {
            "key": list(table.key),
            "description": table.description,
            "columns": {
                c.name: {
                    k: v
                    for k, v in {
                        "type": c.type,
                        "required": c.required,
                        "unit": c.unit or None,
                        "allowed": list(c.allowed) or None,
                        "min": c.min,
                        "max": c.max,
                        "description": c.description or None,
                    }.items()
                    if v is not None
                }
                for c in table.columns
            },
        }
    return doc
