# 03. Token Reduction Mechanisms

## Overview

This section enumerates every concrete mechanism for reducing the token cost of AI software manipulation. Each mechanism targets a specific source of token waste in the current paradigm. Estimates are based on empirical analysis of typical TypeScript/Python codebases loaded into LLM contexts.

The aggregate goal: reduce the tokens required for an AI to perform any local edit from the current average of **3,000–15,000 tokens** to a target of **200–800 tokens**.

---

## Baseline: Where Tokens Go Today

When an AI edits a function in a modern codebase, it typically loads:

| Token source | Tokens (typical) | Necessary? |
|---|---|---|
| File header + imports | 150–400 | 10% — mostly path noise |
| Class/module boilerplate | 100–300 | 0% for AI |
| Variable/function names | 200–500 | 0% (aliases, not identity) |
| Comments (explanatory) | 150–400 | 0% |
| Type annotations (verbose) | 200–600 | 30% carry real type info |
| Business logic (actual behavior) | 200–800 | 100% |
| Test context | 300–1,000 | 50% useful, 50% ceremony |
| Surrounding functions (for context) | 500–3,000 | 20% relevant |
| **Total** | **1,800–7,000** | **~25% truly necessary** |

The signal-to-noise ratio in typical code loaded as context is approximately 1:3 to 1:4. The following mechanisms attack each noise source.

---

## Category 1: Naming Reduction

### M1.1 — Internal IDs Replace Long Names

**Mechanism:** All internal references use content-addressed IDs (`sn:a4f2e9b7`) instead of descriptive strings. Human aliases are stored as metadata, never included in context unless the agent explicitly requests them.

**Token reduction:**
- `UserMainMenuConfigurationController` = 7 tokens → `sn:a4f2` = 2 tokens
- 50 identifiers in a typical context: 350 → 100 tokens
- **Estimated saving: 250 tokens / context (7%)**

### M1.2 — Alias Deferred Loading

**Mechanism:** When loading a node for editing, aliases are not included in the default payload. They are loaded only when: (a) generating human-readable output, or (b) the agent explicitly queries `graph.get_alias(id)`.

**Token reduction:** Alias strings across a 20-node working graph: ~100–200 tokens saved per edit if aliases are never needed.

### M1.3 — Type Signature as Compressed Identity

**Mechanism:** Type signatures are stored in a typed schema format, not as text strings. `(input: UserAccountBalance, amount: Money) → Result<Transfer, InsufficientFundsError>` = ~20 tokens as text, ~5 tokens as a typed schema reference.

**Token reduction:**
- 10 computation nodes in context, each with typed signature: ~200 → 50 tokens
- **Estimated saving: 150 tokens / context (4%)**

---

## Category 2: Comment and Documentation Elimination

### M2.1 — Explanatory Comment Removal

**Mechanism:** All comments that explain WHAT code does are removed from the semantic graph. The node's type, signature, and behavior IR encode this information structurally.

**Token reduction:**
- Typical file: 15–25% of lines are comments
- 300-token file context: 45–75 comment tokens eliminated
- **Estimated saving: 60 tokens / file context (4–8%)**

### M2.2 — Constraint Comments → Constraint Nodes

**Mechanism:** Comments encoding constraints (`// must not be called from async context`, `// balance must be checked before calling`) become constraint nodes. In context, constraint nodes are represented as compact typed objects, not prose strings.

**Compression factor:**
- Prose constraint comment: ~20 tokens
- Compact constraint node reference: ~4 tokens (ID + severity)
- **Compression ratio: 5:1**

### M2.3 — TODO / FIXME → Issue Nodes

**Mechanism:** In-code TODO comments become issue nodes with typed fields (priority, blocking_node, description_embedding). Not loaded in edit context unless the edit explicitly addresses the issue.

**Token reduction:** Average of 3–8 TODOs per file; each ~10 tokens. Zero loaded in normal edit context.

### M2.4 — Documentation Elimination from Edit Context

**Mechanism:** Documentation prose is never loaded into edit context. Domain ontology nodes provide structured semantic context. An AI editing a payment computation node loads domain ontology nodes (`on:settlement`, `on:counterparty`) — structured, ~30 tokens each — not a 5,000-token documentation page.

