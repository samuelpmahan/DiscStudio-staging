# Task 134: finding the RIGHT disc: one fn.shelf.query Calculation over the whole shelf, ranked search across every field including plastic, disc type and the flight numbers ('buzzz 177', 'midrange -1'), the quick filters (in this bag, in no bag, has photo), the sorts (recently added, maker, mold, disc type, speed, weight) and grouping by maker or disc type, with a compact and a card view that both keep every disc's own art

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
git fetch origin exp/134
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/134:pyto/experiments/tasks/134/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 5b4c38a origin/exp/134 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

finding the RIGHT disc: one fn.shelf.query Calculation over the whole shelf, ranked search across every field including plastic, disc type and the flight numbers ('buzzz 177', 'midrange -1'), the quick filters (in this bag, in no bag, has photo), the sorts (recently added, maker, mold, disc type, speed, weight) and grouping by maker or disc type, with a compact and a card view that both keep every disc's own art

## Starting point

f4fe05e13fdd5b8556c0d46f1b4271b1f341a2fb (land(task-132): adding a disc is one gesture: the shelf's + opens a composer with the facts that matter first (maker, mold, plastic, weight, colour, photo) and sensible defaults, and one disc.create command through dispatch makes the maker, the mold and the disc together, so one undo takes the whole disc back and nothing is ever named 'My new disc'). MAIN may have moved since: `git log --oneline 5b4c38a..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  scripts/browser_test.py
- M  scripts/demo_beats.py
- M  src/app.js
- M  src/runtime.js
- A  src/shelf.js
- M  src/style.css
- A  tests/shelf.test.js

```
scripts/browser_test.py |  45 ++++++++++++++++++++
 scripts/demo_beats.py   |  11 +++++
 src/app.js              |  45 ++++++++++++++++----
 src/runtime.js          |  17 +++++++-
 src/shelf.js            | 108 ++++++++++++++++++++++++++++++++++++++++++++++++
 src/style.css           |  27 ++++++++++++
 tests/shelf.test.js     |  90 ++++++++++++++++++++++++++++++++++++++++
 7 files changed, 333 insertions(+), 10 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.SaWpZCu8rg) (evidence/check_all.txt)
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
   `bash pyto/scripts/neat.sh drop 134 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 134`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-134): finding the RIGHT disc: one fn.shelf.query Calculation over the whole shelf, ranked search across every field including plastic, disc type and the flight numbers ('buzzz 177', 'midrange -1'), the quick filters (in this bag, in no bag, has photo), the sorts (recently added, maker, mold, disc type, speed, weight) and grouping by maker or disc type, with a compact and a card view that both keep every disc's own art`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
