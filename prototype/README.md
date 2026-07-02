# Phase-1 Prototype: Semantic Graph as a Derived Index

First working code of the project, and the first **measured** evidence for the paradigm's central claim. Implements Phase 1 of the adoption path ([`spec/06`](../spec/06-projections.md) §6.3): the graph is built *over* existing text code as a derived index — nobody abandons their repository, and the input-token claim becomes testable.

Python stdlib only. No dependencies to install.

## What it does

```
ail/extract.py       Python AST -> semantic graph (computation/data/event/test nodes, typed edges)
ail/store.py         graph traversal + depth-2 edit-context assembly (spec/02 §2.4 protocol)
ail/measure.py       input tokens: edit context vs whole-file baselines
run_measurement.py   runs the pilot over 8 real stdlib modules
tests/               13 unit tests (python -m unittest discover tests)
```

## Run it

```bash
cd prototype
python run_measurement.py        # writes results/measurement-results.json
python -m unittest discover tests
```

## Pilot results (Python 3.11, 2026-07-01)

Corpus: 8 stdlib modules (`argparse`, `configparser`, `json.*`, `http.client`, `urllib.parse`, `email.message`) — 66,500 source tokens, 578 extracted nodes, 238 realistic edit targets (computation nodes with ≥1 resolved dependency).

| Metric | Value |
|---|---|
| AIL edit context (median) | **337 tokens** |
| AIL edit context (mean / max) | 419 / 2,427 tokens |
| vs. loading the whole file | **35.2× less input (median)** — ratio 0.028 |
| vs. file + its corpus imports | **45.1× less input (median)** — ratio 0.022 |

Two spec numbers this pilot puts under measurement for the first time:

- The manual claimed ~420 tokens for a typical edit; measured mean is **419**. The spec target was <800; the median is **337**.
- The README's "90–95% input reduction" projection: measured median reduction is **97.2%** vs whole-file — *on this corpus, with the caveats below*.

## Caveats (part of the result, not fine print)

1. **Token proxy.** Counts use a word/punctuation regex, not a BPE tokenizer. Both sides use the same proxy, so ratios are meaningful; absolute counts are approximate.
2. **Call resolution is 28.6%.** Name-based resolution misses dynamic dispatch, aliased imports, and higher-order calls. Missing `depends-on` edges make the AIL context *smaller* than it should be — the reduction factor is overstated by an unknown amount. Fixing resolution is the top prototype task.
3. **No constraint/ontology nodes.** Plain Python has nothing to extract them from; real AIL contexts would carry a few hundred extra tokens of constraints.
4. **Envelope overhead.** The context JSON costs ~150–200 fixed tokens, so AIL loses on tiny files (measured: a 5-function sample file costs 211 context tokens vs 81 for the file). The win exists only above a small threshold — every real module in the corpus is far past it.
5. **This is a pilot, not the validation.** [`spec/05`](../spec/05-self-critique.md) §5.2 demands ≥50 tasks across ≥3 codebases with real tokenizers and end-to-end edit outcomes (did the agent *succeed* with only this context?). This pilot measures context size only, on one corpus.

## What this does and does not show

**Shows:** on real, non-trivial code, a depth-2 edit context assembled from a derived semantic graph is 1–2 orders of magnitude smaller than whole-file loading, and lands where the spec projected.

**Does not show:** that an agent can complete edits *successfully* with only that context (success-rate experiment, not yet run), nor that the result holds on application codebases with heavy cross-file coupling.

## Next steps, in order

1. Edit-success experiment: give a model the AIL context vs the whole file for the same ≥50 edit tasks; compare success rates and total tokens.
2. Better call resolution (type-informed, import-aware) to close caveat 2.
3. Real BPE tokenizer counts.
4. TypeScript extractor (second corpus family).
