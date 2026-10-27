"""Shared fixtures. Simulations are deterministic per seed, so they are built once per session."""

from __future__ import annotations

import pytest

from voltguard import config
from voltguard.data import simulator
from voltguard.detection import engine


@pytest.fixture(scope="session")
def cfg():
    return config.thresholds()


@pytest.fixture(scope="session")
def demo_sim():
    scn = simulator.demo_scenario()
    tables, truth = simulator.simulate(scn)
    return scn, tables, truth


@pytest.fixture(scope="session")
def demo_run(demo_sim, cfg):
    scn, tables, _ = demo_sim
    return engine.run_tables(tables, scn.start_date, scn.days, cfg)


@pytest.fixture(scope="session")
def demo_run_all(demo_sim, cfg):
    """Every zone scored, including unflagged ones (for checks on clean zones)."""
    scn, tables, _ = demo_sim
    return engine.run_tables(tables, scn.start_date, scn.days, cfg, score_all=True)


def case_premise(truth: dict, zone: str, kind: str, nth: int = 0) -> str:
    cases = [c for c in truth["zones"][zone]["cases"] if c["kind"] == kind]
    return cases[nth]["premise_id"]


def rank_of(run, zone: str, premise_id: str) -> int:
    return next(p.rank for p in run.zones[zone].premises if p.premise_id == premise_id)


def top_k(n: int) -> int:
    from voltguard.evaluation import top_k as k

    return k(n)


# --------------------------------------------------------------------------- database

@pytest.fixture(scope="session")
def pg(tmp_path_factory):
    """Migrated database; yields (owner_url, app_url). DATA_ROOT points at a session temp folder."""
    import os

    from tests.pg_server import TempPostgres
    from voltguard import db

    data_root = tmp_path_factory.mktemp("data_root")
    server = None
    if os.environ.get("TEST_DATABASE_URL"):
        owner = os.environ["TEST_DATABASE_URL"]
        app = os.environ.get("TEST_APP_DATABASE_URL", owner.replace("://voltguard", "://voltguard_app", 1))
    else:
        server = TempPostgres()
        server.start()
        owner, app = server.url("voltguard"), server.url("voltguard_app")
    saved = {k: os.environ.get(k) for k in ("ADMIN_DATABASE_URL", "DATABASE_URL", "DATA_ROOT")}
    os.environ.update({"ADMIN_DATABASE_URL": owner, "DATABASE_URL": app, "DATA_ROOT": str(data_root)})
    db.migrate(owner)
    yield owner, app
    db.close_pools()
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    if server:
        server.stop()


PASSWORD = "test-password-1"


@pytest.fixture(scope="session")
def api(pg):
    """API client over a database with the demo simulation loaded and detection run once."""
    import os
    import shutil

    from fastapi.testclient import TestClient

    from voltguard import config, db
    from voltguard.service import pipeline
    from voltguard.service.users import demo_users, seed_users

    os.environ["SCHEDULER"] = "off"
    repo_models = config.REPO_ROOT / ".data" / "models"
    if repo_models.exists():
        shutil.copytree(repo_models, config.data_root() / "models", dirs_exist_ok=True)
    with db.admin_connection() as conn:
        with conn.transaction():
            seed_users(conn, {u["user_id"]: PASSWORD for u in demo_users()})
    pipeline.run_detection("pipeline", progress=lambda m: None)
    from voltguard.service import seed

    seed.seed_demo_content(progress=lambda m: None)
    from voltguard.api.main import create_app

    with TestClient(create_app()) as client:
        yield client


def login(client, user: str) -> dict:
    response = client.post("/auth/token", json={"username": user, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
