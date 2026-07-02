"""Extract an AIL-2 semantic graph from Python source files.

Mapping (approximate by design -- this is a derived index, not a compiler):
  function / method          -> computation node
  class                      -> data node (fields from annotations + self.x in __init__)
  raise SomeError            -> event node (error subtype) + produces edge
  call to in-corpus function -> depends-on edge
  test_* function            -> test node + tests edge to called corpus functions

Resolution is name-based and conservative: a call resolves only when the name
maps to exactly one known corpus function in scope. Unresolved calls are
counted so the resolution rate is reported, never hidden.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class ExtractionResult:
    nodes: dict = field(default_factory=dict)  # id -> node dict
    edges: set = field(default_factory=set)  # (from, type, to)
    calls_total: int = 0
    calls_resolved: int = 0

    def to_graph(self) -> dict:
        return {
            "nodes": list(self.nodes.values()),
            "edges": sorted(self.edges),
            "stats": {
                "calls_total": self.calls_total,
                "calls_resolved": self.calls_resolved,
                "resolution_rate": round(self.calls_resolved / self.calls_total, 3)
                if self.calls_total
                else None,
            },
        }


def _signature_of(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> dict:
    args = [a.arg for a in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs]
    returns = ast.unparse(fn.returns) if fn.returns else None
    return {"inputs": args, "returns": returns}


def _class_fields(cls: ast.ClassDef) -> list:
    fields = []
    for stmt in cls.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            fields.append(stmt.target.id)
    for stmt in cls.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == "__init__":
            for sub in ast.walk(stmt):
                if (
                    isinstance(sub, ast.Assign)
                    and sub.targets
                    and isinstance(sub.targets[0], ast.Attribute)
                    and isinstance(sub.targets[0].value, ast.Name)
                    and sub.targets[0].value.id == "self"
                ):
                    fields.append(sub.targets[0].attr)
    return sorted(set(fields))


def _raised_names(fn: ast.AST) -> set:
    names = set()
    for sub in ast.walk(fn):
        if isinstance(sub, ast.Raise) and sub.exc is not None:
            target = sub.exc.func if isinstance(sub.exc, ast.Call) else sub.exc
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, ast.Attribute):
                names.add(target.attr)
    return names


def _called_names(fn: ast.AST) -> list:
    """(name, is_self_call) for every call expression inside fn."""
    calls = []
    for sub in ast.walk(fn):
        if not isinstance(sub, ast.Call):
            continue
        f = sub.func
        if isinstance(f, ast.Name):
            calls.append((f.id, False))
        elif isinstance(f, ast.Attribute):
            is_self = isinstance(f.value, ast.Name) and f.value.id == "self"
            calls.append((f.attr, is_self))
    return calls


class _ModuleFunctions(ast.NodeVisitor):
    """Collect every function with its qualname and enclosing class."""

    def __init__(self):
        self.functions = []  # (qualname, class_name | None, ast node)
        self._stack = []

    def visit_ClassDef(self, node: ast.ClassDef):
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def _visit_fn(self, node):
        qual = ".".join(self._stack + [node.name])
        cls = self._stack[-1] if self._stack else None
        self.functions.append((qual, cls, node))
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    visit_FunctionDef = _visit_fn
    visit_AsyncFunctionDef = _visit_fn


def extract(sources: dict) -> ExtractionResult:
    """sources: {module_name: source_text} -> semantic graph."""
    result = ExtractionResult()
    per_module = {}  # module -> {short_name: [node_ids]}
    fn_nodes = []  # (node_id, module, class_name, ast node)

    for module, text in sources.items():
        tree = ast.parse(text)
        collector = _ModuleFunctions()
        collector.visit(tree)
        name_index = {}
        for qual, cls, fn in collector.functions:
            is_test = fn.name.startswith("test_")
            node_id = ("tn:" if is_test else "sn:") + f"{module}.{qual}"
            result.nodes[node_id] = {
                "id": node_id,
                "type": "test" if is_test else "computation",
                "module": module,
                "qualname": qual,
                "signature": _signature_of(fn),
                "lineno": fn.lineno,
                "end_lineno": fn.end_lineno,
            }
            name_index.setdefault(fn.name, []).append(node_id)
            if cls:
                name_index.setdefault(f"{cls}.{fn.name}", []).append(node_id)
            fn_nodes.append((node_id, module, cls, fn))

        for stmt in ast.walk(tree):
            if isinstance(stmt, ast.ClassDef):
                did = f"dn:{module}.{stmt.name}"
                result.nodes[did] = {
                    "id": did,
                    "type": "data",
                    "module": module,
                    "qualname": stmt.name,
                    "fields": _class_fields(stmt),
                    "lineno": stmt.lineno,
                    "end_lineno": stmt.end_lineno,
                }
        per_module[module] = name_index

    _link(result, per_module, fn_nodes)
    return result


def _link(result: ExtractionResult, per_module: dict, fn_nodes: list) -> None:
    for node_id, module, cls, fn in fn_nodes:
        for exc in _raised_names(fn):
            ev_id = f"ev:{exc}"
            result.nodes.setdefault(
                ev_id, {"id": ev_id, "type": "event", "event_subtype": "error", "exception": exc}
            )
            result.edges.add((node_id, "produces", ev_id))

        edge_type = "tests" if result.nodes[node_id]["type"] == "test" else "depends-on"
        for name, is_self in _called_names(fn):
            result.calls_total += 1
            lookup = f"{cls}.{name}" if (is_self and cls) else name
            candidates = per_module[module].get(lookup, [])
            if not candidates and not is_self:  # cross-module: unique global match
                candidates = [
                    nid
                    for mod, idx in per_module.items()
                    if mod != module
                    for nid in idx.get(name, [])
                ]
            if len(candidates) == 1 and candidates[0] != node_id:
                result.calls_resolved += 1
                result.edges.add((node_id, edge_type, candidates[0]))
