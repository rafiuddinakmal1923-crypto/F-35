"""Jobs, Data manager, settings and audit (SDD 7; FR-AD-02, FR-AD-03, prompt 3.4)."""

from __future__ import annotations

import re
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import HTMLResponse

from voltguard import audit as audit_mod
from voltguard import db
from voltguard.api.deps import bad_request, connection, not_found, require
from voltguard.data import ingest, sources
from voltguard.data.canonical import TABLES
from voltguard.db import Caller
from voltguard.service import jobs, pipeline, settings

router = APIRouter()
DATASET_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


# --------------------------------------------------------------------------- jobs

@router.post("/jobs/run-detection", tags=["jobs"])
def run_detection(wait: bool = False, c: Caller = Depends(require("pipeline", "data_scientist"))):
    """Ingest, zone balance, locator and scoring. Creates no cases."""
    job_id = jobs.submit("run_detection", c.user_id, lambda progress: pipeline.run_detection(c.user_id, progress), wait=wait)
    return {"job_id": job_id}


@router.get("/jobs/{job_id}", tags=["jobs"])
def job_status(job_id: int, c: Caller = Depends(require("pipeline", "data_scientist", "admin", "supervisor", "analyst", "manager")),
               conn=Depends(connection)):
    row = jobs.status(conn, job_id)
    if not row:
        raise not_found("No such job")
    return row


@router.get("/jobs", tags=["jobs"])
def jobs_running(c: Caller = Depends(require("pipeline", "data_scientist", "admin", "supervisor", "analyst", "manager")),
                 conn=Depends(connection)):
    recent = conn.execute("SELECT job_id, kind, status, progress, started_by, created_at, finished_at FROM job_run "
                          "ORDER BY job_id DESC LIMIT 10").fetchall()
    return {"active": jobs.running(conn), "recent": recent}


# --------------------------------------------------------------------------- Data manager (admin)

@router.get("/admin/datasets", tags=["data manager"])
def datasets(c: Caller = Depends(require("admin"))):
    root = sources.datasets_root()
    out = []
    for folder in sorted(p for p in root.glob("*") if p.is_dir()) if root.exists() else []:
        out.append({"dataset": folder.name, "versions": sources.dataset_versions(folder.name)})
    return {"datasets": out, "active_sources": sources.active_sources(), "tables": list(TABLES)}


@router.post("/admin/datasets", tags=["data manager"])
async def upload_dataset(dataset: str = Form(...), table: str = Form(...), file: UploadFile = File(...),
                         c: Caller = Depends(require("admin")), conn=Depends(connection)):
    """Upload a CSV or Parquet file for one canonical table, validate it and create a new version."""
    if not DATASET_NAME.match(dataset):
        raise bad_request("Dataset names use letters, digits, '_', '-' and '.' only")
    if table not in TABLES:
        raise bad_request(f"Unknown table; choose one of {', '.join(TABLES)}")
    suffix = ".parquet" if (file.filename or "").lower().endswith(".parquet") else ".csv"
    folder = ingest.uploads_root() / dataset
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob(f"{table}.*"):
        old.unlink()
    with (folder / f"{table}{suffix}").open("wb") as out:
        shutil.copyfileobj(file.file, out)
    result = ingest.ingest(dataset, folder, actor=c.user_id)
    db.audit(conn, c.user_id, "dataset.upload", f"dataset:{dataset}@{result.version}",
             {"table": table, "status": "accepted" if result.ok else "rejected"})
    return {"dataset": dataset, "version": result.version, "report": result.report.to_dict(),
            "preview": ingest.preview(dataset, result.version, 10) if result.ok else {}}


@router.get("/admin/datasets/{dataset}/versions/{version}/report", tags=["data manager"], response_class=HTMLResponse)
def dataset_report(dataset: str, version: str, c: Caller = Depends(require("admin"))):
    path = sources.datasets_root() / dataset / version / "validation.html"
    if not DATASET_NAME.match(dataset) or not re.fullmatch(r"v\d+", version) or not path.exists():
        raise not_found("No such report")
    return HTMLResponse(path.read_text(encoding="utf-8"))


