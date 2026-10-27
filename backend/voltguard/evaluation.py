"""Tuning and the simulation report (SDD 10.2-10.4, NFR-09, prompt 4.9).

* `tune` uses only the tuning scenario: it calibrates the loss model's error margin on clean
  zones and searches the score weights. It never sees held-out settings.
* `simulation_report` measures the held-out settings and every stress test and writes
  reports/simulation_report.md, starting with the summary table for the pitch deck.

Ground truth is read only here, for evaluation; it is never loaded into model inputs.
"""

from __future__ import annotations

import copy
import math
import time
from dataclasses import replace
from datetime import datetime

import numpy as np
import yaml

from voltguard import config
from voltguard.data import simulator
from voltguard.data.simulator import Injected, Scenario
from voltguard.detection import engine, pattern
from voltguard.detection.features import FEATURE_NAMES

LEGIT_KINDS = {"ev_charging", "metered_mining", "solar", "tenancy_only", "home_business", "vacancy"}
MAX_WEIGHT = 0.35


def top_k(n: int) -> int:
    return max(1, math.ceil(0.05 * n))


def run_scenario(scn: Scenario, cfg: dict, score_all: bool = True):
    tables, truth = simulator.simulate(scn)
    run = engine.run_tables(tables, scn.start_date, scn.days, cfg, score_all=score_all)
    return run, truth


def evaluate(run, truth) -> dict:
    """Per-zone and per-case outcomes against ground truth."""
    thefts, legit, zones = [], [], []
    for tx, zt in truth["zones"].items():
        zr = run.zones[tx]
        b = zr.balance
        ranks = {p.premise_id: p.rank for p in zr.premises}
        n = zt["n_homes"]
        k = top_k(n)
        has_theft = any(c["is_theft"] for c in zt["cases"])
        stolen = sum(c["stolen_kwh_per_day"] for c in zt["cases"] if c["is_theft"])
        zones.append({"transformer_id": tx, "has_theft": has_theft, "flagged": b.flagged,
                      "balance": b.balance_available, "n": n,
                      "stolen_share": stolen / max(zt["mean_supply_kwh_per_day"], 1e-9)})
        for c in zt["cases"]:
            rank = ranks.get(c["premise_id"])
            row = {"zone": tx, "premise_id": c["premise_id"], "kind": c["kind"], "rank": rank, "top_k": k, "n": n,
                   "zone_flagged": b.flagged, "balance": b.balance_available, "day_one": c["start_day"] == 0,
                   "stolen_kwh_per_day": c["stolen_kwh_per_day"],
                   "stolen_share": c["stolen_kwh_per_day"] / max(zt["mean_supply_kwh_per_day"], 1e-9)}
            # In the pipeline only flagged and no-balance zones are ranked.
            row["ranked_in_pipeline"] = b.flagged or not b.balance_available
            row["in_top"] = bool(rank is not None and rank <= k)
            (thefts if c["is_theft"] else legit).append(row)
    return {"thefts": thefts, "legit": legit, "zones": zones}


def summarise(ev: dict) -> dict:
    thefts = ev["thefts"]
    in_pipeline = [t for t in thefts if t["ranked_in_pipeline"]]
    found = [t for t in in_pipeline if t["in_top"]]
    legit_top = [l for l in ev["legit"] if l["ranked_in_pipeline"] and l["in_top"]]
    theft_zones = [z for z in ev["zones"] if z["has_theft"] and z["balance"]]
    clean_zones = [z for z in ev["zones"] if not z["has_theft"] and z["balance"]]
    # Inspections per theft found: inspecting the top 5% of each ranked zone vs random order.
    inspections = sum(t["top_k"] for t in {t["zone"]: t for t in in_pipeline}.values())
    random_per_theft = np.mean([t["n"] / max(sum(1 for u in in_pipeline if u["zone"] == t["zone"]), 1) for t in in_pipeline]) if in_pipeline else float("nan")
    return {
        "thefts": len(thefts),
        "thefts_in_flagged_or_no_balance_zones": len(in_pipeline),
        "thefts_in_top5": len(found),
        "share_all_thefts_in_top5": len(found) / max(len(thefts), 1),
        "share_ranked_thefts_in_top5": len(found) / max(len(in_pipeline), 1),
        "theft_zone_flag_rate": sum(z["flagged"] for z in theft_zones) / max(len(theft_zones), 1),
        "clean_zone_false_flags": sum(z["flagged"] for z in clean_zones),
        "clean_zones": len(clean_zones),
        "legit_in_top5": [(l["kind"], l["premise_id"]) for l in legit_top],
        "inspections_per_theft_model": inspections / max(len(found), 1) if found else float("nan"),
        "inspections_per_theft_random": float(random_per_theft),
        # Zone level: total stolen energy as a share of the zone's supply.
        "smallest_flagged_share": min((z["stolen_share"] for z in theft_zones if z["flagged"]), default=float("nan")),
        "largest_missed_share": max((z["stolen_share"] for z in theft_zones if not z["flagged"]), default=float("nan")),
    }


