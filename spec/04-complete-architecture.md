# 04. Complete Architecture

## Overview

This section designs the full AIL-2 system architecture — every component, every integration, and the complete workflow from human intent to deployed software. All components are buildable today using existing technology. No hypothetical hardware or AI capabilities required.

---

## 4.1 System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│  HUMAN INTERFACE LAYER                                              │
│  Natural language / intent language / constraint declarations        │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Intent nodes
┌──────────────────────────▼──────────────────────────────────────────┐
│  ORCHESTRATING AGENT                                                │
│  Intent parsing → decomposition → agent dispatch → synthesis        │
└──────┬───────────────────┬──────────────────┬───────────────────────┘
       │                   │                  │
┌──────▼──────┐  ┌─────────▼─────┐  ┌────────▼────────┐
│ AGENT POOL  │  │ MEMORY SYSTEM │  │  MCP TOOL LAYER │
│ Specialized │  │ 3-tier cache  │  │  Graph / Compile │
│ agents      │  │               │  │  / Deploy tools  │
└──────┬──────┘  └───────────────┘  └────────┬────────┘
       │                                      │
┌──────▼──────────────────────────────────────▼───────────────────────┐
│  SEMANTIC GRAPH STORE                                               │
│  Property graph DB + vector index + version history                  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Compiled subgraph
┌──────────────────────────▼──────────────────────────────────────────┐
│  COMPILATION LAYER                                                  │
│  Graph → IR → LLVM/Cranelift → target artifacts                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Artifacts
┌──────────────────────────▼──────────────────────────────────────────┐
│  DEPLOYMENT LAYER                                                   │
│  Container registry / serverless / edge / WASM runtime               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4.2 Human Interface Layer

### Purpose

The only point where a human interacts with the software creation process. Input is natural language or a simplified intent notation. Output is a set of **intent nodes** in the semantic graph.

### Input Modes

**Mode 1 — Natural language:**
> "Create an inventory system with products, warehouses, and stock movements. Notify the warehouse manager when stock drops below the reorder point."

**Mode 2 — Intent notation (structured):**
```yaml
intent: inventory-system
entities:
  - Product: { sku: string, name: string, reorder_point: quantity }
  - Warehouse: { code: string, location: address }
  - StockMovement: { sku: ref:Product, warehouse: ref:Warehouse, quantity: quantity, direction: in|out }
rules:
  - when: stock_level < product.reorder_point
    then: notify(warehouse_manager, low_stock_event)
  - requires_auth: [warehouse_manager, admin]
```

**Mode 3 — Constraint declaration (for rule updates):**
> "Add: stock movements above $10,000 require manager approval"

### Output

Intent nodes:
```json
[
  {
    "id": "intent:inventory-system-v1",
    "type": "system_intent",
    "entities": [...],
    "behaviors": [...],
    "constraints": [...],
    "actors": [...],
    "created_at": "2026-06-30T00:00:00Z"
  }
]
```

### Interface Technology (Today)

- A simple web UI or CLI accepting text input
- An LLM call to parse natural language → intent notation (one API call)
- A schema validator for the intent notation
- A graph writer that creates intent nodes

This is buildable today with: a React/HTMX frontend or CLI, any LLM API (Claude API, GPT-4 API), and the graph store.

---

## 4.3 Orchestrating Agent

### Purpose

The central coordinator. Receives intent nodes, decomposes them into a work plan, dispatches to specialized agents, and monitors progress. Never generates code directly.

### Responsibilities

1. **Intent interpretation** — parse intent nodes into concrete work items
2. **Existing node matching** — query the semantic graph for nodes that already satisfy parts of the intent ("do we already have a Product data node?")
3. **Gap identification** — determine which required nodes don't exist yet
4. **Agent dispatch** — assign work items to appropriate specialized agents
5. **Dependency ordering** — ensure agents work in dependency order (data nodes before computation nodes, computation nodes before boundary nodes)
6. **Progress tracking** — monitor agent outputs, detect failures, retry or reassign
7. **Verification gate** — before any compilation, confirm all constraints are satisfied

### Decision Loop

