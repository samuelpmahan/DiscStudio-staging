# Review of 941f354 — useful experiment primitives, with trust-boundary gaps

Historical review before the candidate repairs, 2026-09-12, by the parent agent
and three read-only reviewers: neat hot, neat equiv, and studio integration.
No fixes had been implemented at this review point. See RESULTS.md for the later
scoped repairs and their verification; the observations below remain as recorded.

Source: `941f3544f82f80f88c7228abec646b0889d575fa`, merged into
`codex/card-render-experiment`. The user's original checkout remains on
`338e8a2ff14f1c367c618fdbf7d00816a82a850f`. The exact merge commit adds task 150;
the studio observations below concern its accumulated ancestry since that old
checkout, not changes uniquely introduced by task 150.

## Capability gained

`neat hot` turns a run record into measurements and suggestions, then publishes
that analysis as a Part with its own receipt. `neat equiv` reconstructs recorded
inputs, runs a Python candidate and compares its outputs, then publishes a
witness through `fn.neat.equiv.judge`. These are useful reusable components for
the pstack experimental workflow, not merely instructions for an agent to remember.

The studio now composes the global → preset → instance card cascade, shelf-wide
art assignment, shared battle standings, portrait/landscape frames, receipt
queries, undo and LAB stages through the existing runtime. Async scheduling
overlaps awaited work on one JS thread; it does not create CPU workers.

## Three first repairs to consider

### P1: equiv can trust the wrong function by using an input from the future

`pyto/src/pyto/neat/equiv.py:173-185` builds a global writer map;
`:223-230` consults it without respecting the invocation boundary. A real PCR
that reads a preexisting Part and then overwrites it can be replayed with the
later value instead of the one it consumed, even when the correct initial
value is supplied in `store`.

