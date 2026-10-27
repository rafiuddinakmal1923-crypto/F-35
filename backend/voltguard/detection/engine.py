"""Detection engine: run the three stages for every zone (SDD 5, 6.1 steps 2-4).

Pure computation on canonical tables; the pipeline module handles the database and the
simulation report calls this directly on in-memory simulations. Creates no cases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import polars as pl

from voltguard.detection import balance as bal_mod
from voltguard.detection.balance import BalanceResult
from voltguard.detection.features import FEATURE_NAMES, build_features
from voltguard.detection.scoring import score_premise
from voltguard.detection.voltage import VoltageResult, locate
from voltguard.detection.zone_input import ZoneInput, build_zone_inputs


@dataclass
class PremiseResult:
    premise_id: str
    transformer_id: str
    score: int
    rank: int
    confidence: str
    tags: list[str]
    reasons: list[dict]          # the displayed lines: top three, other, capped; they add up to score
    features: dict[str, float]
    details: dict
    smart: bool


@dataclass
class ZoneResult:
    zone: ZoneInput
    balance: BalanceResult
    voltage: VoltageResult | None
    quality_flags: list[dict]
    premises: list[PremiseResult] = field(default_factory=list)

    @property
    def scored(self) -> bool:
        return bool(self.premises)


@dataclass
class DetectionRun:
    run_date: date
    zones: dict[str, ZoneResult]
    model_version: str

    def premise_frame(self) -> pl.DataFrame:
        rows = [{"premise_id": p.premise_id, "transformer_id": p.transformer_id, "score": p.score, "rank": p.rank,
                 "confidence": p.confidence, "tags": ",".join(p.tags)} for z in self.zones.values() for p in z.premises]
        return pl.DataFrame(rows) if rows else pl.DataFrame(schema={"premise_id": pl.Utf8, "score": pl.Int64})


def run_zones(zones: dict[str, ZoneInput], cfg: dict, score_all: bool = False, fallback_loss_share: float | None = None,
              loss_shares: list[float] | None = None) -> DetectionRun:
    """score_all=True scores every zone (tuning and reports); the pipeline scores flagged and no-balance zones.

    Zones without network parameters borrow the median technical-loss share of clean zones with
    parameters (AS-8). The pipeline runs zones in batches: it passes the median found so far as
    `fallback_loss_share`, and `loss_shares` collects this batch's shares for the next batches.
    """
    from voltguard.detection import pattern

    prepared = {}
    for tx, z in zones.items():
        filled, completeness = bal_mod.fill_smart_readings(z)
        conv_slots, conv_daily, u_conv = bal_mod.estimate_conventional(z, filled, cfg["zone"]["conventional_daily_cv"])
        prepared[tx] = (filled, completeness, conv_slots, conv_daily, u_conv)

    # Zones with network parameters first, so the others can borrow a similar-zone loss share (AS-8).
    balances: dict[str, BalanceResult] = {}
    shares = []
    for tx, z in zones.items():
        if z.loss_params is not None and z.has_topology:
            filled, _, conv_slots, _, u_conv = prepared[tx]
            balances[tx] = bal_mod.balance_zone(z, cfg, filled, conv_slots, u_conv)
            b = balances[tx]
            if b.balance_available and not b.flagged:
                shares.append(float(np.nansum(b.tech_loss_kwh) / max(np.nansum(b.supplied_kwh), 1e-9)))
    if loss_shares is not None:
        loss_shares.extend(shares)
    if fallback_loss_share is not None:
        fallback = fallback_loss_share
    else:
        fallback = float(np.median(shares)) if shares else bal_mod.DEFAULT_LOSS_SHARE
    for tx, z in zones.items():
        if tx not in balances:
            filled, _, conv_slots, _, u_conv = prepared[tx]
            balances[tx] = bal_mod.balance_zone(z, cfg, filled, conv_slots, u_conv, fallback_loss_share=fallback)

    results: dict[str, ZoneResult] = {}
    run_date = None
    for tx, z in zones.items():
        filled, completeness, conv_slots, conv_daily, _ = prepared[tx]
        b = balances[tx]
        run_date = z.day_dates()[-1]
        flags = bal_mod.data_quality_flags(z, completeness, cfg["monitoring"]["min_interval_completeness"])
        zr = ZoneResult(z, b, None, flags)
        if score_all or b.flagged or not b.balance_available:
            zr.voltage = locate(z, b, filled, conv_slots, cfg)
            fs = build_features(z, b, zr.voltage, filled, conv_daily, cfg)
            scored = []
            for i, pid in enumerate(z.premise_ids):
                s = score_premise(fs.X[i], fs.tags[i], fs.details[i], fs.sub_reasons[i], cfg)
                scored.append((pid, s, i))
            scored.sort(key=lambda item: (-item[1].score, item[0]))
            for rank, (pid, s, i) in enumerate(scored, start=1):
                confidence = fs.confidence[i]
                if not b.balance_available:
                    confidence = "low"
                zr.premises.append(PremiseResult(
                    premise_id=pid, transformer_id=tx, score=s.score, rank=rank, confidence=confidence,
                    tags=fs.tags[i], reasons=[r.as_dict() for r in s.lines],
                    features={name: round(float(fs.X[i, k]), 4) for k, name in enumerate(FEATURE_NAMES)},
                    details=fs.details[i], smart=bool(z.smart[i]),
                ))
        results[tx] = zr
    return DetectionRun(run_date, results, pattern.load().version)


def run_tables(tables: dict[str, pl.DataFrame], start: date, days: int, cfg: dict, score_all: bool = False, **kwargs) -> DetectionRun:
    return run_zones(build_zone_inputs(tables, start, days), cfg, score_all=score_all, **kwargs)
