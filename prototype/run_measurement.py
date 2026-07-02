"""Run the Phase-1 measurement over real Python stdlib modules.

Corpus: Python standard library source files -- real, non-trivial code that
ships with every Python install, so the experiment is reproducible offline.

Usage:  python run_measurement.py [output_path]
"""

from __future__ import annotations

import importlib
import inspect
import json
import platform
import sys
from datetime import date

from ail import measure
from ail.extract import extract
from ail.store import Graph

CORPUS_MODULES = [
    "argparse",
    "configparser",
    "json.decoder",
    "json.encoder",
    "json.scanner",
    "http.client",
    "urllib.parse",
    "email.message",
]


def load_corpus() -> dict:
    sources = {}
    for name in CORPUS_MODULES:
        module = importlib.import_module(name)
        sources[name] = inspect.getsource(module)
    return sources


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "results/measurement-results.json"
    sources = load_corpus()
    extraction = extract(sources)
    graph_data = extraction.to_graph()
    graph = Graph(graph_data["nodes"], graph_data["edges"])
    results = measure.run(graph, sources)

    report = {
        "experiment": "AIL-2 Phase 1 pilot: input tokens, depth-2 edit context vs whole-file",
        "date": date.today().isoformat(),
        "python": platform.python_version(),
        "corpus": CORPUS_MODULES,
        "corpus_stats": {
            "total_source_tokens": sum(measure.count_tokens(s) for s in sources.values()),
            "graph_nodes": len(graph_data["nodes"]),
            "graph_edges": len(graph_data["edges"]),
            "call_resolution": graph_data["stats"],
        },
        "caveats": [
            "Token counts use a word/punct regex proxy, not a BPE tokenizer; only ratios are meaningful.",
            "Call resolution is name-based; unresolved calls mean some depends-on edges are missing, which UNDERSTATES the ail context size. See resolution_rate.",
            "No constraint/ontology nodes exist in extracted Python -- the ail context is signatures+events+tests only. Real AIL contexts would be somewhat larger.",
            "This is a pilot on stdlib modules, not the >=50-task multi-codebase validation demanded by spec/05 §5.2.",
        ],
        "results": results,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    r = results
    print(f"corpus: {len(sources)} modules, {report['corpus_stats']['total_source_tokens']:,} source tokens")
    print(f"graph:  {report['corpus_stats']['graph_nodes']} nodes, {report['corpus_stats']['graph_edges']} edges, "
          f"call resolution {graph_data['stats']['resolution_rate']}")
    print(f"edit targets: {r['n_edit_targets']}")
    print(f"ail context tokens: median {r['ail_tokens']['median']}, mean {r['ail_tokens']['mean']}, max {r['ail_tokens']['max']}")
    print(f"vs whole file:        median reduction {r['ail_vs_whole_file']['median_reduction_factor']}x "
          f"(median ratio {r['ail_vs_whole_file']['median_ratio']})")
    print(f"vs file+imports:      median reduction {r['ail_vs_file_plus_imports']['median_reduction_factor']}x "
          f"(median ratio {r['ail_vs_file_plus_imports']['median_ratio']})")
    print(f"written: {out_path}")


if __name__ == "__main__":
    main()