# --------------------------------------------------------------------------- tuning

def _fast_scores(X: np.ndarray, tags: list[list[str]], cfg: dict) -> np.ndarray:
    w = np.array([cfg["weights"].get(name, 0.0) for name in FEATURE_NAMES])
    t_idx = FEATURE_NAMES.index("tenancy_change")
    w_other = w.copy()
    w_other[t_idx] = 0
    other = X @ w_other
    tenancy = np.where((X[:, t_idx] > 0) & (other >= cfg["tenancy"]["gate_other_evidence"]),
                       np.minimum(w[t_idx] * X[:, t_idx], cfg["tenancy"]["max_contribution"]), 0.0)
    penalty = np.array([sum(cfg["penalties"].get(t, 0.0) for t in tg) for tg in tags])
    return np.clip(other + tenancy - penalty, 0, 1)


def tune(seed: int = 1000, samples: int = 400, progress=print) -> dict:
    """Calibrate u_loss on clean tuning zones and search weights on the tuning scenario only."""
    cfg = config.thresholds()
    scn = simulator.tuning_scenario(seed=seed)
    progress(f"Simulating {len(scn.zones)} tuning zones...")
    run, truth = run_scenario(scn, cfg)

    # Loss-model error measured on clean zones (SDD 5.1).
    rel_errors = []
    for tx, zt in truth["zones"].items():
        b = run.zones[tx].balance
        if not b.balance_available or any(c["is_theft"] for c in zt["cases"]):
            continue
        true_loss = np.array(zt["tech_loss_kwh_daily"])
        rel_errors.extend(np.abs(b.tech_loss_kwh - true_loss) / np.maximum(true_loss, 1e-6))
    loss_error = float(np.clip(np.percentile(rel_errors, 95) * 1.5, 0.05, 0.5)) if rel_errors else cfg["zone"]["loss_model_error_share"]

    zones = []
    for tx, zt in truth["zones"].items():
        zr = run.zones[tx]
        if not zr.premises:
            continue
        ids = [p.premise_id for p in zr.premises]
        X = np.array([[p.features[f] for f in FEATURE_NAMES] for p in zr.premises])
        tags = [p.tags for p in zr.premises]
        kinds = {c["premise_id"]: c["kind"] for c in zt["cases"]}
        zones.append((ids, X, tags, kinds, top_k(zt["n_homes"]), zr.balance.flagged or not zr.balance.balance_available))

    def objective(c: dict) -> float:
        total, count = 0.0, 0
        for ids, X, tags, kinds, k, ranked in zones:
            if not ranked:
                continue
            s = _fast_scores(X, tags, c)
            order = np.argsort(-s, kind="stable")
            rank = {ids[j]: r + 1 for r, j in enumerate(order)}
            theft_ids = {pid for pid, kind in kinds.items() if kind in simulator.THEFT_KINDS}
            best_other = max((s[j] for j, pid in enumerate(ids) if pid not in theft_ids), default=0.0)
            for pid, kind in kinds.items():
                if kind in simulator.THEFT_KINDS:
                    total += 1.0 if rank[pid] <= k else 1.0 / rank[pid]
                    # Margin over the highest-scoring non-theft premise: prefer robust separations.
                    total += 0.5 * (s[ids.index(pid)] - best_other)
                    count += 1
                elif kind in LEGIT_KINDS and rank[pid] <= k:
                    total -= 0.5
        return total / max(count, 1)

    base_w = np.array([cfg["weights"][f] for f in FEATURE_NAMES])
    rng = np.random.default_rng(seed)
    best_cfg, best = cfg, objective(cfg)
    progress(f"Default weights objective {best:.3f}; searching {samples} weight sets...")
    for s in range(samples):
        alpha = base_w / base_w.sum() * (60 if s % 2 else 15) + 0.05
        w = rng.dirichlet(alpha)
        if w.max() > MAX_WEIGHT:
            continue  # no single signal may dominate the score (day-one taps show no change, for example)
        trial = copy.deepcopy(cfg)
        trial["weights"] = {f: round(float(v), 4) for f, v in zip(FEATURE_NAMES, w)}
        score = objective(trial)
        if score > best + 1e-9:
            best, best_cfg = score, trial
    tuned = {"weights": best_cfg["weights"], "zone": {"loss_model_error_share": round(loss_error, 4)},
             "_tuning": {"seed": seed, "zones": len(scn.zones), "objective": round(float(best), 4),
                         "tuned_at": datetime.now().isoformat(timespec="seconds"), "split": "tuning"}}
    path = config.tuned_weights_path()
    path.write_text(yaml.safe_dump(tuned, sort_keys=False), encoding="utf-8")
    progress(f"Tuned objective {best:.3f}; loss-model error share {loss_error:.3f}; saved {path}")
    return tuned


