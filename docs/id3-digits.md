# Which pixel separates these digits best?

This is the next reference demonstration on the existing algorithm page. The story is
learning to ask useful questions about a handwritten digit. A pile of labelled examples
becomes a branching tree, one evaluated pixel question at a time. The tree fills the
viewport; each node is one card containing its own sample pile and pixel question. It uses ID3 with
explicit binary pixel features, rather than a manually authored tree or a downloaded
trained model.

## Parts and Calculations

`src/reference-algorithms/digit-data.js` retains the original 8×8 integer pixel values,
labels, source-row identities, attribution and selection recipe. The learner's dataset
Part includes the explicit rule `intensity >= 8` for an on pixel. Its model/tree Part
retains the node sample identities, available pixels, pending nodes, chosen splits and
leaf predictions. Pending nodes are expanded in first-in-first-out order so the diagram
grows across a level before descending further.

Scoring a node and choosing/applying its split are separate Calculations and Ticks.
The score Part retains each eligible pixel question's off/on memberships, digit counts,
entropies and information gain. ID3 selects the maximum information gain with a stable
lowest-pixel-index tie rule. Pixels constant over a node are displayed as unhelpful and
are not eligible splits. A zero-gain question can still be used when both groups exist:
stopping merely because the immediate gain is zero would miss XOR-like interactions.

Each branch removes its chosen categorical feature. Pure nodes become labelled leaves;
if no remaining pixel separates conflicting examples, a majority leaf records that
reason. Majority ties use a stable label order. These are declared teaching choices,
not a claim to implement C4.5 or CART by changing one scoring formula.

The live session uses the existing LAB's `document`, `run` and `runRecord`; it does not
introduce an executor. Each step has a unique name, immutable state and Frame Parts,
and an adapter-validated cumulative record of only the Ticks actually executed. The
diagram reads those Frames. A separate prediction Calculation reads a named drawing
and the selected retained tree state. It records the path and returns unresolved when
that path reaches a node the learner has not expanded yet.

## What the human sees

- Before the first Next: the actual labelled training thumbnails and an unexpanded
  root. There are no pixel candidate scores and no learned branch.
- Score: the node shows the best scored pixel question. **Compare questions**, in the
  top right, opens an 8×8 information-gain map and the selected candidate’s saved
  off/on partition. Alternative previews stay in this dialog; the actual tree card
  continues to show the algorithm’s question. There are no hypothetical child nodes
  on the canvas.
- Split: thumbnails move into the two actual child cards connected to their parent.
  There is exactly one card per retained tree node, including its class counts and
  question or leaf label. Zoom, Fit tree, Current node and canvas panning inspect
  larger trees without a duplicate overview.
- Review: Back/scrub uses retained Frames. Play repeats the same Next operation.
- Try: **Try a digit** opens a drawing dialog. A drawn digit or held-out example
  travels through the tree actually learned so far; its path highlights those same
  cards. A pending branch remains unresolved; a wrong classification remains visible.
- Inspect: the node’s arrow opens its saved value and source Parts. Dialogs close with
  their close button or Escape and restore keyboard focus to the opener.

Projection/animation is presentation work. Animation time is not execution time. Source
addresses and full numeric values stay available behind the diagram's inspection UI.
The view yields to browser painting and input between steps, including with reduced
motion enabled, so Play can receive Pause. Card widths are set together before heights
are measured, avoiding a separate layout flush for each node.
The current LAB adapter leaves unavailable invocation timings/digests null; this change
does not strengthen those existing records by inventing values.

## Data and reproducibility

The source is the 1,797-example `digits.csv.gz` distributed by scikit-learn 1.5.2:
`https://raw.githubusercontent.com/scikit-learn/scikit-learn/1.5.2/sklearn/datasets/data/digits.csv.gz`.
Its compressed SHA-256 is
`09f66e6debdee2cd2b5ae59e0d6abbb73fc2b0e0185d2e1957e9ebb51e23aa22`.

In source order, the first three examples of each label are training examples (30).
The next two per label are held out (20). No sample was selected for model performance.
The module retains their zero-based source rows and unchanged intensities. This creates
new teaching subsets of the original UCI test data, not the original benchmark split or
a writer-independent evaluation. The small set keeps every example visible; it is not
an accuracy claim for arbitrary handwriting.

Attribution: E. Alpaydin and C. Kaynak (1998), *Optical Recognition of Handwritten Digits*,
[UCI Machine Learning Repository](https://doi.org/10.24432/C50P49),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See also the
[scikit-learn dataset description](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_digits.html).

## Verification

The package suite passes 262 tests. Six focused ID3 tests also pass after the
candidate-recommendation refinement. Browser checks independently recompute all 64
root gains and partitions, compare visible thumbnails and numbers with source Parts,
exercise real stepping, retained history, prediction and export, and check wide and
narrow diagrams. The unified-tree checks assert one card per actual node, the first
three cards fitting at 1437×789, dialog focus/close behavior, and preview invariance. Their result and exact served build fingerprint are written to
`test-results/algorithm-references-id3/verification.json`, alongside screenshots and
exported records. An absent report is not evidence of a browser pass.

The complete teaching run produces 25 nodes over 50 training Ticks. Its accuracy is
30/30 on the training examples and 10/20 on the disjoint held-out examples; incorrect
predictions remain inspectable. These counts describe this fixed small teaching set.

The split path has a bounded browser profile retained as engineering evidence: in
reduced-motion Chrome at 1437×789, a Next click used to replace the lesson HTML
three times, with 19 measured height flushes by Tick 6. The optimized path replaces
it once per Tick and measured 7 flushes by Tick 6; representative split clicks fell
from about 913 ms to 312 ms at the first root split and from about 803 ms to 623 ms
at a later split in that isolated run. These timings are directional evidence, not
machine-specific gates; browser checks assert behavior and retained values instead.

## Source state

The shared checkout remains on `codex/card-render-experiment`, base
`455f66db91fc34ac0d8d32b66aa6ccbef224b774` plus the existing uncommitted reference work.
No branch switch, commit, promotion or human acceptance is implied by automated checks.
