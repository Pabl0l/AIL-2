# AIL — Paradigm Manual
## Part 5: Quick Reference

> English version of [`manual/parte-5-referencia.md`](../parte-5-referencia.md). This page is the condensed manual: an AI can load only this page to operate under the paradigm in simple situations. For complex work, load the relevant part of parts 1–4 (currently Spanish).

---

## The paradigm in one sentence

Software is a typed semantic graph. Nodes are units of meaning. Edges are typed relationships. Source text is an output artifact, never the source of truth.

---

## The 7 node types

| Type | Contains | Replaces |
|---|---|---|
| `computation` | executable IR + typed signature | function, method, handler |
| `data` | typed fields, no methods | class/struct/DTO/entity |
| `constraint` | verifiable business rule | comment, assertion, embedded validation |
| `event` | typed occurrence with payload | exception, domain event, message |
| `test` | given/expect pair | unit/integration test |
| `boundary` | external entry/exit point | endpoint, API, port |
| `ontology` | defined domain concept | documentation, DDD term |

---

## The 11 edge types

| Edge | Meaning |
|---|---|
| `depends-on` A→B | A needs B to execute |
| `composed-of` A→B | A has a field of type B |
| `constrained-by` A→B | B is a rule A must satisfy |
| `tests` A→B | A verifies the behavior of B |
| `produces` A→B | A emits events of type B |
| `consumes` A→B | A processes events of type B |
| `dispatches-to` A→B | A may resolve as B (polymorphism) |
| `boundary-exposes` A→B | A exposes B externally |
| `derives-from` A→B | A is a modified version of B |
| `belongs-to` A→B | A belongs to domain/partition B |
| `compensates` A→B | A is the compensating computation for B (sagas, spec/07) |

---

## The rules on one page

### Identity (two-level)
- semantic_id = sha256(type + canonical signature) — stable while the contract holds
- version_hash = sha256(semantic_id + IR_hash + dependency version pins) — new on every behavior change
- Edges reference semantic_id (optional version pin)
- Names are aliases in metadata, never identity
- Rename = metadata update, no ID change
- Behavior change = new version, same semantic_id — dependents untouched
- Signature change = new semantic_id — breaking change, dependents must re-target

### Representation
- Every artifact maps to exactly one node type
- Behavior lives in binary IR, never in source text
- Business rules are constraint nodes, never comments
- Cross-cutting concerns are constrained-by edges, never embedded code
- All relationships are explicit edges

### Context
- Local edit = target node + depth-1 neighbors + constraints + tests
- Maximum depth-2. Never more.
- Ontology and constraint nodes: pinned at session start
- Expand context only when type compatibility fails
- Search semantically before expanding

### Change
- Nodes are immutable — new versions are created
- Snapshot always before modifying
- Dependents update explicitly (adopt / keep / incompatible)
- Refactor = graph operation, never text search
- Delete = redirect edges, no direct action

### Knowledge
- One rule = one constraint node (no duplicates)
- Order: ontology → constraint → data → computation → test → boundary
- Every verifiable constraint has a verification node

### Correctness
- Every computation node has ≥1 test node
- Tests are data (given / expect), not code
- Minimum coverage for deployment: 80%
- Types = edge compatibility, not text comparison
- Errors = event nodes with produces/consumes edges

### Runtime (spec/07)
- Effects are ordered (`seq`); event emission always last in a transactional scope
- Atomic scopes never cross partition boundaries; cross-partition workflows are sagas with `compensates` edges
- `at-least-once` delivery requires the consumer to be idempotent — checked structurally
- Retry policy and dead-letter live on the `consumes` edge, not in code

### Time
- Version unit = snapshot
- No text diffs — only semantic deltas
- Rollback = restore snapshot
- Node history = chain of derives-from edges

---

## Work order (always)

```
1. Ontology    (domain concepts)
2. Constraint  (business rules)
3. Data        (structures)
4. Computation (behavior)
5. Test        (verification)
6. Boundary    (external exposure)
7. Snapshot    (validate)
8. Compile     (only if snapshot is valid)
```

---

## Edit protocol (always)

```
1. Identify target node (direct hash or semantic search)
2. Load minimal context (node + depth-1 + constraints + tests)
3. Check constraints before modifying
4. Create snapshot
5. Create new node version with modified behavior
6. Update/create test nodes
7. Update dependents' edges
8. Validate snapshot
```

---

## What does not exist in this paradigm

```
✗ Source code files as primary unit
✗ Folders and directory structure
✗ Classes and inheritance
✗ Interfaces as separate text artifacts
✗ Explanatory comments
✗ Manually maintained documentation
✗ Import / require / use statements
✗ Try/catch embedded in computation logic
✗ Getters, setters, constructors
✗ Validation embedded in business functions
✗ Text search (grep) to navigate the system
✗ Text diffs to version changes
✗ Natural-language commit messages
✗ Pull requests as review mechanism (human sign-off gate remains, spec/05 §5.7)
```

---

## Quick decision table

| Situation | What to do |
|---|---|
| Need a new function | Create `computation` node with signature + IR |
| Need a data structure | Create `data` node with typed fields |
| Have a business rule to record | Create `constraint` node (not a comment) |
| Need to expose functionality externally | Create `boundary` node → `boundary-exposes` → computation |
| Need to verify behavior | Create `test` node → `tests` → computation |
| Need to add auth to something | Add edge `constrained-by → cn:requires-auth`, don't touch the logic |
| Need to find where a rule lives | Query: `MATCH (n)-[:constrained-by]->(cn) WHERE cn.statement CONTAINS "X"` |
| Need to know what can fail | Query: `MATCH (n)-[:produces]->(e:event {subtype: error}) RETURN e` |
| Need a node's history | Traverse `derives-from` edges backward |
| A function must change | Protocol 2 — modify existing behavior |
| A business rule changed | Modify constraint node + re-validate constraints |
| The system failed in production | Protocol 4 — create a test reproducing the bug, then fix |

---

## Reference metrics

| Metric | Target |
|---|---|
| Tokens for a local edit | < 800 |
| Tokens to understand all rules of a domain | < 2,000 |
| Maximum context depth | depth-2 |
| Minimum coverage for deployment | 80% |
| Computation nodes without constraints | 0 (all have at least `belongs-to` a domain) |
| Boundaries without an auth constraint | 0 |
| Business rules outside constraint nodes | 0 |

If any value is out of target, the graph has a design problem that must be fixed before continuing.

---

## Minimal glossary

| Term | Definition |
|---|---|
| **Semantic node** | Atomic unit of meaning in the graph |
| **Typed edge** | Directed relationship with defined semantics between two nodes |
| **Content-addressed** | Identity derived from content, not from an assigned name |
| **IR** | Intermediate Representation — binary format of compiled behavior |
| **Snapshot** | Consistent, immutable state of the full graph at a point in time |
| **Semantic delta** | Difference between two snapshots in nodes and edges, not text |
| **Partition** | Labeled subgraph with boundary nodes at its limits |
| **Alias** | Optional human name attached to a node, separate from identity |
| **Edit locality** | Property: any local edit needs context of depth ≤2 |
| **Context budget** | Maximum tokens an operation may load |
| **Verifiable constraint** | Business rule with a computation node that checks it automatically |
| **Cross-cutting concern** | Auth, logging, rate limiting, cache: they live in edges, not in computation logic |
| **Canonical projection** | Deterministic generated text view of an edit context — the editing surface for current models (spec/08) |
