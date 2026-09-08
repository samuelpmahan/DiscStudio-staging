# S3 validation

S3 continues the accepted S1/S2 Python/PxC/PQL/PCR investigation pattern on
`claude/lab-python-p8x0cf`, based on the S2 checkpoint `5c87d48`.

## Reproduce

From repository root:

```sh
python -m pip install -e packages/quick_anno_py
npm run build --workspace @chainspot/alg
python experiments/quick-anno-python/s3.py \
  ../chainspot-corpus/dev/DashsTrack/DashsTrack-full.jpg
```

Input verified by content, not by filename:

```text
dev/DashsTrack/DashsTrack-full.jpg
sha256 e6616738640eee1d05d8cc2b59dd657f24b4a5a01dc2f68571b7e44c6f372b8a
627,609 bytes  (matches the repository's Git LFS pointer)
```

Python core:

```sh
PYTHONPATH=packages/quick_anno_py python3 -m unittest discover \
  -s packages/quick_anno_py/tests
```

```text
Ran 3 tests — OK
```

Repository typecheck:

```text
npm run check → 1162 FILES 0 ERRORS 0 WARNINGS
```

## Observed Dash's Track result

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

Canonical raster 1290×2083. Remaining opaque px after TeePx subtraction:
2,682,186. TeePx overlap between Tee objects: 0.

The production S3 flow represented by this snapshot is:

```text
bright components + Badge objects
  -> Tee.detectRings      -> px.tees.rings
  -> Tee.findFamily       -> px.tees.family
  -> Tee.findPx           -> px.tees
  -> TeePx subtraction (PCR output only; never written to PxC)
```

## Neon correctness materialization

`s3-neon-correctness-sheet.png` contains:

1. Ring candidates after Badge mute — neon yellow.
2. Rejected — grey diamond (5), red Badge-muted (3), orange unframed (4).
3. Enclosing bright frames — neon orange (20).
4. Family vote — green kept (18), magenta voted out (2).
5. Tee objects — neon green (18).
6. Exact TeePx — neon magenta (4,884).
7. Actual remaining raster — TeePx transparent over checkerboard.
8. What each accepted Tee is — one crop per object (18).
9. What was voted out — one wide-context crop per rejected frame (2).

Visual inspection was performed on the sheet and on the two full-resolution
crop strips. It **did not** confirm all 18 Tee objects. It confirmed:

- the accounting balances and no candidate disappears without a named bucket;
- exact TeePx forms tee silhouettes rather than filled bounding boxes;
- the remaining raster removes those same pixels;
- **and that 3 of the 18 accepted Tee objects are Apple Maps screen chrome** —
  crops 16, 17 and 18 read `SAT`, `aps`, `Map`, all within the bottom 60px of
  the raster;
- **and that 1 real tee pad was voted out of the family** — frame
  `[409,1748,22,33]`, area 171 against the family anchor's 276 (ratio 1.61 >
  `AREA_RATIO` 1.5), partially overlapped by the basket sprite at
  `[368,1734,46,72]`.

Neither is a defect in this lane's code, and neither is fixed here. See
`S3_CHECKPOINT.md` and the claims ledger for the full receipts.

## Refactor proof

The shared spine and drawing kit were promoted into `packages/quick_anno_py`
and S1/S2 rewritten onto them. Both were re-run and diffed against their
pre-refactor output:

```text
39 of 41 generated files byte-identical (sha256)
2 differing: DashsTrack-S1/snapshot.json, DashsTrack-S2/snapshot.json
```

Both are written by Node bridges that this change did not touch. Two
back-to-back runs of the *unmodified* S1 bridge differ in exactly the same
way — `durationMs` and `startedAtMs` inside `runtimePcr`, 32 diff lines, every
other byte and every PNG identical. `snapshot.json` carries wall-clock
timings and was never byte-stable.

S1 and S2 reproduce their documented numbers exactly:

```text
S1  badges 18 · ownedPx 37002 · mutedPx 45813 · addedMutePx 8811
S2  family 17 · shellMembers 17 · baskets 17 · basketPx 36362 · margins [2,3,2,3]
```

## Generated artifacts

```text
experiments/quick-anno-python/generated/DashsTrack-S3/
```

```text
snapshot.json
python-summary.json
python-S3.mmd
s3.receipt.txt
s3-neon-correctness-sheet.png
s3-ring-candidates-neon.png
s3-rejected-neon.png
s3-frames-neon.png
s3-family-vote-neon.png
s3-tees-neon.png
s3-tee-px-neon.png
s3-remaining-checkerboard.png
s3-tee-crops.png
s3-voted-out-crops.png
```

This is the third stage using the same transfer pattern, and the first where
the materialization contradicted the receipt's headline number rather than
confirming it. S4 should be mechanical for a Luna; carry the per-object
identity crop with it.
