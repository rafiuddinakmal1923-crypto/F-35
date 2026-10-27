"""Command line: `python -m voltguard <command>`.

`make.ps1` and the Makefile call these commands; the API's job endpoints call the same
service functions, so a command and its HTTP job always behave the same way.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from voltguard import config

COMMANDS: dict[str, tuple[str, callable, callable | None]] = {}
# Modules that register more commands when imported (data layer, database, demo).
COMMAND_MODULES = ("voltguard.data.ingest", "voltguard.service.commands", "voltguard.service.demo")


def command(name: str, help_text: str, arguments=None):
    def register(fn):
        COMMANDS[name] = (help_text, fn, arguments)
        return fn
    return register


# --------------------------------------------------------------------------- simulation and models

@command("simulate", "Simulate a scenario into DATA_ROOT/simulated/<run> (tables + ground truth)",
         lambda p: (p.add_argument("--run", default="demo", choices=["demo", "tuning", "heldout"]),
                    p.add_argument("--seed", type=int)))
def cmd_simulate(args) -> int:
    from voltguard.data import simulator

    builders = {"demo": simulator.demo_scenario, "tuning": simulator.tuning_scenario, "heldout": simulator.heldout_scenario}
    scn = builders[args.run](seed=args.seed) if args.seed is not None else builders[args.run]()
    started = time.time()
    tables, truth = simulator.simulate(scn)
    folder = simulator.write_run(scn, tables, truth)
    print(f"Simulated {len(scn.zones)} zones, {scn.days} days in {time.time() - started:.1f} s -> {folder}")
    for name, frame in sorted(tables.items()):
        print(f"  {name:24s} {frame.height:>10,d} rows")
    return 0


@command("train-models", "Train the pattern model (SGCC or synthetic) and the autoencoder")
def cmd_train_models(args) -> int:
    from voltguard.detection import anomaly, pattern

    _, metrics = pattern.train_default(save=True)
    pattern.reset_cache()
    print(f"Pattern model: {json.dumps(metrics)}")
    anomaly.train_from_simulation()
    print(f"Autoencoder saved to {anomaly.model_path()}")
    return 0


@command("tune", "Tune score weights and the loss-model margin on the tuning split only",
         lambda p: p.add_argument("--samples", type=int, default=400))
def cmd_tune(args) -> int:
    from voltguard import evaluation

    evaluation.tune(samples=args.samples)
    config.load_yaml.cache_clear()
    return 0


@command("simreport", "Write reports/simulation_report.md (held-out settings and stress tests)")
def cmd_simreport(args) -> int:
    from voltguard import evaluation

    evaluation.simulation_report()
    return 0


@command("detect", "Run detection on a simulated run without a database and print the ranked zones",
         lambda p: p.add_argument("--run", default="demo"))
def cmd_detect(args) -> int:
    from voltguard.data import simulator
    from voltguard.detection import engine

    truth = simulator.load_truth(args.run)
    tables = simulator.load_run_tables(args.run)
    from datetime import date

    run = engine.run_tables(tables, date.fromisoformat(truth["start_date"]), truth["days"], config.thresholds())
    for tx, zr in sorted(run.zones.items(), key=lambda kv: -float(kv[1].balance.gap_pct[-1]) if kv[1].balance.balance_available else 1):
        b = zr.balance
        state = "no balance" if not b.balance_available else ("FLAGGED" if b.flagged else "ok")
        top = ", ".join(f"{p.premise_id} ({p.score})" for p in zr.premises[:3])
        print(f"{tx:12s} {state:10s} {top}")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Later milestones register their commands on import.
    import importlib
    import importlib.util

    for module in COMMAND_MODULES:
        parent = module.rsplit(".", 1)[0]
        if importlib.util.find_spec(parent) and importlib.util.find_spec(module):
            importlib.import_module(module)
    parser = argparse.ArgumentParser(prog="voltguard", description="VoltGuard AI R0 commands")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, (help_text, _, arguments) in sorted(COMMANDS.items()):
        p = sub.add_parser(name, help=help_text)
        if arguments:
            arguments(p)
    args = parser.parse_args(argv)
    return COMMANDS[args.command][1](args) or 0


if __name__ == "__main__":
    sys.exit(main())
