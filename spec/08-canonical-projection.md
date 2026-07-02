# 08. Canonical Text Projection

## Overview

Section 05 (§5.1) identified the paradigm's most severe weakness: current LLMs are trained on human source text, not IR. Storing behavior only as WASM/LLVM blobs makes the graph *less* editable by the very agents it is designed for.

The resolution: **the graph remains the sole source of truth, but the editing surface for current-generation models is a deterministic, minimal, generated text form** — the canonical projection. Agents read projections, propose edits as projection text, and the toolchain parses edits back into graph operations. When future models handle graph/IR natively, the projection becomes optional; nothing else changes.

This is not a retreat to files. The differences are structural, not cosmetic (see §8.6).

---

## 8.1 Requirements

| # | Requirement | Rationale |
|---|---|---|
| R1 | **Deterministic** — same subgraph ⇒ byte-identical projection | Diffs of projections are meaningful; caching works; no style variance |
| R2 | **Minimal** — zero tokens that don't carry semantics | The entire point of the paradigm |
| R3 | **Round-trippable** — parse(project(G)) = G for the projected scope | Edits must map back to graph operations losslessly |
| R4 | **Scoped** — projects exactly the depth-2 edit context, never a "file" | Edit locality is preserved through the text layer |
| R5 | **In-distribution** — syntax close to what models know | The projection exists *because* of model training distribution; alien syntax would defeat it |

R5 decides the key design question: the projection uses a **typed, Python-like expression syntax** for behavior bodies — not S-expressions, not a novel notation. Models are strongest exactly there.

---

## 8.2 Projection of an Edit Context

An edit context (target node + depth-1 dependencies + constraints + tests + dependents, per §2.4) projects as one text unit:

```ail
#context sn:7f3a @ v:c41b        ; target
#partition cp:blog-write-path

; --- constraints in force (read-only in this context) ---
constraint cn:91d2 "comments only on published articles"
  severity error
  verify sn:20c9

constraint cn:4be0 "author must be active"
  severity error
  verify sn:88a1

; --- dependencies (signatures only, read-only) ---
dep sn:20c9 : (article: dn:article) -> bool           ; alias check-published
dep sn:88a1 : (author: dn:user) -> bool               ; alias check-author-active
dep dn:comment = { article: dn:article, author: dn:user, body: text(1..2000) }

; --- target (editable) ---
computation sn:7f3a : (input: dn:comment-input) -> result<dn:comment, ev:rejected>
  constrained-by cn:91d2, cn:4be0
  effects [1 db:read on:article] [2 db:write on:comment] [3 event:emit ev:comment-created]
  deterministic false
  body:
    article = load(input.article_id)
    require cn:91d2: sn:20c9(article)
    require cn:4be0: sn:88a1(input.author)
    comment = dn:comment(article=article, author=input.author, body=input.body)
    store(comment)
    emit ev:comment-created(comment)
    return ok(comment)

; --- tests (editable) ---
test tn:5e02 tests sn:7f3a
  given input = { article_id: fixture:published-article, author: fixture:active-user, body: "x" }
  expect ok, effects [db:write on:comment ×1, event:emit ev:comment-created ×1]

test tn:9a44 tests sn:7f3a
  given input = { article_id: fixture:draft-article, author: fixture:active-user, body: "x" }
  expect ev:rejected(cn:91d2)

; --- dependents (signatures only, must not break) ---
dependent bn:post-comment : boundary POST /articles/{id}/comments -> sn:7f3a
```

Everything a current-generation model needs, nothing it doesn't: no imports, no class ceremony, no comments-as-prose (constraints are typed lines), no code from dependencies (signatures only), no unrelated functions from a shared file.

---

## 8.3 Grammar Rules

1. **IDs are short-form** — `sn:7f3a` (first 4 hex chars) within a context; the projection header carries the full-hash mapping table out-of-band. Collisions within a context are resolved by lengthening only the colliding IDs.
2. **Aliases appear only as trailing `; alias` annotations** and are ignored by the parser. R2 with a concession to R5: models reason better with one human hint per node than with zero.
3. **Order is fixed**: constraints → dependencies → target → tests → dependents. Within each block, ascending ID order. This is what makes projection deterministic (R1).
4. **Behavior bodies** use expression syntax with exactly five statement forms: binding (`=`), `require` (constraint check), effect calls (`load/store/emit` mapped from the effect list), `return`, and `match` for sum types. Control flow beyond `match` and expression conditionals must be decomposed into further computation nodes — the projection *enforces* node granularity by refusing to express big procedures.
5. **No whitespace or formatting freedom** — the emitter has one legal output per graph state.

## 8.4 Parsing Edits Back

The agent returns the modified projection. The toolchain:

1. Parses the text → typed AST (small grammar, ~30 productions).
2. Diffs against the projected subgraph — *semantic* diff: changed body ⇒ new version of target; new `require` line ⇒ new `constrained-by` edge; new test block ⇒ new test node.
3. Rejects out-of-scope edits: touching a `dep`/`dependent` line (read-only blocks) fails with a typed error telling the agent to open a new edit context on that node. Scope discipline is mechanical, not prompted.
4. Compiles the new body to IR, recomputes `version_hash`, produces the snapshot delta.

Failure modes are typed events the agent consumes and repairs: `parse-error(line)`, `type-mismatch(expected, got)`, `scope-violation(node)`, `constraint-unsatisfied(cn)`.

## 8.5 Token Budget

Measured on the example above (§8.2): the full edit context projects to **~340 tokens**. The equivalent traditional context (controller file + model + validator + test file, per manual/parte-4) is 3,200–4,500 tokens. The projection layer costs nothing at rest — it is generated on demand and never stored.

## 8.6 Why This Is Not "Files Again"

| Property | File | Canonical projection |
|---|---|---|
| Stored? | Yes — is the truth | No — generated per edit, discarded after |
| Scope | Whatever humans grouped | Exactly the depth-2 edit context |
| Contains | Everything in the file | Target + signatures of neighbors |
| Style | Author-dependent | Byte-deterministic |
| Comments | Prose, unverifiable | Typed constraint lines, verifiable |
| Edit granularity | Text range | Graph operation (checked, typed) |
| Identity | Path + name | Content-addressed IDs |

The projection is a *view*, in the database sense. Nobody argues SQL result sets mean tables don't exist.

## 8.7 Open Questions

1. **Body syntax expressiveness** — five statement forms may be too austere for numeric/algorithmic nodes (a matrix kernel decomposed into 40 nodes is worse, not better). Likely resolution: an `opaque body` escape hatch projecting the IR's own text format (WAT for WASM) for algorithm-dense nodes, accepting weaker model performance there.
2. **How much neighbor context is optimal** — signatures-only (current design) vs. signatures + one-line intent summaries. Needs measurement, not opinion; belongs in the Phase-1 experiment set.
3. **Grammar versioning** — the projection grammar itself needs versioning so stored agent transcripts remain interpretable. Proposal: grammar version in the `#context` header.
