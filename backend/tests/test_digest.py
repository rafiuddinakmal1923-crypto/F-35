"""Weekly manager summary: region-limited, zone-level, no personal details, PDF and message."""

from __future__ import annotations

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


def test_weekly_summary_pdf_and_message(api):
    manager = login(api, "manager.cen")
    pdf = api.get("/weekly/pdf", headers=manager)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    sent = api.post("/weekly/send", headers=manager).json()
    assert sent["text"].startswith("VoltGuard Weekly summary:") and "flagged zone" in sent["text"] and "/#/weekly" in sent["text"]
    chats = api.get("/telegram/chats", headers=manager).json()
    assert any(m["kind"] == "weekly" and not m["buttons"] for m in chats)


def test_weekly_job_reaches_every_manager_and_supervisor(api):
    from voltguard.service import digest

    sent = digest.send_weekly()
    assert len(sent) >= 4 and all("flagged zone" in s["text"] for s in sent)