```
WHILE intent_not_satisfied:
  gaps = query_graph(what is missing vs intent?)
  if no gaps:
    trigger_verification()
    if verification_passes:
      trigger_compilation()
      break
    else:
      dispatch(fix_agent, verification_failures)
  else:
    prioritize(gaps)  # data before computation before boundary
    for each gap in priority_order:
      dispatch(appropriate_agent, gap)
      wait_for_completion(gap)
```

### Technology (Today)

- Claude API with tool use (MCP tools for graph operations)
- Or: any LLM with function calling + a custom orchestration loop
- The orchestrating agent is a standard agentic loop — no novel technology needed

---

## 4.4 Agent Pool

Each agent specializes in exactly one transformation. Agents are stateless — they read from the graph, produce new/modified nodes, and write back. They communicate only via the semantic graph, never directly with each other.

### Agent Definitions

#### 4.4.1 Decomposition Agent

**Input:** High-level intent node or complex computation requirement
**Output:** 2–10 smaller, more specific nodes (domain nodes, operation requirements, constraint candidates)

**Triggers when:** Intent nodes contain multiple undecomposed concepts, or a computation requirement is too large for one synthesis step (> 50 tokens of behavior specification)

**Technology:** LLM call with structured output schema. Prompt: "Break this intent into atomic computational requirements. Each requirement should correspond to exactly one computation node."

#### 4.4.2 Synthesis Agent

**Input:** Computation requirement node + dependency nodes + constraint nodes
**Output:** Computation node with IR blob

**Process:**
1. Load requirement + direct dependency type signatures
2. Check for existing computation nodes with matching signatures (hash lookup, then semantic search)
3. If match found: create `derives-from` edge, done
4. If no match: generate IR (via LLM → text code → compiler → IR, or direct IR generation)
5. Write computation node to graph
6. Declare dependency edges

**Technology:** LLM generates source code in a target language → compiler (tsc, rustc, zig) → IR extraction → binary blob storage. The source code is a transient artifact, discarded after compilation.

#### 4.4.3 Test Agent

**Input:** Computation node + constraint nodes that apply to it
**Output:** 3–10 test nodes targeting the computation node

**Process:**
1. For each constraint node: generate one test node per constraint requirement
2. For the computation node's signature: generate boundary cases (null inputs, empty collections, maximum values)
3. For the computation node's domain: load domain ontology nodes, generate domain-meaningful test scenarios

**Technology:** LLM call with computation node + constraints as context. Output: structured test node JSON (no code generation needed — test nodes are data).

#### 4.4.4 Verification Agent

**Input:** Set of computation nodes + their test nodes + their constraint nodes
**Output:** Verification report (pass/fail per node, coverage percentage, constraint violations)

**Process:**
1. Execute test nodes against computation nodes (run the IR blobs with test inputs)
2. Check constraint nodes: for each constraint with `verifiable: true`, run its `verification_node`
3. Check dependency edge consistency: type signatures at both ends of each `depends-on` edge must be compatible
4. Compute coverage: `|computation_nodes_with_tests| / |computation_nodes|`

**Technology:** A test runner that can execute WASM bytecode blobs with JSON inputs and verify JSON outputs. Today: Node.js with WASM runtime, or any language with a WASM interpreter.

#### 4.4.5 Optimization Agent

**Input:** A subgraph of recently modified nodes
**Output:** Modified nodes with reduced dependency footprint or equivalent IR with lower compute cost

**Process:**
1. Find structurally identical computation nodes (same IR hash) → deduplicate (merge into single node with multiple `dispatches-to` edges)
2. Find constraint nodes referenced by only one computation node → consider inlining
3. Find computation nodes with no test edges → flag for Test Agent
4. Identify hot paths (heavily-used `depends-on` chains) → recommend pre-compilation to native

**Technology:** Graph query + comparison algorithms. No novel AI needed.

#### 4.4.6 Security Agent

**Input:** Boundary nodes + their resolved computation paths
**Output:** Security findings as structured issue nodes

