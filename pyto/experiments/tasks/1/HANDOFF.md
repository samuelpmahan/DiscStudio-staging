# Task 1: AHI runs on the owner's Windows D:/: neat new works (host path for pip, python checks the install), the ablation fixture is bit-portable (no libm), the card server drains a 413 body, stripped child environments keep SystemDrive

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging.git DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/1
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/1:pyto/experiments/tasks/1/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff b2a2848 origin/exp/1 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

AHI runs on the owner's Windows D:/: neat new works (host path for pip, python checks the install), the ablation fixture is bit-portable (no libm), the card server drains a 413 body, stripped child environments keep SystemDrive

## Starting point

b2a284825708cd592bb0043eec59f1a88afb07b8 (checkpoint: neat, the caveman version: new, pack, show, drop, land, kill, list over one MAIN and EXP/<id>). MAIN may have moved since: `git log --oneline b2a2848..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/BOARD.md
- M  pyto/LANDING.md
- M  pyto/consumers/discstudio-card/app.py
- M  pyto/experiments/art-tournament/harness/fixtures.py
- M  pyto/experiments/grouped-ablation/evidence/determinism.log
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
- M  pyto/experiments/grouped-ablation/evidence/run-1/comparison.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/comparison.md
- M  pyto/experiments/grouped-ablation/evidence/run-1/failed-variants.md
- M  pyto/experiments/grouped-ablation/evidence/run-1/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-1/variants.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/comparison.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/comparison.md
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-2-regroup/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/comparison.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/comparison.md
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/failed-variants.md
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-3-reinput/variants.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/commit.txt
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/comparison.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/comparison.md
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/failed-variants.md
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/receipts.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/retained.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/saved-work.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/timings.json
- M  pyto/experiments/grouped-ablation/evidence/run-4-from-retained/variants.json
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/interpretation.md
- M  pyto/experiments/grouped-ablation/evidence/run-6-cached/reuse-ledger.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/mutating-baseline-refused-record.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/mutating-baseline-refused.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/report.json
- M  pyto/experiments/grouped-ablation/evidence/tamper/retained-tampered.json
- M  pyto/experiments/grouped-ablation/features.py
- M  pyto/experiments/grouped-ablation/replay.py
- M  pyto/experiments/grouped-ablation/retain.py
- M  pyto/experiments/grouped-ablation/run_cached.py
- M  pyto/experiments/grouped-ablation/test_materials.py
- M  pyto/experiments/grouped-ablation/test_replay.py
- A  pyto/experiments/landings/20260909T073102Z-windows-safety/verifier.txt
- A  pyto/experiments/landings/20260909T073146Z-windows-safety/check_all.txt
- A  pyto/experiments/landings/20260909T073146Z-windows-safety/verifier.txt
- A  pyto/experiments/landings/20260909T073247Z-windows-safety/check_all.txt
- A  pyto/experiments/landings/20260909T073247Z-windows-safety/verifier.txt
- A  pyto/experiments/landings/20260909T073355Z-windows-safety/check_all.txt
- A  pyto/experiments/landings/20260909T073355Z-windows-safety/receipt.json
- A  pyto/experiments/landings/20260909T073355Z-windows-safety/verifier.txt
- A  pyto/experiments/landings/20260909T073510Z-windows-safety/check_all.txt
- A  pyto/experiments/landings/20260909T073510Z-windows-safety/receipt.json
- A  pyto/experiments/landings/20260909T073510Z-windows-safety/verifier.txt
- A  pyto/experiments/landings/20260909T073602Z-windows-safety/check_all.txt
- A  pyto/experiments/landings/20260909T073602Z-windows-safety/receipt.json
- A  pyto/experiments/landings/20260909T073602Z-windows-safety/verifier.txt
- A  pyto/experiments/landings/20260909T073723Z-windows-safety/check_all.txt
- A  pyto/experiments/landings/20260909T073723Z-windows-safety/receipt.json
- A  pyto/experiments/landings/20260909T073723Z-windows-safety/verifier.txt
- A  pyto/experiments/landings/20260909T073836Z-landing-protocol/check_all.txt
- A  pyto/experiments/landings/20260909T073836Z-landing-protocol/receipt.json
- A  pyto/experiments/landings/failed/20260909T073102Z-windows-safety.json
- A  pyto/experiments/landings/failed/20260909T073146Z-windows-safety.json
- A  pyto/experiments/landings/failed/20260909T073247Z-windows-safety.json
- A  pyto/experiments/landings/failed/20260909T073355Z-windows-safety.json
- M  pyto/questions.md
- M  pyto/scripts/check_all.sh
- M  pyto/scripts/land.sh
- M  pyto/scripts/neat.sh

```
pyto/BOARD.md                                      |     7 +
 pyto/LANDING.md                                    |     3 +
 pyto/consumers/discstudio-card/app.py              |    25 +
 .../experiments/art-tournament/harness/fixtures.py |     4 +-
 .../grouped-ablation/evidence/determinism.log      |     2 +-
 .../evidence/disc-stats-sidecar.json               |     4 +-
 .../grouped-ablation/evidence/lf-source-drift.log  |    17 +-
 .../evidence/replay/forged-record-refused.log      |    28 +-
 .../replay/fresh-process-run-2-regroup.log         |    28 +-
 .../replay/fresh-process-run-3-reinput.log         |    28 +-
 .../replay/fresh-process-run-4-from-retained.log   |    28 +-
 .../evidence/replay/fresh-process.log              |    28 +-
 .../evidence/replay/refusals/digest-forged.log     |    28 +-
 .../evidence/replay/refusals/module-leak.log       |    28 +-
 .../evidence/replay/refusals/registry-forged.log   |    28 +-
 .../replay/refusals/source-sha-mismatch.log        |    28 +-
 .../evidence/replay/refusals/value-forged-rows.log |    28 +-
 .../grouped-ablation/evidence/run-1/commit.txt     |     2 +-
 .../evidence/run-1/comparison.json                 |    32 +-
 .../grouped-ablation/evidence/run-1/comparison.md  |    14 +-
 .../evidence/run-1/failed-variants.md              |     4 +-
 .../grouped-ablation/evidence/run-1/receipts.json  |    88 +-
 .../grouped-ablation/evidence/run-1/retained.json  | 16028 +++++-----
 .../evidence/run-1/saved-work.json                 |    14 +-
 .../grouped-ablation/evidence/run-1/timings.json   |     6 +-
 .../grouped-ablation/evidence/run-1/variants.json  |    12 +-
 .../evidence/run-2-regroup/commit.txt              |     2 +-
 .../evidence/run-2-regroup/comparison.json         |    14 +-
 .../evidence/run-2-regroup/comparison.md           |     8 +-
 .../evidence/run-2-regroup/interpretation.md       |     8 +-
 .../evidence/run-2-regroup/receipts.json           |    64 +-
 .../evidence/run-2-regroup/retained.json           | 16020 +++++-----
 .../evidence/run-2-regroup/saved-work.json         |     4 +-
 .../evidence/run-2-regroup/timings.json            |     6 +-
 .../evidence/run-3-reinput/commit.txt              |     2 +-
 .../evidence/run-3-reinput/comparison.json         |    32 +-
 .../evidence/run-3-reinput/comparison.md           |    14 +-
 .../evidence/run-3-reinput/failed-variants.md      |     4 +-
 .../evidence/run-3-reinput/interpretation.md       |     2 +-
 .../evidence/run-3-reinput/receipts.json           |    88 +-
 .../evidence/run-3-reinput/retained.json           | 32028 +++++++++----------
 .../evidence/run-3-reinput/saved-work.json         |     4 +-
 .../evidence/run-3-reinput/timings.json            |     6 +-
 .../evidence/run-3-reinput/variants.json           |     8 +-
 .../evidence/run-4-from-retained/commit.txt        |     2 +-
 .../evidence/run-4-from-retained/comparison.json   |    32 +-
 .../evidence/run-4-from-retained/comparison.md     |    14 +-
 .../run-4-from-retained/failed-variants.md         |     4 +-
 .../evidence/run-4-from-retained/interpretation.md |     2 +-
 .../evidence/run-4-from-retained/receipts.json     |    82 +-
 .../evidence/run-4-from-retained/retained.json     | 14424 ++++-----
 .../evidence/run-4-from-retained/saved-work.json   |     4 +-
 .../evidence/run-4-from-retained/timings.json      |     2 +-
 .../evidence/run-4-from-retained/variants.json     |     8 +-
 .../evidence/run-6-cached/interpretation.md        |     8 +-
 .../evidence/run-6-cached/reuse-ledger.json        |    24 +-
 .../tamper/mutating-baseline-refused-record.json   | 16028 +++++-----
 .../evidence/tamper/mutating-baseline-refused.json |    56 +-
 .../grouped-ablation/evidence/tamper/report.json   |    56 +-
 .../evidence/tamper/retained-tampered.json         | 16028 +++++-----
 pyto/experiments/grouped-ablation/features.py      |    20 +-
 pyto/experiments/grouped-ablation/replay.py        |    93 +-
 pyto/experiments/grouped-ablation/retain.py        |     3 +-
 pyto/experiments/grouped-ablation/run_cached.py    |     4 +
 .../experiments/grouped-ablation/test_materials.py |     7 +
 pyto/experiments/grouped-ablation/test_replay.py   |    13 +-
 .../20260909T073102Z-windows-safety/verifier.txt   |     0
 .../20260909T073146Z-windows-safety/check_all.txt  |  1185 +
 .../20260909T073146Z-windows-safety/verifier.txt   |     1 +
 .../20260909T073247Z-windows-safety/check_all.txt  |  1185 +
 .../20260909T073247Z-windows-safety/verifier.txt   |     1 +
 .../20260909T073355Z-windows-safety/check_all.txt  |  1164 +
 .../20260909T073355Z-windows-safety/receipt.json   |   203 +
 .../20260909T073355Z-windows-safety/verifier.txt   |     1 +
 .../20260909T073510Z-windows-safety/check_all.txt  |  1164 +
 .../20260909T073510Z-windows-safety/receipt.json   |   208 +
 .../20260909T073510Z-windows-safety/verifier.txt   |     1 +
 .../20260909T073602Z-windows-safety/check_all.txt  |  1164 +
 .../20260909T073602Z-windows-safety/receipt.json   |   208 +
 .../20260909T073602Z-windows-safety/verifier.txt   |     0
 .../20260909T073723Z-windows-safety/check_all.txt  |  1164 +
 .../20260909T073723Z-windows-safety/receipt.json   |   218 +
 .../20260909T073723Z-windows-safety/verifier.txt   |     1 +
 .../check_all.txt                                  |  1164 +
 .../20260909T073836Z-landing-protocol/receipt.json |   399 +
 .../failed/20260909T073102Z-windows-safety.json    |     9 +
 .../failed/20260909T073146Z-windows-safety.json    |     9 +
 .../failed/20260909T073247Z-windows-safety.json    |     9 +
 .../failed/20260909T073355Z-windows-safety.json    |     9 +
 pyto/questions.md                                  |    40 +
 pyto/scripts/check_all.sh                          |     7 +
 pyto/scripts/land.sh                               |    12 +-
 pyto/scripts/neat.sh                               |    24 +-
 93 files changed, 65490 insertions(+), 55830 deletions(-)
