# PxC algorithm references

The page now also mounts the [ID3 digit-learning diagram](id3-digits.md). Its training
samples, candidate questions, split memberships and growing tree are new reusable
Parts/Calculations; the three original live reference compositions remain below it.

## Contract

**What is.** Three deliberately small, hand-authored reference algorithms/compositions run on the existing
`createLab()` PxC board and through PQL documents: a decision tree, a single-layer
perceptron, and (only after the first two pass their numeric and composition tests) a
tiny transformer layer. The browser page reads the Parts those runs produced and opens
their real shared `pyto-run-record@1`; it does not recompute an explanatory copy.

**e.** A person can edit the small numeric inputs/parameters, prepare a reference, inspect
named input, weight, intermediate, explanation, and output Parts, and see the changed
decision path or numeric contributions. Each run freezes/copies its inputs and writes to
fresh run-scoped addresses, so an older result stays reviewable after controls change.
That history lasts for the current page lifetime; this reference page does not promise
durable reload persistence. At `/public/algorithm-references/index.html`, Next executes
one declared algorithm Tick; Play repeatedly awaits the same operation. Back and the
frame slider inspect retained Frames without executing anything.

**a\*.** Tests assert known tree paths and perceptron sums, then assert their PQL
composition and run-record receipts before transformer work is called solid. The
transformer test asserts projections, scaled dot-product attention and row softmax,
residual plus layer normalization, a two-layer feed-forward network, the second residual
plus normalization, shapes, finite values, and tolerance-bounded expected numbers.
Browser verification edits controls and proves displayed intermediates come from produced
Part addresses, then opens the existing Tick viewer. No test records human acceptance.

**Limits.** These are teaching/reference fixtures, not a neural-network framework.
Weights are fixed illustrative numbers, dimensions are tiny, and there is no training,
language-understanding, model-quality, performance, or production claim. A future example
should add one normal Calculation and named Parts rather than a new executor or store.

## Parts and Calculations

Each fresh run uses `px.reference.<algorithm>.run-<n>.*` addresses. Input snapshots and
weights are Parts; every intermediate below is produced by the named `fn.lab.reference.*`
Calculation through a PQL Tick.

| Reference | Calculation sequence | Produced Parts |
| --- | --- | --- |
| Decision tree | `tree.root`, `tree.branch`, `tree.path`, `tree.leaf` | root comparison, performed/bypassed branch, complete path, leaf/output |
| Perceptron | `perceptron.contributions`, `perceptron.activate` | per-feature products, weighted sum, threshold decision/output |
| Transformer layer | `transformer.project`, `transformer.attend`, `transformer.norm1`, `transformer.ffn`, `transformer.norm2` | Q/K/V projections; scaled scores/softmax/context; first residual/normalization; hidden/activated/projection; second residual/normalization/output |

All explanation panels enumerate these actual Parts. The transformer is one complete
predeclared teaching block with single-head self-attention, residuals, layer normalization,
and a two-layer ReLU FFN; its illustrative LayerNorm fixes `gamma=1` and `beta=0`. The
page edits perceptron weights, while the transformer intentionally keeps its tiny identity
weight fixture fixed and edits only its vector inputs/epsilon. “Replay this record”
offers the existing shared viewer for the currently reviewed boundary, including a
partial run. That viewer replays recorded evidence. The live session executes a fresh
one-Tick document through the existing `invokePql` path on its retained board.
`invokePql` itself still executes the whole document it receives. This fixture is not
labelled as a trained language model.