Reproduction (run with this checkout's pyto package available):

```python
from pyto import Calculation, PCR, Part, PxC
from pyto.materialize import run_record
from pyto.neat.equiv import check, describe, judge

p, out = Part("px.test.input"), Part("px.test.output")
board = PxC()
board.set(p, 1)
pcr = PCR("future-writer")
pcr.calc("Read", Calculation("fn.test.read", lambda a: a["x"]),
         id="read", into=out, x=p)
pcr.calc("Later", Calculation("fn.test.later", lambda a: 2),
         id="later", into=p)
record = run_record(pcr.run(board, observe=True), board,
                    preexisting={p.address})

for label, candidate in [
    ("correct", lambda a: a["x"]),
    ("wrong", lambda a: a["x"] - 1),
]:
    checked = check(record, "fn.test.read", candidate, store={p.address: 1})
    witness = judge({**checked, "candidate": describe(candidate)})
    print(label, witness["trusted"], witness["store_used"])
```

Observed: `correct False False`, then `wrong True False`.

Proposed repair: resolve an input's version at that invocation. Preserve
explicit producer references; a later write cannot satisfy an earlier read.
Missing historical input evidence should be unknown/refused, not substituted.

### P2: checking another record overwrites the previous witness

`pyto/src/pyto/neat/equiv.py:420-422` names output files only by Calculation and
candidate-function SHA and writes them in overwrite mode. The reviewer invoked
the real CLI main twice with the same candidate and two records in a temporary
output directory (mocking only candidate/JSON loading). A first `trusted:true`
witness was replaced by a second `trusted:false` witness; only the second pair
of files remained.

Proposed repair: give an attempt its own retained identity, binding the record,
inputs, candidate dependencies and comparison contract. A latest pointer may
move without deleting the prior attempt. An immediate scoped workaround is a
distinct `--out-dir` per attempt. Exit code zero currently means the report was
produced, not that `trusted` is true.

### P2: hot makes advice out of missing timing

`pyto/src/pyto/neat/hot.py:161` changes null duration into zero; `:237` turns a
zero sum into 1.0; `:259-268` still emits named hotspots saying “fix here first.”
The repro with entirely null durations produced `measured_ms=1.0` and zero-ms
hotspots selected alphabetically. The studio adapter actually emits null
durations (`pyto/viewer/adapters.js:916-917`), so this directly affects using
hot for the card experiment.

Proposed repair: keep unknown distinct from zero, expose measurement coverage,
and issue timing rankings only over measured invocations. Shape observations
can remain useful without pretending to know timing.

## Additional confirmed findings

| Area | Reproduction / consequence | Source |
| --- | --- | --- |
| hot input identity | One multi-output invocation publishes left=1 and right=2; the same consumer runs on each. Both receive the same input key and trigger a false repeated-input/cache claim. The selected `#address` was discarded. | `hot.py:143-146,185-191` |
| hot array coverage | A valid `kind=array` value with uint8 shape `[256,256,3]` becomes zero elements and unknown shape. Fast-run omitted arrays also yield no element counts. No warning is not proof of cheap execution. | `hot.py:122`; task-150 `hot-evo-fast.txt` |
| hot truncation | Materialized `[[0]*1000]*3` is reported as 1,000 rather than 3,000 elements. A retained prefix of 200 numbers followed by 5,000 omitted dictionaries becomes “5,200 numbers.” | `hot.py:126-129` |
| hot causal inference | A function sleeps then returns an existing 10,000-element list without iterating; the >50 ns/element heuristic says it is walking elements in Python. Ratio is measured; cause is not. | `hot.py:306-308` |
| equiv rectangularity | `canonical([[[1,2],[3,4]],[[5],[6]]]) == canonical([1,2,3,4,5,6])`. Deeper ragged shapes slip through the promised rectangular-only byte path. | `equiv.py:85` |
| equiv failure records | Candidate returns an unserializable value, or returns bytes against an over-cap JSON list. Comparison raises outside the handler, leaving no per-receipt judgment. | `equiv.py:293-300` |
| equiv supported values | Current NumPy `kind=array` records and valid JSON null results are not comparable. These fail closed, unlike the future-writer bug. | `equiv.py:192,252` |
| overlapping studio renders | Concurrent portrait and landscape `sceneParallel()` calls on one runtime both return landscape. Their global invocation logs interleave and receipt calls no longer match their own compositions. | `src/runtime.js:117,246` |
| stale LAB capture | Run sample through stage 6, then begin a different 1×1 capture. New stages are not-run, but old holes remain selectable and a course arrangement renders with them. | `src/runtime.js:475,534`; `src/app.js:383` |
| undo on refusal | Gap 16 → successful 17 → refused −1 creates two undo entries. First undo leaves 17 instead of restoring 16; repeated failures can displace useful history. | `src/runtime.js:149` |
| stale review text | Embedded review says 14 Ticks/14 invocations; current seeded serial scene is 22 Ticks/25 invocations. | `src/review-data.js:19` |

All source paths in the table are relative to this checkout; `hot.py` and
`equiv.py` are under `pyto/src/pyto/neat/`. These are observations at the reviewed
commit, not claims about a newer remote revision.

## Choices that are not accidental bugs

Rectangular shape erasure is expressly filed as `EquivShapeNotInTheDigest` in
task 150's packet. It is useful for a raw-pixel interpretation, but is not
general type/shape equivalence. The byte path also equates signed int8 −1 with
uint8 255, and booleans with bytes 0/1. Name the equivalence contract being used.

The candidate fingerprint is function-body-only, excluding imported helpers,
constants and assets (`pyto/src/pyto/pcr.py:307`). The witness receipt attests the
judge over supplied comparison rows, not a captured trace of candidate effects.
Passing retained examples establishes evidence over those examples, not all
future inputs, performance improvement, side-effect equivalence or acceptance.

The historical 32/32 task-150 witness is inspectable testimony. The packet's
`evo-dense.record.json` is the hot-analysis record, not the original evo run;
its `fast_render.py` imports `fast` and `evolve`, absent here. We did not freshly
reproduce the generation's 32/32 from that packet alone.

## Verification actually performed

- hot reviewer: 22/22 scoped tests, plus in-memory repros above.
- equiv reviewer: 28/28 scoped tests, plus real-PCR and temporary-directory repros.
- studio reviewer: 81/81 across core, cards, LAB pipeline, exports and battle.
- parent: separately ran core/cards (57/57, overlapping the studio set).
- parent: all 24 task-150 claimed file hashes match; verifier/check_all log
  digests match. The historical receipt reports 1,873 tests; we did not rerun
  that entire suite.
- parent: attempted USE.md's isolated tests. Four harness tests passed; the 14
  document subprocesses could not import pyto because this local Python has no
  installed package. The test deliberately strips PYTHONPATH and uses `-I`;
  retrying with an absolute PYTHONPATH did not change that. No test was relaxed,
  no package installed, and these are not reported as source regressions.
- No browser verification during this review.

## Effect on the card-render pilot

The new baseline is the full world at 941f354, including cascade overrides,
shelf-wide assignment and scene state. The parent captured 26 reproducible
outputs and cold/warm measurements under
`evidence/card-render/baseline-941f354/`, with source and harness hashes.

Run timing samples sequentially, or give concurrent candidates independent
runtime instances. Actual SVG/result bytes are distinct from the runtime's
material labels. Browser pixels are a separate check. Use hot as a source of
hypotheses until measurement coverage is honest; do not use a bare equiv exit
code or unqualified trusted flag as a promotion gate. Keep the exact review
material and the human response separate.

No optimization candidate, review acceptance or promotion has been made.
