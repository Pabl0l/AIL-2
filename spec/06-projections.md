# 06. Projections: What Survives When AI Writes All Code

## Overview

This section answers the project's final question: what percentage of current programming constructs survives in a world where AI writes, reads, and modifies all code? Each construct receives one of three fates, consistent with the verdicts in section 01:

- **SURVIVES** — computationally necessary in unchanged or near-unchanged form
- **TRANSFORMS** — the underlying need survives; the human-facing form does not
- **DIES** — existed only for human cognition; no computational residue

Percentages are weighted by how much of a typical codebase's token mass each construct occupies (using the baseline distribution from section 03).

---

## 6.1 Construct-by-Construct Fate

| Construct | Fate | What remains |
|---|---|---|
| Type systems | **SURVIVES** | Strengthened — types become the primary compatibility mechanism (edge type-checking) |
| Code reuse (functions as units) | **SURVIVES** | As computation nodes; reuse is computational necessity |
| Tests | **SURVIVES** | As data (given/expect nodes), not code — form changes, function intact |
| Compilation & IR toolchains | **SURVIVES** | LLVM/Cranelift/WASM pipelines work unchanged downstream of the graph |
| APIs / external contracts | **SURVIVES** | As boundary nodes; the boundary is where human-readable naming remains justified |
| Transactions, concurrency control | **SURVIVES** | Unchanged need; representation still unspecified (see 5.4) |
| Access control / encapsulation | **SURVIVES** | As directional edge constraints, not `private` keywords |
| Variable/function names | TRANSFORMS | Aliases in metadata; identity is content-addressed |
| Functions as *named* text units | TRANSFORMS | Computation nodes with typed signatures |
| Classes (data grouping) | TRANSFORMS | Data nodes (schema only, no behavior) |
| Polymorphism | TRANSFORMS | `dispatches-to` edges instead of vtables/inheritance |
| Interfaces | TRANSFORMS | Constraint nodes + signature matching |
| Exceptions | TRANSFORMS | Error-subtype event nodes + handler edges |
| Version control (Git) | TRANSFORMS | Semantic snapshots + deltas; the *need* for history survives fully |
| Code review | TRANSFORMS | Human sign-off gate over semantic deltas + generated projections (see 5.7) |
| Documentation | TRANSFORMS | Ontology nodes (input) + generated prose (output) |
| Design patterns | TRANSFORMS | ~80% were workarounds for language limitations; the rest become graph shapes (observer = produces/consumes edges) |
| DRY / SOLID principles | TRANSFORMS | From discipline to structure: dedup and dependency direction are graph properties, not habits |
| Inheritance hierarchies | **DIES** | Composition edges + dispatch edges cover the computational residue |
| Files | **DIES** | No computational role; storage is the graph |
| Folders / directory trees | **DIES** | Multiple orthogonal groupings via edges replace the single hierarchy |
| Explanatory comments | **DIES** | Constraints become nodes; the rest was narration |
| Import/require statements | **DIES** | Explicit `depends-on` edges; no path resolution |
| Getters/setters/constructors | **DIES** | Pure ceremony; data nodes are their schemas |
| Naming conventions & style guides | **DIES** | Nothing to style; canonical serialization is deterministic |
| Text diffs & merge conflicts on lines | **DIES** | Semantic deltas; conflicts occur on nodes, which are coherent units |
| grep / text search as navigation | **DIES** | Hash lookup, typed traversal, semantic search |

---

## 6.2 The Number

Weighted by token mass in a typical codebase (section 03 baseline):

| Fate | Share of current construct mass |
|---|---|
| SURVIVES (unchanged need, unchanged or near-unchanged form) | **~20%** |
| TRANSFORMS (need survives, form dies) | **~40%** |
| DIES (no computational residue) | **~40%** |

**Headline projection: roughly 60% of what a programmer manipulates today ceases to exist as such; only ~20% passes through intact.** The 40% that transforms is where all the design work of this project lives — and where all the risk concentrates (section 05).

This is consistent with the section 03 finding that only ~25% of tokens loaded in a typical edit context are semantically necessary: the paradigm's claim is precisely that the disposable ~75% maps onto the DIES and TRANSFORMS categories.

---

## 6.3 Adoption Path Projection

The end state does not arrive in one step. Realistic sequence, conditioned on the falsification criteria in 5.9 passing:

| Phase | What exists | Source of truth |
|---|---|---|
| 1. Derived index | Semantic graph built *over* existing text repos; agents use it for retrieval and impact analysis only | Text |
| 2. Graph-first editing | Agents edit via graph operations; canonical text projection is generated and committed for humans/CI | Graph, mirrored to text |
| 3. Boundary inversion | New components are born as graph; legacy text is wrapped in boundary nodes | Graph, text as legacy periphery |
| 4. Native | Models trained on graph+IR representations; text projections generated on demand only | Graph |

Phase 1 is buildable now and is falsifiable cheaply — it directly tests the input-token claim (5.9, criterion 1) without requiring anyone to abandon their repository. **Phase 1 is the correct next deliverable of this project.**

---

## 6.4 What This Project Still Owes

1. Runtime semantics specification (transactions, concurrency, effect ordering) — the missing spec section identified in 5.4.
2. A Phase-1 prototype: graph extraction from a real text codebase + measured input-token comparison on ≥50 edit tasks.
3. Canonical text projection format definition (the editing surface for current-generation models, per 5.1).
4. A formal statement (and ideally proof sketch) of the conditions under which the depth-2 edit locality invariant is maintainable.
