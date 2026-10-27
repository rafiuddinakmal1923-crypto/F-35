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
import math
import sys
import time
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    parser.add_argument("--step", type=int, default=3)
    parser.add_argument("--out", default=str(ROOT / "reports" / "backtest_report.md"))
    args = parser.parse_args(argv)
    started = time.time()
    tables, start, cases = known_cases_simulated() if args.source == "simulated" else known_cases_active()
    total_days = sources.period(tables)[1]
    cfg = config.thresholds()
    history: dict[str, list[tuple[int, bool, int | None, int]]] = {c["premise_id"]: [] for c in cases}
    for d in list(range(args.first_day, total_days + 1, args.step)) + ([total_days] if (total_days - args.first_day) % args.step else []):
        run = engine.run_tables(cut(tables, start, d), start, d, cfg)
        print(f"  day {d:3d}: flagged {[tx for tx, z in run.zones.items() if z.balance.flagged]}")
        for c in cases:
            zr = run.zones.get(c["zone"])
            rank = next((p.rank for p in zr.premises if p.premise_id == c["premise_id"]), None) if zr else None
            n = zr.zone.n if zr else 0
            history[c["premise_id"]].append((d, bool(zr and zr.balance.flagged), rank, n))

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
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
