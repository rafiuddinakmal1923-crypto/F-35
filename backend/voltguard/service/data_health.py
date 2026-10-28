"""Data health per table for the Data manager (UI brief 3.9): how the data was prepared.

Per table: rows in the database, the active source, and what the upload checks did to it
(exact duplicates removed, timestamps given or converted to Malaysia time). Readings also show
completeness per meter-day. The fallbacks of SRS AS-2, 3, 7, 8 and 9 that the latest run used are
listed with the reason. Simulated sources are generated in the canonical form, so they had
nothing to remove or convert; the card says so instead of showing a zero.
"""

from __future__ import annotations

import json
from typing import Any

import psycopg

from voltguard.data import sources

TABLES = ("meter_reading", "meter_monthly_reading", "transformer_reading", "meter", "premise", "transformer", "account_event",
          "district_weather", "duty_roster", "inspection_outcome")


def _upload_checks(source: str) -> dict[str, dict[str, int]] | None:
    """Issue counts by table and check from the active upload's validation report."""
    try:
        folder = sources.resolve_upload(source)
    except Exception:  # noqa: BLE001 - a missing or broken version shows as "no report"
        return None
    path = folder / "validation.json"
    if not path.exists():
        return None
    report = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, int]] = {}
    for issue in report.get("issues", []):
        per = out.setdefault(issue.get("table") or "", {})
        per[issue.get("check")] = per.get(issue.get("check"), 0) + int(issue.get("count") or 0)
    return out


def fallbacks(conn: psycopg.Connection, simulated_voltage: bool) -> list[dict[str, Any]]:
    """SRS assumptions whose fallback the latest detection run used."""
    zones = conn.execute("SELECT transformer_id, balance_available, loss_method, voltage->>'method' AS vmethod, "
                         "voltage->>'confidence' AS vconf FROM zone_run WHERE run_date = (SELECT max(run_date) FROM zone_run)").fetchall()
    solar = conn.execute("SELECT count(*) AS n FROM account_event WHERE event_type = 'solar_registration'").fetchone()["n"]
    out = []
    no_dtm = [z["transformer_id"] for z in zones if not z["balance_available"]]
    if no_dtm:
        out.append({"code": "AS-2", "zones": no_dtm})
    if simulated_voltage:
        out.append({"code": "AS-3", "simulated": True, "zones": []})
    else:
        no_v = [z["transformer_id"] for z in zones if z["vmethod"] in (None, "none")]
        if no_v:
            out.append({"code": "AS-3", "simulated": False, "zones": no_v})
    low = [z["transformer_id"] for z in zones if z["vconf"] == "low"]
    if low:
        out.append({"code": "AS-7", "zones": low})
    similar = [z["transformer_id"] for z in zones if z["loss_method"] == "similar_zones"]
    if similar:
        out.append({"code": "AS-8", "zones": similar})
    if not solar:
        out.append({"code": "AS-9", "zones": []})
    return out


def health(conn: psycopg.Connection) -> dict[str, Any]:
    """Owner connection (counts every region's rows; returns counts only)."""
    active = sources.active_sources()
    cards = []
    for table in TABLES:
        rows = conn.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"]  # noqa: S608 - fixed table names
        source = active.get(table, "simulated")
        checks = _upload_checks(source) if source.startswith("upload:") else None
        per = (checks or {}).get(table, {})
        cards.append({"table": table, "rows": rows, "source": source, "upload_report": checks is not None,
                      "duplicates_removed": per.get("duplicates") if checks is not None else None,
                      "timezone_fixes": per.get("timezone") if checks is not None else None,
                      "warnings": sum(per.values()) if checks is not None else None})
    # Completeness per meter-day: share of smart-meter days with at least 90% of their half-hours.
    days = conn.execute("SELECT count(DISTINCT date) AS n FROM zone_daily_balance").fetchone()["n"]
    smart = conn.execute("SELECT count(*) AS n FROM meter WHERE meter_type = 'smart'").fetchone()["n"]
    short = conn.execute("SELECT count(*) AS n, avg(completeness) AS avg FROM data_quality_flag "
                         "WHERE run_date = (SELECT max(run_date) FROM data_quality_flag)").fetchone()
    meter_days = smart * days
    completeness = {"meter_days": meter_days, "short_meter_days": short["n"],
                    "complete_share": round(1 - short["n"] / meter_days, 4) if meter_days else None,
                    "threshold": 0.9}
    simulated_voltage = active.get("meter_reading", "simulated") == "simulated"
    return {"tables": cards, "completeness": completeness, "fallbacks": fallbacks(conn, simulated_voltage),
            "data_mode": "simulated" if all(v == "simulated" for v in active.values()) else "upload"}