**Token reduction:**
- Current: documentation string in JSDoc above function = 50–500 tokens
- New: zero (documentation is derivable output, not input)
- **Estimated saving: 100–500 tokens / context**

---

## Category 3: Boilerplate Elimination

### M3.1 — Constructor Boilerplate

**Mechanism:** Data nodes have no construction ceremony. A data node IS its field schema. No constructor method, no builder pattern, no factory class.

**Token reduction:**
- Typical TypeScript class constructor with 5 dependencies: 100–200 tokens
- Data node schema: 20–40 tokens
- **Compression ratio: 5:1 for data initialization code**

### M3.2 — Import Statement Elimination

**Mechanism:** Dependencies are explicit graph edges, not import statement text at file heads. No import resolution, no import paths, no barrel exports, no circular import debugging.

**Token reduction:**
- Typical file with 15 imports: 200–400 tokens in import statements
- Graph-based dependencies: 0 tokens in context (edges are resolved at query time, not loaded as text)
- **Estimated saving: 300 tokens / file context (10–15%)**

### M3.3 — Interface Implementation Boilerplate

**Mechanism:** `implements IPaymentService` is a type constraint edge, not text. Repeated method signatures in implementing classes are eliminated — the constraint edge references the type schema once.

**Token reduction:**
- TypeScript class implementing 2 interfaces with 5 methods each: 300–500 tokens of repeated signatures
- Edge + schema: ~30 tokens
- **Compression ratio: 10–15:1**

### M3.4 — Getter / Setter Elimination

**Mechanism:** Data nodes have no methods. Field access is direct (mediated by access edges, not getter/setter methods). The `public get userId(): string { return this._userId; }` pattern disappears entirely.

**Token reduction:** ~20 tokens per getter/setter pair. A typical entity class with 10 fields: 200 tokens saved.

### M3.5 — ORM Entity Annotation Elimination

**Mechanism:** Database mapping is a compilation target annotation, not inline code. `@Entity()`, `@Column()`, `@ManyToOne()` decorators disappear — the storage mapping is derived from data node field types and constraint nodes.

**Token reduction:** ~50–150 tokens per entity class.

---

## Category 4: Structural Compression

### M4.1 — AST Representation vs Text

**Mechanism:** Behavior is stored as IR (WASM bytecode / LLVM IR), not text. IR is structurally typed, compact, and unambiguous.

**Compression factor:**
- A 20-line TypeScript function: ~500 text characters = ~200 tokens
- Same function as WASM bytecode: ~100–200 bytes = not loaded as tokens (stored as binary blob, referenced by hash)
- When loaded for structural analysis: AST has ~50–100 nodes, each ~5 tokens = 250–500 tokens
- **Key insight:** The IR is loaded only when the AI needs to modify behavior. For most edits (adding constraints, changing structure), the IR is never loaded — only the signature and dependency edges.

### M4.2 — Schema-Based Node Compression

**Mechanism:** Common node structures (data schemas, constraint schemas, test schemas) are stored as schema types. Nodes reference schema types rather than repeating structure. When loading a context of 20 data nodes with the same schema, the schema is loaded once (~50 tokens); all 20 nodes reference it (~2 tokens each).

**Token reduction:**
- 20 data nodes without schema sharing: 20 × 50 tokens = 1,000 tokens
- 20 data nodes with schema sharing: 50 + 20 × 2 = 90 tokens
- **Compression ratio: 11:1 for structurally similar nodes**

### M4.3 — Delta Encoding for History

**Mechanism:** Version history is stored as deltas, not full snapshots. Loading the history of a node costs O(delta_size), not O(full_graph_size).

**Token reduction for history queries:**
- Current: loading 3 versions of a file = 3 × full file tokens
- New: loading 3 version deltas = 3 × change set tokens (typically 10–30 tokens per delta)

### M4.4 — Reference Deduplication

**Mechanism:** Two semantic nodes with identical content share a single ID (by content-addressed derivation). In graph storage, this is a single physical node. In context loading, a node appearing in multiple subgraphs is loaded once and referenced by ID multiple times.

