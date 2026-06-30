# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Mission

AIL-2 is a research project designing a new software representation optimized exclusively for AI agents, not human programmers. The central question: what does software look like when only machines write, read, and modify it?

**Core priorities (in order):**
1. Minimize tokens required to understand any component
2. Minimize context needed to make a local edit
3. Eliminate all redundancy in stored representations
4. Maximize AI editability and scalability at any codebase size

## Fundamental Research Lens

For every existing programming construct, ask: *"Does this exist because a computer needs it, or because a human needs it?"*

If the answer is "a human needs it" — eliminate it, compress it, or replace it with a machine-efficient equivalent. Do not preserve constructs out of tradition.

## Primary Deliverable

A structured design specification covering:

1. Critical analysis of existing paradigms — variables, functions, classes, files, folders, comments, documentation, interfaces, architectural patterns, SOLID/DRY/KISS/YAGNI, design patterns, Git, source code itself
2. New paradigm design — unit structure, identity, memory, dependency navigation, context, knowledge and constraint representation
3. Concrete token-reduction mechanisms
4. Complete AI-native architecture (editor, agents, memory layers, compiler, vector store, versioning)
5. Side-by-side comparison: traditional CRUD app vs. new paradigm (file count, token count, context budget, edit cost)
6. Self-critique and limitations
7. Projections: what percentage of current programming constructs survives when AI writes all code?

## Document Conventions

- All files are `.md`, `.json`, or `.yaml` — no compiled code for now
- `spec/` — numbered specification sections (`01-paradigm-analysis.md`, `02-new-paradigm-design.md`, etc.)
- `research/` — raw notes, reference analysis, source material
- `architecture/` — text-based diagrams and architecture sketches
- `examples/` — concrete before/after comparisons

## Terminology

| Term | Definition |
|------|-----------|
| Token cost | Tokens an LLM must consume to understand or edit a component |
| Human construct | Any abstraction that exists primarily for human readability or cognition |
| AI-native | A representation designed exclusively for machine processing |
| Semantic node | Proposed fundamental unit in a graph-based software representation |
| Context budget | Maximum tokens an AI agent should need to perform any single edit |
| IR | Intermediate Representation — proposed replacement for human-readable source code |
| Edit locality | Property: a change to one semantic node requires loading only that node's immediate dependencies |

## Spec Writing Style

- State conclusions directly — no hedging
- Each section follows: *what is it → why it existed → AI necessity audit → verdict → replacement*
- Tables over prose for paradigm comparisons
- Quantify token costs with concrete examples
- Every retained construct must justify itself by computational necessity, not human convenience
- Every eliminated construct must have a concrete AI-native replacement or proof of non-necessity

## Related Fields

This project intersects: LLM context optimization, compiler IR design (LLVM, MIR, WASM), knowledge graphs, AST manipulation, vector databases, MCP protocol, multi-agent systems, information theory, and semantic compression. Reference these fields when analogies clarify a design decision.
