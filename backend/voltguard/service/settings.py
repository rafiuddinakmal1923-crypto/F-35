"""Thresholds and weights (FR-AD-03): config/thresholds.yaml, tuned weights, then admin overrides in `setting`."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from voltguard import config

KEY = "thresholds"
EDITABLE = {
    "zone": {"share_of_supply", "min_gap_kwh_per_day", "consecutive_days", "large_load_share", "flat_cv"},
    "weights": None,          # every weight
    "penalties": None,
    "tenancy": {"max_contribution", "gate_other_evidence"},
    "cases": {"case_threshold", "max_cases_per_zone", "random_sample_per_zone"},
    "dispatch": {"reminder_hours", "escalation_hours", "demo_reminder_minutes", "demo_escalation_minutes"},
    "monitoring": {"min_interval_completeness", "drift_psi_alert"},
}


def overrides(conn: psycopg.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT value FROM setting WHERE key = %s", (KEY,)).fetchone()
    if not row:
        return {}
    return row["value"] if isinstance(row, dict) else row[0]


def thresholds(conn: psycopg.Connection) -> dict[str, Any]:
    return config.thresholds(overrides(conn))


def validate_change(change: dict[str, Any]) -> dict[str, Any]:
    """Only known numeric settings may change; weights must stay between 0 and 1."""
    clean: dict[str, Any] = {}
    base = config.thresholds()
    for section, values in change.items():
        if section not in EDITABLE or not isinstance(values, dict):
            raise ValueError(f"'{section}' cannot be changed here")
        allowed = EDITABLE[section] or set(base.get(section, {}))
        for key, value in values.items():
            if key not in allowed:
                raise ValueError(f"'{section}.{key}' cannot be changed here")
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                raise ValueError(f"'{section}.{key}' must be a non-negative number")
            if section in ("weights", "penalties", "tenancy") and value > 1:
                raise ValueError(f"'{section}.{key}' must be between 0 and 1")
            clean.setdefault(section, {})[key] = value
    return clean


def save(conn: psycopg.Connection, change: dict[str, Any], user_id: str) -> dict[str, Any]:
    merged = config.deep_merge(overrides(conn), validate_change(change))
    conn.execute("INSERT INTO setting (key, value, changed_by) VALUES (%s, %s, %s) "
                 "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, changed_by = EXCLUDED.changed_by, changed_at = now()",
                 (KEY, Jsonb(merged), user_id))
    return merged
