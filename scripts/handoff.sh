#!/usr/bin/env bash
# Rebuild the hand-off material for the next session (run after every finished part):
#   1. graphify code graph  -> graphify-out/ (graph.json, graph.html, GRAPH_REPORT.md)
#   2. TRACEABILITY.md      -> requirement -> code -> tests
#   3. HANDOFF.md auto part -> commit, test count, file tree, graph hubs
# The hand-written part of HANDOFF.md (status, decisions, next steps) is kept as is.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=python3
[[ -x .venv/bin/python ]] && PY=.venv/bin/python
if ! command -v graphify >/dev/null 2>&1 && [[ ! -x .venv/bin/graphify ]]; then
  "$PY" -m pip install -q graphifyy
fi
GRAPHIFY=graphify
[[ -x .venv/bin/graphify ]] && GRAPHIFY=.venv/bin/graphify

"$GRAPHIFY" update . --force >/dev/null 2>&1 || "$GRAPHIFY" update . >/dev/null
"$PY" scripts/traceability.py

tests="$(cd backend && "../$PY" -m pytest --collect-only -q 2>/dev/null | awk -F': ' '/: [0-9]+$/ {s+=$2} END {if (s) print s " tests"}' || true)"
"$PY" - "$tests" <<'PYEOF'
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

root = Path(".")
handoff = root / "HANDOFF.md"
text = handoff.read_text(encoding="utf-8") if handoff.exists() else "# Hand-off\n\n<!-- auto:start -->\n<!-- auto:end -->\n"
head = subprocess.run(["git", "log", "-1", "--format=%h %s"], capture_output=True, text=True).stdout.strip()
branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
files = subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True).stdout.split("\0")
files += subprocess.run(["git", "ls-files", "-z", "--others", "--exclude-standard"], capture_output=True, text=True).stdout.split("\0")
files = [f for f in files if f]

tree: dict[str, list[str]] = {}
for f in sorted(set(files)):
    if f.startswith("graphify-out/"):
        continue
    parts = f.split("/")
    folder = "/".join(parts[:-1][:3]) or "."
    tree.setdefault(folder, []).append(parts[-1] if len(parts) <= 4 else "/".join(parts[3:]))
tree_lines = []
for folder, names in tree.items():
    shown = ", ".join(names[:12]) + (f", ... (+{len(names) - 12})" if len(names) > 12 else "")
    tree_lines.append(f"- `{folder}/`: {shown}")

report = root / "graphify-out" / "GRAPH_REPORT.md"
graph = ""
if report.exists():
    r = report.read_text(encoding="utf-8")
    summary = re.search(r"## Summary\n(.*?)\n\n", r, re.S)
    gods = re.search(r"## God Nodes.*?\n(.*?)\n\n", r, re.S)
    graph = (summary.group(1) if summary else "") + "\n\nMost connected (core abstractions):\n" + (gods.group(1) if gods else "")

auto = f"""<!-- auto:start -->
## Auto-generated state (scripts/handoff.sh)

- Generated: {datetime.now().isoformat(timespec='minutes')}
- Branch: `{branch}`; last commit: `{head}`
- Tests collected: {sys.argv[1] or 'n/a'}
- Requirement coverage: see `TRACEABILITY.md`
- Code graph: `graphify-out/GRAPH_REPORT.md` (open `graphify-out/graph.html` in a browser;
  query with `graphify query "<question>"` or `graphify explain "<name>"`)

### Graph summary

{graph}

### File tree

{chr(10).join(tree_lines)}
<!-- auto:end -->"""
text = re.sub(r"<!-- auto:start -->.*?<!-- auto:end -->", lambda _: auto, text, flags=re.S)
handoff.write_text(text, encoding="utf-8")
print("Updated HANDOFF.md, TRACEABILITY.md and graphify-out/")
PYEOF
