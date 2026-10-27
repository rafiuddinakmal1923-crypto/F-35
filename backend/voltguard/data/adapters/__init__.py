"""Adapters for the current public datasets (prompt 3.2).

Each adapter converts its raw files under DATA_ROOT/raw/<source>/ to Parquet under
DATA_ROOT/processed/ once; later runs read only the Parquet, because files shared from a
Windows drive into Docker are read slowly. A stamp file records the raw files' sizes and
modification times, so a new download triggers one fresh conversion.
"""

from __future__ import annotations

import json
from pathlib import Path

from voltguard import config


def raw_dir(source: str) -> Path:
    path = config.data_root() / "raw" / source
    path.mkdir(parents=True, exist_ok=True)
    return path


def processed(name: str) -> Path:
    return config.data_path("processed", name)


def _stamp(files: list[Path]) -> dict:
    return {p.name: [p.stat().st_size, int(p.stat().st_mtime)] for p in sorted(files)}


def up_to_date(files: list[Path], outputs: list[Path]) -> bool:
    stamp_path = outputs[0].with_suffix(".stamp.json")
    if not all(p.exists() for p in outputs) or not stamp_path.exists():
        return False
    return json.loads(stamp_path.read_text(encoding="utf-8")) == _stamp(files)


def write_stamp(files: list[Path], outputs: list[Path]) -> None:
    outputs[0].with_suffix(".stamp.json").write_text(json.dumps(_stamp(files)), encoding="utf-8")