**Process:**
1. For each boundary node with `direction: inbound`: verify `constrained-by` includes an auth constraint
2. For each computation node that accesses data with PII annotations: verify access control edges
3. For each computation node with `effects: [db:write]`: verify input validation constraint exists
4. Check for computation nodes missing rate limiting constraints on inbound boundary paths

**Technology:** Graph traversal + constraint existence queries. This is a set of graph queries, not heuristic AI analysis.

#### 4.4.7 Migration Agent

**Input:** A semantic node in an older schema version
**Output:** The same node in the current schema version

**Triggered by:** Schema version upgrades, dependency node ID changes, target language/IR version updates.

**Technology:** Schema transformation rules stored as computation nodes (`migration:v1-to-v2`). Deterministic transformation, not AI.

---

## 4.5 Memory System

### Tier 1: Working Graph (LLM In-Context)

- **Capacity:** 10–50 nodes
- **Format:** Full node JSON
- **Population:** Explicit agent graph queries
- **Example turn cost:** 1,000–4,000 tokens for a focused edit

### Tier 2: Session Index (Redis / SQLite)

- **Capacity:** 500–5,000 node summaries
- **Format:** `{ id, type, signature_hash, alias, edge_count, last_accessed }`
- **Population:** Built during session; updated on each Tier 1 access
- **Eviction:** LFU with pinned set (domain ontology + project constraints always pinned)
- **Access cost:** ~2 tokens per node reference (ID only, with summary on demand)

### Tier 3: Full Graph Store

- **Technology:** Neo4j (production), Apache AGE on PostgreSQL (embedded), or LevelGraph (Node.js embedded)
- **Indices:**
  - Primary: hash index on node ID (O(1) lookup)
  - Vector: cosine similarity on `intent_embedding` (semantic search)
  - Type index: all nodes of a given type (fast neighborhood queries)
  - Edge index: all edges of a given type from a given source
- **Persistence:** Append-only WAL + periodic snapshot (like PostgreSQL WAL)
- **Retention:** Full version history; snapshots retained, individual deltas may be compacted after N snapshots

### Memory Promotion / Demotion

```
On agent graph.get(id):
  if id in Tier1: return immediately
  if id in Tier2: promote to Tier1, return
  else: load from Tier3 → Tier2 → Tier1, return

On Tier1 overflow (> 50 nodes):
  demote LFU node from Tier1 to Tier2
  if Tier2 overflow: demote LFU (non-pinned) from Tier2 to eviction
```

---

## 4.6 MCP Tool Layer

All agent capabilities are exposed as MCP tools. This means any MCP-compatible agent framework can use the AIL-2 infrastructure.

### Graph Tools

```typescript
graph.get(id: NodeID): SemanticNode
graph.neighborhood(id: NodeID, edge_type?: EdgeType, depth?: 1|2): SemanticNode[]
graph.search_semantic(query_embedding: float[], limit: number): SemanticNode[]
graph.search_by_signature(signature: TypeSignature): SemanticNode[]
graph.upsert(node: SemanticNode): NodeID
graph.delete(id: NodeID, cascade?: boolean): DeletionReport
graph.add_edge(source: NodeID, edge_type: EdgeType, target: NodeID): void
graph.remove_edge(source: NodeID, edge_type: EdgeType, target: NodeID): void
graph.snapshot(): SnapshotID
graph.diff(snap_a: SnapshotID, snap_b: SnapshotID): SemanticDiff
graph.restore(snap_id: SnapshotID): void
```

### Compilation Tools

```typescript
compiler.compile(entry_points: NodeID[], target: 'wasm'|'native'|'container'): ArtifactID
compiler.check_types(subgraph: NodeID[]): TypeCheckReport
compiler.optimize(subgraph: NodeID[], strategy: 'size'|'speed'): OptimizationReport
```

### Verification Tools

```typescript
verifier.run_tests(node_ids: NodeID[]): TestReport
verifier.check_constraints(node_ids: NodeID[]): ConstraintReport
verifier.coverage(context_partition?: PartitionID): CoverageReport
verifier.security_scan(boundary_ids: NodeID[]): SecurityReport
```

### Deployment Tools

