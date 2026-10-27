"""Try to download the public datasets (prompt 3.2). Never blocks: on failure it prints manual steps.

    python scripts/fetch_datasets.py            # all sources
    python scripts/fetch_datasets.py datagovmy  # one source

Kaggle downloads need the `kaggle` package and an API token (%USERPROFILE%\\.kaggle\\kaggle.json
or KAGGLE_USERNAME / KAGGLE_KEY). Dataset slugs are set in config/data_sources.yaml under
`downloads` when the defaults below move. After downloading, the files are converted to Parquet
once (`python -m voltguard convert`). The demo runs fully offline without any of them.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("DATA_ROOT", ROOT / ".data"))

SOURCES = {
    "datagovmy": {
        "url": "https://storage.data.gov.my/energy/electricity_consumption.parquet",
        "file": "electricity_consumption.parquet",
        "manual": [
            "Open https://open.dosm.gov.my/data-catalogue/electricity_consumption",
            "Download the Parquet (or CSV) file",
            "Save it in {dir}",
        ],
    },
    "london": {
        "kaggle": "jeanmidev/smart-meters-in-london",
        "kaggle_files": ["halfhourly_dataset/halfhourly_dataset/block_0.csv"],
        "manual": [
            "Kaggle: search 'Smart meters in London' and download one half-hourly block CSV (e.g. block_0.csv),",
            "  or the London Datastore 'SmartMeter Energy Consumption Data in London Households' CSV",
            "  (https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households)",
            "Save the CSV in {dir} (a few hundred households are used by default)",
        ],
    },
    "sgcc": {
        "kaggle": "bensalem14/sgcc-dataset",
        "kaggle_files": [],
        "manual": [
            "Kaggle: search 'SGCC electricity theft' and download the CSV (CONS_NO, FLAG and one column per day)",
            "Save it in {dir}",
            "Set pattern_training: sgcc in config/data_sources.yaml, then run make.ps1 train",
        ],
    },
}


def manual(name: str, reason: str) -> None:
    folder = DATA_ROOT / "raw" / name
    print(f"  {name}: automatic download failed ({reason}). Manual steps:")
    for step in SOURCES[name]["manual"]:
        print(f"    - {step.format(dir=folder)}")


def fetch_url(name: str) -> bool:
    spec = SOURCES[name]
    folder = DATA_ROOT / "raw" / name
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / spec["file"]
    if target.exists():
        print(f"  {name}: already downloaded ({target})")
        return True
    try:
        with urllib.request.urlopen(spec["url"], timeout=60) as response, open(target.with_suffix(".part"), "wb") as out:
            shutil.copyfileobj(response, out)
        target.with_suffix(".part").rename(target)
        print(f"  {name}: downloaded {target}")
        return True
    except Exception as exc:  # network blocks, proxies and timeouts all end up here
        target.with_suffix(".part").unlink(missing_ok=True)
        manual(name, str(exc)[:120])
        return False


def fetch_kaggle(name: str) -> bool:
    spec = SOURCES[name]
    folder = DATA_ROOT / "raw" / name
    folder.mkdir(parents=True, exist_ok=True)
    if any(folder.glob("*.csv")):
        print(f"  {name}: CSV already present in {folder}")
        return True
    if shutil.which("kaggle") is None:
        manual(name, "the kaggle command is not installed (pip install kaggle) or no API token")
        return False
    cmd = ["kaggle", "datasets", "download", "-d", spec["kaggle"], "-p", str(folder), "--unzip"]
    try:
        if spec["kaggle_files"]:
            for file in spec["kaggle_files"]:
                subprocess.run(cmd[:5] + ["-f", file, "-p", str(folder)], check=True, timeout=1800)
            for archive in folder.glob("*.zip"):
                shutil.unpack_archive(archive, folder)
                archive.unlink()
        else:
            subprocess.run(cmd, check=True, timeout=1800)
        print(f"  {name}: downloaded into {folder}")
        return True
    except Exception as exc:
        manual(name, str(exc)[:120])
        return False


def apply_overrides() -> None:
    """`downloads: {london: <kaggle slug>, sgcc: <kaggle slug>}` in config/data_sources.yaml."""
    try:
        import yaml

        cfg = yaml.safe_load((ROOT / "config" / "data_sources.yaml").read_text(encoding="utf-8")) or {}
    except Exception:
        return
    for name, slug in (cfg.get("downloads") or {}).items():
        if name in SOURCES and "kaggle" in SOURCES[name] and slug:
            SOURCES[name]["kaggle"] = str(slug)


def main(argv: list[str]) -> int:
    apply_overrides()
    wanted = argv or list(SOURCES)
    print(f"DATA_ROOT = {DATA_ROOT}")
    results = {}
    for name in wanted:
        results[name] = fetch_url(name) if "url" in SOURCES[name] else fetch_kaggle(name)
    print("\nDownloaded: " + (", ".join(n for n, ok in results.items() if ok) or "none"))
    print("Offline mode needs none of these: the built-in generator and synthetic SGCC patterns are used instead.")
    if any(results.values()):
        print("Next: python -m voltguard convert   (converts raw files to Parquet once)")
    return 0  # never block setup on a download


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
