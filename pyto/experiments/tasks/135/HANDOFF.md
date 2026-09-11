# Task 135: constraints defining DiscComp: a battle is composed from reusable Constraints with parameters (discCap, placesPoints, tieRule) the way a competition is, scoring is one Calculation over the battle's states with a receipt (ranks, points, a running total), and the UX for a 5-disc cap battle where the top 3 score 3,2,1 is pick the template, add discs against the cap, tap the order Also carries the review item Boone (the AI PM) raised for the vertical frame, worded for the orientation control task 133 landed ('frame': Landscape and vertical export frames, on the OnTheCourse inspector).

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
git fetch origin exp/135
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/135:pyto/experiments/tasks/135/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff ac62bf5 origin/exp/135 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

constraints defining DiscComp: a battle is composed from reusable Constraints with parameters (discCap, placesPoints, tieRule) the way a competition is, scoring is one Calculation over the battle's states with a receipt (ranks, points, a running total), and the UX for a 5-disc cap battle where the top 3 score 3,2,1 is pick the template, add discs against the cap, tap the order Also carries the review item Boone (the AI PM) raised for the vertical frame, worded for the orientation control task 133 landed ('frame': Landscape and vertical export frames, on the OnTheCourse inspector).

## Starting point

bbcf4dc374ee3aa50d76b2c5d1e557e8f64b7e10 (land(task-133): vertical content: a 1080x1920 portrait canvas beside the 1920x1080 one, composed by the same fn.comparison.layout, plus a reusable frame preset (fill, safe area, title strip, sponsor lockup on the cards cascade's global tokens) materialized by the same fn.overlay.svg, and exports that honour the orientation). MAIN may have moved since: `git log --oneline ac62bf5..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  scripts/browser_test.py
- M  src/app.js
- A  src/battle.js
- M  src/constraints.js
- M  src/domain.js
- M  src/presentation.js
- M  src/review-data.js
- M  src/runtime.js
- M  src/seed.js
- M  src/style.css
- A  tests/battle.test.js
- M  tests/core.test.js
- M  tests/embedded_harness.py
- M  tests/fixtures/serial-run-record.json

```
scripts/browser_test.py               |   59 ++
 src/app.js                            |   70 ++-
 src/battle.js                         |  141 +++++
 src/constraints.js                    |   55 ++
 src/domain.js                         |   30 +-
 src/presentation.js                   |    4 +-
 src/review-data.js                    |    1 +
 src/runtime.js                        |   69 +-
 src/seed.js                           |    2 +-
 src/style.css                         |    2 +-
 tests/battle.test.js                  |  101 +++
 tests/core.test.js                    |   11 +-
 tests/embedded_harness.py             |   42 +-
 tests/fixtures/serial-run-record.json | 1114 +++++++++++++++++++++++++++------
 14 files changed, 1487 insertions(+), 214 deletions(-)
```

## Evidence

- verify: `npm test` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.hxRbxPzjpw) (evidence/check_all.txt)
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

{?} HarnessWasExponential: tests/embedded_harness.py inlined every module's data: URL into its
parent, once per import edge, so one source byte in a diamond like src/domain.js was mounted dozens of
times: 48 modules totalling ~1 MB of source were reaching the browser as a single 32 MB data: URL, and
this slice's one extra import into domain.js was enough to crash the renderer ("Target crashed" on the
first pointer drag, three runs in a row, on an otherwise idle machine). The harness now mounts each
module once and resolves `mod:<path>` specifiers through an import map: 1.03 MB instead of 32 MB, and
the whole browser suite runs in about a minute instead of ten. Anything that reads the shape of the
mounted page (rather than the app) should know it changed.

{?} EntryIsAPart: a card's BattleEntry is now published by `fn.battle.entry`, and `fn.domain.fields`
takes it as a second input so the values a card shows come from that Part. The material Part still
carries `roots.entry` with a null record beside it -- two ways to say "this card's entry", one now
vestigial. A root that could name an address instead of carrying a record would remove the second and
make the material state-independent outright.

{?} OneBattleTwoReceipts: the battle's Constraints run as their own composition (`discomp`) and its
standings run inside `on-the-course`; both read `px.battle.material`, and the memo makes the second
free. But "one battle, two receipts" is a shape the board has no word for. A composition that could
declare it consumes another composition's produce -- rather than re-deriving it -- would be one.

{?} TieShareRounding: `tieRule: share` averages the tied places' points and rounds to two decimals, so
3,2,1 shared over two places puts 2.5 on a card. Integers with a stated rounding rule, or fractions on
screen, is the owner's call; the Constraint has the parameter either way.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 135 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 135`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-135): constraints defining DiscComp: a battle is composed from reusable Constraints with parameters (discCap, placesPoints, tieRule) the way a competition is, scoring is one Calculation over the battle's states with a receipt (ranks, points, a running total), and the UX for a 5-disc cap battle where the top 3 score 3,2,1 is pick the template, add discs against the cap, tap the order Also carries the review item Boone (the AI PM) raised for the vertical frame, worded for the orientation control task 133 landed ('frame': Landscape and vertical export frames, on the OnTheCourse inspector).`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
