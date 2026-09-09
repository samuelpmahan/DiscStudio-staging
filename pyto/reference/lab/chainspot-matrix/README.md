# Branch-space-fill matrix

The selected experiment runs through LAB's Sweep entry and the public ALG ABFeatureSet gateway. All listed variants are enabled when this experiment is selected. Frozen clean stages are unchanged.

From the repository root, after building ALG and installing the LAB runtime:

```sh
bash experiments/dashs-track-edge-sensing/exp/branch-space-fill/run.sh
bash experiments/dashs-track-edge-sensing/exp/branch-space-fill/run.sh H18
bash experiments/dashs-track-edge-sensing/exp/branch-space-fill/run.sh H18 --resume
```

The equivalent command is `./lab sweep matrix experiments/dashs-track-edge-sensing/matrix-review/MATRIX.json [COURSE|H18] [--resume]`.

The manifest contains 18 Dash hole cases and five explicit missing-seed cases for the remaining Dev courses. Source rasters alone do not supply the missing Tee/Badge associations. Annotation Basket and bend targets are not supplied to the producer. H3, H5 and H12 retain their assisted seed provenance from the saved input sidecar.

The four variants compare a fixed heading, strict loss-triggered branches, permissive loss-triggered branches, and an explicitly unsupported reflection-contact diagnostic. Strict and permissive thresholds use the same measured profile; the permissive arm requires half the calibrated broad-edge support. Both retain the same center-reference test. These are prototype judgments, not calibrated probabilities or verified path ownership.

The queue measures a new pose every 3 or 4 pixels after the two initial offsets. Supported poses continue their own heading. A loss proposes separated destinations around its own last supported ancestor. The proposals retain their full positions, while the connecting observations remain within four pixels of their actual parents. Poisson-disc rejection sampling spaces these local destinations; it does not establish global space coverage or correct hole association. Heading alternatives remain distinct.

`PAUSED` preserves the frontier, random state, observations, proposal destinations and parameters. `--resume` grants another computation slice and writes a new immutable receipt. A completed probe merely exhausted its current frontier; it does not mean the hole is solved. No fixed physical hole-length cutoff is used.

LAB stores actual calibration and pose profiles at PxC addresses keyed by source bytes, frame, seed, masks, sensor parameters and calculation revision. Variant-specific interpretations read those shared profiles. The board is shared across each case's variants and released between cases. Source pixels are decoded once per case. Saved events include numerical measurements, selected width profiles, broad and narrow edge spans, proposals, ancestry and source provenance.

Outputs are under `artifacts/sweep/matrix/source-edge-branching-matrix-v1/`. `summary.json` covers the full manifest; filtered and resumed summaries have separate filenames. Missing, unsupported and failed cells stay in the matrix. An individual failed variant cannot erase successful siblings.

To regenerate the source comparison and portable filterable gallery:

```sh
python experiments/dashs-track-edge-sensing/matrix-review/render.py artifacts/sweep/matrix/source-edge-branching-matrix-v1/summary.json matrix-proof --hole 18
python experiments/dashs-track-edge-sensing/matrix-review/gallery.py artifacts/sweep/matrix/source-edge-branching-matrix-v1/summary.json matrix-gallery
```

The comparison plots one parent-linked branch, rather than joining unrelated sibling readings. Green marks a sensor acceptance. The gallery retains failure groups and missing prerequisites. Reflection remains `unsupported/no-contact`: a gradient at an arbitrary center pixel is insufficient to establish an edge contact.

`verify_runner.py` exercises actual CLI resumption, immutable previous slices, course/hole selectors, and partial failure isolation. Focused unit tests additionally check continuous long travel, connection lengths, deterministic spacing, resume parity, source masks, profile reuse, and width selection.
