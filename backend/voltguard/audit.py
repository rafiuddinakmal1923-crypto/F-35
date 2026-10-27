"""Tamper-evident audit log (FR-AD-02, NFR-12).

Rows are appended only by the database function vg_audit(), which stores each row's hash and
the previous row's. `verify` recomputes the chain here, independently of the database, and
compares it with the daily anchors: the latest hash copied to DATA_ROOT/audit_anchor/ outside
the database (write-once files). An edited row breaks its own hash; a deleted row breaks the
link; a rewritten chain no longer matches an anchor.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from voltguard import config, db

GENESIS = "0" * 64


def row_text(prev: str, log_id: int, ts: datetime, user_id: str, action: str, object_ref: str | None, detail_text: str | None) -> str:
    """Same canonical text as the SQL function vg_audit_text()."""
    stamp = ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return "|".join([prev, str(log_id), stamp, user_id, action, object_ref or "", detail_text or ""])


def row_hash(*args) -> str:
    return hashlib.sha256(row_text(*args).encode("utf-8")).hexdigest()


def anchor_dir() -> Path:
    path = config.data_root() / "audit_anchor"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class VerifyResult:
    ok: bool
    rows: int
    problems: list[dict] = field(default_factory=list)
    anchors_checked: int = 0

    def as_dict(self) -> dict:
        return {"ok": self.ok, "rows": self.rows, "anchors_checked": self.anchors_checked, "problems": self.problems[:50]}


def verify() -> VerifyResult:
    problems: list[dict] = []
    prev = GENESIS
    hashes: dict[int, str] = {}
    rows = 0
    with db.admin_connection() as conn:
        cur = conn.execute("SELECT log_id, ts, user_id, action, object_ref, detail::text AS detail_text, prev_hash, row_hash "
                           "FROM audit_log ORDER BY log_id")
        for r in cur:
            rows += 1
            if r["prev_hash"] != prev:
                problems.append({"log_id": r["log_id"], "problem": "chain broken: previous hash does not match (row deleted or reordered)"})
            expected = row_hash(r["prev_hash"], r["log_id"], r["ts"], r["user_id"], r["action"], r["object_ref"], r["detail_text"])
            if expected != r["row_hash"]:
                problems.append({"log_id": r["log_id"], "problem": "row edited: content does not match its hash"})
            hashes[r["log_id"]] = r["row_hash"]
            prev = r["row_hash"]
    anchors = sorted(anchor_dir().glob("anchor-*.json"))
    for path in anchors:
        anchor = json.loads(path.read_text(encoding="utf-8"))
        if hashes.get(anchor["log_id"]) != anchor["row_hash"]:
            problems.append({"log_id": anchor["log_id"], "problem": f"does not match the anchor {path.name}: chain rewritten"})
    return VerifyResult(not problems, rows, problems, len(anchors))


def write_anchor(today: str | None = None) -> Path | None:
    """Copy the latest hash outside the database (daily job). Existing anchors are never overwritten."""
    with db.admin_connection() as conn:
        last = conn.execute("SELECT log_id, ts, row_hash FROM audit_log ORDER BY log_id DESC LIMIT 1").fetchone()
    if not last:
        return None
    today = today or datetime.now().date().isoformat()
    path = anchor_dir() / f"anchor-{today}.json"
    if path.exists():
        return path
    path.write_text(json.dumps({"log_id": last["log_id"], "row_hash": last["row_hash"], "ts": last["ts"].isoformat(),
                                "written_at": datetime.now().astimezone().isoformat(timespec="seconds")}), encoding="utf-8")
    os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)   # write-once on the file system
    return path
