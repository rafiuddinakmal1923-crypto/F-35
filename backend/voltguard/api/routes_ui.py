"""Endpoints for the UI upgrade (VoltGuard_UI_Upgrade_Prompt.md): top-bar status, tariff, validation,
back-test replay, data health and the demo-only guide, role cards and reset.

Privacy and role rules are unchanged: validation and back-test results are simulation files, region
limited, and premise IDs in the replay go only to roles that already see ranked suspects.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from voltguard import auth, config, db
from voltguard.api.deps import ApiError, bad_request, caller, connection, forbidden, not_found, require
from voltguard.data import sources
from voltguard.db import Caller
from voltguard.service import data_health, demo_guide, jobs, learning, value

router = APIRouter(tags=["ui"])
REPORTS = config.REPO_ROOT / "reports"
SUMMARY_FILE = "simulation_summary.json"
REPLAY_FILE = "backtest_replay.json"
ANONYMOUS = Caller("anonymous", "anonymous", "")
SUSPECT_ROLES = {"analyst", "supervisor", "data_scientist"}


def _demo_only() -> None:
    if not config.demo_ui():
        raise not_found("Demo features are off (DEMO_MODE)")


def _read_report(name: str) -> dict[str, Any] | None:
    path = REPORTS / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- top bar

@router.get("/meta")
def meta(c: Caller = Depends(caller), conn=Depends(connection)):
    """Region, latest run date, data mode (simulated or upload) and demo switch for the top bar."""
    run_date = None
    if c.role in ("manager", "analyst", "supervisor", "data_scientist", "admin", "auditor"):
        row = conn.execute("SELECT max(run_date) AS d FROM zone_run").fetchone()
        run_date = row["d"] if row else None
    active = sources.active_sources()
    regions = {r["code"]: r["name"] for r in config.demo_config().get("regions", [])}
    return {"region": c.region, "region_name": regions.get(c.region), "run_date": run_date,
            "data_mode": "simulated" if all(v == "simulated" for v in active.values()) else "upload",
            "llm_mode": config.llm_mode(), "demo": config.demo_ui()}


# --------------------------------------------------------------------------- tariff (3.1)

class Tariff(BaseModel):
    rm_per_kwh: float | None = None
    source: str | None = None


@router.get("/settings/tariff", tags=["settings"])
def get_tariff(c: Caller = Depends(require("manager", "analyst", "supervisor", "admin", "data_scientist"))):
    return value.tariff_info()


@router.put("/settings/tariff", tags=["settings"])
def put_tariff(body: Tariff, c: Caller = Depends(require("admin")), conn=Depends(connection)):
    try:
        info = value.write_tariff(body.rm_per_kwh, body.source)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    except OSError as exc:
        raise ApiError(status.HTTP_409_CONFLICT, "read_only", f"config/tariffs.yaml cannot be written here: {exc}") from exc
    value.sync_setting(conn)
    db.audit(conn, c.user_id, "settings.change", "setting:tariff", {"rm_per_kwh": body.rm_per_kwh, "source": info["source"]})
    return info


# --------------------------------------------------------------------------- validation (3.6)

@router.get("/validation/summary", tags=["validation"])
def validation_summary(c: Caller = Depends(require("manager", "analyst", "data_scientist")), conn=Depends(connection)):
    """Held-out results and sweeps from reports/simulation_summary.json, hit rates per model version
    from the database. Missing results are null ("not run yet"), never a placeholder number."""
    summary = _read_report(SUMMARY_FILE)
    versions = []
    for v in learning.versions(conn):
        h = (v.get("metrics") or {}).get("hit_rates") or {}
        versions.append({"version_id": v["version_id"], "trained_at": v["trained_at"], "active": v.get("active"),
                         "model_ranked": h.get("model_ranked"), "random_sample": h.get("random_sample")})
    return {"simulation": summary, "file": f"reports/{SUMMARY_FILE}", "model_versions": versions}


# --------------------------------------------------------------------------- back-test replay (3.7)

def _replay() -> dict[str, Any]:
    data = _read_report(REPLAY_FILE)
    if data is None:
        raise not_found("No back-test replay yet: run scripts/backtest.py --replay")
    return data


def _zone_allowed(c: Caller, zone: dict) -> bool:
    return c.region == "*" or zone.get("region") == c.region


@router.get("/backtest", tags=["validation"])
def backtest_zones(c: Caller = Depends(require("manager", "analyst", "supervisor", "data_scientist"))):
    data = _read_report(REPLAY_FILE)
    if data is None:
        return {"zones": [], "generated": None}
    zones = [{"zone": z["zone"], "region": z["region"], "known_cases": len(z["known_cases"]),
              "detected": sum(k["first_top5_day"] is not None for k in z["known_cases"])}
             for z in data["zones"].values() if _zone_allowed(c, z)]
    return {"zones": zones, "generated": data["generated"], "source": data["source"], "step_days": data["step_days"]}


@router.get("/backtest/{zone}", tags=["validation"])
def backtest_zone(zone: str, c: Caller = Depends(require("manager", "analyst", "supervisor", "data_scientist"))):
    data = _replay()
    z = data["zones"].get(zone)
    if not z or not _zone_allowed(c, z):
        raise not_found("No back-test for this zone in your region")
    out = {**z, "generated": data["generated"], "source": data["source"], "step_days": data["step_days"]}
    if c.role not in SUSPECT_ROLES:
        # Managers see zone-level figures only (SRS 2.2): no premise IDs, only when detection happened.
        out["known_cases"] = [{k: v for k, v in kc.items() if k != "premise_id"} for kc in z["known_cases"]]
        out["frames"] = [{k: v for k, v in f.items() if k != "top"} for f in z["frames"]]
        out["premise_ids_hidden"] = True
    return out


# --------------------------------------------------------------------------- data health (3.9)

@router.get("/admin/data-health", tags=["data manager"])
def get_data_health(c: Caller = Depends(require("admin"))):
    with db.admin_connection() as conn:
        return data_health.health(conn)


# --------------------------------------------------------------------------- demo mode (2.6, 3.8)

class DemoSignIn(BaseModel):
    username: str


@router.get("/demo/accounts", tags=["demo"])
def demo_accounts():
    """Test accounts for the sign-in page's role cards (DEMO_MODE only; no passwords)."""
    _demo_only()
    return {"accounts": demo_guide.accounts()}


