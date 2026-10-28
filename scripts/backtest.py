"""Back-test (R1 first step, SDD 10.1 "Pilot evaluation"): run detection day by day over a past period
and report where known confirmed cases would have ranked, and from which day.

    python scripts/backtest.py                 # simulated history with ground truth (R0 demonstration)
    python scripts/backtest.py --source active # the active data sources (e.g. a TNB extract) and the
                                               # confirmed cases in inspection_outcome (historic labels)
    python scripts/backtest.py --step 2 --first-day 14

Each simulated "day d" sees only the readings up to and including that day, as the nightly
pipeline would have. Output: reports/backtest_report.md.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPLAY = ROOT / "reports" / "backtest_replay.json"
sys.path.insert(0, str(ROOT / "backend"))

import polars as pl  # noqa: E402

from voltguard import config  # noqa: E402
from voltguard.data import simulator, sources  # noqa: E402
from voltguard.detection import engine  # noqa: E402


def known_cases_simulated() -> tuple[dict, object, list[dict]]:
    scn = simulator.demo_scenario()
    tables, truth = simulator.simulate(scn)
    cases = [{"premise_id": c["premise_id"], "zone": tx, "kind": c["kind"], "start": scn.start_date + timedelta(days=c["start_day"])}
             for tx, z in truth["zones"].items() for c in z["cases"] if c["is_theft"]]
    return tables, scn.start_date, cases


def known_cases_active() -> tuple[dict, object, list[dict]]:
    tables = sources.load_active_tables()
    start, _ = sources.period(tables)
    outcomes = tables.get("inspection_outcome")
    if outcomes is None or not outcomes.height:
        raise SystemExit("No historic inspection_outcome rows in the active sources: nothing to back-test against.")
    premises = tables["premise"].select("premise_id", "transformer_id")
    confirmed = outcomes.filter(pl.col("outcome") == "confirmed_theft").join(premises, on="premise_id")
    cases = [{"premise_id": r["premise_id"], "zone": r["transformer_id"], "kind": "confirmed_theft",
              "start": r["recorded_at"].date() if r["recorded_at"] else None} for r in confirmed.iter_rows(named=True)]
    return tables, start, cases


def cut(tables: dict, start, days: int) -> dict:
    end = start + timedelta(days=days)
    out = dict(tables)
    for name, col in (("meter_reading", "ts"), ("transformer_reading", "ts")):
        if name in out:
            out[name] = out[name].filter(pl.col(col).dt.date() < end)
    if "meter_monthly_reading" in out:
        out["meter_monthly_reading"] = out["meter_monthly_reading"].filter(pl.col("month") < end.replace(day=1))  # a month's reading arrives after it ends
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", choices=["simulated", "active"], default="simulated")
    parser.add_argument("--first-day", type=int, default=14, help="first day to score (days of history before it)")
    parser.add_argument("--step", type=int, default=None, help="days between runs (default 3; 1 with --replay)")
    parser.add_argument("--replay", action="store_true",
                        help="also write reports/backtest_replay.json for the web app's back-test replay (GET /backtest/{zone})")
    parser.add_argument("--out", default=str(ROOT / "reports" / "backtest_report.md"))
    args = parser.parse_args(argv)
    args.step = args.step or (1 if args.replay else 3)
    started = time.time()
    tables, start, cases = known_cases_simulated() if args.source == "simulated" else known_cases_active()
    total_days = sources.period(tables)[1]
    cfg = config.thresholds()
    history: dict[str, list[tuple[int, bool, int | None, int]]] = {c["premise_id"]: [] for c in cases}
    replay: dict[str, list[dict]] = {c["zone"]: [] for c in cases}
    run = None
    for d in list(range(args.first_day, total_days + 1, args.step)) + ([total_days] if (total_days - args.first_day) % args.step else []):
        run = engine.run_tables(cut(tables, start, d), start, d, cfg)
        print(f"  day {d:3d}: flagged {[tx for tx, z in run.zones.items() if z.balance.flagged]}")
        for c in cases:
            zr = run.zones.get(c["zone"])
            rank = next((p.rank for p in zr.premises if p.premise_id == c["premise_id"]), None) if zr else None
            n = zr.zone.n if zr else 0
            history[c["premise_id"]].append((d, bool(zr and zr.balance.flagged), rank, n))
        if args.replay:
            for tx, frames in replay.items():
                zr = run.zones.get(tx)
                if zr:
                    frames.append(replay_frame(d, start, zr))

    lines = [f"# Back-test report ({args.source} data)", "",
             f"Generated in {time.time() - started:.0f} s by `scripts/backtest.py --source {args.source}`. Detection was run as of every "
             f"{args.step} day(s) from day {args.first_day} to day {total_days}, each time seeing only the readings up to that day.",
             "Ranked = the premise's zone was flagged or had no balance, so the pipeline ranked it. Top 5% = within the zone's top 5%.", "",
             "| Premise | Zone | Case | Theft starts | First day zone flagged | First day in top 5% | Rank on the last day |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    found = 0
    for c in cases:
        rows = history[c["premise_id"]]
        flagged_day = next((start + timedelta(days=d - 1) for d, f, _, _ in rows if f), None)
        top_day = next((start + timedelta(days=d - 1) for d, f, r, n in rows if r is not None and r <= max(1, math.ceil(0.05 * n))), None)
        last_rank = rows[-1][2] if rows else None
        found += top_day is not None
        lines.append(f"| {c['premise_id']} | {c['zone']} | {c['kind']} | {c['start']} | {flagged_day or 'not flagged'} | "
                     f"{top_day or 'no'} | {last_rank if last_rank is not None else '-'} |")
    lines += ["", f"{found} of {len(cases)} known cases reached their zone's top 5% at some point in the period.",
              "On simulated data this rehearses the R1 back-test; it says nothing about TNB data (SRS NFR-10, SDD OI-12)."]
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    if args.replay and run is not None:
        write_replay(args, tables, start, cases, history, replay, run)
    return 0


def replay_frame(d: int, start, zr) -> dict:
    """One replay day: what the nightly run would have shown as of day d (zone flag, ranking)."""
    b = zr.balance
    k = max(1, math.ceil(0.05 * zr.zone.n))
    return {"day": d, "date": (start + timedelta(days=d - 1)).isoformat(), "flagged": bool(b.flagged),
            "over_threshold": bool(b.over_threshold[-1]) if len(b.over_threshold) else False,
            "gap_start": b.gap_start.isoformat() if b.gap_start else None, "gap_since_start": bool(b.gap_since_start),
            "top_k": k, "ranked": bool(zr.premises),
            "top": [{"premise_id": p.premise_id, "rank": p.rank, "score": p.score} for p in zr.premises[:10]]}


def write_replay(args, tables, start, cases, history, replay, run) -> None:
    """reports/backtest_replay.json: per zone with a known case, the final daily balance and one frame per run day."""
    regions = dict(zip(tables["transformer"]["transformer_id"].to_list(), tables["transformer"]["region"].to_list()))
    zones = {}
    for tx, frames in replay.items():
        zr = run.zones.get(tx)
        if not zr or not frames:
            continue
        b = zr.balance
        known = []
        for c in (c for c in cases if c["zone"] == tx):
            rows = history[c["premise_id"]]
            top_day = next((d for d, f, r, n in rows if r is not None and r <= max(1, math.ceil(0.05 * n))), None)
            flag_day = next((d for d, f, _, _ in rows if f), None)
            theft_day = (c["start"] - start).days + 1 if c["start"] else None
            known.append({"premise_id": c["premise_id"], "kind": c["kind"], "theft_starts": str(c["start"]) if c["start"] else None,
                          "theft_start_day": theft_day, "first_flag_day": flag_day, "first_top5_day": top_day,
                          "days_to_detection": (top_day - max(theft_day, 1)) if top_day and theft_day else None})

        def series(values) -> list[float | None]:
            return [None if x is None or not math.isfinite(float(x)) else round(float(x), 1) for x in values]

        zones[tx] = {"zone": tx, "region": regions.get(tx), "balance_available": bool(b.balance_available), "n_premises": zr.zone.n,
                     "balance": {"dates": [x.isoformat() for x in b.dates], "supplied_kwh": series(b.supplied_kwh),
                                 "explained_kwh": series(b.metered_kwh + b.estimated_kwh + b.tech_loss_kwh),
                                 "gap_kwh": series(b.gap_kwh), "uncertainty_kwh": series(b.uncertainty_kwh)},
                     "known_cases": known, "frames": frames}
    payload = {"generated": datetime.now().isoformat(timespec="seconds"), "source": args.source, "step_days": args.step,
               "first_day": args.first_day, "start": start.isoformat(), "zones": zones}
    REPLAY.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {REPLAY}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
