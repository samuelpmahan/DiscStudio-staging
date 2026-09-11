# Task 137: SingleCard and the export queue: Single Disc mode composes one disc with a spotlight design made for it (the photo large, the numbers legible, a winner mark that scales, the score/highlight/winner it has in the battle, an export named after the disc), and every export is a queued job that runs in order - all states, this battle vertical, every disc in the battle - each leaving an export.record receipt and a file, the queue surviving navigation, failures as sentences

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
git fetch origin exp/137
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/137:pyto/experiments/tasks/137/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 36ee0ce origin/exp/137 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

SingleCard and the export queue: Single Disc mode composes one disc with a spotlight design made for it (the photo large, the numbers legible, a winner mark that scales, the score/highlight/winner it has in the battle, an export named after the disc), and every export is a queued job that runs in order - all states, this battle vertical, every disc in the battle - each leaving an export.record receipt and a file, the queue surviving navigation, failures as sentences

## Starting point

a87812e363bd904660bbf093804dc4198d16deb8 (land(task-135): constraints defining DiscComp: a battle is composed from reusable Constraints with parameters (discCap, placesPoints, tieRule) the way a competition is, scoring is one Calculation over the battle's states with a receipt (ranks, points, a running total), and the UX for a 5-disc cap battle where the top 3 score 3,2,1 is pick the template, add discs against the cap, tap the order Also carries the review item Boone (the AI PM) raised for the vertical frame, worded for the orientation control task 133 landed ('frame': Landscape and vertical export frames, on the OnTheCourse inspector).). MAIN may have moved since: `git log --oneline 36ee0ce..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  scripts/browser_test.py
- M  scripts/demo_beats.py
- M  src/app.js
- M  src/cards.js
- M  src/domain.js
- A  src/exports.js
- M  src/presentation.js
- M  src/runtime.js
- M  src/seed.js
- M  src/style.css
- M  tests/cards.test.js
- A  tests/exports.test.js
- M  tests/fixtures/serial-run-record.json

```
scripts/browser_test.py               |  87 +++++++++++++++++++++++---
 scripts/demo_beats.py                 |  12 ++++
 src/app.js                            | 113 ++++++++++++++++++++++++++++------
 src/cards.js                          |   2 +-
 src/domain.js                         |   3 +-
 src/exports.js                        |  53 ++++++++++++++++
 src/presentation.js                   |  10 ++-
 src/runtime.js                        |  18 ++++--
 src/seed.js                           |   2 +-
 src/style.css                         |   2 +-
 tests/cards.test.js                   |   4 +-
 tests/exports.test.js                 |  43 +++++++++++++
 tests/fixtures/serial-run-record.json |   2 +-
 13 files changed, 310 insertions(+), 41 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 1, last line: SOME SUITES FAILED (logs in /tmp/tmp.cLj2Xij0ky) (evidence/check_all.txt)
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
{?} QueueIsSessionState: the export queue lives in the page's own `ui` object, not on the board: a job is
not a Part, so a reload loses a queue that has not finished, while the receipts it already wrote survive
in the world. A Part for the queue would make it inspectable and restartable like everything else here,
but a Part that changes five times a second during a run is a different animal from the Parts this board
holds, and the kernel has no word for that yet.

{?} SvgExportsAreRecorded: the queue files an `export.record` for SVG jobs too (`type: 'SVG'`), so
`world.exports` is no longer "the PNG exports" -- anything counting that array now has to filter by type.
The alternative (SVG downloads leaving no receipt) is what the studio did before, and it meant half the
exports a person actually made had no record at all.

{?} SinglePresetIsTheProjection: `single` in the card cascade now means OnTheCourse's Single Disc mode and
composes with `layout.singlePresetId`; before this slice it meant the comparison's own design. The
Component Editor's DisplayCard tab still previews whichever preset is selected there, so "the single
projection" and "the card the editor is showing" are two things wearing one word.


{?} DialogsAfterRehydrate: scripts/browser_test.py rehydrates by closing the page and mounting a new one,
and the new page carried no dialog handler, so every `confirm()` after that point was auto-dismissed and
the action behind it silently did nothing (this slice's "clear the lineup" looked like it worked and did
not). The handler is now re-registered on the rehydrated page. Any check written after that line and
before this fix may have been asserting on an action that never happened.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 137 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 137`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-137): SingleCard and the export queue: Single Disc mode composes one disc with a spotlight design made for it (the photo large, the numbers legible, a winner mark that scales, the score/highlight/winner it has in the battle, an export named after the disc), and every export is a queued job that runs in order - all states, this battle vertical, every disc in the battle - each leaving an export.record receipt and a file, the queue surviving navigation, failures as sentences`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
