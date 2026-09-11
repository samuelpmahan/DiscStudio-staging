# Task 124: S5 Tee->Badge and S6 straight holes: a tee's pointing end read off its own pixels, the ray cast at the badge it points at, and the basket found by continuing that ray past the badge -- three points on a line, with the badges whose ray finds nothing reported as doglegs

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
git fetch origin exp/124
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/124:pyto/experiments/tasks/124/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 896d1d3 origin/exp/124 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

S5 Tee->Badge and S6 straight holes: a tee's pointing end read off its own pixels, the ray cast at the badge it points at, and the basket found by continuing that ray past the badge -- three points on a line, with the badges whose ray finds nothing reported as doglegs

## Starting point

03dbfbd1684c30b15122698fd32498485674b182 (land(task-122): draw a Stage by the addresses it publishes, not by its number: the Course overlay becomes an address table, the searched round joins the pipeline, and the renumbered S4-S7 draw themselves as they land). MAIN may have moved since: `git log --oneline 896d1d3..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  src/lab/fixtures.js
- M  src/lab/map.js
- A  src/lab/s5.js
- A  src/lab/s6.js
- M  src/lab/stage-sources.js
- A  src/lab/stages/S5.args.json
- A  src/lab/stages/S5.mmd
- A  src/lab/stages/S6.args.json
- A  src/lab/stages/S6.mmd
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
- A  src/lab/store/records/S5.invariants.json
- A  src/lab/store/records/S5.json
- A  src/lab/store/records/S6.invariants.json
- A  src/lab/store/records/S6.json
- M  src/lab/store/records/S7.course.invariants.json
- M  src/lab/store/records/S7.course.json
- M  src/lab/store/records/S7.round.invariants.json
- M  src/lab/store/records/S7.round.json
- M  src/lab/store/records/S7.vs-straight.json
- M  src/lab/store/records/route-labfixture.json
- A  tests/lab-s5.test.js
- A  tests/lab-s6.test.js

```
src/lab/fixtures.js                                |   44 +-
 src/lab/map.js                                     |   19 +-
 src/lab/s5.js                                      |  194 +
 src/lab/s6.js                                      |  175 +
 src/lab/stage-sources.js                           |    4 +
 src/lab/stages/S5.args.json                        |    4 +
 src/lab/stages/S5.mmd                              |   29 +
 src/lab/stages/S6.args.json                        |    3 +
 src/lab/stages/S6.mmd                              |   29 +
 src/lab/store/lab.json                             | 7576 +++++++++++++++-----
 .../records/HolesByNearestAnchor.invariants.json   |   32 +-
 src/lab/store/records/HolesByNearestAnchor.json    |  209 +-
 src/lab/store/records/S0.json                      |  102 +-
 src/lab/store/records/S1.json                      | 2822 ++++++--
 src/lab/store/records/S2.json                      |  242 +-
 src/lab/store/records/S3.json                      |  175 +-
 src/lab/store/records/S3.quick-anno.json           |   24 +-
 src/lab/store/records/S4.invariants.json           |   12 +-
 src/lab/store/records/S4.json                      | 1506 +++-
 src/lab/store/records/S5.invariants.json           |  107 +
 src/lab/store/records/S5.json                      |  609 ++
 src/lab/store/records/S6.invariants.json           |  127 +
 src/lab/store/records/S6.json                      |  415 ++
 src/lab/store/records/S7.course.invariants.json    |   28 +-
 src/lab/store/records/S7.course.json               |  172 +-
 src/lab/store/records/S7.round.invariants.json     |   24 +-
 src/lab/store/records/S7.round.json                |  562 +-
 src/lab/store/records/S7.vs-straight.json          |   53 +-
 src/lab/store/records/route-labfixture.json        |  203 +-
 tests/lab-s5.test.js                               |  110 +
 tests/lab-s6.test.js                               |  111 +
 31 files changed, 12813 insertions(+), 2909 deletions(-)
```

## Evidence

- verify: `node --test tests/*.test.js` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.RnYu9Thtmv) (evidence/check_all.txt)
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
   `bash pyto/scripts/neat.sh drop 124 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 124`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-124): S5 Tee->Badge and S6 straight holes: a tee's pointing end read off its own pixels, the ray cast at the badge it points at, and the basket found by continuing that ray past the badge -- three points on a line, with the badges whose ray finds nothing reported as doglegs`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
