"""data.gov.my monthly electricity consumption adapter (prompt 3.2).

Source: https://storage.data.gov.my/energy/electricity_consumption.parquet (catalogue
"electricity_consumption"), national consumption by month and sector. It holds national totals,
not per-household figures, so it rescales the simulator's household profiles only by month:
each calendar month's domestic consumption relative to the yearly average gives a factor that
multiplies simulated daily use (`rescale: datagovmy`). The household level itself stays the
configurable placeholder `mean_kwh`; no per-household figure is invented.

The adapter looks for a date column, a sector column with a domestic sector (falls back to
the total when none) and a numeric consumption column, so small schema changes do not break it.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from voltguard.data import adapters

URL = "https://storage.data.gov.my/energy/electricity_consumption.parquet"


def _columns(frame: pl.DataFrame) -> tuple[str, str | None, str]:
    date_col = next((c for c in frame.columns if c.lower() in ("date", "month", "period")), None)
    sector_col = next((c for c in frame.columns if c.lower() in ("sector", "category", "type")), None)
    numeric = [c for c, t in frame.schema.items() if t.is_numeric() and c != date_col]
    value_col = next((c for c in numeric if "consum" in c.lower()), numeric[0] if numeric else None)
    if date_col is None or value_col is None:
        raise ValueError(f"Unexpected data.gov.my schema: {frame.schema}")
    return date_col, sector_col, value_col


def month_factors_from(frame: pl.DataFrame, years: int = 5) -> pl.DataFrame:
    date_col, sector_col, value_col = _columns(frame)
    if frame[date_col].dtype == pl.Utf8:
        frame = frame.with_columns(pl.col(date_col).str.slice(0, 10).str.to_date(strict=False))
    if sector_col:
        sectors = frame[sector_col].cast(pl.Utf8).str.to_lowercase()
        domestic = sectors.str.contains("domestic")
        chosen = frame.filter(domestic) if domestic.any() else frame.filter(sectors.str.contains("total"))
        sector = "domestic" if domestic.any() else "total"
    else:
        chosen, sector = frame, "all"
    chosen = chosen.drop_nulls([date_col, value_col])
    latest = chosen[date_col].max()
    chosen = chosen.filter(pl.col(date_col) > latest.replace(year=latest.year - years))
    monthly = chosen.group_by(pl.col(date_col).dt.month().alias("month")).agg(pl.col(value_col).mean().alias("mean"))
    # Per-day factor: monthly totals differ partly because months have different lengths.
    days_in = {1: 31.0, 2: 28.25, 3: 31.0, 4: 30.0, 5: 31.0, 6: 30.0, 7: 31.0, 8: 31.0, 9: 30.0, 10: 31.0, 11: 30.0, 12: 31.0}
    monthly = monthly.with_columns((pl.col("mean") / pl.col("month").replace_strict(days_in, return_dtype=pl.Float64)).alias("per_day"))
    overall = float(monthly["per_day"].mean())
    return monthly.with_columns((pl.col("per_day") / overall).round(4).alias("factor"), pl.lit(sector).alias("sector")).sort("month").select(
        "month", "factor", "sector")


def convert(force: bool = False) -> dict | None:
    files = sorted(adapters.raw_dir("datagovmy").glob("*.parquet")) + sorted(adapters.raw_dir("datagovmy").glob("*.csv"))
    out = adapters.processed("datagovmy_month_factors.parquet")
    if not files:
        return None
    if not force and adapters.up_to_date(files, [out]):
        return {"status": "up to date", "path": str(out)}
    frame = pl.concat([pl.read_parquet(p) if p.suffix == ".parquet" else pl.read_csv(p, try_parse_dates=True) for p in files],
                      how="diagonal_relaxed")
    factors = month_factors_from(frame)
    factors.write_parquet(out)
    adapters.write_stamp(files, [out])
    return {"status": "converted", "sector": factors["sector"][0], "factors": dict(zip(factors["month"], factors["factor"])),
            "path": str(out)}


def month_factors() -> np.ndarray | None:
    """(13,) factor per calendar month (index 1-12), or None when not converted."""
    path = adapters.processed("datagovmy_month_factors.parquet")
    if not path.exists():
        return None
    frame = pl.read_parquet(path)
    factors = np.ones(13)
    for month, factor in zip(frame["month"], frame["factor"]):
        factors[int(month)] = float(factor)
    return factors
