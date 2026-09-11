# Task 83: brain ml foundation: the ml vertical's shared core (backend dispatch py/np, matrix helpers, seeded generators, part/oracle/bench/record writers) plus linear regression closed form and gradient descent, ridge, regression metrics (mse/mae/r2) and seeded train-test split and k-fold, each a Calculation fn.brain.ml.<name> with oracle Parts, tests and benchmarks

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
git fetch origin exp/83
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/83:pyto/experiments/tasks/83/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 41923bd origin/exp/83 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain ml foundation: the ml vertical's shared core (backend dispatch py/np, matrix helpers, seeded generators, part/oracle/bench/record writers) plus linear regression closed form and gradient descent, ridge, regression metrics (mse/mae/r2) and seeded train-test split and k-fold, each a Calculation fn.brain.ml.<name> with oracle Parts, tests and benchmarks

## Starting point

e6f06534cee445bb54fa685e40bb9f44228d8489 (board: **started** `task-82`: brain/stats descriptive and correlation as Calcul). MAIN may have moved since: `git log --oneline 41923bd..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/brain/ml/__init__.py
- A  pyto/experiments/brain/ml/build.py
- A  pyto/experiments/brain/ml/calcs.py
- A  pyto/experiments/brain/ml/core.py
- A  pyto/experiments/brain/ml/linear.py
- A  pyto/experiments/brain/ml/metrics.py
- A  pyto/experiments/brain/ml/parts.py
- A  pyto/experiments/brain/ml/resample.py
- A  pyto/experiments/brain/ml/test_core.py
- A  pyto/experiments/brain/ml/test_linear.py
- A  pyto/experiments/brain/ml/test_metrics.py
- A  pyto/experiments/brain/ml/test_resample.py
- A  pyto/experiments/brain/ml/test_store.py
- A  pyto/experiments/brain/records/ml.regression.json
- A  pyto/experiments/brain/store/ml.json

```
pyto/experiments/brain/ml/__init__.py             |    1 +
 pyto/experiments/brain/ml/build.py                |  359 ++
 pyto/experiments/brain/ml/calcs.py                |   62 +
 pyto/experiments/brain/ml/core.py                 |  236 +
 pyto/experiments/brain/ml/linear.py               |  175 +
 pyto/experiments/brain/ml/metrics.py              |  221 +
 pyto/experiments/brain/ml/parts.py                |  266 +
 pyto/experiments/brain/ml/resample.py             |  210 +
 pyto/experiments/brain/ml/test_core.py            |   75 +
 pyto/experiments/brain/ml/test_linear.py          |  121 +
 pyto/experiments/brain/ml/test_metrics.py         |  126 +
 pyto/experiments/brain/ml/test_resample.py        |  107 +
 pyto/experiments/brain/ml/test_store.py           |   83 +
 pyto/experiments/brain/records/ml.regression.json | 4128 ++++++++++++
 pyto/experiments/brain/store/ml.json              | 7141 +++++++++++++++++++++
 15 files changed, 13311 insertions(+)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.tRyrvlUMyB) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               117  OK
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
   `bash pyto/scripts/neat.sh drop 83 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 83`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-83): brain ml foundation: the ml vertical's shared core (backend dispatch py/np, matrix helpers, seeded generators, part/oracle/bench/record writers) plus linear regression closed form and gradient descent, ridge, regression metrics (mse/mae/r2) and seeded train-test split and k-fold, each a Calculation fn.brain.ml.<name> with oracle Parts, tests and benchmarks`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