**Token reduction:** In refactored codebases with shared utilities, this can reduce context size by 20–40% when multiple entry points use the same shared computation nodes.

---

## Category 5: Context Loading Optimization

### M5.1 — Depth-Limited Subgraph Loading

**Mechanism:** Edit context is bounded to `depth=1` for normal edits (direct dependencies + direct dependents). Only complex edits requiring understanding of transitive dependencies expand to `depth=2`. Never depth=3 or beyond without explicit agent reasoning.

**Token reduction:**
- Current: loading a file loads all its imports (transitive); a 5-hop dependency chain = hundreds of files potentially touched
- New: depth=1 loads exactly 5–15 nodes; depth=2 loads 20–60 nodes
- **Token reduction: 80–95% vs. current file-based loading for typical edits**

### M5.2 — Type-Filtered Context

**Mechanism:** When an AI loads a node's neighborhood, it filters by edge type. For an edit that changes behavior: load `computation` and `constraint` nodes. Ignore `test` nodes (unless verifying), `ontology` nodes (unless domain reasoning needed), `boundary` nodes (unless changing API surface).

**Token reduction:**
- Full neighborhood of a node: 20–50 nodes
- Behavior-change context (computation + constraints only): 5–15 nodes
- **Token reduction: 50–70%**

### M5.3 — Semantic Caching

**Mechanism:** When two edits in a session access overlapping subgraphs, the shared portion is cached in the session index (Tier 2 memory). Subsequent loads retrieve from cache at ~2 tokens/node (summary) rather than full node payload.

**Token reduction:** For iterative editing sessions (common in feature development), context loading cost drops 40–60% after the first few edits establish the cache.

### M5.4 — Constraint Boundary Detection

**Mechanism:** Constraint nodes define the boundary of context loading. If node A has a `constrained-by` edge to constraint C, and C specifies `scope: local` (the constraint is fully local to A), the AI knows it can edit A without understanding A's callers. This eliminates the need to load the caller context.

**Token reduction:** For edits within a locally-constrained node: eliminates loading of all caller/dependent context. Estimated 30–50% reduction in edit context.

### M5.5 — Pinned Core Context

**Mechanism:** Domain ontology nodes and project-level constraint nodes are pinned in Tier 2 (session index) at session start. They never consume Tier 1 context budget. When the AI needs domain context, it retrieves from the session index at low cost (~2 tokens/node reference), not from the full graph store.

**Token reduction:** Eliminates the per-edit cost of loading domain context (which would otherwise cost 100–500 tokens per domain-relevant edit).

---

## Category 6: Knowledge Concentration

### M6.1 — Single Business Rule Source

**Mechanism:** Business rules are defined in constraint nodes and applied via `constrained-by` edges to N computation nodes. The rule is stored once. When editing any of the N computation nodes, the constraint node is loaded once in context (~30 tokens), not N copies of the same prose comment.

**Current situation:** DRY is violated constantly at the comment level. The rule "amount must be positive" appears in JSDoc above 8 different payment methods, in 3 validation functions, and in 2 README files. Total: ~400 tokens across a session.

**New situation:** One constraint node, 8 `constrained-by` edges. Context cost: ~30 tokens once per session.

**Token reduction: 13:1 for constraint knowledge**

### M6.2 — Cross-Cutting Concern Externalization

**Mechanism:** Authentication, authorization, logging, rate limiting, and caching are expressed as constraint nodes and aspect edges — never as embedded code in computation nodes. A computation node that requires authentication has a `constrained-by` edge to an auth constraint node. The auth logic is a separate computation node.

**Current situation:** Auth logic embedded in every controller method (50–200 tokens per method), plus middleware (500+ tokens), plus interceptors (500+ tokens).

**New situation:** Auth constraint node (30 tokens) + auth computation node (loaded once). All computation nodes reference via edge (2 tokens each).

**Token reduction: 20–50× for cross-cutting concern loading**

### M6.3 — Shared Test Patterns

**Mechanism:** Test templates are reusable test nodes. A new computation node inherits applicable test templates via `applicable-template` edges. The AI does not re-specify the test structure — it parameterizes the template.

