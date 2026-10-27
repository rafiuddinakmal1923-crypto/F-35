"""Upload validation (prompt 3.4, SRS 5.3, FR-DI-06): coerce raw files to canonical types and check them.

Checks: missing columns, types, units and plausible ranges, allowed values, duplicates,
time-zone problems, 30-minute boundaries, at least 90% of intervals per meter-day, and every
meter linked to exactly one transformer. Errors block the dataset; warnings do not.
The same checks run on uploads (CLI and Data manager) and on the pipeline's active sources.
"""

from __future__ import annotations

import html
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime

import polars as pl

from voltguard.data.canonical import TABLES, TIMEZONE, Table

DTYPES = {
    "string": pl.Utf8, "float": pl.Float64, "int": pl.Int64, "bool": pl.Boolean,
    "date": pl.Date, "timestamp": pl.Datetime("us", TIMEZONE), "json": pl.Utf8,
}
UNIT_FACTORS = {  # source unit -> multiply to reach the canonical unit
    ("Wh", "kWh"): 0.001, ("MWh", "kWh"): 1000.0, ("kWh", "kWh"): 1.0,
    ("kV", "V"): 1000.0, ("V", "V"): 1.0, ("km", "m"): 1000.0, ("m", "m"): 1.0,
}
TRUE_WORDS = {"true", "t", "yes", "y", "1"}
FALSE_WORDS = {"false", "f", "no", "n", "0"}
OUT_OF_RANGE_ERROR_SHARE = 0.001   # above this share of rows, out-of-range values block the dataset
MIN_COMPLETENESS = 0.90            # SRS 5.3


@dataclass
class Issue:
    level: str                 # error | warning
    table: str
    check: str
    message: str
    column: str | None = None
    count: int = 0
    examples: list = field(default_factory=list)


@dataclass
class ValidationReport:
    dataset: str
    version: str
    created_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat(timespec="seconds"))
    rows: dict[str, int] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    flagged_meters: list[dict] = field(default_factory=list)   # meter-days under 90% complete (FR-DI-06)
    missing_optional: dict[str, list[str]] = field(default_factory=dict)  # drive the AS-x fallbacks

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    def add(self, level: str, table: str, check: str, message: str, column: str | None = None,
            count: int = 0, examples: list | None = None) -> None:
        self.issues.append(Issue(level, table, check, message, column, int(count), [str(e) for e in (examples or [])][:5]))

    def to_dict(self) -> dict:
        return {"dataset": self.dataset, "version": self.version, "created_at": self.created_at, "ok": self.ok,
                "status": "accepted" if self.ok else "rejected", "rows": self.rows,
                "errors": sum(i.level == "error" for i in self.issues),
                "warnings": sum(i.level == "warning" for i in self.issues),
                "issues": [asdict(i) for i in self.issues], "flagged_meters": self.flagged_meters[:500],
                "flagged_meter_days": len(self.flagged_meters), "missing_optional": self.missing_optional}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_html(self) -> str:
        d = self.to_dict()
        esc = html.escape
        rows = "".join(f"<tr><td>{esc(t)}</td><td>{n:,}</td></tr>" for t, n in d["rows"].items())
        issues = "".join(
            f"<tr class='{i['level']}'><td>{esc(i['level'])}</td><td>{esc(i['table'])}</td><td>{esc(i['column'] or '')}</td>"
            f"<td>{esc(i['check'])}</td><td>{esc(i['message'])}</td><td>{i['count']:,}</td>"
            f"<td>{esc(', '.join(i['examples']))}</td></tr>" for i in d["issues"]) or "<tr><td colspan='7'>No issues found.</td></tr>"
        missing = "".join(f"<li><b>{esc(t)}</b>: {esc(', '.join(c))}</li>" for t, c in d["missing_optional"].items())
        status = "Accepted" if self.ok else "Rejected: fix the errors below and upload again"
        return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Validation {esc(self.dataset)} {esc(self.version)}</title>
