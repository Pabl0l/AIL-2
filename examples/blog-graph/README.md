# Blog System as a Semantic Graph

Machine-readable version of the blog example from [`manual/parte-4-ejemplo.md`](../../manual/parte-4-ejemplo.md). The manual describes the graph in prose; [`graph.json`](graph.json) *is* the graph.

## Inventory

| Node type | Count |
|---|---|
| ontology | 8 |
| constraint | 7 |
| data | 4 |
| computation | 13 |
| event | 11 |
| test | 25 |
| boundary | 6 |
| **Total** | **74** |

**90 typed edges** (`depends-on` 23, `constrained-by` 18, `tests` 25, `produces` 14, `boundary-exposes` 6, `composed-of` 4). Test coverage: 13/13 computation nodes.

## Why 74 nodes, not the manual's 65

Making the graph machine-readable exposed three inconsistencies the prose hid — which is itself the paradigm's argument:

1. **4 verification nodes were missing.** The constraint nodes reference `sn:verificar-estado-publicado`, `sn:verificar-estado-moderacion`, `sn:verificar-unicidad-slug`, and `sn:verificar-longitud-titulo` as their verification computations, but the manual's computation inventory (9 nodes) never listed them. A graph store would have rejected the dangling references at snapshot validation.
2. **`cn:requires-auth` was uncounted.** Five boundary nodes are `constrained-by cn:requires-auth`, but it wasn't among the manual's 6 constraint nodes.
3. **4 computation nodes had no tests.** The paradigm's own rule (parte-2: every computation node has ≥1 test node) failed for the verification nodes; 4 test nodes were added (21 → 25).

Every one of these is invisible in prose and a one-line query on the graph:

```
dangling refs:   nodes referenced by any edge or property that don't exist
uncounted:       COUNT(type=constraint) vs. documented inventory
untested:        MATCH (c:computation) WHERE NOT (:test)-[:tests]->(c)
```

## Conventions in this file

- IDs are human-readable aliases (`sn:crear-articulo`) for pedagogy. In a real store, identity is content-addressed (`semantic_id` + `version_hash`, spec/02 §2.3) and these strings live in alias metadata.
- Effects use the ordered form from spec/07 §7.2 (`seq` + kind + target); execution properties (`atomicity`, `idempotent`, `deterministic`) follow spec/07 §§7.3–7.5.
- Edges are `[from, type, to]` triples using the 10-edge catalog from spec/02 §2.2.
- Domain membership is a `domain` property rather than `belongs-to` edges — a flattening acceptable in a single-domain example.

## Things to try

Load the JSON and answer, with trivial traversals, questions that require reading 5–8 files in the TypeScript version:

- *Where does "only the author can edit" live?* → 1 node (`cn:solo-autor-edita`) + its 3 incoming `constrained-by` edges.
- *What can fail when adding a comment?* → outgoing `produces` edges of `sn:agregar-comentario` with `event_subtype: error`.
- *What breaks if `dn:articulo` changes?* → incoming `depends-on`/`composed-of` edges (11 dependents).
- *Add rate limiting to all writes* → 1 new constraint node + 4 `constrained-by` edges; zero computation nodes touched.

The Phase-1 prototype ([`prototype/`](../../prototype/)) operates on graphs in exactly this format.
