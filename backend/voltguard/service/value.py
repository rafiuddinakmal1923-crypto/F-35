"""Value at risk per flagged zone (UI brief 3.1): an estimate in kWh and, once a tariff is set, in RM.

    excess gap (kWh/day) = max(recent gap - uncertainty margin u, 0)     flagged zones only
    kWh per month        = excess gap x 30
    RM per month         = kWh per month x tariff (config/tariffs.yaml, RM/kWh)

Only the gap above the uncertainty margin counts, so meter, estimate and loss-model error are not
billed as theft. With no tariff in config/tariffs.yaml the RM figure stays empty and the page shows
the placeholder "[TNB domestic tariff: to confirm]"; a number is never guessed. The weekly report
(service/digest.py) reads the same file, so both always use the same tariff.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from voltguard import config
from voltguard.service.digest import tariff

DAYS_PER_MONTH = 30
PLACEHOLDER = "[TNB domestic tariff: to confirm]"
_HEADER = """# Tariff used for value-at-risk estimates (RM = excess kWh x tariff): the weekly report, the
# Overview and Zone pages, and the rpt_zone_latest view. Leave rm_per_kwh empty until TNB supplies
# the figure: the pages then show "[TNB domestic tariff: to confirm]" and no RM amount.
# Never fill in a guessed number. Admins can set it in Settings (logged).
"""


def excess_kwh_per_day(zone: dict[str, Any]) -> float | None:
    """Gap above the uncertainty margin for a flagged zone with a balance; None otherwise."""
    if not zone.get("flagged") or not zone.get("balance_available") or zone.get("gap_kwh_recent") is None:
        return None
    return max(float(zone["gap_kwh_recent"]) - float(zone.get("uncertainty_kwh_recent") or 0.0), 0.0)


def zone_value(zone: dict[str, Any], rate: float | None) -> dict[str, Any] | None:
    excess = excess_kwh_per_day(zone)
    if excess is None:
        return None
    kwh_month = excess * DAYS_PER_MONTH
    return {"excess_kwh_per_day": round(excess, 1), "kwh_per_month": round(kwh_month),
            "rm_per_month": round(kwh_month * rate) if rate else None, "estimate": True}


def totals(values: list[dict | None], rate: float | None) -> dict[str, Any]:
    present = [v for v in values if v]
    kwh = sum(v["kwh_per_month"] for v in present)
    return {"zones": len(present), "kwh_per_month": round(kwh), "rm_per_month": round(kwh * rate) if rate and present else None,
            "estimate": True}


def tariff_info() -> dict[str, Any]:
    rate = tariff()
    return {"rm_per_kwh": rate["rm_per_kwh"], "source": rate["source"], "placeholder": PLACEHOLDER,
            "days_per_month": DAYS_PER_MONTH, "file": "config/tariffs.yaml"}


def write_tariff(rm_per_kwh: float | None, source: str | None) -> dict[str, Any]:
    """Admin change from Settings: rewrite config/tariffs.yaml (empty value = back to the placeholder)."""
    if rm_per_kwh is not None and not (0 < rm_per_kwh < 10):
        raise ValueError("The tariff must be between 0 and 10 RM per kWh, or empty")
    source = (source or "").strip().replace("\n", " ")[:200]
    value = "" if rm_per_kwh is None else f"{rm_per_kwh:g}"
    text = _HEADER + f"rm_per_kwh: {value}\nsource: {_yaml_str(source)}\n"
    (config.config_dir() / "tariffs.yaml").write_text(text, encoding="utf-8")
    config.load_yaml.cache_clear()          # YAML files are cached; the next read sees the new value
    return tariff_info()


def _yaml_str(text: str) -> str:
    return "" if not text else '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def sync_setting(conn: psycopg.Connection) -> None:
    """Copy the file's tariff into `setting` so the rpt_ views (Power BI) can use it (owner connection)."""
    rate = tariff()
    conn.execute("INSERT INTO setting (key, value, changed_by) VALUES ('tariff', %s, 'config') "
                 "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, changed_at = now()",
                 (Jsonb({"rm_per_kwh": rate["rm_per_kwh"], "source": rate["source"]}),))