<style>body{{font-family:system-ui,sans-serif;margin:24px;color:#1b1f24}}table{{border-collapse:collapse;margin:12px 0}}
td,th{{border:1px solid #d0d7de;padding:4px 8px;text-align:left;font-size:14px}}.error td{{background:#ffebe9}}
.warning td{{background:#fff8c5}}.status{{font-weight:600;color:{'#1a7f37' if self.ok else '#cf222e'}}}</style></head><body>
<h1>Validation report: {esc(self.dataset)} ({esc(self.version)})</h1>
<p class="status">{status}</p><p>Created {esc(self.created_at)}. {d['errors']} error(s), {d['warnings']} warning(s).
{d['flagged_meter_days']} meter-day(s) below {MIN_COMPLETENESS:.0%} of intervals (flagged, FR-DI-06).</p>
<h2>Rows per table</h2><table><tr><th>Table</th><th>Rows</th></tr>{rows}</table>
<h2>Issues</h2><table><tr><th>Level</th><th>Table</th><th>Column</th><th>Check</th><th>Message</th><th>Count</th><th>Examples</th></tr>{issues}</table>
<h2>Optional fields not supplied</h2><p>The pipeline uses the SDD fallbacks (AS-2, AS-3, AS-7, AS-8) and marks affected results low confidence.</p>
<ul>{missing or '<li>None</li>'}</ul></body></html>"""


# --------------------------------------------------------------------------- coercion

def _parse_bool(s: pl.Series) -> pl.Series:
    if s.dtype == pl.Boolean:
        return s
    low = s.cast(pl.Utf8).str.strip_chars().str.to_lowercase().to_list()
    return pl.Series(s.name, [True if v in TRUE_WORDS else False if v in FALSE_WORDS else None for v in low], dtype=pl.Boolean)


def _parse_timestamp(s: pl.Series, source_tz: str, report: ValidationReport, table: str) -> pl.Series:
    """ISO 8601 with an offset is converted to Asia/Kuala_Lumpur; naive values are read as `source_tz`."""
    if isinstance(s.dtype, pl.Datetime):
        if s.dtype.time_zone is None:
            report.add("warning", table, "timezone", f"Timestamps have no time zone; read as {source_tz}", s.name, s.len())
            return s.dt.replace_time_zone(source_tz, ambiguous="earliest", non_existent="null").dt.convert_time_zone(TIMEZONE)
        if s.dtype.time_zone != TIMEZONE:
            report.add("warning", table, "timezone", f"Timestamps converted from {s.dtype.time_zone} to {TIMEZONE}", s.name, s.len())
        return s.dt.convert_time_zone(TIMEZONE)
    text = (s.cast(pl.Utf8).str.strip_chars().str.replace(" ", "T", literal=True)
            .str.replace(r"(\.\d+)?Z$", "+00:00").str.replace(r"\.\d+([+-]\d{2}:?\d{2})$", "$1"))
    has_offset = text.str.contains(r"(Z|[+-]\d{2}:?\d{2})$")
    with_offset = text.filter(has_offset)
    out = pl.Series(s.name, [None] * s.len(), dtype=pl.Datetime("us", TIMEZONE))
    # Format inference follows the first value, so each group is parsed from its own masked copy.
    only_offset = pl.select(pl.when(has_offset).then(text)).to_series()
    only_naive = pl.select(pl.when(~has_offset).then(text)).to_series()
    if with_offset.len():
        parsed = only_offset.str.to_datetime(time_zone="UTC", strict=False, time_unit="us").dt.convert_time_zone(TIMEZONE)
        out = pl.select(pl.when(has_offset).then(parsed).otherwise(out)).to_series().alias(s.name)
        other = with_offset.str.extract(r"([+-]\d{2}:?\d{2}|Z)$").drop_nulls().unique().to_list()
        other = [o for o in other if o.replace(":", "") != "+0800"]
        if other:
            report.add("warning", table, "timezone", f"Timestamps with offsets {', '.join(other)} converted to +08:00", s.name,
                       int(with_offset.str.contains(r"(Z|[+-]\d{2}:?\d{2})$").sum()), other)
    naive_count = int((~has_offset & text.is_not_null()).sum())
    if naive_count:
        naive = only_naive.str.to_datetime(strict=False, time_unit="us").dt.replace_time_zone(
            source_tz, ambiguous="earliest", non_existent="null").dt.convert_time_zone(TIMEZONE)
        out = pl.select(pl.when(~has_offset).then(naive).otherwise(out)).to_series().alias(s.name)
        report.add("warning", table, "timezone", f"{naive_count:,} timestamps have no offset; read as {source_tz}", s.name, naive_count)
    return out


def coerce(table: Table, raw: pl.DataFrame, report: ValidationReport, source_tz: str = TIMEZONE,
           units: dict[str, str] | None = None) -> pl.DataFrame:
    """Raw frame (any types, canonical column names) -> canonical types; problems go to the report."""
    columns = {}
    missing_optional = []
    for col in table.columns:
        if col.name not in raw.columns:
            if col.required:
                report.add("error", table.name, "missing_column", f"Required column '{col.name}' is missing", col.name)
            else:
                missing_optional.append(col.name)
            columns[col.name] = pl.Series(col.name, [None] * raw.height, dtype=DTYPES[col.type])
            continue
        s = raw[col.name]
        if s.dtype == pl.Utf8:
            s = s.str.strip_chars().replace({"": None, "NULL": None, "Null": None, "null": None, "NaN": None, "nan": None})
        before_nulls = s.null_count()
        if col.type == "timestamp":
            out = _parse_timestamp(s, source_tz, report, table.name)
        elif col.type == "date":
            out = s if s.dtype == pl.Date else (s.dt.date() if isinstance(s.dtype, pl.Datetime) else s.cast(pl.Utf8).str.slice(0, 10).str.to_date(strict=False))
        elif col.type == "bool":
            out = _parse_bool(s)
        elif col.type == "json":
            out = s.cast(pl.Utf8) if s.dtype != pl.Utf8 else s
        else:
            out = s.cast(DTYPES[col.type], strict=False)
        bad = out.null_count() - before_nulls
        if bad > 0:
            examples = s.filter(out.is_null() & s.is_not_null()).head(5).to_list()
            report.add("error", table.name, "type", f"{bad:,} value(s) are not a valid {col.type}", col.name, bad, examples)
        unit = (units or {}).get(col.name)
        if unit and col.unit and col.type in ("float", "int"):
            factor = UNIT_FACTORS.get((unit, col.unit))
            if factor is None:
                report.add("error", table.name, "unit", f"Cannot convert unit {unit} to {col.unit}", col.name)
            elif factor != 1.0:
                out = out.cast(pl.Float64) * factor
                report.add("warning", table.name, "unit", f"Converted {unit} to {col.unit}", col.name, out.len())
        if not col.required and out.null_count() == out.len() and raw.height:
            missing_optional.append(col.name)
        columns[col.name] = out.alias(col.name)
    if missing_optional:
        report.missing_optional[table.name] = sorted(set(missing_optional))
    extra = [c for c in raw.columns if c not in table.names]
    if extra:
        report.add("warning", table.name, "extra_columns", f"Columns not in the canonical schema are ignored: {', '.join(extra)}", count=len(extra))
    return pl.DataFrame(columns)


# --------------------------------------------------------------------------- checks

def _check_values(table: Table, frame: pl.DataFrame, report: ValidationReport) -> None:
    for col in table.columns:
        s = frame[col.name]
        if col.required and col.name in frame.columns:
            nulls = s.null_count()
            if nulls and not any(i.column == col.name and i.check in ("type", "missing_column") for i in report.issues if i.table == table.name):
                report.add("error", table.name, "required", f"{nulls:,} empty value(s) in a required column", col.name, nulls)
        if col.allowed:
            bad = s.drop_nulls().filter(~s.drop_nulls().is_in(list(col.allowed)))
            if bad.len():
                report.add("error", table.name, "allowed_values", f"Allowed values: {', '.join(map(str, col.allowed))}",
                           col.name, bad.len(), bad.unique().head(5).to_list())
        if col.type in ("float", "int") and (col.min is not None or col.max is not None):
            values = s.drop_nulls()
            out = values.filter(((values < col.min) if col.min is not None else False) | ((values > col.max) if col.max is not None else False))
            if out.len():
                share = out.len() / max(values.len(), 1)
                level = "error" if share > OUT_OF_RANGE_ERROR_SHARE else "warning"
                report.add(level, table.name, "range", f"{out.len():,} value(s) outside the plausible range "
                           f"{col.min}..{col.max} {col.unit} ({share:.2%} of rows)", col.name, out.len(), out.head(5).to_list())


def _check_duplicates(table: Table, frame: pl.DataFrame, report: ValidationReport) -> pl.DataFrame:
    key = list(table.key)
    if not frame.height or any(frame[k].null_count() == frame.height for k in key):
        return frame
    exact = frame.height - frame.unique().height
    if exact:
        report.add("warning", table.name, "duplicates", f"{exact:,} exact duplicate row(s) removed", ",".join(key), exact)
        frame = frame.unique(maintain_order=True)
    conflicts = frame.height - frame.unique(subset=key).height
    if conflicts:
        dup = frame.filter(frame.select(key).is_duplicated()).select(key).head(5).rows()
        report.add("error", table.name, "duplicates", f"{conflicts:,} row(s) share a key ({', '.join(key)}) with different values",
                   ",".join(key), conflicts, dup)
    return frame


def _check_intervals(name: str, frame: pl.DataFrame, report: ValidationReport, id_col: str) -> None:
    ts = frame["ts"].drop_nulls()
    if not ts.len():
        return
    local = ts.dt.convert_time_zone(TIMEZONE)
    off = local.filter((local.dt.minute() % 30 != 0) | (local.dt.second() != 0))
    if off.len():
        report.add("error", name, "interval", f"{off.len():,} timestamp(s) are not on a 30-minute boundary (clock error?)", "ts",
                   off.len(), off.head(5).to_list())
    if name != "meter_reading":
        return
    per_day = (frame.drop_nulls("ts").with_columns(pl.col("ts").dt.convert_time_zone(TIMEZONE).dt.date().alias("day"))
               .group_by([id_col, "day"]).agg(pl.len().alias("n")))
    first, last = per_day["day"].min(), per_day["day"].max()
    # Partial first and last days of an extract are expected; only whole days inside are checked.
    inner = per_day.filter((pl.col("day") > first) & (pl.col("day") < last)) if first != last else per_day
    low = inner.filter(pl.col("n") < MIN_COMPLETENESS * 48).sort([id_col, "day"])
    if low.height:
        report.flagged_meters = [{"meter_id": r[id_col], "date": r["day"].isoformat(), "completeness": round(r["n"] / 48, 3)}
                                 for r in low.iter_rows(named=True)]
        report.add("warning", name, "completeness", f"{low.height:,} meter-day(s) have fewer than {MIN_COMPLETENESS:.0%} of "
                   "intervals; those meters are flagged (FR-DI-06)", "ts", low.height, low[id_col].unique().head(5).to_list())
    over = per_day.filter(pl.col("n") > 48)
    if over.height:
        report.add("error", name, "interval", f"{over.height:,} meter-day(s) have more than 48 intervals (clock or time-zone error)",
                   "ts", over.height, over[id_col].unique().head(5).to_list())


def _check_links(tables: dict[str, pl.DataFrame], context: dict[str, pl.DataFrame], report: ValidationReport) -> None:
    """Every meter linked to exactly one transformer (SRS 5.3, AS-1); readings refer to known meters."""
    def get(name):
        return tables.get(name) if name in tables else context.get(name)

    meters, premises, transformers = get("meter"), get("premise"), get("transformer")
    if premises is not None and transformers is not None and premises.height:
        known = set(transformers["transformer_id"].to_list())
        orphan = premises.filter(~pl.col("transformer_id").is_in(list(known)) | pl.col("transformer_id").is_null())
        if orphan.height:
            report.add("error", "premise", "link", f"{orphan.height:,} premise(s) point to no known transformer", "transformer_id",
                       orphan.height, orphan["premise_id"].head(5).to_list())
    if meters is not None and premises is not None and meters.height:
        linked = meters.join(premises.select("premise_id", "transformer_id"), on="premise_id", how="left")
        unlinked = linked.filter(pl.col("transformer_id").is_null())
        if unlinked.height:
            report.add("error", "meter", "link", f"{unlinked.height:,} meter(s) are not linked to a transformer", "premise_id",
                       unlinked.height, unlinked["meter_id"].head(5).to_list())
        multi = linked.group_by("meter_id").agg(pl.col("transformer_id").n_unique().alias("n")).filter(pl.col("n") > 1)
        if multi.height:
            report.add("error", "meter", "link", f"{multi.height:,} meter(s) are linked to more than one transformer", "meter_id",
                       multi.height, multi["meter_id"].head(5).to_list())
    for name in ("meter_reading", "meter_monthly_reading"):
        frame = tables.get(name)
        if frame is not None and frame.height and meters is not None:
            unknown = frame.filter(~pl.col("meter_id").is_in(meters["meter_id"].to_list()))["meter_id"].unique()
            if unknown.len():
                report.add("error", name, "link", f"{unknown.len():,} meter ID(s) not in the meter table", "meter_id",
                           unknown.len(), unknown.head(5).to_list())
    frame = tables.get("transformer_reading")
    if frame is not None and frame.height and transformers is not None:
        unknown = frame.filter(~pl.col("transformer_id").is_in(transformers["transformer_id"].to_list()))["transformer_id"].unique()
        if unknown.len():
            report.add("error", "transformer_reading", "link", f"{unknown.len():,} transformer ID(s) not in the transformer table",
                       "transformer_id", unknown.len(), unknown.head(5).to_list())
    for name, col in (("account_event", "premise_id"), ("customer_pii", "premise_id")):
        frame = tables.get(name)
        if frame is not None and frame.height and premises is not None:
            unknown = frame.filter(~pl.col(col).is_in(premises["premise_id"].to_list()))[col].unique()
            if unknown.len():
                report.add("warning", name, "link", f"{unknown.len():,} premise ID(s) not in the premise table; those rows are ignored",
                           col, unknown.len(), unknown.head(5).to_list())


def validate(tables: dict[str, pl.DataFrame], report: ValidationReport,
             context: dict[str, pl.DataFrame] | None = None) -> dict[str, pl.DataFrame]:
    """Check canonical-typed tables; returns them with exact duplicates removed."""
    out = {}
    for name, frame in tables.items():
        table = TABLES[name]
        frame = _check_duplicates(table, frame, report)
        _check_values(table, frame, report)
        if name in ("meter_reading", "transformer_reading"):
            _check_intervals(name, frame, report, "meter_id" if name == "meter_reading" else "transformer_id")
        report.rows[name] = frame.height
        out[name] = frame
    _check_links(out, context or {}, report)
    return out
