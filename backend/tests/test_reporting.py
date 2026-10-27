"""Manager dashboard data (SRS FR-UI-01, NFR-07, SDD 9.2): zone-level pseudonymised rpt_ views only."""

from __future__ import annotations

import psycopg
import pytest

from voltguard.cli import main
from voltguard.service.commands import REPORT_VIEWS


def test_FR_UI_01_powerbi_role_reads_rpt_views_only(api, pg):
    owner, app = pg
    bi = app.replace("voltguard_app", "voltguard_powerbi")
    with psycopg.connect(bi) as conn:
        for view in REPORT_VIEWS:
            conn.execute(f"SELECT * FROM {view} LIMIT 1")
        latest = conn.execute("SELECT zone, region FROM rpt_zone_latest").fetchall()
        assert {r[1] for r in latest} == {"CEN", "NOR"}           # R0: one read-only account, all regions, zone level
    for table in ("premise", "premise_score", "customer_pii", "inspection_case", "zone_run", "meter_reading", "audit_log"):
        with psycopg.connect(bi) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
    with psycopg.connect(app) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute("SELECT 1 FROM rpt_zone_latest")              # the API role cannot bypass RLS through the views


def test_NFR_07_rpt_views_hold_no_premise_ids_or_personal_details(api, pg, tmp_path):
    with psycopg.connect(pg[0]) as conn:
        columns = {r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name LIKE 'rpt\\_%'").fetchall()}
        names = [r[0].replace("FAKE ", "") for r in conn.execute("SELECT holder_name FROM customer_pii").fetchall()]
    assert not columns & {"premise_id", "lat", "lon", "holder_name", "address", "contact", "meter_id", "notes", "notes_redacted"}
    assert main(["snapshot", "--out", str(tmp_path)]) == 0
    text = "".join(p.read_text(encoding="utf-8") for p in tmp_path.glob("*.csv"))
    assert "P-CEN-" not in text and "P-NOR-" not in text and "MTR-" not in text
    assert not any(name in text for name in names)
    assert "TX-CEN-001" in (tmp_path / "rpt_zone_latest.csv").read_text(encoding="utf-8")
