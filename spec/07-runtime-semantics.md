# 07. Runtime Semantics

## Overview

Sections 01–04 specify how software is *represented*; they do not specify how it *runs*. Section 05 (§5.4) identified this as the largest unwritten part of the design: a paradigm that cannot express a bank transfer transactionally is not general-purpose. This section closes that gap.

Design constraint carried over from section 02: runtime semantics must be expressible **in the graph itself** — as node properties and typed edges — never as conventions buried inside IR blobs. If a behavior matters to correctness, it must be queryable.

---

## 7.1 The Execution Model

A compiled snapshot executes as a set of **activations**. An activation is one run of a computation node: inputs in, outputs out, effects performed. Activations are the runtime counterpart of computation nodes — the node is the *program*, the activation is the *process*.

```
activation = {
  node: semantic_id @ version_hash,
  inputs: typed values,
  effect_context: transaction | saga | none,
  causality: id of the activation or boundary event that triggered this one
}
```

Three properties every activation carries:

1. **Typed inputs/outputs** — checked against the node signature at the boundary of every activation. A type violation is a runtime event node (`ev:type-violation`), never undefined behavior.
2. **Declared effects only** — an activation may perform only the effects listed in its node's `signature.effects`. Attempting an undeclared effect aborts the activation. This makes `effects` a capability list, not documentation.
3. **Recorded causality** — every activation records what triggered it. The runtime trace is itself a graph (activations + causality edges), which is what makes debugging possible without file/line stack traces (see §7.6).

---

## 7.2 Effect Ordering

`signature.effects` in section 02 was an unordered set. That is insufficient: real computations require sequencing (validate → write → emit). The schema is amended:

```json
"effects": [
  { "seq": 1, "kind": "db:read",  "target": "on:stock-level" },
  { "seq": 2, "kind": "db:write", "target": "on:stock-movement" },
  { "seq": 3, "kind": "event:emit", "target": "ev:stock-updated" }
]
```

**Rules:**

- Effects with distinct `seq` values execute in ascending order; the runtime enforces this.
- Effects sharing a `seq` value are declared order-independent and may be parallelized or reordered by the optimizer.
- `event:emit` effects are always last-ordered within a transactional context (see §7.3) — events must not announce state that can still roll back.

This is the graph-level equivalent of what monadic sequencing or async/await ordering does inside a function body, lifted to where the compiler and verification agents can see it.

---

## 7.3 Transactions

A transaction boundary is a graph annotation, not a code construct. Two mechanisms, chosen per computation:

### Atomic scope (single-partition)

A computation node (or a `depends-on`-connected chain of nodes within one context partition) may be marked:

```json
"execution": { "atomicity": "atomic", "isolation": "serializable | snapshot | read-committed" }
```

Semantics: all `db:*` effects of all activations inside the scope commit together or not at all. The compiler maps the scope onto the underlying store's native transactions. Cross-node atomic scopes are permitted **only within one context partition** — a boundary crossing inside an atomic scope is a compile-time error, because distributed atomicity over synchronous boundaries is a known operational trap.

### Saga scope (cross-partition)

Cross-partition workflows use explicit compensation, declared with a dedicated edge type:

```
compensates  A → B     A is the compensating computation for B
```

A saga is a chain of computation nodes connected by `produces`/`consumes` event edges where every state-mutating step has a `compensates` incoming edge. **Verifiable completeness rule:** a snapshot in which a cross-partition workflow contains a state-mutating node without a compensator fails validation — the query is one graph traversal. Compensation logic stops being tribal knowledge; it becomes a checkable structural property.

### The bank transfer, expressed

```
bn:transfer-request (boundary)
  → sn:validate-transfer          effects: [db:read]
  → sn:debit-account              effects: [db:write]   ┐ atomic scope
  → sn:credit-account             effects: [db:write]   ┘ (same partition)
  → produces ev:transfer-completed

cross-bank variant (two partitions):
  sn:debit-local     ← compensates ← sn:refund-local
  ev:debit-done → consumed by partition B → sn:credit-remote
  sn:credit-remote fails → produces ev:credit-failed → consumed by sn:refund-local
```

Both variants are fully expressible with: one node property (`execution.atomicity`), one edge type (`compensates`), and the existing event edges. No new primitives.

---

## 7.4 Concurrency Model

The unit of concurrency is the activation. Rules:

1. **Activations are share-nothing by default.** Data nodes define schemas; runtime state lives in stores accessed via declared `db:*`/`state:*` effects. Two activations never share mutable memory — there is no graph representation for shared mutable memory, deliberately.
2. **Event delivery declares its guarantee on the `consumes` edge:**

