"""SGCC electricity-theft adapter (prompt 3.2): daily kWh per customer plus a theft flag.

Used only to train the pattern model (SDD 5.4). Raw file in DATA_ROOT/raw/sgcc/ (CSV): one row
per customer with CONS_NO, FLAG (1 = theft) and one column per day (e.g. 2014/1/1).
Output processed/sgcc_windows.parquet: one 28-day window per customer (columns d0..d27, flag),
chosen at random among windows with at least half the days present; missing days stay null
and the pattern features fill them with the window mean.
"""

from __future__ import annotations

import re

import numpy as np
import polars as pl

from voltguard.data import adapters
from voltguard.detection.pattern import WINDOW_DAYS

DATE_COLUMN = re.compile(r"^\d{4}[/-]\d{1,2}[/-]\d{1,2}$")


def _sort_key(col: str) -> tuple[int, int, int]:
    y, m, d = (int(x) for x in re.split(r"[/-]", col))
    return y, m, d


def convert(force: bool = False, seed: int = 5) -> dict | None:
    files = sorted(adapters.raw_dir("sgcc").glob("*.csv"))
    out = adapters.processed("sgcc_windows.parquet")
    if not files:
        return None
    if not force and adapters.up_to_date(files, [out]):
        return {"status": "up to date", "path": str(out)}
    frame = pl.concat([pl.read_csv(p, infer_schema=False) for p in files], how="diagonal_relaxed")
    flag_col = next((c for c in frame.columns if c.strip().upper() == "FLAG"), None)
    if flag_col is None:
        raise ValueError("SGCC file needs a FLAG column")
    days = sorted((c for c in frame.columns if DATE_COLUMN.match(c.strip())), key=_sort_key)
    if len(days) < WINDOW_DAYS:
        raise ValueError(f"SGCC file has {len(days)} day columns; need at least {WINDOW_DAYS}")
    values = frame.select([pl.col(c).cast(pl.Float64, strict=False) for c in days]).to_numpy()
    flags = frame[flag_col].cast(pl.Int64, strict=False).to_numpy()
    rng = np.random.default_rng(seed)
    rows, labels = [], []
    for row, flag in zip(values, flags):
        if flag not in (0, 1):
            continue
        starts = [s for s in range(0, len(days) - WINDOW_DAYS + 1, 7) if np.isfinite(row[s:s + WINDOW_DAYS]).mean() >= 0.5]
        if not starts:
            continue
        s = int(rng.choice(starts))
        rows.append(row[s:s + WINDOW_DAYS])
        labels.append(int(flag))
    if not rows:
        raise ValueError("No usable SGCC windows (too many missing days)")
    data = np.array(rows)
    windows = pl.DataFrame({f"d{i}": data[:, i] for i in range(WINDOW_DAYS)}).with_columns(
        pl.all().fill_nan(None)).with_columns(pl.Series("flag", labels))
    windows.write_parquet(out)
    adapters.write_stamp(files, [out])
    return {"status": "converted", "customers": len(labels), "theft_share": round(float(np.mean(labels)), 4), "path": str(out)}
