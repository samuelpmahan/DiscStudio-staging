# Task 140: neat ask surfaces questions, not notes: batch 9 collated 359 items because every packet's Uncertain section is harvested whether it carries a {?} label or an evidence note; collate keeps only {?}-labelled items and filed defaults, ranks the owner's open ones first, and the batch says how many notes it left out; batch 9 as collated tonight is kept as the record of the defect

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
git fetch origin exp/140
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/140:pyto/experiments/tasks/140/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 9ac0f53 origin/exp/140 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

neat ask surfaces questions, not notes: batch 9 collated 359 items because every packet's Uncertain section is harvested whether it carries a {?} label or an evidence note; collate keeps only {?}-labelled items and filed defaults, ranks the owner's open ones first, and the batch says how many notes it left out; batch 9 as collated tonight is kept as the record of the defect

## Starting point

9ac0f53aca6d79464400fcb658e85ad956539468 (land(task-139): bags that never feel limiting: a disc reads as being in several bags at once (the shelf row names them), one tap adds or removes it from the shelf or from the bag, the order inside a bag is the owner's by arrows or by dragging the grip (one drop, one bag.reorder command, one undo), a bag is duplicated with bag.duplicate and renamed in place, an empty bag invites with the discs you would reach for, and nothing on the shelf side caps a bag). MAIN may have moved since: `git log --oneline 9ac0f53..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/review/batches/9.json
- A  pyto/experiments/review/runs/ask-9.json
- M  pyto/scripts/walk.py
- M  pyto/src/pyto/neat/review.py
- M  pyto/tests/test_neat_review.py

```
pyto/experiments/review/batches/9.json  | 2927 +++++++++++++++++++++++++++++++
 pyto/experiments/review/runs/ask-9.json | 1671 ++++++++++++++++++
 pyto/scripts/walk.py                    |   12 +-
 pyto/src/pyto/neat/review.py            |   73 +-
 pyto/tests/test_neat_review.py          |   90 +
 5 files changed, 4749 insertions(+), 24 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest tests.test_neat_review` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.jBET5BDSaG) (evidence/check_all.txt)
    suite                         tests  status
    library                         447  OK
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
   `bash pyto/scripts/neat.sh drop 140 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 140`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-140): neat ask surfaces questions, not notes: batch 9 collated 359 items because every packet's Uncertain section is harvested whether it carries a {?} label or an evidence note; collate keeps only {?}-labelled items and filed defaults, ranks the owner's open ones first, and the batch says how many notes it left out; batch 9 as collated tonight is kept as the record of the defect`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