@router.get("/admin/datasets/{dataset}/versions/{version}/preview", tags=["data manager"])
def dataset_preview(dataset: str, version: str, rows: int = Query(10, le=100), c: Caller = Depends(require("admin"))):
    if not DATASET_NAME.match(dataset) or not re.fullmatch(r"v\d+", version):
        raise not_found("No such version")
    return ingest.preview(dataset, version, rows)


@router.post("/admin/datasets/{dataset}/versions/{version}/activate", tags=["data manager"])
def dataset_activate(dataset: str, version: str, c: Caller = Depends(require("admin")), conn=Depends(connection)):
    if not DATASET_NAME.match(dataset) or not re.fullmatch(r"v\d+", version):
        raise not_found("No such version")
    try:
        tables = ingest.activate_dataset(dataset, version)
    except sources.SourceError as exc:
        raise bad_request(str(exc)) from exc
    db.audit(conn, c.user_id, "dataset.activate", f"dataset:{dataset}@{version}", {"tables": tables})
    return {"activated": tables, "active_sources": sources.active_sources(),
            "next": "Run detection (POST /jobs/run-detection) to use the new data"}


@router.post("/admin/sources/{table}", tags=["data manager"])
def set_source(table: str, source: str = Form(...), c: Caller = Depends(require("admin")), conn=Depends(connection)):
    """Switch one table back to `simulated`, `london` or another dataset."""
    if table not in TABLES:
        raise not_found("Unknown table")
    if source not in ("simulated", "london") and not source.startswith("upload:"):
        raise bad_request("Source must be simulated, london or upload:<dataset>[@vN]")
    sources.set_source(table, source)
    db.audit(conn, c.user_id, "dataset.set_source", f"table:{table}", {"source": source})
    return {"active_sources": sources.active_sources()}


# --------------------------------------------------------------------------- settings (FR-AD-03)

@router.get("/settings/thresholds", tags=["settings"])
def get_thresholds(c: Caller = Depends(require("analyst", "admin", "data_scientist", "manager", "supervisor")), conn=Depends(connection)):
    cfg = settings.thresholds(conn)
    return {"effective": {k: cfg[k] for k in settings.EDITABLE if k in cfg}, "overrides": settings.overrides(conn)}


@router.put("/settings/thresholds", tags=["settings"])
def put_thresholds(change: dict, c: Caller = Depends(require("admin")), conn=Depends(connection)):
    try:
        merged = settings.save(conn, change, c.user_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    db.audit(conn, c.user_id, "settings.change", "setting:thresholds", change)
    return {"overrides": merged, "next": "The next detection run uses the new values"}


# --------------------------------------------------------------------------- audit (FR-AD-02, NFR-12)

@router.get("/audit", tags=["audit"])
def audit_log(from_: datetime | None = Query(None, alias="from"), to: datetime | None = None, user: str | None = None,
              action: str | None = None, limit: int = Query(100, le=1000), cursor: int | None = None,
              c: Caller = Depends(require("auditor")), conn=Depends(connection)):
    rows = conn.execute(
        """SELECT log_id, ts, user_id, action, object_ref, detail, row_hash FROM audit_log
           WHERE (%s::timestamptz IS NULL OR ts >= %s) AND (%s::timestamptz IS NULL OR ts <= %s)
             AND (%s::text IS NULL OR user_id = %s) AND (%s::text IS NULL OR action LIKE %s || '%%')
             AND (%s::bigint IS NULL OR log_id < %s)
           ORDER BY log_id DESC LIMIT %s""",
        (from_, from_, to, to, user, user, action, action, cursor, cursor, limit)).fetchall()
    return {"rows": rows, "next_cursor": rows[-1]["log_id"] if len(rows) == limit else None}


@router.get("/audit/verify", tags=["audit"])
def audit_verify(c: Caller = Depends(require("auditor", "admin")), conn=Depends(connection)):
    result = audit_mod.verify()
    db.audit(conn, c.user_id, "audit.verify", None, {"ok": result.ok, "problems": len(result.problems)})
    return result.as_dict()
