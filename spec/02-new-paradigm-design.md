# 02. New Paradigm Design

## Overview

This section designs the AI-native software representation from scratch. No concept is inherited from current paradigms without explicit justification. Every element must justify its existence by computational necessity — not convention, not human readability, not team coordination.

The result is a **typed semantic graph** where every unit is a node, every relationship is a typed edge, and the entire state of a software system at any point in time is a queryable, versioned, content-addressed graph.

---

## 2.1 Fundamental Unit: The Semantic Node

The semantic node replaces files, classes, functions, and modules as the fundamental unit of software representation.

A semantic node encodes exactly one piece of coherent meaning — it cannot be subdivided without losing that meaning.

### Node Schema

```json
{
  "id": "sn:sha256:a4f2e9b7c3d1f0a2",
  "type": "computation | data | constraint | event | test | boundary | ontology",
  "version": "v:3a9f2c",
  "signature": {
    "inputs": [{ "type": "sn:user-type", "cardinality": "1" }],
    "outputs": [{ "type": "sn:result-type", "cardinality": "0..1" }],
    "effects": ["db:write", "event:emit"]
  },
  "behavior": {
    "ir": "base64-encoded-wasm-or-ir-blob",
    "ir_hash": "sha256:...",
    "ir_format": "wasm | llvm-ir | cranelift-ir"
  },
  "meta": {
    "intent_embedding": [0.12, -0.87, ...],
    "domain": "on:payments",
    "context_partition": "cp:order-processing",
    "created_in_snapshot": "snap:00342",
    "aliases": ["create-payment", "process-payment"]
  }
}
```

### Node Types

| Type | Replaces | Purpose |
|---|---|---|
| `computation` | Function / method | Executable behavior with typed inputs/outputs |
| `data` | Class fields / struct / DTO | Typed data structure (no behavior) |
| `constraint` | Comment / interface / assertion | Machine-checkable rule that applies to other nodes |
| `event` | Domain event / message | Named, typed occurrence that triggers downstream nodes |
| `test` | Unit/integration test | Specification of expected computation behavior |
| `boundary` | Service interface / API endpoint | Explicit partition crossing point |
| `ontology` | Domain documentation / DDD concept | Business concept definition in the domain ontology |

### Why not classes, files, or modules?

Each of those units forces grouping by a criterion the human chose — "things that relate to User", "things that belong in this file", "things exported from this module." The grouping is in the node type and in its edges. Multiple groupings coexist without conflict (a node can belong to domain `payments`, service `order-processor`, and context partition `write-path` simultaneously, via three different edge types).

---

## 2.2 Relationships: The Typed Edge

The graph connecting semantic nodes is a **labeled property graph** — each edge has a type, a direction, and optional properties.

### Core Edge Types

| Edge type | Direction | Semantics |
|---|---|---|
| `depends-on` | A → B | A requires B to function; B must exist before A compiles |
| `produces` | A → B | A emits events or data of type B |
| `consumes` | A → B | A reads events or data of type B |
| `constrained-by` | A → B | B is a constraint node that applies to A |
| `tests` | A → B | A is a test node that verifies B |
| `dispatches-to` | A → B | A may resolve to B at execution (polymorphic dispatch) |
| `composed-of` | A → B | A is a data node that contains B as a field |
| `boundary-exposes` | A → B | A is a boundary node that exposes B externally |
| `belongs-to-domain` | A → B | A is part of domain ontology context B |
| `deployed-in` | A → B | A is compiled into deployment unit B |
| `derives-from` | A → B | A is a modified version of B (temporal lineage) |
| `satisfies` | A → B | A is a concrete node that satisfies constraint B |

### Why a graph (not a tree, not a hypergraph)?

**Not a tree:** Trees force a single parent. Code has cross-cutting concerns — a payment computation node belongs simultaneously to the `payments` domain, the `write-path` execution context, and the `order-processing` context partition. A tree cannot represent this without duplication or artificial root nodes.

