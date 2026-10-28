"""Rebuild the hand-off material for the next session (run after every finished part).

  1. graphify code graph  -> graphify-out/ (graph.json, graph.html, GRAPH_REPORT.md)
  2. TRACEABILITY.md      -> requirement -> code -> tests
  3. HANDOFF.md auto part -> commit, test count, file tree, graph hubs

The hand-written part of HANDOFF.md (status, decisions, next steps) is kept as is.
Works on Windows and Linux: `python scripts/handoff.py` (make.ps1 handoff / make handoff).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], cwd: Path = ROOT, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def graphify_cmd() -> list[str]:
    exe = shutil.which("graphify")
    if exe:
        return [exe]
    venv = Path(sys.executable).with_name("graphify.exe" if sys.platform == "win32" else "graphify")
    if venv.exists():
        return [str(venv)]
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "graphifyy"], check=True)
    return [shutil.which("graphify") or str(venv)]


def update_graph() -> None:
    g = graphify_cmd()
    if run(g + ["update", ".", "--force"]).returncode != 0:
        run(g + ["update", "."], check=True)


def test_count() -> str:
    out = run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT / "backend").stdout
    total = sum(int(m) for m in re.findall(r": (\d+)$", out, re.M))
    if not total:
        m = re.search(r"(\d+) tests? collected", out)
        total = int(m.group(1)) if m else 0
    return f"{total} tests" if total else "n/a"


def file_tree() -> list[str]:
    files = run(["git", "ls-files", "-z"]).stdout.split("\0")
    files += run(["git", "ls-files", "-z", "--others", "--exclude-standard"]).stdout.split("\0")
    tree: dict[str, list[str]] = {}
    for f in sorted({f for f in files if f and not f.startswith("graphify-out/")}):
        parts = f.split("/")
        folder = "/".join(parts[:-1][:3]) or "."
        tree.setdefault(folder, []).append(parts[-1] if len(parts) <= 4 else "/".join(parts[3:]))
    lines = []
    for folder, names in tree.items():
        shown = ", ".join(names[:12]) + (f", ... (+{len(names) - 12})" if len(names) > 12 else "")
        lines.append(f"- `{folder}/`: {shown}")
    return lines


def update_handoff(tests: str) -> None:
    handoff = ROOT / "HANDOFF.md"
    text = handoff.read_text(encoding="utf-8") if handoff.exists() else "# Hand-off\n\n<!-- auto:start -->\n<!-- auto:end -->\n"
    head = run(["git", "log", "-1", "--format=%h %s"]).stdout.strip()
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    report = ROOT / "graphify-out" / "GRAPH_REPORT.md"
    graph = ""
    if report.exists():
        r = report.read_text(encoding="utf-8")
        summary = re.search(r"## Summary\n(.*?)\n\n", r, re.S)
        gods = re.search(r"## God Nodes.*?\n(.*?)\n\n", r, re.S)
        graph = (summary.group(1) if summary else "") + "\n\nMost connected (core abstractions):\n" + (gods.group(1) if gods else "")
    auto = f"""<!-- auto:start -->
## Auto-generated state (scripts/handoff.py)

- Generated: {datetime.now().isoformat(timespec='minutes')}
- Branch: `{branch}`; last commit: `{head}`
- Tests collected: {tests}
- Requirement coverage: see `TRACEABILITY.md`
- Code graph: `graphify-out/GRAPH_REPORT.md` (open `graphify-out/graph.html` in a browser;
  query with `graphify query "<question>"` or `graphify explain "<name>"`)

### Graph summary

{graph}

### File tree

{chr(10).join(file_tree())}
<!-- auto:end -->"""
    text = re.sub(r"<!-- auto:start -->.*?<!-- auto:end -->", lambda _: auto, text, flags=re.S)
    handoff.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    update_graph()
    subprocess.run([sys.executable, "scripts/traceability.py"], cwd=ROOT, check=True)
    update_handoff(test_count())
    print("Updated HANDOFF.md, TRACEABILITY.md and graphify-out/")


if __name__ == "__main__":
    main()
