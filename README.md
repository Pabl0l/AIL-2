# AIL-2 — AI Language: A New Programming Paradigm

> **By 2026, humans won't be writing in stone, much less code. AI will be doing it all.**
> So we need to leave behind old programming paradigms and welcome a new era.

---

## The Problem with Code as We Know It

Every programming construct we use today was designed for human cognition, not machine processing.

- **Files** exist because humans need to navigate
- **Folders** exist because humans need to organize
- **Comments** exist because humans need explanations
- **Class inheritance** exists because humans think in taxonomies
- **Variable names** exist because humans need readable identifiers

When an AI reads your code, it converts: `text → AST → semantics`. That intermediate step is pure waste.

**~60–70% of current programming constructs exist for human cognitive reasons, not computational ones.**

---

## The Solution: Software as a Semantic Graph

AIL-2 defines a programming paradigm where software exists **directly in its semantic representation** — no source files, no folders, no comments.

```
The Axiom:
Software is a typed semantic graph.
Nodes are units of meaning.
Edges are typed relationships.
Source text is a generated artifact, never the source of truth.
```

Every edit an AI needs to make loads at most **depth-2 from the target node** — typically 5–20 nodes, regardless of how large the codebase is.

---

## What This Means in Numbers

| Metric | Traditional Paradigm | AIL |
|--------|---------------------|-----|
| Tokens to understand all business rules | 50,000+ | ~1,800 |
| Tokens for a typical local edit | 3,200–4,500 | ~420 |
| Files touched to add a cross-cutting rule | 3–8 files | 1 constraint node + N edges |
| Business rules explicitly declared | 0 (buried in code) | 1 node per rule |
| Context needed regardless of codebase size | Scales with codebase | Bounded at depth-2 |

**At global AI compute scale:** ~90–95% reduction in input tokens for large codebases translates to hundreds of millions of dollars in compute savings annually.

---

## The 4 Primitives

Everything in AIL is built from 4 primitives:

### 1. Semantic Node (7 types)

| Type | Replaces | Contains |
|------|---------|---------|
| `computation` | function, method, handler | executable IR |
| `data` | struct, DTO, entity | typed fields, no methods |
| `constraint` | comment, assertion, validation | verifiable business rule |
| `event` | exception, domain event, message | typed occurrence with payload |
| `test` | unit/integration test | given/expect specification |
| `boundary` | endpoint, API, port | external entry/exit point |
| `ontology` | documentation, DDD concept | domain concept definition |

### 2. Typed Edge (10 types)

```
depends-on      A needs B to execute
composed-of     A has a field of type B
constrained-by  B is a rule A must follow
tests           A verifies behavior of B
produces        A emits events of type B
consumes        A processes events of type B
dispatches-to   A can resolve as B (polymorphism)
boundary-exposes A exposes B externally
derives-from    A is a modified version of B
belongs-to      A belongs to domain/partition B
```

### 3. Graph

The complete software system. Navigation is by typed traversal or semantic search — never text search.

### 4. Snapshot

The versioning unit. Not a text diff. A complete, immutable graph state. Rollback = restore snapshot.

---

## What No Longer Exists

```
✗ Source code files as primary unit
✗ Folders and directory structure
✗ Classes and inheritance
✗ Explanatory comments
✗ Manually maintained documentation
✗ Import / require / use statements
✗ Try/catch embedded in business logic
✗ Getters, setters, constructors
✗ Validation embedded in computation functions
✗ Text search (grep) to navigate the system
✗ Text diffs to version changes
✗ Natural language commit messages
✗ Pull requests as review mechanism
```

---

## Example: Blog System

**Traditional approach:**
- 43 files, ~2,800 lines of code
- 3,200–4,500 tokens for a typical edit
- 0 explicitly declared business rules

**AIL:**
- 0 files
- 65 nodes (8 ontology + 6 constraint + 4 data + 9 computation + 11 event + 21 test + 6 boundary)
- ~420 tokens for the same edit
- 6 explicit constraint nodes — each business rule is a first-class citizen

**At 10× scale:**
- Traditional: 50,000+ tokens to understand all rules
- AIL: ~1,800 tokens

---

## The Token Test

We ran 5 identical tasks in both paradigms and measured output tokens:

| Task | Senior Dev | AIL | Savings |
|------|-----------|-----|---------|
| Business rule: no negative stock | 797 | 643 | -19.3% |
| Rate limiting on write operations | 622 | 484 | -22.2% |
| Bug: comments on draft articles | 591 | 471 | -20.3% |
| New "archived" article state | 653 | 835 | +27.9% |
| Stock notification logic change | 889 | 692 | -22.2% |
| **Total** | **3,552** | **3,125** | **-12.0%** |

The 12% output savings is the **measurable** part. The real gains come from input token reduction — when working on large codebases, AIL's depth-2 constraint means loading 500–1,500 tokens instead of 20,000–80,000.

---

## The Manual

This repository contains a complete manual written so that **any AI (or person) can read it and immediately adopt this paradigm as their coding foundation**.

```
manual/
├── parte-1-modelo.md       The 4 primitives: nodes, edges, graph, snapshot
├── parte-2-reglas.md       35 prescriptive rules across 7 categories
├── parte-3-practica.md     5 operational protocols + 8 anti-patterns
├── parte-4-ejemplo.md      Before/after: blog system (token counts included)
└── parte-5-referencia.md   One-page condensed reference (load as AI system context)

spec/
├── 01-paradigm-analysis.md    Critical analysis: what exists for humans vs. computers
├── 02-new-paradigm-design.md  Full graph design, node schemas, identity, memory
├── 03-token-reduction.md      20+ mechanisms, aggregate ~80% reduction estimate
└── 04-complete-architecture.md Full system: 7 layers, 7 agents, MCP catalog
```

**Start here:** [`manual/parte-5-referencia.md`](manual/parte-5-referencia.md) — designed to be loaded as the system context for any AI session.

---

## Core Design Decisions

**Content-addressed identity:**
```
ID = sha256(type + canonical_signature + IR_hash + sorted(dep_IDs))
```
Names are aliases in metadata. Identity never changes when you rename something.

**Edit locality rule:**
Any local edit requires loading at most depth-2 from the target node. Typical edit = 5–20 nodes. This property holds regardless of total codebase size.

**Immutable nodes:**
Nodes never mutate. Changes create new nodes with `derives-from` edges. The graph accumulates history without explicit versioning overhead.

**Business rules as constraint nodes:**
Every business rule is exactly one `constraint` node, attached via `constrained-by` edges to N computation nodes. Adding a cross-cutting rule means creating 1 node + N edges — never modifying N functions.

---

## For AI Agents

To operate under this paradigm, load [`manual/parte-5-referencia.md`](manual/parte-5-referencia.md) as your system context. It contains:

- All 7 node types
- All 10 edge types
- All rules condensed to one page
- Work order and edit protocol
- Decision table for common situations
- Reference metrics and glossary

No additional context needed for standard operations.

---

## Status

This is a research project and living specification. The paradigm is fully defined. Implementation (graph store, compiler, agent toolkit) is the next phase.

**Contributions welcome** — especially:
- Formal proofs of the edit locality property
- Token measurement studies on real codebases
- Implementation proposals for the IR format
- Counterexamples that challenge the design

---

## Related Fields

This work intersects: LLM context optimization, compiler IR design (LLVM, MIR, WASM), knowledge graphs, AST manipulation, vector databases, MCP protocol, multi-agent systems, information theory, and semantic compression.

---

*"Software is not text. Software is meaning."*
