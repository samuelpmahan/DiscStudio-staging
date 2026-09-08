# Python quick_anno S3 checkpoint

Branch: `claude/lab-python-p8x0cf`
Base S2 checkpoint: `5c87d48945ecc11b6e1466cfd193b071747238b6`

## Purpose

Third transfer of the bounded pattern established by S1 and S2, on the Stage
where it earns the most: S3 is the first Stage whose **drop surface is wider
than its output**. A ring can die four different ways before a Tee exists, so
"18 Tee objects" is not by itself a statement about the world.

This is an experimental investigation surface. No production S3 semantics were
changed — no threshold moved, no selector edited, nothing registered into
`S3_PLAN`.

## Reproduce

```sh
python -m pip install -e packages/quick_anno_py
npm run build --workspace @chainspot/alg
python experiments/quick-anno-python/s3.py \
  ../chainspot-corpus/dev/DashsTrack/DashsTrack-full.jpg
```

The one command executes real S0 → S1 → S2 → S3 through the built
`@chainspot/alg` runtime, exports the S3 snapshot, seeds first-class Python
PxC, runs a two-Calculation Python PCR, queries the published scratch Part
through PQL, emits Mermaid, and materializes the neon correctness sheet.

Outputs land under `experiments/quick-anno-python/generated/DashsTrack-S3/`.

## Observed Dash's Track result

Production receipt (`s3.receipt.txt`):

```text
enclosed holes: 32
elongated rings: 27
excluded by Badge mute: 3
ring candidates: 24
enclosing bright frames: 20
rings without frame: 4
common visible Tee family: 18
Tee objects: 18
TeePx: 4884
recovery: NOT RUN
component fallback: NOT RUN
```

The Python-owned derived Part `scratch.s3.teeSummary`:

```json
{
  "enclosed": 32,
  "diamondDropped": 5,
  "elongated": 27,
  "excludedByBadge": 3,
  "candidates": 24,
  "measured": 20,
  "unframed": 4,
  "votedOutOfFamily": 2,
  "familyMembers": 18,
  "tees": 18,
  "teePx": 4884,
  "balanced": true
}
```

`balanced` is the whole point of the investigation. It asserts the four
accounting identities hold, so every enclosed ring left through exactly one
named door:

```text
32 enclosed  = 27 elongated + 5 diamond
27 elongated = 24 candidates + 3 Badge-muted
24 candidates = 20 measured  + 4 unframed
20 measured  = 18 members    + 2 voted out
18 members   = 18 Tee objects
```

## Two Calculations, not one

S3 is the first Stage with something to compose, so the PCR has two Ticks and
the second consumes the first's published Part *by result* inside the same
graph — the direct-result behavior the Python core was built for, finally
exercised on real material. `python-S3.mmd`:

```text
accountRings --> p2["scratch.s3.ringLedger"]
accountRings -->|ledger| checkBalance
```

## What the neon sheet shows

`s3-neon-correctness-sheet.png`, nine panels:

1. Ring candidates after Badge mute — neon yellow, inner holes.
2. Rejected — grey diamond, red Badge-muted, orange unframed.
3. Enclosing bright frames — neon orange.
4. Family vote — green kept, magenta voted out.
5. Tee objects — neon green, frame bbox, order-labelled.
6. Exact TeePx — neon magenta on a heavily dimmed canonical image.
7. Actual remaining raster — TeePx transparent over checkerboard.
8. **What each accepted Tee is** — one upscaled crop per object.
9. **What was voted out** — one wide-context crop per rejected frame.

Panels 2, 4, 8 and 9 do not exist in the S1 or S2 sheets. They were added
because S3 needs them, and panels 8 and 9 were added *after* looking at the
first render: panels 1-7 prove **where** each object was accepted and never
**what** it is. Identity precedes geometry; a full-course panel cannot
establish identity at course zoom.

## What visual inspection found

Both findings come from panel 8 and panel 9. Neither is fixed here — this lane
proves the investigation pattern, it does not change the algorithm.

