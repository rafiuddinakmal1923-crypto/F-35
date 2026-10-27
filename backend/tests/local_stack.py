"""A complete local stack without Docker, for browser tests and demo rehearsal on Linux.

    python -m tests.local_stack          # from backend/: runs until Ctrl+C

Starts a throwaway PostgreSQL, migrates, seeds the test accounts (password from
VG_STACK_PASSWORD, default "demo-pass-1"), runs detection, serves the API on :8000 and the
built web app (`npm run build` first) with an /api proxy on :4173.
"""

from __future__ import annotations

import atexit
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PASSWORD = os.environ.get("VG_STACK_PASSWORD", "demo-pass-1")


def chromium_path() -> str | None:
    """Pre-installed Chromium when the Playwright package's own browser is not installed."""
    for candidate in ("/opt/pw-browsers/chromium-1243/chrome-linux64/chrome",):
        if Path(candidate).exists():
            return candidate
    found = sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux64/chrome")) if Path("/opt/pw-browsers").exists() else []
    return str(found[-1]) if found else None


class LocalStack:
    def __init__(self, api_port: int = 8000, web_port: int = 4173, with_cases: bool = False):
        self.api_port, self.web_port, self.with_cases = api_port, web_port, with_cases
        self.pg = None
        self.web = None
        self.server = None

    def start(self) -> "LocalStack":
        from tests.pg_server import TempPostgres

        self.pg = TempPostgres()
        self.pg.start()
        data_root = Path(self.pg.dir) / "data_root"
        data_root.mkdir()
        os.environ.update({"ADMIN_DATABASE_URL": self.pg.url("voltguard"), "DATABASE_URL": self.pg.url("voltguard_app"),
                           "DATA_ROOT": str(data_root), "SCHEDULER": os.environ.get("SCHEDULER", "on"), "LLM_MODE": "mock",
                           "REPORT_MODE": os.environ.get("REPORT_MODE", "mock"), "PUBLIC_BASE_URL": f"http://localhost:{self.web_port}"})
        models = ROOT / ".data" / "models"
        if models.exists():
            shutil.copytree(models, data_root / "models")
        from voltguard import db
        from voltguard.service import pipeline
        from voltguard.service.users import demo_users, seed_users

        db.migrate()
        with db.admin_connection() as conn:
            with conn.transaction():
                seed_users(conn, {u["user_id"]: PASSWORD for u in demo_users()})
        try:
            from voltguard.service import seed

            seed.seed_demo_content(progress=lambda m: None)
        except ImportError:
            pass
        pipeline.run_detection("pipeline", progress=lambda m: None)
        if self.with_cases:
            from voltguard.db import Caller
            from voltguard.service import cases

            with db.app_connection(Caller("pipeline", "pipeline", "*")) as conn:
                cases.create_cases_job(conn, Caller("pipeline", "pipeline", "*"))

        import uvicorn

        from voltguard.api.main import create_app

        config = uvicorn.Config(create_app(), host="127.0.0.1", port=self.api_port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        while not self.server.started:
            time.sleep(0.1)
        if not (ROOT / "web" / "dist" / "index.html").exists():
            subprocess.run(["npm", "run", "build"], cwd=ROOT / "web", check=True)
        self.web = subprocess.Popen(["npx", "vite", "preview", "--port", str(self.web_port), "--strictPort"], cwd=ROOT / "web",
                                    env={**os.environ, "VG_API": f"http://127.0.0.1:{self.api_port}"},
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        atexit.register(self.stop)
        import httpx

        for _ in range(100):
            try:
                if httpx.get(f"http://127.0.0.1:{self.web_port}/api/health", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        return self

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.web_port}"

    def stop(self) -> None:
        if self.web and self.web.poll() is None:
            try:
                os.killpg(self.web.pid, signal.SIGTERM)   # npx -> sh -> node: stop the whole group
            except ProcessLookupError:
                pass
        if self.server:
            self.server.should_exit = True
            self.thread.join(timeout=10)      # lifespan shutdown stops the scheduler before the database goes
            self.server = None
        from voltguard import db

        db.close_pools()
        if self.pg:
            self.pg.stop()
            self.pg = None


if __name__ == "__main__":
    stack = LocalStack(with_cases="--cases" in sys.argv).start()
    print(f"Web: {stack.url}   API: http://127.0.0.1:{stack.api_port}/docs   password for every test account: {PASSWORD}")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        stack.stop()
