"""Weekly manager summary: region-limited, zone-level, no personal details, PDF and message."""

from __future__ import annotations

import psycopg

from tests.conftest import login


def test_weekly_summary_is_zone_level_and_region_limited(api, pg):
    from tests.test_cases import fake_names

    cen = api.get("/weekly", headers=login(api, "manager.cen")).json()
    nor = api.get("/weekly", headers=login(api, "manager.nor")).json()
    assert cen["region"] == "CEN" and cen["kpis"]["flagged_zones"] >= 2 and cen["kpis"]["unexplained_kwh_per_day"] > 0
    assert all(z["transformer_id"].startswith("TX-CEN") for z in cen["top_zones"])
    assert all(z["transformer_id"].startswith("TX-NOR") for z in nor["top_zones"])
    assert len(cen["daily_gap"]) == 14 and cen["kpis"]["value_at_risk"].startswith("[TNB")
    text = str(cen)
    assert "P-CEN" not in text and not any(n in text for n in fake_names(pg[0]))
    for user in ("analyst.cen", "inspector.b", "auditor"):
        assert api.get("/weekly", headers=login(api, user)).status_code == 403


def test_FR_AD_01_training_labels_and_hit_rates_are_region_limited(api, pg):
    """The training_label view once ran as its owner, so each region's hit rate counted every region's labels."""
    from voltguard import db
    from voltguard.db import Caller

    with psycopg.connect(pg[0]) as conn:
        everyone = conn.execute("SELECT region, count(*) FROM training_label GROUP BY region").fetchall()
    assert {r for r, _ in everyone} >= {"CEN", "NOR"}
    for user, region in (("manager.cen", "CEN"), ("manager.nor", "NOR")):
        with db.app_connection(Caller(user, "manager", region, None)) as conn:
            regions = {r["region"] for r in conn.execute("SELECT DISTINCT region FROM training_label").fetchall()}
        assert regions == {region}
        hits = api.get("/weekly", headers=login(api, user)).json()["hit_rates"]
        labelled = sum(h["inspections"] for h in hits.values())
        assert labelled == dict(everyone)[region]


def test_weekly_summary_pdf_and_message(api):
    manager = login(api, "manager.cen")
    pdf = api.get("/weekly/pdf", headers=manager)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    assert "VG-WK-CEN-" in pdf.headers["content-disposition"]
    sent = api.post("/weekly/send", headers=manager).json()
    assert sent["text"].startswith("VoltGuard Weekly summary:") and "flagged zone" in sent["text"] and "/#/weekly" in sent["text"]
    assert sent["document"].startswith("VG-WK-CEN-")          # weekly.send_pdf = 1: the checked PDF goes with it
    chats = api.get("/telegram/chats", headers=manager).json()
    assert any(m["kind"] == "weekly" and not m["buttons"] for m in chats)


def test_weekly_report_page_explains_itself_in_both_languages(api, pg):
    from tests.test_cases import fake_names
    from tests.test_digest_render import HEADINGS

    manager = login(api, "manager.cen")
    figures = api.get("/weekly", headers=manager).json()
    assert figures["report_id"].startswith("VG-WK-CEN-") and figures["data_mode"]["simulated"]
    assert all(z["threshold_kwh"] >= 15 and z["margin_kwh"] >= 0 for z in figures["zones"])
    assert "model_ranked" in figures["hit_rates"] and figures["hit_rates"]["model_ranked"]["ci_low_pct"] is not None
    for lang in ("en", "ms"):
        page = api.get(f"/weekly/html?lang={lang}", headers=manager)
        assert page.status_code == 200 and page.headers["content-type"].startswith("text/html")
        for heading in HEADINGS[lang]:
            assert heading in page.text, (lang, heading)
        assert "P-CEN-" not in page.text and not any(n in page.text for n in fake_names(pg[0]))
    assert api.get("/weekly/html?lang=fr", headers=manager).status_code == 422
    assert api.get("/weekly/html", headers=login(api, "analyst.cen")).status_code == 403


def test_weekly_job_reaches_every_manager_and_supervisor(api):
    from voltguard.service import digest

    sent = digest.send_weekly()
    assert len(sent) >= 4 and all("flagged zone" in s["text"] for s in sent)