```typescript
deployer.deploy(artifact_id: ArtifactID, env: 'staging'|'production'): DeploymentID
deployer.rollback(deployment_id: DeploymentID): void
deployer.status(deployment_id: DeploymentID): DeploymentStatus
deployer.canary(artifact_id: ArtifactID, traffic_pct: number): DeploymentID
```

### Embedding Tools

```typescript
embedder.embed_text(text: string): float[]
embedder.embed_node(node: SemanticNode): float[]
```

---

## 4.7 Semantic Graph Store: Implementation

### Technology Stack (Available Today)

| Component | Technology | Why |
|---|---|---|
| Graph DB | Neo4j Community or Apache AGE | Production-ready property graph, Cypher query language |
| Vector Index | pgvector on PostgreSQL, or Qdrant | Semantic search, available today |
| Blob Storage | S3-compatible (MinIO for local, S3 for cloud) | IR bytecode blobs by hash |
| Cache | Redis | Tier 2 session index |
| WAL | PostgreSQL WAL or custom append-only log | Version history |
| API | REST + WebSocket | Agent access |

### Graph Schema

```cypher
// Node creation
CREATE (n:SemanticNode {
  id: 'sn:a4f2e9b7',
  node_type: 'computation',
  signature_hash: 'sha256:...',
  ir_blob_key: 's3://ail2-blobs/sha256:...',
  domain: 'on:inventory',
  context_partition: 'cp:inventory-write',
  snapshot_created: 'snap:00342',
  intent_embedding: [0.12, -0.87, ...]
})

// Edge creation
MATCH (a:SemanticNode {id: 'sn:a4f2'}), (b:SemanticNode {id: 'sn:b3e1'})
CREATE (a)-[:DEPENDS_ON {weight: 1.0}]->(b)

// Semantic search (via vector extension)
CALL db.index.vector.queryNodes('intent_index', 5, $embedding)
YIELD node, score
RETURN node.id, score
```

---

## 4.8 Compilation Layer

### Compiler Architecture

The AIL-2 compiler is a **graph-to-IR translator** + existing IR toolchain.

```
SemanticGraph
    │
    ▼
[GraphCompiler]
    │  1. BFS from entry points → ordered node list
    │  2. Retrieve IR blobs from storage
    │  3. Generate link table (node ID → runtime address)
    │
    ▼
Linked IR Module (LLVM IR or WASM module)
    │
    ▼
[Existing IR Toolchain]
    │  LLVM → native binary
    │  wasm-opt → optimized WASM
    │  Docker build → container image
    │
    ▼
Target Artifact
```

### Multi-Target from Single Graph

The same semantic graph snapshot compiles to multiple targets using deployment annotations:

```cypher
// Find all nodes deployed to the 'inventory-service'
MATCH (n:SemanticNode)-[:DEPLOYED_IN]->(s:DeploymentUnit {name: 'inventory-service'})
RETURN n
```

Different deployment units → different compiler invocations → different artifacts. No code duplication, no multi-repo setup.

---

## 4.9 Complete Workflow

### Example: "Create an inventory system"

**Human input:**
> "Create an inventory system with products, warehouses, and stock movements. When stock drops below the reorder point, notify the warehouse manager. Restrict movement creation to warehouse managers and admins."

---

**Step 1: Intent Parsing (< 5 seconds)**

LLM parses natural language → intent nodes:
```json
{
  "entities": ["Product", "Warehouse", "StockMovement"],
  "behaviors": ["track_stock_level", "create_stock_movement", "notify_on_low_stock"],
  "constraints": [
    "stock_level >= 0",
    "movement_creation requires role in [warehouse_manager, admin]",
    "stock_level < reorder_point → notify(warehouse_manager)"
  ],
  "actors": ["warehouse_manager", "admin"]
}
```

---

**Step 2: Graph Matching (< 2 seconds)**

Orchestrator queries graph:
- "Do we have a Product data node?" → semantic search → No match → gap
- "Do we have a generic notification system?" → semantic search → Match found (`sn:notification-system-v2`) → reuse
- "Do we have auth constraint nodes?" → exact match (`cn:requires-auth`) → reuse