# --------------------------------------------------------------------------- stress tests

def stress_scenarios(seed: int = 9000, count: int = 8) -> dict[str, Scenario]:
    base = simulator.heldout_scenario(seed=seed, count=count)
    out: dict[str, Scenario] = {}

    def variant(name, zone_fn):
        zones = [zone_fn(replace(z, cases=list(z.cases)), i) for i, z in enumerate(base.zones)]
        out[name] = replace(base, name=f"stress_{name}", zones=zones, split="stress")

    variant("noise_high", lambda z, i: replace(z, noise=0.45, missing_rate=0.03, meter_noise_v=0.8))
    variant("small_taps", lambda z, i: replace(z, cases=[replace(c, size=c.size * 0.4) if c.kind in simulator.THEFT_KINDS else c for c in z.cases]))
    variant("day_one_taps", lambda z, i: replace(z, cases=[replace(c, start_day=0) if c.kind in simulator.THEFT_KINDS else c for c in z.cases]))
    variant("monthly_meters_50pct", lambda z, i: replace(z, conventional_share=0.5))
    variant("tx_voltage_swings", lambda z, i: replace(z, tx_voltage_swing=6.0))
    variant("two_thieves", lambda z, i: replace(z, cases=z.cases + [Injected("partial_bypass", start_day=25, size=0.7, premise_type="bungalow")]))
    variant("no_voltage", lambda z, i: replace(z, voltage=False))
    variant("no_phase_data", lambda z, i: replace(z, phase_data=False))
    variant("no_transformer_meter", lambda z, i: replace(z, has_dtm=False))
    variant("many_solar_homes", lambda z, i: replace(z, cases=z.cases + [
        Injected("solar", start_day=int(10 + 4 * k), size=3.5, export=bool(k % 2), registered=bool(k % 3 == 0)) for k in range(8)]))
    return out


def _fmt(x, pct=False):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    return f"{x * 100:.0f}%" if pct else f"{x:.2f}" if isinstance(x, float) else str(x)


