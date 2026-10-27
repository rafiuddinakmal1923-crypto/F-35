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
