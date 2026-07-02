"""Graph store: traversal and depth-2 edit-context assembly (spec/02 §2.4)."""

from __future__ import annotations

import json
from collections import defaultdict


class Graph:
    def __init__(self, nodes: list, edges: list):
        self.nodes = {n["id"]: n for n in nodes}
        self.out = defaultdict(list)  # id -> [(edge_type, target)]
        self.inc = defaultdict(list)  # id -> [(edge_type, source)]
        for a, t, b in edges:
            self.out[a].append((t, b))
            self.inc[b].append((t, a))

    @classmethod
    def load(cls, path: str) -> "Graph":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(data["nodes"], [tuple(e) for e in data["edges"]])

    def neighbors_out(self, node_id: str, edge_type: str | None = None) -> list:
        return [b for t, b in self.out[node_id] if edge_type is None or t == edge_type]

    def neighbors_in(self, node_id: str, edge_type: str | None = None) -> list:
        return [a for t, a in self.inc[node_id] if edge_type is None or t == edge_type]

    def edit_context(self, node_id: str) -> dict:
        """Context Loading Protocol, spec/02 §2.4.

        target + direct depends-on + constraints + tests + direct dependents.
        Neighbor nodes contribute signatures only, never bodies.
        """
        if node_id not in self.nodes:
            raise KeyError(node_id)
        return {
            "target": self.nodes[node_id],
            "depends_on": [self._stub(b) for b in self.neighbors_out(node_id, "depends-on")],
            "constraints": [self.nodes[b] for b in self.neighbors_out(node_id, "constrained-by")],
            "produces": [self._stub(b) for b in self.neighbors_out(node_id, "produces")],
            "tests": [self.nodes[a] for a in self.neighbors_in(node_id, "tests")],
            "dependents": [self._stub(a) for a in self.neighbors_in(node_id, "depends-on")],
        }

    def _stub(self, node_id: str) -> dict:
        """Signature-only view of a neighbor -- what crosses the context boundary."""
        n = self.nodes[node_id]
        stub = {"id": n["id"], "type": n["type"]}
        for key in ("signature", "fields", "exception", "statement"):
            if key in n:
                stub[key] = n[key]
        return stub
