# S1 validation

Validated locally against Dash's Track after the first-class Python core and S1 materialization bridge were assembled.

## Python core

```text
3 passed
```

Focused command:

```sh
PYTHONPATH=packages/quick_anno_py python -m pytest -q \
  packages/quick_anno_py/tests/test_first_class.py
```

## Real S1 materialization

Install the tiny Python package dependencies once:

```sh
python -m pip install -e packages/quick_anno_py
```

Then from repository root:

```sh
python experiments/quick-anno-python/s1.py \
  ../chainspot-corpus/dev/DashsTrack/DashsTrack-full.jpg
```

This one command:

1. executes the real TS S0 and S1 Stage contracts;
2. exports the S1 PxC/materialization snapshot;
3. loads Badge objects, owned pixels, and muted pixels into first-class Python PxC;
4. executes the Python PCR ownership investigation;
5. queries its published scratch Part through PQL;
6. emits `python-S1.mmd`;
7. emits a neon-first correctness sheet plus individual neon materializations.

Observed Python PQL result:

```json
{
  "badges": 18,
  "ownedPx": 37002,
  "mutedPx": 45813,
  "addedMutePx": 8811
}
```

Observed Stage material:

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

## Visual correctness rule

The first subtle contact sheet was not sufficiently judgeable. The accepted investigation convention is **neon first**: make semantic differences unmistakable before making a render aesthetically subtle.

`s1-neon-correctness-sheet.png` contains:

1. Badge objects — thick neon green boxes and labels.
2. Production bright/dark masks.
3. Owned pixels — neon cyan on a heavily dimmed canonical image.
4. Added mute only (`muted - owned`) — neon yellow.
5. Total muted — cyan owned + yellow added mute.
6. Everything removed from remaining — neon magenta.
7. Actual remaining raster — removed pixels transparent over a checkerboard.

Visual inspection confirmed the ownership/mute material is concentrated on the badge regions, added mute extends beyond owned BadgePx, and the remaining raster removes those regions.

Generated outputs land under:

```text
experiments/quick-anno-python/generated/DashsTrack-S1/
```

Important files:

```text
snapshot.json
python-summary.json
python-S1.mmd
s1-neon-correctness-sheet.png
s1-owned-neon.png
s1-added-mute-neon.png
s1-muted-neon.png
s1-removed-neon.png
s1-remaining-checkerboard.png
s1-badge-objects-neon.png
```

This establishes the bounded transfer pattern: production Stage -> snapshot/PxC material -> first-class Python PxC -> Python Calculation/PCR -> published scratch Part -> PQL query -> deterministic neon correctness materialization + Mermaid view.
