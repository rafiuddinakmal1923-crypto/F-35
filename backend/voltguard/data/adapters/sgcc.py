"""SGCC electricity-theft adapter (prompt 3.2): daily kWh per customer plus a theft flag.

Used only to train the pattern model (SDD 5.4). Raw files in DATA_ROOT/raw/sgcc/ (CSV): one row
per customer with CONS_NO, FLAG (1 = theft) and one column per day. Day columns may be written
year first (2014/1/1, 2014-01-01) or month first as in the Kaggle copy (1/1/2014, 01/13/2014); a file
whose first part goes above 12 is read day first. When several files hold the same customers (the
Kaggle "datasetsmall.csv" is a 28-day extract of "data set.csv"), each customer is taken once, from
the file with the most days.

Output processed/sgcc_windows.parquet: one 28-day window per customer (columns d0..d27, flag),
chosen at random among windows with at least half the days present; missing days stay null
and the pattern features fill them with the window mean.
"""

from __future__ import annotations

import re
from datetime import date

import numpy as np
import polars as pl

from voltguard.data import adapters
from voltguard.detection.pattern import WINDOW_DAYS

YEAR_FIRST = re.compile(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$")
YEAR_LAST = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$")


def day_columns(columns: list[str]) -> dict[str, date]:
    """Day column name -> date, for either year-first or year-last names (month first unless a part > 12)."""
    first = {c: YEAR_FIRST.match(c.strip()) for c in columns}
    out = {c: date(int(m[1]), int(m[2]), int(m[3])) for c, m in first.items() if m}
    last = {c: YEAR_LAST.match(c.strip()) for c in columns if c not in out}
    last = {c: m for c, m in last.items() if m}
    if last:
        day_first = any(int(m[1]) > 12 for m in last.values())
        for c, m in last.items():
            a, b, y = int(m[1]), int(m[2]), int(m[3])
            out[c] = date(y, b, a) if day_first else date(y, a, b)
    return out


def _id_column(columns: list[str]) -> str | None:
    return next((c for c in columns if c.strip().upper() in ("CONS_NO", "CUSTOMER", "CUSTOMER_ID")), None)


def convert(force: bool = False, seed: int = 5) -> dict | None:
    files = sorted(adapters.raw_dir("sgcc").glob("*.csv"))
    out = adapters.processed("sgcc_windows.parquet")
    if not files:
        return None
    if not force and adapters.up_to_date(files, [out]):
        return {"status": "up to date", "path": str(out)}
    frames = []
    for path in files:
        frame = pl.read_csv(path, infer_schema=False)
        flag_col = next((c for c in frame.columns if c.strip().upper() == "FLAG"), None)
        if flag_col is None:
            raise ValueError(f"{path.name}: SGCC file needs a FLAG column")
        days = day_columns(frame.columns)
        id_col = _id_column(frame.columns)
        frame = frame.select(
            (pl.col(id_col) if id_col else pl.lit(None, dtype=pl.Utf8)).alias("customer"),
            pl.col(flag_col).alias("flag"),
            *[pl.col(c).alias(d.isoformat()) for c, d in days.items()])
        frames.append((len(days), path.name, frame))
    # The file with the most days first; a customer already taken is not read again from a smaller extract.
    frames.sort(key=lambda f: -f[0])
    seen: set[str] = set()
    parts = []
    for _, _, frame in frames:
        if frame["customer"].null_count() < frame.height:
            frame = frame.filter(~pl.col("customer").is_in(sorted(seen)))
            seen |= set(frame["customer"].drop_nulls().to_list())
        parts.append(frame)
    combined = pl.concat(parts, how="diagonal_relaxed")
    day_names = sorted(c for c in combined.columns if c not in ("customer", "flag"))
    if len(day_names) < WINDOW_DAYS:
        raise ValueError(f"SGCC files have {len(day_names)} day columns; need at least {WINDOW_DAYS}")
    values = combined.select([pl.col(c).cast(pl.Float64, strict=False) for c in day_names]).to_numpy()
    flags = combined["flag"].cast(pl.Int64, strict=False).to_numpy()
    rng = np.random.default_rng(seed)
    rows, labels = [], []
    for row, flag in zip(values, flags):
        if flag not in (0, 1):
            continue
        starts = [s for s in range(0, len(day_names) - WINDOW_DAYS + 1, 7) if np.isfinite(row[s:s + WINDOW_DAYS]).mean() >= 0.5]
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
    return {"status": "converted", "customers": len(labels), "theft_share": round(float(np.mean(labels)), 4),
            "days": len(day_names), "files": [name for _, name, _ in frames], "path": str(out)}
