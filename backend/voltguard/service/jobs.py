"""Background jobs with status (detection, case job, retrain, model loading).

One heavy job runs at a time (prompt 7.5): a single worker thread takes jobs in order, so a
second request waits as "queued" and the page shows the job's status instead of overloading
the laptop. Each job's progress, result and error are stored in `job_run`.
"""

from __future__ import annotations

import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from psycopg.types.json import Jsonb

from voltguard import db

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="voltguard-job")


def _update(job_id: int, **fields) -> None:
    sets = ", ".join(f"{k} = %s" for k in fields)
    values = [Jsonb(v) if k == "result" else v for k, v in fields.items()]
    with db.admin_connection() as conn:
        with conn.transaction():
            conn.execute(f"UPDATE job_run SET {sets} WHERE job_id = %s", (*values, job_id))


def _run(job_id: int, fn: Callable[[Callable[[str], None]], dict]) -> None:
    with db.admin_connection() as conn:
        with conn.transaction():
            conn.execute("UPDATE job_run SET status = 'running', started_at = now() WHERE job_id = %s", (job_id,))
    try:
        result = fn(lambda message: _update(job_id, progress=message[:500]))
        with db.admin_connection() as conn:
            with conn.transaction():
                conn.execute("UPDATE job_run SET status = 'done', finished_at = now(), result = %s WHERE job_id = %s",
                             (Jsonb(result or {}), job_id))
    except Exception as exc:  # the job's error is shown on the job status, never swallowed
        with db.admin_connection() as conn:
            with conn.transaction():
                conn.execute("UPDATE job_run SET status = 'failed', finished_at = now(), error = %s WHERE job_id = %s",
                             (f"{exc}\n{traceback.format_exc(limit=3)}"[:4000], job_id))


def submit(kind: str, started_by: str, fn: Callable[[Callable[[str], None]], dict], wait: bool = False) -> int:
    with db.admin_connection() as conn:
        with conn.transaction():
            job_id = conn.execute("INSERT INTO job_run (kind, started_by) VALUES (%s, %s) RETURNING job_id",
                                  (kind, started_by)).fetchone()["job_id"]
    future = _executor.submit(_run, job_id, fn)
    if wait:
        future.result()
    return job_id


def status(conn, job_id: int) -> dict | None:
    return conn.execute("SELECT job_id, kind, status, started_by, created_at, started_at, finished_at, progress, result, error "
                        "FROM job_run WHERE job_id = %s", (job_id,)).fetchone()


def running(conn) -> list[dict]:
    return conn.execute("SELECT job_id, kind, status, progress, created_at FROM job_run WHERE status IN ('queued', 'running') "
                        "ORDER BY job_id").fetchall()