Result: 6 gaps identified (3 data nodes, 3 computation nodes, 2 new constraint nodes).

---

**Step 3: Domain Decomposition (< 10 seconds)**

Decomposition Agent processes intent:
- Creates domain ontology nodes: `on:stock-level`, `on:reorder-point`, `on:sku`
- Creates constraint nodes: `cn:stock-non-negative`, `cn:notify-on-reorder-breach`, `cn:auth-warehouse-manager-or-admin`
- Creates operation requirement nodes: `req:create-product`, `req:create-warehouse`, `req:create-stock-movement`, `req:get-stock-level`, `req:check-reorder`, `req:notify-warehouse-manager`

Orchestrator dependency-orders requirements: data nodes → computation nodes → boundary nodes.

---

**Step 4: Parallel Data Synthesis (< 30 seconds)**

Three Synthesis Agent instances run in parallel:

Agent 1 → creates `sn:product-data-node`:
```json
{
  "id": "sn:sha256:product-v1",
  "type": "data",
  "signature": {
    "fields": [
      { "name": "sku", "type": "string", "unique": true },
      { "name": "name", "type": "string" },
      { "name": "reorder_point", "type": "quantity", "min": 0 }
    ]
  }
}
```

Agent 2 → creates `sn:warehouse-data-node`
Agent 3 → creates `sn:stock-movement-data-node`

Each agent: LLM generates field list → type inference → schema node creation. No code generation yet.

---

**Step 5: Computation Synthesis (< 2 minutes)**

Six Synthesis Agent instances, run in dependency order:

Round 1 (parallel): `create-product`, `create-warehouse` (no cross-dependencies)
Round 2: `create-stock-movement` (depends on Product and Warehouse data nodes)
Round 3: `check-reorder-and-notify` (depends on `create-stock-movement` + existing `sn:notification-system-v2`)

For each computation node:
1. LLM generates source code (TypeScript/Python/Rust — configurable)
2. Compiler converts to IR
3. IR blob stored in object storage
4. Computation node created with `ir_blob_key` + signature
5. `depends-on` edges declared

---

**Step 6: Constraint Attachment (< 10 seconds)**

Orchestrator:
- Attaches `cn:stock-non-negative` → `sn:create-stock-movement` via `constrained-by` edge
- Attaches `cn:auth-warehouse-manager-or-admin` → `sn:create-stock-movement` via `constrained-by` edge
- Attaches `cn:notify-on-reorder-breach` → `sn:check-reorder-and-notify` via `constrained-by` edge

---

**Step 7: Boundary Node Creation (< 20 seconds)**

Synthesis Agent creates boundary nodes:
- `bn:POST/products` → resolves to `sn:create-product`
- `bn:POST/warehouses` → resolves to `sn:create-warehouse`
- `bn:POST/stock-movements` → resolves to `sn:create-stock-movement`
- `bn:GET/stock-level/{sku}/{warehouse}` → resolves to `sn:get-stock-level`

Each boundary node inherits auth constraints from its resolved computation node via `constrained-by` edge traversal.

---

**Step 8: Test Generation (parallel with Step 7, < 30 seconds)**

Test Agent processes all computation nodes:
- 3–5 test nodes per computation node
- 1 constraint verification test per constraint node
- Total: ~25 test nodes

Example test node for `sn:create-stock-movement`:
```json
{
  "id": "tn:create-movement-negative-qty",
  "type": "test",
  "tests": "sn:create-stock-movement",
  "given": { "quantity": -5, "direction": "out", "sku": "SKU-001" },
  "expects": { "error": "ev:invalid-quantity" }
}
```

---

**Step 9: Verification (< 30 seconds)**

Verification Agent:
1. Runs 25 test nodes against their target computation nodes → all pass
2. Checks constraint satisfaction:
   - `cn:stock-non-negative` → `sn:check-stock-non-negative` verification node passes
   - `cn:auth-warehouse-manager-or-admin` → auth constraint check passes
3. Coverage: 6/6 computation nodes have test nodes → 100%
4. Security scan: all inbound boundary nodes have auth constraint → pass
5. **Verification report: PASS**

