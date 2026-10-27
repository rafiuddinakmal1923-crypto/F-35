"""Upload area ingest (prompt 3.4): `make.ps1 ingest -Dataset <name>` and POST /admin/datasets.

Files dropped into DATA_ROOT/uploads/<dataset>/ (CSV or Parquet) are mapped to canonical tables
by an optional `column_map.yaml`, coerced, validated and stored as a new version under
DATA_ROOT/datasets/<dataset>/v<N>/ with a manifest and an HTML + JSON validation report.
Rejected versions keep their report but no tables. Activation is a change to
config/data_sources.yaml (`--activate` or the Data manager's Activate button).

column_map.yaml (all keys optional):

    timezone: Asia/Kuala_Lumpur        # for timestamps without an offset
    files:
      readings_oct.csv:
        table: meter_reading
        columns: {METER_NO: meter_id, READ_TIME: ts, KWH: kwh, VOLT: voltage_v}
        units: {kwh: Wh}               # converted to the canonical unit
        timezone: Asia/Kuala_Lumpur
Without a map, each file's name must be a canonical table name (meter_reading.csv) and its
columns the canonical names.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import polars as pl
import yaml

from voltguard import config
from voltguard.cli import command
from voltguard.data import sources
from voltguard.data.canonical import TABLES, TIMEZONE
from voltguard.data.validation import ValidationReport, coerce, validate

SUPPORTED = (".csv", ".parquet")


@dataclass
class IngestResult:
    dataset: str
    version: str
    report: ValidationReport
    tables: dict[str, pl.DataFrame]
    folder: Path

    @property
    def ok(self) -> bool:
        return self.report.ok


def uploads_root() -> Path:
    return config.data_root() / "uploads"


def read_raw(path: Path) -> pl.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pl.read_parquet(path)
    # Everything as text first, so type problems are reported per value instead of failing the read.
    return pl.read_csv(path, infer_schema=False, try_parse_dates=False, encoding="utf8-lossy")


def load_column_map(folder: Path) -> dict:
    path = folder / "column_map.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def next_version(name: str) -> str:
    existing = [int(p.name[1:]) for p in (sources.datasets_root() / name).glob("v*") if p.name[1:].isdigit()]
    return f"v{max(existing, default=0) + 1}"


def map_files(folder: Path, column_map: dict, report: ValidationReport) -> dict[str, list[tuple[Path, dict]]]:
    """Group the dataset's files by target table."""
    files_cfg = column_map.get("files", {}) or {}
    grouped: dict[str, list[tuple[Path, dict]]] = {}
    for path in sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED):
        spec = files_cfg.get(path.name, {}) or {}
        table = spec.get("table") or path.stem.lower()
        if table not in TABLES:
            report.add("error", path.name, "table", f"Cannot tell which table '{path.name}' fills: name the file after a "
                       f"canonical table or add it to column_map.yaml ({', '.join(TABLES)})")
            continue
        grouped.setdefault(table, []).append((path, spec))
    if not grouped:
        report.add("error", "-", "files", f"No CSV or Parquet files found in {folder}")
    return grouped


def build_tables(folder: Path, report: ValidationReport) -> dict[str, pl.DataFrame]:
    column_map = load_column_map(folder)
    default_tz = column_map.get("timezone", TIMEZONE)
    tables: dict[str, pl.DataFrame] = {}
    for table_name, files in map_files(folder, column_map, report).items():
        parts = []
        for path, spec in files:
            raw = read_raw(path)
            rename = {src: dst for src, dst in (spec.get("columns") or {}).items() if src in raw.columns}
            missing_src = [src for src in (spec.get("columns") or {}) if src not in raw.columns]
            if missing_src:
                report.add("error", table_name, "column_map", f"{path.name}: mapped column(s) not in the file: {', '.join(missing_src)}")
            raw = raw.rename(rename)
            parts.append(coerce(TABLES[table_name], raw, report, spec.get("timezone", default_tz), spec.get("units")))
        tables[table_name] = pl.concat(parts, how="vertical_relaxed") if len(parts) > 1 else parts[0]
    return tables


def context_for(tables: dict[str, pl.DataFrame]) -> dict[str, pl.DataFrame]:
    """Currently active tables this dataset does not replace, for the cross-table link checks."""
    context = {}
    for name in ("transformer", "premise", "meter"):
        if name in tables:
            continue
        try:
            frame = sources.load_table(name, sources.active_sources()[name])
        except sources.SourceError:
            frame = None
        if frame is not None:
            context[name] = frame
    return context


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def ingest(name: str, folder: Path | None = None, activate: bool = False, actor: str = "cli") -> IngestResult:
    folder = folder or uploads_root() / name
    if not folder.is_dir():
        raise FileNotFoundError(f"No upload folder {folder}; create it and drop CSV or Parquet files in it")
    version = next_version(name)
    report = ValidationReport(name, version)
    tables = build_tables(folder, report)
    tables = validate(tables, report, context_for(tables))

    out = sources.datasets_root() / name / version
    out.mkdir(parents=True, exist_ok=True)
    if report.ok:
        for table_name, frame in tables.items():
            frame.write_parquet(out / f"{table_name}.parquet")
    files = [{"file": p.name, "bytes": p.stat().st_size, "sha256": _checksum(p)}
             for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in SUPPORTED + (".yaml",)]
    manifest = {"dataset": name, "version": version, "status": "accepted" if report.ok else "rejected",
                "created_at": datetime.now().astimezone().isoformat(timespec="seconds"), "created_by": actor,
                "tables": {t: f.height for t, f in tables.items()}, "files": files,
                "missing_optional": report.missing_optional, "activated": False}
    (out / "validation.json").write_text(report.to_json(), encoding="utf-8")
    (out / "validation.html").write_text(report.to_html(), encoding="utf-8")
    reports_dir = folder / "_reports" / version
    reports_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(out / "validation.json", reports_dir / "validation.json")
    shutil.copy(out / "validation.html", reports_dir / "validation.html")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    result = IngestResult(name, version, report, tables, out)
    if activate and report.ok:
        activate_dataset(name, version)
    return result


