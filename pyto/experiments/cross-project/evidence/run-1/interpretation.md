# Cross-project hit: the shelf domain reuses the ablation domain's split

The shelf domain (`px.shelf.*` / `fn.shelf.*`, this experiment) shared exactly one material with the ablation domain (`pyto/experiments/grouped-ablation`): the seed-7, n=400 split of `features.make_data`'s synthetic rows, resolved through the same content-addressed materials store both domains read (`materials.material_key(revision, source, args)`, key `31e1e57286cf7682aa074cb16ad11bc4f41032f78f9af19a12d528e02bb21fa7`).

Everything else -- the disc bag fixture, the stability histogram, and which discs to carry -- is the shelf domain's own: neither `px.shelf.*` nor `fn.shelf.*` exists anywhere in the ablation domain, and the shelf's own materials-store resolutions were misses (the first time anything under `fn.shelf.*` was ever stored) that then wrote this run's own new material.

A hit here means the shelf domain asked the shared store for `sha(canonical({revision, source, args}))` of the ablation split and the store answered without calling `fn.ablation.split` again; the returned value's own sha256 digest (`cefbd6bdda24c1770b8dd863559305b4b4ebc60ccc179fab0a1499297963f4f0`) is checked byte for byte against the digest the ablation experiment already committed (pyto/experiments/grouped-ablation/evidence/run-6-cached/reuse-ledger.json), not merely asserted equal by construction.

The hit is not evidence that the two domains agree on what a disc or a feature row means -- it is evidence only that the same (revision, source, args) triple, computed the same way by two different programs, addresses the same stored bytes; the shelf domain never calls into the ablation domain's Calculations for anything except this one imported Calculation object, and never runs the ablation domain's own program.

What would break it: a change to `fn.ablation.split`'s source (a different `implementation_sha256` revision), a change to `make_data`'s output for seed 7 / n 400 (a different args digest), or pointing `PYTO_MATERIALS_DIR` somewhere the shelf run cannot see -- each turns the resolution from a hit into a fresh miss, which is exactly what `test_cross_project.py`'s negative test demonstrates by mutating one of the shelf domain's OWN revision strings instead (the shared revision is the ablation domain's to change, not this experiment's).

## Counters

final: {'requests': 4, 'hits': 1, 'misses': 3, 'writes': 3}
hits before any shelf write: 1; writes before any shelf write: 0

| material | counters delta |
|---|---|
| fn.ablation.split (shared) | requests=+1 hits=+1 misses=+0 writes=+0 |
| fn.shelf.stabilityHistogram (own) | requests=+1 hits=+0 misses=+1 writes=+1 |
| fn.shelf.pickToCarry (own) | requests=+1 hits=+0 misses=+1 writes=+1 |

seeded by domain A this run: True
digest equal to the ablation experiment's committed evidence: True
