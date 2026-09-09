# Task 22: Everything is a Part: with observe on, each invocation's receipt is also written into the store under the reserved px.receipt segment, so PQL can read receipts like anything else; with observe off nothing is written; no Calculation may bind a px.receipt address; the testimony stays byte-identical either way

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/22
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/22:pyto/experiments/tasks/22/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 76bc3d2 origin/exp/22 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

Everything is a Part: with observe on, each invocation's receipt is also written into the store under the reserved px.receipt segment, so PQL can read receipts like anything else; with observe off nothing is written; no Calculation may bind a px.receipt address; the testimony stays byte-identical either way

## Starting point

76bc3d2a51c0e5442a0e4e8f519fe7d01484e9f5 (land(task-11): Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test). MAIN may have moved since: `git log --oneline 76bc3d2..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
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
- M  pyto/src/pyto/core.py
- M  pyto/src/pyto/materialize.py
- M  pyto/src/pyto/pcr.py
- M  pyto/tests/test_receipts.py
- M  pyto/viewer/RECORD.md

```
pyto/CHANGES.md                                    |   2 +
 .../evidence/disc-stats-sidecar.json               |   4 +-
 .../grouped-ablation/evidence/lf-source-drift.log  |  12 +-
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
 .../grouped-ablation/evidence/run-1/commit.txt     |   2 +-
 .../grouped-ablation/evidence/run-1/receipts.json  |  60 +++---
 .../grouped-ablation/evidence/run-1/retained.json  |   6 +-
 .../evidence/run-1/saved-work.json                 |   8 +-
 .../grouped-ablation/evidence/run-1/timings.json   |   6 +-
 .../evidence/run-2-regroup/commit.txt              |   2 +-
 .../evidence/run-2-regroup/interpretation.md       |   2 +-
 .../evidence/run-2-regroup/receipts.json           |  44 ++---
 .../evidence/run-2-regroup/retained.json           |   6 +-
 .../evidence/run-2-regroup/saved-work.json         |   4 +-
 .../evidence/run-2-regroup/timings.json            |   6 +-
 .../evidence/run-3-reinput/commit.txt              |   2 +-
 .../evidence/run-3-reinput/interpretation.md       |   2 +-
 .../evidence/run-3-reinput/receipts.json           |  60 +++---
 .../evidence/run-3-reinput/retained.json           |   6 +-
 .../evidence/run-3-reinput/saved-work.json         |   4 +-
 .../evidence/run-3-reinput/timings.json            |   6 +-
 .../evidence/run-4-from-retained/commit.txt        |   2 +-
 .../evidence/run-4-from-retained/interpretation.md |   2 +-
 .../evidence/run-4-from-retained/receipts.json     |  56 +++---
 .../evidence/run-4-from-retained/retained.json     |   6 +-
 .../evidence/run-4-from-retained/saved-work.json   |   4 +-
 .../evidence/run-4-from-retained/timings.json      |   2 +-
 .../evidence/run-6-cached/interpretation.md        |   6 +-
 .../evidence/run-6-cached/reuse-ledger.json        |  16 +-
 .../tamper/mutating-baseline-refused-record.json   |   6 +-
 .../evidence/tamper/retained-tampered.json         |   6 +-
 pyto/src/pyto/core.py                              |  10 +
 pyto/src/pyto/materialize.py                       |  23 ++-
 pyto/src/pyto/pcr.py                               |  55 +++++-
 pyto/tests/test_receipts.py                        | 218 ++++++++++++++++++++-
 pyto/viewer/RECORD.md                              |  17 ++
 45 files changed, 578 insertions(+), 275 deletions(-)
```

## Evidence

- verify: `cd pyto && python3 -m unittest tests.test_receipts tests.test_materialize tests.test_semantics tests.test_first_class` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         155  OK
    experiments/grouped-ablation    240  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           87  OK
    viewer-record-schema             19  OK
    
    ALL SUITES PASSED

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} ReceiptInputNotRefused: the design constraint refuses only a declared `into`/produces under `px.receipt.`, so a Calculation may still *bind a receipt Part as an input* (a test does exactly that); if "no Calculation may bind a px.receipt address" was meant to cover reads too, the guard has to move from `into` to the whole binding map.
{?} ReceiptPreexisting: `run_record`'s inferred `preexisting` excludes only the receipt addresses *this* run wrote, so a receipt left in the store by an earlier run still reports `preexisting: true` when an invocation reads it -- correct by the letter of RECORD.md, but the owner may want no `px.receipt.` Part ever counted as preexisting.
{?} ReceiptNameSegments: the PCR name and the Tick name go into the address verbatim, so a name carrying a dot silently adds a segment (`ablation.grouped` -> `px.receipt.ablation.grouped.Fit.fit.all`) and a name carrying a space makes an address `address.check` cannot flag; slugifying in `receipt_address`, or constraining PCR/Tick names, is a rule I did not want to invent.
{?} ReceiptRerunOverwrite: the scheme has no run identity, so running the same PCR twice against one store replaces each receipt Part in place (one address, no history) and only the last run's receipts survive; adding a run id or an invocation index would keep both, at the cost of an address a reader can no longer predict from the PCR alone.
- Decided: the grouped-ablation evidence was regenerated with the experiment's own scripts because it pins the kernel modules' digests; no test expectation was edited.
{?} ReceiptStoreSetUnguarded: the refusal lives in the binder (`PCR.calc`/`Tick.calc`), not in `PxC.set`, so anything holding the store can still write a forged Part under `px.receipt.` -- consistent with `address.py` describing and enforcing nothing, but it means the segment is reserved against programs, not against callers.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 22 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 22`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-22): Everything is a Part: with observe on, each invocation's receipt is also written into the store under the reserved px.receipt segment, so PQL can read receipts like anything else; with observe off nothing is written; no Calculation may bind a px.receipt address; the testimony stays byte-identical either way`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
