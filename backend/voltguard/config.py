"""Settings from environment variables and the YAML files in config/.

Environment variables hold machine and secret settings (.env.example lists them).
YAML files hold tunable defaults; admins override thresholds at runtime through the
`setting` table (FR-AD-03), which `thresholds()` merges on top of the file.
"""

from __future__ import annotations

import copy
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _env(name: str, default: str = "") -> str:
    """An empty value (e.g. `DATA_ROOT=` in .env) counts as unset, never as the current folder."""
    return os.environ.get(name) or default


def config_dir() -> Path:
    return Path(_env("VG_CONFIG_DIR", str(REPO_ROOT / "config")))


def data_root() -> Path:
    """Runtime data folder (datasets, uploads, photos, PDFs, logs, audit anchor, mlruns)."""
    root = Path(_env("DATA_ROOT", str(REPO_ROOT / ".data")))
    root.mkdir(parents=True, exist_ok=True)
    return root


def data_path(*parts: str) -> Path:
    path = data_root().joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def database_url() -> str:
    return _env("DATABASE_URL", "postgresql://voltguard:voltguard@localhost:5432/voltguard")


def admin_database_url() -> str:
    """Owner connection used for migrations and the pipeline (bypasses row-level security)."""
    return _env("ADMIN_DATABASE_URL", database_url())


def llm_mode() -> str:
    return _env("LLM_MODE", "mock").lower()


def report_mode() -> str:
    return _env("REPORT_MODE", "predrafted").lower()


def demo_mode() -> bool:
    return _env("DEMO_MODE", "1") == "1"


def jwt_secret() -> str:
    secret = _env("JWT_SECRET")
    if not secret:
        # Development fallback only; `make.ps1 demo` writes a random secret into .env.
        secret = "dev-only-change-me"
    return secret


def public_base_url() -> str:
    return _env("PUBLIC_BASE_URL", f"http://localhost:{_env('WEB_PORT', '8080')}").rstrip("/")


@lru_cache(maxsize=None)
def load_yaml(name: str) -> dict[str, Any]:
    path = config_dir() / name
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def thresholds(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Thresholds file, then tuned weights (if `tune` has run), then admin overrides."""
    merged = load_yaml("thresholds.yaml")
    tuned = tuned_weights_path()
    if tuned.exists():
        with tuned.open(encoding="utf-8") as handle:
            merged = deep_merge(merged, yaml.safe_load(handle) or {})
    return deep_merge(merged, overrides or {})


def tuned_weights_path() -> Path:
    """Output of `tune`, kept in the repository so the tuned weights travel with the code."""
    return config_dir() / "tuned_weights.yaml"


def data_sources() -> dict[str, Any]:
    return load_yaml("data_sources.yaml")


def demo_config() -> dict[str, Any]:
    return load_yaml("demo.yaml")
