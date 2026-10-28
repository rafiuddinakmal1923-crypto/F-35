"""Apply curated community names to the graphify graph without re-clustering.

    graphify update . --force                          # refresh the graph first
    <graphify python> scripts/graph_labels.py          # names from scripts/graph_labels.json

Run it with the Python that has graphify installed (for the uv tool:
`%APPDATA%\\uv\\tools\\graphifyy\\Scripts\\python.exe`). `graphify label` needs an LLM backend; without one,
communities are named after their busiest node ("get", "columns", ...). This script keeps the
communities exactly as `graphify update` built them and gives them readable names:

* names come from `scripts/graph_labels.json`, matched to a community by its key files and nodes, so
  they survive renumbering;
* a community that matches no rule keeps its current name;
* graph.json, GRAPH_REPORT.md, graph.html and the label sidecars are rewritten together, with the
  membership signatures, so a later `graphify update` keeps the names while the communities stay the same.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "graphify-out"
RULES = Path(__file__).with_name("graph_labels.json")


def community_index(raw: dict) -> dict[int, list[str]]:
    communities: dict[int, list[str]] = defaultdict(list)
    for node in raw["nodes"]:
        if node.get("community") is not None:
            communities[int(node["community"])].append(str(node["id"]))
    return {cid: communities[cid] for cid in sorted(communities)}


def describe(raw: dict, communities: dict[int, list[str]]) -> dict[int, dict]:
    """Per community: its main files (most nodes; ties all count) and node labels, for matching rules."""
    nodes = {str(n["id"]): n for n in raw["nodes"]}
    out = {}
    for cid, members in communities.items():
        files = Counter((nodes[m].get("source_file") or "").replace("\\", "/") for m in members if nodes[m].get("source_file"))
        most = max(files.values(), default=0)
        main_files = sorted(f for f, n in files.items() if n == most)
        out[cid] = {"files": main_files, "labels": {str(nodes[m].get("label") or m) for m in members}}
    return out


def match(rules: list[dict], info: dict) -> str | None:
    """First rule whose `file` is one of the community's main files and whose `has` labels are all present.
    When only one rule names a file, the file alone is enough (a community's busiest node changes as code grows)."""
    per_file = Counter(r.get("file") for r in rules)
    for strict in (True, False):
        for rule in rules:
            if rule.get("file") and not any(f.endswith(rule["file"]) for f in info["files"]):
                continue
            needs_has = strict or per_file[rule.get("file")] > 1
            if needs_has and any(h not in info["labels"] for h in rule.get("has", [])):
                continue
            return rule["name"]
    return None


def main() -> int:
    from graphify.analyze import god_nodes, suggest_questions, surprising_connections
    from graphify.build import build_from_json
    from graphify.cluster import community_member_sigs, score_all
    from graphify.detect import detect
    from graphify.export import to_html, to_json
    from graphify.exporters.html import _viz_node_limit
    from graphify.report import generate, load_learning_for_report
    from graphify.watch import _git_head, _report_root_label

    raw = json.loads((OUT / "graph.json").read_text(encoding="utf-8"))
    G = build_from_json(raw, directed=bool(raw.get("directed", False)))
    communities = community_index(raw)
    current = {int(k): v for k, v in json.loads((OUT / ".graphify_labels.json").read_text(encoding="utf-8")).items()}
    rules = json.loads(RULES.read_text(encoding="utf-8"))["rules"]
    info = describe(raw, communities)
    labels, named, kept = {}, 0, []
    for cid in sorted(communities):
        name = match(rules, info[cid])
        if name:
            named += 1
        else:
            kept.append(cid)
        labels[cid] = name or current.get(cid) or f"Community {cid}"
    # Two communities with the same name are told apart by their main file.
    seen = Counter(labels.values())
    for cid, name in list(labels.items()):
        if seen[name] > 1 and info[cid]["files"]:
            labels[cid] = f"{name} ({Path(info[cid]['files'][0]).name})"

    # Corpus line as `graphify update` writes it: the files the code graph is built from.
    detected = detect(ROOT, gitignore=True)
    detection = {"files": {"code": detected["files"]["code"], "document": [], "paper": [], "image": []},
                 "total_files": len(detected["files"]["code"]), "total_words": detected.get("total_words", 0)}
    cohesion = score_all(G, communities)
    gods = god_nodes(G)
    surprises = surprising_connections(G, communities)
    questions = suggest_questions(G, communities, labels)
    commit = raw.get("built_at_commit") or _git_head(cwd=ROOT)
    report = generate(G, communities, cohesion, labels, gods, surprises, detection, {"input": 0, "output": 0},
                      _report_root_label(ROOT), suggested_questions=questions, built_at_commit=commit,
                      learning=load_learning_for_report(OUT / "graph.json"))
    if not to_json(G, communities, str(OUT / "graph.json"), force=True, built_at_commit=commit, community_labels=labels):
        print("graph.json not written", file=sys.stderr)
        return 1
    (OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    (OUT / ".graphify_labels.json").write_text(
        json.dumps({str(k): v for k, v in sorted(labels.items())}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / ".graphify_labels.json.sig").write_text(
        json.dumps({str(k): v for k, v in community_member_sigs(communities).items()}), encoding="utf-8")
    limit = _viz_node_limit()
    if limit > 0:
        to_html(G, communities, str(OUT / "graph.html"), community_labels=labels, node_limit=limit)
    print(f"{len(communities)} communities: {named} named from rules, {len(kept)} kept their current name {kept}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
