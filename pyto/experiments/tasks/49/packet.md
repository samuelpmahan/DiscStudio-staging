# Task 49

Intent: oc, effects with receipts: an OperationalCalculation (oc. prefix) may perform effects only through an Effects handle the run gives it (write_text, read_text, now_ms, random, env); every effect is recorded in the receipt and the run record; replay feeds recorded effect results back and refuses a tampered one; fn. Calculations get no effects; px effects lists them; testimony byte-identical observe on and off
Starting point: 46303dd6deb50b05be812d8a07c20e49d68e6205 (board: **started** `task-48`: the JavaScript runtime speaks the same schedule:)
Verify: cd pyto && python3 -m unittest tests.test_receipts tests.test_materialize tests.test_semantics tests.test_first_class tests.test_parallel tests.test_budget tests.test_effects tests.test_px
Allow: pyto/src/pyto/pcr.py pyto/src/pyto/core.py pyto/src/pyto/effects.py pyto/src/pyto/materialize.py pyto/src/pyto/px.py pyto/src/pyto/__init__.py pyto/tests pyto/viewer/RECORD.md pyto/viewer/test/record_schema.py pyto/viewer/test/test_record_schema.py pyto/viewer/fixtures pyto/experiments/grouped-ablation/evidence pyto/CHANGES.md pyto/experiments/tasks
Candidate: 61 files of this task's own, plus MAIN merged in (see Merge below)
Evidence: verify exit 0, suite exit 0 (ALL SUITES PASSED after merging MAIN), see below

## What landed

- `pyto/src/pyto/effects.py` (new): `Effects` (performs and records) and `ReplayEffects` (plays a
  recorded ledger back), five verbs -- `write_text`, `read_text`, `now_ms`, `random`, `env` -- one
  ledger entry per call, `{kind, args, result, result_sha256}`, paths relative to the run's
  `effects_root` and never absolute, one digest rule (sha256 of canonical JSON) for every kind.
- `core.py`: `CALCULATION_ROOTS = ("fn.", "oc.")` and no third; `Calculation.is_operational`;
  `EFFECTS_ARG = "effects"`, the one argument name an `oc.` receives its handle under.
- `pcr.py`: `PCR.run(..., effects_root=, replay_effects=, allow_parallel_effects=)`; a fresh handle
  per `oc` invocation; `Receipt.effects` and `PcrRun.effects` (filled with `observe` on **and**
  off); an `oc` in a parallel Tick refused without the opt-in; a replay that diverges refused with
  the invocation, the kind and the index.
- `materialize.py` + `viewer/RECORD.md` + `viewer/test/record_schema.py` (+ its tests): the
  optional per-invocation `effects` list, its entry shape, and a validator that accepts exactly it.
- `px.py`: `px effects <record> [--tick NAME]`, pinned byte for byte against
  `tests/fixtures/px/effects-demo.txt`, `effects-demo-summarize.txt` and `effects-students.txt`
  over the committed `tests/fixtures/px/effects-record.json`.
- `tests/test_effects.py` (24 tests) and `tests/fixture_effects.py`, the `oc` program the record,
  the fresh-process replay child and the `px` fixture all share.

`pyto/viewer/adapters.js` was **not** touched: another team is editing it. The JavaScript reader
ignores keys it does not know, so a record carrying `effects` reads there exactly as it did before,
and teaching the viewer to draw effects is that team's change, not this one.

## Merge with MAIN (claude/os-sprint-st8hnu @ 20cee0f)

`git merge claude/os-sprint-st8hnu` -- tasks 39 (landed), 40, 42, 43, 46, 47, 50, 51 -- reported
**no conflicted file**; the three-way merge resolved every overlap on its own, and each was checked
by hand afterwards:

- `pyto/experiments/grouped-ablation/evidence` (39 files both sides had regenerated): the merge kept
  this side's, and all of it was regenerated again from the merged tree by the six commands below,
  so the question is moot in the committed bytes.
- `pyto/src/pyto/pcr.py`, `materialize.py`, `core.py`, `px.py`: everything MAIN has added there
  since `46303dd` is task 39, which is already in this branch's base (`c087bd7`), so there was
  nothing of MAIN's to re-apply and this side's files stand unchanged. `git diff MERGE_HEAD --
  pyto/src` is this task's diff and nothing else.
- `pyto/viewer/RECORD.md`: took MAIN's rename of `tickLatencyMs` to `tickLatencyMsFromRecord` and
  its `{?} TwoLatencyFallbacks` paragraph, kept this task's "Effects" section.
