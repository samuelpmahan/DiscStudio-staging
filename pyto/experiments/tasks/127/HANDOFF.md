# Task 127: S7 plays the holes S6 resolved: the course graph binds px.holes.straight and reports px.holes.unresolved as unplayed doglegs, a second pointing tee gives the round more than one leg, and the comparison with the straight-leg route is re-run on that binding

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
git fetch origin exp/127
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/127:pyto/experiments/tasks/127/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 878f7a9 origin/exp/127 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

S7 plays the holes S6 resolved: the course graph binds px.holes.straight and reports px.holes.unresolved as unplayed doglegs, a second pointing tee gives the round more than one leg, and the comparison with the straight-leg route is re-run on that binding

## Starting point

878f7a91d29db8f1b13ee8cabf4f58bb8ec01e56 (land(task-126): the port's map, honest after the renumbering: S4-S7 under ran, the stubs that S4 recovery actually retired removed, and what S7 still owes the straight holes written down as the next step with its for). MAIN may have moved since: `git log --oneline 878f7a9..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  src/lab/fixtures.js
- M  src/lab/map.js
- M  src/lab/s7course.js
- M  src/lab/s7round.js
- M  src/lab/stage-sources.js
- M  src/lab/stages.js
- M  src/lab/stages/S7.course.mmd
- M  src/lab/store/lab.json
- M  src/lab/store/records/HolesByNearestAnchor.invariants.json
- M  src/lab/store/records/HolesByNearestAnchor.json
- M  src/lab/store/records/S0.json
- M  src/lab/store/records/S1.json
- M  src/lab/store/records/S2.json
- M  src/lab/store/records/S3.json
- M  src/lab/store/records/S3.quick-anno.json
- M  src/lab/store/records/S4.invariants.json
- M  src/lab/store/records/S4.json
- M  src/lab/store/records/S5.invariants.json
- M  src/lab/store/records/S5.json
- M  src/lab/store/records/S6.invariants.json
- M  src/lab/store/records/S6.json
- M  src/lab/store/records/S7.course.invariants.json
- M  src/lab/store/records/S7.course.json
- M  src/lab/store/records/S7.round.invariants.json
- M  src/lab/store/records/S7.round.json
- M  src/lab/store/records/S7.vs-straight.json
- M  src/lab/store/records/route-labfixture.json
- M  src/runtime.js
- M  tests/lab-pipeline.test.js
- M  tests/lab-s7course.test.js
- M  tests/lab-s7round.test.js

```
src/lab/fixtures.js                                |   25 +-
 src/lab/map.js                                     |    7 +-
 src/lab/s7course.js                                |   67 +-
 src/lab/s7round.js                                 |   32 +-
 src/lab/stage-sources.js                           |    2 +-
 src/lab/stages.js                                  |    8 +
 src/lab/stages/S7.course.mmd                       |    6 +-
 src/lab/store/lab.json                             | 2716 ++++++++++++++------
 .../records/HolesByNearestAnchor.invariants.json   |   24 +-
 src/lab/store/records/HolesByNearestAnchor.json    |  173 +-
 src/lab/store/records/S0.json                      |   56 +-
 src/lab/store/records/S1.json                      |  262 +-
 src/lab/store/records/S2.json                      |  150 +-
 src/lab/store/records/S3.json                      |  175 +-
 src/lab/store/records/S3.quick-anno.json           |   24 +-
 src/lab/store/records/S4.invariants.json           |    8 +-
 src/lab/store/records/S4.json                      |  162 +-
 src/lab/store/records/S5.invariants.json           |    4 +-
 src/lab/store/records/S5.json                      |  108 +-
 src/lab/store/records/S6.invariants.json           |    4 +-
 src/lab/store/records/S6.json                      |  115 +-
 src/lab/store/records/S7.course.invariants.json    |   45 +-
 src/lab/store/records/S7.course.json               |  267 +-
 src/lab/store/records/S7.round.invariants.json     |   12 +-
 src/lab/store/records/S7.round.json                |  606 +++--
 src/lab/store/records/S7.vs-straight.json          |   84 +-
 src/lab/store/records/route-labfixture.json        |  237 +-
 src/runtime.js                                     |    5 +-
 tests/lab-pipeline.test.js                         |   39 +-
 tests/lab-s7course.test.js                         |   70 +-
 tests/lab-s7round.test.js                          |   46 +-
 31 files changed, 3877 insertions(+), 1662 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.6wsVJ3yPfO) (evidence/check_all.txt)
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
   `bash pyto/scripts/neat.sh drop 127 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 127`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-127): S7 plays the holes S6 resolved: the course graph binds px.holes.straight and reports px.holes.unresolved as unplayed doglegs, a second pointing tee gives the round more than one leg, and the comparison with the straight-leg route is re-run on that binding`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
