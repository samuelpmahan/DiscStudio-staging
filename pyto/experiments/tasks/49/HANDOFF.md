# Task 49: oc, effects with receipts: an OperationalCalculation (oc. prefix) may perform effects only through an Effects handle the run gives it (write_text, read_text, now_ms, random, env); every effect is recorded in the receipt and the run record; replay feeds recorded effect results back and refuses a tampered one; fn. Calculations get no effects; px effects lists them; testimony byte-identical observe on and off

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Stop here first (the owner's rule)

Read this page, `pyto/BOARD.md`, and the packet. No fourth file yet. Then write the one question
you would answer by reading another hundred thousand tokens of code, and ask the owner instead.
His answer is worth more than the reading: the last session that read everything first was
confidently wrong about half of it, and one sentence from him undid each wrong half. The answer
goes on `pyto/questions.md` verbatim, as `{?} Label: ...` with his words, so the next agent starts
one stupid question deeper. Only then read further and do the work below.

## Get the code (once)

```
git clone -b claude/os-sprint-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/49
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/49:pyto/experiments/tasks/49/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 20cee0f origin/exp/49 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
```

## Why this repository is worth twenty minutes

pyto is a Python transfer of a design the owner proved three times in JavaScript and TypeScript
(ChainSpot, ChessLab, EmbodiedWumpusWorld): a store of named values (PxC), pure functions over them
(Calculations), and a program that names which functions run in which order (a PCR, made of Ticks).
Every run leaves receipts: what each function read and wrote, how long it took, and a digest of its
source. From receipts you get three things for free: a cache (same inputs and digest, skip the call,
also across processes), a replay that verifies a shipped record in a fresh process, and a per-Tick
view of what the algorithm used. The founding need is the last one: the owner's course-map parser
had to fit five seconds on a phone, and nothing it used was visible. pyto is the workshop where that
visibility is designed before it is stripped for speed. JavaScript is first class; Python is where
the design is checked.

Do not take that from this page. In two minutes:

```
bash pyto/scripts/check_all.sh                                        # nine suites, ~600 tests
python pyto/experiments/grouped-ablation/run_cached.py --out /tmp/hit  # a miss, then two hits, one from a fresh process
node pyto/viewer/embed.mjs pyto/viewer/fixtures/pyto-grouped-ablation.json --out /tmp/hit/ticks.html
```

The tests were checked by mutation (each guards a specific line). The fixtures for the JavaScript
port are 440 byte-exact cases. `pyto/questions.md` is where anyone unsure writes `{?} Label: ...`
and the owner answers; read it before assuming. `pyto/BOARD.md` is the owner's one page.

## What was asked

oc, effects with receipts: an OperationalCalculation (oc. prefix) may perform effects only through an Effects handle the run gives it (write_text, read_text, now_ms, random, env); every effect is recorded in the receipt and the run record; replay feeds recorded effect results back and refuses a tampered one; fn. Calculations get no effects; px effects lists them; testimony byte-identical observe on and off

## Starting point

46303dd6deb50b05be812d8a07c20e49d68e6205 (board: **started** `task-48`: the JavaScript runtime speaks the same schedule:). MAIN may have moved since: `git log --oneline 20cee0f..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

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

```
pyto/CHANGES.md                                    |   1 +
 .../evidence/disc-stats-sidecar.json               |   4 +-
 .../grouped-ablation/evidence/lf-source-drift.log  |  12 +-
 .../evidence/replay/forged-record-refused.log      |  22 +-
 .../replay/fresh-process-run-2-regroup.log         |  22 +-
 .../replay/fresh-process-run-3-reinput.log         |  22 +-
 .../replay/fresh-process-run-4-from-retained.log   |  22 +-
 .../evidence/replay/fresh-process.log              |  22 +-
 .../evidence/replay/refusals/digest-forged.log     |  22 +-
 .../evidence/replay/refusals/module-leak.log       |  22 +-
 .../evidence/replay/refusals/registry-forged.log   |  22 +-
 .../replay/refusals/source-sha-mismatch.log        |  22 +-
 .../evidence/replay/refusals/value-forged-rows.log |  22 +-
 .../grouped-ablation/evidence/run-1/commit.txt     |   2 +-
 .../grouped-ablation/evidence/run-1/receipts.json  |  75 +--
 .../grouped-ablation/evidence/run-1/retained.json  |   6 +-
 .../evidence/run-1/saved-work.json                 |   8 +-
 .../grouped-ablation/evidence/run-1/timings.json   |   6 +-
 .../evidence/run-2-regroup/commit.txt              |   2 +-
 .../evidence/run-2-regroup/interpretation.md       |   2 +-
 .../evidence/run-2-regroup/receipts.json           |  55 +-
 .../evidence/run-2-regroup/retained.json           |   6 +-
 .../evidence/run-2-regroup/saved-work.json         |   4 +-
 .../evidence/run-2-regroup/timings.json            |   6 +-
 .../evidence/run-3-reinput/commit.txt              |   2 +-
 .../evidence/run-3-reinput/interpretation.md       |   2 +-
 .../evidence/run-3-reinput/receipts.json           |  75 +--
 .../evidence/run-3-reinput/retained.json           |   6 +-
 .../evidence/run-3-reinput/saved-work.json         |   4 +-
 .../evidence/run-3-reinput/timings.json            |   6 +-
 .../evidence/run-4-from-retained/commit.txt        |   2 +-
 .../evidence/run-4-from-retained/interpretation.md |   2 +-
 .../evidence/run-4-from-retained/receipts.json     |  70 ++-
 .../evidence/run-4-from-retained/retained.json     |   6 +-
 .../evidence/run-4-from-retained/saved-work.json   |   4 +-
 .../evidence/run-4-from-retained/timings.json      |   2 +-
 .../evidence/run-6-cached/interpretation.md        |   6 +-
 .../evidence/run-6-cached/reuse-ledger.json        |  14 +-
 .../tamper/mutating-baseline-refused-record.json   |   6 +-
 .../evidence/tamper/retained-tampered.json         |   6 +-
 pyto/src/pyto/__init__.py                          |   5 +
 pyto/src/pyto/core.py                              |  41 +-
 pyto/src/pyto/effects.py                           | 397 ++++++++++++++
 pyto/src/pyto/materialize.py                       |  15 +
 pyto/src/pyto/pcr.py                               | 175 +++++-
 pyto/src/pyto/px.py                                |  58 +-
 pyto/tests/fixture_effects.py                      |  99 ++++
 pyto/tests/fixtures/px/effects-demo-summarize.txt  |   1 +
 pyto/tests/fixtures/px/effects-demo.txt            |   6 +
 pyto/tests/fixtures/px/effects-record.json         | 160 ++++++
 pyto/tests/fixtures/px/effects-students.txt        |   1 +
 pyto/tests/test_effects.py                         | 587 +++++++++++++++++++++
 pyto/tests/test_multi_into.py                      |   9 +-
 pyto/tests/test_px.py                              |  60 +++
 pyto/tests/test_semantics.py                       |   4 +
 pyto/viewer/RECORD.md                              |  58 ++
 pyto/viewer/test/record_schema.py                  |  54 +-
 pyto/viewer/test/test_record_schema.py             |  83 ++-
 58 files changed, 2134 insertions(+), 301 deletions(-)
```

## Evidence

- verify: `cd pyto && python3 -m unittest tests.test_receipts tests.test_materialize tests.test_semantics tests.test_first_class tests.test_parallel tests.test_budget tests.test_effects tests.test_px` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.caELe3skM0) (evidence/check_all.txt)
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

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 49 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 49`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-49): oc, effects with receipts: an OperationalCalculation (oc. prefix) may perform effects only through an Effects handle the run gives it (write_text, read_text, now_ms, random, env); every effect is recorded in the receipt and the run record; replay feeds recorded effect results back and refuses a tampered one; fn. Calculations get no effects; px effects lists them; testimony byte-identical observe on and off`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