**Token reduction:** Test specification for a CRUD operation: current ~500–1,000 tokens. Template instantiation: ~100 tokens.

---

## Category 7: Representation Format Optimization

### M7.1 — Binary IR vs Text for Behavior

**Mechanism:** Computation node behavior is stored as binary IR, never loaded as text into the AI context. When the AI needs to understand or modify behavior, it receives the IR as a structured AST (not text), which is ~5× more information-dense than equivalent text code.

**Implementation today:** WebAssembly (WASM) is a binary format with a well-defined text representation (WAT). LLVM IR has both binary and text forms. Both are usable today.

### M7.2 — Typed Schema Encoding

**Mechanism:** Data types are encoded as typed schema references (IDs), not as inline type declarations. `PaymentAmount` is referenced as `type:on:payment-amount` (5 tokens) rather than declared inline as `{ currency: string, cents: number, precision: 2 }` (15 tokens). The schema is loaded once when needed.

**Compression ratio: 3:1 for type declarations**

### M7.3 — Embedding-Based Semantic Lookup

**Mechanism:** Intent embeddings on semantic nodes enable lookup by meaning, not by traversal. When the AI needs to find "the node that validates payment amounts," it queries the vector index for the nearest embedding to "validate payment amount" — returning the correct node in ~2 tokens of query overhead, rather than a full-text search across thousands of files.

**Token reduction for search:** Current semantic search in a codebase requires loading grep results (100–500 tokens of matches + surrounding context). Vector search returns a ranked list of node IDs (~10–20 tokens).

---

## Aggregate Estimated Reduction

Applying all mechanisms to a typical edit operation:

| Mechanism category | Current tokens | New tokens | Reduction |
|---|---|---|---|
| Import statements | 300 | 0 | −300 |
| Variable/function names | 400 | 100 | −300 |
| Comments | 300 | 30 | −270 |
| Boilerplate (class, constructor, interfaces) | 500 | 50 | −450 |
| Surrounding functions (depth overflow) | 2,000 | 0 | −2,000 |
| Business rules (duplicated) | 400 | 60 | −340 |
| Type declarations (verbose) | 300 | 80 | −220 |
| Actual logic to edit | 400 | 400 | 0 |
| Test context (relevant) | 200 | 200 | 0 |
| Constraint context | 200 | 80 | −120 |
| **Total** | **5,000** | **1,000** | **−80%** |

**Target achieved:** 5,000 → 1,000 tokens for a typical edit. For complex edits requiring deeper context, the reduction is smaller (~50%) but still substantial.

---

## Token Reduction Hierarchy (Priority Order)

When implementing token reduction, apply in this order (highest impact first):

1. **Eliminate file-based loading** → replace with depth-limited subgraph loading (largest single reduction)
2. **Eliminate boilerplate** → constructor, imports, interface implementation ceremony
3. **Concentrate business rules** → single constraint nodes vs. duplicated prose
4. **Externalize cross-cutting concerns** → auth, logging, caching as edges, not embedded code
5. **Eliminate explanatory comments** → zero loss of information, significant token saving
6. **Compress naming** → IDs instead of descriptive strings for internal references
7. **Schema-based node compression** → shared schemas for similar nodes
8. **Semantic caching** → session-level cache for hot nodes
9. **Binary IR for behavior** → not loaded as text unless being modified
10. **Embedding-based search** → replace text search with vector similarity

---

## What Cannot Be Reduced

Some token costs are irreducible — they reflect genuine information:

| Irreducible cost | Reason |
|---|---|
| Actual computation logic (behavior to edit) | The semantic content being changed |
| Direct dependency signatures | Needed to type-check the edit |
| Constraint content (business rules) | Genuine domain knowledge, not derivable |
| Test specifications for the target node | Required to verify edit correctness |
| Domain ontology for the relevant domain | Real semantic context needed for correct edit |

These irreducible costs total approximately **300–600 tokens** for a focused local edit. Any system claiming to perform correct edits in fewer tokens is either: (a) ignoring correctness requirements, or (b) has pre-computed the context into embeddings that substitute for explicit token loading (which is a valid approach but should be stated explicitly).
