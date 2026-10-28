"""Route planner: the visiting order of a team's assigned cases for the day (supports FR-AG-02 dispatch).

Starts at the team's base on today's roster, orders the stops by nearest neighbour and then improves
the order with 2-opt (swapping crossing legs). Distances are straight-line km times a road factor;
time adds an average driving speed and a fixed time on site (config `route`). No external routing
service is called: the plan works offline and no location leaves the system.

Locations come only through vg_case_contact(), so the caller sees a stop only where the case rules
already show its address (the assigned team's inspectors and the region's supervisor). Navigation
links (Google Maps, Waze) carry coordinates only and are opened by the inspector, never sent.
"""

from __future__ import annotations

from datetime import date

import psycopg

from voltguard.agents.dispatch import haversine_km, roster_date
from voltguard.db import Caller
from voltguard.service import settings

MAX_WAYPOINTS = 9      # Google Maps directions links accept up to 9 waypoints


def _leg(a: tuple[float, float], b: tuple[float, float], road_factor: float) -> float:
    return haversine_km(a[0], a[1], b[0], b[1]) * road_factor


def route_length(start: tuple[float, float], points: list[tuple[float, float]], seq: list[int], road_factor: float = 1.0) -> float:
    path = [start] + [points[i] for i in seq]
    return sum(_leg(path[k], path[k + 1], road_factor) for k in range(len(path) - 1))


def nearest_neighbour(start: tuple[float, float], points: list[tuple[float, float]], road_factor: float = 1.0) -> list[int]:
    left, order, here = set(range(len(points))), [], start
    while left:
        nxt = min(left, key=lambda i: (_leg(here, points[i], road_factor), i))
        order.append(nxt)
        left.remove(nxt)
        here = points[nxt]
    return order


def order_stops(start: tuple[float, float], points: list[tuple[float, float]], road_factor: float = 1.0) -> list[int]:
    """Indices of `points` in visiting order from `start` (open route: no return to base)."""
    order = nearest_neighbour(start, points, road_factor)

    def length(seq: list[int]) -> float:
        return route_length(start, points, seq, road_factor)

    improved = True
    while improved:                      # 2-opt: reverse a stretch when that shortens the route
        improved = False
        best = length(order)
        for i in range(len(order) - 1):
            for j in range(i + 1, len(order)):
                candidate = order[:i] + order[i:j + 1][::-1] + order[j + 1:]
                if length(candidate) < best - 1e-9:
                    order, best, improved = candidate, length(candidate), True
    return order


def _base(conn: psycopg.Connection, team: str, region: str) -> tuple[float, float] | None:
    shift = roster_date(conn, region)
    row = conn.execute("SELECT base_lat, base_lon FROM duty_roster WHERE team_id = %s AND shift_date = %s", (team, shift)).fetchone() if shift else None
    if row:
        return row["base_lat"], row["base_lon"]
    from voltguard import config

    t = next((t for t in config.demo_config().get("teams", []) if t["team_id"] == team), None)
    return (t["base_lat"], t["base_lon"]) if t else None


def maps_links(lat: float, lon: float) -> dict:
    return {"google": f"https://www.google.com/maps/dir/?api=1&destination={lat:.6f},{lon:.6f}&travelmode=driving",
            "waze": f"https://waze.com/ul?ll={lat:.6f},{lon:.6f}&navigate=yes"}


def plan(conn: psycopg.Connection, caller: Caller, team: str) -> dict:
    """Today's route for one team: ordered stops with leg and running distance and an arrival estimate."""
    cfg = settings.thresholds(conn).get("route", {"road_factor": 1.3, "speed_kmh": 30, "visit_minutes": 30})
    team_row = conn.execute("SELECT team_id, name, region FROM team WHERE team_id = %s", (team,)).fetchone()
    if not team_row:
        raise LookupError("Team not found in your region")
    cases = conn.execute("""SELECT case_id, premise_id, origin, joint_operation, assigned_at FROM inspection_case
                            WHERE assigned_team = %s AND status = 'assigned' ORDER BY case_id""", (team,)).fetchall()
    stops, unplaced = [], []
    for c in cases:
        loc = conn.execute("SELECT address, lat, lon FROM vg_case_contact(%s)", (c["case_id"],)).fetchone()
        if loc and loc["lat"] is not None:
            stops.append({**c, "address": loc["address"], "lat": loc["lat"], "lon": loc["lon"]})
        else:
            unplaced.append(c["case_id"])
    base = _base(conn, team, team_row["region"])
    start = base or ((stops[0]["lat"], stops[0]["lon"]) if stops else None)
    order = order_stops(start, [(s["lat"], s["lon"]) for s in stops], cfg["road_factor"]) if start else []
    here, total_km, minutes, out = start, 0.0, 0.0, []
    for n, i in enumerate(order, 1):
        s = stops[i]
        leg = _leg(here, (s["lat"], s["lon"]), cfg["road_factor"])
        total_km += leg
        minutes += leg / cfg["speed_kmh"] * 60
        out.append({"stop": n, "case_id": s["case_id"], "premise_id": s["premise_id"],
                    "label": "Routine meter check" if s["origin"] == "random_sample" else "Inspection",
                    "joint_operation": s["joint_operation"], "address": s["address"], "lat": s["lat"], "lon": s["lon"],
                    "leg_km": round(leg, 1), "total_km": round(total_km, 1), "arrive_after_min": round(minutes),
                    "base_km": round(haversine_km(start[0], start[1], s["lat"], s["lon"]), 1),   # straight line from base
                    "navigate": maps_links(s["lat"], s["lon"])})
        minutes += cfg["visit_minutes"]
        here = (s["lat"], s["lon"])
    full = None
    if out and start:
        last = out[-1]
        waypoints = "|".join(f"{s['lat']:.6f},{s['lon']:.6f}" for s in out[:-1][:MAX_WAYPOINTS])
        full = (f"https://www.google.com/maps/dir/?api=1&origin={start[0]:.6f},{start[1]:.6f}"
                f"&destination={last['lat']:.6f},{last['lon']:.6f}&travelmode=driving" + (f"&waypoints={waypoints}" if waypoints else ""))
    return {"team": team, "team_name": team_row["name"], "date": date.today().isoformat(),
            "base": {"lat": start[0], "lon": start[1]} if start else None, "stops": out, "unplaced": unplaced,
            "total_km": round(total_km, 1), "total_minutes": round(minutes), "full_route_url": full,
            "assumptions": f"Straight line x {cfg['road_factor']} road factor, {cfg['speed_kmh']} km/h, "
                           f"{cfg['visit_minutes']} min per visit; joint operations wait for the police."}
