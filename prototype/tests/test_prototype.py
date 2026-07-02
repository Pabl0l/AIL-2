"""Tests for the Phase-1 prototype. Run:  python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ail import measure
from ail.extract import extract
from ail.store import Graph

SAMPLE = '''
class Account:
    def __init__(self, owner):
        self.owner = owner
        self.balance = 0

def validate(amount):
    if amount < 0:
        raise ValueError("negative")
    return True

def deposit(account, amount):
    validate(amount)
    account.balance += amount
    return account

def test_deposit():
    acc = Account("a")
    deposit(acc, 10)
'''


def build():
    sources = {"sample": SAMPLE}
    data = extract(sources).to_graph()
    return sources, data, Graph(data["nodes"], data["edges"])


class TestExtract(unittest.TestCase):
    def test_node_types_extracted(self):
        _, data, _ = build()
        types = {n["type"] for n in data["nodes"]}
        self.assertEqual(types, {"computation", "data", "event", "test"})

    def test_function_becomes_computation_node(self):
        _, data, graph = build()
        self.assertIn("sn:sample.deposit", graph.nodes)
        self.assertEqual(graph.nodes["sn:sample.deposit"]["signature"]["inputs"], ["account", "amount"])

    def test_class_becomes_data_node_with_fields(self):
        _, _, graph = build()
        self.assertEqual(graph.nodes["dn:sample.Account"]["fields"], ["balance", "owner"])

    def test_call_becomes_depends_on_edge(self):
        _, _, graph = build()
        self.assertIn("sn:sample.validate", graph.neighbors_out("sn:sample.deposit", "depends-on"))

    def test_raise_becomes_error_event_with_produces_edge(self):
        _, _, graph = build()
        self.assertIn("ev:ValueError", graph.neighbors_out("sn:sample.validate", "produces"))
        self.assertEqual(graph.nodes["ev:ValueError"]["event_subtype"], "error")

    def test_test_function_becomes_test_node_with_tests_edge(self):
        _, _, graph = build()
        self.assertIn("sn:sample.deposit", graph.neighbors_out("tn:sample.test_deposit", "tests"))


class TestStore(unittest.TestCase):
    def test_edit_context_shape(self):
        _, _, graph = build()
        ctx = graph.edit_context("sn:sample.deposit")
        self.assertEqual(ctx["target"]["id"], "sn:sample.deposit")
        self.assertEqual([d["id"] for d in ctx["depends_on"]], ["sn:sample.validate"])
        self.assertEqual([t["id"] for t in ctx["tests"]], ["tn:sample.test_deposit"])

    def test_neighbor_stubs_have_no_body_locations(self):
        _, _, graph = build()
        ctx = graph.edit_context("sn:sample.deposit")
        for stub in ctx["depends_on"] + ctx["dependents"]:
            self.assertNotIn("lineno", stub)

    def test_dependents_are_reverse_depends_on(self):
        _, _, graph = build()
        ctx = graph.edit_context("sn:sample.validate")
        self.assertEqual([d["id"] for d in ctx["dependents"]], ["sn:sample.deposit"])

    def test_unknown_node_raises(self):
        _, _, graph = build()
        with self.assertRaises(KeyError):
            graph.edit_context("sn:nope")


class TestMeasure(unittest.TestCase):
    def test_token_proxy_counts_words_and_punct(self):
        self.assertEqual(measure.count_tokens("a = b(1)"), 6)

    def test_context_envelope_has_fixed_overhead(self):
        # On a tiny file the context EXCEEDS the file: the JSON envelope has
        # fixed overhead, so AIL only wins above a file-size threshold.
        # The stdlib measurement shows the crossover is far below real file sizes.
        sources, _, graph = build()
        ail = measure.ail_context_tokens(graph, "sn:sample.deposit", sources)
        self.assertGreater(ail, measure.count_tokens(SAMPLE))

    def test_run_reports_edit_targets(self):
        sources, _, graph = build()
        results = measure.run(graph, sources)
        self.assertEqual(results["n_edit_targets"], 1)
        self.assertEqual(results["per_node"][0]["node"], "sn:sample.deposit")


if __name__ == "__main__":
    unittest.main()
