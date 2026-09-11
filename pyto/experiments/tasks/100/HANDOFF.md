# Task 100: brain/backend the benchmark Parts are what decides: the vertical's benchmark Parts are folded through PQL into one Part, px.exp.brain.result.backend.plan, and fn.brain.backend.<op> takes backend=auto, which reads the plan at the size this invocation actually has - still one pure Calculation, because the plan is an input like any other and an auto with no plan is refused by name rather than quietly given numpy; the plan is worth reading: cumsum is fastest in pure python at every size measured, argsort changes engine at the largest one and eig and fft change at the middle

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
git fetch origin exp/100
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/100:pyto/experiments/tasks/100/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff 365ab20 origin/exp/100 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
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

brain/backend the benchmark Parts are what decides: the vertical's benchmark Parts are folded through PQL into one Part, px.exp.brain.result.backend.plan, and fn.brain.backend.<op> takes backend=auto, which reads the plan at the size this invocation actually has - still one pure Calculation, because the plan is an input like any other and an auto with no plan is refused by name rather than quietly given numpy; the plan is worth reading: cumsum is fastest in pure python at every size measured, argsort changes engine at the largest one and eig and fft change at the middle

## Starting point

6d29ac32d88cd0a2814eb96cea9ebd30db1e32c1 (land(task-95): brain ml distances: the four calculations that each built their own n-by-n matrix (knn_predict, silhouette, kmeans, dbscan) route through fn.brain.backend.pairwise as one more backend, oracled against their own spelling and against scipy cdist, with the bracket that decides which spelling deserves the default; and exp/88 is killed, its candidate having landed inside task-89). MAIN may have moved since: `git log --oneline 365ab20..origin/claude/os-sprint-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- A  pyto/experiments/brain/backend/choose.py
- M  pyto/experiments/brain/backend/evidence.py
- M  pyto/experiments/brain/backend/ops.py
- M  pyto/experiments/brain/backend/summary.py
- A  pyto/experiments/brain/backend/test_choose.py
- M  pyto/experiments/brain/store/backend.json

```
pyto/experiments/brain/backend/choose.py      |   88 ++
 pyto/experiments/brain/backend/evidence.py    |   16 +-
 pyto/experiments/brain/backend/ops.py         |   43 +-
 pyto/experiments/brain/backend/summary.py     |   22 +-
 pyto/experiments/brain/backend/test_choose.py |  103 ++
 pyto/experiments/brain/store/backend.json     | 1370 ++++++++++++++++---------
 6 files changed, 1179 insertions(+), 463 deletions(-)
```

## Evidence

- verify: `cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (logs in /tmp/tmp.R7GJyDHsjB) (evidence/check_all.txt)
    suite                         tests  status
    library                         439  OK
    experiments/brain               673  OK
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

{?} both runs are in the packet: the copy's venv (python 3.11, numpy 2.4.6) through the Verify
line, and python 3.12.3 with numpy 2.5.3 and scipy 1.18.1 at
experiments/tasks/100/evidence/verify-python312-numpy253.txt. 673 tests, OK in both - the whole
brain suite, not only this vertical's.
{?} the plan is measured on THIS machine. A slower or faster host, or a numpy built against a
different BLAS, would measure different crossovers and the committed plan Part would be wrong for
it. That is why `choose.build(store)` is a function anyone can re-run rather than a table anyone
typed, and why the map's next list asks for the plan to be rebuilt where it runs.
{?} `backend="auto"` needs `args["plan"]`. Reading the plan off disk inside the facade would have
been friendlier and would have made `fn.brain.backend.<op>` an effect, so it is refused by name
instead. The cost is that every caller who wants auto has to carry one more Part.
{?} the plan only decides at sizes where every engine of an op was measured; a partially measured
size is skipped rather than guessed at. With three engines everywhere today, that skips nothing.
{?} the plan is worth reading before anyone hard-codes numpy: cumsum is fastest in PURE PYTHON at
all three measured sizes (1.2-1.4x), because numpy's per-call overhead is most of the measurement
and the op is one pass either way. argsort, cholesky, eig and fft each change engine between their
three sizes.

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 100 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 100`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-100): brain/backend the benchmark Parts are what decides: the vertical's benchmark Parts are folded through PQL into one Part, px.exp.brain.result.backend.plan, and fn.brain.backend.<op> takes backend=auto, which reads the plan at the size this invocation actually has - still one pure Calculation, because the plan is an input like any other and an auto with no plan is refused by name rather than quietly given numpy; the plan is worth reading: cumsum is fastest in pure python at every size measured, argsort changes engine at the largest one and eig and fft change at the middle`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
