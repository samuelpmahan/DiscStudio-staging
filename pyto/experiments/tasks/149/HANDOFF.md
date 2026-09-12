# Task 149: a record of big values is cheap and an array is an array: one canonical json dump per value instead of three, an ndarray digested from its dtype, shape and raw bytes (so it has a cache key at last) and carried as kind array with its buffer beside the record instead of 109 MiB of integers, no PNG encoded that cannot fit the cap, and the viewer reading the new kind

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
git clone -b main https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/149
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/149:pyto/experiments/tasks/149/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 04009ce origin/exp/149 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

a record of big values is cheap and an array is an array: one canonical json dump per value instead of three, an ndarray digested from its dtype, shape and raw bytes (so it has a cache key at last) and carried as kind array with its buffer beside the record instead of 109 MiB of integers, no PNG encoded that cannot fit the cap, and the viewer reading the new kind

## Starting point

a0b1b1c877246bd20f33fcb05a413f01e67fb1e0 (land(task-147): pyto study on a table that is not tiny: a seeded sample where the method's cost is quadratic, a refusal where a training fold is narrower than the fit, the separator and the hole spelling the caller's, the entry point callable in a fresh process, and USE.md section 11). MAIN may have moved since: `git log --oneline 04009ce..origin/main` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/USE.md
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
- M  pyto/experiments/grouped-ablation/evidence/run-1/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/reuse-ledger.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/mutating-baseline-refused-record.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/retained-tampered.json
- A  pyto/scripts/bench_record.py
- M  pyto/src/pyto/materialize.py
- M  pyto/src/pyto/pcr.py
- M  pyto/tests/test_materialize.py
- M  pyto/viewer/RECORD.md
- M  pyto/viewer/adapters.js
- M  pyto/viewer/test/adapters.test.mjs
- M  pyto/viewer/test/record_schema.py
- M  pyto/viewer/test/render.test.mjs
- M  pyto/viewer/test/test_record_schema.py
- M  pyto/viewer/tick-viewer.js

```
pyto/USE.md                                        |  21 ++
 .../evidence/disc-stats-sidecar.json               |   2 +-
 .../grouped-ablation/evidence/lf-source-drift.log  |  10 +-
 .../evidence/replay/forged-record-refused.log      |  18 +-
 .../replay/fresh-process-run-2-regroup.log         |  18 +-
 .../replay/fresh-process-run-3-reinput.log         |  18 +-
 .../replay/fresh-process-run-4-from-retained.log   |  18 +-
 .../evidence/replay/fresh-process.log              |  18 +-
 .../evidence/replay/refusals/digest-forged.log     |  18 +-
 .../evidence/replay/refusals/module-leak.log       |  18 +-
 .../evidence/replay/refusals/registry-forged.log   |  18 +-
 .../replay/refusals/source-sha-mismatch.log        |  18 +-
 .../evidence/replay/refusals/value-forged-rows.log |  18 +-
 .../grouped-ablation/evidence/run-1/retained.json  |   4 +-
 .../evidence/run-2-regroup/commit.txt              |   2 +-
 .../evidence/run-2-regroup/receipts.json           |  44 ++--
 .../evidence/run-2-regroup/retained.json           |   4 +-
 .../evidence/run-2-regroup/timings.json            |   6 +-
 .../evidence/run-3-reinput/commit.txt              |   2 +-
 .../evidence/run-3-reinput/receipts.json           |  60 ++---
 .../evidence/run-3-reinput/retained.json           |   4 +-
 .../evidence/run-3-reinput/timings.json            |   6 +-
 .../evidence/run-4-from-retained/commit.txt        |   2 +-
 .../evidence/run-4-from-retained/receipts.json     |  56 ++--
 .../evidence/run-4-from-retained/retained.json     |   4 +-
 .../evidence/run-4-from-retained/timings.json      |   2 +-
 .../evidence/run-6-cached/interpretation.md        |   6 +-
 .../evidence/run-6-cached/reuse-ledger.json        |  14 +-
 .../tamper/mutating-baseline-refused-record.json   |   4 +-
 .../evidence/tamper/retained-tampered.json         |   4 +-
 pyto/scripts/bench_record.py                       | 230 ++++++++++++++++
 pyto/src/pyto/materialize.py                       | 291 ++++++++++++++++++++-
 pyto/src/pyto/pcr.py                               |  76 +++++-
 pyto/tests/test_materialize.py                     | 265 +++++++++++++++++++
 pyto/viewer/RECORD.md                              |  33 ++-
 pyto/viewer/adapters.js                            |  26 +-
 pyto/viewer/test/adapters.test.mjs                 |  38 +++
 pyto/viewer/test/record_schema.py                  |  27 +-
 pyto/viewer/test/render.test.mjs                   |  29 ++
 pyto/viewer/test/test_record_schema.py             |  43 +++
 pyto/viewer/tick-viewer.js                         |  15 ++
 41 files changed, 1282 insertions(+), 228 deletions(-)
```

## Evidence

- verify: `bash pyto/scripts/check_all.sh` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.CAXJ229chI) (evidence/check_all.txt)
    suite                         tests  status
    library                         493  OK
    experiments/brain               756  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK

## Uncertain

{?} ArraySidecarWriter: the owner asked for the raw bytes when "write_record is given a sidecar
directory"; the bytes exist only where the values are, and write_record is handed a finished
document, so `run_record(values_dir=...)` writes them and write_record is unchanged. Undo is one
parameter moved.

{?} ArrayPreviewCap: the owner asked for "a small preview (first array_cap entries flattened)";
his own generation passes array_cap=250000, and under that reading every one of a render's 196,608
numbers is spelled back into the record (123 MiB, measured) and the kind buys nothing. The preview
is the first 200, and array_cap can only lower it. Undo is deleting one `min`.

{?} ArrayDigestIsNew: an ndarray result had no digest at all before (json.dumps refuses one), and
has one now, so a receipt written by a numpy run before today says null where one written after
says a sha256. No committed record or fixture carries an array value, so nothing here changed byte
for byte; a store of receipts kept outside this repository would see it.

{?} OverCapImageNote: an image whose PNG cannot fit the cap now carries a digest of its pixels
(mode, size, raw bytes) instead of a digest of the base64 that used to be built and thrown away.
No fixture carries an omitted image, so the old note's format was not pinned anywhere; the rule is
in RECORD.md.

{?} ModuleDigestEvidence: touching pcr.py changes the pcr.py sha256 that the Day 1 evidence pins
(`provider.pyto.modules`), so evidence/run-1..6, the replay logs, the tamper reports and the
disc-stats sidecar were regenerated through their own builders (replay.py --force, run_regrouped.py,
run_reinput.py, run_from_retained.py, run_cached.py -- never by hand). Their commit.txt now carries
the copy's sha with -dirty, which is what those builders stamp from a working tree.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 149 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 149`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-149): a record of big values is cheap and an array is an array: one canonical json dump per value instead of three, an ndarray digested from its dtype, shape and raw bytes (so it has a cache key at last) and carried as kind array with its buffer beside the record instead of 109 MiB of integers, no PNG encoded that cannot fit the cap, and the viewer reading the new kind`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
