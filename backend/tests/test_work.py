"""Role home pages ("my work") and the overview trend: each role sees its own next actions, in its region."""

from __future__ import annotations

from tests.conftest import login
from tests.test_cases import case_job  # noqa: F401  (fixture)


def test_my_work_lists_the_next_actions_per_role(api, case_job):
    sup = api.get("/work", headers=login(api, "supervisor.cen")).json()
    sections = {s["key"]: s for s in sup["sections"]}
    assert {"suggestions", "overdue", "unassigned", "teams"} <= set(sections)
    assert all(i["link"].startswith("/cases/C-") for i in sections["suggestions"]["items"])
    assert all("T-NOR" not in i["title"] for i in sections["teams"]["items"])
    ana = api.get("/work", headers=login(api, "analyst.cen")).json()
    assert {s["key"] for s in ana["sections"]} == {"reports", "unclaimed", "mine"}
    assert all("P-CEN" in i["detail"] for i in next(s for s in ana["sections"] if s["key"] == "unclaimed")["items"])
    mgr = api.get("/work", headers=login(api, "manager.cen")).json()
    assert {s["key"] for s in mgr["sections"]} == {"exports", "alerts"}
    for user in ("inspector.b", "auditor", "datasci"):
        assert api.get("/work", headers=login(api, user)).status_code == 403


def test_FR_UI_01_overview_trend_is_zone_level(api):
    z = api.get("/zones", headers=login(api, "manager.cen")).json()
    assert len(z["trend"]) == 14 and all(set(p) == {"date", "gap_kwh", "flagged"} for p in z["trend"])
    klang = api.get("/zones", params={"district": "Klang"}, headers=login(api, "manager.cen")).json()
    assert sum(p["gap_kwh"] for p in klang["trend"]) < sum(p["gap_kwh"] for p in z["trend"])
