# Task 39: parallel for real and budgets: PcrRun runs the Calculations inside a Tick concurrently when the node law holds, records placement per invocation, refuses a sibling result ref at bind time; a run takes a time budget and stops at a Tick boundary with the record saying where; testimony byte-identical serial versus parallel

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
git fetch origin exp/39
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/39:pyto/experiments/tasks/39/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff c712cf2 origin/exp/39 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

parallel for real and budgets: PcrRun runs the Calculations inside a Tick concurrently when the node law holds, records placement per invocation, refuses a sibling result ref at bind time; a run takes a time budget and stops at a Tick boundary with the record saying where; testimony byte-identical serial versus parallel

## Starting point

0debaf30cfd58da2fd65860d320438abe3bbee54 (board: **sprint** 2026-09-10 02:20 UTC on branch claude/os-sprint-st8hnu: the o). MAIN may have moved since: `git log --oneline c712cf2..origin/claude/os-sprint-st8hnu` shows how far.
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
- M  pyto/src/pyto/materialize.py
- M  pyto/src/pyto/pcr.py
- A  pyto/tests/test_budget.py
- M  pyto/tests/test_multi_into.py
- A  pyto/tests/test_parallel.py
- M  pyto/tests/test_receipts.py
- M  pyto/tests/test_semantics.py
- M  pyto/viewer/RECORD.md
- M  pyto/viewer/adapters.js
- M  pyto/viewer/test/adapters.test.mjs
- M  pyto/viewer/test/record_schema.py
- M  pyto/viewer/test/test_record_schema.py

```
pyto/CHANGES.md                                    |   1 +
 .../evidence/disc-stats-sidecar.json               |   2 +-
 .../grouped-ablation/evidence/lf-source-drift.log  |   8 +-
 .../evidence/replay/forged-record-refused.log      |  22 +-
 .../replay/fresh-process-run-2-regroup.log         |  22 +-
 .../replay/fresh-process-run-3-reinput.log         |  22 +-
 .../replay/fresh-process-run-4-from-retained.log   |  22 +-
 .../evidence/replay/fresh-process.log              |  24 +-
 .../evidence/replay/refusals/digest-forged.log     |  22 +-
 .../evidence/replay/refusals/module-leak.log       |  22 +-
 .../evidence/replay/refusals/registry-forged.log   |  22 +-
 .../replay/refusals/source-sha-mismatch.log        |  22 +-
 .../evidence/replay/refusals/value-forged-rows.log |  22 +-
 .../grouped-ablation/evidence/run-1/commit.txt     |   2 +-
 .../grouped-ablation/evidence/run-1/receipts.json  |  75 +--
 .../grouped-ablation/evidence/run-1/retained.json  |   4 +-
 .../evidence/run-1/saved-work.json                 |   8 +-
 .../grouped-ablation/evidence/run-1/timings.json   |   6 +-
 .../evidence/run-2-regroup/commit.txt              |   2 +-
 .../evidence/run-2-regroup/interpretation.md       |   2 +-
 .../evidence/run-2-regroup/receipts.json           |  55 ++-
 .../evidence/run-2-regroup/retained.json           |   4 +-
 .../evidence/run-2-regroup/saved-work.json         |   4 +-
 .../evidence/run-2-regroup/timings.json            |   6 +-
 .../evidence/run-3-reinput/commit.txt              |   2 +-
 .../evidence/run-3-reinput/interpretation.md       |   2 +-
 .../evidence/run-3-reinput/receipts.json           |  75 +--
 .../evidence/run-3-reinput/retained.json           |   4 +-
 .../evidence/run-3-reinput/saved-work.json         |   4 +-
 .../evidence/run-3-reinput/timings.json            |   6 +-
 .../evidence/run-4-from-retained/commit.txt        |   2 +-
 .../evidence/run-4-from-retained/interpretation.md |   2 +-
 .../evidence/run-4-from-retained/receipts.json     |  70 +--
 .../evidence/run-4-from-retained/retained.json     |   4 +-
 .../evidence/run-4-from-retained/saved-work.json   |   4 +-
 .../evidence/run-4-from-retained/timings.json      |   2 +-
 .../evidence/run-6-cached/interpretation.md        |   6 +-
 .../evidence/run-6-cached/reuse-ledger.json        |  14 +-
 .../tamper/mutating-baseline-refused-record.json   |   4 +-
 .../evidence/tamper/retained-tampered.json         |   4 +-
 pyto/src/pyto/materialize.py                       |  71 ++-
 pyto/src/pyto/pcr.py                               | 540 ++++++++++++++++-----
 pyto/tests/test_budget.py                          | 272 +++++++++++
 pyto/tests/test_multi_into.py                      |  31 +-
 pyto/tests/test_parallel.py                        | 437 +++++++++++++++++
 pyto/tests/test_receipts.py                        |   4 +-
 pyto/tests/test_semantics.py                       |  17 +-
 pyto/viewer/RECORD.md                              |  38 ++
 pyto/viewer/adapters.js                            |  88 ++++
 pyto/viewer/test/adapters.test.mjs                 | 117 +++++
 pyto/viewer/test/record_schema.py                  | 114 ++++-
 pyto/viewer/test/test_record_schema.py             | 159 +++++-
 52 files changed, 2088 insertions(+), 406 deletions(-)
```

