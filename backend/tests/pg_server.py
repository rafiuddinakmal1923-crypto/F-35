"""A throwaway PostgreSQL for database tests.

Uses TEST_DATABASE_URL (owner connection to an empty database) when set; otherwise starts a
temporary cluster from local PostgreSQL 16 binaries (as the `postgres` user when running as root).
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

BIN_DIRS = ["/usr/lib/postgresql/16/bin", "/usr/lib/postgresql/17/bin", "/usr/local/pgsql/bin"]


def _bin(name: str) -> str | None:
    for folder in BIN_DIRS:
        path = Path(folder) / name
        if path.exists():
            return str(path)
    return shutil.which(name)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TempPostgres:
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="vg-pg-"))
        self.port = _free_port()
        self.as_postgres = os.geteuid() == 0

    def _run(self, args: list[str]) -> None:
        if self.as_postgres:
            subprocess.run(["su", "postgres", "-s", "/bin/sh", "-c", " ".join(f"'{a}'" for a in args)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        else:
            subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def start(self) -> str:
        initdb, pg_ctl = _bin("initdb"), _bin("pg_ctl")
        if not initdb or not pg_ctl:
            raise RuntimeError("PostgreSQL binaries not found; set TEST_DATABASE_URL")
        if self.as_postgres:
            shutil.chown(self.dir, "postgres")
        self._run([initdb, "-D", str(self.dir / "data"), "-A", "trust", "-U", "voltguard", "-E", "UTF8", "--no-locale"])
        self._run([pg_ctl, "-D", str(self.dir / "data"), "-l", str(self.dir / "log"), "-w", "-o",
                   f"-p {self.port} -k {self.dir} -c listen_addresses='' -c fsync=off -c synchronous_commit=off", "start"])
        for _ in range(50):
            if (self.dir / f".s.PGSQL.{self.port}").exists():
                break
            time.sleep(0.1)
        subprocess.run([_bin("psql") or "psql", "-h", str(self.dir), "-p", str(self.port), "-U", "voltguard", "-d", "postgres",
                        "-c", "CREATE DATABASE voltguard"], check=True, stdout=subprocess.DEVNULL)
        return self.url("voltguard")

    def url(self, user: str) -> str:
        return f"postgresql://{user}@/voltguard?host={self.dir}&port={self.port}"

    def stop(self) -> None:
        try:
            self._run([_bin("pg_ctl"), "-D", str(self.dir / "data"), "-m", "immediate", "stop"])
        finally:
            shutil.rmtree(self.dir, ignore_errors=True)
