# Task 71: the owner's ten replies to the first batch, filed in his words through the loop; an answer overturns a filed default (a label answered by default keeps its number in the batch's default group until the owner speaks, and his answer supersedes it on the root and in the answer Part); the walk stops scraping quotes after the word owner: his words on a step come only from filed answers

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
git fetch origin exp/71
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/71:pyto/experiments/tasks/71/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 129de8f origin/exp/71 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

the owner's ten replies to the first batch, filed in his words through the loop; an answer overturns a filed default (a label answered by default keeps its number in the batch's default group until the owner speaks, and his answer supersedes it on the root and in the answer Part); the walk stops scraping quotes after the word owner: his words on a step come only from filed answers

## Starting point

4946780e26116adfbc65f85733f6796e6bc0b6ab (board: **started** `task-70`: the batch carries only what needs the owner: a ro). MAIN may have moved since: `git log --oneline 129de8f..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/review/answers/BatchItemTextLength.json
- A  pyto/experiments/review/answers/ChainLatencyIsTheWholeTick.json
- M  pyto/experiments/review/answers/FileIsNotAnEffect.json
- M  pyto/experiments/review/answers/MoleculeAddress.json
- A  pyto/experiments/review/answers/MoleculeScheme.json
- A  pyto/experiments/review/answers/NeatIsAMount.json
- A  pyto/experiments/review/answers/OwnerQuotes.json
- A  pyto/experiments/review/answers/RefusedAndKilledSteps.json
- A  pyto/experiments/review/answers/RootLabelsCountAsOpen.json
- A  pyto/experiments/review/answers/StubOpensTheSelftest.json
- A  pyto/experiments/review/batches/8.json
- A  pyto/experiments/review/captures/7-1.json
- A  pyto/experiments/review/captures/7-2.json
- A  pyto/experiments/review/captures/7-3.json
- A  pyto/experiments/review/captures/7-4.json
- A  pyto/experiments/review/captures/7-5.json
- A  pyto/experiments/review/captures/7-6.json
- A  pyto/experiments/review/captures/7-7.json
- A  pyto/experiments/review/captures/8-157.json
- A  pyto/experiments/review/captures/8-215.json
- A  pyto/experiments/review/captures/8-225.json
- A  pyto/experiments/review/freezes/7-1.json
- A  pyto/experiments/review/freezes/7-2.json
- A  pyto/experiments/review/freezes/7-3.json
- A  pyto/experiments/review/freezes/7-4.json
- A  pyto/experiments/review/freezes/7-5.json
- A  pyto/experiments/review/freezes/7-6.json
- A  pyto/experiments/review/freezes/7-7.json
- A  pyto/experiments/review/freezes/8-157.json
- A  pyto/experiments/review/freezes/8-215.json
- A  pyto/experiments/review/freezes/8-225.json
- A  pyto/experiments/review/runs/answer-7-1.json
- A  pyto/experiments/review/runs/answer-7-2.json
- A  pyto/experiments/review/runs/answer-7-3.json
- A  pyto/experiments/review/runs/answer-7-4.json
- A  pyto/experiments/review/runs/answer-7-5.json
- A  pyto/experiments/review/runs/answer-7-6.json
- A  pyto/experiments/review/runs/answer-7-7.json
- A  pyto/experiments/review/runs/answer-8-157.json
- A  pyto/experiments/review/runs/answer-8-215.json
- A  pyto/experiments/review/runs/answer-8-225.json
- A  pyto/experiments/review/runs/ask-8.json
- M  pyto/questions.md
- M  pyto/scripts/walk.py
- M  pyto/src/pyto/neat/review.py
- M  pyto/tests/test_neat_review.py

```
.../review/answers/BatchItemTextLength.json        |   11 +
 .../review/answers/ChainLatencyIsTheWholeTick.json |   11 +
 .../review/answers/FileIsNotAnEffect.json          |   10 +-
 .../review/answers/MoleculeAddress.json            |   10 +-
 .../experiments/review/answers/MoleculeScheme.json |   11 +
 pyto/experiments/review/answers/NeatIsAMount.json  |   11 +
 pyto/experiments/review/answers/OwnerQuotes.json   |   11 +
 .../review/answers/RefusedAndKilledSteps.json      |   11 +
 .../review/answers/RootLabelsCountAsOpen.json      |   11 +
 .../review/answers/StubOpensTheSelftest.json       |   11 +
 pyto/experiments/review/batches/8.json             | 2147 ++++++++++++++++++++
 pyto/experiments/review/captures/7-1.json          |   11 +
 pyto/experiments/review/captures/7-2.json          |   11 +
 pyto/experiments/review/captures/7-3.json          |   11 +
 pyto/experiments/review/captures/7-4.json          |   11 +
 pyto/experiments/review/captures/7-5.json          |   11 +
 pyto/experiments/review/captures/7-6.json          |   11 +
 pyto/experiments/review/captures/7-7.json          |   11 +
 pyto/experiments/review/captures/8-157.json        |   11 +
 pyto/experiments/review/captures/8-215.json        |   11 +
 pyto/experiments/review/captures/8-225.json        |   11 +
 pyto/experiments/review/freezes/7-1.json           |    8 +
 pyto/experiments/review/freezes/7-2.json           |    8 +
 pyto/experiments/review/freezes/7-3.json           |    8 +
 pyto/experiments/review/freezes/7-4.json           |    8 +
 pyto/experiments/review/freezes/7-5.json           |    8 +
 pyto/experiments/review/freezes/7-6.json           |    8 +
 pyto/experiments/review/freezes/7-7.json           |    8 +
 pyto/experiments/review/freezes/8-157.json         |    8 +
 pyto/experiments/review/freezes/8-215.json         |    8 +
 pyto/experiments/review/freezes/8-225.json         |    8 +
 pyto/experiments/review/runs/answer-7-1.json       |  189 ++
 pyto/experiments/review/runs/answer-7-2.json       |  189 ++
 pyto/experiments/review/runs/answer-7-3.json       |  189 ++
 pyto/experiments/review/runs/answer-7-4.json       |  189 ++
 pyto/experiments/review/runs/answer-7-5.json       |  189 ++
 pyto/experiments/review/runs/answer-7-6.json       |  189 ++
 pyto/experiments/review/runs/answer-7-7.json       |  189 ++
 pyto/experiments/review/runs/answer-8-157.json     |  189 ++
 pyto/experiments/review/runs/answer-8-215.json     |  189 ++
 pyto/experiments/review/runs/answer-8-225.json     |  189 ++
 pyto/experiments/review/runs/ask-8.json            | 1671 +++++++++++++++
 pyto/questions.md                                  |   36 +
 pyto/scripts/walk.py                               |   20 +-
 pyto/src/pyto/neat/review.py                       |   41 +-
 pyto/tests/test_neat_review.py                     |   13 +-
 46 files changed, 6089 insertions(+), 27 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_neat_review tests.test_walk && python scripts/walk.py --check && grep -c 'Owner, 2026-09-10: ' questions.md | grep -q .` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.nUFGj25dY6) (evidence/check_all.txt)
    suite                         tests  status
    library                         368  OK
    experiments/classroom            16  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    250  OK
    experiments/hiding-primitives      6  OK
    experiments/molecules            10  OK
    experiments/s3-synthetic          5  OK
    experiments/students             17  OK
    experiments/tick-laws            14  OK
    consumer                         61  OK
    disc-stats                        4  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
{?} FiledDefaultsBecomeRootEntries: filing a default under a label that had no root entry creates one (### {?} Label with a Default line), and the collator then lists it twice, as the packet item and as a root item; the second is counted as default too, so nothing is asked twice, but the batch is longer than it need be.
{?} ReviewedItemsStillAnswerable: a reviewed item (task 58 and earlier) keeps its number in the batch JSON though it is not printed, so neat answer reaches it; ChainLatencyIsTheWholeTick was answered that way.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 71 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 71`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-71): the owner's ten replies to the first batch, filed in his words through the loop; an answer overturns a filed default (a label answered by default keeps its number in the batch's default group until the owner speaks, and his answer supersedes it on the root and in the answer Part); the walk stops scraping quotes after the word owner: his words on a step come only from filed answers`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