## Evidence

- verify: `cd pyto && python3 -m unittest tests.test_receipts tests.test_materialize tests.test_semantics tests.test_first_class tests.test_parallel tests.test_budget` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 1, last line: SOME SUITES FAILED (logs in /tmp/tmp.wQyMWb0GWD) (evidence/check_all.txt)
    suite                         tests  status
    library                         285  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    249  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    experiments/students             14  OK
    experiments/tick-laws            12  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} ScheduleFieldsOptional: the contract says a serial run writes `"placement": null`, but a serial run's record is compared byte for byte against committed evidence by `experiments/students/grade.py` (check 2 drops `duration_ms` and `counters.wall_ms` and nothing else, and `students/` is outside this task's allow list), and `latency_ms` is a wall clock that moves between two identical runs. Taken as the default: the four fields are written **together and only** when the run was parallel, was given a budget, or was stopped by one, so "absent means serial, unbudgeted" is the whole rule in both validators and a serial record is byte for byte what it was. Owner: say the word and `run_record` writes them always, and `students/evidence/run-1/record.json` is regenerated with `latency_ms` added to grade.py's not-compared list.

{?} ReceiptWriteMarker (merge with task 41, decided by the record): after merging MAIN, `pcr.py` files its receipts with `pxc.set(..., _from_run=True)` -- the marker `core.py`'s new guard names as the run's own (`PxC.set`, "``_from_run`` is the run's marker: ``PcrRun``'s observe branch passes it when it files a receipt"). The guard's frame fallback (`RUN_MODULE = "pyto.pcr"`) still passes for this kernel, and was written only because `pcr.py` was another team's file at the time; saying so beats being recognised, and it is what lets a store *view* between the run and the PxC relay a receipt write without owning a frame in `pyto.pcr` -- which is exactly what `tests/test_parallel.RecordingPxC`, the oracle for "the store never holds half a Tick", is. Two lines: the marker in `pcr.py:_publish`, and `**marker` relayed by that test's view.

{?} ParallelFailure: a branch that raises stops the run before anything of its Tick is published, so its siblings' work is discarded and they file no receipts -- the price of "the store never sees half a Tick". `{?} TicksAsCircuits` wants the other reading ("a failing branch leaves its siblings' receipts and shows as a hole downstream"), which needs a partial-Tick publish and a receipt for a Calculation whose Part was never written. Left as it is, with a test only for the atomicity, until the owner picks which of the two the record should show.

{?} ParallelDurations: in a parallel run an invocation's `duration_ms` is measured from the worker picking it up to its Part being published, so it includes the wait for its slowest sibling, and a Tick's `sum(duration_ms)` is therefore *not* the work it would have taken serially. `latency_ms` is exact either way. Alternative: stop the clock when the call returns and leave the publish out of it, which makes the work figure honest and the "what did PCR.run do on this invocation's behalf" reading less so.

{?} WorkerNumbering: `placement.worker` is handed out in the order threads first pick work up **within one Tick**, so it is stable in a run but means nothing across Ticks or across runs, and the same OS thread can be worker 0 in one Tick and worker 1 in the next. Enough to read "these two really did overlap" off a record; not enough to say "the same worker ran both of these".

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 39 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 39`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-39): parallel for real and budgets: PcrRun runs the Calculations inside a Tick concurrently when the node law holds, records placement per invocation, refuses a sibling result ref at bind time; a run takes a time budget and stops at a Tick boundary with the record saying where; testimony byte-identical serial versus parallel`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
