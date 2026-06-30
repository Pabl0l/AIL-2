---
name: paradigm-analysis
description: Analyze a named programming paradigm, construct, principle, or pattern through the AI-optimization lens. Outputs a structured verdict: origin, necessity audit, token cost, elimination or transformation decision, and what AI gains.
---

When the user names a programming construct (e.g. "classes", "DRY", "git commits", "files", "Factory pattern", "variable names", "interfaces"), produce this structured analysis:

---

## [Construct Name]

**Origin:** When and why was this created? What era, what problem domain?

**Problem solved:** What specific pain did it address for the people who invented it?

**AI necessity audit:**
- Does this construct exist for the computer's benefit or the human's?
- If AI agents write, read, and modify all code, does this still serve any purpose?
- Can it be eliminated entirely, or only transformed?

**Token cost (current):** How much context does this construct force an AI to load? Give a concrete example with approximate token counts.

**Verdict:** `ELIMINATE` | `TRANSFORM` | `RETAIN`
- If `ELIMINATE`: what replaces it (if anything), and how does the replacement work?
- If `TRANSFORM`: describe the AI-optimized version — what changes, what stays?
- If `RETAIN`: what fundamental computational constraint (not human preference) requires it?

**AI gain:** What specifically improves — fewer tokens, smaller context window needed, faster edits, less ambiguity, better edit locality?

---

Rules:
- Keep each analysis under 400 words
- Be direct and opinionated — this is a design decision, not a literature review
- If you find a construct partially survives in transformed form, show what the transformation looks like concretely
- Reference relevant IR design (LLVM, WASM), information theory, or graph theory when it clarifies the argument
- After the analysis, check if this verdict conflicts with any prior decisions in `spec/` — flag conflicts explicitly
