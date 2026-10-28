#!/usr/bin/env bash
# Rebuild the hand-off material (graphify graph, TRACEABILITY.md, HANDOFF.md auto part).
# The logic lives in scripts/handoff.py so Windows and Linux run the same steps.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=python3
[[ -x .venv/bin/python ]] && PY=.venv/bin/python
exec "$PY" scripts/handoff.py
