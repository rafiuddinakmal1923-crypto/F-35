"""SGCC electricity-theft adapter (prompt 3.2): daily kWh per customer plus a theft flag.

Used only to train the pattern model (SDD 5.4). Raw file in DATA_ROOT/raw/sgcc/ (CSV): one row
per customer with CONS_NO, FLAG (1 = theft) and one column per day (e.g. 2014/1/1).
Output processed/sgcc_windows.parquet: up to four 28-day windows per customer (columns d0..d27, flag,
customer), chosen at random among windows with at least half the days present; missing days stay null
and the pattern features fill them with the window mean.
"""

from __future__ import annotations

import re

import numpy as np
import polars as pl

from voltguard.data import adapters
from voltguard.detection.pattern import WINDOW_DAYS

WINDOWS_PER_CUSTOMER = 4

# Day columns: year first (2014/1/1) or year last (1/13/2014, 01/01/2014, as in the Kaggle copies).
DATE_COLUMN = re.compile(r"^(\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})$")


def _parts(col: str) -> list[int]:
    return [int(x) for x in re.split(r"[/-]", col.strip())]


def _sort_key(col: str, day_first: bool = False) -> tuple[int, int, int]:
    a, b, c = _parts(col)
    if a > 31:                      # year first
        return a, b, c
    return (c, b, a) if day_first else (c, a, b)


def _day_first(columns: list[str]) -> bool:
    """Year-last columns are month-first (1/13/2014) unless a first part above 12 shows day-first."""
    return any(_parts(c)[0] > 12 for c in columns if _parts(c)[0] <= 31)


def convert(force: bool = False, seed: int = 5) -> dict | None:
    files = sorted(adapters.raw_dir("sgcc").glob("*.csv"))
    out = adapters.processed("sgcc_windows.parquet")
    if not files:
        return None
    if not force and adapters.up_to_date(files, [out]):
        return {"status": "up to date", "path": str(out)}
    frames = []
    for p in files:
        part = pl.read_csv(p, infer_schema=False)
        # Normalise day columns to Y/M/D, so copies that write dates differently line up.
        raw_days = [c for c in part.columns if DATE_COLUMN.match(c.strip())]
        day_first = _day_first([c for c in raw_days if _parts(c)[0] <= 31])
        part = part.rename({c: "{}/{}/{}".format(*_sort_key(c, day_first)) for c in raw_days})
        frames.append(part)
    frame = pl.concat(frames, how="diagonal_relaxed")
    flag_col = next((c for c in frame.columns if c.strip().upper() == "FLAG"), None)
    if flag_col is None:
        raise ValueError("SGCC file needs a FLAG column")
    id_col = next((c for c in frame.columns if c.strip().upper() == "CONS_NO"), None)
    if id_col is not None:
        # A smaller copy of the same dataset in the folder must not count customers twice.
        frame = frame.unique(subset=[id_col], keep="first", maintain_order=True)
    days = sorted((c for c in frame.columns if DATE_COLUMN.match(c.strip())), key=_sort_key)
    if len(days) < WINDOW_DAYS:
        raise ValueError(f"SGCC file has {len(days)} day columns; need at least {WINDOW_DAYS}")
    values = frame.select([pl.col(c).cast(pl.Float64, strict=False) for c in days]).to_numpy()
    flags = frame[flag_col].cast(pl.Int64, strict=False).to_numpy()
    rng = np.random.default_rng(seed)
    rows, labels, customers = [], [], []
    for customer, (row, flag) in enumerate(zip(values, flags)):
        if flag not in (0, 1):
            continue
        starts = [s for s in range(0, len(days) - WINDOW_DAYS + 1, 7) if np.isfinite(row[s:s + WINDOW_DAYS]).mean() >= 0.5]
        if not starts:
            continue
        # Several windows per customer: more training rows; the model's hold-out is split by customer.
        for s in rng.choice(starts, size=min(WINDOWS_PER_CUSTOMER, len(starts)), replace=False):
            rows.append(row[int(s):int(s) + WINDOW_DAYS])
            labels.append(int(flag))
            customers.append(customer)
    if not rows:
        raise ValueError("No usable SGCC windows (too many missing days)")
    data = np.array(rows)
    windows = pl.DataFrame({f"d{i}": data[:, i] for i in range(WINDOW_DAYS)}).with_columns(
        pl.all().fill_nan(None)).with_columns(pl.Series("flag", labels), pl.Series("customer", customers))
    windows.write_parquet(out)
    adapters.write_stamp(files, [out])
    return {"status": "converted", "customers": len(set(customers)), "windows": len(labels),
            "theft_share": round(float(np.mean(labels)), 4), "path": str(out)}