@router.post("/auth/demo-token", tags=["demo"])
def demo_token(body: DemoSignIn):
    """One-click sign-in as a test account (DEMO_MODE only, simulated data and fake details only)."""
    _demo_only()
    username = body.username.strip().lower()
    if username not in {a["user_id"] for a in demo_guide.accounts()}:
        raise forbidden("Only the demo test accounts can sign in this way")
    with db.app_connection(ANONYMOUS) as conn:
        user = conn.execute("SELECT * FROM vg_user_auth(%s)", (username,)).fetchone()
        if not user or not user["active"]:
            raise ApiError(status.HTTP_401_UNAUTHORIZED, "bad_credentials", "This test account is not set up")
        token, expires = auth.issue_token(user)
        db.audit(conn, username, "auth.sign_in", None, {"role": user["role"], "via": "demo_role_card"})
    return {"access_token": token, "token_type": "bearer", "expires_at": expires,
            "user": {k: user[k] for k in ("user_id", "role", "region", "team")}}


@router.get("/demo/status", tags=["demo"])
def demo_status(c: Caller = Depends(caller)):
    _demo_only()
    with db.admin_connection() as conn:
        return demo_guide.status(conn, c.role)


@router.post("/admin/demo/reset", tags=["demo"])
def demo_reset(wait: bool = False, c: Caller = Depends(require("admin"))):
    _demo_only()
    job_id = jobs.submit("demo_reset", c.user_id, lambda progress: demo_guide.reset(c.user_id, progress), wait=False)
    if wait:
        import time

        with db.admin_connection() as conn:
            while jobs.status(conn, job_id)["status"] in ("queued", "running"):
                time.sleep(0.5)
    return {"job_id": job_id}