**Not a hypergraph (for now):** Hyperedges (edges connecting more than two nodes) would allow expressing relationships like "these three nodes together implement this constraint." This is more expressive but requires hypergraph databases that are not production-ready with today's tooling. The same semantics can be approximated with an intermediate constraint node connected to multiple nodes via `constrained-by` edges.

**A labeled property graph** (Neo4j, Apache AGE, Amazon Neptune) is available today, queryable with Cypher/SPARQL/Gremlin, supports all needed edge types, and has proven scalability at millions of nodes.

---

## 2.3 Identity: Content-Addressed Hashing

Every semantic node's ID is derived from its content, not from a human-chosen name.

### ID Derivation

```
id = "sn:" + sha256(
  node.type +
  canonical_serialize(node.signature) +
  node.behavior.ir_hash +
  sorted(node.direct_dependency_ids)
)
```

**Properties this gives us:**

| Property | Consequence |
|---|---|
| Two nodes with identical semantics share an ID | True deduplication at semantic level — DRY enforced structurally |
| Renaming a node does not change its ID | Rename = metadata update, zero semantic change |
| Moving a node between contexts does not change its ID | Restructuring is metadata, not semantic change |
| ID is deterministic | Two independent agents deriving the same computation produce the same node |
| ID encodes dependency set | Changing a dependency changes the ID — dependency drift is structurally impossible |

### Human Aliases

Human-readable names are stored as a many-to-one index: `alias → node_id`. Multiple aliases can point to one node. One node can have zero aliases (internal implementation detail) or many (public API with versioned names).

Aliases are never used for graph traversal. They are only used for:
- Human-facing output (generating readable source code from the graph)
- External API naming (boundary nodes expose human-readable names for external consumers)
- Search interface (humans querying "find the node called X")

---

## 2.4 Memory: Tiered Context Management

The full semantic graph of a production system may contain millions of nodes. An LLM context window holds thousands of tokens. Loading the full graph is never an option. Memory is structured as three tiers:

### Tier 1: Working Graph (In-Context)

- **Size:** 10–50 nodes, ~2,000–8,000 tokens
- **Content:** The nodes directly involved in the current edit
- **Population:** The AI agent explicitly loads these via graph queries
- **Persistence:** Lives in the LLM's context window for the current turn

### Tier 2: Session Index (Persisted Between Turns)

- **Size:** ~500–2,000 node summaries, ~20,000–50,000 tokens
- **Content:** Compact summaries (ID + type + signature hash + direct edge count) of frequently accessed nodes this session
- **Population:** Built up as the agent navigates the graph; hot nodes stay, cold nodes evict
- **Persistence:** Stored in a session-scoped vector store, survives context window resets
- **Eviction policy:** LFU (least frequently used); constraint nodes and domain ontology nodes are pinned (never evicted)

### Tier 3: Full Graph Store (Never Fully Loaded)

- **Size:** Unbounded; millions of nodes in production systems
- **Content:** All nodes, all edges, full version history
- **Access:** Point lookup by hash (O(1)), neighborhood traversal, semantic similarity search
- **Persistence:** Graph database with write-ahead log and snapshot compaction

### Context Loading Protocol

When an AI agent needs to edit node `sn:a4f2e9b7`:

1. Load the node itself (from Tier 3 if not in Tier 1/2)
2. Load its direct `depends-on` edges (one hop) — what it needs
3. Load its direct `constrained-by` edges — what rules apply
4. Load its direct incoming edges from `tests` nodes — what behavior is expected
5. Load its direct dependents (nodes that `depends-on` this node) — what it must not break
6. Total context: typically 5–20 nodes; rarely exceeds 50

**Edit locality guarantee:** Any single-node edit can be performed by loading at most `depth=2` graph hops from the target node. This is a design invariant maintained by limiting the allowed depth of `depends-on` chains between context partitions.