---

**Step 10: Snapshot + Compilation (< 60 seconds)**

```
graph.snapshot() → snap:inventory-v1-0001
compiler.compile(entry_points: [all boundary nodes], target: 'container')
→ artifact:inventory-service-v1.0.0
```

Compiler output: Docker container image, ~50MB.

---

**Step 11: Staging Deployment + Human Approval**

```
deployer.deploy(artifact:inventory-service-v1.0.0, env: 'staging')
→ deployment:staging-001
```

Human receives: staging URL + auto-generated API documentation (derived from boundary node schemas) + test coverage report.

Human tests the staging environment, approves.

```
deployer.deploy(artifact:inventory-service-v1.0.0, env: 'production')
→ deployment:prod-001
```

---

**Total time (automated steps): 3–5 minutes**
**Human time: 30 seconds** (write intent + approve staging)

---

## 4.10 Editor

The editor is a **graph visualization and intent entry tool**, not a code editor.

### Views

| View | Content | Primary user |
|---|---|---|
| Intent view | Natural language input + intent nodes | Human |
| Graph view | Visual node-edge diagram, filterable by type/domain | Human (debugging/oversight) |
| Constraint view | All constraint nodes + their attachment points | Human (auditing rules) |
| Version view | Snapshot list with semantic diffs | Human |
| Test view | Test node results + coverage graph | Human |
| Generated source view | On-demand generated readable code from any subgraph | Human (inspection only) |

### What the editor does NOT have

- A code text editor (source code is generated output, not input)
- File tree (no files in the primary representation)
- Git blame / diff view (replaced by semantic diff view)
- Search-in-files (replaced by semantic search)

### Technology (Today)

- Web frontend: React + D3.js or Cytoscape.js for graph visualization
- Backend: REST API to the semantic graph store
- Auth: standard web auth
- Intent entry: text input → LLM call → intent node creation
- Graph rendering: force-directed layout, filterable by node type and edge type

---

## 4.11 Technology Stack Summary

| Layer | Technology (Today) | Notes |
|---|---|---|
| Human interface | Web UI (React) or CLI | Simple text → intent node |
| Orchestrating agent | Claude API or GPT-4 with tool use | Standard agentic loop |
| Specialized agents | Claude API / GPT-4, parallel instances | Stateless, graph-mediated |
| Graph DB | Neo4j 5.x Community Edition | Free, production-ready |
| Vector search | Qdrant or pgvector | Semantic node search |
| Session cache | Redis 7.x | Tier 2 memory |
| Blob storage | MinIO (local) / S3 (cloud) | IR bytecode blobs |
| IR format | WASM (primary) / LLVM IR (native) | Existing toolchains |
| Compiler frontend | Custom graph traversal + blob linking | ~500 lines of code |
| Compiler backend | LLVM / wasm-opt / Docker build | Existing tools |
| Test runner | WASM runtime + JSON I/O harness | ~200 lines of code |
| Deployment | Kubernetes / Fly.io / AWS ECS | Standard container runtime |
| MCP | Claude Code MCP protocol | Standard interface |
| Embeddings | text-embedding-3-small or equivalent | Standard API call |

**No novel technology required.** Every component is available today. The innovation is the composition and the semantic graph as the primary representation — not any individual component.

---

## 4.12 Minimal Implementation Path

The system can be built incrementally. Each phase delivers immediate value:

**Phase 1 (2–4 weeks):** Semantic graph store + basic node/edge operations + MCP tools for Claude Code. Result: AI can navigate a codebase via graph queries instead of file reads. Immediate token reduction.

**Phase 2 (2–4 weeks):** Synthesis agent + basic compilation. Result: AI can generate computation nodes from requirement descriptions, compile to a target language. First end-to-end prototype.

**Phase 3 (2–4 weeks):** Test agent + verification agent. Result: Generated code is automatically tested. Quality gate before compilation.

**Phase 4 (2–4 weeks):** Orchestrating agent + full workflow. Result: "Create X" → deployed service, largely automated.

**Phase 5 (ongoing):** Optimization agent, migration agent, security agent, editor UI.
