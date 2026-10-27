"""Database access: migrations, the owner connection (pipeline) and the API connection (RLS applies).

Every API transaction runs as voltguard_app with the caller's identity in `app.*` settings, so
PostgreSQL row-level security limits each query to the caller's region (FR-AD-01) even if an
API check were missed. The owner connection is used only for migrations, the pipeline, seeding
and scheduled jobs.
"""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from voltguard import config

SQL_DIR = Path(__file__).parent / "sql"
_pools: dict[str, ConnectionPool] = {}


@dataclass(frozen=True)
class Caller:
    """Identity an API request (or an agent acting for a user) carries into the database."""
    user_id: str
    role: str
    region: str
    team: str | None = None


SYSTEM = Caller("system", "pipeline", "*")


def _pool(url: str) -> ConnectionPool:
    pool = _pools.get(url)
    if pool is None:
        pool = ConnectionPool(url, min_size=1, max_size=int(os.environ.get("DB_POOL_SIZE", "8")), open=True,
                              kwargs={"row_factory": dict_row, "autocommit": False})
        _pools[url] = pool
    return pool


def close_pools() -> None:
    for pool in _pools.values():
        pool.close()
    _pools.clear()


@contextmanager
def admin_connection() -> Iterator[psycopg.Connection]:
    """Owner connection (bypasses row-level security): migrations, pipeline, seed, scheduler."""
    with _pool(config.admin_database_url()).connection() as conn:
        yield conn


@contextmanager
def app_connection(caller: Caller) -> Iterator[psycopg.Connection]:
    """API connection with the caller's identity; one transaction, committed on success."""
    with _pool(config.database_url()).connection() as conn:
        with conn.transaction():
            conn.execute(
                "SELECT set_config('app.user_id', %s, true), set_config('app.role', %s, true), "
                "set_config('app.region', %s, true), set_config('app.team', %s, true)",
                (caller.user_id, caller.role, caller.region, caller.team or ""),
            )
            yield conn


def audit(conn: psycopg.Connection, user_id: str, action: str, object_ref: str | None = None, detail: dict | None = None) -> int:
    """Append a hash-chained audit row (FR-AD-02, NFR-12) inside the caller's transaction."""
    row = conn.execute("SELECT vg_audit(%s, %s, %s, %s::jsonb) AS id",
                       (user_id, action, object_ref, Jsonb(detail) if detail is not None else None)).fetchone()
    return int(row["id"] if isinstance(row, dict) else row[0])


# --------------------------------------------------------------------------- migrations

def _role_password(name: str) -> str | None:
    return os.environ.get(name) or None


def migrate(url: str | None = None) -> list[str]:
    """Apply sql/*.sql in order (each once) and set the application roles' passwords."""
    applied = []
    with psycopg.connect(url or config.admin_database_url(), autocommit=True) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY, applied_at timestamptz DEFAULT now())")
        done = {r[0] for r in conn.execute("SELECT name FROM schema_migrations").fetchall()}
        for path in sorted(SQL_DIR.glob("*.sql")):
            # Files marked "-- always" are idempotent and re-applied on every migrate (views, functions, grants).
            text = path.read_text(encoding="utf-8")
            if path.name in done and not text.startswith("-- always"):
                continue
            with conn.transaction():
                conn.execute(text)
                conn.execute("INSERT INTO schema_migrations (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET applied_at = now()",
                             (path.name,))
            applied.append(path.name)
        for role, env in (("voltguard_app", "APP_DB_PASSWORD"), ("voltguard_powerbi", "POWERBI_DB_PASSWORD")):
            password = _role_password(env)
            if password:
                conn.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(sql.Identifier(role), sql.Literal(password)))
    return applied


def database_name(url: str) -> str:
    match = re.search(r"/([^/?]+)(\?|$)", url)
    return match.group(1) if match else "voltguard"