Math follows sections 3.1–3.3 of Vaswani et al., [Attention Is All You Need](https://arxiv.org/html/1706.03762v7):
single-head scaled dot-product self-attention, then post-residual normalization, then the
position-wise feed-forward sublayer and its post-residual normalization. Tokenization,
positional encoding, masking, dropout, training, and multiple heads are outside this fixture.

## Live execution contract (defined before implementation)

The source snapshot for this change starts at `455f66db91fc34ac0d8d32b66aa6ccbef224b774`
plus the existing, uncommitted reference files. Work stays on
`codex/card-render-experiment`; no worktree or branch change is needed.

Preparation freezes input/parameter Parts and the original PQL composition without
running an algorithm Calculation. The existing run-all entry points wrap that
same preparation. A live session keeps one LAB board and submits a one-Tick document
to `lab.run()` on each Next, with a unique receipt name. There is no new executor.

| Added Part | Contents and purpose |
| --- | --- |
| `<run-prefix>.session` | Source document/input digests, original addresses/composition, optional parent session, next Tick, status, and retained Step/Frame/record addresses; the execution cursor lives on the board. |
| `<run-prefix>.step.<n>` | Actual consumes/produces from the executed receipt, receipt and per-step record addresses, measured LAB-call wall time; immutable evidence of one declared Tick. |
| `<run-prefix>.frame.<n>` | Readable nodes/cells/edges, labels and highlights, each retaining its source Part address and value. Frame zero represents inputs only. |
| `<run-prefix>.frame-spec.<n>` | Projection bindings and the new step's produced-address highlights; no algorithm arithmetic. |
| `px.run.<composition>.through-<n>` | Valid cumulative record assembled from executed Tick testimonies, never by rerunning or including future Ticks. |

`fn.lab.reference.frame` reads a frame-spec Part and only the input/output Parts
that exist at that boundary. It projects them into the Frame Part in a separate,
observed presentation composition. Its work is separate from the one algorithm Tick
executed by Next. Projection never computes a missing algorithm result.

Next coalesces overlapping requests. Play awaits that same Next operation and the
presentation transition. Back/scrub read retained Frames, without moving the execution
cursor or running Calculations. Changed inputs prepare a fresh run with parent identity;
old input snapshots, Steps, Frames and exported record snapshots stay unchanged.
Animation duration is presentation time. The Step reports wall time around `lab.run()`;
existing adapter invocation durations and implementation/result digests remain null
where the LAB did not measure/provide them. Bound reads are the existing adapter's
read evidence, not a new claim of dynamic property-level tracing. Frame zero has its
own presentation receipt; “inputs only” describes the algorithm state, not an absence
of session metadata or presentation work. Matrix cells display three decimal places;
their titles and the raw Part inspector retain the actual numbers.

## Breadth before depth

Sam's BFS direction is a scope rule: explore nearby simple additions that can combine
and recombine, rather than following the most exciting idea into a deep specialization.
Here, input preparation, one-Tick execution, retained Frames, fork identity and record
export work across all three algorithms. A view is a lens over those Parts; arithmetic
stays in the existing Calculations. Finer term-by-term decomposition is a possible
next composition, not an extra executor to build now.

The signature-intervention evidence remains separate. Its 39 same-capture comparisons
and measured serialization savings concern Studio's signature wrapper; `createLab()`
does not use that wrapper. No speed benefit is inferred for these examples.

## Verification and review

On the default perceptron, before Next there is no Contributions, Weighted sum,
Activation or Output Part. First Next produces products `1, -1` and weighted sum
`0.25`; Activation and Output still do not exist. Second Next produces output `1`.
Change bias to `-1`: a new session starts at frame zero, keeps its parent address,
and produces output `0` after its own two steps. The older output stays `1`.

Automated checks: 256 package tests, 142 shared viewer tests, and the headless Chrome
reference harness pass. The latter checks rapid clicks, Play, absent future outputs,
retained history, changed-input forks, visible Part values, partial record export,
four tree steps, five transformer steps, rectangular projections, correctly labelled
3×3 attention and the shared replay page. Screenshots and a partial exported record
are in `test-results/algorithm-references-live/`.

The package scripts ran via the bundled runtime because `npm` is absent. The first
viewer run selected macOS Python 3.9 and failed four cross-runtime checks; using the
bundled current Python made all 142 pass. The separate legacy Studio Python browser
harness is unavailable in the current interpreter (`playwright` is not installed);
the JS reference harness used headless Chrome over the real local HTTP origin.
Verification is automated; human acceptance remains unrecorded.