**1. Three of the eighteen accepted Tee objects are Apple Maps screen chrome.**
Crops 16, 17 and 18 read, in plain letters, `SAT`, `aps` and `Map` — the
satellite toggle and the Apple Maps wordmark along the bottom edge of the
screenshot. Their frames sit at `[1165,2024,27,29]`, `[133,2039,23,34]` and
`[107,2039,21,26]` on a 1290×2083 canonical raster: all inside the bottom 60
pixels. Letterforms with enclosed counters produce enclosed rings, and their
strokes produce enclosing bright components inside S3's `FRAME_AREA_MIN/MAX`
and 50×50 bbox guards.

So Dash's Track's visible S3 output is **15 tee pads plus 3 chrome glyphs**,
and the 18 that matches an 18-hole course is a coincidence. This is the known
`screenChrome.ts` bottom-edge limitation reaching S3.

**2. One real tee pad is lost to the family size vote.**
Voted-out frame `[409,1748,22,33]`, area 171, major 32.2, minor 18.0. Panel 9
shows a tee pad immediately right of a basket sprite, partially overlapped by
it, inside that basket's C1S ring. The nearest S2 basket is bbox
`[368,1734,46,72]` — its right edge at x=414 crosses the pad's left edge at
x=409, i.e. the pad lies in the basket bbox's empty margin, exactly where the
engram says occluded pads leave remnants.

Its major axis (32.2) is *larger* than the family anchor's (30.9); only its
area is short — 276/171 = 1.61, past the `AREA_RATIO` of 1.5. Occlusion shrank
the visible area and the size vote dropped it. This is the documented
`minesweeper` HIGH item ("teeFamily majority-votes by size family — correct
tees at a non-dominant scale get excluded") firing with a pixel receipt.

The other voted-out frame, `[1041,2028,9,10]`, is the `MAP` button — correctly
rejected, though by size rather than by identity.

Corroborating observation, **not proven here**: 15 visible pads is consistent
with the claims-ledger record that DashsTrack reaches 18/18 with three tees
arriving via G4 recovery. The G-gate and S-stage paths share detection
primitives but are not the same wrapper, so this is a consistency note, not a
result of this run.

## Correctness boundary

Unchanged from S1 and S2, and worth restating because S3 is where it gets
tempting: the Python-authored graph does **not** execute the tee detector.
Production executes S3; Python consumes the resulting material and performs
bounded calculations over it. `recovery: NOT RUN` and `component fallback:
NOT RUN` are production's own receipt lines, not omissions here.

`exp/fill-consistent` — the fourth family dimension from the historical G3
selector — is **NOT RUN**. It is an exported function with no registered
Calculation and no Tick in `S3_PLAN`, so the clean run never reaches it. The
snapshot and the script both say so in as many words rather than leaving it
unmentioned.

## The convenience promoted, and the friction that paid for it

S3 made the boilerplate a third identical copy, which is the threshold the
pattern sets for promotion. Two modules were extracted; neither adds a
capability, both delete duplication:

- `chainspot_quick_anno/neon.py` — the drawing kit (`dim`, `draw_boxes`,
  `paint_pixels`, `checkerboard`, `remaining`, `panel`, `sheet`, the colours).
  S1 and S2 had each grown a private copy, already drifted: two names for the
  same dim function, two label-box widths, one with a redundant convert.
- `chainspot_quick_anno/investigation.py` — `StageInvestigation`, the spine
  every stage script repeated: paths, the Node snapshot bridge subprocess, the
  summary/Mermaid writes, the materializer subprocess.

One genuinely new function, `neon.crops`, added for the reason above: after
looking at the first sheet, there was no way to ask what an accepted object
actually was.

**S1 and S2 were re-run after the refactor and their output is byte-identical**
— 39 of 41 generated files match their pre-refactor sha256 exactly. The two
that differ are `snapshot.json`, written by the Node bridges, which were not
modified: back-to-back runs of the *original* bridge differ in `durationMs`
and `startedAtMs` inside `runtimePcr`, so that file was never byte-stable.

## Delegate from here

S4 follows the same ten steps as S2's handoff, with one addition earned here:

11. materialize a per-object identity crop before claiming any object is what
    its bounding box implies. A count that matches expectation is not evidence.