- `pyto/viewer/test/test_record_schema.py`: took MAIN's four `tickLatencyMsFromRecord` call sites,
  kept this task's `EffectsLedger` class.
- `pyto/CHANGES.md`: kept both sides' entries; the merge left `## exp/39` twice (MAIN reordered the
  file), so the second copy -- byte-identical to the first -- was deleted, leaving MAIN's order with
  this task's `## exp/49` line on top.
- everything outside the allow list (`viewer/adapters.js`, `viewer/tick-viewer.js`,
  `viewer/fixtures/effects-demo.json`, `viewer/test/effects-view.test.mjs`, BOARD, FRONTIER, KT-MAC,
  the landings, `experiments/classroom`, the workflow) is MAIN's, untouched.

The viewer failure this task reported before the merge is gone: MAIN's rename removed the duplicate
export, and the `viewer` suite is green (130 tests).

**The two readers, checked against each other after the merge.** MAIN's `adapters.js` `validate`
accepts a record this task's `materialize.run_record` wrote and `fromPytoRecord` reads all five of
its ledger entries (`write_text, now_ms, random_seed, random, random`), so the JS reader refuses
nothing this side produces. The other direction does not hold; see `{?} EffectsDemoFixtureShape`.

## Candidate

- M  pyto/CHANGES.md
- M  pyto/experiments/grouped-ablation/evidence/disc-stats-sidecar.json
- M  pyto/experiments/grouped-ablation/evidence/lf-source-drift.log
- M  pyto/experiments/grouped-ablation/evidence/replay/forged-record-refused.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-2-regroup.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-3-reinput.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process-run-4-from-retained.log
- M  pyto/experiments/grouped-ablation/evidence/replay/fresh-process.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/digest-forged.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/module-leak.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/registry-forged.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/source-sha-mismatch.log
- M  pyto/experiments/grouped-ablation/evidence/replay/refusals/value-forged-rows.log
- M  pyto/experiments/grouped-ablation/evidence/run-1/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-1/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/reuse-ledger.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/mutating-baseline-refused-record.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/retained-tampered.json
- A  pyto/experiments/tasks/49/evidence/check_all.txt
- A  pyto/experiments/tasks/49/evidence/verify.txt
- A  pyto/experiments/tasks/49/packet.md
- M  pyto/src/pyto/__init__.py
- M  pyto/src/pyto/core.py
- A  pyto/src/pyto/effects.py
- M  pyto/src/pyto/materialize.py
- M  pyto/src/pyto/pcr.py
- M  pyto/src/pyto/px.py
- A  pyto/tests/fixture_effects.py
- A  pyto/tests/fixtures/px/effects-demo-summarize.txt
- A  pyto/tests/fixtures/px/effects-demo.txt
- A  pyto/tests/fixtures/px/effects-record.json
- A  pyto/tests/fixtures/px/effects-students.txt
- A  pyto/tests/test_effects.py
- M  pyto/tests/test_multi_into.py
- M  pyto/tests/test_px.py
- M  pyto/tests/test_semantics.py
- M  pyto/viewer/RECORD.md
- M  pyto/viewer/test/record_schema.py
- M  pyto/viewer/test/test_record_schema.py

## Evidence

- verify: `cd pyto && python3 -m unittest tests.test_receipts tests.test_materialize tests.test_semantics tests.test_first_class tests.test_parallel tests.test_budget tests.test_effects tests.test_px` exit 0, 215 tests, OK (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt), after merging MAIN

    == per-suite counts
    suite                         tests  status
    library                         314  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                          130  OK
    viewer-record-schema             36  OK
    
    ALL SUITES PASSED (logs in /tmp/tmp.XXSIoG2bN3)
    exit=0