def simulation_report(progress=print, stress_count: int = 8) -> str:
    started = time.time()
    cfg = config.thresholds()
    tuned_meta = cfg.get("_tuning")
    sections = []

    progress("Held-out scenario...")
    held_scn = simulator.heldout_scenario()
    held_tables, held_truth = simulator.simulate(held_scn)
    held_run = engine.run_tables(held_tables, held_scn.start_date, held_scn.days, cfg)
    held = summarise(evaluate(held_run, held_truth))

    # Threshold sweep on the same held-out data (for OI-7: false alarms vs missed small taps).
    sweep = []
    for theta in (0.05, 0.03, 0.02, 0.01):
        progress(f"Threshold sweep {theta:.0%}...")
        trial = config.deep_merge(cfg, {"zone": {"share_of_supply": theta}})
        s = summarise(evaluate(engine.run_tables(held_tables, held_scn.start_date, held_scn.days, trial), held_truth))
        sweep.append((theta, s))

    progress("Demo scenario...")
    demo_run, demo_truth = run_scenario(simulator.demo_scenario(), cfg, score_all=False)
    demo_ev = evaluate(demo_run, demo_truth)
    demo_zone = config.demo_config().get("demo_zone", "TX-CEN-001")
    demo_cases = [t for t in demo_ev["thefts"] if t["zone"] == demo_zone]
    demo_legit = [l for l in demo_ev["legit"] if l["zone"] == demo_zone]

    stress = {}
    for name, scn in stress_scenarios(count=stress_count).items():
        progress(f"Stress test {name}...")
        run, truth = run_scenario(scn, cfg, score_all=False)
        stress[name] = summarise(evaluate(run, truth))

    pm_meta_path = pattern.model_path().with_suffix(".meta.json")
    pm_meta = yaml.safe_load(pm_meta_path.read_text(encoding="utf-8")) if pm_meta_path.exists() else {}
    day_one = next((t for t in demo_cases if t["day_one"]), None)
    partial = next((t for t in demo_cases if t["kind"] == "partial_bypass"), None)
    legit_top_demo = [l["kind"] for l in demo_legit if l["in_top"]]
    flagged_small = [n for n, s in stress.items() if not math.isnan(s["smallest_flagged_share"])]
    smallest = min((stress[n]["smallest_flagged_share"] for n in flagged_small), default=float("nan"))

    summary = [
        "| Result | Value |",
        "| --- | --- |",
        f"| Injected thefts in the top 5% (held-out settings, ranked zones) | {held['thefts_in_top5']} of {held['thefts_in_flagged_or_no_balance_zones']} ({_fmt(held['share_ranked_thefts_in_top5'], True)}) |",
        f"| Injected thefts in the top 5% (held-out settings, all thefts incl. unflagged zones) | {held['thefts_in_top5']} of {held['thefts']} ({_fmt(held['share_all_thefts_in_top5'], True)}) |",
        f"| Inspections per theft found: model ranking vs random order | {_fmt(held['inspections_per_theft_model'])} vs {_fmt(held['inspections_per_theft_random'])} |",
        f"| Day-one tap in the demo zone flagged and in the top 5% | {'yes' if day_one and day_one['zone_flagged'] and day_one['in_top'] else 'no'} (rank {day_one['rank'] if day_one else 'n/a'}) |",
        f"| Partial bypass in the demo zone flagged and in the top 5% | {'yes' if partial and partial['zone_flagged'] and partial['in_top'] else 'no'} (rank {partial['rank'] if partial else 'n/a'}) |",
        f"| EV, rooftop solar, metered mining or tenancy-only homes in the top suspects (demo zone) | {', '.join(legit_top_demo) if legit_top_demo else 'none'} |",
        f"| Same, held-out settings | {', '.join(sorted({k for k, _ in held['legit_in_top5']})) if held['legit_in_top5'] else 'none'} |",
        f"| Pattern model AUC on a held-out split ({pm_meta.get('source', 'unknown')}) | {pm_meta.get('holdout_auc', 'n/a')} |",
        f"| Smallest total theft that flagged its zone (stress tests, share of zone supply) | {_fmt(smallest, True)} |",
        f"| Largest total theft that did not flag its zone (held-out settings) | {_fmt(held['largest_missed_share'], True)} |",
        f"| Clean held-out zones wrongly flagged | {held['clean_zone_false_flags']} of {held['clean_zones']} |",
    ]
    sections.append("## Summary (copy into the pitch deck)\n\n" + "\n".join(summary))

    notes = [
        "- Voltages are generated by the load-flow model, because the open datasets hold kWh only. These results show the voltage locator works on physics-consistent data, not that it works on TNB meters (SRS AS-3).",
        f"- Flag threshold: {cfg['zone']['share_of_supply'] * 100:.0f}% of supply plus the uncertainty margin, for {cfg['zone']['consecutive_days']} days. A single partial bypass is usually a few percent of a zone's supply, so on its own it often stays below this threshold; such thefts are counted as missed above, not hidden.",
        f"- Weights: {'tuned on the tuning split only (' + str(tuned_meta.get('zones')) + ' zones, seed ' + str(tuned_meta.get('seed')) + ')' if tuned_meta else 'defaults from config/thresholds.yaml (run `make.ps1 tune` first)'}; never tuned on held-out or stress settings.",
        f"- Pattern model training data: {pm_meta.get('source', 'unknown')}. When the SGCC download is not available it is trained on synthetic windows that follow the SGCC theft patterns; its AUC then measures fit to those patterns, not real-world performance.",
        "- 'Ranked zones' are the zones the pipeline ranks: flagged zones and zones without a transformer meter.",
    ]
    sections.append("## How to read this\n\n" + "\n".join(notes))

    sweep_rows = ["| Flag threshold (share of supply) | Theft zones flagged | Clean zones wrongly flagged | All thefts in top 5% | Smallest flagged zone theft |",
                  "| --- | --- | --- | --- | --- |"]
    for theta, s in sweep:
        sweep_rows.append(f"| {theta:.0%}{' (default)' if theta == cfg['zone']['share_of_supply'] else ''} | {_fmt(s['theft_zone_flag_rate'], True)} | "
                          f"{s['clean_zone_false_flags']}/{s['clean_zones']} | {s['thefts_in_top5']}/{s['thefts']} | {_fmt(s['smallest_flagged_share'], True)} |")
    sections.append("## Flag threshold sweep (held-out settings, for OI-7)\n\n"
                    "The uncertainty margin u is always added on top. Lower thresholds catch smaller taps; the clean-zone column shows the false-alarm cost.\n\n"
                    + "\n".join(sweep_rows))

    rows = ["| Stress test | Theft zones flagged | Thefts in top 5% (ranked zones) | All thefts in top 5% | Smallest flagged tap | Clean zones wrongly flagged | Legitimate homes in top 5% |",
            "| --- | --- | --- | --- | --- | --- | --- |"]
    for name, s in stress.items():
        rows.append(f"| {name.replace('_', ' ')} | {_fmt(s['theft_zone_flag_rate'], True)} | {s['thefts_in_top5']}/{s['thefts_in_flagged_or_no_balance_zones']} | "
                    f"{s['thefts_in_top5']}/{s['thefts']} | {_fmt(s['smallest_flagged_share'], True)} | {s['clean_zone_false_flags']}/{s['clean_zones']} | "
                    f"{', '.join(sorted({k for k, _ in s['legit_in_top5']})) or 'none'} |")
    sections.append("## Stress tests (SDD 10.3): where detection breaks\n\n" + "\n".join(rows))

    held_rows = ["| Zone | Case | Stolen kWh/day | Share of supply | Zone flagged | Rank | Top 5%? |", "| --- | --- | --- | --- | --- | --- | --- |"]
    ev = evaluate(held_run, held_truth)
    for t in ev["thefts"]:
        held_rows.append(f"| {t['zone']} | {t['kind']}{' (day one)' if t['day_one'] else ''} | {t['stolen_kwh_per_day']:.1f} | {t['stolen_share'] * 100:.1f}% | "
                         f"{'yes' if t['zone_flagged'] else ('no balance' if not t['balance'] else 'no')} | {t['rank'] if t['ranked_in_pipeline'] else '-'} | {'yes' if t['in_top'] and t['ranked_in_pipeline'] else 'no'} |")
    sections.append("## Held-out thefts, one by one\n\n" + "\n".join(held_rows))

    demo_rows = ["| Case | Premise | Rank | Tags |", "| --- | --- | --- | --- |"]
    ranks = {p.premise_id: p for p in demo_run.zones[demo_zone].premises}
    for c in demo_truth["zones"][demo_zone]["cases"]:
        p = ranks.get(c["premise_id"])
        demo_rows.append(f"| {c['kind']} | {c['premise_id']} | {p.rank if p else '-'} | {', '.join(p.tags) if p and p.tags else ''} |")
    sections.append(f"## Demo zone {demo_zone}\n\n" + "\n".join(demo_rows))

    header = (f"# Simulation report\n\nGenerated {datetime.now().isoformat(timespec='seconds')} in {time.time() - started:.0f} s by "
              "`make.ps1 simreport`. Failures are reported as they are.\n")
    text = header + "\n\n".join(sections) + "\n"
    out = config.REPO_ROOT / "reports" / "simulation_report.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(text, encoding="utf-8")
    progress(f"Wrote {out}")
    return text
