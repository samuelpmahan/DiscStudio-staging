# Python quick_anno S1 checkpoint

Branch: `task/quick-anno-s1-materialization`
Base first-class Python core: `f3ecab36eed4f3a8eaa785197ac48f087b960f67`

## Purpose

Prove one complete slice before delegating S2+:

- PxC, PQL, PCR, Part, Calculation and Tick are first-class Python objects;
- Python can consume a real S1 snapshot from the production ChainSpot runtime;
- a Python PCR can derive and publish a scratch Part;
- PQL can query that result;
- S1 emits deterministic neon-first correctness renders from the same production run;
- the Python PCR can emit Mermaid as a view of composition.

This is an experimental investigation surface, not a production Stage rewrite.

## Reproduce

From repository root:

```sh
python -m pip install -e packages/quick_anno_py
python experiments/quick-anno-python/s1.py \
  ../chainspot-corpus/dev/DashsTrack/DashsTrack-full.jpg
```

Focused Python-core validation:

```sh
PYTHONPATH=packages/quick_anno_py python -m pytest -q \
  packages/quick_anno_py/tests/test_first_class.py
```

The S1 script invokes `export_s1_snapshot.cjs`, which executes real S0 then real S1 using the built `@chainspot/alg` runtime, loads the exported material into first-class Python PxC, runs the Python PCR/PQL investigation, then generates the neon correctness materialization.

Outputs land under:

```text
experiments/quick-anno-python/generated/DashsTrack-S1/
```

Primary correctness artifact:

```text
s1-neon-correctness-sheet.png
```

Its panels are intentionally loud before subtle:

1. Badge objects — thick neon green boxes and labels.
2. Production bright/dark masks.
3. Owned pixels — neon cyan.
4. Added mute only (`muted - owned`) — neon yellow.
5. Total muted — cyan owned + yellow added mute.
6. Everything removed from remaining — neon magenta.
7. Actual remaining raster — removals transparent over checkerboard.

Other useful artifacts:

```text
snapshot.json
python-summary.json
python-S1.mmd
s1-owned-neon.png
s1-added-mute-neon.png
s1-muted-neon.png
s1-removed-neon.png
s1-remaining-checkerboard.png
s1-badge-objects-neon.png
s0.receipt.txt
s1.receipt.txt
```

## Observed Dash's Track result

```text
canonical: 1290x2083
badges: 18
bright components: 144
dark components: 708
family: 18
owned px: 37002
muted px: 45813
added mute px: 8811
remaining opaque px: 2641257
```

The Python-owned derived Part `scratch.s1.ownershipSummary` produced:

```json
{
  "badges": 18,
  "ownedPx": 37002,
  "mutedPx": 45813,
  "addedMutePx": 8811
}
```

Visual inspection confirmed the neon owned/mute material is localized to the badge regions, added mute extends beyond owned BadgePx, and the remaining raster removes those regions. A subtle render is not accepted as the first correctness proof; **neon first** is the investigation convention.

## Correctness boundary

Do not claim the Python-authored semantic S1 graph itself executes the full badge detector yet. Today the production runtime executes S1; Python consumes its resulting testimony/materials and performs experimental calculations over them.

That boundary is deliberate: first make PxC/PQL/PCR behavior pleasant in Python, then promote only proven calculations.

## Delegate from here

A Luna extending this pattern should:

1. take the prior Stage's PxC material as input;
2. expose the smallest real runtime snapshot needed for the investigation;
3. seed first-class Python Parts;
4. express new experimental work as named Calculations in a PCR;
5. publish useful scratch Parts into Python PxC;
6. query with PQL rather than parallel ad-hoc state;
7. materialize a **neon-first** visual correctness check;
8. visually inspect the materialization before claiming success;
9. emit Mermaid/PCR testimony from the same composition;
10. add a convenience only after real repeated friction demonstrates it.

S2 is the next transfer test.