```

## Evidence

- verify: none beyond the suite
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         103  OK
    experiments/grouped-ablation    230  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           83  OK
    viewer-record-schema             19  OK
    
    ALL SUITES PASSED

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} Evidence regenerated on Windows: fixed experiments/grouped-ablation/features.py's make_data() (random.Random.gauss -> an Irwin-Hall sum-of-12-random()-minus-6 approximation) because gauss() goes through libm and drifted by 1 ULP between this Windows box and the Linux machine that produced the originally committed evidence, which replay.py byte-compares. Regenerated every evidence/run-*/ file that derives from the fixture on this Windows machine (via run.py/run_regrouped.py/run_reinput.py/run_from_retained.py/run_cached.py/replay.py, each with --force) and committed it. commit.txt/retained.commit in that evidence now stamp this worktree's sha rather than the Linux run's. Is committing Windows-generated evidence acceptable, or should it instead be regenerated on the Linux CI box and pulled back in?
{?} grouped-ablation still fails one test on this machine, unrelated to the two assigned failures: test_replay.ChildModuleTable.test_the_full_table_check_is_strictly_stronger_than_the_old_difference asserts the child interpreter has a non-stdlib startup-resident module (comment names _distutils_hack/sitecustomize, from setuptools) before it imports anything; this worktree's .venv has no setuptools installed (no _distutils_hack, no *.pth for it), so the assertion sees an empty list and fails. Not touched, per scope (not one of the two diagnosed failures, and fixing it means either installing setuptools into .venv or loosening the test's environment assumption -- both owner calls). `bash pyto/scripts/check_all.sh` therefore still exits 1 with only experiments/grouped-ablation FAILED; every other suite (library, s3-synthetic, consumer, disc-stats, examples, art-registry-md, viewer, viewer-record-schema) is OK.
{?} Untracked debris found, not touched: two directories literally named `%SystemDrive%` (`pyto/%SystemDrive%/ProgramData/...` and `pyto/experiments/grouped-ablation/%SystemDrive%/ProgramData/...`, each holding a handful of real Windows Caches/*.db files) appeared while running the suites on this machine -- something somewhere is treating a cmd.exe-style `%SystemDrive%` env-var reference as a literal path instead of expanding it. Left untracked and uncommitted since it's unrelated to the two assigned failures and its origin wasn't tracked down; worth a look if it recurs.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 1 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 1`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-1): AHI runs on the owner's Windows D:/: neat new works (host path for pip, python checks the install), the ablation fixture is bit-portable (no libm), the card server drains a 413 body, stripped child environments keep SystemDrive`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
