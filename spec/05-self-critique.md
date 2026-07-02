# 05. Self-Critique and Limitations

## Overview

This section attacks the paradigm with the same severity applied to existing paradigms in section 01. Every claim in sections 01–04 is audited for weakness. Where a weakness is fatal without mitigation, the mitigation is stated; where no mitigation exists today, that is stated too.

A design that cannot name the conditions under which it fails is not a specification — it is marketing.

---

## 5.1 The LLM–IR Gap (Most Severe)

**The claim under attack:** Behavior lives in binary IR blobs (WASM, LLVM IR); source text is eliminated.

**The problem:** Current LLMs are trained on trillions of tokens of human-readable source code and near-zero tokens of semantically annotated IR. Today, every frontier model is *better* at reading, writing, and editing TypeScript than at editing WASM. The paradigm eliminates the exact representation LLMs are strongest at and keeps the one they are weakest at.

**Severity: CRITICAL.** This inverts the paradigm's core premise for the current model generation.

**Honest assessment of mitigations:**

| Mitigation | Status | Cost |
|---|---|---|
| Canonical text projection: graph is source of truth, a deterministic minimal-text rendering is the *editing surface* the LLM touches | Buildable today | Reintroduces a text layer — but as a generated, canonical, comment-free view (~40–60% smaller than human source), not as stored truth |
| Train/fine-tune models on IR + graph representations | Not available; requires corpus that doesn't exist yet | Chicken-and-egg: the corpus exists only if the paradigm is adopted |
| Constrained decoding into IR grammar | Partially available | Guarantees syntactic validity, not semantic quality |

**Conclusion:** For the current generation, AIL-2 must ship with a canonical text projection as the default editing surface. The pure-IR claim is a projection for future model generations, not a property usable today. Sections 02.9 and 03 should be read with this correction applied.

---

## 5.2 The Measurement Is Weak

**The claim under attack:** Section 03 estimates ~80% aggregate token reduction; the README cites 90–95% input reduction at scale.

**What was actually measured** (`test-resultados.json`):

| Fact | Value |
|---|---|
| Tasks measured | 5 |
| Runs per task | 1 |
| Models tested | 1 |
| Tokens measured | Output only |
| Result | −12.0% output tokens |
| Tasks where AIL cost *more* | 1 of 5 (+27.9%, state-machine change) |

**What was never measured:** input tokens — the entire basis of the 90–95% claim. That number is a projection from the depth-2 loading model, not an observation.

**The system-prompt amortization problem:** the AIL system context costs 2,085 tokens vs. 75 for the baseline. At −85 output tokens saved per edit (average), the AIL context pays for itself only after **~24 edits in a single session**. Short sessions are net-negative.

**The unfavorable case is informative:** Task 4 (adding an "archived" state) cost +27.9% in AIL. Changes that touch a state machine fan out across many small nodes (events, constraints, tests, edges) where a text edit touches one enum and two functions. Graph granularity has a per-node overhead that text amortizes.

**What honest validation requires:** ≥50 tasks, ≥3 codebases of different sizes, input+output tokens, multiple models, and a real graph store — not simulated node payloads. Until then, every number in section 03 is an estimate, and the README must say so.

---

## 5.3 Identity: The Cascade Problem and Its Residue

**The original design was wrong.** v1 identity (`id = sha256(type + signature + ir_hash + dep_ids)`) made the graph a Merkle tree: one leaf edit re-identified every transitive dependent, destroying the edit locality invariant the paradigm is built on. This was a genuine design bug, fixed in section 2.3 (two-level identity: stable `semantic_id` + per-revision `version_hash`).

**The fix has costs of its own:**

- **Deduplication is weakened.** v1 promised structural DRY (identical semantics ⇒ identical ID). Under two-level identity, two nodes with the same signature but different IR share a semantic ID *namespace* but are distinct versions — semantic-level dedup now requires IR equivalence checking, which is undecidable in general and expensive in practice.
- **Unpinned edges introduce temporal ambiguity.** "What does A depend on?" now requires version resolution at snapshot time. The graph gained a package-manager problem (resolution, pinning policy, upgrade waves) that v1 pretended not to have.
- **Signature changes still cascade** — correctly, since they are breaking changes, but a hub node with 400 dependents still forces 400 edge updates. Edit locality holds for behavior edits, not for contract edits. No representation can fix this; it is essential complexity.

---

## 5.4 Runtime Semantics Are Unspecified

The specification covers representation, editing, compilation, and versioning. It does not cover:

| Missing | Why it matters |
|---|---|
| Transaction boundaries | Where does an ACID transaction start and end in a graph of computation nodes? An `effects: ["db:write"]` annotation is not a transaction semantics |
| Concurrency model | Two computation nodes consuming the same event: ordered? parallel? exactly-once? The graph is silent |
| State and resource lifetimes | Connections, file handles, memory ownership across node boundaries — unaddressed |
| Effect ordering | `effects` lists are sets; real systems need sequencing (validate → write → emit) |
| Partial failure | A 5-node computation chain fails at node 3: compensation? retry? The error-event model (2.11) routes errors but does not define recovery semantics |