```json
{ "edge": "consumes", "delivery": "at-least-once | at-most-once | exactly-once-effective",
  "ordering": "none | per-key(on:sku) | global" }
```

   - `at-least-once` is the default; it requires the consumer node to be marked idempotent (§7.5).
   - `per-key` ordering serializes delivery per value of a declared ontology key — the graph form of partitioned queues (Kafka partition keys), without naming any vendor.
   - `global` ordering is permitted only within one partition; cross-partition global ordering fails validation (it does not scale, and the graph refuses to promise it).
3. **Multiple consumers of one event type are independent.** Each `consumes` edge is its own subscription with its own delivery guarantee. Fan-out is visible as fan-out in the graph.
4. **Determinism annotation.** Computation nodes are marked `deterministic: true|false`. Deterministic nodes with identical inputs may be memoized, replayed, or speculatively parallelized by the runtime; nondeterministic nodes (time, random, external I/O) may not. This annotation is verifiable: a node whose effects list contains only reads of immutable inputs must be deterministic, and the verification agent checks the consistency.

---

## 7.5 Partial Failure and Recovery

Section 02 (§2.11) routes errors as event nodes but defines no recovery semantics. Amendments:

**Idempotency is a node property, checked at the edge.**

```json
"execution": { "idempotent": true, "idempotency_key": "on:transfer-id" }
```

Any node consuming with `at-least-once` delivery must be idempotent — validated structurally at snapshot time. Non-idempotent consumers must use `at-most-once` and accept loss, explicitly.

**Retry policy lives on the `consumes` edge, not in code:**

```json
{ "edge": "consumes", "retry": { "max": 5, "backoff": "exponential", "dead_letter": "ev:transfer-dlq" } }
```

Exhausted retries produce a dead-letter event node — which is a normal event node with handlers, so "what happens when this keeps failing?" is a graph query, answerable before deployment.

**Failure inside an atomic scope** rolls back the scope and produces the node's declared error event. **Failure inside a saga** triggers the `compensates` chain in reverse causal order, driven by the recorded causality of §7.1.

**Timeouts are boundary properties.** Every synchronous `boundary` node declares `timeout_ms`; expiry produces `ev:timeout` with the causality chain attached. Unbounded synchronous waits are unrepresentable.

---

## 7.6 Observability of Activations

The runtime trace is a graph in the same formalism as the program:

| Program (design time) | Trace (run time) |
|---|---|
| computation node | activation record |
| `depends-on` / `consumes` edge | causality edge between activations |
| event node | event occurrence with payload |
| constraint node | constraint check record (pass/fail) |

A production incident is investigated by traversing the trace graph backward from the failing activation — the replacement for stack traces promised in §5.5. Debug metadata maps IR offsets → `(semantic_id, version_hash)` exactly as source maps map minified JS → source, so existing observability tooling can be bridged by translating file/line to node IDs at the ingestion layer.

---

## 7.7 What This Section Deliberately Excludes

- **Memory management within a node's IR** — delegated to the IR runtime (WASM linear memory, LLVM-managed). The graph does not model intra-node allocation; it models only cross-node contracts.
- **Real-time / hard-latency scheduling** — out of scope for v1; would require deadline annotations and admission control not yet designed.
- **Distributed consensus internals** — the graph declares delivery and ordering guarantees; *implementing* them is the runtime's job, using existing infrastructure. The paradigm specifies the contract surface, not the broker.

---

## 7.8 Summary of Additions to the Core Model

| Addition | Where it lives | Verifiable at snapshot time? |
|---|---|---|
| Ordered effects (`seq`) | node signature | yes — emit-last rule, undeclared-effect rule |
| Atomic scope | node `execution` property | yes — no boundary crossing inside scope |
| `compensates` edge (11th edge type) | graph edge | yes — saga completeness traversal |
| Delivery + ordering guarantees | `consumes` edge properties | yes — idempotency pairing, no cross-partition global order |
| Idempotency + key | node `execution` property | partially — structural checks + verification node |
| Retry + dead-letter | `consumes` edge properties | yes — DLQ handler existence |
| Determinism flag | node property | partially — effect-list consistency check |
| Activation trace graph | runtime artifact | n/a — produced, not authored |

Every addition is a node property or edge property — no new primitive beyond one edge type. The 4-primitive model of section 02 survives contact with runtime reality, which was the test this section had to pass.