---

## 2.5 Dependencies: Explicit Directed Edges

All dependencies are explicit `depends-on` edges. There is no implicit loading, no module resolution from filesystem paths, no transitive import following.

### Dependency Rules

1. **All dependencies must be declared** — if node A uses node B, a `depends-on` edge from A to B must exist. No edge = no access.

2. **Dependencies are directed** — `A depends-on B` means A needs B. B has no knowledge of A. This is enforced structurally by the edge direction.

3. **Circular dependency detection** — a graph cycle query at snapshot time. Any cycle in `depends-on` edges is a compile-time error, not a runtime problem.

4. **Transitive dependency depth** — at context partition boundaries, transitive depth is constrained (at most N hops to cross a boundary). This enforces edit locality.

5. **Dependency updates propagate** — when node B changes (new content hash → new ID), all nodes with `depends-on` edges to the old B ID must either update their edge or declare explicit compatibility.

### Dependency vs. Composition

| Relationship | Edge | Semantics |
|---|---|---|
| A calls B | `depends-on` | A needs B's computation |
| A has field of type B | `composed-of` | A contains a B data field |
| A listens to B | `consumes` | A reacts to B events |
| A emits for B | `produces` | A generates events B processes |

---

## 2.6 Context Partitions: Replacing Bounded Contexts and Services

A context partition is a subgraph with:
- A defined boundary (a set of `boundary` nodes through which cross-partition traffic flows)
- A deployment annotation (which deployment unit contains this partition)
- An optional team or domain annotation

Context partitions replace:
- DDD Bounded Contexts (semantic partitioning)
- Microservice boundaries (deployment partitioning)
- Module systems (dependency partitioning)

All three are the same concept at different scales. In the semantic graph, they're represented as a partition label on nodes and boundary nodes at partition edges.

**Cross-partition dependency rule:** Node A in partition P1 may `depend-on` node B in partition P2 only through a `boundary` node in P2. Direct cross-partition `depends-on` edges are a compile-time error.

---

## 2.7 Business Rules and Domain Knowledge

Business rules are `constraint` nodes, not comments or documentation. They are first-class graph citizens.

### Constraint Node Schema

```json
{
  "id": "cn:sha256:c3d1f0a2",
  "type": "constraint",
  "domain": "on:inventory",
  "statement_embedding": [...],
  "human_description": "Stock cannot go negative",
  "severity": "error | warning | info",
  "verifiable": true,
  "verification_node": "sn:check-stock-non-negative",
  "applies-to": ["sn:stock-deduct-fn", "sn:stock-transfer-fn"]
}
```

### Domain Ontology

Business concepts live in `ontology` nodes:

```json
{
  "id": "on:reorder-point",
  "type": "ontology",
  "domain": "on:inventory",
  "definition_embedding": [...],
  "human_description": "Minimum stock level triggering a purchase order",
  "related-to": ["on:stock-level", "on:purchase-order", "on:sku"]
}
```

When an AI agent edits a computation node in the `inventory` domain, it can load all relevant domain ontology nodes and constraint nodes in a single graph query: `MATCH (n)-[:belongs-to-domain]->(d:on:inventory) WHERE n.type IN ['ontology', 'constraint'] RETURN n`. This replaces reading domain documentation.

---

## 2.8 APIs: Boundary Nodes

APIs survive as `boundary` nodes — explicit points where the semantic graph crosses from internal to external representation.

```json
{
  "id": "bn:create-stock-movement",
  "type": "boundary",
  "direction": "inbound | outbound",
  "protocol": "http-rest | grpc | event-stream | graphql",
  "external_name": "POST /inventory/movements",
  "external_schema_version": "v2",
  "resolves-to": "sn:create-stock-movement-fn",
  "constrained-by": ["cn:auth-required", "cn:rate-limited"]
}
```

