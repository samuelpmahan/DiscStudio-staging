# Task 123: S4 Recovery: the objects the clean detectors lose to an overlap, found again from other evidence -- the LAB's own dark-plate recovery for badges, and the shell recovery and component fallback its S2 and S3 receipts mark NOT RUN -- published as px.recovered.* for the later Stages to read

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
git fetch origin exp/123
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/123:pyto/experiments/tasks/123/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff bcfd499 origin/exp/123 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

S4 Recovery: the objects the clean detectors lose to an overlap, found again from other evidence -- the LAB's own dark-plate recovery for badges, and the shell recovery and component fallback its S2 and S3 receipts mark NOT RUN -- published as px.recovered.* for the later Stages to read

## Starting point

88ca019fdd869010f3fdc122907069ab2d08be06 (land(task-121): renumber the invented Stages to the owner's S4-S7: the nearest-anchor hole assembly becomes the HolesByNearestAnchor fallback, the course graph and the A* round become S7 Pathfinding, and S4/S5/S6 are freed for recovery, the tee-to-badge ray and the straight holes). MAIN may have moved since: `git log --oneline bcfd499..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  src/lab/fixtures.js
- M  src/lab/map.js
- A  src/lab/s4.js
- M  src/lab/stage-sources.js
- A  src/lab/stages/S4.args.json
- A  src/lab/stages/S4.mmd
- M  src/lab/store/lab.json
- M  src/lab/store/records/HolesByNearestAnchor.invariants.json
- M  src/lab/store/records/HolesByNearestAnchor.json
- M  src/lab/store/records/S0.json
- M  src/lab/store/records/S1.json
- M  src/lab/store/records/S2.json
- M  src/lab/store/records/S3.json
- M  src/lab/store/records/S3.quick-anno.json
- A  src/lab/store/records/S4.invariants.json
- A  src/lab/store/records/S4.json
- M  src/lab/store/records/S7.course.invariants.json
- M  src/lab/store/records/S7.course.json
- M  src/lab/store/records/S7.round.invariants.json
- M  src/lab/store/records/S7.round.json
- M  src/lab/store/records/S7.vs-straight.json
- M  src/lab/store/records/route-labfixture.json
- A  tests/lab-s4.test.js

```
src/lab/fixtures.js                                |   50 +-
 src/lab/map.js                                     |   14 +-
 src/lab/s4.js                                      |  280 +
 src/lab/stage-sources.js                           |    2 +
 src/lab/stages/S4.args.json                        |   29 +
 src/lab/stages/S4.mmd                              |   50 +
 src/lab/store/lab.json                             | 9156 +++++++++++---------
 .../records/HolesByNearestAnchor.invariants.json   |   32 +-
 src/lab/store/records/HolesByNearestAnchor.json    |  217 +-
 src/lab/store/records/S0.json                      |   43 +-
 src/lab/store/records/S1.json                      | 2566 +++---
 src/lab/store/records/S2.json                      |  252 +-
 src/lab/store/records/S3.json                      |  175 +-
 src/lab/store/records/S3.quick-anno.json           |   24 +-
 src/lab/store/records/S4.invariants.json           |  164 +
 src/lab/store/records/S4.json                      | 3306 +++++++
 src/lab/store/records/S7.course.invariants.json    |   40 +-
 src/lab/store/records/S7.course.json               |  315 +-
 src/lab/store/records/S7.round.invariants.json     |   32 +-
 src/lab/store/records/S7.round.json                |  843 +-
 src/lab/store/records/S7.vs-straight.json          |   55 +-
 src/lab/store/records/route-labfixture.json        |  203 +-
 tests/lab-s4.test.js                               |  151 +
 23 files changed, 10632 insertions(+), 7367 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.YR8UYgZLrO) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
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

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 123 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 123`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-123): S4 Recovery: the objects the clean detectors lose to an overlap, found again from other evidence -- the LAB's own dark-plate recovery for badges, and the shell recovery and component fallback its S2 and S3 receipts mark NOT RUN -- published as px.recovered.* for the later Stages to read`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