- grouped-ablation evidence regenerated twice, before the merge and again from the merged tree (pinned `pcr.py`/`core.py` digests moved): `run.py --out evidence/run-1 --force`, `run_regrouped.py --force`, `run_reinput.py --force`, `run_from_retained.py --force`, `run_cached.py --force`, `replay.py --force`, in that order. `evidence/run-1/record.json` is **unchanged** -- the Day 1 program is pure, so its record carries no `effects` field -- while `receipts.json` gained `"effects": []` per receipt.
- the effects ledger of the test run, as `px effects tests/fixtures/px/effects-record.json` prints it:

    TICK  ID     INDEX  KIND         ARGS          DIGEST
    0     stamp  0      write_text   out/note.txt  d21ca159a726d89af58f7d9fc59be7bced2c40e07e2ec0fcc02aee380b447de6
    0     stamp  1      now_ms       -             3ac586ef19aeef0c72224b75ab639426b7e2aff953943f6f7251045336d3d3fd
    0     stamp  2      random_seed  -             a30034cc537bfb7d29ad2faa1a4c0594de7bd352f64e7492b9dc06297e3f37f3
    0     stamp  3      random       n=1           1361a01415f7dd8eb8f1b3d6d6c0e62857f7d557094e62e0c755ed2d8c9db175
    0     stamp  4      random       n=1           762aa71a7b8055acaf31ed128a2d4bcb7ce96df7b8d4513a903f034bda9ed59c

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} EffectsFieldOptional: the task asked for `effects` on every invocation; it is written on every invocation of a run that had effects (an `oc.` ran, or a receipt carries a ledger) and left out entirely when the run had none, exactly as `{?} ScheduleFieldsOptional` treats placement -- because unconditional presence changes the bytes of every record ever written, and `experiments/students/grade.py` check 2 compares a fresh record against the committed one field for field (its evidence is outside this task's allow list). Absent therefore means "this run performed no effect", and inside a record that carries the field an empty list means "this invocation performed none".
{?} EffectsInTestimony: "testimony includes the effects ledger" is implemented as `PcrRun.effects` filled with `observe` on and off (an effect is what happened, not an observation of it) rather than as a new field on `CalculationTestimony`, because `ticks` is the bytes consumers embed (`consumers/discstudio-card/card_composition.py:177`) and `experiments/grouped-ablation/retain.py` requires a retained program to equal `asdict(run.ticks)`; if the owner wants the ledger inside `ticks` itself, that is a testimony-bytes change and wants its own task.
{?} ParallelEffectsOptIn: an `oc.` inside a parallel Tick is refused unless `PCR.run(..., allow_parallel_effects=True)` -- the simplest honest rule, since "their effects are file writes to distinct paths" is not checkable before the branches run; the alternative (check the ledgers afterwards and refuse a collision) would let both writes happen first, so it is not obviously better.
{?} RandomSeedIsAnEffect: `random(n)` draws from a seeded generator whose seed is drawn once per handle and recorded as its own ledger entry (`random_seed`), so the demo's "a write, a clock and two draws" is five entries and not four, and a kind was added that the intent's five verbs do not name.
{?} EffectDigestIsCanonicalJson: `result_sha256` is sha256 of the canonical JSON of the recorded value for every kind, including `write_text`, so a written file's ledger digest is the digest of the JSON string, not `sha256sum` of the file's bytes; one rule makes any two entries comparable, but a reader who wants to check a file on disk has to digest it the same way.
{?} OcNeedsEffectsRoot: reaching an `oc.` with no `effects_root` refuses the run rather than defaulting to the cwd, and when `replay_effects` is given every `oc.` invocation must have a ledger in it (an id it does not name would perform a real effect in the middle of a replay).
{?} ViewerBundleDuplicateBeforeThisTask: **resolved by the merge.** Before merging MAIN, `check_all.sh` ended in SOME SUITES FAILED because `viewer/adapters.js:576` and `viewer/tick-viewer.js:138` both exported `tickLatencyMs` and the inlined bundle would not parse -- at the branch's starting commit `c087bd7`, before this task's first edit, and in two files outside this allow list. MAIN's rename to `tickLatencyMsFromRecord` (task 39's landing) fixes it; after the merge every suite passes.
{?} EffectsDemoFixtureShape: `viewer/fixtures/effects-demo.json` (task 50's hand-made witness, another team's file) is **not** a record this task's validator accepts: its ledger entries carry no `result` key and their paths are absolute (`/tmp/effects-demo/roster.csv`), where RECORD.md's "Effects" says an entry is exactly `{kind, args, result, result_sha256}` and a path is relative to the run's `effects_root` and never absolute. Nothing in Python reads that fixture, so no suite fails; the JS side accepts what pyto writes, and the disagreement is only about what a *hand-made* record may claim. Either the fixture is regenerated from a real run or the shape is loosened -- both are the owner's call, and this task changed neither.
{?} JsEffectKindsMissRandomSeed: `viewer/tick-viewer.js` `EFFECT_KINDS` lists five kinds (`write_text, read_text, now_ms, random, env`) and not `random_seed`, which this kernel records because the seed is an effect; the viewer draws an unknown kind unstyled rather than refusing it, so a real record renders, with its seed row plainer than its neighbours.