def activate_dataset(name: str, version: str | None = None) -> list[str]:
    """Point every table this dataset version holds at it in data_sources.yaml."""
    versions = sources.dataset_versions(name)
    chosen = next((v for v in versions if v["version"] == version), None) if version else (versions[-1] if versions else None)
    if not chosen or chosen["status"] != "accepted":
        raise sources.SourceError(f"Dataset {name} {version or ''} is not an accepted version")
    source = f"upload:{name}@{chosen['version']}"
    for table in chosen["tables"]:
        sources.set_source(table, source)
    manifest_path = sources.datasets_root() / name / chosen["version"] / "manifest.json"
    chosen["activated"] = True
    chosen["activated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(chosen, indent=2), encoding="utf-8")
    return list(chosen["tables"])


def preview(name: str, version: str, rows: int = 10) -> dict[str, list[dict]]:
    folder = sources.datasets_root() / name / version
    return {p.stem: pl.read_parquet(p).head(rows).to_dicts() for p in sorted(folder.glob("*.parquet"))}


# --------------------------------------------------------------------------- upload kit

def write_upload_kit(target: Path | None = None) -> Path:
    """data/uploads/: schema.yaml, one CSV template per table, an example column_map.yaml."""
    from voltguard.data.canonical import schema_document

    target = target or config.REPO_ROOT / "data" / "uploads"
    templates = target / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    (target / "schema.yaml").write_text(
        "# Canonical schema for uploads. Generated from backend/voltguard/data/canonical.py; do not edit by hand.\n"
        + yaml.safe_dump(schema_document(), sort_keys=False, allow_unicode=True), encoding="utf-8")
    def text(value) -> str:
        if value is None:
            return ""
        return str(value).lower() if isinstance(value, bool) else str(value)

    for table in TABLES.values():
        rows = [[text(v) for v in row] for row in table.examples]
        frame = pl.DataFrame(rows, schema={c: pl.Utf8 for c in table.names}, orient="row")
        frame.write_csv(templates / f"{table.name}.csv")
    return target


# --------------------------------------------------------------------------- CLI

def _print_result(result: IngestResult) -> None:
    d = result.report.to_dict()
    print(f"{result.dataset} {result.version}: {d['status'].upper()} ({d['errors']} error(s), {d['warnings']} warning(s))")
    for table, n in d["rows"].items():
        print(f"  {table:24s} {n:>10,d} rows")
    for issue in d["issues"]:
        print(f"  [{issue['level']}] {issue['table']}.{issue['column'] or '-'} {issue['check']}: {issue['message']}")
    print(f"Report: {result.folder / 'validation.html'}")


@command("ingest", "Validate an upload folder (DATA_ROOT/uploads/<dataset>) and store it as a new version",
         lambda p: (p.add_argument("dataset"), p.add_argument("--activate", action="store_true",
                                                               help="point data_sources.yaml at this version if accepted")))
def cmd_ingest(args) -> int:
    result = ingest(args.dataset, activate=args.activate)
    _print_result(result)
    if result.ok and args.activate:
        print("Activated in config/data_sources.yaml; run make.ps1 pipeline to use it.")
    elif result.ok:
        print(f"Activate with: python -m voltguard activate {args.dataset} {result.version}")
    return 0 if result.ok else 2


@command("activate", "Point data_sources.yaml at an accepted dataset version",
         lambda p: (p.add_argument("dataset"), p.add_argument("version", nargs="?")))
def cmd_activate(args) -> int:
    tables = activate_dataset(args.dataset, args.version)
    print(f"Active for: {', '.join(tables)}. Run make.ps1 pipeline to use it.")
    return 0


@command("sources", "Show the active source of every canonical table")
def cmd_sources(args) -> int:
    for table, source in sources.active_sources().items():
        print(f"{table:24s} {source}")
    return 0


@command("upload-kit", "Regenerate data/uploads/schema.yaml and the CSV templates from the canonical schema")
def cmd_upload_kit(args) -> int:
    print(f"Wrote {write_upload_kit()}")
    return 0


@command("convert", "Convert raw public datasets (DATA_ROOT/raw/...) to Parquet once",
         lambda p: p.add_argument("--force", action="store_true"))
def cmd_convert(args) -> int:
    from voltguard.data.adapters import datagovmy, london, sgcc

    for name, module in (("london", london), ("sgcc", sgcc), ("datagovmy", datagovmy)):
        try:
            result = module.convert(force=args.force)
        except Exception as exc:  # one bad download must not stop the others
            print(f"{name:10s} FAILED: {exc}")
            continue
        print(f"{name:10s} {result if result else 'no raw files (offline mode uses the built-in generator)'}")
    return 0
