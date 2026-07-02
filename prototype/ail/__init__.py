"""AIL-2 Phase-1 prototype: semantic graph as a derived index over Python source.

Stdlib-only. Three modules:
  extract  - Python AST -> semantic graph (nodes + typed edges)
  store    - graph loading, traversal, depth-2 edit-context assembly
  measure  - input-token comparison: edit context vs. whole-file baselines
"""

__version__ = "0.1.0"