**Key property:** Boundary nodes have human-readable external names (`POST /inventory/movements`) because external consumers are humans or human-built systems. Internal names are content-addressed IDs. The boundary is the only place where human-readable naming is computationally justified.

External-facing documentation (OpenAPI spec, etc.) is **generated** from boundary node schemas — never written manually.

---

## 2.9 Compilation

The compiler takes a graph snapshot and produces execution artifacts.

### Compilation Steps

1. **Entry point identification** — query: `MATCH (n:boundary) WHERE n.direction = 'inbound' RETURN n` — find all public entry points
2. **Subgraph extraction** — BFS traversal from entry points along `depends-on` edges; collect all reachable nodes
3. **Topological sort** — sort by `depends-on` edges (dependency order)
4. **IR retrieval** — for each computation node, retrieve `behavior.ir` blob
5. **Linking** — resolve cross-node calls (the IR blobs reference node IDs; linking substitutes runtime addresses)
6. **Optimization** — pass through LLVM/Cranelift optimization pipeline (standard IR optimizers work unchanged on the IR blobs)
7. **Target emission** — binary, WASM, or container image

**Advantage:** The compiler never parses text. Steps 1–4 are graph queries + binary blob retrieval. Steps 5–7 are standard IR toolchain operations. The entire custom logic is in steps 1–4, which are simpler than any current text-based compiler frontend.

### Multi-Target Compilation

The same graph snapshot compiles to multiple targets without modification. Deployment unit annotations (`deployed-in`) determine which partition of the graph compiles to which target. A single graph can produce: a monolithic binary, a set of microservice containers, a WASM module, and a set of serverless functions — all from the same semantic source.

---

## 2.10 Testing

Tests are `test` nodes connected to computation nodes via `tests` edges. Tests are **data**, not code.

### Test Node Schema

```json
{
  "id": "tn:sha256:t7b3e1c9",
  "type": "test",
  "tests": "sn:a4f2e9b7",
  "test_type": "example | property | contract | e2e",
  "given": {
    "inputs": [{ "type": "sn:stock-movement-input", "value": {...} }],
    "state": { "db_fixtures": "fixture:empty-inventory" }
  },
  "expects": {
    "outputs": [{ "type": "sn:result", "value": {...} }],
    "effects": [{ "type": "db:write", "table": "stock_movements", "count": 1 }]
  },
  "constrained-by": ["cn:stock-movement-business-rules"]
}
```

**Property-based tests** are constraint nodes with a verification computation node:
```json
{
  "id": "cn:stock-always-non-negative",
  "type": "constraint",
  "verifiable": true,
  "verification_node": "sn:check-stock-non-negative-property",
  "property": "for all valid inputs, stock_level >= 0 after any operation"
}
```

**Coverage** is a graph property: percentage of computation nodes with at least one incoming `tests` edge. Computed by graph query in O(E) time.

---

## 2.11 Errors

Errors are `event` nodes with an error subtype:

```json
{
  "id": "ev:insufficient-stock",
  "type": "event",
  "event_subtype": "error",
  "domain": "on:inventory",
  "payload_type": {
    "required": "on:stock-quantity",
    "available": "on:stock-quantity",
    "sku": "on:sku"
  },
  "handlers": ["sn:notify-warehouse-manager", "sn:trigger-purchase-order"]
}
```

Error handling is expressed as `consumes` edges from handler nodes to error event nodes. No `try/catch` blocks embedded in computation logic. Computation nodes emit error events via `produces` edges; they do not handle errors internally.

**Advantage:** Error handling logic is never mixed with computation logic. Changing error handling is a graph edit on handler nodes — it never touches computation nodes.

---

## 2.12 Refactoring

Refactoring is a semantic graph transformation with defined operations:

| Refactoring | Graph operation |
|---|---|
| Extract function | Split computation node: create new node, redirect edges |
| Inline function | Merge computation node into caller: merge IR, redirect edges |
| Rename | Update alias metadata on node: zero semantic change |
| Move to different context | Update `deployed-in` and `belongs-to-domain` edges: zero semantic change |
| Extract abstraction | Create shared node, replace N identical nodes with references: true DRY |
| Change interface | Update signature on boundary node, propagate type-check to all `depends-on` nodes |
| Add cross-cutting concern (auth, logging) | Add constraint node + `constrained-by` edges: zero change to computation nodes |

**Key property:** Most refactoring operations in current software require text search-and-replace across many files. In the semantic graph, most refactoring operations are metadata edits or edge rewirings — they never touch behavior IR blobs unless the behavior itself changes.

---

## 2.13 Versioning: Temporal Graph

Version control is a **temporal dimension on the semantic graph**, not a separate text-diffing system.

### Snapshot

A snapshot is:
```json
{
  "id": "snap:sha256:00342a",
  "parent": "snap:sha256:00341b",
  "delta": {
    "added_nodes": ["sn:x", "sn:y"],
    "removed_nodes": [],
    "modified_nodes": [{ "old": "sn:a:v3", "new": "sn:a:v4" }],
    "added_edges": [["sn:x", "depends-on", "sn:z"]],
    "removed_edges": []
  },
  "graph_hash": "sha256:full-graph-at-this-snapshot",
  "agent": "agent:synthesis-agent-01",
  "timestamp": "2026-06-30T14:32:00Z",
  "intent_ref": "intent:add-reorder-notification"
}
```

### Semantic Diff

Two snapshots differ by their `delta`. A human-readable changelog is generated from the delta on demand:
> "Added: stock-reorder notification computation. Modified: warehouse-manager boundary to expose new notification endpoint. Added 3 test nodes."

This is more informative than most commit messages written by humans.

### Parallel Versioning (Branches)

Multiple agents can work on separate graph regions simultaneously. Merge conflicts are detected at the semantic level: if two agents modify the same node (same starting `sn:id`), the merge agent must reconcile. Unlike text merges, the conflict is always on a semantically coherent unit (one node), not an arbitrary text range.

---

## 2.14 Search

Three search mechanisms replace text search (grep, find, IDE symbol search):

| Mechanism | Query type | Complexity | Use case |
|---|---|---|---|
| **Hash lookup** | `graph.get("sn:a4f2e9b7")` | O(1) | Known node retrieval |
| **Graph traversal** | Cypher/Gremlin from known node | O(E * filter) | "What does this depend on?" |
| **Semantic search** | Vector cosine similarity on intent embeddings | O(log N) with index | "Find nodes that do something like X" |

No text search. No filename search. The semantic search (vector similarity) is the most powerful — it finds nodes by meaning, not by name. "Find the node that validates stock quantities" returns the correct node even if the human alias is `check-qty`, `validateInventoryAmount`, or `sn:3f9b2c` (no alias).

---

## 2.15 Design Decisions Summary

| Concern | Current paradigm | AIL-2 paradigm |
|---|---|---|
| Fundamental unit | File / Class / Function | Semantic node (typed, content-addressed) |
| Organization | Filesystem hierarchy | Graph edge types (domain, service, context) |
| Identity | Human-chosen name string | Content-addressed SHA256 hash |
| Naming | Required, embedded in identity | Optional alias metadata |
| Relationships | Implicit (file imports, class inheritance) | Explicit typed edges |
| Memory loading | Load whole file or module | Load exact subgraph needed |
| Business rules | Comments / documentation | Constraint nodes |
| Versioning | Text diffs + prose commit messages | Semantic deltas + intent references |
| Testing | Separate test files | Test nodes in the same graph |
| Errors | Exception handling embedded in logic | Error event nodes + handler edges |
| Refactoring | Text search-and-replace | Graph transformation operations |
| APIs | Manual contract definition | Generated from boundary node schemas |
| Documentation | Manually written prose | Generated from ontology + type signatures |
