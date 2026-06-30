---
name: spec-section
description: Draft a section of the AIL-2 design specification. Reads existing spec files to maintain consistent terminology, design decisions, and format.
---

When asked to draft a specification section:

**Step 1 — Read existing spec files** in `spec/` (if any exist) to pick up: terminology already defined, design decisions already made, and the current sequential numbering.

**Step 2 — Draft the section** using this format:

```markdown
# [NN]. [Section Title]

## Overview
[2–3 sentences: what this section covers and its main conclusion.]

## Analysis
[Core content. Use tables for paradigm comparisons. Use direct assertions for conclusions.
Quantify token costs with concrete examples where possible.]

## Design Decision
[Concrete verdict: what survives, what is replaced, what is eliminated, and in what form.]

## Justification
[Why this decision reduces token cost, context burden, or reasoning time for an AI agent.
Reference computational constraints (not human preferences) to justify anything retained.]
```

**Step 3 — Consistency check** after drafting:
- Flag any terminology used here that differs from `spec/` files or CLAUDE.md's terminology table
- Flag any design decisions that conflict with previous sections
- List open questions that need resolution before this section can be finalized

**Step 4 — File placement:** Save to `spec/[NN]-[section-name].md` where NN is the next sequential number (zero-padded, e.g. `03`).

---

Style rules:
- No hedging language ("simply", "just", "basically", "it could be argued")
- Every retained construct must cite a computational necessity, not human convenience
- Every eliminated construct must name a concrete AI-native replacement or prove non-necessity
- Introduce new terms with a callout: `> **Term:** definition`
- Prefer tables over prose lists for comparisons
