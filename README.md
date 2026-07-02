# AIL-2 — AI Language: A Programming Paradigm for Machines

> What does software look like when only machines write, read, and modify it?

AIL-2 is a research specification for an AI-native software representation. It starts from one observation: **most programming constructs exist for human cognition, not computation** — files for navigation, folders for organization, names for memory, comments for explanation, inheritance for mental modeling. When an AI is the only author and reader, that entire layer is overhead.

**Status: research specification with a first working prototype.** The paradigm is fully designed, honestly self-critiqued, and now has pilot measurements from real code ([`prototype/`](prototype/)). See [Limitations](#limitations-read-this-before-the-claims) before believing any number in this document.

---

## The Core Idea

```
Software is a typed semantic graph.
Nodes are units of meaning.
Edges are typed relationships.
Source text is a generated artifact, never the source of truth.
```

Instead of an AI loading files, parsing text into meaning, and regenerating text, the software *lives* in its semantic form: a content-addressed, versioned, queryable graph. Any local edit loads at most **depth-2 from the target node** — typically 5–20 nodes — regardless of codebase size.

## The 4 Primitives

**1. Semantic Node** — 7 types replace every current construct:

| Type | Replaces |
|------|----------|
| `computation` | function, method, handler |
| `data` | class fields, struct, DTO |
| `constraint` | comment, assertion, embedded validation |
| `event` | exception, domain event, message |
| `test` | unit/integration test (as data: given/expect) |
| `boundary` | endpoint, API, port |
| `ontology` | documentation, DDD concept |

**2. Typed Edge** — 11 relationship types (`depends-on`, `constrained-by`, `tests`, `produces`, `consumes`, `dispatches-to`, `composed-of`, `boundary-exposes`, `derives-from`, `belongs-to`, `compensates`). All relationships explicit; no imports, no implicit coupling.

**3. Graph** — the complete system. Navigation is hash lookup (O(1)), typed traversal, or semantic search — never text search.

**4. Snapshot** — the versioning unit. Semantic deltas over immutable graph states, not text diffs.

## Two-Level Identity

```
semantic_id  = sha256(type + canonical_signature)          — stable contract identity
version_hash = sha256(semantic_id + IR_hash + dep_pins)    — per-revision identity
```

Edges reference semantic IDs. A behavior fix creates a new version — dependents untouched. A signature change creates a new identity — dependents must explicitly re-target, so breaking changes are never silent. Renames are metadata; identity never depends on names.

(The original single-level design had a Merkle-cascade bug — one leaf edit re-identified every transitive dependent. Documented and fixed in [`spec/02`](spec/02-new-paradigm-design.md) §2.3 and [`spec/05`](spec/05-self-critique.md) §5.3.)

## Business Rules as First-Class Nodes

Every business rule is exactly one `constraint` node attached via `constrained-by` edges. Adding a cross-cutting rule ("all write operations require auth") = 1 node + N edges — never editing N functions. Rules are queryable, verifiable, and impossible to bury in implementation.

---

## What the Numbers Actually Say

**Pilot measurement — input tokens (Phase-1 prototype, real stdlib code, n=238 edit targets):**

| Metric | Value |
|--------|-------|
| AIL depth-2 edit context (median) | **337 tokens** (mean 419 — the manual had projected ~420) |
| vs. loading the whole file | **35× less input** (median), i.e. −97.2% |
| vs. file + its imports | **45× less input** (median) |

First measured evidence for the central claim — with real caveats: call resolution at 28.6% understates context size, no constraint nodes in plain Python, token proxy instead of BPE. Full method and caveats in [`prototype/README.md`](prototype/README.md); raw data in [`prototype/results/`](prototype/results/measurement-results.json). What this does **not** show yet: that an agent *succeeds* at edits with only that context — that experiment is next.

**Output tokens (5 tasks, both paradigms, [`test-resultados.json`](test-resultados.json)):**

| Measured | Result |
|----------|--------|
| Output tokens across 5 tasks | **−12.0%** for AIL |
| Tasks where AIL won | 4 of 5 |
| Task where AIL lost | state-machine change: **+27.9%** |
| AIL system context vs. baseline | 2,085 vs. 75 tokens — pays for itself after ~24 edits/session |

[`spec/05`](spec/05-self-critique.md) §5.2 states what full validation still requires (≥50 tasks, ≥3 codebases, edit success rates).

---

## Limitations (read this before the claims)

The spec audits itself with the same severity it applies to existing paradigms. Full analysis in [`spec/05-self-critique.md`](spec/05-self-critique.md). The short version:

1. **The LLM–IR gap (critical).** Current models are trained on human source text, not IR. Editing WASM directly is *worse* today than editing TypeScript. Mitigation: the graph is truth, but a canonical generated text projection is the editing surface for current-generation models — now specified in [`spec/08`](spec/08-canonical-projection.md).
2. **Input-token evidence is a pilot, not validation.** One corpus, context-size only, known biases (see above). Edit *success rates* under depth-2 context remain unmeasured.
3. **Runtime semantics** — transactions, concurrency, effect ordering — were the largest unwritten section; now specified in [`spec/07`](spec/07-runtime-semantics.md) (atomic scopes, sagas via `compensates` edges, ordered effects, delivery guarantees). Unimplemented.
4. **Ecosystem cold start** — no training data, no tooling, no libraries speak the graph. Adoption must begin as a derived index over existing text repos, not a rewrite — which is exactly what the prototype does.
5. **Human accountability survives** — regulated industries require sign-off; review compresses to semantic deltas + generated projections, it does not disappear.

What would falsify the design is stated explicitly in §5.9.

---

## Projections

[`spec/06-projections.md`](spec/06-projections.md) answers the project's final question — what fraction of current programming constructs survives when AI writes all code:

| Fate | Share |
|------|-------|
| Survives near-unchanged (types, tests, reuse, APIs, transactions) | ~20% |
| Transforms (names→aliases, classes→data nodes, Git→snapshots, review→sign-off) | ~40% |
| Dies (files, folders, comments, imports, inheritance, ceremony) | ~40% |

Adoption path: **derived index over text → graph-first editing with text mirror → boundary inversion → native**. Phase 1 is buildable today and cheaply falsifiable.

---

## Repository Map

```
manual/                          Operating manual (Spanish) — how to work under the paradigm
├── parte-1-modelo.md            The 4 primitives
├── parte-2-reglas.md            35 prescriptive rules across 7 categories
├── parte-3-practica.md          5 operational protocols + 8 anti-patterns
├── parte-4-ejemplo.md           Before/after: blog system, with token counts
├── parte-5-referencia.md        One-page reference — load as AI system context
└── en/part-5-reference.md       English version of the reference page

spec/                            Design specification (English)
├── 01-paradigm-analysis.md      Every construct audited: eliminate / transform / retain
├── 02-new-paradigm-design.md    Full graph design: nodes, edges, identity, memory, compilation
├── 03-token-reduction-mechanisms.md  20+ mechanisms with per-mechanism estimates
├── 04-complete-architecture.md  7-layer system: agents, memory tiers, MCP tools, compiler
├── 05-self-critique.md          The paradigm attacked with its own severity
├── 06-projections.md            What survives, and the adoption path
├── 07-runtime-semantics.md      Transactions, sagas, concurrency, partial failure
└── 08-canonical-projection.md   Generated text editing surface for current models

examples/blog-graph/             The blog system as an actual machine-readable graph
├── graph.json                   74 nodes, 90 typed edges — validated, 13/13 test coverage
└── README.md                    Includes 3 inconsistencies the JSON exposed in the prose

prototype/                       Phase-1 working code (Python, stdlib-only)
├── ail/                         extractor (AST→graph), store, token measurement
├── run_measurement.py           reproduces the pilot results
├── tests/                       13 unit tests
└── results/measurement-results.json

test-resultados.json             Raw token measurements (5 tasks, output-only)
```

**For AI agents:** load [`manual/en/part-5-reference.md`](manual/en/part-5-reference.md) (or the Spanish original) as system context to operate under the paradigm.

**For skeptics:** start with [`spec/05-self-critique.md`](spec/05-self-critique.md) — it is the strongest argument that the rest is worth reading.

---

## Contributing

The highest-value contributions, in order:

1. **Edit-success experiment** — same ≥50 edit tasks given to a model with AIL context vs. whole files; compare success rates and total tokens (the prototype measures context *size*; this measures whether the context is *sufficient*)
2. **Better call resolution in the extractor** — the pilot's 28.6% resolution rate is its weakest point
3. **A second-language extractor (TypeScript)** — application code with heavy cross-file coupling is the hard case
4. **Counterexamples** — real edit tasks where depth-2 locality breaks
5. Formal treatment of the edit-locality invariant

## Related Fields

LLM context optimization · compiler IR design (LLVM, MIR, WASM) · knowledge graphs · AST manipulation · vector databases · MCP protocol · multi-agent systems · information theory · semantic compression

## License

[MIT](LICENSE)

---

*"Software is not text. Software is meaning."*
