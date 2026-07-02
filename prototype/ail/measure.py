"""Input-token measurement: depth-2 edit context vs. whole-file baselines.

For every computation node that has at least one resolved depends-on edge
(a realistic edit target), compare the tokens an agent must load:

  ail      - target's own source + edit context (neighbor signatures, events,
             tests, dependents) rendered as compact JSON
  file     - the whole source file containing the target (common practice:
             "open the file")
  closure  - the file plus every other corpus file it imports (what an agent
             loads when it also opens the imports)

Token counting uses a word/punctuation proxy (regex split). It is NOT a real
BPE tokenizer; both sides of every comparison use the same proxy, so ratios
are meaningful even though absolute counts are approximate.
"""

from __future__ import annotations

import ast
import json
import re
import statistics

_TOKEN_RE = re.compile(r"\w+|[^\w\s]")


def count_tokens(text: str) -> int:
    return len(_TOKEN_RE.findall(text))


def node_source(node: dict, sources: dict) -> str:
    lines = sources[node["module"]].splitlines()
    return "\n".join(lines[node["lineno"] - 1 : node["end_lineno"]])


def ail_context_tokens(graph, node_id: str, sources: dict) -> int:
    ctx = graph.edit_context(node_id)
    target_src = node_source(ctx["target"], sources)
    payload = {k: v for k, v in ctx.items() if k != "target"}
    payload["target"] = {"id": node_id, "signature": ctx["target"]["signature"]}
    return count_tokens(target_src) + count_tokens(json.dumps(payload, separators=(",", ":")))


def _import_closure(module: str, sources: dict) -> set:
    """Corpus-internal modules imported by `module` (depth-1)."""
    imported = set()
    for stmt in ast.walk(ast.parse(sources[module])):
        if isinstance(stmt, ast.Import):
            names = [a.name for a in stmt.names]
        elif isinstance(stmt, ast.ImportFrom) and stmt.module:
            names = [stmt.module] + [f"{stmt.module}.{a.name}" for a in stmt.names]
        else:
            continue
        for name in names:
            for candidate in (name, name.split(".")[0]):
                if candidate in sources and candidate != module:
                    imported.add(candidate)
    return imported


def run(graph, sources: dict) -> dict:
    file_tokens = {m: count_tokens(text) for m, text in sources.items()}
    closure_tokens = {
        m: file_tokens[m] + sum(file_tokens[i] for i in _import_closure(m, sources))
        for m in sources
    }

    per_node, ratios_file, ratios_closure = [], [], []
    for node_id, node in graph.nodes.items():
        if node["type"] != "computation" or not graph.neighbors_out(node_id, "depends-on"):
            continue
        ail = ail_context_tokens(graph, node_id, sources)
        fil = file_tokens[node["module"]]
        clo = closure_tokens[node["module"]]
        per_node.append(
            {"node": node_id, "ail_tokens": ail, "file_tokens": fil, "closure_tokens": clo}
        )
        ratios_file.append(ail / fil)
        ratios_closure.append(ail / clo)

    def summary(ratios: list) -> dict:
        return {
            "mean_ratio": round(statistics.mean(ratios), 4),
            "median_ratio": round(statistics.median(ratios), 4),
            "p90_ratio": round(sorted(ratios)[int(0.9 * (len(ratios) - 1))], 4),
            "mean_reduction_factor": round(1 / statistics.mean(ratios), 1),
            "median_reduction_factor": round(1 / statistics.median(ratios), 1),
        }

    return {
        "n_edit_targets": len(per_node),
        "ail_vs_whole_file": summary(ratios_file),
        "ail_vs_file_plus_imports": summary(ratios_closure),
        "ail_tokens": {
            "mean": round(statistics.mean(p["ail_tokens"] for p in per_node)),
            "median": statistics.median(p["ail_tokens"] for p in per_node),
            "max": max(p["ail_tokens"] for p in per_node),
        },
        "per_node": sorted(per_node, key=lambda p: p["node"]),
    }
