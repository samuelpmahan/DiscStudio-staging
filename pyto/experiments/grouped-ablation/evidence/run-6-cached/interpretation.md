# run-6-cached: content-addressed materials over the Day 1 ablation split

Ported from ChainSpot's `createMatrixMaterials` (pyto/reference/lab/chainspot-matrix/matrix/materials.ts:263-317), experiment-local (`materials.py`), applied to `fn.ablation.split`.

revision (fn.ablation.split's implementation_sha256, Day 2's receipts seam): `8674a964aba6e3cf16317f233884204439271c1853c0f945548a4a625e05bc86`
content-addressed key: `31e1e57286cf7682aa074cb16ad11bc4f41032f78f9af19a12d528e02bb21fa7`

## In-process counters (two fresh PxCs sharing one MaterialsStore)

requests=2 hits=1 misses=1 writes=1

| resolution | where | outcome | counters delta |
|---|---|---|---|
| 1 | in-process, fresh PxC, empty store | miss+write | requests=+1 hits=+0 misses=+1 writes=+1 |
| 2 | in-process, second fresh PxC, same store | hit (disk) | requests=+1 hits=+1 misses=+0 writes=+0 |
| 3 | fresh python3 -I process, PYTO_MATERIALS_DIR shared | hit (disk) | requests=+1 hits=+1 misses=+0 writes=+0 |

## Milliseconds saved

Read from the sibling full-program run's own receipts.json duration_ms for 'split' (the smaller of the two), never by re-running split to time the skipped call -- that would defeat the point of the cache hit. Synthetic-fixture wall time, labelled so (research/ULTRACODE-WEEK.md Reframing 2). ms_saved_total is this figure times hits_observed -- the number of the three resolutions whose own counters recorded a hit -- never times a constant, so a run in which a disk load fails reports 0 saved rather than hits that did not happen.
split duration_ms, program run 1: 0.051605995395220816; program run 2: 0.04590799653669819.
ms saved per cache hit (conservative, the smaller of the two): 0.04590799653669819.
Resolutions whose own counters recorded a hit (derived, never asserted): 2 of 3 -> ms saved this run: 0.092.

## Ordinary within-program reuse (hits.py, for comparison)

This is a different thing from the materials cache above: hit_ledger counts a Calculation address already registered earlier in the SAME run (e.g. `fn.ablation.fit` invoked once per variant); the materials cache counts one Part's VALUE reused ACROSS runs and processes.

program run 1: {'invocations': 15, 'part_hits': 2, 'calculation_hits': 10}
program run 2: {'invocations': 15, 'part_hits': 2, 'calculation_hits': 10}

## What each cannot express

The materials cache is silent about *why* a value is reused (no perceptual matching, no course identity -- ULTRACODE-WEEK.md Reframing 4); it only knows that `sha(canonical({revision, source, args}))` repeats. hits.py's Calculation ledger is silent about VALUES entirely -- two invocations of the same address with different args are equally 'already registered' even though they compute different things; it is a registration ledger, not a content-addressed one.
