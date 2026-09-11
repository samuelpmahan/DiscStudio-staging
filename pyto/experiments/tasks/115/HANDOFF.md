# Task 115: S4 Holes: assemble each hole from S1 badges, S2 baskets and S3 tees as a Stage with explicit invariants, and extend the lab fixture with a third badge and an obstacle region

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
git fetch origin exp/115
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/115:pyto/experiments/tasks/115/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff b082fab origin/exp/115 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

S4 Holes: assemble each hole from S1 badges, S2 baskets and S3 tees as a Stage with explicit invariants, and extend the lab fixture with a third badge and an obstacle region

## Starting point

db7bf336ed1dc3af0441711c7a4f1c135063d2f9 (land(task-114): port S2 (baskets) and S3 (visible tees) onto the studio core as the documents their OperationSpecs declare, with the Python analogue's ring balance as S3's oracle, and redefine pathfinding on the Stage outputs: the round in badge order, tee to basket to the next tee). MAIN may have moved since: `git log --oneline b082fab..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  src/lab/fixtures.js
- M  src/lab/map.js
- A  src/lab/s4.js
- M  src/lab/source.js
- A  src/lab/stages/S4.args.json
- A  src/lab/stages/S4.mmd
- M  src/lab/store/lab.json
- M  src/lab/store/records/S0.json
- M  src/lab/store/records/S1.json
- M  src/lab/store/records/S2.json
- M  src/lab/store/records/S3.json
- M  src/lab/store/records/S3.quick-anno.json
- A  src/lab/store/records/S4.invariants.json
- A  src/lab/store/records/S4.json
- M  src/lab/store/records/route-labfixture.json
- A  tests/lab-s4.test.js

```
src/lab/fixtures.js                         |   64 +-
 src/lab/map.js                              |   21 +-
 src/lab/s4.js                               |  229 ++
 src/lab/source.js                           |    9 +
 src/lab/stages/S4.args.json                 |    3 +
 src/lab/stages/S4.mmd                       |   31 +
 src/lab/store/lab.json                      | 4314 +++++++++++++++++++++------
 src/lab/store/records/S0.json               |   58 +-
 src/lab/store/records/S1.json               | 2854 +++++++++++++-----
 src/lab/store/records/S2.json               |  128 +-
 src/lab/store/records/S3.json               |  199 +-
 src/lab/store/records/S3.quick-anno.json    |   24 +-
 src/lab/store/records/S4.invariants.json    |  196 ++
 src/lab/store/records/S4.json               |  730 +++++
 src/lab/store/records/route-labfixture.json |   89 +-
 tests/lab-s4.test.js                        |  137 +
 16 files changed, 7404 insertions(+), 1682 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 1, last line: SOME SUITES FAILED (logs in /tmp/tmp.GYczQsJxNP) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               756  FAIL
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

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 115 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 115`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-115): S4 Holes: assemble each hole from S1 badges, S2 baskets and S3 tees as a Stage with explicit invariants, and extend the lab fixture with a third badge and an obstacle region`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