**Severity: HIGH.** A paradigm that cannot express a bank transfer transactionally is not a general-purpose paradigm yet. This is the largest unwritten section of the spec.

---

## 5.5 Debugging and Observability

A production incident at 03:00 produces a stack trace. In AIL-2, that trace references IR offsets inside content-addressed nodes with no names.

- The human on call needs the generated text projection, the alias index, and the graph — the paradigm's "humans never read code" assumption fails exactly when stakes are highest.
- Logging, tracing, and profiling correlate to nodes, but every existing observability tool (Sentry, Datadog, perf) speaks files and line numbers. The interop layer is unbuilt and nontrivial.
- **Mitigation:** debug metadata mapping IR offsets → node IDs → aliases is exactly what source maps do today. Buildable, but it must be in the compilation spec (04) and currently is not.

---

## 5.6 The Ecosystem Cold-Start Problem

- **Zero training data.** No model has seen an AIL-2 graph. Every capability claim relies on in-context instruction following (the manual), which degrades under context pressure.
- **Zero libraries.** Using any existing package (npm, PyPI, crates) requires wrapping it in boundary nodes. The world's software is text; the graph must import it. An automated text→graph decompiler is required infrastructure and is mentioned nowhere in section 04.
- **Zero tooling.** No debugger, no profiler, no CI, no security scanner speaks the graph. Each must be built or bridged.
- **Migration is the adoption killer.** No organization rewrites working systems into a new representation without incremental value. The realistic wedge: run the graph as a *derived index over existing code* (analysis layer first), and only later invert which representation is the source of truth. The spec currently presents only the end state.

---

## 5.7 Human Accountability Was Eliminated Prematurely

Section 01 eliminates pull requests, commit messages, and human review. But:

- **Review is a trust mechanism, not just a reading mechanism.** Regulated industries (finance, medical, aviation) legally require human accountability for changes. "The merge agent reconciled it" is not an audit trail a regulator accepts in 2026.
- **Semantic deltas are better records than commit messages** — that claim survives. But the *approval* function of a PR survives too, and the spec conflates the two.
- **Correction:** intent nodes + semantic deltas + a human sign-off gate at snapshot promotion. The reviewing human reads generated projections. Human review compresses; it does not disappear.

---

## 5.8 Embedding Fragility

Semantic search (2.14) and intent matching depend on stored embeddings.

- Embeddings are model-versioned. A model upgrade silently degrades or invalidates every stored vector — millions of nodes need re-embedding on every embedding-model change.
- Two agents using different embedding models cannot share semantic search.
- Cosine similarity on intent is probabilistic; graph traversal is exact. Any protocol step that *requires* semantic search to succeed (rather than as a fallback) imports nondeterminism into the edit path.
- **Mitigation:** embeddings are a cache, never truth. Typed signature match and graph traversal must always be sufficient; embeddings only accelerate. The spec mostly respects this but 2.14 oversells search-by-meaning as primary.

---

## 5.9 What Would Falsify This Design

The paradigm is falsified if any of the following holds under honest measurement:

1. Input tokens for local edits on a large real codebase do **not** drop by at least 5× versus a well-organized text repo with a good retrieval layer (the null hypothesis is that RAG over text already captures most of the gain).
2. Frontier models produce lower-quality behavior when editing canonical projections + graph context than when editing idiomatic source files, at equal token budgets.
3. Graph maintenance overhead (edge updates, constraint propagation, version resolution) consumes more agent turns than the context savings return.
4. The depth-2 invariant proves unmaintainable on real domain logic — i.e., real business changes routinely require depth-4+ context, and partitioning to prevent that fragments domains unnaturally (Task 4 in the token test is early evidence in this direction).

None of these have been tested. They define the experimental agenda.

---

## 5.10 Severity Summary

| Weakness | Severity | Mitigated in spec? |
|---|---|---|
| LLM–IR capability gap | CRITICAL | Partially — canonical text projection (5.1) |
| Input-token claims unmeasured | CRITICAL | No — requires experiments (5.9) |
| Runtime semantics missing | HIGH | No — unwritten spec section |
| Ecosystem cold start / migration path | HIGH | Partially — derived-index wedge (5.6) |
| Identity cascade | HIGH | **Yes — two-level identity (2.3)** |
| Debugging / observability | MEDIUM | Sketched — node source maps (5.5) |
| Human accountability | MEDIUM | Yes — sign-off gate at snapshot promotion (5.7) |
| Embedding fragility | LOW | Yes — embeddings as cache, never truth (5.8) |

The paradigm survives its own audit as a **research direction with two critical open dependencies**: models that handle graph+IR representations as well as they handle text, and empirical validation of the input-token claim. It does not survive as a production-ready replacement for text-based programming in 2026 — and does not claim to.
