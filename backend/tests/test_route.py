"""Route planner (supports FR-AG-02): visiting order, navigation links, and who may see a team's stops."""

from __future__ import annotations

import random

from tests.conftest import login
from voltguard.agents import route


def test_route_order_beats_nearest_neighbour_and_is_close_to_the_best():
    from itertools import permutations

    rng = random.Random(7)
    start = (3.07, 101.52)
    worse_than_best = []
    for _ in range(30):
        pts = [(3.0 + rng.random() * 0.2, 101.4 + rng.random() * 0.3) for _ in range(6)]
        order = route.order_stops(start, pts)
        assert sorted(order) == list(range(6))
        got = route.route_length(start, pts, order)
        assert got <= route.route_length(start, pts, route.nearest_neighbour(start, pts)) + 1e-9
        best = min(route.route_length(start, pts, list(p)) for p in permutations(range(6)))
        worse_than_best.append(got / best - 1)
    assert max(worse_than_best) < 0.15 and sum(worse_than_best) / len(worse_than_best) < 0.03


def test_FR_AG_02_team_route_with_navigation_and_limits(api, pg):
    analyst, sup = login(api, "analyst.nor"), login(api, "supervisor.nor")
    made = []
    for n in range(40, 80):                       # three free premises on one street, assigned to Team C
        r = api.post("/cases", json={"premise_id": f"P-NOR-002-{n:03d}"}, headers=analyst)
        if r.status_code == 200:
            made.append(r.json()["case_id"])
            api.patch(f"/cases/{made[-1]}/assign", json={"team": "T-NOR-C"}, headers=sup)
        if len(made) == 3:
            break
    plan = api.get("/route", headers=login(api, "inspector.c")).json()
    ids = [s["case_id"] for s in plan["stops"]]
    assert set(made) <= set(ids) and [s["stop"] for s in plan["stops"]] == list(range(1, len(ids) + 1))
    assert plan["base"] and plan["total_km"] > 0 and plan["full_route_url"].startswith("https://www.google.com/maps/dir/")
    first = plan["stops"][0]
    assert first["navigate"]["waze"].startswith("https://waze.com/ul?ll=") and "FAKE" not in first["navigate"]["google"]
    running = [s["total_km"] for s in plan["stops"]]
    assert running == sorted(running) and plan["stops"][1]["arrive_after_min"] >= first["arrive_after_min"] + 30
    # The supervisor sees the same route; other teams, other regions and other roles do not.
    assert [s["case_id"] for s in api.get("/route", params={"team": "T-NOR-C"}, headers=sup).json()["stops"]] == ids
    assert api.get("/route", params={"team": "T-NOR-C"}, headers=login(api, "inspector.a")).status_code == 403
    assert api.get("/route", params={"team": "T-NOR-C"}, headers=login(api, "supervisor.cen")).status_code == 404
    assert api.get("/route", params={"team": "T-NOR-C"}, headers=login(api, "analyst.nor")).status_code == 403
