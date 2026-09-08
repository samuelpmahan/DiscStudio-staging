# S2 validation

S2 continues the accepted S1 Python/PxC/PQL/PCR investigation pattern on `task/quick-anno-s2-materialization`.

## Reproduce

From repository root after installing the Python package dependencies:

```sh
python -m pip install -e packages/quick_anno_py
python experiments/quick-anno-python/s2.py \
  ../chainspot-corpus/dev/DashsTrack/DashsTrack-full.jpg
```

The run executes real S0 -> S1 -> S2, exports the S2 runtime/PxC material, loads the Basket family/shell/objects/pixels into first-class Python PxC, runs a Python PCR summary Calculation, queries the published scratch Part through PQL, emits Mermaid, and materializes a neon-first correctness sheet.

## Observed Dash's Track result

```json
{
  "family": 17,
  "shellMembers": 17,
  "baskets": 17,
  "basketPx": 36362,
  "shellMargins": [2, 3, 2, 3]
}
```

The production S2 flow represented by this snapshot is:

```text
bright components
  -> Basket.detectFamily
  -> px.baskets.family
  -> Basket.findShellFamily
  -> px.baskets.shellFamily
  -> Basket.findPx
  -> px.baskets
  -> BasketPx subtraction/materialization
```

## Neon correctness materialization

`s2-neon-correctness-sheet.png` contains:

1. Basket family — neon cyan boxes.
2. Shell family — neon yellow boxes.
3. Basket objects — neon green boxes.
4. Exact BasketPx — neon magenta on a heavily dimmed canonical image.
5. Pixels removed from remaining — neon orange.
6. Actual remaining raster — BasketPx transparent over checkerboard.

Visual inspection confirmed all 17 family/shell/object boxes are localized to basket sprites, exact BasketPx forms the basket silhouettes rather than full bounding boxes, and the remaining raster removes those same basket pixels.

Generated artifacts land under:

```text
experiments/quick-anno-python/generated/DashsTrack-S2/
```

Important files:

```text
snapshot.json
python-summary.json
python-S2.mmd
s2-neon-correctness-sheet.png
s2-family-neon.png
s2-shell-family-neon.png
s2-baskets-neon.png
s2-basket-px-neon.png
s2-remaining-checkerboard.png
s2.receipt.txt
```

This is now the second stage using the same transfer pattern. S3 should be mostly mechanical for a Luna: real Stage snapshot -> Python PxC Parts -> small PCR/PQL investigation -> neon-first materialization -> visually inspect -> emit Mermaid/testimony.
